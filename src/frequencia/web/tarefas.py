# Tarefas de fundo: dispara a CLI em subprocesso e acompanha o estado.
"""Operações longas disparadas pela interface, sem bloquear a página.

Cada tarefa roda a própria CLI em subprocesso, grava a saída em
var/logs/tarefas/<id>.log e registra início e desfecho em
var/estado/tarefas.jsonl; a página consulta o estado e segue livre.
"""

from __future__ import annotations

import subprocess
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path

from frequencia.infra import caminhos
from frequencia.infra import estado as estado_infra


def executavel_cli() -> str:
    """Caminho do executável frequencia dentro do ambiente ativo."""
    import sys

    base = Path(sys.executable).parent / "frequencia"
    if base.exists():
        return str(base)
    return str(Path(sys.executable).parent.parent / "frequencia")


def disparar(
    argumentos: list[str],
    *,
    rotulo: str = "",
    workspace: Path | None = None,
) -> dict:
    """Dispara um comando da CLI em fundo e devolve o recibo da tarefa."""
    identificador = f"tarefa-{uuid.uuid4().hex[:8]}"
    pasta_logs = caminhos.caminho("logs") / "tarefas"
    pasta_logs.mkdir(parents=True, exist_ok=True)
    alvo_log = pasta_logs / f"{identificador}.log"

    import os

    ambiente = dict(os.environ)
    if workspace is not None:
        ambiente["FREQUENCIA_WORKSPACE"] = str(workspace)

    comando = [executavel_cli(), "--silencioso", *argumentos]
    with alvo_log.open("w", encoding="utf-8") as saida:
        saida.write(f"# {rotulo or ' '.join(argumentos)}\n")
        saida.flush()
        processo = subprocess.Popen(
            comando,
            stdout=saida,
            stderr=subprocess.STDOUT,
            env=ambiente,
            cwd=str(workspace or caminhos.raiz_workspace()),
        )

    estado_infra.registrar_tarefa(
        identificador,
        " ".join(argumentos),
        estado="iniciada",
        pid=processo.pid,
        rotulo=rotulo,
        log=str(alvo_log),
    )

    def _aguardar() -> None:
        codigo = processo.wait()
        estado_infra.registrar_tarefa(
            identificador,
            " ".join(argumentos),
            estado="concluida" if codigo == 0 else "falhou",
            codigo_saida=codigo,
            rotulo=rotulo,
            log=str(alvo_log),
            momento_fim=datetime.now(UTC).isoformat(timespec="seconds"),
        )

    threading.Thread(target=_aguardar, daemon=True).start()
    return {
        "id": identificador,
        "comando": " ".join(argumentos),
        "log": str(alvo_log),
        "pid": processo.pid,
    }


def ler_log(identificador: str, linhas: int = 40) -> str:
    """Lê o final do log de uma tarefa."""
    alvo = caminhos.caminho("logs") / "tarefas" / f"{identificador}.log"
    if not alvo.is_file():
        return "Sem log registrado."
    conteudo = alvo.read_text(encoding="utf-8").splitlines()
    return "\n".join(conteudo[-linhas:])
