# Diário por aluno e dia, materializado como snapshot temporal (point-in-time).
"""Estado das marcas de frequência em qualquer instante do passado.

A derivação da marca segue docs/modelo-de-dados.md do FrequenciApp, que é
soberano: FJ quando todas as faltas do dia têm justificativa, F quando falta
em todas as aulas, S quando falta parcial no modo por aula, P quando estava
na lista sem falta e vazia quando não havia chamada. Célula vazia é ausência
de frequência, nunca presença (ponto cego 1 do projeto).

O parâmetro instante filtra os eventos conhecidos até um momento: chamadas
salvas com atraso e correções retroativas não contaminam o passado previsto
(ponto cego 4).
"""

from __future__ import annotations

from typing import Any

import polars as pl

COLUNAS_SAIDA = (
    "aluno_id",
    "dia",
    "turma_do_dia",
    "serie_id",
    "escola_id",
    "n_aulas",
    "tem_chamada",
    "marca",
    "faltou",
    "justificada",
    "parcial",
    "justificativa_codigo",
    "tem_saida",
    "momento_saida",
    "tem_entrada",
    "perfil_chamada_por_aula",
    "perfil_saida_antecipada",
    "perfil_origem_na_chamada",
)


def materializar(
    tabelas: dict[str, pl.DataFrame],
    *,
    instante: str | None = None,
    ate_dia: str | None = None,
) -> pl.DataFrame:
    """Materializa o diário de marcas como visível no instante dado.

    instante nulo significa estado final (tudo conhecido), usado para rótulos
    e avaliação. Com instante, o diário reflete apenas o que a coordenação
    via naquele momento, incluindo chamadas salvas com atraso.
    """
    alunos = tabelas["alunos"]
    frequencias = tabelas["frequencias"]
    faltas = tabelas["faltas"]
    horarios = tabelas["horarios"]
    saidas = tabelas["saidas"]
    entradas = tabelas["entradas"]
    turmas = tabelas["turmas"].select("turma_id", "serie_id", "escola_id")
    escolas = tabelas["escolas"].select(
        "escola_id",
        pl.col("frequencia_por_aula").alias("perfil_chamada_por_aula"),
        pl.col("saida_antecipada").alias("perfil_saida_antecipada"),
        pl.col("origem_na_chamada").alias("perfil_origem_na_chamada"),
    )

    limite = ate_dia or frequencias["dia"].max()
    dias = frequencias.select(pl.col("dia").unique()).filter(pl.col("dia") <= limite).sort("dia")

    grade = horarios.filter(pl.col("ativo")).group_by("turma_id").agg(pl.len().alias("n_aulas"))

    chamadas = frequencias.filter(pl.col("dia") <= limite)
    if instante is not None:
        chamadas = chamadas.filter(pl.col("criado_em") <= instante)
    chamadas = chamadas.select("frequencia_id", "turma_id", "dia", "criado_em")

    base_faltas = faltas.join(
        chamadas.select("frequencia_id", "turma_id", "dia"),
        on="frequencia_id",
        how="inner",
    )
    if instante is not None:
        base_faltas = base_faltas.filter(
            (pl.col("criado_em") <= instante)
            & (pl.col("removida_em").is_null() | (pl.col("removida_em") > instante))
        )
        base_faltas = base_faltas.with_columns(
            pl.when(pl.col("atualizado_em").is_null() | (pl.col("atualizado_em") <= instante))
            .then(pl.col("justificativa"))
            .otherwise(pl.col("justificativa_inicial"))
            .alias("justificativa_asof")
        )
    else:
        base_faltas = base_faltas.with_columns(pl.col("justificativa").alias("justificativa_asof"))

    resumo_faltas = (
        base_faltas.sort("falta_id")
        .group_by("aluno_id", "dia")
        .agg(
            pl.len().alias("n_faltas"),
            (pl.col("justificativa_asof").is_not_null()).sum().alias("n_justificadas"),
            pl.col("justificativa_asof").drop_nulls().first().alias("justificativa_codigo"),
        )
    )

    resumo_saidas = saidas.filter(pl.col("dia") <= limite)
    if instante is not None:
        resumo_saidas = resumo_saidas.filter(pl.col("criado_em") <= instante)
    resumo_saidas = resumo_saidas.select("aluno_id", "dia", pl.col("momento").alias("momento_saida"))

    resumo_entradas = entradas.filter(pl.col("dia") <= limite)
    if instante is not None:
        resumo_entradas = resumo_entradas.filter(pl.col("criado_em") <= instante)
    resumo_entradas = resumo_entradas.select("aluno_id", "dia", pl.lit(True).alias("tem_entrada"))

    return (
        alunos.select(
            "aluno_id",
            "nome",
            "turma_id",
            "turma_original_id",
            "criado_em",
            "desistente_em",
            "transferido_em",
        )
        .join(dias, how="cross")
        .filter(
            (pl.col("criado_em") <= pl.col("dia"))
            & (pl.col("desistente_em").is_null() | (pl.col("dia") < pl.col("desistente_em")))
        )
        .with_columns(
            pl.when(pl.col("transferido_em").is_not_null() & (pl.col("dia") >= pl.col("transferido_em")))
            .then(pl.col("turma_id"))
            .otherwise(pl.col("turma_original_id"))
            .alias("turma_do_dia")
        )
        .join(turmas, left_on="turma_do_dia", right_on="turma_id", how="left")
        .join(escolas, on="escola_id", how="left")
        .join(grade, left_on="turma_do_dia", right_on="turma_id", how="left")
        .join(
            chamadas.select("turma_id", "dia", pl.lit(True).alias("tem_chamada")),
            left_on=["turma_do_dia", "dia"],
            right_on=["turma_id", "dia"],
            how="left",
        )
        .join(resumo_faltas, on=["aluno_id", "dia"], how="left")
        .join(resumo_saidas, on=["aluno_id", "dia"], how="left")
        .join(resumo_entradas, on=["aluno_id", "dia"], how="left")
        .with_columns(
            pl.col("tem_chamada").fill_null(False),
            pl.col("n_faltas").fill_null(0),
            pl.col("n_justificadas").fill_null(0),
            pl.col("n_aulas").fill_null(1),
            pl.col("tem_entrada").fill_null(False),
        )
        .with_columns(marca=_derivar_marca())
        .with_columns(
            pl.col("marca").is_in(["F", "FJ"]).alias("faltou"),
            (pl.col("marca") == "FJ").alias("justificada"),
            (pl.col("marca") == "S").alias("parcial"),
            pl.col("momento_saida").is_not_null().alias("tem_saida"),
        )
        .select(COLUNAS_SAIDA)
        .sort("aluno_id", "dia")
    )


def _derivar_marca() -> pl.Expr:
    """Deriva a marca do dia conforme o documento soberano de dados."""
    return (
        pl.when(~pl.col("tem_chamada"))
        .then(pl.lit("vazia"))
        .when(pl.col("n_faltas") == 0)
        .then(pl.lit("P"))
        .when(pl.col("n_justificadas") >= pl.col("n_faltas"))
        .then(pl.lit("FJ"))
        .when(pl.col("n_faltas") >= pl.col("n_aulas"))
        .then(pl.lit("F"))
        .otherwise(pl.lit("S"))
    )


def resumo_por_marca(diario: pl.DataFrame) -> dict[str, Any]:
    """Contagem de células por marca, para painéis e verificação de contrato."""
    contagens = diario.group_by("marca").agg(pl.len().alias("celulas")).sort("marca")
    return {linha["marca"]: linha["celulas"] for linha in contagens.to_dicts()}
