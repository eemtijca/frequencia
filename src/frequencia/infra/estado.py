# Estado do ecossistema: registro de modelos, auditoria e tarefas em JSON/JSONL.
"""Banco leve de metadados com gravação atômica e trava exclusiva.

O registro de modelos (var/estado/registro.json) guarda versões, estados e
aprovações; toda alteração passa por registro_travado, que serializa leitura,
alteração e gravação entre processos. A auditoria (var/estado/auditoria.jsonl) é só de acréscimo e
registra quem agiu, o quê e quando. As tarefas (var/estado/tarefas.jsonl)
acompanham operações longas disparadas pela interface web.
"""

from __future__ import annotations

import contextlib
import fcntl
import json
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from frequencia.infra import caminhos
from frequencia.infra.erros import ErroEstado, ErroPermissao

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


@contextlib.contextmanager
def registro_travado() -> Iterator[dict[str, Any]]:
    """Entrega o registro para alteração e o regrava sob trava exclusiva.

    A gravação atômica impede arquivo corrompido, mas não impede que duas
    tarefas paralelas leiam a mesma versão e uma apague a mudança da outra:
    a trava cobre o ciclo inteiro. Se o bloco levantar exceção, nada é gravado.
    """
    alvo_trava = caminho_registro().with_suffix(".lock")
    alvo_trava.parent.mkdir(parents=True, exist_ok=True)
    with alvo_trava.open("w", encoding="utf-8") as trava:
        fcntl.flock(trava, fcntl.LOCK_EX)
        try:
            registro = ler_registro()
            yield registro
            gravar_registro(registro)
        finally:
            fcntl.flock(trava, fcntl.LOCK_UN)


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
    with registro_travado() as registro:
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
        versao_registrada = corpo["versoes"][versao]
    registrar_auditoria("modelo.registrar", alvo=f"{identificador}@{versao}")
    return versao_registrada


def _checar_promocao(
    registro: dict[str, Any], identificador: str, versao: str, novo_estado: str, papel: str
) -> dict[str, Any]:
    """Confere existência, transição e papel; devolve a versão sem alterá-la."""
    modelos = registro.get("modelos", {})
    if identificador not in modelos or versao not in modelos[identificador]["versoes"]:
        msg = f"Modelo {identificador}@{versao} não consta no registro."
        raise ValueError(msg)
    versao_modelo = modelos[identificador]["versoes"][versao]
    atual = versao_modelo["situacao"]
    permitidas = TRANSICOES_PERMITIDAS.get(atual, ())
    if novo_estado not in permitidas:
        caminhos_validos = ", ".join(permitidas) or "nenhum"
        msg = f"Transição não permitida: {atual} para {novo_estado}. Caminhos válidos: {caminhos_validos}"
        raise ValueError(msg)
    if novo_estado in ("homologado", "publicado") and papel != "aprovador":
        msg = "A promoção exige o papel de aprovador."
        raise ErroPermissao(msg)
    pendencias = [item for item, ok in requisitos_promocao(versao_modelo, novo_estado).items() if not ok]
    if pendencias:
        msg = f"Promoção para {novo_estado} bloqueada: {'; '.join(pendencias)}."
        raise ErroEstado(msg, dica="Resolva as pendências e tente de novo.")
    return versao_modelo


def aprovacao_vigente(versao_modelo: dict[str, Any]) -> bool:
    """Verdadeiro quando a decisão mais recente sobre a versão é aprovação.

    Uma rejeição posterior cancela aprovações anteriores: vale a última palavra.
    """
    aprovacoes = versao_modelo.get("aprovacoes", [])
    return bool(aprovacoes) and bool(aprovacoes[-1].get("aprovado"))


def requisitos_promocao(versao_modelo: dict[str, Any], novo_estado: str) -> dict[str, bool]:
    """Requisitos objetivos de cada destino, avaliados pelo motor.

    Candidato exige gates aprovados no experimento que gerou a versão;
    homologado e publicado exigem, além disso, aprovação registrada vigente.
    Descontinuar e arquivar não têm requisito: retirar uma versão nunca fica
    bloqueado.
    """
    requisitos: dict[str, bool] = {}
    if novo_estado in ("candidato", "homologado", "publicado"):
        gates = versao_modelo.get("gates") or {}
        requisitos["gates do experimento aprovados"] = gates.get("aprovado") is True
    if novo_estado in ("homologado", "publicado"):
        requisitos["aprovação registrada e não revogada por rejeição"] = aprovacao_vigente(versao_modelo)
    return requisitos


def registrar_gates(identificador: str, versao: str, veredito: dict[str, Any]) -> None:
    """Grava o veredito dos gates na versão registrada, para a promoção."""
    with registro_travado() as registro:
        corpo = registro.get("modelos", {}).get(identificador)
        if corpo is None or versao not in corpo["versoes"]:
            msg = f"Modelo {identificador}@{versao} não consta no registro."
            raise ValueError(msg)
        corpo["versoes"][versao]["gates"] = {
            "aprovado": bool(veredito.get("aprovado")),
            "vereditos": veredito.get("vereditos", {}),
            "avaliado_em": _agora_iso(),
        }
    registrar_auditoria(
        "modelo.gates",
        alvo=f"{identificador}@{versao}",
        aprovado=bool(veredito.get("aprovado")),
    )


def validar_promocao(
    identificador: str, versao: str, novo_estado: str, *, papel: str = "aprovador"
) -> dict[str, Any]:
    """Verifica se a promoção seria aceita, sem gravar nada.

    Usada por quem precisa decidir antes de agir (a publicação, por exemplo,
    só copia arquivos depois que a transição está garantida).
    """
    return _checar_promocao(ler_registro(), identificador, versao, novo_estado, papel)


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
    with registro_travado() as registro:
        versao_modelo = _checar_promocao(registro, identificador, versao, novo_estado, papel)
        versao_modelo["situacao"] = novo_estado
        if novo_estado == "publicado":
            registro["modelos"][identificador]["atual"] = versao
            registro.setdefault("publicacoes", {})[f"{identificador}@{versao}"] = {
                "publicado_em": _agora_iso(),
                "ator": ator,
            }
    registrar_auditoria(
        "modelo.promover",
        alvo=f"{identificador}@{versao}",
        ator=ator,
        papel=papel,
        detalhe=justificativa,
        estado_novo=novo_estado,
    )
    return versao_modelo


def definir_atual(identificador: str, versao: str, *, ator: str = "cli") -> None:
    """Aponta a versão atual do canal para uma versão já publicada."""
    with registro_travado() as registro:
        corpo = registro.get("modelos", {}).get(identificador)
        if corpo is None or versao not in corpo["versoes"]:
            msg = f"Modelo {identificador}@{versao} não consta no registro."
            raise ValueError(msg)
        if corpo["versoes"][versao]["situacao"] != "publicado":
            msg = f"A versão {versao} não está publicada e não pode ser a atual."
            raise ValueError(msg)
        corpo["atual"] = versao
    registrar_auditoria("modelo.definir_atual", alvo=f"{identificador}@{versao}", ator=ator)


def aprovar_modelo(
    identificador: str,
    versao: str,
    aprovado: bool,
    *,
    ator: str = "cli",
    comentario: str = "",
) -> dict[str, Any]:
    """Registra aprovação ou rejeição de uma versão do modelo."""
    with registro_travado() as registro:
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
    registrar_auditoria(
        "modelo.aprovar" if aprovado else "modelo.rejeitar",
        alvo=f"{identificador}@{versao}",
        ator=ator,
        comentario=comentario,
    )
    return alvo
