# Teste de documentação executável: comandos da CLI citados nos Markdown.
"""Todo comando frequencia em bloco bash usa grupo, subcomando e opções reais.

A documentação já mandou passar opções globais (--ator, --papel) depois do
subcomando, o que a CLI recusa; este teste confere cada comando citado contra
a árvore de comandos do typer, sem executar nada.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path
from typing import Any

import typer

RAIZ = Path(__file__).resolve().parents[2]
ARQUIVOS = [
    RAIZ / "README.md",
    RAIZ / "INSTRUCOES.md",
    RAIZ / "CONTRIBUTING.md",
    RAIZ / "AGENTS.md",
    *sorted((RAIZ / "docs").rglob("*.md")),
    *sorted((RAIZ / "projetos").rglob("*.md")),
    *sorted((RAIZ / ".agents").rglob("*.md")),
]
BLOCO_BASH = re.compile(r"```bash\n(.*?)```", re.DOTALL)


def _comandos(texto: str) -> list[list[str]]:
    """Comandos frequencia dos blocos bash, com continuações juntadas."""
    encontrados = []
    for bloco in BLOCO_BASH.findall(texto):
        for linha in bloco.replace("\\\n", " ").splitlines():
            linha = linha.split(" #", 1)[0].strip()
            if not linha or linha.startswith("#"):
                continue
            try:
                partes = shlex.split(linha)
            except ValueError:
                continue
            if "frequencia" in partes:
                restante = partes[partes.index("frequencia") + 1 :]
                for separador in ("|", ">", "&&", ";"):
                    if separador in restante:
                        restante = restante[: restante.index(separador)]
                encontrados.append(restante)
    return encontrados


def _opcoes(comando: Any) -> dict[str, bool]:
    """Nome de cada opção do comando e se ela é flag (sem valor).

    O typer 0.27 embute a própria cópia do click, então a inspeção é por
    atributo, não por classe.
    """
    opcoes: dict[str, bool] = {}
    for parametro in comando.params:
        if getattr(parametro, "param_type_name", "") == "option":
            for nome in (*parametro.opts, *parametro.secondary_opts):
                opcoes[nome] = parametro.is_flag
    return opcoes


def _problemas(argumentos: list[str], raiz: Any) -> list[str]:
    """Erros de estrutura de um comando citado; lista vazia quando válido."""
    globais = _opcoes(raiz)
    posicao = 0
    while posicao < len(argumentos) and argumentos[posicao].startswith("--"):
        opcao = argumentos[posicao].split("=", 1)[0]
        if opcao == "--help":
            return []
        if opcao not in globais:
            return [f"opção global inexistente {opcao}"]
        posicao += 1 if (globais[opcao] or "=" in argumentos[posicao]) else 2
    if posicao >= len(argumentos):
        return []
    if argumentos[posicao].startswith("<"):
        return []  # gabarito genérico, como frequencia <grupo> --help
    grupo = raiz.commands.get(argumentos[posicao])
    if grupo is None:
        return [f"grupo inexistente {argumentos[posicao]}"]
    posicao += 1
    if not hasattr(grupo, "commands") or posicao >= len(argumentos):
        return []
    if argumentos[posicao] in ("--help", "-h"):
        return []
    subcomando = grupo.commands.get(argumentos[posicao])
    if subcomando is None:
        return [f"subcomando inexistente {argumentos[posicao]}"]
    validas = _opcoes(subcomando)
    erros = []
    for argumento in argumentos[posicao + 1 :]:
        if argumento.startswith("--") and argumento.split("=", 1)[0] not in validas:
            nome = argumento.split("=", 1)[0]
            dica = " (é global: vai antes do grupo)" if nome in globais else ""
            erros.append(f"opção inexistente {nome}{dica}")
    return erros


def test_comandos_documentados_existem_com_as_opcoes_citadas() -> None:
    """Grupos, subcomandos e opções citados batem com a CLI real."""
    from frequencia.cli.app import app

    raiz = typer.main.get_command(app)
    assert hasattr(raiz, "commands")
    falhas = []
    total = 0
    for arquivo in ARQUIVOS:
        for argumentos in _comandos(arquivo.read_text(encoding="utf-8")):
            total += 1
            for problema in _problemas(argumentos, raiz):
                falhas.append(f"{arquivo.relative_to(RAIZ)}: frequencia {' '.join(argumentos)}: {problema}")
    assert total > 50, total
    assert not falhas, "\n".join(falhas)
