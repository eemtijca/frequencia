# Cálculo das features do catálogo sobre o diário, por dia de referência.
"""Engenharia de features temporal com janelas deslizantes e relatividade.

Recebe o diário as-of (features) ou final (avaliação) e um dia de referência
D, e devolve uma linha por aluno presente em D com todas as features do
catálogo na ordem do contrato. Todo o cálculo é vetorial em polars e
determinístico.
"""

from __future__ import annotations

from datetime import date, timedelta

import polars as pl

from frequencia.dados import catalogos
from frequencia.features import calendario
from frequencia.features.catalogo import (
    VOCABULARIO_JUSTIFICATIVA,
    VOCABULARIO_MOMENTO_SAIDA,
)

AGRUPAMENTO_JUSTIFICATIVA = {
    codigo: ("OUTROS" if codigo in catalogos.JUSTIFICATIVAS_RARAS else codigo)
    for codigo in catalogos.CODIGOS_JUSTIFICATIVA
}

INDICE_JUSTIFICATIVA = {
    codigo: VOCABULARIO_JUSTIFICATIVA.index(codigo) for codigo in VOCABULARIO_JUSTIFICATIVA
}

INDICE_MOMENTO = {momento: VOCABULARIO_MOMENTO_SAIDA.index(momento) for momento in VOCABULARIO_MOMENTO_SAIDA}

CAP_PADRAO = 30.0
LIMITE_RECENTE = 30  # linhas (dias letivos) para ordinais recentes


def calcular(
    diario: pl.DataFrame,
    *,
    dia_referencia: str,
    contexto_mec: pl.DataFrame,
    feriados: list[date],
    dias_restantes_periodo: int,
) -> pl.DataFrame:
    """Calcula as features de todos os alunos no dia de referência.

    O diário informado precisa estar filtrado até o dia de referência e
    materializado como o instante desejado (as-of para treino, final para
    avaliação).
    """
    faltou_num = pl.col("faltou").cast(pl.Int32)
    just_num = pl.col("justificada").cast(pl.Int32)
    parcial_num = pl.col("parcial").cast(pl.Int32)
    chamada_num = pl.col("tem_chamada").cast(pl.Int32)
    saida_num = pl.col("tem_saida").cast(pl.Int32)
    entrada_num = pl.col("tem_entrada").cast(pl.Int32)

    base = (
        diario.filter(pl.col("dia") <= dia_referencia)
        .with_row_index("linha_global")
        .with_columns(pl.int_range(pl.len()).over("aluno_id").alias("idx"))
    )

    just_idx = (
        pl.when(pl.col("justificada"))
        .then(_indice_justificativa(pl.col("justificativa_codigo")))
        .otherwise(None)
    )
    momento_idx = pl.when(pl.col("tem_saida")).then(_indice_momento(pl.col("momento_saida"))).otherwise(None)

    janela = base.with_columns(
        faltas_7d=faltou_num.rolling_sum(7, min_samples=1).over("aluno_id"),
        faltas_14d=faltou_num.rolling_sum(14, min_samples=1).over("aluno_id"),
        faltas_30d=faltou_num.rolling_sum(30, min_samples=1).over("aluno_id"),
        faltas_justificadas_30d=just_num.rolling_sum(30, min_samples=1).over("aluno_id"),
        presencas_parciais_30d=parcial_num.rolling_sum(30, min_samples=1).over("aluno_id"),
        dias_com_chamada_30d=chamada_num.rolling_sum(30, min_samples=1).over("aluno_id"),
        chamadas_7d=chamada_num.rolling_sum(7, min_samples=1).over("aluno_id"),
        saidas_30d=saida_num.rolling_sum(30, min_samples=1).over("aluno_id"),
        saidas_7d=saida_num.rolling_sum(7, min_samples=1).over("aluno_id"),
        entradas_atrasadas_30d=entrada_num.rolling_sum(30, min_samples=1).over("aluno_id"),
        entradas_atrasadas_7d=entrada_num.rolling_sum(7, min_samples=1).over("aluno_id"),
        historico_dias=pl.col("idx") + 1,
        ultima_falta_idx=pl.when(pl.col("faltou"))
        .then(pl.col("idx"))
        .otherwise(None)
        .forward_fill()
        .over("aluno_id"),
        ultima_presenca_idx=pl.when(~pl.col("faltou"))
        .then(pl.col("idx"))
        .otherwise(None)
        .forward_fill()
        .over("aluno_id"),
        ultima_saida_idx=pl.when(pl.col("tem_saida"))
        .then(pl.col("idx"))
        .otherwise(None)
        .forward_fill()
        .over("aluno_id"),
        ultimo_just_idx=just_idx.forward_fill().over("aluno_id"),
        ultimo_momento_idx=momento_idx.forward_fill().over("aluno_id"),
        troca_turma_idx=pl.when(pl.col("turma_do_dia") != pl.col("turma_do_dia").shift(1).over("aluno_id"))
        .then(pl.col("idx"))
        .otherwise(None)
        .forward_fill()
        .over("aluno_id"),
    )

    linha = janela.filter(pl.col("dia") == dia_referencia)

    linha = linha.with_columns(
        faltas_consecutivas=pl.col("idx") - pl.col("ultima_presenca_idx").fill_null(-1),
        dias_desde_ultima_falta=(pl.col("idx") - pl.col("ultima_falta_idx").fill_null(-1)).clip(0, 30),
        dias_desde_ultima_saida=(pl.col("idx") - pl.col("ultima_saida_idx").fill_null(-1)).clip(0, 30),
        dias_na_turma_atual=pl.col("idx") - pl.col("troca_turma_idx").fill_null(-1),
        media_movel_faltas_7d=pl.col("faltas_7d") / 7,
        taxa_infrequencia_30d=pl.when(pl.col("dias_com_chamada_30d") > 0)
        .then(pl.col("faltas_30d") / pl.col("dias_com_chamada_30d"))
        .otherwise(0.0),
        cobertura_chamada_7d=pl.col("chamadas_7d") / 7,
        chamada_realizada_no_dia=pl.col("tem_chamada"),
        aluno_novo=pl.col("historico_dias") < 30,
        historico_insuficiente=pl.col("historico_dias") < 10,
    )

    # Relatividade coletiva no mesmo dia de referência.
    linha = linha.with_columns(
        media_faltas_turma_7d=pl.col("faltas_7d").mean().over("turma_do_dia"),
        percentil_bruto=pl.col("faltas_30d").rank("average").over("turma_do_dia")
        / pl.len().over("turma_do_dia"),
        media_serie_30d=pl.col("faltas_30d").mean().over("serie_id"),
    )
    linha = linha.with_columns(
        desvio_faltas_turma_7d=pl.col("faltas_7d") - pl.col("media_faltas_turma_7d"),
        taxa_infrequencia_turma_7d=pl.col("media_faltas_turma_7d") / 7,
        desvio_relativo_serie_30d=pl.when(pl.col("media_serie_30d") > 0)
        .then((pl.col("faltas_30d") - pl.col("media_serie_30d")) / pl.col("media_serie_30d"))
        .otherwise(0.0),
    )

    # Ordinais recentes com limite de janela.
    linha = linha.with_columns(
        justificativa_recente=pl.when(
            pl.col("ultimo_just_idx").is_not_null()
            & ((pl.col("idx") - pl.col("ultimo_just_idx")) < LIMITE_RECENTE)
        )
        .then(pl.col("ultimo_just_idx"))
        .otherwise(0),
        momento_saida_recente=pl.when(
            pl.col("ultimo_momento_idx").is_not_null()
            & ((pl.col("idx") - pl.col("ultimo_momento_idx")) < LIMITE_RECENTE)
        )
        .then(pl.col("ultimo_momento_idx"))
        .otherwise(0),
    )

    # Features de calendário do primeiro dia do horizonte.
    alvo = date.fromisoformat(dia_referencia) + timedelta(days=1)
    seno_semana, cosseno_semana = calendario.ciclo_dia_semana(alvo)
    seno_mes, cosseno_mes = calendario.ciclo_mes(alvo)
    _, fase, dias_fim_bimestre = calendario.mes_para_fase_bimestre(alvo)
    desde_feriado, ate_feriado = calendario.distancias_feriado(alvo, feriados)
    linha = linha.with_columns(
        pl.lit(seno_semana).alias("dia_semana_seno"),
        pl.lit(cosseno_semana).alias("dia_semana_cosseno"),
        pl.lit(seno_mes).alias("mes_seno"),
        pl.lit(cosseno_mes).alias("mes_cosseno"),
        pl.lit(calendario.semana_do_mes(alvo)).alias("semana_do_mes"),
        pl.lit(fase).alias("fase_bimestre"),
        pl.lit(float(dias_fim_bimestre)).alias("dias_ate_fim_bimestre"),
        pl.lit(float(desde_feriado)).alias("dias_desde_feriado"),
        pl.lit(float(ate_feriado)).alias("dias_ate_proximo_feriado"),
        pl.lit(float(dias_restantes_periodo)).alias("dias_ate_fim_periodo_letivo"),
    )

    # Contexto do MEC por série.
    linha = linha.join(
        contexto_mec.select(
            "serie_id",
            pl.col("taxa_abandono_historica").cast(pl.Float64),
            pl.col("taxa_reprovacao").alias("taxa_reprovacao_serie"),
            pl.col("distorcao_idade_serie"),
            pl.col("ideb").alias("ideb_serie"),
        ),
        on="serie_id",
        how="left",
    )

    # Transferência recente: última troca de turma dentro da janela letiva.
    linha = linha.with_columns(
        transferencia_recente=pl.when(pl.col("troca_turma_idx").is_not_null())
        .then((pl.col("idx") - pl.col("troca_turma_idx")) < LIMITE_RECENTE)
        .otherwise(False),
    )
    return _finalizar(linha)


def _indice_justificativa(coluna: pl.Expr) -> pl.Expr:
    """Mapeia o código da justificativa para índice ordinal estável."""
    expressao = pl.lit(INDICE_JUSTIFICATIVA["OUTROS"])
    for codigo, indice in INDICE_JUSTIFICATIVA.items():
        if codigo in ("NENHUMA", "OUTROS"):
            continue
        expressao = pl.when(coluna == codigo).then(pl.lit(indice)).otherwise(expressao)
    return expressao


def _indice_momento(coluna: pl.Expr) -> pl.Expr:
    """Mapeia o momento da saída para índice ordinal estável."""
    expressao = pl.lit(0)
    for momento, indice in INDICE_MOMENTO.items():
        if indice == 0:
            continue
        expressao = pl.when(coluna == momento).then(pl.lit(indice)).otherwise(expressao)
    return expressao


def _finalizar(frame: pl.DataFrame) -> pl.DataFrame:
    """Preenche nulos com os padrões do catálogo e ordena as colunas."""
    from frequencia.features.catalogo import CATALOGO, NOMES_FEATURES

    chaves = ["aluno_id", "dia", "turma_do_dia", "serie_id", "escola_id"]
    ajustes = []
    for spec in CATALOGO:
        if spec.nome not in frame.columns:
            ajustes.append(pl.lit(spec.padrao).cast(pl.Float64).alias(spec.nome))
        else:
            ajustes.append(pl.col(spec.nome).cast(pl.Float64).fill_null(spec.padrao).alias(spec.nome))
    return frame.with_columns(ajustes).select(chaves + list(NOMES_FEATURES))


def montar_vetores(
    features: pl.DataFrame,
) -> tuple[list[list[float]], list[str]]:
    """Extrai a matriz X na ordem do contrato e os identificadores."""
    from frequencia.features.catalogo import NOMES_FEATURES

    matriz = features.select(NOMES_FEATURES).to_numpy()
    identificadores = features["aluno_id"].to_list()
    return matriz.tolist(), identificadores
