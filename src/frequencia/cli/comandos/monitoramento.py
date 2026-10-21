# Comandos de monitoramento: feedback, drift, validade e saúde.
"""Acompanhamento pós-publicação com dados agregados."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl
import typer

from frequencia.cli import contexto as contexto_mod
from frequencia.cli.contexto import Contexto

app = typer.Typer(no_args_is_help=True, help="Drift, validade, feedback e recomendações.")


def _ctx(ctx: typer.Context) -> Contexto:
    return ctx.obj or contexto_mod.Contexto()


@app.command("importar-feedback")
def importar_feedback(
    ctx: typer.Context,
    arquivo: Path = typer.Argument(..., help="JSON com dias, acuracia_observada e taxa_descarte."),
    fonte: str = typer.Option("painel", help="Fonte do feedback agregado."),
) -> None:
    """Registra feedback agregado por dia, sem dado individual."""
    from frequencia.monitoramento import saude

    contexto = _ctx(ctx)
    try:
        corpo = json.loads(arquivo.read_text(encoding="utf-8"))
        registro = saude.registrar_feedback(
            dias=corpo["dias"],
            acuracia_observada=corpo["acuracia_observada"],
            taxa_descarte=corpo["taxa_descarte"],
            fonte=fonte,
        )
        contexto_mod.emitir(contexto, registro, titulo="Feedback registrado:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("acuracia-observada")
def acuracia_observada(ctx: typer.Context) -> None:
    """Resume a acurácia observada do feedback mais recente."""
    from frequencia.monitoramento import saude

    contexto = _ctx(ctx)
    try:
        feedback = saude.ler_feedback()
        if not feedback:
            contexto_mod.emitir(contexto, "Nenhum feedback registrado ainda.")
            return
        ultimo = feedback[-1]
        media = sum(ultimo["acuracia_observada"]) / max(1, len(ultimo["acuracia_observada"]))
        contexto_mod.emitir(
            contexto,
            {"acuracia_media": round(media, 4), "dias": len(ultimo["dias"])},
        )
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("taxa-descarte")
def taxa_descarte(ctx: typer.Context) -> None:
    """Resume a taxa de descarte do indicador no feedback recente."""
    from frequencia.monitoramento import saude

    contexto = _ctx(ctx)
    try:
        feedback = saude.ler_feedback()
        if not feedback:
            contexto_mod.emitir(contexto, "Nenhum feedback registrado ainda.")
            return
        ultimo = feedback[-1]
        media = sum(ultimo["taxa_descarte"]) / max(1, len(ultimo["taxa_descarte"]))
        contexto_mod.emitir(contexto, {"taxa_descarte_media": round(media, 4)})
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("drift")
def drift(
    ctx: typer.Context,
    pasta_experimento: Path = typer.Argument(...),
    pasta_atual: Path = typer.Argument(..., help="Pacote de dados com a fotografia atual."),
) -> None:
    """Calcula o drift de features entre o treino e a fotografia atual."""

    from frequencia.features.catalogo import NOMES_FEATURES
    from frequencia.monitoramento import saude

    contexto = _ctx(ctx)
    try:
        dados = _dataset_do_experimento(pasta_experimento)
        referencia = dados.select(NOMES_FEATURES)
        atual = _features_da_fotografia(pasta_atual)
        corpo = saude.calcular_drift(referencia, atual)
        with (Path(pasta_experimento) / "drift.json").open("w", encoding="utf-8") as saida:
            json.dump(corpo, saida, ensure_ascii=False, indent=2, sort_keys=True)
        contexto_mod.emitir(contexto, corpo["piores"], titulo="Maior drift por feature:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("validade")
def validade(ctx: typer.Context) -> None:
    """Verifica a validade da versão publicada atual."""
    from frequencia.modelos import publicacao

    contexto = _ctx(ctx)
    try:
        atual = publicacao.versao_atual()
        if not atual:
            contexto_mod.emitir(contexto, "Nenhuma versão publicada no registro.")
            return
        corpo = {
            "versao": atual["versao"],
            "validade_ate": atual.get("validade_ate"),
            "vencida": _vencida(atual.get("validade_ate")),
        }
        contexto_mod.emitir(contexto, corpo)
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("recalibrar")
def recalibrar(ctx: typer.Context, pasta_experimento: Path = typer.Argument(...)) -> None:
    """Reexecuta a etapa de calibração com os dados do experimento."""
    from frequencia.pipelines import experimento as exp_mod

    contexto = _ctx(ctx)
    try:
        from frequencia.pipelines import dataset as dataset_mod

        pasta_experimento = Path(pasta_experimento)
        estado = json.loads((pasta_experimento / "estado.json").read_text(encoding="utf-8"))
        pasta_dataset = Path(estado["config"]["pasta_dataset"])
        dados = dataset_mod.carregar_dataset(pasta_dataset)["dataset"]
        resultado = exp_mod._executar_calibracao(
            exp_mod.ConfigExperimento(pasta_dataset=pasta_dataset),
            pasta_experimento,
            dados,
            contexto.detalhado,
        )
        contexto_mod.emitir(contexto, resultado["resumo"], titulo="Recalibração:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("relatorio-saude")
def relatorio_saude(ctx: typer.Context, pasta_experimento: Path = typer.Option(None)) -> None:
    """Gera o relatório de saúde com recomendações."""
    from frequencia.monitoramento import saude

    contexto = _ctx(ctx)
    try:
        corpo = saude.relatorio_saude(pasta_experimento=pasta_experimento)
        from frequencia.infra import caminhos

        alvo = caminhos.caminho("relatorios") / "relatorio-saude.json"
        alvo.write_text(json.dumps(corpo, ensure_ascii=False, indent=2), encoding="utf-8")
        corpo["arquivo"] = str(alvo)
        contexto_mod.emitir(contexto, corpo, titulo="Relatório de saúde:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("recomendar-retreinamento")
def recomendar_retreinamento(ctx: typer.Context) -> None:
    """Recomenda retreinamento com base em validade, drift e feedback."""
    from frequencia.monitoramento import saude

    contexto = _ctx(ctx)
    try:
        corpo = saude.relatorio_saude()
        contexto_mod.emitir(contexto, corpo["recomendacoes"], titulo="Recomendações:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


def _vencida(validade: str | None) -> bool:
    from datetime import UTC, datetime

    if not validade:
        return False
    alvo = datetime.fromisoformat(validade).replace(tzinfo=UTC)
    return datetime.now(UTC) > alvo


def _dataset_do_experimento(pasta: Path) -> pl.DataFrame:
    from frequencia.pipelines import dataset as dataset_mod

    alvo = Path(pasta) / "estado.json"
    estado = json.loads(alvo.read_text(encoding="utf-8"))
    pasta_dataset = estado.get("config", {}).get("pasta_dataset")
    return dataset_mod.carregar_dataset(Path(pasta_dataset))["dataset"]


def _features_da_fotografia(pasta_atual: Path) -> pl.DataFrame:
    """Recalcula as features de referência a partir da fotografia atual."""
    from frequencia.dados import sintetico
    from frequencia.features import calculo
    from frequencia.features import diario as diario_mod

    pacote = sintetico.carregar_pacote(pasta_atual)
    tabelas = pacote["tabelas"]
    feriados = [
        __import__("datetime").date.fromisoformat(valor)
        for valor in tabelas["feriados"]["dia"].drop_nulls().to_list()
    ]
    dia = sorted(tabelas["frequencias"]["dia"].unique().to_list())[-1]
    diario = diario_mod.materializar(tabelas, instante=None, ate_dia=dia)
    return calculo.calcular(
        diario,
        dia_referencia=dia,
        contexto_mec=tabelas["contexto_mec"],
        feriados=feriados,
        dias_restantes_periodo=0,
    )
