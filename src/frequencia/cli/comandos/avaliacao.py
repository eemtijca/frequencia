# Comandos de avaliação: métricas, subgrupos, fairness e gates.
"""Avaliação transversal de modelos e conjuntos."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from frequencia.cli import contexto as contexto_mod
from frequencia.cli.contexto import Contexto

app = typer.Typer(no_args_is_help=True, help="Métricas, subgrupos, fairness e gates de promoção.")


def _ctx(ctx: typer.Context) -> Contexto:
    return ctx.obj or contexto_mod.Contexto()


def _avaliacao(pasta: Path) -> dict:
    alvo = Path(pasta) / "avaliacao.json"
    if not alvo.is_file():
        msg = f"Avaliação não encontrada: {alvo}. Execute o ciclo antes."
        raise FileNotFoundError(msg)
    return json.loads(alvo.read_text(encoding="utf-8"))


@app.command("modelo")
def modelo(ctx: typer.Context, pasta_experimento: Path = typer.Argument(...)) -> None:
    """Mostra as métricas globais da avaliação do experimento."""
    contexto = _ctx(ctx)
    try:
        corpo = _avaliacao(pasta_experimento)
        contexto_mod.emitir(contexto, corpo["metricas"], titulo="Métricas globais:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("calibracao")
def calibracao(ctx: typer.Context, pasta_experimento: Path = typer.Argument(...)) -> None:
    """Mostra a curva de calibração e o erro por grupo."""
    contexto = _ctx(ctx)
    try:
        alvo = Path(pasta_experimento) / "calibracao.json"
        corpo = json.loads(alvo.read_text(encoding="utf-8"))
        contexto_mod.emitir(contexto, corpo, titulo="Calibração:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("ensemble")
def ensemble(ctx: typer.Context, pasta_experimento: Path = typer.Argument(...)) -> None:
    """Mostra métricas, pesos e discordância do ensemble."""
    contexto = _ctx(ctx)
    try:
        alvo = Path(pasta_experimento) / "estado.json"
        estado = json.loads(alvo.read_text(encoding="utf-8"))
        corpo = estado.get("etapas", {}).get("ensemble", {}).get("resultado", {})
        contexto_mod.emitir(contexto, corpo, titulo="Ensemble:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("subgrupos")
def subgrupos(ctx: typer.Context, pasta_experimento: Path = typer.Argument(...)) -> None:
    """Mostra o desempenho por série e por faixa de histórico."""
    contexto = _ctx(ctx)
    try:
        corpo = _avaliacao(pasta_experimento)
        saida = {
            "por_serie": corpo.get("por_serie", []),
            "por_faixa_historico": corpo.get("por_faixa_historico", []),
        }
        contexto_mod.emitir(contexto, saida, titulo="Desempenho por subgrupo:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("fairness")
def fairness(ctx: typer.Context, pasta_experimento: Path = typer.Argument(...)) -> None:
    """Mostra dispersão de revocação e de taxa de alerta entre séries."""
    contexto = _ctx(ctx)
    try:
        corpo = _avaliacao(pasta_experimento)
        contexto_mod.emitir(contexto, corpo.get("fairness", {}), titulo="Fairness básico:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("curva-aprendizado")
def curva_aprendizado(ctx: typer.Context, pasta_experimento: Path = typer.Argument(...)) -> None:
    """Mostra a qualidade por quantidade de histórico acumulado."""
    contexto = _ctx(ctx)
    try:
        corpo = _avaliacao(pasta_experimento)
        contexto_mod.emitir(
            contexto,
            corpo.get("curva_aprendizado", []),
            titulo="Curva de aprendizado:",
        )
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("custo-operacional")
def custo_operacional(ctx: typer.Context, pasta_experimento: Path = typer.Argument(...)) -> None:
    """Mostra o custo operacional: alertas por dia e falsos positivos."""
    contexto = _ctx(ctx)
    try:
        corpo = _avaliacao(pasta_experimento)["metricas"]
        saida = {
            "limiar_alerta": corpo.get("limiar_alerta"),
            "taxa_alerta": corpo.get("taxa_alerta"),
            "precisao_alerta": corpo.get("precisao_alerta"),
            "revocacao_alerta": corpo.get("revocacao_alerta"),
            "lift_alerta": corpo.get("lift_alerta"),
            "alertas_por_dia_estimado": corpo.get("alertas_por_dia_estimado"),
            "falsos_positivos": corpo.get("falsos_positivos"),
            "precisao_top_10_diario": corpo.get("precisao_top_10_diario"),
            "revocacao_top_10_diario": corpo.get("revocacao_top_10_diario"),
        }
        contexto_mod.emitir(contexto, saida, titulo="Custo operacional:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("baseline")
def baseline(ctx: typer.Context, pasta_experimento: Path = typer.Argument(...)) -> None:
    """Compara o modelo com o baseline de regras."""
    contexto = _ctx(ctx)
    try:
        corpo = _avaliacao(pasta_experimento)
        contexto_mod.emitir(contexto, corpo.get("comparacao_baseline", {}), titulo="Comparação com baseline:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("validar-gates")
def validar_gates(ctx: typer.Context, pasta_experimento: Path = typer.Argument(...)) -> None:
    """Aplica os gates mínimos de promoção da versão."""
    from frequencia.pipelines import avaliacao as avaliacao_mod

    contexto = _ctx(ctx)
    try:
        corpo = _avaliacao(pasta_experimento)
        tamanho = None
        latencia = None
        alvo_export = Path(pasta_experimento) / "exportacoes" / "validacao.json"
        if alvo_export.is_file():
            validacao = json.loads(alvo_export.read_text(encoding="utf-8"))
            tamanho = validacao.get("tamanho_bytes")
            latencia = validacao.get("latencia_ms")
        veredito = avaliacao_mod.validar_gates(corpo, tamanho_pacote_bytes=tamanho, latencia_ms=latencia)
        contexto_mod.emitir(contexto, veredito, titulo="Gates de promoção:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("relatorio")
def relatorio(ctx: typer.Context, pasta_experimento: Path = typer.Argument(...)) -> None:
    """Lê o relatório de avaliação em Markdown do experimento."""
    contexto = _ctx(ctx)
    try:
        alvo = Path(pasta_experimento) / "relatorio-avaliacao.md"
        texto = alvo.read_text(encoding="utf-8")
        contexto_mod.emitir(contexto, {"arquivo": str(alvo), "linhas": len(texto.splitlines())})
    except Exception as exc:
        contexto_mod.falha(contexto, exc)
