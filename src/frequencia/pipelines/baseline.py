# Baseline de regras: score determinístico espelhável no navegador.
"""Modelo de referência por regras, usado no ensemble e no fallback.

A pontuação é uma soma ponderada legível de sinais de infrequência, passada
por uma sigmoide. A mesma fórmula vive no fallback.js do pacote publicado; o
teste de paridade confere as duas versões.
"""

from __future__ import annotations

from numpy import ndarray

PESOS_REGRAS = {
    "faltas_7d": 1.1,
    "faltas_consecutivas": 0.9,
    "faltas_30d": 0.12,
    "recencia_ultima_falta": 0.55,
    "media_movel_faltas_7d": 0.8,
    "taxa_infrequencia_30d": 1.2,
    "saidas_30d": 0.18,
    "entradas_atrasadas_30d": 0.15,
    "desvio_faltas_turma_7d": 0.25,
    "chamada_realizada_no_dia_off": -0.35,
    "historico_dias": 0.004,
    "taxa_abandono_historica": 1.5,
}
VIÉS_REGRAS = -3.2


def pontuar(x: ndarray | list[list[float]], ordem: list[str] | None = None) -> ndarray:
    """Pontua amostras com as regras; colunas na ordem do catálogo.

    Espera colunas na ordem NOMES_FEATURES; a ordem explícita permite uso em
    cenários de teste com subconjuntos.
    """
    import numpy as np

    if ordem is None:
        from frequencia.features.catalogo import NOMES_FEATURES

        ordem = list(NOMES_FEATURES)
    indice = {nome: posicao for posicao, nome in enumerate(ordem)}
    matriz = np.asarray(x, dtype=float)
    escore = np.full(matriz.shape[0], VIÉS_REGRAS, dtype=float)
    for nome, peso in PESOS_REGRAS.items():
        if nome == "recencia_ultima_falta":
            coluna = matriz[:, indice["dias_desde_ultima_falta"]]
            escore += peso * (30.0 - coluna) / 30.0
            continue
        if nome == "chamada_realizada_no_dia_off":
            escore += peso * (1.0 - matriz[:, indice["chamada_realizada_no_dia"]])
            continue
        escore += peso * matriz[:, indice[nome]]
    return 1.0 / (1.0 + np.exp(-escore))


def descrever() -> list[str]:
    """Descreve as regras em linguagem clara, para cartão e documentação."""
    return [
        "Cada falta nos últimos 7 dias soma 1,1 ponto; a sequência consecutiva soma 0,9 por dia.",
        "A taxa de infrequência em 30 dias soma 1,2 ponto quando cheia; o desvio frente à turma soma 0,25.",
        "Quanto mais recente a última falta, maior o acréscimo, até 0,55 ponto.",
        "Saídas e entradas recentes somam 0,18 e 0,15 por registro; chamada ausente no dia desconta 0,35.",
        "O contexto do MEC entra com 1,5 ponto na taxa histórica de abandono da série.",
        "A soma passa por uma sigmoide com viés de -3,2, o que mantém o risco base baixo.",
    ]
