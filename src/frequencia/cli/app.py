# Raiz da CLI: grupos funcionais e bandeiras transversais.
"""Interface de linha de comando do FrequencIA.

Uso: frequencia <grupo> <comando> [opções]. Ajuda completa com
frequencia --help e por grupo. Toda operação registra log estruturado e,
quando muda estado, entrada de auditoria.
"""

from __future__ import annotations

from pathlib import Path

import typer

from frequencia.cli import contexto as contexto_mod
from frequencia.cli.comandos import (
    auditoria,
    avaliacao,
    dados,
    datasets,
    empacotamento,
    experimentos,
    exportacao,
    features,
    monitoramento,
    privacidade,
    publicacao,
    registro,
)

app = typer.Typer(
    name="frequencia",
    help="FrequencIA: ecossistema de MLOps do FrequenciApp.",
    no_args_is_help=True,
    add_completion=False,
)

for grupo, modulo in (
    ("dados", dados),
    ("privacidade", privacidade),
    ("features", features),
    ("datasets", datasets),
    ("experimentos", experimentos),
    ("avaliacao", avaliacao),
    ("exportacao", exportacao),
    ("empacotamento", empacotamento),
    ("registro", registro),
    ("publicacao", publicacao),
    ("monitoramento", monitoramento),
    ("auditoria", auditoria),
):
    app.add_typer(modulo.app, name=grupo, help=(modulo.__doc__ or grupo).strip().splitlines()[0])


@app.callback()
def principal(
    ctx: typer.Context,
    json: bool = typer.Option(False, "--json", help="Saída estruturada para scripts."),
    seco: bool = typer.Option(False, "--seco", help="Modo seco: ensaia sem executar."),
    detalhado: bool = typer.Option(False, "--detalhado", help="Logs detalhados e stack trace."),
    silencioso: bool = typer.Option(False, "--silencioso", help="Suprime a saída padrão."),
    perfil: str = typer.Option("padrao", "--perfil", help="Perfil de ambiente: padrao, fumaca ou ciclo."),
    workspace: Path = typer.Option(
        None, "--workspace", help="Pasta raiz do workspace (padrão: o repositório).", exists=False
    ),
    forca: bool = typer.Option(False, "--forca", help="Reexecuta etapas concluídas."),
    justificativa: str = typer.Option(
        "", "--justificativa", help="Motivo da força; obrigatória com --forca."
    ),
    ator: str = typer.Option("cli", "--ator", help="Identidade que opera, para auditoria."),
    papel: str = typer.Option(
        "engenheiro", "--papel", help="Papel da operação: observador, cientista, engenheiro ou aprovador."
    ),
) -> None:
    """Resolve as bandeiras transversais e valida o ambiente na partida."""
    import sys

    if workspace is not None:
        import os

        os.environ["FREQUENCIA_WORKSPACE"] = str(workspace.resolve())
    from frequencia.infra import ambiente

    ambiente.validar(perfil=perfil, detalhado=detalhado)
    if forca and not justificativa:
        mensagem = (
            "Use --forca apenas com --justificativa informada. Explique o motivo da reexecução completa."
        )
        print(f"Erro: {mensagem}", file=sys.stderr)
        raise typer.Exit(1)
    ctx.obj = contexto_mod.Contexto(
        json=json,
        seco=seco,
        detalhado=detalhado,
        silencioso=silencioso,
        perfil=perfil,
        forca=forca,
        justificativa=justificativa,
        ator=ator,
        papel=papel,
    )


def executar() -> None:  # pragma: no cover - ponto de entrada
    """Ponto de entrada do console script."""
    app()


if __name__ == "__main__":  # pragma: no cover
    executar()
