# Comandos de dados: fontes, importação, validação, perfil e sintéticos.
"""Gestão da camada de dados do FrequencIA."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from frequencia.cli import contexto as contexto_mod
from frequencia.cli.contexto import Contexto
from frequencia.infra import hash as hash_infra

app = typer.Typer(no_args_is_help=True, help="Fontes, importação, validação e dados sintéticos.")


def _ctx(ctx: typer.Context) -> Contexto:
    return ctx.obj or contexto_mod.Contexto()


@app.command("listar-fontes")
def listar_fontes(ctx: typer.Context) -> None:
    """Lista as fontes externas documentadas (MEC e INEP)."""
    from frequencia.dados import mec

    try:
        contexto_mod.emitir(_ctx(ctx), mec.catalogo_fontes(), titulo="Fontes externas:")
    except Exception as exc:
        contexto_mod.falha(_ctx(ctx), exc)


@app.command("importar")
def importar(
    ctx: typer.Context,
    pasta: Path = typer.Argument(..., help="Pasta do pacote de dados a importar."),
    origem: str = typer.Option("sintetico", help="Origem: sintetico, mec ou institucional."),
    licenca: str = typer.Option("dados abertos", help="Licença declarada da fonte."),
    base_legal: str = typer.Option("", help="Base legal, obrigatória para origem institucional."),
) -> None:
    """Registra a importação com validação, hash e verificação de PII."""
    from frequencia.dados import importacao

    contexto = _ctx(ctx)
    try:
        if contexto.seco:
            contexto_mod.emitir(
                contexto,
                {"acao": "importar", "pasta": str(pasta), "origem": origem},
                titulo="Modo seco: a importação registraria o pacote a seguir.",
            )
            return
        manifesto = importacao.registrar_importacao(
            pasta, origem=origem, licenca=licenca, base_legal=base_legal, detalhado=contexto.detalhado
        )
        contexto_mod.emitir(contexto, manifesto, titulo="Importação registrada:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("validar")
def validar(ctx: typer.Context, pasta: Path = typer.Argument(...)) -> None:
    """Valida o esquema de todas as tabelas do pacote."""
    from frequencia.dados import sintetico

    contexto = _ctx(ctx)
    try:
        pacote = sintetico.carregar_pacote(pasta)
        contexto_mod.emitir(contexto, pacote["contagens"], titulo="Pacote válido:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("verificar-licenca")
def verificar_licenca(ctx: typer.Context, identificador: str = typer.Argument(...)) -> None:
    """Mostra a licença e as restrições de uma fonte do catálogo."""
    from frequencia.dados import mec

    contexto = _ctx(ctx)
    try:
        fonte = mec.fonte_por_identificador(identificador)
        corpo = {
            "fonte": fonte["nome"],
            "licenca": fonte["licenca"],
            "restricoes": list(mec.restricoes_de_uso()),
        }
        contexto_mod.emitir(contexto, corpo)
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("registrar-hash")
def registrar_hash(ctx: typer.Context, pasta: Path = typer.Argument(...)) -> None:
    """Calcula o hash SHA-256 da pasta de dados e o registra no log."""
    contexto = _ctx(ctx)
    try:
        digestao = hash_infra.hash_pasta(pasta)
        from frequencia.infra import logs

        logs.registrar("dados.hash", estagio="dados", pasta=str(pasta), hash=digestao)
        contexto_mod.emitir(contexto, {"pasta": str(pasta), "hash": digestao})
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("gerar-perfil")
def gerar_perfil(ctx: typer.Context, pasta: Path = typer.Argument(...)) -> None:
    """Gera o perfil estatístico das tabelas do pacote."""
    from frequencia.dados import importacao

    contexto = _ctx(ctx)
    try:
        perfil = importacao.gerar_perfil(pasta)
        resumo = {tabela: corpo["linhas"] for tabela, corpo in perfil["tabelas"].items()}
        contexto_mod.emitir(contexto, resumo, titulo="Linhas por tabela:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("detectar-pii")
def detectar_pii(ctx: typer.Context, pasta: Path = typer.Argument(...)) -> None:
    """Varre os campos de texto do pacote atrás de dados pessoais."""
    from frequencia.dados import sintetico
    from frequencia.privacidade import detector

    contexto = _ctx(ctx)
    try:
        tabelas = sintetico.carregar_pacote(pasta)["tabelas"]
        achados = detector.examinar_tabelas(tabelas)
        if achados or contexto.json:
            contexto_mod.emitir(contexto, achados, titulo="Achados de privacidade:")
        else:
            print("Nenhum dado pessoal detectado.")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("versionar")
def versionar(ctx: typer.Context, pasta: Path = typer.Argument(...)) -> None:
    """Versiona o pacote com DVC sem repositório Git (hash e manifesto .dvc)."""
    contexto = _ctx(ctx)
    try:
        if contexto.seco:
            contexto_mod.emitir(
                contexto,
                {"acao": "versionar", "pasta": str(pasta)},
                titulo="Modo seco: criaria o arquivo .dvc e o cache local.",
            )
            return
        resultado = _versionar_dvc(pasta)
        contexto_mod.emitir(contexto, resultado, titulo="Versionamento DVC:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


def _versionar_dvc(pasta: Path) -> dict:
    """Executa o versionamento DVC em modo sem SCM."""
    import subprocess

    pasta = Path(pasta).resolve()
    raiz = pasta.parent
    comando = ["dvc", "add", str(pasta.relative_to(raiz)), "--no-commit"]
    if not (raiz / ".dvc").exists():
        subprocess.run(["dvc", "init", "--no-scm"], cwd=raiz, check=True, capture_output=True, timeout=120)
    concluido = subprocess.run(comando, cwd=raiz, check=True, capture_output=True, text=True, timeout=300)
    _ = concluido
    alvo_dvc = raiz / f"{pasta.name}.dvc"
    corpo: dict = {"pasta": str(pasta), "arquivo_dvc": str(alvo_dvc)}
    if alvo_dvc.is_file():
        declaracao = json.loads(alvo_dvc.read_text(encoding="utf-8"))
        corpo["hash"] = declaracao["outs"][0]["md5"]
    return corpo


@app.command("gerar-sintetico")
def gerar_sintetico(
    ctx: typer.Context,
    perfil: str = typer.Option("fumaca", help="Perfil de volume: amostra, fumaca ou padrao."),
    semente: int = typer.Option(20261018, help="Semente determinística da geração."),
    ano: int = typer.Option(2026, help="Ano letivo simulado."),
    alunos: int = typer.Option(None, help="Alunos por turma (sobrepõe o perfil)."),
    destino: Path = typer.Option(None, help="Pasta destino (padrão: workspace/var/dados/sinteticos)."),
) -> None:
    """Gera o pacote de dados sintéticos completo, sem dados pessoais."""
    from frequencia.dados import sintetico
    from frequencia.infra import caminhos

    contexto = _ctx(ctx)
    try:
        alvo = destino or (caminhos.caminho("sinteticos") / f"perfil-{perfil}")
        if contexto.seco:
            corpo = {
                "acao": "gerar-sintetico",
                "perfil": perfil,
                "semente": semente,
                "destino": str(alvo),
            }
            contexto_mod.emitir(contexto, corpo, titulo="Modo seco: geraria o pacote a seguir.")
            return
        resultado = sintetico.gerar(
            sintetico.ConfigSintetico(
                perfil=perfil,
                semente=semente,
                ano=ano,
                alunos_por_turma=alunos,
                destino=alvo,
            ),
            detalhado=contexto.detalhado,
        )
        corpo = {
            "destino": str(alvo),
            "contagens": resultado["meta"]["contagens"],
            "dias_letivos": resultado["meta"]["dias_letivos"],
            "perfis_escola": resultado["meta"]["perfis_escola"],
        }
        contexto_mod.emitir(contexto, corpo, titulo="Pacote sintético gerado:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("verificar-integridade")
def verificar_integridade(ctx: typer.Context, pasta: Path = typer.Argument(...)) -> None:
    """Confere os hashes dos arquivos contra o meta.json do pacote."""
    contexto = _ctx(ctx)
    try:
        from frequencia.infra import hash as hash_mod

        meta = json.loads((pasta / "meta.json").read_text(encoding="utf-8"))
        declarados = meta.get("hashes", {})
        veredito = hash_mod.resumo_integridade(pasta, declarados)
        contexto_mod.emitir(contexto, veredito, titulo="Integridade dos arquivos:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)
