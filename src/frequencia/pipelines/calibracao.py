# Calibração regularizada, predição conforme Mondrian e curva de aprendizado.
"""Confiança estatística da saída do modelo.

Três camadas: Platt escalado com prior em direção à identidade (pouca
evidência não deforma a saída, muita evidência corrige o que precisar),
encolhimento para a taxa base durante o aquecimento, e predição conforme
Mondrian por série e faixa de histórico. Tudo é ajustado uma única vez, no
conjunto de calibração, sobre a saída do estudante destilado: o mesmo
preditor que o modelo.js publica (ADR-020).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Força do prior de Platt em pseudo-observações: a perda é somada, não
# média, então o prior pesa como cerca de cem linhas de dados e perde
# importância à medida que a evidência cresce (ADR-020).
LAMBDA_PLATT = 10.0
NIVEL_CONFORMAL = 0.90
FAIXAS_HISTORICO = (0, 14, 30, 10**6)
NOMES_FAIXAS = ("curto", "medio", "longo")


@dataclass
class AjusteCalibracao:
    """Parâmetros calibrados, serializáveis no manifesto do modelo."""

    a_platt: float
    b_platt: float
    lambda_platt: float
    taxa_base: float
    nivel_conformal: float
    quantis_conformal: dict[str, float]
    cobertura_por_grupo: dict[str, float]
    ece_antes: float
    ece_depois: float

    def para_dict(self) -> dict:
        return {
            "a_platt": round(self.a_platt, 6),
            "b_platt": round(self.b_platt, 6),
            "lambda_platt": self.lambda_platt,
            "taxa_base": round(self.taxa_base, 6),
            "nivel_conformal": self.nivel_conformal,
            "quantis_conformal": {chave: round(valor, 6) for chave, valor in self.quantis_conformal.items()},
            "cobertura_por_grupo": {
                chave: round(valor, 4) for chave, valor in self.cobertura_por_grupo.items()
            },
            "ece_antes": round(self.ece_antes, 4),
            "ece_depois": round(self.ece_depois, 4),
        }


def _logit(p: np.ndarray) -> np.ndarray:
    estavel = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(estavel / (1 - estavel))


def aplicar_platt(p: np.ndarray, a: float, b: float) -> np.ndarray:
    """Aplica o escalonamento de Platt em espaço logit."""
    return 1.0 / (1.0 + np.exp(-(a * _logit(p) + b)))


def ajustar_platt(
    probabilidades: np.ndarray, rotulos: np.ndarray, *, lam: float = LAMBDA_PLATT
) -> tuple[float, float]:
    """Ajusta (a, b) com perda logística e prior em direção à identidade.

    A identidade é a=1 e b=0. O objetivo é a perda somada mais
    lam((a-1)² + b²), escrito como média com o prior dividido por n para
    manter a escala numérica: com poucas linhas o prior domina e a saída
    quase não se move; com muitas, os dados decidem. Somar o prior à perda
    média, como antes, congelava a calibração na identidade para qualquer n.
    """
    from scipy.optimize import minimize

    z = _logit(np.asarray(probabilidades, dtype=float))
    y = np.asarray(rotulos, dtype=float)

    def objetivo(theta):
        a, b = theta
        escore = a * z + b
        # Perda logística estável.
        perda = np.mean(np.logaddexp(0, -escore) + (1 - y) * escore)
        regularizacao = lam / max(1, len(y)) * ((a - 1.0) ** 2 + b**2)
        return perda + regularizacao

    resultado = minimize(
        objetivo,
        x0=np.array([1.0, 0.0]),
        method="L-BFGS-B",
        bounds=[(0.2, 5.0), (-3.0, 3.0)],
    )
    a, b = resultado.x
    return float(a), float(b)


def _erro_calibracao_esperado(probabilidades: np.ndarray, rotulos: np.ndarray, bins: int = 10) -> float:
    """Erro de calibração esperado (ECE) com bins de igual largura."""
    y = np.asarray(rotulos, dtype=float)
    p = np.clip(np.asarray(probabilidades, dtype=float), 0, 1)
    bordas = np.linspace(0, 1, bins + 1)
    total = max(1, len(y))
    erro = 0.0
    for indice in range(bins):
        mascara = (p > bordas[indice]) & (p <= bordas[indice + 1])
        if mascara.sum() == 0:
            continue
        media_p = p[mascara].mean()
        media_y = y[mascara].mean()
        erro += mascara.sum() / total * abs(media_y - media_p)
    return float(erro)


def prever_publicado(
    bruto: np.ndarray,
    a: float,
    b: float,
    taxa_base: float,
    historico: np.ndarray,
    aquecimento_dias: int | None = None,
) -> np.ndarray:
    """Probabilidade final, vetorizada, com a semântica exata do modelo.js.

    Platt sobre a saída do núcleo, depois mistura com a taxa base pelo peso
    min(1, histórico/aquecimento). Calibração, conformal e avaliação usam
    esta função para medir o preditor que vai para o navegador.
    """
    from frequencia.features.confianca import LIMIARES_CONFIANCA

    dias = LIMIARES_CONFIANCA["aquecimento_dias"] if aquecimento_dias is None else aquecimento_dias
    calibrada = aplicar_platt(np.clip(np.asarray(bruto, dtype=float), 1e-6, 1 - 1e-6), a, b)
    peso = np.clip(np.asarray(historico, dtype=float) / max(1, dias), 0.0, 1.0)
    return np.clip(peso * calibrada + (1 - peso) * taxa_base, 0.0, 1.0)


def ajustar(
    bruto: np.ndarray,
    rotulos: np.ndarray,
    series: list[str] | None,
    historico: np.ndarray,
    *,
    lam: float = LAMBDA_PLATT,
    nivel: float = NIVEL_CONFORMAL,
) -> AjusteCalibracao:
    """Ajusta Platt e os quantis conformes sobre o conjunto de calibração.

    bruto é a saída do núcleo publicado (o estudante) em linhas que ele não
    viu no treino; os quantis conformes usam a probabilidade final, depois
    do Platt e do aquecimento.
    """
    p = np.clip(np.asarray(bruto, dtype=float), 1e-6, 1 - 1e-6)
    y = np.asarray(rotulos, dtype=float)
    a, b = ajustar_platt(p, y, lam=lam)
    taxa_base = float(y.mean())
    calibradas = prever_publicado(p, a, b, taxa_base, np.asarray(historico, dtype=float))

    if series is None:
        series = ["geral"] * len(y)
    faixas = np.digitize(historico, FAIXAS_HISTORICO[1:-1])
    grupos: dict[str, list[int]] = {}
    for posicao, (serie, faixa) in enumerate(zip(series, faixas, strict=True)):
        chave = f"{serie}|{NOMES_FAIXAS[min(faixa, len(NOMES_FAIXAS) - 1)]}"
        grupos.setdefault(chave, []).append(posicao)

    quantis: dict[str, float] = {}
    cobertura: dict[str, float] = {}
    residuo = np.abs(y - calibradas)
    for chave, posicoes in grupos.items():
        if len(posicoes) < 8:
            quantis[chave] = 0.5
            cobertura[chave] = 1.0
            continue
        quantis[chave] = _quantil_conforme(residuo[posicoes], nivel)
        dentro = residuo[posicoes] <= quantis[chave]
        cobertura[chave] = float(dentro.mean())

    return AjusteCalibracao(
        a_platt=a,
        b_platt=b,
        lambda_platt=lam,
        taxa_base=taxa_base,
        nivel_conformal=nivel,
        quantis_conformal=quantis,
        cobertura_por_grupo=cobertura,
        ece_antes=_erro_calibracao_esperado(p, y),
        ece_depois=_erro_calibracao_esperado(calibradas, y),
    )


def _quantil_conforme(residuos: np.ndarray, nivel: float) -> float:
    """Quantil conforme com correção de amostra finita.

    Garante cobertura de nível pedido sob trocabilidade: usa o posto
    ceil((n+1)(1-alfa)) dos resíduos ordenados.
    """
    import math

    n = len(residuos)
    if n == 0:
        return 0.5
    alfa = max(0.0, min(0.5, 1 - nivel))
    posto = min(math.ceil((n + 1) * (1 - alfa)), n)
    ordenados = np.sort(residuos)
    return float(ordenados[posto - 1])


def intervalo_conformal(
    probabilidade: float,
    chave_grupo: str,
    quantis: dict[str, float],
) -> tuple[float, float]:
    """Intervalo conforme para uma previsão calibrada."""
    largura = quantis.get(chave_grupo, 0.5)
    return (
        max(0.0, probabilidade - largura),
        min(1.0, probabilidade + largura),
    )


def chave_grupo(serie: str, historico_dias: int) -> str:
    """Chave do grupo Mondrian: série e faixa de histórico."""
    if historico_dias < FAIXAS_HISTORICO[1]:
        faixa = NOMES_FAIXAS[0]
    elif historico_dias < FAIXAS_HISTORICO[2]:
        faixa = NOMES_FAIXAS[1]
    else:
        faixa = NOMES_FAIXAS[2]
    return f"{serie}|{faixa}"


def curva_aprendizado(
    probabilidades: np.ndarray,
    rotulos: np.ndarray,
    historico: np.ndarray,
    *,
    bins: tuple[int, ...] = (10, 20, 30, 45, 60, 90, 120),
) -> list[dict]:
    """AUC e volume por faixa de histórico disponível."""
    from sklearn.metrics import roc_auc_score

    p = np.asarray(probabilidades, dtype=float)
    y = np.asarray(rotulos, dtype=int)
    h = np.asarray(historico, dtype=float)
    pontos: list[dict] = []
    anterior = 0
    for limite in bins:
        mascara = (h > anterior) & (h <= limite)
        if mascara.sum() >= 30 and len(np.unique(y[mascara])) == 2:
            pontos.append(
                {
                    "faixa": f"{anterior + 1} a {limite} dias",
                    "linhas": int(mascara.sum()),
                    "auc": round(float(roc_auc_score(y[mascara], p[mascara])), 4),
                }
            )
        anterior = limite
    return pontos
