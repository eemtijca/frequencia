# Esquemas formais das tabelas do domínio, validados com pandera sobre polars.
"""Contratos de dados do FrequenciApp aplicados a cada importação.

Os esquemas seguem docs/modelo-de-dados.md do FrequenciApp, que é soberano:
uma frequência por turma e dia, falta só de aluno na lista da chamada,
saída e entrada únicas por aluno e dia, datas civis em ISO.
"""

from __future__ import annotations

import pandera.polars as pa_pl
import polars as pl
from pandera import Check

from frequencia.dados import catalogos

DATA_ISO = r"^\d{4}-\d{2}-\d{2}$"
MOMENTO_ISO = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$"
HORARIO_HHMM = r"^([01]\d|2[0-3]):[0-5]\d$"

CAMPOS_PROIBIDOS = (
    "cpf",
    "telefone",
    "email",
    "matricula",
    "endereco",
    "nome_mae",
    "data_nascimento",
)

esquema_escolas = pa_pl.DataFrameSchema(
    {
        "escola_id": pa_pl.Column(pl.Utf8, unique=True),
        "nome": pa_pl.Column(pl.Utf8),
        "frequencia_por_aula": pa_pl.Column(pl.Boolean),
        "saida_antecipada": pa_pl.Column(pl.Boolean),
        "origem_na_chamada": pa_pl.Column(pl.Boolean),
    },
    strict=True,
)

esquema_series = pa_pl.DataFrameSchema(
    {
        "serie_id": pa_pl.Column(pl.Utf8, unique=True),
        "escola_id": pa_pl.Column(pl.Utf8),
        "nome": pa_pl.Column(pl.Utf8),
        "ordem": pa_pl.Column(pl.Int64, Check.ge(1)),
    },
    strict=True,
)

esquema_turmas = pa_pl.DataFrameSchema(
    {
        "turma_id": pa_pl.Column(pl.Utf8, unique=True),
        "serie_id": pa_pl.Column(pl.Utf8),
        "escola_id": pa_pl.Column(pl.Utf8),
        "nome": pa_pl.Column(pl.Utf8, Check.str_length(1, 4)),
    },
    strict=True,
)

esquema_alunos = pa_pl.DataFrameSchema(
    {
        "aluno_id": pa_pl.Column(pl.Utf8, unique=True),
        "nome": pa_pl.Column(pl.Utf8, Check.str_length(2, 100)),
        "turma_id": pa_pl.Column(pl.Utf8),
        "turma_original_id": pa_pl.Column(pl.Utf8),
        "ordem": pa_pl.Column(pl.Int64, Check.ge(1)),
        "ativo": pa_pl.Column(pl.Boolean),
        "desistente_em": pa_pl.Column(pl.Utf8, nullable=True, checks=Check.str_matches(DATA_ISO)),
        "transferido_em": pa_pl.Column(pl.Utf8, nullable=True, checks=Check.str_matches(DATA_ISO)),
        "criado_em": pa_pl.Column(pl.Utf8, Check.str_matches(DATA_ISO)),
    },
    strict=True,
)

esquema_horarios = pa_pl.DataFrameSchema(
    {
        "horario_id": pa_pl.Column(pl.Utf8, unique=True),
        "turma_id": pa_pl.Column(pl.Utf8),
        "ordem": pa_pl.Column(pl.Int64, Check.ge(1)),
        "inicio": pa_pl.Column(pl.Utf8, Check.str_matches(HORARIO_HHMM)),
        "fim": pa_pl.Column(pl.Utf8, Check.str_matches(HORARIO_HHMM)),
        "dias_semana": pa_pl.Column(pl.Utf8),
        "ativo": pa_pl.Column(pl.Boolean),
    },
    strict=True,
)

esquema_frequencias = pa_pl.DataFrameSchema(
    {
        "frequencia_id": pa_pl.Column(pl.Utf8, unique=True),
        "turma_id": pa_pl.Column(pl.Utf8),
        "dia": pa_pl.Column(pl.Utf8, checks=Check.str_matches(DATA_ISO)),
        "revisao": pa_pl.Column(pl.Int64, checks=Check.ge(1)),
        "criado_em": pa_pl.Column(pl.Utf8, checks=Check.str_matches(MOMENTO_ISO)),
        "atualizado_em": pa_pl.Column(pl.Utf8, checks=Check.str_matches(MOMENTO_ISO)),
    },
    strict=True,
)

esquema_faltas = pa_pl.DataFrameSchema(
    {
        "falta_id": pa_pl.Column(pl.Utf8, unique=True),
        "frequencia_id": pa_pl.Column(pl.Utf8),
        "aluno_id": pa_pl.Column(pl.Utf8),
        "horario_id": pa_pl.Column(pl.Utf8),
        "justificativa": pa_pl.Column(
            pl.Utf8,
            nullable=True,
            checks=Check.isin(list(catalogos.CODIGOS_JUSTIFICATIVA)),
        ),
        "justificativa_inicial": pa_pl.Column(pl.Utf8, nullable=True),
        "observacao": pa_pl.Column(pl.Utf8, nullable=True),
        "criado_em": pa_pl.Column(pl.Utf8, checks=Check.str_matches(MOMENTO_ISO)),
        "atualizado_em": pa_pl.Column(pl.Utf8, nullable=True, checks=Check.str_matches(MOMENTO_ISO)),
        "removida_em": pa_pl.Column(pl.Utf8, nullable=True, checks=Check.str_matches(MOMENTO_ISO)),
    },
    strict=True,
)

esquema_saidas = pa_pl.DataFrameSchema(
    {
        "saida_id": pa_pl.Column(pl.Utf8, unique=True),
        "aluno_id": pa_pl.Column(pl.Utf8),
        "turma_id": pa_pl.Column(pl.Utf8),
        "dia": pa_pl.Column(pl.Utf8, checks=Check.str_matches(DATA_ISO)),
        "momento": pa_pl.Column(
            pl.Utf8,
            Check.isin(
                [
                    "aula_1",
                    "aula_2",
                    "aula_3",
                    "aula_4",
                    "aula_5",
                    "intervalo_1",
                    "intervalo_2",
                    "almoco",
                ]
            ),
        ),
        "horario": pa_pl.Column(pl.Utf8, nullable=True, checks=Check.str_matches(HORARIO_HHMM)),
        "justificativa": pa_pl.Column(pl.Utf8, nullable=True),
        "texto": pa_pl.Column(pl.Utf8, nullable=True, checks=Check.str_length(0, 100)),
        "liberado_por_codigo": pa_pl.Column(
            pl.Utf8,
            nullable=True,
            checks=Check.isin(list(catalogos.CODIGOS_LIBERADOR)),
        ),
        "criado_em": pa_pl.Column(pl.Utf8, checks=Check.str_matches(MOMENTO_ISO)),
    },
    strict=True,
)

esquema_entradas = pa_pl.DataFrameSchema(
    {
        "entrada_id": pa_pl.Column(pl.Utf8, unique=True),
        "aluno_id": pa_pl.Column(pl.Utf8),
        "turma_id": pa_pl.Column(pl.Utf8),
        "dia": pa_pl.Column(pl.Utf8, checks=Check.str_matches(DATA_ISO)),
        "horario": pa_pl.Column(pl.Utf8, Check.str_matches(HORARIO_HHMM)),
        "momento": pa_pl.Column(pl.Utf8, Check.isin(["aula_1", "aula_2", "aula_3", "pausa"])),
        "motivo": pa_pl.Column(pl.Utf8, nullable=True),
        "responsavel_codigo": pa_pl.Column(pl.Utf8, nullable=True),
        "criado_em": pa_pl.Column(pl.Utf8, checks=Check.str_matches(MOMENTO_ISO)),
    },
    strict=True,
)

esquema_feriados = pa_pl.DataFrameSchema(
    {
        "dia": pa_pl.Column(pl.Utf8, unique=True, checks=Check.str_matches(DATA_ISO)),
        "nome": pa_pl.Column(pl.Utf8, Check.str_length(2, 120)),
        "origem": pa_pl.Column(pl.Utf8, Check.isin(["MANUAL", "API"])),
    },
    strict=True,
)

esquema_contexto_mec = pa_pl.DataFrameSchema(
    {
        "serie_id": pa_pl.Column(pl.Utf8, unique=True),
        "taxa_abandono_historica": pa_pl.Column(pl.Float64, checks=[Check.ge(0), Check.le(1)]),
        "taxa_reprovacao": pa_pl.Column(pl.Float64, checks=[Check.ge(0), Check.le(1)]),
        "distorcao_idade_serie": pa_pl.Column(pl.Float64, checks=[Check.ge(0), Check.le(1)]),
        "ideb": pa_pl.Column(pl.Float64, checks=[Check.ge(0), Check.le(10)]),
    },
    strict=True,
)

ESQUEMAS = {
    "escolas": esquema_escolas,
    "series": esquema_series,
    "turmas": esquema_turmas,
    "alunos": esquema_alunos,
    "horarios": esquema_horarios,
    "frequencias": esquema_frequencias,
    "faltas": esquema_faltas,
    "saidas": esquema_saidas,
    "entradas": esquema_entradas,
    "feriados": esquema_feriados,
    "contexto_mec": esquema_contexto_mec,
}

TABELAS_OBRIGATORIAS = tuple(ESQUEMAS)

# Unicidade composta: verificada em código, por ausência de check nativo no
# backend polars do pandera 0.34 (registrado em ADR-004).
UNICIDADE_COMPOSTA = {
    "frequencias": (("turma_id", "dia"),),
    "faltas": (("frequencia_id", "aluno_id", "horario_id"),),
    "saidas": (("aluno_id", "dia"),),
    "entradas": (("aluno_id", "dia"),),
}


def validar_tabela(nome: str, dados: pl.DataFrame) -> pl.DataFrame:
    """Valida uma tabela contra o esquema formal; falha com erro amigável."""
    if nome not in ESQUEMAS:
        msg = f"Tabela desconhecida: {nome}. Use uma de {sorted(ESQUEMAS)}."
        raise KeyError(msg)
    colunas = set(dados.columns)
    for proibida in CAMPOS_PROIBIDOS:
        if proibida in colunas:
            msg = (
                f"A tabela {nome} contém o campo proibido {proibida}. "
                "Remova o campo antes de importar: dado pessoal não entra no fluxo."
            )
            raise ValueError(msg)
    validado = ESQUEMAS[nome].validate(dados, lazy=True)
    for chaves in UNICIDADE_COMPOSTA.get(nome, ()):
        if validado.n_unique(subset=list(chaves)) != validado.height:
            msg = (
                f"A tabela {nome} tem combinação repetida de {chaves}. "
                "Cada combinação deve aparecer uma única vez."
            )
            raise ValueError(msg)
    return validado


def validar_pacote_tabelas(tabelas: dict[str, pl.DataFrame]) -> dict[str, int]:
    """Valida todas as tabelas obrigatórias e devolve a contagem de linhas."""
    contagens: dict[str, int] = {}
    for nome in TABELAS_OBRIGATORIAS:
        if nome not in tabelas:
            msg = f"Tabela obrigatória ausente: {nome}. Complete o pacote de dados."
            raise ValueError(msg)
        validar_tabela(nome, tabelas[nome])
        contagens[nome] = tabelas[nome].height
    return contagens
