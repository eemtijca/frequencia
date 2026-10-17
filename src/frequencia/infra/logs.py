# Logs estruturados em JSONL: uma linha por evento, sem dado pessoal.
"""Registro estruturado de eventos do ciclo de MLOps.

Cada evento vira uma linha JSON em var/logs/operacao.jsonl com data em UTC,
estágio, ação e campos de contexto. Logs nunca recebem dados pessoais de
alunos; a política é verificada por teste dedicado.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_NIVEL_PADRAO = "info"


def _agora_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def registrar(
    acao: str,
    *,
    estagio: str = "geral",
    nivel: str = _NIVEL_PADRAO,
    detalhado: bool = False,
    **campos: Any,
) -> dict[str, Any]:
    """Grava um evento no log estruturado e devolve o registro montado."""
    from frequencia.infra import caminhos

    registro = {
        "momento": _agora_iso(),
        "estagio": estagio,
        "acao": acao,
        "nivel": nivel,
        **campos,
    }
    destino = caminhos.caminho("logs") / "operacao.jsonl"
    with destino.open("a", encoding="utf-8") as alvo:
        alvo.write(json.dumps(registro, ensure_ascii=False, default=str) + "\n")
    if detalhado:
        print(json.dumps(registro, ensure_ascii=False, default=str))
    return registro


def ler_eventos(destino: Path | None = None) -> list[dict[str, Any]]:
    """Lê todos os eventos do log estruturado, na ordem em que ocorreram."""
    from frequencia.infra import caminhos

    caminho = destino or caminhos.caminho("logs") / "operacao.jsonl"
    if not caminho.exists():
        return []
    linhas: list[dict[str, Any]] = []
    with caminho.open(encoding="utf-8") as origem:
        for linha in origem:
            if linha.strip():
                linhas.append(json.loads(linha))
    return linhas
