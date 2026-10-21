# Calibração regularizada, predição conforme Mondrian e curva de aprendizado.
"""Confiança estatística da saída do modelo.

Três camadas: Platt escalado com prior em direção à identidade (pouca
evidência não deforma a saída, muita evidência corrige o que precisar),
encolhimento para a taxa base durante o aquecimento, e conjuntos de
predição conformes Mondrian por série, faixa de histórico e classe
(ADR-021). Tudo é ajustado uma única vez, no
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
# Mínimo de linhas de uma classe num grupo para estimar o limiar conforme;
# abaixo disso o grupo devolve o conjunto completo {0, 1}, sem informação.
MINIMO_POR_CLASSE = 20
METODO_CONFORMAL = "conjuntos_mondrian_por_classe"
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
    limiares_conformal: dict[str, dict[str, float]]
    linhas_por_grupo: dict[str, dict[str, int]]
    ece_antes: float
    ece_depois: float

    def para_dict(self) -> dict:
        return {
            "a_platt": round(self.a_platt, 6),
            "b_platt": round(self.b_platt, 6),
            "lambda_platt": self.lambda_platt,
            "taxa_base": round(self.taxa_base, 6),
            "nivel_conformal": self.nivel_conformal,
            "metodo_conformal": METODO_CONFORMAL,
            "limiares_conformal": {
                chave: {classe: round(valor, 6) for classe, valor in limiar.items()}
                for chave, limiar in self.limiares_conformal.items()
            },
            "linhas_por_grupo": self.linhas_por_grupo,
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
        if indice == 0:
            mascara |= p == 0.0
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
    """Ajusta Platt e os conjuntos conformes sobre o conjunto de calibração.

    bruto é a saída do núcleo publicado (o estudante) em linhas que ele não
    viu no treino; os conjuntos conformes usam a probabilidade final, depois
    do Platt e do aquecimento.
    """
    p = np.clip(np.asarray(bruto, dtype=float), 1e-6, 1 - 1e-6)
    y = np.asarray(rotulos, dtype=float)
    a, b = ajustar_platt(p, y, lam=lam)
    taxa_base = float(y.mean())
    calibradas = prever_publicado(p, a, b, taxa_base, np.asarray(historico, dtype=float))

    if series is None:
        series = ["geral"] * len(y)
    chaves = [chave_grupo(serie, int(dias)) for serie, dias in zip(series, historico, strict=True)]
    limiares, contagens = ajustar_conjuntos(calibradas, y, chaves, nivel)

    return AjusteCalibracao(
        a_platt=a,
        b_platt=b,
        lambda_platt=lam,
        taxa_base=taxa_base,
        nivel_conformal=nivel,
        limiares_conformal=limiares,
        linhas_por_grupo=contagens,
        ece_antes=_erro_calibracao_esperado(p, y),
        ece_depois=_erro_calibracao_esperado(calibradas, y),
    )


def _quantil_conforme(escores: np.ndarray, nivel: float) -> float:
    """Quantil conforme com correção de amostra finita.

    Garante cobertura de nível pedido sob trocabilidade: usa o posto
    ceil((n+1)(1-alfa)) dos escores ordenados. Quando o posto passa de n, a
    amostra é pequena demais para o nível e o quantil é infinito: o conjunto
    inclui a classe sempre.
    """
    import math

    n = len(escores)
    alfa = max(0.0, min(0.5, 1 - nivel))
    posto = math.ceil((n + 1) * (1 - alfa))
    if n == 0 or posto > n:
        return math.inf
    return float(np.sort(escores)[posto - 1])


def ajustar_conjuntos(
    probabilidades: np.ndarray,
    rotulos: np.ndarray,
    chaves: list[str],
    nivel: float = NIVEL_CONFORMAL,
    minimo: int = MINIMO_POR_CLASSE,
) -> tuple[dict[str, dict[str, float]], dict[str, dict[str, int]]]:
    """Limiares dos conjuntos de predição conformes, por grupo e classe.

    O escore de não conformidade de uma linha é 1 - p(classe verdadeira).
    Para cada grupo Mondrian e cada classe, o quantil conforme dos escores
    das linhas daquela classe vira um limiar na probabilidade p do positivo:
    a classe 0 entra no conjunto quando p <= limiar negativo; a classe 1
    entra quando p >= limiar positivo. Isso garante cobertura de pelo menos
    `nivel` dentro de cada grupo e classe, sob trocabilidade, o que importa
    com classes desbalanceadas: a cobertura marginal seria atingida dizendo
    {0} para quase todos. Grupos com menos de `minimo` linhas de uma classe
    incluem essa classe sempre.
    """
    p = np.asarray(probabilidades, dtype=float)
    y = np.asarray(rotulos, dtype=int)
    chaves_arr = np.asarray(chaves)
    limiares: dict[str, dict[str, float]] = {}
    contagens: dict[str, dict[str, int]] = {}
    for chave in sorted(set(chaves)):
        no_grupo = chaves_arr == chave
        negativos = p[no_grupo & (y == 0)]
        positivos = p[no_grupo & (y == 1)]
        q_negativo = _quantil_conforme(negativos, nivel) if len(negativos) >= minimo else np.inf
        q_positivo = _quantil_conforme(1 - positivos, nivel) if len(positivos) >= minimo else np.inf
        limiares[chave] = {
            "negativo": float(min(1.0, q_negativo)),
            "positivo": float(max(0.0, 1.0 - q_positivo)),
        }
        contagens[chave] = {"0": len(negativos), "1": len(positivos)}
    return limiares, contagens


def conjunto_conformal(probabilidade: float, chave: str, limiares: dict[str, dict[str, float]]) -> list[int]:
    """Conjunto de classes plausíveis para uma previsão, no nível ajustado.

    {0}: sem risco no nível pedido; {1}: risco; {0, 1}: indefinido. Grupo
    sem limiar devolve {0, 1}. Um conjunto vazio (possível quando o modelo
    separa bem) também vira {0, 1}: acrescentar classes nunca reduz a
    cobertura, e o produto não tem leitura para conjunto vazio.
    """
    limiar = limiares.get(chave)
    if limiar is None:
        return [0, 1]
    conjunto = []
    if probabilidade <= limiar["negativo"]:
        conjunto.append(0)
    if probabilidade >= limiar["positivo"]:
        conjunto.append(1)
    return conjunto or [0, 1]


def avaliar_conjuntos(
    probabilidades: np.ndarray,
    rotulos: np.ndarray,
    chaves: list[str],
    limiares: dict[str, dict[str, float]],
    *,
    minimo_grupo: int = MINIMO_POR_CLASSE,
) -> dict:
    """Cobertura e eficiência dos conjuntos num conjunto de dados.

    Cobertura por classe é a fração de linhas daquela classe cujo conjunto
    contém a classe verdadeira; eficiência é a fração de conjuntos unitários
    (os que informam algo). Grupos com menos de `minimo_grupo` linhas de uma
    classe não entram no mínimo por grupo, para não reportar cobertura de
    amostra minúscula.
    """
    p = np.asarray(probabilidades, dtype=float)
    y = np.asarray(rotulos, dtype=int)
    conjuntos = [
        conjunto_conformal(float(valor), chave, limiares) for valor, chave in zip(p, chaves, strict=True)
    ]
    coberto = np.array([int(rotulo) in conjunto for rotulo, conjunto in zip(y, conjuntos, strict=True)])
    tamanhos = np.array([len(conjunto) for conjunto in conjuntos])
    por_classe = {
        str(classe): (round(float(coberto[y == classe].mean()), 4) if (y == classe).any() else None)
        for classe in (0, 1)
    }
    chaves_arr = np.asarray(chaves)
    por_grupo: dict[str, dict[str, float]] = {}
    for chave in sorted(set(chaves)):
        for classe in (0, 1):
            mascara = (chaves_arr == chave) & (y == classe)
            if mascara.sum() >= minimo_grupo:
                por_grupo.setdefault(chave, {})[str(classe)] = round(float(coberto[mascara].mean()), 4)
    valores_grupo = [valor for grupo in por_grupo.values() for valor in grupo.values()]
    return {
        "cobertura_por_classe": por_classe,
        "cobertura_minima_por_classe": (
            min(valor for valor in por_classe.values() if valor is not None)
            if any(valor is not None for valor in por_classe.values())
            else None
        ),
        "cobertura_por_grupo": por_grupo,
        "cobertura_minima_por_grupo": min(valores_grupo) if valores_grupo else None,
        "fracao_conjuntos_unitarios": round(float((tamanhos == 1).mean()), 4) if len(tamanhos) else None,
        "fracao_conjunto_0": round(float(np.mean([c == [0] for c in conjuntos])), 4) if conjuntos else None,
        "fracao_conjunto_1": round(float(np.mean([c == [1] for c in conjuntos])), 4) if conjuntos else None,
    }


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
