# Leitura do estado do workspace para as páginas da interface web.
"""Ponte de leitura entre o Streamlit e o mesmo motor da CLI.

Nenhuma página consulta dado individual de aluno: o estado compartilhado é
feito de manifestos, métricas e contagens agregadas.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from frequencia.infra import caminhos
from frequencia.infra import estado as estado_infra


def ler_json(caminho: Path) -> dict | None:
    """Lê um JSON do workspace; devolve None quando ausente."""
    if caminho is None or not Path(caminho).is_file():
        return None
    try:
        return json.loads(Path(caminho).read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def registro() -> dict:
    """Registro completo de modelos e publicações."""
    return estado_infra.ler_registro()


def auditoria(limite: int = 200) -> list[dict]:
    """Últimos eventos da trilha de auditoria."""
    return estado_infra.ler_auditoria()[-limite:]


def tarefas() -> list[dict]:
    """Estado mais recente das tarefas de fundo disparadas pela interface."""
    return estado_infra.ler_tarefas()


def experimentos() -> list[dict]:
    """Experimentos registrados com suas métricas."""
    from frequencia.pipelines import treino as treino_mod

    return treino_mod.listar_experimentos()


def datasets() -> list[dict]:
    """Datasets construídos no workspace."""
    linhas: list[dict[str, Any]] = []
    pasta = caminhos.caminho("processados")
    if not pasta.exists():
        return linhas
    for filho in sorted(pasta.iterdir()):
        meta = ler_json(filho / "meta.json")
        if meta:
            linhas.append(
                {
                    "identificador": meta["identificador"],
                    "linhas": meta["resumo"]["linhas"],
                    "taxa_rotulo": meta["resumo"]["taxa_rotulo"],
                    "pasta": str(filho),
                }
            )
    return linhas


def detalhe_experimento(pasta: Path) -> dict:
    """Estado, avaliação e calibração de um experimento."""
    pasta = Path(pasta)
    return {
        "estado": ler_json(pasta / "estado.json"),
        "avaliacao": ler_json(pasta / "avaliacao.json"),
        "calibracao": ler_json(pasta / "calibracao.json"),
        "gates": ler_json(pasta / "gates.json"),
        "empacotamento": ler_json(pasta / "empacotamento.json"),
    }


def publicacoes() -> list[dict]:
    """Versões publicadas com data e hash."""
    from frequencia.modelos import publicacao

    return publicacao.listar_publicacoes()


def versao_atual() -> dict | None:
    """Versão em produção no registro."""
    from frequencia.modelos import publicacao

    return publicacao.versao_atual()


def pacote_publicado(versao: str) -> dict | None:
    """Manifesto da versão publicada."""
    alvo = caminhos.caminho("publicacoes") / versao / "manifest.json"
    return ler_json(alvo)


def importacoes() -> list[dict]:
    """Importações registradas com hash e licença."""
    from frequencia.dados import importacao

    return importacao.listar_importacoes()


def logs_estruturados(limite: int = 100) -> list[dict]:
    """Últimos eventos do log estruturado."""
    from frequencia.infra import logs as logs_mod

    return logs_mod.ler_eventos()[-limite:]


def contagens_workspace() -> dict[str, int]:
    """Contagens agregadas para a visão geral."""
    return {
        "experimentos": len(experimentos()),
        "datasets": len(datasets()),
        "publicacoes": len(publicacoes()),
        "importacoes": len(importacoes()),
        "auditoria": len(auditoria(limite=10**9)),
    }


def resumo_risco() -> dict:
    """Resumo de privacidade do último relatório gerado."""
    pasta = caminhos.caminho("relatorios")
    alvo = pasta / "relatorio-privacidade.json"
    return ler_json(alvo) or {"nivel": "sem relatório", "achados": []}


def feedback() -> list[dict]:
    """Histórico de feedback agregado importado."""
    from frequencia.monitoramento import saude

    return saude.ler_feedback()
