# Treinamento declarativo com Optuna leve e rastreamento no MLflow.
"""Treino do modelo generalista e do estudante destilado.

O treino é declarativo: semente, dataset, parâmetros e orçamento de busca
vêm da configuração. Toda execução registra parâmetros, métricas e artefatos
no MLflow local (backend SQLite em var/mlflow) e grava o modelo em
var/artefatos/modelos com hash e metadado.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from frequencia.infra import caminhos, logs
from frequencia.infra import hash as hash_infra
from frequencia.infra.erros import ErroValidacao
from frequencia.pipelines import dataset as dataset_mod

PARAMETROS_PADRAO: dict[str, Any] = {
    "n_estimators": 120,
    "max_depth": 4,
    "num_leaves": 24,
    "learning_rate": 0.08,
    "min_child_samples": 25,
    "subsample": 0.9,
    "colsample_bytree": 0.9,
    "reg_lambda": 1.0,
}

PARAMETROS_DESTILADO: dict[str, Any] = {
    "n_estimators": 60,
    "max_depth": 3,
    "num_leaves": 15,
    "learning_rate": 0.10,
    "min_child_samples": 20,
    "subsample": 1.0,
    "colsample_bytree": 1.0,
    "reg_lambda": 2.0,
}

LIMITE_TAMANHO_MODELO_BYTES = 512 * 1024


@dataclass
class ConfigTreino:
    """Configuração declarativa de um treinamento."""

    pasta_dataset: Path
    semente: int = 20261018
    tentativas_optuna: int = 0
    parametros: dict = field(default_factory=lambda: dict(PARAMETROS_PADRAO))
    identificador: str = ""
    descricao: str = "Modelo generalista de risco individual de infrequência"
    pasta_destino: Path | None = None


@dataclass
class ResultadoTreino:
    """Saída de um treinamento concluído."""

    pasta: Path
    identificador: str
    metricas: dict
    parametros: dict
    run_mlflow: str
    duracao_segundos: float
    tamanho_modelo_bytes: int


def _probabilidade_positiva(modelo: Any, x: np.ndarray) -> np.ndarray:
    """Coluna de probabilidade da classe positiva; o LightGBM devolve ndarray denso.

    A assinatura da biblioteca declara união com matrizes esparsas, que só
    aparecem com entrada esparsa; aqui a entrada é sempre densa.
    """
    resultado = modelo.predict_proba(x)
    if not isinstance(resultado, np.ndarray):  # pragma: no cover - entrada densa
        resultado = np.asarray(resultado)
    return resultado[:, 1]


def treinar(config: ConfigTreino, *, detalhado: bool = False) -> ResultadoTreino:
    """Treina o modelo principal com LightGBM e registra no MLflow."""
    import joblib
    import lightgbm as lgb
    from sklearn.metrics import average_precision_score, roc_auc_score

    pacote = dataset_mod.carregar_dataset(config.pasta_dataset)
    dados = pacote["dataset"]
    treino = dados.filter(pl.col("divisao") == "treino")
    validacao = dados.filter(pl.col("divisao") == "validacao")
    if treino.height < 50 or validacao.height < 20:
        msg = "Dataset pequeno demais para treinar. Gere mais dias letivos ou reduza o mínimo de histórico."
        raise ErroValidacao(msg)

    from frequencia.features.catalogo import NOMES_FEATURES

    x_treino = treino.select(NOMES_FEATURES).to_numpy()
    y_treino = treino["rotulo"].cast(pl.Int32).to_numpy()
    x_val = validacao.select(NOMES_FEATURES).to_numpy()
    y_val = validacao["rotulo"].cast(pl.Int32).to_numpy()

    parametros: dict[str, Any] = dict(config.parametros)
    inicio = time.time()
    if config.tentativas_optuna > 0:
        parametros = _otimizar(x_treino, y_treino, x_val, y_val, config)
    modelo = lgb.LGBMClassifier(
        **parametros,
        random_state=config.semente,
        verbose=-1,
        importance_type="gain",
    )
    modelo.fit(x_treino, y_treino)
    duracao = time.time() - inicio

    probabilidade = _probabilidade_positiva(modelo, x_val)
    metricas = {
        "auc": round(float(roc_auc_score(y_val, probabilidade)), 4),
        "ap": round(float(average_precision_score(y_val, probabilidade)), 4),
    }

    identificador = config.identificador or f"exp-{hash_infra.hash_pasta(config.pasta_dataset)[:8]}"
    pasta = (
        Path(config.pasta_destino)
        if config.pasta_destino is not None
        else caminhos.caminho("modelos") / identificador
    )
    pasta.mkdir(parents=True, exist_ok=True)
    alvo_modelo = pasta / "modelo.joblib"
    joblib.dump(modelo, alvo_modelo)

    run_mlflow = _registrar_mlflow(
        identificador,
        parametros=parametros,
        metricas=metricas,
        semente=config.semente,
        dataset=pacote["meta"].get("identificador", ""),
        alvo_modelo=alvo_modelo,
    )
    meta = {
        "identificador": identificador,
        "descricao": config.descricao,
        "semente": config.semente,
        "parametros": parametros,
        "metricas": metricas,
        "dataset": pacote["meta"].get("identificador", ""),
        "features": list(NOMES_FEATURES),
        "run_mlflow": run_mlflow,
        "duracao_segundos": round(duracao, 2),
        "tamanho_modelo_bytes": alvo_modelo.stat().st_size,
        "hash_modelo": hash_infra.hash_arquivo(alvo_modelo),
        "criado_em": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    with (pasta / "meta.json").open("w", encoding="utf-8") as saida:
        json.dump(meta, saida, ensure_ascii=False, indent=2, sort_keys=True)
        saida.write("\n")

    logs.registrar(
        "experimentos.treinar",
        estagio="treino",
        identificador=identificador,
        metricas=metricas,
        duracao=round(duracao, 2),
        detalhado=detalhado,
    )
    return ResultadoTreino(
        pasta=pasta,
        identificador=identificador,
        metricas=metricas,
        parametros=parametros,
        run_mlflow=run_mlflow,
        duracao_segundos=round(duracao, 2),
        tamanho_modelo_bytes=alvo_modelo.stat().st_size,
    )


def destilar(
    pasta_experimento: Path,
    *,
    alvos: np.ndarray,
    x: np.ndarray,
    semente: int = 20261018,
) -> dict:
    """Treina o estudante pequeno a partir das probabilidades do professor.

    O LightGBM 4.7 rejeita rótulos fracionários no objetivo binário, então a
    destilação codifica o alvo suave por duplicação ponderada: cada linha
    entra duas vezes, com rótulo 1 e peso p, e com rótulo 0 e peso 1-p, o que
    reproduz exatamente o gradiente esperado do alvo suave. A árvore final
    é pequena de propósito: profundidade 3 e 60 iterações, para caber no
    pacote do navegador (ADR-012).
    """
    import joblib
    import lightgbm as lgb

    pasta_experimento = Path(pasta_experimento)
    alvos = np.clip(np.asarray(alvos, dtype=float), 0.0, 1.0)
    x_duplicado = np.vstack([x, x])
    y_duplicado = np.concatenate([np.ones(len(alvos), dtype=float), np.zeros(len(alvos), dtype=float)])
    pesos = np.concatenate([alvos, 1.0 - alvos])
    estudante = lgb.LGBMClassifier(
        **PARAMETROS_DESTILADO,
        random_state=semente,
        verbose=-1,
        importance_type="gain",
    )
    estudante.fit(x_duplicado, y_duplicado, sample_weight=pesos)
    alvo = pasta_experimento / "estudante.joblib"
    joblib.dump(estudante, alvo)
    return {
        "arquivo": str(alvo),
        "tamanho_bytes": alvo.stat().st_size,
        "hash": hash_infra.hash_arquivo(alvo),
        "parametros": dict(PARAMETROS_DESTILADO),
        "metodo": "duplicacao_ponderada",
    }


def carregar_modelo(pasta: Path):
    """Carrega o modelo principal de um experimento."""
    import joblib

    alvo = Path(pasta) / "modelo.joblib"
    if not alvo.is_file():
        msg = f"Modelo não encontrado: {alvo}. Treine antes de usar."
        raise ErroValidacao(msg)
    return joblib.load(alvo)


def carregar_estudante(pasta: Path):
    """Carrega o modelo destilado de um experimento."""
    import joblib

    alvo = Path(pasta) / "estudante.joblib"
    if not alvo.is_file():
        msg = f"Modelo destilado não encontrado: {alvo}. Execute a destilação."
        raise ErroValidacao(msg)
    return joblib.load(alvo)


def _otimizar(
    x_treino: np.ndarray,
    y_treino: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
    config: ConfigTreino,
) -> dict:
    """Busca leve de hiperparâmetros com Optuna sobre a divisão temporal."""
    import lightgbm as lgb
    import optuna
    from sklearn.metrics import roc_auc_score

    optuna.logging.set_verbosity(optuna.logging.WARNING)

    def objetivo(ens):
        parametros = dict(config.parametros)
        parametros.update(
            {
                "num_leaves": ens.suggest_int("num_leaves", 12, 48),
                "learning_rate": ens.suggest_float("learning_rate", 0.03, 0.2, log=True),
                "min_child_samples": ens.suggest_int("min_child_samples", 10, 40),
                "reg_lambda": ens.suggest_float("reg_lambda", 0.5, 8.0, log=True),
            }
        )
        modelo = lgb.LGBMClassifier(**parametros, random_state=config.semente, verbose=-1)
        modelo.fit(x_treino, y_treino)
        return float(roc_auc_score(y_val, _probabilidade_positiva(modelo, x_val)))

    estudo = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=config.semente),
    )
    estudo.optimize(objetivo, n_trials=config.tentativas_optuna, show_progress_bar=False)
    return {**config.parametros, **estudo.best_params}


def _registrar_mlflow(
    identificador: str,
    *,
    parametros: dict,
    metricas: dict,
    semente: int,
    dataset: str,
    alvo_modelo: Path,
) -> str:
    """Registra a execução do treino no MLflow local; devolve a run."""
    return registrar_execucao_mlflow(
        identificador,
        parametros={**parametros, "semente": semente, "dataset": dataset},
        metricas=metricas,
        artefatos=[alvo_modelo],
        estagio="treino",
    )


def registrar_execucao_mlflow(
    nome: str,
    *,
    parametros: dict,
    metricas: dict,
    artefatos: list[Path],
    estagio: str,
    etiquetas: dict | None = None,
) -> str:
    """Registra uma execução no MLflow do workspace; devolve o id da run.

    Falha de rastreamento não interrompe o ciclo: vira aviso no log e a run
    volta como "sem-rastreamento".
    """
    import mlflow

    from frequencia.infra import ambiente

    try:
        ambiente_resolvido = ambiente.validar()
        caminhos.caminho("mlflow").mkdir(parents=True, exist_ok=True)
        mlflow.set_tracking_uri(ambiente_resolvido.mlflow_uri)
        if mlflow.get_experiment_by_name("frequencia") is None:
            local = ambiente_resolvido.mlflow_uri.startswith(("sqlite:", "file:"))
            if local:
                # Sem local explícito, o MLflow resolve o repositório de
                # artefatos relativo ao diretório de trabalho e cria mlruns/
                # na raiz do projeto; o local explicito mantém tudo em var/.
                destino = (caminhos.caminho("mlflow") / "artifacts").as_uri()
                mlflow.create_experiment("frequencia", artifact_location=destino)
            else:
                mlflow.create_experiment("frequencia")
        mlflow.set_experiment("frequencia")
        with mlflow.start_run(run_name=nome) as corrida:
            mlflow.set_tags({"estagio": estagio, **(etiquetas or {})})
            mlflow.log_params({chave: str(valor)[:500] for chave, valor in parametros.items()})
            mlflow.log_metrics(
                {chave: float(valor) for chave, valor in metricas.items() if isinstance(valor, int | float)}
            )
            for artefato in artefatos:
                if Path(artefato).is_file():
                    mlflow.log_artifact(str(artefato))
            return corrida.info.run_id
    except Exception as exc:
        logs.registrar(
            "mlflow.falha",
            estagio=estagio,
            nivel="aviso",
            erro=str(exc)[:200],
        )
        return "sem-rastreamento"


def listar_experimentos() -> list[dict]:
    """Lista os experimentos registrados em var/artefatos/experimentos."""
    experimentos: list[dict] = []
    for base in (caminhos.caminho("modelos"), caminhos.caminho("artefatos") / "experimentos"):
        if not base.exists():
            continue
        for filho in sorted(base.iterdir()):
            alvo = filho / "meta.json"
            if alvo.is_file():
                meta = json.loads(alvo.read_text(encoding="utf-8"))
                meta["pasta"] = str(filho)
                if meta not in experimentos:
                    experimentos.append(meta)
    return experimentos
