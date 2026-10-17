# Comandos de privacidade: identificadores, pseudonimização e portão.
"""Governança de dados pessoais pela linha de comando."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import typer

from frequencia.cli import contexto as contexto_mod
from frequencia.cli.contexto import Contexto

app = typer.Typer(no_args_is_help=True, help="Detecção de PII, pseudonimização e portão de treino.")


def _ctx(ctx: typer.Context) -> Contexto:
    return ctx.obj or contexto_mod.Contexto()


@app.command("verificar-identificadores")
def verificar_identificadores(ctx: typer.Context, pasta: Path = typer.Argument(...)) -> None:
    """Confere que nenhuma coluna é identificadora direta proibida."""
    from frequencia.dados import sintetico
    from frequencia.privacidade import detector

    contexto = _ctx(ctx)
    try:
        tabelas = sintetico.carregar_pacote(pasta)["tabelas"]
        problemas = detector.verificar_identificadores(tabelas)
        contexto_mod.emitir(
            contexto,
            problemas if problemas else "Nenhum identificador proibido encontrado.",
            titulo="Identificadores proibidos:",
        )
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("verificar-sensiveis")
def verificar_sensiveis(ctx: typer.Context, pasta: Path = typer.Argument(...)) -> None:
    """Varre textos livres atrás de dados sensíveis com o motor completo."""
    from frequencia.dados import sintetico
    from frequencia.privacidade import detector

    contexto = _ctx(ctx)
    try:
        tabelas = sintetico.carregar_pacote(pasta)["tabelas"]
        achados = detector.examinar_tabelas(tabelas, com_presidio=True)
        contexto_mod.emitir(
            contexto,
            achados if achados else "Nenhum dado sensível detectado.",
            titulo="Achados sensíveis:",
        )
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("pseudonimizar")
def pseudonimizar(
    ctx: typer.Context,
    pasta: Path = typer.Argument(...),
    colunas: str = typer.Option("nome", help="Colunas a pseudonimizar, separadas por vírgula."),
    destino: Path = typer.Option(None, help="Pasta destino (padrão: sufixo -pseudonimizado)."),
) -> None:
    """Aplica pseudonimização determinística nas colunas indicadas."""
    from frequencia.privacidade import relatorio

    contexto = _ctx(ctx)
    try:
        alvo = destino or pasta.parent / f"{pasta.name}-pseudonimizado"
        if contexto.seco:
            corpo = {
                "acao": "pseudonimizar",
                "pasta": str(pasta),
                "colunas": colunas,
                "destino": str(alvo),
            }
            contexto_mod.emitir(contexto, corpo, titulo="Modo seco: pseudonimizaria a seguir.")
            return
        import shutil

        shutil.copytree(pasta, alvo, dirs_exist_ok=True)
        trocadas = 0
        for arquivo in alvo.glob("*.csv"):
            dados = pl.read_csv(arquivo, null_values=[""])
            alvo_colunas = [c for c in colunas.split(",") if c in dados.columns]
            if not alvo_colunas:
                continue
            novos = relatorio.pseudonimizar_tabela(dados, alvo_colunas)
            novos.write_csv(arquivo)
            trocadas += len(alvo_colunas)
        contexto.auditar("privacidade.pseudonimizar", alvo=str(alvo), colunas=colunas)
        contexto_mod.emitir(contexto, {"destino": str(alvo), "colunas_trocadas": trocadas})
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("relatorio-risco")
def relatorio_risco(
    ctx: typer.Context,
    pasta: Path = typer.Argument(...),
    base_legal: str = typer.Option("", help="Base legal declarada do tratamento."),
) -> None:
    """Gera o relatório de risco de privacidade do pacote."""
    from frequencia.dados import sintetico
    from frequencia.privacidade import relatorio

    contexto = _ctx(ctx)
    try:
        tabelas = sintetico.carregar_pacote(pasta)["tabelas"]
        corpo = relatorio.gerar_relatorio_risco(tabelas, base_legal=base_legal)
        destino = relatorio.gravar_relatorio(corpo)
        corpo["arquivo"] = str(destino)
        contexto_mod.emitir(contexto, corpo, titulo="Relatório de risco:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("validar-entrada-treino")
def validar_entrada_treino(
    ctx: typer.Context,
    pasta: Path = typer.Argument(...),
    exigir_base_legal: bool = typer.Option(False, help="Exige base legal no manifesto."),
) -> None:
    """Executa o portão de privacidade antes do treinamento."""
    from frequencia.privacidade import bloqueio

    contexto = _ctx(ctx)
    try:
        veredito = bloqueio.validar_entrada_treino(pasta, exigir_base_legal=exigir_base_legal)
        contexto_mod.emitir(contexto, veredito, titulo="Portão de privacidade:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("bloquear")
def bloquear(
    ctx: typer.Context,
    pasta: Path = typer.Argument(...),
    motivo: str = typer.Option("", help="Motivo do bloqueio registrável."),
) -> None:
    """Bloqueia explicitamente um pacote para o fluxo de treino."""
    from frequencia.infra import estado as estado_infra

    contexto = _ctx(ctx)
    try:
        contexto.auditar("privacidade.bloquear", alvo=str(pasta), detalhe=motivo)
        estado_infra.registrar_auditoria("privacidade.bloquear", alvo=str(pasta), detalhe=motivo)
        contexto_mod.emitir(contexto, {"bloqueado": str(pasta), "motivo": motivo}, titulo="Pacote bloqueado:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)
