# Comandos de features: catálogo, contrato, distribuição e congelamento.
"""Inspeção e governança do contrato de features."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from frequencia.cli import contexto as contexto_mod
from frequencia.cli.contexto import Contexto

app = typer.Typer(no_args_is_help=True, help="Catálogo de features como contrato versionado.")


def _ctx(ctx: typer.Context) -> Contexto:
    return ctx.obj or contexto_mod.Contexto()


@app.command("listar")
def listar(ctx: typer.Context) -> None:
    """Lista as features do catálogo com tipo, origem e janela."""
    from frequencia.features.catalogo import CATALOGO

    contexto = _ctx(ctx)
    try:
        linhas = [
            {
                "feature": spec.nome,
                "tipo": spec.tipo,
                "origem": spec.origem,
                "janela": spec.janela,
                "dependencia": spec.dependencia or "",
            }
            for spec in CATALOGO
        ]
        contexto_mod.emitir(contexto, linhas, titulo="Catálogo de features:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("validar-contrato")
def validar_contrato(ctx: typer.Context) -> None:
    """Valida a integridade do catálogo: nomes, tipos e vocabulários."""
    from frequencia.features.catalogo import validar_contrato as validar

    contexto = _ctx(ctx)
    try:
        veredito = validar()
        contexto_mod.emitir(contexto, veredito, titulo="Contrato de features:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("gerar-dicionario")
def gerar_dicionario(ctx: typer.Context, destino: Path = typer.Option(None)) -> None:
    """Exporta o dicionário de features em JSON."""
    from frequencia.features.catalogo import exportar_json
    from frequencia.infra import caminhos

    contexto = _ctx(ctx)
    try:
        alvo = destino or caminhos.caminho("relatorios") / "dicionario-features.json"
        corpo = exportar_json()
        alvo.write_text(json.dumps(corpo, ensure_ascii=False, indent=2), encoding="utf-8")
        contexto_mod.emitir(
            contexto,
            {"arquivo": str(alvo), "features": len(corpo["features"])},
        )
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("verificar-dependencia")
def verificar_dependencia(ctx: typer.Context) -> None:
    """Mostra as features que dependem de cada flag do FrequenciApp."""
    from frequencia.features.catalogo import dependentes_de_configuracao

    contexto = _ctx(ctx)
    try:
        mapa = dependentes_de_configuracao()
        contexto_mod.emitir(contexto, mapa, titulo="Dependências de configuração:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("gerar-distribuicao")
def gerar_distribuicao(
    ctx: typer.Context,
    pasta_dataset: Path = typer.Argument(...),
    feature: str = typer.Option("", help="Feature única; vazio resume todas."),
) -> None:
    """Resume a distribuição das features do dataset de treino."""

    from frequencia.features.catalogo import NOMES_FEATURES
    from frequencia.pipelines import dataset as dataset_mod

    contexto = _ctx(ctx)
    try:
        dados = dataset_mod.carregar_dataset(pasta_dataset)["dataset"]
        colunas = [feature] if feature else list(NOMES_FEATURES)
        estatisticas = dados.select(colunas).describe()
        corpo = {
            coluna: {
                "min": estatisticas[coluna][0],
                "media": round(float(estatisticas[coluna][1]), 4),
                "max": estatisticas[coluna][3],
                "nulos": dados[coluna].null_count(),
            }
            for coluna in colunas
        }
        contexto_mod.emitir(contexto, corpo, titulo="Distribuição das features:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("detectar-constantes")
def detectar_constantes(ctx: typer.Context, pasta_dataset: Path = typer.Argument(...)) -> None:
    """Aponta features constantes no dataset, que não ajudam o modelo."""

    from frequencia.pipelines import dataset as dataset_mod

    contexto = _ctx(ctx)
    try:
        dados = dataset_mod.carregar_dataset(pasta_dataset)["dataset"]
        constantes = [
            coluna
            for coluna in dados.columns
            if coluna not in ("aluno_id", "dia", "rotulo", "divisao") and dados[coluna].n_unique() <= 1
        ]
        contexto_mod.emitir(
            contexto,
            constantes if constantes else "Nenhuma feature constante.",
            titulo="Features constantes:",
        )
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("detectar-nulos")
def detectar_nulos(ctx: typer.Context, pasta_dataset: Path = typer.Argument(...)) -> None:
    """Conta valores nulos por feature após o preenchimento de padrões."""

    from frequencia.pipelines import dataset as dataset_mod

    contexto = _ctx(ctx)
    try:
        dados = dataset_mod.carregar_dataset(pasta_dataset)["dataset"]
        nulos = {
            coluna: dados[coluna].null_count()
            for coluna in dados.columns
            if coluna not in ("aluno_id", "dia", "rotulo", "divisao")
        }
        com_nulos = {col: total for col, total in nulos.items() if total > 0}
        contexto_mod.emitir(
            contexto,
            com_nulos if com_nulos else "Nenhum nulo após os padrões do contrato.",
            titulo="Nulos por feature:",
        )
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("verificar-vazamento")
def verificar_vazamento(ctx: typer.Context, pasta_dataset: Path = typer.Argument(...)) -> None:
    """Verifica a ausência de futuro nas features de uma amostra."""
    from frequencia.pipelines import dataset as dataset_mod

    contexto = _ctx(ctx)
    try:
        veredito = dataset_mod.validar_ausencia_de_futuro(pasta_dataset)
        contexto_mod.emitir(contexto, veredito, titulo="Verificação de vazamento temporal:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("congelar")
def congelar(ctx: typer.Context, destino: Path = typer.Option(None)) -> None:
    """Congela a versão do catálogo no estado do workspace."""
    from frequencia.features.catalogo import VERSAO_CATALOGO, exportar_json
    from frequencia.infra import caminhos
    from frequencia.infra import estado as estado_infra

    contexto = _ctx(ctx)
    try:
        alvo = destino or caminhos.caminho("estado") / "catalogo-congelado.json"
        corpo = exportar_json()
        alvo.write_text(json.dumps(corpo, ensure_ascii=False, indent=2), encoding="utf-8")
        contexto.auditar("features.congelar", alvo=str(alvo), versao=VERSAO_CATALOGO)
        estado_infra.registrar_auditoria("features.congelar", alvo=str(alvo), versao=VERSAO_CATALOGO)
        contexto_mod.emitir(contexto, {"arquivo": str(alvo), "versao": VERSAO_CATALOGO})
    except Exception as exc:
        contexto_mod.falha(contexto, exc)
