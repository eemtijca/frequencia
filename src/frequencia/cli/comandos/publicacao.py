# Comandos de publicação: releases, rollback e revogação.
"""Canal de publicação consumido pelo FrequenciApp."""

from __future__ import annotations

from pathlib import Path

import typer

from frequencia.cli import contexto as contexto_mod
from frequencia.cli.contexto import Contexto
from frequencia.infra.erros import ErroPermissao

app = typer.Typer(no_args_is_help=True, help="Publicação, rollback e revogação de versões.")


def _ctx(ctx: typer.Context) -> Contexto:
    return ctx.obj or contexto_mod.Contexto()


@app.command("publicar")
def publicar(
    ctx: typer.Context,
    pacote: Path = typer.Argument(..., help="Pasta do pacote validado."),
    versao: str = typer.Argument(..., help="Versão do modelo no pacote."),
    notas: str = typer.Option("", help="Notas de mudança da versão."),
) -> None:
    """Publica o pacote no canal local com auditoria."""
    from frequencia.modelos import publicacao

    contexto = _ctx(ctx)
    try:
        if contexto.papel != "aprovador":
            msg = "Publicação exige o papel de aprovador. Use --papel aprovador."
            raise ErroPermissao(msg)
        resultado = publicacao.publicar(
            pacote, versao_modelo=versao, notas=notas, ator=contexto.ator, papel=contexto.papel
        )
        contexto_mod.emitir(contexto, resultado, titulo="Publicação:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("release")
def release(ctx: typer.Context, versao: str = typer.Argument(...)) -> None:
    """Lista os arquivos do release local de uma versão."""
    from frequencia.infra import caminhos

    contexto = _ctx(ctx)
    try:
        pasta = caminhos.caminho("publicacoes") / versao
        if not pasta.is_dir():
            msg = f"Release não encontrado: {versao}."
            raise FileNotFoundError(msg)
        arquivos = sorted(arquivo.name for arquivo in pasta.iterdir())
        contexto_mod.emitir(contexto, {"versao": versao, "arquivos": arquivos}, titulo="Release:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("verificar-compatibilidade")
def verificar_compatibilidade(
    ctx: typer.Context,
    versao: str = typer.Argument(...),
    versao_app: str = typer.Option("1.4.0"),
) -> None:
    """Confere a compatibilidade da versão publicada com o app."""
    import json

    from packaging.version import Version

    from frequencia.infra import caminhos

    contexto = _ctx(ctx)
    try:
        alvo = caminhos.caminho("publicacoes") / versao / "manifest.json"
        manifesto = json.loads(alvo.read_text(encoding="utf-8"))
        compativel = Version(versao_app) >= Version(manifesto["min_app_versao"])
        contexto_mod.emitir(
            contexto,
            {
                "versao": versao,
                "compativel": compativel,
                "min_app_versao": manifesto["min_app_versao"],
            },
        )
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("verificar-hash")
def verificar_hash(ctx: typer.Context, versao: str = typer.Argument(...)) -> None:
    """Confere o hash do modelo publicado contra o manifesto."""
    import json

    from frequencia.infra import caminhos
    from frequencia.infra import hash as hash_mod

    contexto = _ctx(ctx)
    try:
        pasta = caminhos.caminho("publicacoes") / versao
        manifesto = json.loads((pasta / "manifest.json").read_text(encoding="utf-8"))
        atual = hash_mod.hash_arquivo(pasta / "modelo.js")
        contexto_mod.emitir(
            contexto,
            {
                "versao": versao,
                "hash_manifesto": manifesto["hash_modelo"],
                "hash_atual": atual,
                "integro": atual == manifesto["hash_modelo"],
            },
        )
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("instrucoes")
def instrucoes(ctx: typer.Context, versao: str = typer.Argument(...)) -> None:
    """Mostra as instruções de consumo da versão publicada."""
    from frequencia.infra import caminhos

    contexto = _ctx(ctx)
    try:
        alvo = caminhos.caminho("publicacoes") / versao / "instrucoes-de-consumo.md"
        contexto_mod.emitir(contexto, {"arquivo": str(alvo), "conteudo": alvo.read_text(encoding="utf-8")})
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("marcar-producao")
def marcar_producao(
    ctx: typer.Context,
    versao: str = typer.Argument(...),
    justificativa: str = typer.Option("", help="Justificativa da marcação."),
) -> None:
    """Marca a versão como a de produção no registro."""
    from frequencia.modelos import registro as registro_mod

    contexto = _ctx(ctx)
    try:
        corpo = registro_mod.promover_modelo(
            "risco-infrequencia",
            versao,
            "publicado",
            ator=contexto.ator,
            papel=contexto.papel,
            justificativa=justificativa,
        )
        contexto_mod.emitir(contexto, {"versao": versao, "situacao": corpo["situacao"]})
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("reverter")
def reverter(
    ctx: typer.Context,
    versao_anterior: str = typer.Argument(...),
    motivo: str = typer.Option("", help="Motivo do rollback."),
) -> None:
    """Reverte a produção para uma versão anterior."""
    from frequencia.modelos import publicacao

    contexto = _ctx(ctx)
    try:
        resultado = publicacao.reverter(
            versao_anterior, ator=contexto.ator, papel=contexto.papel, motivo=motivo
        )
        contexto_mod.emitir(contexto, resultado, titulo="Rollback:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("revogar")
def revogar(
    ctx: typer.Context,
    versao: str = typer.Argument(...),
    motivo: str = typer.Option("", help="Motivo da revogação."),
) -> None:
    """Revoga a versão publicada: remove o canal e descontinua."""
    from frequencia.modelos import publicacao

    contexto = _ctx(ctx)
    try:
        resultado = publicacao.revogar(versao, ator=contexto.ator, motivo=motivo)
        contexto_mod.emitir(contexto, resultado, titulo="Revogação:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("listar")
def listar(ctx: typer.Context) -> None:
    """Lista as versões publicadas com data, hash e validade."""
    from frequencia.modelos import publicacao

    contexto = _ctx(ctx)
    try:
        publicacoes = publicacao.listar_publicacoes()
        contexto_mod.emitir(contexto, publicacoes, titulo="Publicações:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)
