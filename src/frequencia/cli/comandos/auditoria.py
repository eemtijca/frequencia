# Comandos de auditoria: trilha, filtros, integridade e linhagem.
"""Prestação de contas das ações sobre o ecossistema."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from frequencia.cli import contexto as contexto_mod
from frequencia.cli.contexto import Contexto

app = typer.Typer(no_args_is_help=True, help="Trilha de auditoria e linhagem.")


def _ctx(ctx: typer.Context) -> Contexto:
    return ctx.obj or contexto_mod.Contexto()


@app.command("listar")
def listar(ctx: typer.Context, limite: int = typer.Option(50, help="Últimos eventos.")) -> None:
    """Lista os eventos mais recentes da trilha de auditoria."""
    from frequencia.infra import estado as estado_infra

    contexto = _ctx(ctx)
    try:
        eventos = estado_infra.ler_auditoria()[-limite:]
        linhas = [
            {
                "momento": evento["momento"],
                "ator": evento.get("ator", ""),
                "acao": evento["acao"],
                "alvo": evento.get("alvo", ""),
            }
            for evento in eventos
        ]
        contexto_mod.emitir(contexto, linhas, titulo="Auditoria (mais recentes):")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("filtrar")
def filtrar(
    ctx: typer.Context,
    ator: str = typer.Option("", help="Filtra pelo ator."),
    acao: str = typer.Option("", help="Filtra pelo prefixo da ação."),
    alvo: str = typer.Option("", help="Filtra pelo alvo."),
    inicio: str = typer.Option("", help="Data ISO inicial, inclusive."),
    fim: str = typer.Option("", help="Data ISO final, inclusive."),
) -> None:
    """Filtra a trilha por ator, ação, alvo e período."""
    from frequencia.infra import estado as estado_infra

    contexto = _ctx(ctx)
    try:
        eventos = estado_infra.ler_auditoria()
        selecionados = [
            evento
            for evento in eventos
            if (not ator or evento.get("ator") == ator)
            and (not acao or evento.get("acao", "").startswith(acao))
            and (not alvo or alvo in evento.get("alvo", ""))
            and (not inicio or evento["momento"] >= inicio)
            and (not fim or evento["momento"] <= fim + "T23:59:59")
        ]
        contexto_mod.emitir(contexto, selecionados, titulo=f"{len(selecionados)} eventos filtrados:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("exportar")
def exportar(ctx: typer.Context, destino: Path = typer.Option(None)) -> None:
    """Exporta a trilha de auditoria completa em JSON."""
    from frequencia.infra import caminhos
    from frequencia.infra import estado as estado_infra

    contexto = _ctx(ctx)
    try:
        alvo = destino or caminhos.caminho("relatorios") / "auditoria.json"
        eventos = estado_infra.ler_auditoria()
        alvo.write_text(json.dumps(eventos, ensure_ascii=False, indent=2), encoding="utf-8")
        contexto_mod.emitir(contexto, {"arquivo": str(alvo), "eventos": len(eventos)})
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("verificar-integridade")
def verificar_integridade(ctx: typer.Context) -> None:
    """Confere hashes dos manifestos das publicações atuais."""
    import json as json_mod

    from frequencia.infra import caminhos
    from frequencia.infra import hash as hash_mod

    contexto = _ctx(ctx)
    try:
        pasta = caminhos.caminho("publicacoes")
        vereditos = []
        for filho in sorted(pasta.iterdir()) if pasta.exists() else []:
            alvo = filho / "manifest.json"
            if not alvo.is_file():
                continue
            manifesto = json_mod.loads(alvo.read_text(encoding="utf-8"))
            atual = hash_mod.hash_arquivo(filho / "modelo.js")
            vereditos.append(
                {
                    "versao": manifesto.get("versao_modelo", filho.name),
                    "integro": atual == manifesto.get("hash_modelo"),
                }
            )
        contexto_mod.emitir(contexto, vereditos, titulo="Integridade dos manifestos:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("reconstruir-linhagem")
def reconstruir_linhagem(ctx: typer.Context, pasta_experimento: Path = typer.Argument(...)) -> None:
    """Reconstrói a linhagem do experimento: dados, dataset e artefatos."""
    contexto = _ctx(ctx)
    try:
        alvo = Path(pasta_experimento) / "estado.json"
        estado = json.loads(alvo.read_text(encoding="utf-8"))
        dataset_config = estado.get("config", {}).get("pasta_dataset", "")
        alvo_dataset = Path(dataset_config) / "meta.json"
        linhagem = {}
        if alvo_dataset.is_file():
            meta = json.loads(alvo_dataset.read_text(encoding="utf-8"))
            linhagem = meta.get("linhagem", {})
        corpo = {
            "experimento": str(pasta_experimento),
            "dataset": dataset_config,
            "origem_dados": linhagem.get("origem", ""),
            "hash_dados": linhagem.get("hash_pasta", ""),
            "etapas": list(estado.get("etapas", {}).keys()),
        }
        contexto_mod.emitir(contexto, corpo, titulo="Linhagem reconstruída:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)
