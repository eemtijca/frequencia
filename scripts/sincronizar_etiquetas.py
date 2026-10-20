# Sincroniza as etiquetas do GitHub com o catálogo em .github/labels.json.
# Requer o GitHub CLI autenticado (gh auth status) e execução na raiz do repositório.
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CATALOGO = RAIZ / ".github" / "labels.json"


def executar_gh(argumentos: list[str]) -> str:
    """Executa o GitHub CLI e devolve a saída padrão."""
    try:
        resultado = subprocess.run(
            ["gh", *argumentos],
            cwd=RAIZ,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except FileNotFoundError as erro:
        raise SystemExit("GitHub CLI não encontrado. Instale o gh e rode gh auth login.") from erro
    except subprocess.CalledProcessError as erro:
        detalhe = (erro.stderr or erro.stdout).strip()
        raise SystemExit(f"Falha ao executar gh: {detalhe}") from erro
    return resultado.stdout


def main() -> int:
    """Cria ou atualiza as etiquetas do catálogo e informa o total."""
    if not CATALOGO.exists():
        raise SystemExit(f"Catálogo de etiquetas ausente: {CATALOGO}")

    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    etiquetas = catalogo.get("etiquetas", [])
    if not etiquetas:
        raise SystemExit("O catálogo de etiquetas está vazio.")

    existentes = {
        item["name"]
        for item in json.loads(executar_gh(["label", "list", "--limit", "200", "--json", "name"]))
    }

    criadas = 0
    atualizadas = 0
    for etiqueta in etiquetas:
        executar_gh(
            [
                "label",
                "create",
                etiqueta["nome"],
                "--color",
                etiqueta["cor"],
                "--description",
                etiqueta["descricao"],
                "--force",
            ]
        )
        if etiqueta["nome"] in existentes:
            atualizadas += 1
        else:
            criadas += 1

    print(f"Etiquetas sincronizadas: {criadas} criadas e {atualizadas} atualizadas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
