# Avaliação transversal: métricas, subgrupos, fairness, custo e gates.
"""Critérios objetivos de qualidade antes de qualquer promoção.

Calcula métricas globais e por subgrupo (série, período, faixa de histórico),
fairness básico pela dispersão de recall e taxa de alerta, custo operacional
do Top-K diário, estabilidade temporal e comparação com o baseline de regras.
Os gates mínimos decidem se a versão pode seguir para candidata.
"""

from __future__ import annotations

import numpy as np

GATES_PADRAO = {
    "auc_minimo": 0.70,
    "ece_maximo": 0.10,
    "cobertura_conformal_minima": 0.80,
    "taxa_alerta_maxima": 0.35,
    "melhora_sobre_baseline_minima": 0.0,
    "tamanho_pacote_maximo_bytes": 262144,
    "latencia_maxima_ms": 5.0,
}

K_TOP_PADRAO = 10


def avaliar(
    probabilidades: np.ndarray,
    rotulos: np.ndarray,
    *,
    series: list[str] | None = None,
    turmas: list[str] | None = None,
    historico: np.ndarray | None = None,
    dias: list[str] | None = None,
    probabilidades_baseline: np.ndarray | None = None,
    ajuste_calibracao: dict | None = None,
    conformal: dict | None = None,
    k_top: int = K_TOP_PADRAO,
) -> dict:
    """Avaliação completa de uma versão do modelo sobre um conjunto."""
    from sklearn.metrics import (
        average_precision_score,
        brier_score_loss,
        log_loss,
        roc_auc_score,
    )

    p = np.clip(np.asarray(probabilidades, dtype=float), 0, 1)
    y = np.asarray(rotulos, dtype=int)
    if len(np.unique(y)) < 2:
        msg = "Avaliação exige as duas classes presentes no conjunto."
        raise ValueError(msg)

    metricas = {
        "linhas": len(y),
        "prevalencia": round(float(y.mean()), 4),
        "auc": round(float(roc_auc_score(y, p)), 4),
        "ap": round(float(average_precision_score(y, p)), 4),
        "logloss": round(float(log_loss(y, p, labels=[0, 1])), 4),
        "brier": round(float(brier_score_loss(y, p)), 4),
        "ece": round(erro_calibracao_esperado(p, y), 4),
    }
    metricas.update(_precisao_top_k(p, y, k_top, dias=dias))
    metricas.update(_taxa_alerta(p, y))

    relatorio: dict = {"metricas": metricas}

    if series is not None:
        relatorio["por_serie"] = _por_grupo(y, p, series, "serie")
    if turmas is not None and len(set(turmas)) > 1:
        relatorio["por_turma"] = _por_grupo(y, p, turmas, "turma")
    if historico is not None:
        relatorio["por_faixa_historico"] = _por_faixa_historico(y, p, historico)
    if dias is not None:
        relatorio["estabilidade_temporal"] = _por_periodo(y, p, dias)
    if probabilidades_baseline is not None:
        auc_baseline = float(roc_auc_score(y, np.asarray(probabilidades_baseline)))
        relatorio["comparacao_baseline"] = {
            "auc_baseline": round(auc_baseline, 4),
            "ganho_absoluto": round(metricas["auc"] - auc_baseline, 4),
        }
    # O ECE do gate é o do conjunto avaliado; o da calibração fica como
    # referência, porque foi medido nos dados em que o Platt foi ajustado.
    relatorio["calibracao"] = {"ece": metricas["ece"]}
    if ajuste_calibracao is not None:
        relatorio["calibracao"]["ece_no_ajuste"] = ajuste_calibracao.get("ece_depois")
    if conformal is not None:
        relatorio["conformal"] = conformal
    if series is not None:
        relatorio["fairness"] = _fairness(y, p, series, metricas)
    return relatorio


def erro_calibracao_esperado(probabilidades: np.ndarray, rotulos: np.ndarray, bins: int = 10) -> float:
    """ECE com bins de igual largura, incluindo p exatamente zero no primeiro."""
    from frequencia.pipelines.calibracao import _erro_calibracao_esperado

    return _erro_calibracao_esperado(probabilidades, rotulos, bins)


def _precisao_top_k(p: np.ndarray, y: np.ndarray, k: int, dias: list[str] | None = None) -> dict:
    """Precisão e revocação no Top-K diário, a capacidade da coordenação.

    Sem a lista de dias, cai no Top-K global; com dias, seleciona os K
    maiores escores de cada dia de referência, que é como o painel opera.
    """
    if dias is None:
        ordem = np.argsort(-p)
        top = ordem[: min(k, len(p))]
    else:
        escolhidos: list[int] = []
        for dia in sorted(set(dias)):
            mascara = np.asarray([d == dia for d in dias])
            posicoes = np.flatnonzero(mascara)
            ordem_dia = posicoes[np.argsort(-p[posicoes])]
            escolhidos.extend(ordem_dia[: min(k, len(ordem_dia))].tolist())
        top = np.array(escolhidos, dtype=int)
    positivos = int(y.sum())
    acertos = int(y[top].sum())
    sufixo = "_diario" if dias is not None else ""
    return {
        f"precisao_top_{k}{sufixo}": round(acertos / max(1, len(top)), 4),
        f"revocacao_top_{k}{sufixo}": round(acertos / max(1, positivos), 4),
    }


def _taxa_alerta(p: np.ndarray, y: np.ndarray, limiar: float = 0.65) -> dict:
    """Taxa de alerta, falsos positivos e negativos no limiar de entrada."""
    alerta = p >= limiar
    fp = int((alerta & (y == 0)).sum())
    fn = int((~alerta & (y == 1)).sum())
    return {
        "taxa_alerta": round(float(alerta.mean()), 4),
        "falsos_positivos": fp,
        "falsos_negativos": fn,
        "alertas_por_dia_estimado": round(float(alerta.mean() * 100), 2),
    }


def _por_grupo(y, p, grupos: list[str], rotulo: str) -> list[dict]:
    """Métricas por grupo, com proteção contra grupos sem as duas classes."""
    from sklearn.metrics import roc_auc_score

    saida = []
    for nome in sorted(set(grupos)):
        mascara = np.asarray([g == nome for g in grupos])
        if mascara.sum() < 20:
            continue
        parciais = {
            rotulo: nome,
            "linhas": int(mascara.sum()),
            "prevalencia": round(float(y[mascara].mean()), 4),
        }
        if len(np.unique(y[mascara])) == 2:
            parciais["auc"] = round(float(roc_auc_score(y[mascara], p[mascara])), 4)
            parciais["taxa_alerta"] = round(float((p[mascara] >= 0.65).mean()), 4)
            parciais["revocacao"] = round(
                float(((p[mascara] >= 0.65) & (y[mascara] == 1)).sum() / max(1, int(y[mascara].sum()))),
                4,
            )
        saida.append(parciais)
    return saida


def _por_faixa_historico(y, p, historico: np.ndarray) -> list[dict]:
    """Desempenho por quantidade de histórico acumulado."""
    faixas = ((0, 20), (20, 40), (40, 70), (70, 10**6))
    from sklearn.metrics import roc_auc_score

    saida = []
    for inicio, fim in faixas:
        mascara = (historico > inicio) & (historico <= fim)
        if mascara.sum() < 20 or len(np.unique(y[mascara])) < 2:
            continue
        saida.append(
            {
                "faixa": f"{inicio + 1} a {fim if fim < 10**5 else 'infinito'} dias",
                "linhas": int(mascara.sum()),
                "auc": round(float(roc_auc_score(y[mascara], p[mascara])), 4),
            }
        )
    return saida


def _por_periodo(y, p, dias: list[str]) -> list[dict]:
    """Estabilidade temporal: AUC por mês de referência."""
    from sklearn.metrics import roc_auc_score

    meses = sorted({dia[:7] for dia in dias})
    saida = []
    for mes in meses:
        mascara = np.asarray([dia.startswith(mes) for dia in dias])
        if mascara.sum() < 20 or len(np.unique(y[mascara])) < 2:
            continue
        saida.append(
            {
                "mes": mes,
                "linhas": int(mascara.sum()),
                "auc": round(float(roc_auc_score(y[mascara], p[mascara])), 4),
            }
        )
    return saida


def _fairness(y, p, series: list[str], metricas: dict) -> dict:
    """Fairness básico: dispersão de revocação e de taxa de alerta."""
    revocacoes = []
    taxas = []
    for nome in sorted(set(series)):
        mascara = np.asarray([g == nome for g in series])
        if mascara.sum() < 20 or y[mascara].sum() == 0:
            continue
        alerta = p[mascara] >= 0.65
        revocacoes.append(float((alerta & (y[mascara] == 1)).sum() / max(1, int(y[mascara].sum()))))
        taxas.append(float(alerta.mean()))
    if len(revocacoes) < 2:
        return {"dispersao_revocacao": None, "dispersao_taxa_alerta": None}
    return {
        "dispersao_revocacao": round(max(revocacoes) - min(revocacoes), 4),
        "dispersao_taxa_alerta": round(max(taxas) - min(taxas), 4),
        "revocacoes_por_serie": [round(valor, 4) for valor in revocacoes],
    }


def _no_maximo(valor, limite) -> bool:
    return valor is not None and float(valor) <= float(limite)


def _no_minimo(valor, limite) -> bool:
    return valor is not None and float(valor) >= float(limite)


def validar_gates(
    relatorio: dict,
    *,
    tamanho_pacote_bytes: int | None = None,
    latencia_ms: float | None = None,
    gates: dict | None = None,
) -> dict:
    """Aplica os gates mínimos de promoção e devolve o veredito por gate.

    Todo gate reprova quando a medida está ausente: valor faltando é falha
    do ciclo, não aprovação. Tamanho e latência só entram quando informados.
    """
    limiares = dict(GATES_PADRAO)
    if gates:
        limiares.update(gates)
    metricas = relatorio.get("metricas", {})
    comparacao = relatorio.get("comparacao_baseline", {})
    calibracao = relatorio.get("calibracao", {})
    conformal = relatorio.get("conformal", {})
    vereditos = {
        "auc": _no_minimo(metricas.get("auc"), limiares["auc_minimo"]),
        "ece": _no_maximo(calibracao.get("ece"), limiares["ece_maximo"]),
        "cobertura_conformal": _no_minimo(
            conformal.get("cobertura_minima_por_classe"), limiares["cobertura_conformal_minima"]
        ),
        "taxa_alerta": _no_maximo(metricas.get("taxa_alerta"), limiares["taxa_alerta_maxima"]),
        "melhora_sobre_baseline": _no_minimo(
            comparacao.get("ganho_absoluto"), limiares["melhora_sobre_baseline_minima"]
        ),
    }
    if tamanho_pacote_bytes is not None:
        vereditos["tamanho_pacote"] = _no_maximo(
            tamanho_pacote_bytes, limiares["tamanho_pacote_maximo_bytes"]
        )
    if latencia_ms is not None:
        vereditos["latencia"] = _no_maximo(latencia_ms, limiares["latencia_maxima_ms"])
    return {
        "gates": limiares,
        "vereditos": vereditos,
        "aprovado": all(vereditos.values()),
    }


def gerar_relatorio_markdown(relatorio: dict, destino) -> str:
    """Renderiza o relatório de avaliação em Markdown legível."""
    linhas = ["# Relatório de avaliação", ""]
    metricas = relatorio.get("metricas", {})
    linhas.append("## Métricas globais")
    linhas.append("")
    linhas.append("| Métrica | Valor |")
    linhas.append("| --- | --- |")
    for chave, valor in metricas.items():
        linhas.append(f"| {chave} | {valor} |")
    for secao in (
        "por_serie",
        "por_faixa_historico",
        "estabilidade_temporal",
        "comparacao_baseline",
        "calibracao",
        "conformal",
        "fairness",
    ):
        corpo = relatorio.get(secao)
        if not corpo:
            continue
        linhas.append("")
        linhas.append(f"## {secao.replace('_', ' ').capitalize()}")
        linhas.append("")
        if isinstance(corpo, list):
            linhas.append("| | | |")
            linhas.append("| --- | --- | --- |")
            for item in corpo:
                valores = " | ".join(str(v) for v in item.values())
                linhas.append(f"| {valores} |")
        else:
            for chave, valor in corpo.items():
                linhas.append(f"- {chave}: {valor}")
    texto = "\n".join(linhas) + "\n"
    if destino is not None:
        from pathlib import Path

        alvo = Path(destino)
        alvo.parent.mkdir(parents=True, exist_ok=True)
        alvo.write_text(texto, encoding="utf-8")
    return texto
