# Comandos de exportação: artefato leve, paridade e compatibilidade.
"""Conversão e verificação do artefato de inferência no navegador."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from frequencia.cli import contexto as contexto_mod
from frequencia.cli.contexto import Contexto

app = typer.Typer(no_args_is_help=True, help="Exportação para o navegador e verificação do artefato.")


def _ctx(ctx: typer.Context) -> Contexto:
    return ctx.obj or contexto_mod.Contexto()


def _validacao(pasta_experimento: Path) -> dict:
    alvo = Path(pasta_experimento) / "exportacoes" / "validacao.json"
    if not alvo.is_file():
        msg = f"Validação da exportação não encontrada: {alvo}. Execute a exportação antes."
        raise FileNotFoundError(msg)
    return json.loads(alvo.read_text(encoding="utf-8"))


@app.command("validar-contratos")
def validar_contratos(
    ctx: typer.Context,
    pacote: Path = typer.Argument(..., help="Pasta do pacote de distribuição."),
) -> None:
    """Valida o contrato de entrada e saída do manifesto do pacote."""
    from frequencia.distribuicao import manifesto as manifesto_mod

    contexto = _ctx(ctx)
    try:
        manifesto = manifesto_mod.carregar(Path(pacote) / "manifest.json")
        contrato = manifesto["contrato"]
        saida = {
            "features": len(contrato["features"]),
            "padroes": len(contrato["padroes"]),
            "runtime": manifesto["runtime_alvo"],
            "versao_contrato": manifesto["versao_contrato"],
        }
        contexto_mod.emitir(contexto, saida, titulo="Contrato de inferência:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("verificar-tamanho-latencia")
def verificar_tamanho_latencia(ctx: typer.Context, pasta_experimento: Path = typer.Argument(...)) -> None:
    """Confere tamanho em bytes e latência de inferência do modelo.js."""
    contexto = _ctx(ctx)
    try:
        corpo = _validacao(pasta_experimento)
        saida = {
            "tamanho_bytes": corpo["tamanho_bytes"],
            "tamanho_ok": corpo["tamanho_ok"],
            "latencia_ms": corpo["latencia_ms"],
            "latencia_ok": corpo["latencia_ok"],
        }
        contexto_mod.emitir(contexto, saida, titulo="Tamanho e latência:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("artefato-teste")
def artefato_teste(ctx: typer.Context, pasta_experimento: Path = typer.Argument(...)) -> None:
    """Gera um mini pacote de teste com os casos sintéticos da exportação."""
    contexto = _ctx(ctx)
    try:
        alvo = Path(pasta_experimento) / "exportacoes" / "dados-teste.json"
        corpo = json.loads(alvo.read_text(encoding="utf-8"))
        contexto_mod.emitir(
            contexto,
            {"arquivo": str(alvo), "casos": corpo["total"]},
        )
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("testar-sinteticos")
def testar_sinteticos(
    ctx: typer.Context,
    pacote: Path = typer.Argument(..., help="Pasta do pacote com modelo.js e dados-teste.json."),
) -> None:
    """Roda os casos sintéticos no Node e confere as saídas esperadas."""
    from frequencia.pipelines import exportacao as exportacao_mod

    contexto = _ctx(ctx)
    try:
        dados = json.loads((Path(pacote) / "dados-teste.json").read_text(encoding="utf-8"))
        casos = [{"vetor": caso["vetor"], "contexto": caso["contexto"]} for caso in dados["casos"]]
        esperados = [caso["esperado"] for caso in dados["casos"]]
        veredito = exportacao_mod.validar_artefato_js(Path(pacote) / "modelo.js", casos, esperados)
        contexto_mod.emitir(contexto, veredito, titulo="Teste com dados sintéticos:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("verificar-compatibilidade")
def verificar_compatibilidade(
    ctx: typer.Context,
    pacote: Path = typer.Argument(...),
    versao_app: str = typer.Option("1.4.0", help="Versão atual do FrequenciApp."),
) -> None:
    """Confere compatibilidade do pacote com a versão do app."""
    from packaging.version import Version

    from frequencia.distribuicao import manifesto as manifesto_mod

    contexto = _ctx(ctx)
    try:
        manifesto = manifesto_mod.carregar(Path(pacote) / "manifest.json")
        compativel = Version(versao_app) >= Version(manifesto["min_app_versao"])
        saida = {
            "versao_app": versao_app,
            "min_app_versao": manifesto["min_app_versao"],
            "compativel": compativel,
            "validade_ate": manifesto["validade_ate"],
        }
        contexto_mod.emitir(contexto, saida, titulo="Compatibilidade:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("hash")
def hash_(ctx: typer.Context, pasta_experimento: Path = typer.Argument(...)) -> None:
    """Mostra o hash do modelo exportado e do estudante destilado."""
    contexto = _ctx(ctx)
    try:
        from frequencia.infra import hash as hash_mod

        alvo_js = Path(pasta_experimento) / "exportacoes" / "modelo.js"
        alvo_estudante = Path(pasta_experimento) / "estudante.joblib"
        saida = {
            "modelo_js": hash_mod.hash_arquivo(alvo_js) if alvo_js.is_file() else "",
            "estudante": hash_mod.hash_arquivo(alvo_estudante) if alvo_estudante.is_file() else "",
        }
        contexto_mod.emitir(contexto, saida, titulo="Hashes do artefato:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("registrar")
def registrar(ctx: typer.Context, pasta_experimento: Path = typer.Argument(...)) -> None:
    """Registra a exportação no log estruturado e na auditoria."""
    contexto = _ctx(ctx)
    try:
        corpo = _validacao(pasta_experimento)
        contexto.auditar(
            "exportacao.registrar",
            alvo=str(pasta_experimento),
            tamanho=corpo["tamanho_bytes"],
            latencia=corpo["latencia_ms"],
        )
        contexto_mod.emitir(contexto, corpo, titulo="Exportação registrada:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)
