# Estado do ecossistema: registro de modelos, auditoria e tarefas em JSON/JSONL.
"""Banco leve de metadados com gravação atômica.

O registro de modelos (var/estado/registro.json) guarda versões, estados e
aprovações. A auditoria (var/estado/auditoria.jsonl) é só de acréscimo e
registra quem agiu, o quê e quando. As tarefas (var/estado/tarefas.jsonl)
acompanham operações longas disparadas pela interface web.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from frequencia.infra import caminhos

ESTADOS_MODELO = (
    "experimental",
    "candidato",
    "homologado",
    "publicado",
    "descontinuado",
    "arquivado",
)

TRANSICOES_PERMITIDAS: dict[str, tuple[str, ...]] = {
    "experimental": ("candidato", "descontinuado", "arquivado"),
    "candidato": ("homologado", "experimental", "descontinuado", "arquivado"),
    "homologado": ("publicado", "candidato", "descontinuado", "arquivado"),
    "publicado": ("descontinuado", "arquivado"),
    "descontinuado": ("arquivado",),
    "arquivado": (),
}

PAPEIS = ("observador", "cientista", "engenheiro", "aprovador")


def _agora_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def caminho_registro() -> Path:
    return caminhos.caminho("estado") / "registro.json"


def ler_registro() -> dict[str, Any]:
    """Lê o registro de modelos completo; devolve vazio quando inexistente."""
    alvo = caminho_registro()
    if not alvo.exists():
        return {"modelos": {}, "publicacoes": {}, "versao_formato": 1}
    with alvo.open(encoding="utf-8") as origem:
        return json.load(origem)


def gravar_registro(registro: dict[str, Any]) -> None:
    """Grava o registro de forma atômica (escreve temporário e renomeia)."""
    alvo = caminho_registro()
    temporario = alvo.with_suffix(".json.tmp")
    with temporario.open("w", encoding="utf-8") as destino:
        json.dump(registro, destino, ensure_ascii=False, indent=2, sort_keys=True)
        destino.write("\n")
    temporario.replace(alvo)


def registrar_auditoria(
    acao: str,
    *,
    alvo: str = "",
    ator: str = "cli",
    papel: str = "engenheiro",
    **detalhes: Any,
) -> dict[str, Any]:
    """Acrescenta um evento à trilha de auditoria e o devolve."""
    evento = {
        "momento": _agora_iso(),
        "ator": ator,
        "papel": papel,
        "acao": acao,
        "alvo": alvo,
        **detalhes,
    }
    destino = caminhos.caminho("estado") / "auditoria.jsonl"
    with destino.open("a", encoding="utf-8") as saida:
        saida.write(json.dumps(evento, ensure_ascii=False, default=str) + "\n")
    return evento


def ler_auditoria() -> list[dict[str, Any]]:
    """Lê a trilha de auditoria completa, em ordem cronológica."""
    destino = caminhos.caminho("estado") / "auditoria.jsonl"
    if not destino.exists():
        return []
    eventos: list[dict[str, Any]] = []
    with destino.open(encoding="utf-8") as origem:
        for linha in origem:
            if linha.strip():
                eventos.append(json.loads(linha))
    return eventos


def registrar_tarefa(
    identificador: str,
    comando: str,
    *,
    estado: str = "iniciada",
    **campos: Any,
) -> dict[str, Any]:
    """Registra um evento de tarefa de longa duração (interface web)."""
    evento = {
        "momento": _agora_iso(),
        "id": identificador,
        "comando": comando,
        "estado": estado,
        **campos,
    }
    destino = caminhos.caminho("estado") / "tarefas.jsonl"
    with destino.open("a", encoding="utf-8") as saida:
        saida.write(json.dumps(evento, ensure_ascii=False, default=str) + "\n")
    return evento


def ler_tarefas() -> list[dict[str, Any]]:
    """Lê o histórico de tarefas e devolve o estado mais recente de cada uma."""
    destino = caminhos.caminho("estado") / "tarefas.jsonl"
    if not destino.exists():
        return []
    estados: dict[str, dict[str, Any]] = {}
    with destino.open(encoding="utf-8") as origem:
        for linha in origem:
            if linha.strip():
                evento = json.loads(linha)
                estados[evento["id"]] = evento
    return sorted(estados.values(), key=lambda e: e.get("momento", ""), reverse=True)


def registrar_modelo(
    identificador: str,
    versao: str,
    *,
    runtime_alvo: str,
    hash_artefato: str,
    tamanho_bytes: int,
    dataset: dict[str, Any],
    metricas: dict[str, float],
    limitacoes: list[str],
    referencia_artefato: str,
    validade_ate: str,
    situacao: str = "experimental",
) -> dict[str, Any]:
    """Cria ou atualiza um modelo no registro, com auditoria."""
    if situacao not in ESTADOS_MODELO:
        msg = f"Situação inválida: {situacao}. Use uma de {ESTADOS_MODELO}."
        raise ValueError(msg)
    registro = ler_registro()
    modelos = registro.setdefault("modelos", {})
    modelos.setdefault(identificador, {"versoes": {}, "atual": None})
    corpo = modelos[identificador]
    corpo["versoes"][versao] = {
        "situacao": situacao,
        "runtime_alvo": runtime_alvo,
        "hash_artefato": hash_artefato,
        "tamanho_bytes": tamanho_bytes,
        "treinado_em": _agora_iso(),
        "dataset": dataset,
        "metricas": metricas,
        "limitacoes": limitacoes,
        "referencia_artefato": referencia_artefato,
        "validade_ate": validade_ate,
        "aprovacoes": [],
    }
    gravar_registro(registro)
    registrar_auditoria("modelo.registrar", alvo=f"{identificador}@{versao}")
    return corpo["versoes"][versao]


def promover_modelo(
    identificador: str,
    versao: str,
    novo_estado: str,
    *,
    ator: str = "cli",
    papel: str = "aprovador",
    justificativa: str = "",
) -> dict[str, Any]:
    """Move um modelo entre estados com verificação de transição válida."""
    registro = ler_registro()
    modelos = registro.get("modelos", {})
    if identificador not in modelos or versao not in modelos[identificador]["versoes"]:
        msg = f"Modelo {identificador}@{versao} não consta no registro."
        raise ValueError(msg)
    versao_modelo = modelos[identificador]["versoes"][versao]
    atual = versao_modelo["situacao"]
    permitidas = TRANSICOES_PERMITIDAS.get(atual, ())
    if novo_estado not in permitidas:
        msg = (
            f"Transição não permitida: {atual} para {novo_estado}. "
            f"Caminhos válidos: {permitidas or 'nenhum'}."
        )
        raise ValueError(msg)
    if novo_estado in ("homologado", "publicado") and papel != "aprovador":
        msg = "A promoção exige o papel de aprovador."
        raise PermissionError(msg)
    versao_modelo["situacao"] = novo_estado
    if novo_estado == "publicado":
        modelos[identificador]["atual"] = versao
        registro.setdefault("publicacoes", {})[f"{identificador}@{versao}"] = {
            "publicado_em": _agora_iso(),
            "ator": ator,
        }
    gravar_registro(registro)
    registrar_auditoria(
        "modelo.promover",
        alvo=f"{identificador}@{versao}",
        ator=ator,
        papel=papel,
        detalhe=justificativa,
        estado_novo=novo_estado,
    )
    return versao_modelo


def aprovar_modelo(
    identificador: str,
    versao: str,
    aprovado: bool,
    *,
    ator: str = "cli",
    comentario: str = "",
) -> dict[str, Any]:
    """Registra aprovação ou rejeição de uma versão do modelo."""
    registro = ler_registro()
    modelos = registro.get("modelos", {})
    if identificador not in modelos or versao not in modelos[identificador]["versoes"]:
        msg = f"Modelo {identificador}@{versao} não consta no registro."
        raise ValueError(msg)
    alvo = modelos[identificador]["versoes"][versao]
    alvo.setdefault("aprovacoes", []).append(
        {
            "momento": _agora_iso(),
            "ator": ator,
            "aprovado": aprovado,
            "comentario": comentario,
        }
    )
    gravar_registro(registro)
    registrar_auditoria(
        "modelo.aprovar" if aprovado else "modelo.rejeitar",
        alvo=f"{identificador}@{versao}",
        ator=ator,
        comentario=comentario,
    )
    return alvo
