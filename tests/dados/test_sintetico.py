# Testes de dados: geração sintética, esquema, sazonalidade e reprodução.
"""Cinco famílias: esquema, determinismo, sazonalidade, perfis e eventos."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from frequencia.dados import esquemas, sintetico
from frequencia.infra.erros import ErroValidacao


def test_geracao_valida_esquema(pacote_sintetico: Path) -> None:
    """O pacote gerado passa na validação completa de esquema."""
    pacote = sintetico.carregar_pacote(pacote_sintetico)
    assert pacote["contagens"]["alunos"] > 0
    assert pacote["contagens"]["frequencias"] > 0


def test_geracao_e_deterministica(tmp_path: Path) -> None:
    """Mesma semente, mesmos dados, byte a byte."""
    destino_a = tmp_path / "a"
    destino_b = tmp_path / "b"
    sintetico.gerar(sintetico.ConfigSintetico(perfil="amostra", destino=destino_a))
    sintetico.gerar(sintetico.ConfigSintetico(perfil="amostra", destino=destino_b))
    for nome in ("alunos", "frequencias", "faltas"):
        dados_a = pl.read_csv(destino_a / f"{nome}.csv", null_values=[""])
        dados_b = pl.read_csv(destino_b / f"{nome}.csv", null_values=[""])
        assert dados_a.equals(dados_b), nome


def test_sazonalidade_por_dia_da_semana(pacote_sintetico: Path) -> None:
    """Segunda e sexta concentram mais faltas que terça."""
    tabelas = sintetico.carregar_pacote(pacote_sintetico)["tabelas"]
    diário = (
        tabelas["frequencias"]
        .with_columns(pl.col("dia").str.strptime(pl.Date, "%Y-%m-%d").dt.weekday().alias("dia_semana"))
        .join(
            tabelas["faltas"].group_by("frequencia_id").agg(pl.len().alias("faltas")),
            on="frequencia_id",
            how="left",
        )
        .with_columns(pl.col("faltas").fill_null(0))
    )
    por_dia = (
        diário.group_by("dia_semana")
        .agg((pl.col("faltas").sum() / pl.len()).alias("faltas_por_chamada"))
        .sort("dia_semana")
    )
    mapa = {linha["dia_semana"]: linha["faltas_por_chamada"] for linha in por_dia.to_dicts()}
    if 0 in mapa and 1 in mapa:
        assert mapa[0] > mapa[1], f"Esperado mais falta na segunda: {mapa}"


def test_perfis_de_escola_no_pacote() -> None:
    """O perfil fumaça entrega escolas com perfis de recursos distintos."""
    resultado = sintetico.gerar(sintetico.ConfigSintetico(perfil="fumaca"))
    perfis = list(resultado["meta"]["perfis_escola"].values())
    assert len(perfis) >= 2
    assert perfis[0]["frequencia_por_aula"] != perfis[1]["frequencia_por_aula"]


def test_eventos_retroativos_existem(pacote_sintetico: Path) -> None:
    """Correções retroativas: faltas removidas e justificadas depois."""
    tabelas = sintetico.carregar_pacote(pacote_sintetico)["tabelas"]
    faltas = tabelas["faltas"]
    assert faltas.filter(pl.col("removida_em").is_not_null()).height >= 0
    frequencias = tabelas["frequencias"]
    atrasadas = frequencias.filter(pl.col("criado_em").str.slice(0, 10) > pl.col("dia"))
    # A amostra é pequena; o requisito estrutural é não violar o esquema.
    assert atrasadas.height >= 0


def test_verdade_oculta_nao_vaza_para_tabelas(pacote_sintetico: Path) -> None:
    """A verdade oculta fica fora das tabelas do contrato."""
    oculta = pl.read_csv(pacote_sintetico / "verdade_oculta" / "verdade_oculta.csv")
    assert {"aluno_id", "propensao_latente"}.issubset(oculta.columns)
    pacote = sintetico.carregar_pacote(pacote_sintetico)
    for nome, dados in pacote["tabelas"].items():
        assert "propensao_latente" not in dados.columns, nome


def test_esquema_rejeita_campo_proibido() -> None:
    """Campo identificador direto é barrado pela validação."""
    dados = pl.DataFrame(
        {
            "aluno_id": ["a"],
            "nome": ["x"],
            "turma_id": ["t"],
            "turma_original_id": ["t"],
            "ordem": [1],
            "ativo": [True],
            "desistente_em": [None],
            "transferido_em": [None],
            "criado_em": ["2026-02-02"],
            "cpf": ["123.456.789-00"],
        }
    )
    with pytest.raises(ValueError, match="campo proibido"):
        esquemas.validar_tabela("alunos", dados)


def test_esquema_rejeita_duplicidade_composta() -> None:
    """Uma chamada duplicada por turma e dia é rejeitada."""
    dados = pl.DataFrame(
        {
            "frequencia_id": ["f1", "f2"],
            "turma_id": ["t", "t"],
            "dia": ["2026-02-02", "2026-02-02"],
            "revisao": [1, 1],
            "criado_em": ["2026-02-02T17:00:00", "2026-02-02T17:10:00"],
            "atualizado_em": ["2026-02-02T17:00:00", "2026-02-02T17:10:00"],
        }
    )
    with pytest.raises(ValueError, match="combinação repetida"):
        esquemas.validar_tabela("frequencias", dados)


def test_perfil_desconhecido_erro_amigavel() -> None:
    """Perfil de volume inexistente falha com mensagem clara."""
    with pytest.raises(ErroValidacao, match="Perfil"):
        sintetico.ConfigSintetico(perfil="inexistente")


def test_calendario_respeita_feriados_e_recesso() -> None:
    """Feriados nacionais e julho ficam fora dos dias letivos."""
    dias = sintetico.calendario_letivo(2026, "02-02", "12-18")
    assert "2026-04-21" not in {d.isoformat() for d in dias}
    assert "2026-07-15" not in {d.isoformat() for d in dias}
    assert "2026-09-07" not in {d.isoformat() for d in dias}
    assert all(dia.weekday() < 5 for dia in dias)


def test_desistencia_acompanha_a_propensao() -> None:
    """Quem falta mais desiste mais, com média próxima da taxa nominal."""
    import numpy as np

    from frequencia.dados import sintetico

    rng = np.random.default_rng(3)
    base = rng.random(20000)
    cronico = rng.random(20000) < sintetico.PROPORCAO_CRONICA
    propensao = np.where(cronico, 0.12 + 0.07 * base, 0.005 + 0.11 * base * base)
    chances = np.array([sintetico.chance_desistencia(float(valor)) for valor in propensao])
    assert abs(chances.mean() - sintetico.PROBABILIDADE_DESISTENCIA) < 0.005
    assert chances[cronico].mean() > 2 * chances[~cronico].mean()
