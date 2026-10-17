# Monitoramento: drift, validade, feedback agregado e saúde do modelo.
"""Acompanhamento pós-publicação com dados agregados, nunca individuais.

O feedback entra agregado por dia (acurácia observada, taxa de descarte) e o
drift é medido por PSI sobre a distribuição das features de treino frente a
uma nova fotografia. Recomendações de retreinamento seguem critérios
explícitos e auditáveis.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import polars as pl

from frequencia.infra import caminhos, logs
from frequencia.infra.erros import ErroValidacao

LIMITE_DRIFT_PSI = 0.2
LIMITE_ACURACIA_OBSERVADA = 0.6
LIMITE_TAXA_DESCARTE = 0.5


def registrar_feedback(
    *,
    dias: list[str],
    acuracia_observada: list[float],
    taxa_descarte: list[float],
    fonte: str = "painel",
) -> dict:
    """Registra feedback agregado por dia, sem dado individual."""
    if len(dias) != len(acuracia_observada) or len(dias) != len(taxa_descarte):
        msg = "As listas de dias, acurácia e descarte precisam ter o mesmo tamanho."
        raise ErroValidacao(msg)
    corpo = {
        "registrado_em": datetime.now(UTC).isoformat(timespec="seconds"),
        "fonte": fonte,
        "dias": dias,
        "acuracia_observada": [round(float(v), 4) for v in acuracia_observada],
        "taxa_descarte": [round(float(v), 4) for v in taxa_descarte],
    }
    destino = caminhos.caminho("estado") / "feedback.jsonl"
    with destino.open("a", encoding="utf-8") as saida:
        saida.write(json.dumps(corpo, ensure_ascii=False) + "\n")
    logs.registrar("monitoramento.feedback", estagio="monitoramento", dias=len(dias))
    return corpo


def ler_feedback() -> list[dict]:
    """Lê o histórico de feedback agregado."""
    destino = caminhos.caminho("estado") / "feedback.jsonl"
    if not destino.exists():
        return []
    return [json.loads(linha) for linha in destino.read_text(encoding="utf-8").splitlines() if linha.strip()]


def calcular_psi(referencia: np.ndarray, atual: np.ndarray, *, bins: int = 10) -> np.ndarray:
    """Índice de mudança de população estável por feature."""
    referencia = np.asarray(referencia, dtype=float)
    atual = np.asarray(atual, dtype=float)
    bordas = np.unique(np.quantile(referencia, np.linspace(0, 1, bins + 1)))
    if len(bordas) < 3:
        return np.zeros(1)
    psi_valores = []
    for indice in range(len(bordas) - 1):
        inferior = bordas[indice]
        superior = bordas[indice + 1]
        ref_peso = ((referencia >= inferior) & (referencia <= superior)).mean() + 1e-6
        atu_peso = ((atual >= inferior) & (atual <= superior)).mean() + 1e-6
        psi_valores.append((atu_peso - ref_peso) * np.log(atu_peso / ref_peso))
    return np.array([max(0.0, float(np.sum(psi_valores)))])


def calcular_drift(
    features_referencia: pl.DataFrame,
    features_atuais: pl.DataFrame,
) -> dict:
    """Drift por feature entre a fotografia de treino e a atual."""
    from frequencia.features.catalogo import NOMES_FEATURES

    drift: dict[str, float] = {}
    for nome in NOMES_FEATURES:
        if nome not in features_referencia.columns or nome not in features_atuais.columns:
            continue
        base = features_referencia[nome].to_numpy()
        atual = features_atuais[nome].to_numpy()
        if len(base) == 0 or len(atual) == 0:
            continue
        psi = float(calcular_psi(base, atual)[0])
        drift[nome] = round(psi, 4)
    piores = sorted(drift.items(), key=lambda item: -item[1])[:5]
    return {
        "por_feature": drift,
        "piores": [{"feature": nome, "psi": valor} for nome, valor in piores],
        "drift_alto": any(valor > LIMITE_DRIFT_PSI for valor in drift.values()),
    }


def relatorio_saude(*, pasta_experimento: Path | None = None) -> dict:
    """Relatório de saúde: validade, drift, feedback e recomendações."""
    from frequencia.modelos import publicacao

    atual = publicacao.versao_atual()
    feedback = ler_feedback()
    recomendacoes: list[str] = []
    validade = None
    idade_dias = None
    if atual:
        validade = atual.get("validade_ate")
        if validade:
            alvo = datetime.fromisoformat(validade)
            idade_dias = (datetime.now(UTC) - alvo.replace(tzinfo=UTC)).days
            if idade_dias is not None and idade_dias > 0:
                recomendacoes.append("Validade vencida: suprimir o indicador e retreinar com dados recentes.")
    drift = None
    if pasta_experimento is not None:
        alvo_drift = Path(pasta_experimento) / "drift.json"
        if alvo_drift.is_file():
            drift = json.loads(alvo_drift.read_text(encoding="utf-8"))
            if drift.get("drift_alto"):
                recomendacoes.append("Drift de features acima do limite: retreinar com dados recentes.")
    if feedback:
        ultimo = feedback[-1]
        media_acuracia = float(np.mean(ultimo["acuracia_observada"]))
        media_descarte = float(np.mean(ultimo["taxa_descarte"]))
        if media_acuracia < LIMITE_ACURACIA_OBSERVADA:
            recomendacoes.append("Acurácia observada abaixo do limite: revisar o modelo ou os dados.")
        if media_descarte > LIMITE_TAXA_DESCARTE:
            recomendacoes.append("Taxa de descarte alta: revisar limiares e mensagens com a coordenação.")
    if not recomendacoes:
        recomendacoes.append("Modelo saudável: nenhuma ação necessária agora.")
    corpo = {
        "gerado_em": datetime.now(UTC).isoformat(timespec="seconds"),
        "versao_atual": atual.get("versao") if atual else None,
        "validade_ate": validade,
        "drift": drift,
        "feedback_recente": feedback[-1] if feedback else None,
        "recomendacoes": recomendacoes,
    }
    logs.registrar("monitoramento.saude", estagio="monitoramento")
    return corpo
