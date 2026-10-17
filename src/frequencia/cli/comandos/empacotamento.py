# Comandos de empacotamento: montagem, validação e assinatura lógica.
"""Pacotes de distribuição prontos para homologação e publicação."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from frequencia.cli import contexto as contexto_mod
from frequencia.cli.contexto import Contexto

app = typer.Typer(no_args_is_help=True, help="Montagem e validação do pacote de distribuição.")


def _ctx(ctx: typer.Context) -> Contexto:
    return ctx.obj or contexto_mod.Contexto()


@app.command("montar")
def montar(ctx: typer.Context, pasta_experimento: Path = typer.Argument(...)) -> None:
    """Monta o pacote com modelo, manifesto, fallback e cartão."""
    from frequencia.infra import caminhos

    contexto = _ctx(ctx)
    try:
        if contexto.seco:
            corpo = {
                "acao": "empacotamento.montar",
                "experimento": str(pasta_experimento),
                "arquivos": [
                    "modelo.js",
                    "fallback.js",
                    "manifest.json",
                    "dados-teste.json",
                    "modelo-cartao.md",
                    "LEIA-ME.md",
                    "contexto-mec.json",
                ],
            }
            contexto_mod.emitir(contexto, corpo, titulo="Modo seco: montaria o pacote a seguir.")
            return
        alvo = caminhos.caminho("pacotes")
        _ = alvo
        # A montagem faz parte do ciclo; aqui remonta a partir do experimento.
        resultado = _remontar(pasta_experimento)
        contexto_mod.emitir(
            contexto,
            {"pacote": resultado["zip"], "tamanho_zip_bytes": resultado["tamanho_zip_bytes"]},
            titulo="Pacote montado:",
        )
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


def _remontar(pasta_experimento: Path) -> dict:
    """Remonta o pacote a partir dos artefatos gravados do experimento."""
    from frequencia.distribuicao import pacote as pacote_mod
    from frequencia.infra import caminhos

    pasta_experimento = Path(pasta_experimento)
    alvo_export = pasta_experimento / "exportacoes"
    validacao = json.loads((alvo_export / "validacao.json").read_text(encoding="utf-8"))
    estado = json.loads((pasta_experimento / "estado.json").read_text(encoding="utf-8"))
    params = estado["etapas"]["exportacao"]["resultado"]["params"]
    dados_teste = json.loads((alvo_export / "dados-teste.json").read_text(encoding="utf-8"))
    nucleo = exp_nucleo(alvo_export / "modelo.js")
    versao = validacao.get("versao_modelo") or estado.get("config", {}).get("versao_modelo") or "remontado"
    destino = caminhos.caminho("pacotes") / f"risco-infrequencia-{versao}"
    if destino.exists():
        destino = caminhos.caminho("pacotes") / f"risco-infrequencia-{versao}-{pasta_experimento.name}"
    corpo_cartao = _cartao_minimo(params)
    return pacote_mod.montar_pacote(
        pasta_destino=destino,
        nucleo_js=nucleo,
        params=params,
        versao_modelo=versao,
        dados_teste=dados_teste,
        cartao_markdown=corpo_cartao,
        contexto_mec_json=None,
        identificador="risco-infrequencia",
    )


def exp_nucleo(caminho_modelo_js: Path) -> str:
    """Extrai o núcleo do modelo.js gravado."""
    texto = Path(caminho_modelo_js).read_text(encoding="utf-8")
    inicio = texto.index("function score(")
    fim = texto.index("function logit(")
    return texto[inicio:fim].rstrip() + "\n"


def _cartao_minimo(params: dict) -> str:
    """Cartão resumido para remontagens pela CLI."""
    versao = params.get("identificacao", {}).get("versao_modelo", "n/d")
    return (
        "# Cartão do modelo: risco de infrequência\n\n"
        f"- Versão: {versao}\n"
        "- Treinado com dados sintéticos, sem dados pessoais reais.\n"
        "- Indicador de apoio à coordenação, sujeito a revisão humana.\n"
        "- Inferência local no navegador; limite e mensagens no manifesto.\n"
    )


@app.command("validar")
def validar(ctx: typer.Context, pacote: Path = typer.Argument(...)) -> None:
    """Valida a integridade do pacote: arquivos e hashes do manifesto."""
    from frequencia.distribuicao import pacote as pacote_mod

    contexto = _ctx(ctx)
    try:
        veredito = pacote_mod.validar_pacote(pacote)
        contexto_mod.emitir(contexto, veredito, titulo="Validação do pacote:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("homologacao")
def homologacao(
    ctx: typer.Context,
    pacote: Path = typer.Argument(...),
    versao: str = typer.Option(..., help="Versão do modelo no pacote."),
) -> None:
    """Promove o pacote validado para o estado de homologação."""
    from frequencia.modelos import registro as registro_mod

    contexto = _ctx(ctx)
    try:
        versao_modelo = registro_mod.promover_modelo(
            "risco-infrequencia", versao, "homologado", ator=contexto.ator, papel=contexto.papel
        )
        contexto_mod.emitir(contexto, {"versao": versao, "situacao": versao_modelo["situacao"]})
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("publicacao")
def publicacao_cmd(
    ctx: typer.Context,
    pacote: Path = typer.Argument(...),
    versao: str = typer.Argument(...),
    notas: str = typer.Option("", help="Notas de mudança da versão."),
) -> None:
    """Publica o pacote homologado no canal local de releases."""
    from frequencia.modelos import publicacao

    contexto = _ctx(ctx)
    try:
        if contexto.papel != "aprovador":
            msg = "Publicação exige o papel de aprovador. Use --papel aprovador."
            raise PermissionError(msg)
        resultado = publicacao.publicar(
            pacote, versao_modelo=versao, notas=notas, ator=contexto.ator, papel=contexto.papel
        )
        contexto_mod.emitir(contexto, resultado, titulo="Publicação concluída:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("assinar")
def assinar(ctx: typer.Context, pacote: Path = typer.Argument(...)) -> None:
    """Confere a assinatura lógica: hashes dos arquivos do manifesto."""
    from frequencia.distribuicao import pacote as pacote_mod
    from frequencia.infra import hash as hash_mod

    contexto = _ctx(ctx)
    try:
        manifesto = json.loads((Path(pacote) / "manifest.json").read_text(encoding="utf-8"))
        integridade = pacote_mod.validar_pacote(pacote)
        corpo = {
            "hash_modelo": manifesto.get("hash_modelo"),
            "hash_atual": hash_mod.hash_arquivo(Path(pacote) / "modelo.js")
            if (Path(pacote) / "modelo.js").is_file()
            else "",
            "integro": integridade["integro"],
        }
        contexto.auditar("empacotamento.assinar", alvo=str(pacote))
        contexto_mod.emitir(contexto, corpo, titulo="Assinatura lógica:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)
