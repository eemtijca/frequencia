# Comandos de datasets: construção temporal, perfis e linhagem.
"""Construção e verificação dos datasets de treino."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from frequencia.cli import contexto as contexto_mod
from frequencia.cli.contexto import Contexto
from frequencia.pipelines import dataset as dataset_mod

app = typer.Typer(no_args_is_help=True, help="Datasets temporais com rótulo futuro.")


def _ctx(ctx: typer.Context) -> Contexto:
    return ctx.obj or contexto_mod.Contexto()


@app.command("construir")
def construir(
    ctx: typer.Context,
    pasta_dados: Path = typer.Argument(..., help="Pasta do pacote de dados (sintético ou importado)."),
    horizonte: int = typer.Option(7, help="Dias letivos do rótulo futuro."),
    limiar_rotulo: int = typer.Option(2, help="Faltas mínimas no horizonte para rótulo 1."),
    min_historico: int = typer.Option(10, help="Dias de histórico mínimo por linha."),
    passo: int = typer.Option(1, help="Passo dos dias de referência (2 pula dias alternados)."),
    ponto_no_tempo: str = typer.Option("estrito", help="estrito (as-of) ou atual (estado final)."),
    perfil: str = typer.Option("", help="Filtro de perfil, como 'frequencia_por_aula=true'."),
    versao: str = typer.Option("", help="Identificador explícito do dataset."),
) -> None:
    """Constrói o dataset temporal com separação estrita por tempo."""
    contexto = _ctx(ctx)
    try:
        config = dataset_mod.ConfigDataset(
            pasta_dados=pasta_dados,
            horizonte_dias_letivos=horizonte,
            limiar_rotulo=limiar_rotulo,
            min_historico=min_historico,
            passo=passo,
            ponto_no_tempo=ponto_no_tempo,
            perfil=perfil or None,
            versao=versao,
        )
        if contexto.seco:
            corpo = {
                "acao": "construir",
                "config": json.loads(json.dumps(vars(config), default=str)),
            }
            contexto_mod.emitir(contexto, corpo, titulo="Modo seco: construiria com a configuração a seguir.")
            return
        resultado = dataset_mod.construir(config, detalhado=contexto.detalhado)
        corpo = {
            "pasta": str(resultado["pasta"]),
            **resultado["meta"]["resumo"],
        }
        contexto_mod.emitir(contexto, corpo, titulo="Dataset construído:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("separar")
def separar(ctx: typer.Context, pasta_dataset: Path = typer.Argument(...)) -> None:
    """Mostra as fronteiras temporais e a divisão do dataset."""
    contexto = _ctx(ctx)
    try:
        pacote = dataset_mod.carregar_dataset(pasta_dataset)
        contexto_mod.emitir(
            contexto,
            pacote["meta"]["resumo"]["divisao"],
            titulo="Divisão temporal:",
        )
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("gerar-por-perfil")
def gerar_por_perfil(
    ctx: typer.Context,
    pasta_dados: Path = typer.Argument(...),
    perfil: str = typer.Option("frequencia_por_aula=true", help="Chave do perfil de dados."),
    versao: str = typer.Option("", help="Identificador do dataset restrito."),
) -> None:
    """Constrói dataset restrito às escolas de um perfil de recursos."""
    contexto = _ctx(ctx)
    try:
        config = dataset_mod.ConfigDataset(
            pasta_dados=pasta_dados,
            perfil=perfil,
            versao=versao or f"perfil-{perfil.replace('=', '-').replace(',', '_')}"[:80],
        )
        if contexto.seco:
            contexto_mod.emitir(
                contexto,
                {"acao": "gerar-por-perfil", "perfil": perfil},
                titulo="Modo seco: construiria o dataset restrito.",
            )
            return
        resultado = dataset_mod.construir(config, detalhado=contexto.detalhado)
        contexto_mod.emitir(
            contexto,
            {"pasta": str(resultado["pasta"]), **resultado["meta"]["resumo"]},
            titulo="Dataset por perfil:",
        )
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("validar-ausencia-futuro")
def validar_ausencia_futuro(ctx: typer.Context, pasta_dataset: Path = typer.Argument(...)) -> None:
    """Verifica por reconstrução que as features não enxergam o futuro."""
    contexto = _ctx(ctx)
    try:
        veredito = dataset_mod.validar_ausencia_de_futuro(pasta_dataset)
        contexto_mod.emitir(contexto, veredito, titulo="Ausência de futuro:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("registrar-linhagem")
def registrar_linhagem(ctx: typer.Context, pasta_dataset: Path = typer.Argument(...)) -> None:
    """Registra a linhagem do dataset na trilha de auditoria."""
    contexto = _ctx(ctx)
    try:
        pacote = dataset_mod.carregar_dataset(pasta_dataset)
        linhagem = pacote["meta"]["linhagem"]
        contexto.auditar("datasets.linhagem", alvo=str(pasta_dataset), **linhagem)
        contexto_mod.emitir(contexto, linhagem, titulo="Linhagem registrada:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("listar")
def listar(ctx: typer.Context) -> None:
    """Lista os datasets construídos no workspace."""
    from frequencia.infra import caminhos

    contexto = _ctx(ctx)
    try:
        pasta = caminhos.caminho("processados")
        linhas = []
        for filho in sorted(pasta.iterdir()):
            alvo = filho / "meta.json"
            if alvo.is_file():
                meta = json.loads(alvo.read_text(encoding="utf-8"))
                linhas.append(
                    {
                        "identificador": meta["identificador"],
                        "linhas": meta["resumo"]["linhas"],
                        "taxa_rotulo": meta["resumo"]["taxa_rotulo"],
                        "ponto_no_tempo": meta["config"]["ponto_no_tempo"],
                    }
                )
        contexto_mod.emitir(contexto, linhas, titulo="Datasets:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)
