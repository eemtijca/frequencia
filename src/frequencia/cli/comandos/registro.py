# Comandos do registro: estados, promoções, aprovações e histórico.
"""Registro versionado de modelos do FrequencIA."""

from __future__ import annotations

import typer

from frequencia.cli import contexto as contexto_mod
from frequencia.cli.contexto import Contexto

app = typer.Typer(no_args_is_help=True, help="Registro de modelos: estados e promoções.")


def _ctx(ctx: typer.Context) -> Contexto:
    return ctx.obj or contexto_mod.Contexto()


@app.command("registrar")
def registrar(
    ctx: typer.Context,
    identificador: str = typer.Argument(...),
    versao: str = typer.Argument(...),
    artefato: str = typer.Option(..., help="Caminho do artefato exportado (zip)."),
    validade: str = typer.Option("", help="Data de validade em ISO."),
) -> None:
    """Registra uma versão nova no estado experimental."""
    from frequencia.infra import caminhos
    from frequencia.infra import estado as estado_infra
    from frequencia.infra import hash as hash_mod

    contexto = _ctx(ctx)
    try:
        from datetime import UTC, datetime, timedelta

        alvo = caminhos.caminho("artefatos") / "experimentos" / identificador
        alvo = __import__("pathlib").Path(artefato)
        tamanho = alvo.stat().st_size if alvo.is_file() else 0
        digestao = hash_mod.hash_arquivo(alvo) if alvo.is_file() else ""
        validade_final = validade or (datetime.now(UTC) + timedelta(days=180)).strftime("%Y-%m-%d")
        corpo = estado_infra.registrar_modelo(
            identificador,
            versao,
            runtime_alvo="js-m2cgen",
            hash_artefato=digestao,
            tamanho_bytes=tamanho,
            dataset={},
            metricas={},
            limitacoes=[],
            referencia_artefato=artefato,
            validade_ate=validade_final,
        )
        contexto_mod.emitir(contexto, corpo, titulo="Versão registrada:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("promover")
def promover(
    ctx: typer.Context,
    identificador: str = typer.Argument(...),
    versao: str = typer.Argument(...),
    estado: str = typer.Option(..., help="Estado destino da promoção."),
    justificativa: str = typer.Option("", help="Motivo registrado na auditoria."),
) -> None:
    """Promove a versão entre estados com transição validada."""
    from frequencia.modelos import registro as registro_mod

    contexto = _ctx(ctx)
    try:
        corpo = registro_mod.promover_modelo(
            identificador,
            versao,
            estado,
            ator=contexto.ator,
            papel=contexto.papel,
            justificativa=justificativa,
        )
        contexto_mod.emitir(contexto, {"versao": versao, "situacao": corpo["situacao"]})
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("descontinuar")
def descontinuar(
    ctx: typer.Context,
    identificador: str = typer.Argument(...),
    versao: str = typer.Argument(...),
    motivo: str = typer.Option("", help="Motivo da descontinuação."),
) -> None:
    """Descontinua a versão com motivo auditado."""
    from frequencia.modelos import registro as registro_mod

    contexto = _ctx(ctx)
    try:
        corpo = registro_mod.descontinuar(identificador, versao, ator=contexto.ator, motivo=motivo)
        contexto_mod.emitir(contexto, {"versao": versao, "situacao": corpo["situacao"]})
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("arquivar")
def arquivar(
    ctx: typer.Context, identificador: str = typer.Argument(...), versao: str = typer.Argument(...)
) -> None:
    """Arquiva a versão retirando-a do ciclo ativo."""
    from frequencia.modelos import registro as registro_mod

    contexto = _ctx(ctx)
    try:
        corpo = registro_mod.promover_modelo(
            identificador, versao, "arquivado", ator=contexto.ator, papel=contexto.papel
        )
        contexto_mod.emitir(contexto, {"versao": versao, "situacao": corpo["situacao"]})
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("atualizar-estado")
def atualizar_estado(
    ctx: typer.Context,
    identificador: str = typer.Argument(...),
    versao: str = typer.Argument(...),
    situacao: str = typer.Option(..., help="Situação alvo da versão."),
) -> None:
    """Atualiza a situação da versão com verificação de transição."""
    from frequencia.modelos import registro as registro_mod

    contexto = _ctx(ctx)
    try:
        corpo = registro_mod.promover_modelo(
            identificador, versao, situacao, ator=contexto.ator, papel=contexto.papel
        )
        contexto_mod.emitir(contexto, {"versao": versao, "situacao": corpo["situacao"]})
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("listar")
def listar(ctx: typer.Context, identificador: str = typer.Argument("risco-infrequencia")) -> None:
    """Lista as versões registradas do modelo."""
    from frequencia.modelos import registro as registro_mod

    contexto = _ctx(ctx)
    try:
        versoes = registro_mod.listar_versoes(identificador)
        linhas = [
            {
                "versao": corpo["versao"],
                "situacao": corpo["situacao"],
                "treinado_em": corpo["treinado_em"],
                "validade_ate": corpo["validade_ate"],
            }
            for corpo in versoes
        ]
        contexto_mod.emitir(contexto, linhas, titulo=f"Versões de {identificador}:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("comparar")
def comparar(
    ctx: typer.Context,
    identificador: str = typer.Argument(...),
    versao_a: str = typer.Argument(...),
    versao_b: str = typer.Argument(...),
) -> None:
    """Compara métricas de duas versões registradas."""
    from frequencia.modelos import registro as registro_mod

    contexto = _ctx(ctx)
    try:
        versoes = registro_mod.listar_versoes(identificador)
        corpo_a = next((v for v in versoes if v["versao"] == versao_a), None)
        corpo_b = next((v for v in versoes if v["versao"] == versao_b), None)
        if not corpo_a or not corpo_b:
            msg = "Uma das versões não consta no registro."
            raise ValueError(msg)
        saida = {
            "metricas_a": corpo_a.get("metricas", {}),
            "metricas_b": corpo_b.get("metricas", {}),
            "diferenca": {
                chave: round(
                    float(corpo_a["metricas"].get(chave, 0)) - float(corpo_b["metricas"].get(chave, 0)),
                    4,
                )
                for chave in set(corpo_a.get("metricas", {})) | set(corpo_b.get("metricas", {}))
            },
        }
        contexto_mod.emitir(contexto, saida, titulo="Comparação de versões:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("aprovar")
def aprovar(
    ctx: typer.Context,
    identificador: str = typer.Argument(...),
    versao: str = typer.Argument(...),
    comentario: str = typer.Option("", help="Comentário da aprovação."),
) -> None:
    """Registra aprovação da versão com o papel atual."""
    from frequencia.modelos import registro as registro_mod

    contexto = _ctx(ctx)
    try:
        corpo = registro_mod.aprovar_modelo(
            identificador, versao, True, ator=contexto.ator, comentario=comentario
        )
        contexto_mod.emitir(contexto, {"versao": versao, "aprovacoes": len(corpo["aprovacoes"])})
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("rejeitar")
def rejeitar(
    ctx: typer.Context,
    identificador: str = typer.Argument(...),
    versao: str = typer.Argument(...),
    comentario: str = typer.Option("", help="Comentário da rejeição."),
) -> None:
    """Registra rejeição da versão com o papel atual."""
    from frequencia.modelos import registro as registro_mod

    contexto = _ctx(ctx)
    try:
        corpo = registro_mod.aprovar_modelo(
            identificador, versao, False, ator=contexto.ator, comentario=comentario
        )
        contexto_mod.emitir(contexto, {"versao": versao, "aprovacoes": len(corpo["aprovacoes"])})
    except Exception as exc:
        contexto_mod.falha(contexto, exc)
