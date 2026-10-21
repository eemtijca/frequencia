# Estados de confiança, aquecimento e histerese do alerta.
"""Lógica de confiança espelhada entre Python e o pacote JavaScript.

As constantes e as funções puras desta página entram no manifesto e são
reimplementadas no modelo.js publicado; o teste de paridade garante que as
duas versões entregam o mesmo resultado.
"""

from __future__ import annotations

LIMIARES_CONFIANCA = {
    "sem_historico_min": 0,
    "dados_insuficientes_min": 7,
    "em_observacao_min": 14,
    "confianca_alta_min": 30,
    "cobertura_minima_alta": 0.6,
    "validade_modelo_dias": 180,
    "aquecimento_dias": 30,
}

ESTADOS_CONFIANCA = (
    "sem_historico",
    "dados_insuficientes",
    "em_observacao",
    "confianca_moderada",
    "confianca_alta",
    "modelo_desatualizado",
)

LIMIARES_ALERTA: dict[str, int | float] = {
    "entrada": 0.65,
    "saida": 0.45,
    "dias_consecutivos_entrada": 2,
}

VOCABULARIO_MENSAGENS = {
    "sem_historico": "Sem histórico de chamadas para avaliar o risco.",
    "dados_insuficientes": "Histórico ainda curto: indicador em observação.",
    "em_observacao": "Indicador em observação por pouco histórico.",
    "confianca_moderada": "Indicador com confiança moderada.",
    "confianca_alta": "Indicador com boa confiança.",
    "modelo_desatualizado": "Modelo desatualizado: use o indicador com cautela até a atualização.",
    "alerta_ativo": "Atenção sugerida: acompanhar este estudante na próxima semana.",
    "alerta_encerrado": "Indicador normalizado.",
}


def estado_confianca(
    historico_dias: int,
    *,
    idade_modelo_dias: int = 0,
    cobertura_chamada: float = 1.0,
) -> str:
    """Classifica a confiança do indicador para um estudante num dia."""
    if historico_dias is None or historico_dias <= LIMIARES_CONFIANCA["sem_historico_min"]:
        return "sem_historico"
    if idade_modelo_dias > LIMIARES_CONFIANCA["validade_modelo_dias"]:
        return "modelo_desatualizado"
    if historico_dias < LIMIARES_CONFIANCA["dados_insuficientes_min"]:
        return "dados_insuficientes"
    if historico_dias < LIMIARES_CONFIANCA["em_observacao_min"]:
        return "em_observacao"
    if (
        historico_dias >= LIMIARES_CONFIANCA["confianca_alta_min"]
        and cobertura_chamada >= LIMIARES_CONFIANCA["cobertura_minima_alta"]
    ):
        return "confianca_alta"
    return "confianca_moderada"


def peso_historico(historico_dias: int, aquecimento_dias: int | None = None) -> float:
    """Peso do modelo no aquecimento; o restante vem da taxa base da escola.

    No primeiro mês de uso, a previsão ancora na taxa base observada e ganha
    peso do modelo conforme o histórico acumula.
    """
    dias_aquecimento = (
        LIMIARES_CONFIANCA["aquecimento_dias"] if aquecimento_dias is None else int(aquecimento_dias)
    )
    if historico_dias is None or historico_dias <= 0:
        return 0.0
    return min(1.0, historico_dias / max(1, dias_aquecimento))


def atualizar_alerta(
    probabilidade: float,
    estado_anterior: dict | None,
    *,
    limiar_entrada: float | None = None,
    limiar_saida: float | None = None,
    dias_consecutivos: int | None = None,
) -> dict:
    """Aplica histerese para evitar oscilação diária do alerta.

    O alerta liga após dois dias seguidos acima do limiar de entrada e só
    desliga abaixo do limiar de saída, mais baixo que o de entrada.
    """
    if limiar_entrada is None:
        limiar_entrada = LIMIARES_ALERTA["entrada"]
    if limiar_saida is None:
        limiar_saida = LIMIARES_ALERTA["saida"]
    if dias_consecutivos is None:
        dias_consecutivos = int(LIMIARES_ALERTA["dias_consecutivos_entrada"])

    dias_acima = 0
    em_alerta = False
    if estado_anterior:
        dias_acima = int(estado_anterior.get("dias_acima", 0))
        em_alerta = bool(estado_anterior.get("em_alerta", False))

    acima = probabilidade >= limiar_entrada
    dias_acima = dias_acima + 1 if acima else 0
    if not em_alerta and dias_acima >= dias_consecutivos:
        em_alerta = True
    elif em_alerta and probabilidade < limiar_saida:
        em_alerta = False
        dias_acima = 0
    return {
        "em_alerta": em_alerta,
        "dias_acima": dias_acima,
        "probabilidade": probabilidade,
    }


def combinacao_aquecimento(
    probabilidade_modelo: float,
    taxa_base: float,
    historico_dias: int,
    aquecimento_dias: int | None = None,
) -> float:
    """Mistura a previsão com a taxa base durante o aquecimento."""
    peso = peso_historico(historico_dias, aquecimento_dias)
    valor = peso * probabilidade_modelo + (1 - peso) * taxa_base
    return min(1.0, max(0.0, valor))
