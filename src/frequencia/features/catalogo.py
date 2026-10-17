# Catálogo versionado de features: o contrato entre treino e inferência.
"""Declaração formal de todas as features do modelo de risco.

Cada feature documenta nome técnico, nome amigável, tipo, unidade, janela,
origem, sensibilidade, cálculo no navegador, dependência de configuração do
FrequenciApp e valor padrão. O catálogo é a fonte da verdade compartilhada
entre o pipeline de treino e o pacote de inferência publicado.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

VERSAO_CATALOGO = "1.0.0"

# Vocabulários estáveis de ordinais: a posição na lista é o valor do modelo.
VOCABULARIO_JUSTIFICATIVA = (
    "NENHUMA",
    "D",
    "Dat",
    "T",
    "Vi",
    "CM",
    "De",
    "O",
    "OUTROS",
)
VOCABULARIO_MOMENTO_SAIDA = (
    "NENHUM",
    "aula_1",
    "aula_2",
    "aula_3",
    "aula_4",
    "aula_5",
    "intervalo_1",
    "intervalo_2",
    "almoco",
)


@dataclass(frozen=True)
class EspecificacaoFeature:
    """Contrato de uma feature do modelo."""

    nome: str
    nome_amigavel: str
    tipo: str  # numerico | ordinal | binario
    grupo: str
    unidade: str
    origem: str  # app | mec | calendario
    janela: str = "nenhuma"
    sensibilidade: str = "baixa"
    calculavel_no_navegador: bool = True
    dependencia: str | None = None  # flag da configuração do FrequenciApp
    padrao: float = 0.0
    vocabulario: tuple[str, ...] | None = None
    descricao: str = ""

    def para_dict(self) -> dict[str, Any]:
        corpo = {
            "nome": self.nome,
            "nome_amigavel": self.nome_amigavel,
            "tipo": self.tipo,
            "grupo": self.grupo,
            "unidade": self.unidade,
            "origem": self.origem,
            "janela": self.janela,
            "sensibilidade": self.sensibilidade,
            "calculavel_no_navegador": self.calculavel_no_navegador,
            "dependencia": self.dependencia,
            "padrao": self.padrao,
            "descricao": self.descricao,
        }
        if self.vocabulario:
            corpo["vocabulario"] = list(self.vocabulario)
        return corpo


def _f(
    nome: str,
    amigavel: str,
    grupo: str,
    unidade: str,
    origem: str = "app",
    janela: str = "nenhuma",
    dependencia: str | None = None,
    padrao: float = 0.0,
    descricao: str = "",
) -> EspecificacaoFeature:
    """Construtor encurtado para features numéricas de janela."""
    return EspecificacaoFeature(
        nome=nome,
        nome_amigavel=amigavel,
        tipo="numerico",
        grupo=grupo,
        unidade=unidade,
        origem=origem,
        janela=janela,
        dependencia=dependencia,
        padrao=padrao,
        descricao=descricao,
    )


CATALOGO: tuple[EspecificacaoFeature, ...] = (
    # Histórico de faltas do aluno.
    _f(
        "faltas_7d",
        "Faltas nos últimos 7 dias letivos",
        "faltas",
        "dias",
        janela="7d",
        descricao="Dias com marca F ou FJ nos 7 dias letivos anteriores à referência.",
    ),
    _f("faltas_14d", "Faltas nos últimos 14 dias letivos", "faltas", "dias", janela="14d"),
    _f("faltas_30d", "Faltas nos últimos 30 dias letivos", "faltas", "dias", janela="30d"),
    _f(
        "faltas_consecutivas",
        "Faltas consecutivas até a referência",
        "faltas",
        "dias",
        descricao="Sequência atual de dias letivos seguidos com falta.",
    ),
    _f(
        "faltas_justificadas_30d",
        "Faltas justificadas em 30 dias",
        "faltas",
        "dias",
        janela="30d",
        descricao="Dias com marca FJ nos últimos 30 dias letivos.",
    ),
    _f(
        "proporcao_fj_30d",
        "Proporção de faltas justificadas",
        "faltas",
        "fração",
        janela="30d",
        padrao=0.0,
        descricao="FJ dividido por F mais FJ em 30 dias; zero sem faltas.",
    ),
    _f("dias_desde_ultima_falta", "Dias letivos desde a última falta", "faltas", "dias", padrao=30.0),
    _f("media_movel_faltas_7d", "Média móvel de faltas (7 dias)", "faltas", "faltas/dia", janela="7d"),
    _f(
        "taxa_infrequencia_30d",
        "Taxa de infrequência em 30 dias",
        "faltas",
        "fração",
        janela="30d",
        descricao="Faltas em 30 dias dividido pelos dias com chamada em 30 dias.",
    ),
    _f(
        "presencas_parciais_30d",
        "Presenças parciais (S) em 30 dias",
        "faltas",
        "dias",
        janela="30d",
        dependencia="frequencia_por_aula",
        descricao="Dias com marca S; exige chamada por aula ligada.",
    ),
    # Saídas e entradas.
    _f(
        "saidas_30d",
        "Saídas antecipadas em 30 dias",
        "saidas",
        "registros",
        janela="30d",
        dependencia="saida_antecipada",
        padrao=0.0,
    ),
    _f(
        "saidas_7d",
        "Saídas antecipadas em 7 dias",
        "saidas",
        "registros",
        janela="7d",
        dependencia="saida_antecipada",
    ),
    _f(
        "dias_desde_ultima_saida",
        "Dias letivos desde a última saída",
        "saidas",
        "dias",
        dependencia="saida_antecipada",
        padrao=30.0,
    ),
    _f(
        "entradas_atrasadas_30d",
        "Entradas atrasadas em 30 dias",
        "saidas",
        "registros",
        janela="30d",
        dependencia="saida_antecipada",
    ),
    _f(
        "entradas_atrasadas_7d",
        "Entradas atrasadas em 7 dias",
        "saidas",
        "registros",
        janela="7d",
        dependencia="saida_antecipada",
    ),
    # Comparação com a coletividade.
    _f("media_faltas_turma_7d", "Média de faltas da turma (7 dias)", "coletivo", "dias", janela="7d"),
    _f("desvio_faltas_turma_7d", "Desvio do aluno frente à turma", "coletivo", "dias", janela="7d"),
    _f(
        "percentil_faltas_turma_30d",
        "Posição do aluno na turma",
        "coletivo",
        "percentil",
        janela="30d",
        padrao=0.5,
    ),
    _f("taxa_infrequencia_turma_7d", "Taxa de infrequência da turma", "coletivo", "fração", janela="7d"),
    _f("desvio_relativo_serie_30d", "Desvio relativo frente à série", "coletivo", "fração", janela="30d"),
    # Cobertura de chamada e estrutura.
    _f("dias_com_chamada_30d", "Dias com chamada registrada em 30 dias", "estrutura", "dias", janela="30d"),
    _f("cobertura_chamada_7d", "Cobertura de chamada em 7 dias", "estrutura", "fração", janela="7d"),
    _f("chamada_realizada_no_dia", "Chamada do dia de referência realizada", "estrutura", "binário"),
    _f("historico_dias", "Dias letivos de histórico do aluno", "estrutura", "dias"),
    _f("aluno_novo", "Aluno matriculado há menos de 30 dias", "estrutura", "binário"),
    _f("transferencia_recente", "Transferência nos últimos 30 dias letivos", "estrutura", "binário"),
    _f("dias_na_turma_atual", "Dias letivos na turma atual", "estrutura", "dias"),
    _f("historico_insuficiente", "Histórico abaixo do mínimo de treino", "estrutura", "binário"),
    _f("perfil_chamada_por_aula", "Escola com chamada por aula ligada", "perfil", "binário"),
    _f("perfil_saida_antecipada", "Escola com saídas antecipadas ligadas", "perfil", "binário"),
    _f("perfil_origem_na_chamada", "Escola com origem na chamada ligada", "perfil", "binário"),
    # Calendário e sazonalidade.
    _f("dia_semana_seno", "Dia da semana (seno)", "calendario", "adimensional", origem="calendario"),
    _f("dia_semana_cosseno", "Dia da semana (cosseno)", "calendario", "adimensional", origem="calendario"),
    _f("mes_seno", "Mês (seno)", "calendario", "adimensional", origem="calendario"),
    _f("mes_cosseno", "Mês (cosseno)", "calendario", "adimensional", origem="calendario"),
    _f("semana_do_mes", "Semana dentro do mês", "calendario", "índice", origem="calendario"),
    _f("fase_bimestre", "Fase do bimestre", "calendario", "fração", origem="calendario"),
    _f("dias_ate_fim_bimestre", "Dias até o fim do bimestre", "calendario", "dias", origem="calendario"),
    _f(
        "dias_desde_feriado",
        "Dias desde o último feriado",
        "calendario",
        "dias",
        origem="calendario",
        padrao=15.0,
    ),
    _f(
        "dias_ate_proximo_feriado",
        "Dias até o próximo feriado",
        "calendario",
        "dias",
        origem="calendario",
        padrao=15.0,
    ),
    _f(
        "dias_ate_fim_periodo_letivo",
        "Dias letivos até o fim do período",
        "calendario",
        "dias",
        origem="calendario",
    ),
    # Contexto agregado do MEC.
    _f("taxa_abandono_historica", "Taxa histórica de abandono da série", "mec", "fração", origem="mec"),
    _f("taxa_reprovacao_serie", "Taxa de reprovação da série", "mec", "fração", origem="mec"),
    _f("distorcao_idade_serie", "Distorção idade-série", "mec", "fração", origem="mec"),
    _f("ideb_serie", "IDEB da série", "mec", "índice", origem="mec"),
    # Ordinais de catálogo.
    EspecificacaoFeature(
        nome="justificativa_recente",
        nome_amigavel="Justificativa mais recente do aluno",
        tipo="ordinal",
        grupo="ordinais",
        unidade="código",
        origem="app",
        janela="30d",
        sensibilidade="media",
        padrao=0.0,
        vocabulario=VOCABULARIO_JUSTIFICATIVA,
        descricao="Última justificativa de falta em 30 dias; códigos raros agrupados em OUTROS.",
    ),
    EspecificacaoFeature(
        nome="momento_saida_recente",
        nome_amigavel="Momento da saída mais recente",
        tipo="ordinal",
        grupo="ordinais",
        unidade="código",
        origem="app",
        janela="30d",
        dependencia="saida_antecipada",
        padrao=0.0,
        vocabulario=VOCABULARIO_MOMENTO_SAIDA,
        descricao="Momento da última saída antecipada em 30 dias; NENHUM sem registro.",
    ),
)

NOMES_FEATURES = tuple(feat.nome for feat in CATALOGO)


def catalogo_por_grupo() -> dict[str, list[EspecificacaoFeature]]:
    """Agrupa as features por família de cálculo."""
    grupos: dict[str, list[EspecificacaoFeature]] = {}
    for feat in CATALOGO:
        grupos.setdefault(feat.grupo, []).append(feat)
    return grupos


def feature(nome: str) -> EspecificacaoFeature:
    """Localiza a especificação de uma feature pelo nome técnico."""
    for feat in CATALOGO:
        if feat.nome == nome:
            return feat
    msg = f"Feature desconhecida: {nome}. Consulte o catálogo em features/catalogo.py."
    raise KeyError(msg)


def validar_contrato() -> dict:
    """Verifica integridade do catálogo: nomes únicos, tipos e vocabulários."""
    nomes = [feat.nome for feat in CATALOGO]
    duplicadas = {nome for nome in nomes if nomes.count(nome) > 1}
    problemas = []
    if duplicadas:
        problemas.append(f"Nomes duplicados: {sorted(duplicadas)}.")
    for feat in CATALOGO:
        if feat.tipo not in ("numerico", "ordinal", "binario"):
            problemas.append(f"Tipo inválido em {feat.nome}: {feat.tipo}.")
        if feat.tipo == "ordinal" and not feat.vocabulario:
            problemas.append(f"Ordinal sem vocabulário: {feat.nome}.")
        if feat.dependencia not in (None, "frequencia_por_aula", "saida_antecipada", "origem_na_chamada"):
            problemas.append(f"Dependência desconhecida em {feat.nome}: {feat.dependencia}.")
    if problemas:
        msg = "Contrato de features inválido: " + " ".join(problemas)
        raise ValueError(msg)
    return {
        "versao": VERSAO_CATALOGO,
        "total": len(CATALOGO),
        "grupos": {grupo: len(feats) for grupo, feats in catalogo_por_grupo().items()},
        "valido": True,
    }


def exportar_json() -> dict:
    """Exporta o catálogo completo como dicionário serializável."""
    return {
        "versao": VERSAO_CATALOGO,
        "features": [feat.para_dict() for feat in CATALOGO],
    }


def dependentes_de_configuracao() -> dict[str, list[str]]:
    """Mapa de flag do FrequenciApp para features que dela dependem."""
    mapa: dict[str, list[str]] = {}
    for feat in CATALOGO:
        if feat.dependencia:
            mapa.setdefault(feat.dependencia, []).append(feat.nome)
    return mapa
