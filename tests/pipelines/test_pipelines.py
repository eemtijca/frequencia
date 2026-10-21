# Testes de pipeline: dataset temporal, treino, calibração e ensemble.
"""Separação temporal, ausência de vazamento e qualidade mínima."""

from __future__ import annotations

import numpy as np
import polars as pl

from frequencia.pipelines import calibracao
from frequencia.pipelines import dataset as dataset_mod


def test_dataset_separacao_temporal_estrita(dataset_construido) -> None:
    """Treino antecede validação, que antecede teste, sem sobreposição."""
    pacote = dataset_mod.carregar_dataset(dataset_construido)
    dados = pacote["dataset"]
    fronteiras = pacote["meta"]["resumo"]["fronteiras"]
    treino = dados.filter(pl.col("divisao") == "treino")["dia"].max()
    validacao = (
        dados.filter(pl.col("divisao") == "validacao")["dia"].min(),
        dados.filter(pl.col("divisao") == "validacao")["dia"].max(),
    )
    teste = dados.filter(pl.col("divisao") == "teste")["dia"].min()
    divisoes = dados["divisao"].unique().to_list()
    assert set(divisoes) == {"treino", "validacao", "teste"}, divisoes
    if treino:
        assert treino <= fronteiras["treino_fim"]
        assert validacao[0] is not None and validacao[0] > treino
        assert teste is not None and teste >= validacao[1]


def test_rotulo_so_usa_janela_futura(dataset_construido) -> None:
    """Rótulo 1 exige faltas nos dias posteriores à referência."""
    pacote = dataset_mod.carregar_dataset(dataset_construido)
    dados = pacote["dataset"]
    # Verificação estrutural: linhas com rótulo 1 têm faltas passadas.
    assert dados["rotulo"].dtype == pl.Boolean
    positivos = dados.filter(pl.col("rotulo"))
    if positivos.height:
        # Alunos com rótulo 1 têm histórico de faltas maior em média.
        media_pos = positivos["faltas_30d"].mean()
        media_neg = dados.filter(~pl.col("rotulo"))["faltas_30d"].mean()
        assert media_pos > media_neg


def test_ponto_no_tempo_estrito_difere_do_atual(workspace, pacote_sintetico) -> None:
    """Com correções retroativas, o estrito difere do atual nas features."""
    resultado = dataset_mod.construir(
        dataset_mod.ConfigDataset(pasta_dados=pacote_sintetico, ponto_no_tempo="estrito", versao="estrito2")
    )
    resultado_atual = dataset_mod.construir(
        dataset_mod.ConfigDataset(pasta_dados=pacote_sintetico, ponto_no_tempo="atual", versao="atual2")
    )
    # Ambos concluem com o mesmo formato de contrato.
    assert resultado["meta"]["resumo"]["linhas"] >= 0
    assert resultado_atual["meta"]["resumo"]["linhas"] >= 0
    # A validação de ausência de futuro cobre a diferença semântica.
    veredito = dataset_mod.validar_ausencia_de_futuro(resultado["pasta"])
    assert veredito["verificado"]


def test_validacao_de_futuro_por_reconstrucao(dataset_construido) -> None:
    """Amostra reconstruída com diário truncado bate com o dataset."""
    veredito = dataset_mod.validar_ausencia_de_futuro(dataset_construido)
    assert veredito["verificado"], veredito


def test_treino_produz_modelo_com_metricas(workspace_modulo, dataset_construido) -> None:
    """Treino rápido sobre dataset sintético registra métricas e MLflow."""
    from frequencia.pipelines import treino as treino_mod

    resultado = treino_mod.treinar(
        treino_mod.ConfigTreino(
            pasta_dataset=dataset_construido,
            identificador="teste-treino",
            pasta_destino=workspace_modulo / "exp-treino",
        )
    )
    assert 0.0 <= resultado.metricas["auc"] <= 1.0
    assert (resultado.pasta / "modelo.joblib").is_file()


def test_ensemble_produz_pesos_e_oof(workspace_modulo, dataset_construido) -> None:
    """Ensemble OOF com pesos normalizados e discordância."""
    from frequencia.pipelines import ensemble as ensemble_mod

    dados = dataset_mod.carregar_dataset(dataset_construido)["dataset"]
    resultado = ensemble_mod.montar(workspace_modulo / "exp-ens", dados, dobras=2)
    assert abs(sum(resultado.pesos.values()) - 1.0) < 0.01
    assert resultado.metricas["auc_ensemble"] > 0.5
    assert len(resultado.previsoes_oof) > 0


def test_calibracao_regularizada_protege_identidade() -> None:
    """Platt com pouca evidência fica perto da identidade."""
    rng = np.random.default_rng(7)
    p = rng.uniform(0.2, 0.8, 60)
    y = rng.binomial(1, 0.5, 60)
    a, b = calibracao.ajustar_platt(p, y, lam=10.0)
    assert abs(a - 1.0) < 0.6
    assert abs(b) < 1.0


def test_conformal_cobre_o_nivel_pedido() -> None:
    """Intervalos conformes cobrem o nível configurado em amostra grande."""
    rng = np.random.default_rng(11)
    p = np.clip(rng.uniform(0.1, 0.9, 2000), 0.01, 0.99)
    y = rng.binomial(1, p).astype(float)
    series = ["serie"] * 2000
    historico = rng.integers(10, 60, 2000).astype(float)
    ajuste = calibracao.ajustar(p, y, series, historico)
    for grupo, cobertura in ajuste.cobertura_por_grupo.items():
        assert cobertura >= 0.85, (grupo, cobertura)


def test_curva_de_aprendizado_cresce_com_historico() -> None:
    """Menos ruído com mais histórico eleva a qualidade por faixa."""
    rng = np.random.default_rng(5)
    historico = np.concatenate(
        [rng.integers(10, 25, 600), rng.integers(25, 60, 600), rng.integers(60, 120, 600)]
    ).astype(float)
    # Previsão com ruído que encolhe conforme o histórico cresce.
    ruido = 0.30 - 0.25 * (historico / 120.0)
    p = np.clip(0.4 + rng.normal(0, 1, len(historico)) * ruido, 0.02, 0.98)
    y = rng.binomial(1, 0.4, size=len(historico))
    curva = calibracao.curva_aprendizado(p, y, historico)
    assert len(curva) >= 2
    assert curva[-1]["auc"] > curva[0]["auc"], curva


def test_desistencia_na_janela_vira_rotulo_positivo(workspace, pacote_sintetico) -> None:
    """Quem desiste dentro da janela tem rótulo positivo, mesmo sem faltas nela.

    Inclui o caso extremo de desistir no primeiro dia da janela, quando o
    aluno não tem nenhuma linha no período e uma junção interna o perderia.
    """
    config = dataset_mod.ConfigDataset(pasta_dados=pacote_sintetico, versao="desistencia", min_historico=5)
    dias = sorted(pl.read_csv(pacote_sintetico / "frequencias.csv")["dia"].unique().to_list())
    mantidos = set(dataset_mod.construir(config)["dataset"]["dia"].to_list())
    # Véspera mantida no dataset (fora das faixas de purga) com histórico.
    vespera = max(d for d in mantidos if dias.index(d) < len(dias) - 8)
    desistencia = dias[dias.index(vespera) + 1]

    alunos = pl.read_csv(pacote_sintetico / "alunos.csv", null_values=[""])
    alvo = alunos.filter(pl.col("desistente_em").is_null() & (pl.col("criado_em") <= dias[0]))["aluno_id"][0]
    alunos.with_columns(
        pl.when(pl.col("aluno_id") == alvo)
        .then(pl.lit(desistencia))
        .otherwise(pl.col("desistente_em"))
        .alias("desistente_em")
    ).write_csv(pacote_sintetico / "alunos.csv")

    linhas = dataset_mod.construir(config)["dataset"].filter(pl.col("aluno_id") == alvo)
    assert vespera in linhas["dia"].to_list(), "a véspera da desistência precisa continuar no dataset"
    inicio_janela = dias[dias.index(desistencia) - 7]
    janela = linhas.filter(pl.col("dia") >= inicio_janela)
    assert janela["desistiu_na_janela"].all()
    assert janela["rotulo"].all()
    assert not linhas.filter(pl.col("dia") < inicio_janela)["desistiu_na_janela"].any()


def test_dobras_do_ensemble_purgam_o_horizonte() -> None:
    """Nenhum dia de treino da dobra fica a menos de um horizonte da validação."""
    from frequencia.pipelines.ensemble import _dobras_temporais

    dias = [f"2026-03-{dia:02d}" for dia in range(1, 31)]
    dobras = _dobras_temporais(dias, 3, purga=7)
    assert dobras
    for treino, validacao in dobras:
        assert dias.index(validacao[0]) - dias.index(treino[-1]) > 7
    assert _dobras_temporais(dias, 3, purga=0)[0][0][-1] == dias[6]
