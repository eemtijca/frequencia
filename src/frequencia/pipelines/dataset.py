# Construção do dataset temporal com rótulo futuro e separação estrita.
"""Dataset de treino: unidade aluno-dia, horizonte futuro e sem vazamento.

Para cada dia de referência D, as features vêm do snapshot as-of do fim de D
(ponto-in-tempo estrito) e o rótulo vem dos 7 dias letivos seguintes no
estado final: positivo com pelo menos duas faltas na janela ou com
desistência dentro dela. Sem a segunda condição, quem desiste no começo da
janela teria as faltas truncadas e rótulo negativo justamente no desfecho
mais grave (ADR-019). A separação treino/validação/teste é por tempo, com intervalo
de purga do tamanho do horizonte entre blocos, para que nenhum rótulo
atravesse a fronteira.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import polars as pl

from frequencia.dados import sintetico
from frequencia.features import calculo
from frequencia.features import diario as diario_mod
from frequencia.infra import caminhos, logs
from frequencia.infra import hash as hash_infra
from frequencia.infra.erros import ErroValidacao

FIM_DIA = "T23:59:59"


@dataclass
class ConfigDataset:
    """Parâmetros declarativos da construção do dataset."""

    pasta_dados: Path
    horizonte_dias_letivos: int = 7
    limiar_rotulo: int = 2
    min_historico: int = 10
    passo: int = 1
    ponto_no_tempo: str = "estrito"  # estrito | atual
    perfil: str | None = None
    versao: str = ""


def _dias_letivos_apos(dias: list[str], dia: str, quantidade: int) -> list[str]:
    """Dias letivos estritamente posteriores ao dia dado, em quantidade."""
    posteriores = [d for d in dias if d > dia]
    return posteriores[:quantidade]


def construir(config: ConfigDataset, *, detalhado: bool = False) -> dict:
    """Constrói o dataset completo e grava em var/dados/processados."""
    if config.ponto_no_tempo not in ("estrito", "atual"):
        msg = "ponto_no_tempo deve ser estrito ou atual."
        raise ErroValidacao(msg)
    pacote = sintetico.carregar_pacote(config.pasta_dados)
    tabelas = pacote["tabelas"]

    if config.perfil:
        tabelas = _filtrar_perfil(tabelas, config.perfil)

    # Diário final: base dos rótulos (o desfecho observado ao fim do período).
    diario_final = diario_mod.materializar(tabelas, instante=None)
    dias = sorted(diario_final["dia"].unique().to_list())
    if len(dias) < config.horizonte_dias_letivos + 5:
        msg = (
            "Período de dados curto demais para o horizonte pedido. "
            "Reduza o horizonte ou gere mais dias letivos."
        )
        raise ErroValidacao(msg)

    feriados = [date.fromisoformat(valor) for valor in tabelas["feriados"]["dia"].drop_nulls().to_list()]
    contexto_mec = tabelas["contexto_mec"]

    dias_referencia = [
        d
        for indice, d in enumerate(dias)
        if indice % max(1, config.passo) == 0
        and len([x for x in dias if x > d]) >= config.horizonte_dias_letivos
    ]

    # Rótulos a partir do diário final, por aluno e janela futura.
    faltou_final = diario_final.select("aluno_id", "dia", "faltou")
    desistencias = tabelas["alunos"].select("aluno_id", "desistente_em")
    por_dia: list[pl.DataFrame] = []
    for dia in dias_referencia:
        janela = _dias_letivos_apos(dias, dia, config.horizonte_dias_letivos)
        faltas_janela = (
            faltou_final.filter(pl.col("dia").is_in(janela))
            .group_by("aluno_id")
            .agg(pl.col("faltou").sum().alias("faltas_futuras"))
        )
        instante = None if config.ponto_no_tempo == "atual" else f"{dia}{FIM_DIA}"
        diario_asof = diario_mod.materializar(tabelas, instante=instante, ate_dia=dia)
        frame = calculo.calcular(
            diario_asof,
            dia_referencia=dia,
            contexto_mec=contexto_mec,
            feriados=feriados,
            dias_restantes_periodo=sum(1 for d in dias if d > dia),
        )
        # Junção pela esquerda: quem desiste no primeiro dia da janela não
        # tem nenhuma linha nela, e uma junção interna o descartaria.
        frame = (
            frame.join(faltas_janela, on="aluno_id", how="left")
            .with_columns(pl.col("faltas_futuras").fill_null(0))
            .join(desistencias.rename({"desistente_em": "_desistente_em"}), on="aluno_id", how="left")
            .with_columns(
                (
                    pl.col("_desistente_em").is_not_null()
                    & (pl.col("_desistente_em") > dia)
                    & (pl.col("_desistente_em") <= janela[-1])
                ).alias("desistiu_na_janela")
            )
            .with_columns(
                ((pl.col("faltas_futuras") >= config.limiar_rotulo) | pl.col("desistiu_na_janela")).alias(
                    "rotulo"
                )
            )
            .drop("_desistente_em")
        )
        frame = frame.filter(
            (pl.col("historico_dias") >= config.min_historico) & pl.col("rotulo").is_not_null()
        )
        por_dia.append(frame)

    dataset = pl.concat(por_dia, how="vertical") if por_dia else _dataset_vazio()

    dias_uteis = sorted(dataset["dia"].unique().to_list())
    fronteiras = _separar_temporal(dias_uteis, config.horizonte_dias_letivos)
    dataset = dataset.with_columns(
        pl.when(pl.col("dia") <= fronteiras["treino_fim"])
        .then(pl.lit("treino"))
        .when(
            (pl.col("dia") >= fronteiras["validacao_inicio"]) & (pl.col("dia") <= fronteiras["validacao_fim"])
        )
        .then(pl.lit("validacao"))
        .when(pl.col("dia") >= fronteiras["teste_inicio"])
        .then(pl.lit("teste"))
        .otherwise(pl.lit("purga"))
        .alias("divisao")
    ).filter(pl.col("divisao") != "purga")

    pasta_destino = caminhos.caminho("processados") / _identificador(config)
    pasta_destino.mkdir(parents=True, exist_ok=True)
    dataset.write_parquet(pasta_destino / "dataset.parquet")
    dataset.head(500).write_csv(pasta_destino / "amostra.csv")

    resumo = {
        "linhas": dataset.height,
        "alunos": dataset["aluno_id"].n_unique(),
        "dias_referencia": len(dias_referencia),
        "taxa_rotulo": round(
            float(dataset.select(pl.col("rotulo").cast(pl.Float64).mean()).item(0, 0) or 0.0), 4
        ),
        "positivos_por_desistencia": int(
            dataset.filter(
                pl.col("desistiu_na_janela") & (pl.col("faltas_futuras") < config.limiar_rotulo)
            ).height
        )
        if "desistiu_na_janela" in dataset.columns
        else 0,
        "divisao": dataset.group_by("divisao")
        .agg(
            pl.len().alias("linhas"),
            pl.col("rotulo").cast(pl.Float64).mean().round(4).alias("taxa_rotulo"),
        )
        .sort("divisao")
        .to_dicts(),
        "fronteiras": fronteiras,
    }
    meta = {
        "identificador": _identificador(config),
        "config": {
            "pasta_dados": str(config.pasta_dados),
            "horizonte_dias_letivos": config.horizonte_dias_letivos,
            "limiar_rotulo": config.limiar_rotulo,
            "min_historico": config.min_historico,
            "passo": config.passo,
            "ponto_no_tempo": config.ponto_no_tempo,
            "perfil": config.perfil,
        },
        "resumo": resumo,
        "linhagem": {
            "origem": pacote["meta"].get("identificador", str(config.pasta_dados)),
            "hash_pasta": pacote["meta"].get("hashes", {}).get("faltas.csv", ""),
            "verdade_oculta": str(Path(config.pasta_dados) / "verdade_oculta"),
        },
        "colunas": dataset.columns,
    }
    with (pasta_destino / "meta.json").open("w", encoding="utf-8") as saida:
        json.dump(meta, saida, ensure_ascii=False, indent=2, sort_keys=True)
        saida.write("\n")

    logs.registrar(
        "datasets.construir",
        estagio="datasets",
        identificador=meta["identificador"],
        linhas=resumo["linhas"],
        detalhado=detalhado,
    )
    return {"pasta": pasta_destino, "meta": meta, "dataset": dataset}


def _dataset_vazio() -> pl.DataFrame:
    """Frame vazio com as colunas do contrato, para períodos inviáveis."""
    from frequencia.features.catalogo import NOMES_FEATURES

    return pl.DataFrame(
        schema={
            "aluno_id": pl.Utf8,
            "dia": pl.Utf8,
            "rotulo": pl.Boolean,
            **dict.fromkeys(NOMES_FEATURES, pl.Float64),
        }
    )


def _identificador(config: ConfigDataset) -> str:
    """Identificador estável do dataset a partir da configuração."""
    digestao = hash_infra.hash_pasta(config.pasta_dados)[:10]
    corpo = (
        f"{digestao}-h{config.horizonte_dias_letivos}-r{config.limiar_rotulo}"
        f"-m{config.min_historico}-p{config.passo}-{config.ponto_no_tempo}"
    )
    if config.perfil:
        corpo += f"-{config.perfil}"
    return config.versao or corpo


def _separar_temporal(dias: list[str], purga: int) -> dict[str, str]:
    """Divide os dias em treino/validação/teste com purga do horizonte.

    Os dias das faixas de purga são descartados: os rótulos deles
    atravessariam a fronteira e vazariam futuro entre divisões.
    """
    if not dias:
        msg = "Sem dias de referência para separar o dataset."
        raise ErroValidacao(msg)
    total = len(dias)
    fim_treino = max(1, int(total * 0.55))
    inicio_validacao = min(fim_treino + purga, max(fim_treino + 1, total - 2))
    fim_validacao = max(inicio_validacao + 1, int(total * 0.8))
    inicio_teste = min(fim_validacao + purga, total - 1)
    return {
        "treino_fim": dias[fim_treino - 1],
        "validacao_inicio": dias[inicio_validacao],
        "validacao_fim": dias[min(fim_validacao, total - 2)],
        "teste_inicio": dias[inicio_teste],
    }


def _filtrar_perfil(tabelas: dict[str, pl.DataFrame], perfil: str) -> dict[str, pl.DataFrame]:
    """Restringe as tabelas às escolas cujo perfil de recursos casa com a chave."""
    chave = dict(parte.split("=") for parte in perfil.split(",") if "=" in parte)
    escolas = tabelas["escolas"]
    mantidas = escolas
    for campo, valor in chave.items():
        alvo = valor.lower() in ("true", "sim", "1")
        mantidas = mantidas.filter(pl.col(campo) == alvo)
    ids = mantidas["escola_id"].to_list()
    if not ids:
        msg = f"Nenhuma escola casa com o perfil {perfil}."
        raise ErroValidacao(msg)
    saida: dict[str, pl.DataFrame] = {}
    for nome, dados in tabelas.items():
        if "escola_id" in dados.columns:
            saida[nome] = dados.filter(pl.col("escola_id").is_in(ids))
        else:
            saida[nome] = dados
    return saida


def carregar_dataset(pasta: Path) -> dict:
    """Carrega um dataset construído com seu metadado."""
    pasta = Path(pasta)
    alvo = pasta / "dataset.parquet"
    if not alvo.is_file():
        msg = f"Dataset não encontrado em {pasta}. Construa antes de treinar."
        raise ErroValidacao(msg)
    dados = pl.read_parquet(alvo)
    meta = {}
    alvo_meta = pasta / "meta.json"
    if alvo_meta.is_file():
        meta = json.loads(alvo_meta.read_text(encoding="utf-8"))
    return {"dataset": dados, "meta": meta, "pasta": pasta}


def validar_ausencia_de_futuro(pasta: Path) -> dict:
    """Confere que features de cada linha usam apenas dias anteriores.

    Verificação por construção: recalcula as features de uma amostra de
    linhas com o diário truncado no dia de referência e compara.
    """
    pacote = carregar_dataset(pasta)
    dados = pacote["dataset"]
    if dados.height == 0:
        return {"verificado": True, "linhas_conferidas": 0, "divergencias": 0}
    dados_origem = Path(pacote["meta"]["config"]["pasta_dados"])
    tabelas = sintetico.carregar_pacote(dados_origem)["tabelas"]
    feriados = [date.fromisoformat(valor) for valor in tabelas["feriados"]["dia"].drop_nulls().to_list()]
    dias_completos = sorted(tabelas["frequencias"]["dia"].unique().to_list())
    amostra = dados.sample(n=min(200, dados.height), seed=2026)
    divergencias = 0
    conferidas = 0
    for linha in amostra.iter_rows(named=True):
        dia = linha["dia"]
        diario_asof = diario_mod.materializar(tabelas, instante=f"{dia}{FIM_DIA}", ate_dia=dia)
        frame = calculo.calcular(
            diario_asof,
            dia_referencia=dia,
            contexto_mec=tabelas["contexto_mec"],
            feriados=feriados,
            dias_restantes_periodo=sum(1 for d in dias_completos if d > dia),
        ).filter(pl.col("aluno_id") == linha["aluno_id"])
        if frame.height != 1:
            divergencias += 1
            continue
        from frequencia.features.catalogo import NOMES_FEATURES

        for nome in NOMES_FEATURES:
            esperado = float(linha[nome])
            obtido = float(frame[nome][0])
            if abs(esperado - obtido) > 1e-6:
                divergencias += 1
                break
        conferidas += 1
    return {
        "verificado": divergencias == 0,
        "linhas_conferidas": conferidas,
        "divergencias": divergencias,
    }


def dias_para_date(lista: list[str]) -> list[date]:
    """Converte dias ISO em datas civis."""
    return [date.fromisoformat(valor) for valor in lista]
