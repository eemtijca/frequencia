# Comandos de experimentos: ciclo completo, execução e recuperação.
"""Ciclo de vida dos experimentos de modelagem."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import polars as pl

import typer

from frequencia.cli import contexto as contexto_mod
from frequencia.cli.contexto import Contexto
from frequencia.pipelines import experimento as experimento_mod

app = typer.Typer(no_args_is_help=True, help="Experimentos: treino, ensemble, destilação e ciclo.")


def _ctx(ctx: typer.Context) -> Contexto:
    return ctx.obj or contexto_mod.Contexto()


@app.command("criar")
def criar(
    ctx: typer.Context,
    pasta_dataset: Path = typer.Argument(...),
    identificador: str = typer.Option("", help="Identificador curto do experimento."),
    semente: int = typer.Option(20261018, help="Semente determinística."),
    versao_modelo: str = typer.Option("", help="Versão do modelo a gerar (padrão: data)."),
    config: Path = typer.Option(None, help="Arquivo YAML declarativo do experimento."),
) -> None:
    """Cria a configuração declarativa de um experimento."""
    from frequencia.infra import caminhos

    contexto = _ctx(ctx)
    try:
        parametros: dict[str, Any] = {}
        if config is not None and config.is_file():
            import yaml

            parametros = yaml.safe_load(config.read_text(encoding="utf-8")) or {}
        identificacao = identificador or "novo-experimento"
        destino = caminhos.caminho("artefatos") / "experimentos" / identificacao
        destino.mkdir(parents=True, exist_ok=True)
        corpo = {
            "identificador": identificacao,
            "pasta_dataset": str(pasta_dataset),
            "semente": parametros.get("semente", semente),
            "versao_modelo": parametros.get("versao_modelo", versao_modelo),
            "min_app_versao": parametros.get("min_app_versao", "1.4.0"),
            "tentativas_optuna": parametros.get("tentativas_optuna", 0),
            "dobras_ensemble": parametros.get("dobras_ensemble", 3),
            "taxa_alerta_alvo": parametros.get("taxa_alerta_alvo", 0.10),
        }
        with (destino / "config.json").open("w", encoding="utf-8") as saida:
            json.dump(corpo, saida, ensure_ascii=False, indent=2, sort_keys=True)
        contexto_mod.emitir(contexto, corpo, titulo="Experimento declarado:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("executar")
def executar(
    ctx: typer.Context,
    pasta_dataset: Path = typer.Argument(...),
    identificador: str = typer.Option("", help="Identificador do experimento."),
    semente: int = typer.Option(20261018),
    tentativas: int = typer.Option(0, help="Chamadas ao Optuna (0 desliga a busca)."),
    dobras: int = typer.Option(3, help="Dobras temporais do ensemble."),
    versao_modelo: str = typer.Option("", help="Versão explícita do modelo gerado."),
    min_app: str = typer.Option("1.4.0", help="Versão mínima do FrequenciApp."),
    taxa_alerta_alvo: float = typer.Option(
        0.10, help="Fração-alvo de alunos acima do limiar de entrada do alerta (capacidade da escola)."
    ),
) -> None:
    """Executa o ciclo completo: treino, ensemble, destilação, calibração,
    avaliação, exportação e empacotamento, com idempotência por etapa."""
    contexto = _ctx(ctx)
    try:
        contexto.exigir_justificativa()
        if contexto.seco:
            corpo = {
                "acao": "experimento.executar",
                "etapas": list(experimento_mod.ETAPAS),
                "pasta_dataset": str(pasta_dataset),
                "identificador": identificador or "automático",
            }
            contexto_mod.emitir(contexto, corpo, titulo="Modo seco: executaria as etapas a seguir.")
            return
        config = experimento_mod.ConfigExperimento(
            pasta_dataset=pasta_dataset,
            identificador=identificador,
            semente=semente,
            tentativas_optuna=tentativas,
            dobras_ensemble=dobras,
            versao_modelo=versao_modelo,
            min_app_versao=min_app,
            taxa_alerta_alvo=taxa_alerta_alvo,
        )
        resumo = experimento_mod.executar(
            config,
            forcar=contexto.forca,
            justificativa=contexto.justificativa,
            detalhado=contexto.detalhado,
        )
        contexto_mod.emitir(contexto, resumo, titulo="Ciclo concluído:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("treinar")
def treinar(ctx: typer.Context, pasta_dataset: Path = typer.Argument(...)) -> None:
    """Executa apenas a etapa de treinamento do modelo principal."""
    from frequencia.pipelines import treino as treino_mod

    contexto = _ctx(ctx)
    try:
        config = treino_mod.ConfigTreino(pasta_dataset=pasta_dataset)
        resultado = treino_mod.treinar(config, detalhado=contexto.detalhado)
        corpo = {
            "identificador": resultado.identificador,
            "metricas": resultado.metricas,
            "pasta": str(resultado.pasta),
            "run_mlflow": resultado.run_mlflow,
        }
        contexto_mod.emitir(contexto, corpo, titulo="Treino concluído:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("ensemble")
def ensemble(ctx: typer.Context, pasta_experimento: Path = typer.Argument(...)) -> None:
    """Executa a etapa de ensemble com validação temporal."""
    from frequencia.pipelines import ensemble as ensemble_mod

    contexto = _ctx(ctx)
    try:
        pasta_experimento = Path(pasta_experimento)
        pacote = _pacote_do_experimento(pasta_experimento)
        horizonte = int(pacote["meta"].get("config", {}).get("horizonte_dias_letivos", 7))
        resultado = ensemble_mod.montar(
            pasta_experimento, pacote["dataset"], purga=horizonte, detalhado=contexto.detalhado
        )
        corpo = {
            "membros": resultado.membros,
            "pesos": resultado.pesos,
            "metricas": resultado.metricas,
            "discordancia_media": resultado.discordancia_media,
        }
        contexto_mod.emitir(contexto, corpo, titulo="Ensemble ajustado:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("destilar")
def destilar(ctx: typer.Context, pasta_experimento: Path = typer.Argument(...)) -> None:
    """Executa a destilação para o estudante leve publicável."""
    from frequencia.pipelines import experimento as exp_mod

    contexto = _ctx(ctx)
    try:
        pasta_experimento = Path(pasta_experimento)
        dados = _dataset_do_experimento(pasta_experimento)
        corpo = exp_mod._executar_destilacao(
            exp_mod.ConfigExperimento(pasta_dataset=Path()),
            pasta_experimento,
            dados,
            contexto.detalhado,
        )
        contexto_mod.emitir(contexto, corpo, titulo="Destilação concluída:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("listar")
def listar(ctx: typer.Context) -> None:
    """Lista os experimentos registrados no workspace."""
    from frequencia.pipelines import treino as treino_mod

    contexto = _ctx(ctx)
    try:
        experimentos = treino_mod.listar_experimentos()
        linhas = [
            {
                "identificador": corpo["identificador"],
                "auc": corpo.get("metricas", {}).get("auc", ""),
                "semente": corpo.get("semente", ""),
                "dataset": corpo.get("dataset", ""),
            }
            for corpo in experimentos
        ]
        contexto_mod.emitir(contexto, linhas, titulo="Experimentos:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("comparar")
def comparar(
    ctx: typer.Context,
    experimentos: list[Path] = typer.Argument(...),
) -> None:
    """Compara as métricas de dois ou mais experimentos lado a lado."""
    contexto = _ctx(ctx)
    try:
        linhas = []
        for pasta in experimentos:
            alvo = Path(pasta) / "avaliacao.json"
            if not alvo.is_file():
                continue
            corpo = json.loads(alvo.read_text(encoding="utf-8"))
            linha = {"experimento": Path(pasta).name}
            linha.update(corpo.get("metricas", {}))
            linhas.append(linha)
        contexto_mod.emitir(contexto, linhas, titulo="Comparação de experimentos:")
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("interromper")
def interromper(ctx: typer.Context, identificador: str = typer.Argument(...)) -> None:
    """Marca o experimento como interrompido para recuperação posterior."""
    from frequencia.infra import caminhos

    contexto = _ctx(ctx)
    try:
        alvo = caminhos.caminho("artefatos") / "experimentos" / identificador / "estado.json"
        if not alvo.is_file():
            msg = f"Experimento não encontrado: {identificador}."
            raise FileNotFoundError(msg)
        estado = json.loads(alvo.read_text(encoding="utf-8"))
        estado["interrompido"] = True
        alvo.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")
        contexto.auditar("experimentos.interromper", alvo=identificador)
        contexto_mod.emitir(contexto, {"interrompido": identificador})
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("recuperar")
def recuperar(ctx: typer.Context, identificador: str = typer.Argument(...)) -> None:
    """Retoma um experimento interrompido do ponto em que parou."""
    from frequencia.infra import caminhos

    contexto = _ctx(ctx)
    try:
        alvo = caminhos.caminho("artefatos") / "experimentos" / identificador
        if not (alvo / "estado.json").is_file():
            msg = f"Experimento não encontrado: {identificador}."
            raise FileNotFoundError(msg)
        estado = json.loads((alvo / "estado.json").read_text(encoding="utf-8"))
        estado.pop("interrompido", None)
        (alvo / "estado.json").write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")
        concluidas = list(estado.get("etapas", {}).keys())
        contexto_mod.emitir(
            contexto,
            {"experimento": identificador, "etapas_concluidas": concluidas},
            titulo="Experimento recuperável:",
        )
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


@app.command("relatorio")
def relatorio(ctx: typer.Context, pasta_experimento: Path = typer.Argument(...)) -> None:
    """Exporta o relatório de avaliação do experimento em Markdown."""
    contexto = _ctx(ctx)
    try:
        alvo = Path(pasta_experimento) / "relatorio-avaliacao.md"
        if not alvo.is_file():
            msg = f"Relatório não encontrado: {alvo}. Execute a avaliação antes."
            raise FileNotFoundError(msg)
        contexto_mod.emitir(contexto, {"arquivo": str(alvo), "conteudo": alvo.read_text(encoding="utf-8")})
    except Exception as exc:
        contexto_mod.falha(contexto, exc)


def _dataset_do_experimento(pasta: Path) -> pl.DataFrame:
    """Localiza o dataset usado por um experimento a partir do estado."""
    return _pacote_do_experimento(pasta)["dataset"]


def _pacote_do_experimento(pasta: Path) -> dict:
    """Dataset e metadado usados por um experimento, a partir do estado."""
    from frequencia.pipelines import dataset as dataset_mod

    alvo = Path(pasta) / "estado.json"
    if alvo.is_file():
        estado = json.loads(alvo.read_text(encoding="utf-8"))
        pasta_dataset = estado.get("config", {}).get("pasta_dataset")
        if pasta_dataset:
            return dataset_mod.carregar_dataset(Path(pasta_dataset))
    msg = f"Estado do experimento ausente em {pasta}. Execute o ciclo completo antes."
    raise FileNotFoundError(msg)
