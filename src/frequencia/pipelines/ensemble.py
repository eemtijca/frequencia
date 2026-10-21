# Ensemble offline diversificado com validação temporal e blending regularizado.
"""Combinação de modelos de base como ferramenta de treino, não de produção.

Membros de base: LightGBM curto e médio, XGBoost, CatBoost, histogramas do
scikit-learn, regressão logística e baseline de regras. A validação usa
dobras temporais expansivas com previsões fora da dobra (OOF), o meta-modelo
é uma regressão logística regularizada sobre as probabilidades dos membros e
a discordância entre membros alimenta o sinal de incerteza. O ensemble nunca
é publicado: destila para o estudante leve (inspiração TabFM, ADR-012).
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from frequencia.infra import logs
from frequencia.infra.erros import ErroValidacao
from frequencia.pipelines import baseline

NOME_BASELINE = "baseline_regras"


@dataclass
class ResultadoEnsemble:
    """Saída do ensemble ajustado."""

    membros: list[str]
    pesos: dict[str, float]
    metricas: dict
    discordancia_media: float
    previsoes_oof: np.ndarray
    duracao_segundos: float


def _dobras_temporais(
    dias: list[str], quantidade: int = 3, purga: int = 0
) -> list[tuple[list[str], list[str]]]:
    """Dobras expansivas: treino cresce, validação desliza no tempo.

    Os últimos `purga` dias antes de cada bloco de validação saem do treino
    da dobra: o rótulo deles olha para dias que já são validação, e
    mantê-los vazaria o desfecho para o membro (mesma regra da separação
    do dataset, ADR-014). Dobras sem nenhum dia de treino são descartadas.
    """
    total = len(dias)
    if total < 2:
        return []
    if total < quantidade + 2:
        candidatas = [(dias[: max(0, total - 1 - purga)], dias[-1:])]
    else:
        tamanho_bloco = max(1, total // (quantidade + 1))
        candidatas = []
        for indice in range(quantidade):
            inicio_validacao = tamanho_bloco * (indice + 1)
            fim_validacao = inicio_validacao + tamanho_bloco
            if indice == quantidade - 1:
                fim_validacao = total
            candidatas.append(
                (dias[: max(0, inicio_validacao - purga)], dias[inicio_validacao:fim_validacao])
            )
    return [(treino, validacao) for treino, validacao in candidatas if treino]


def montar(
    pasta_experimento: Path,
    dataset: pl.DataFrame,
    *,
    semente: int = 20261018,
    dobras: int = 3,
    purga: int = 0,
    detalhado: bool = False,
) -> ResultadoEnsemble:
    """Ajusta o ensemble completo sobre o dataset com OOF temporal.

    Grava os membros, os pesos e as previsões OOF no experimento para uso da
    calibração e da destilação. A métrica final é medida fora da dobra.
    """
    import joblib
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import average_precision_score, roc_auc_score

    from frequencia.features.catalogo import NOMES_FEATURES

    inicio = time.time()
    pasta_experimento = Path(pasta_experimento)
    pasta_ensemble = pasta_experimento / "ensemble"
    pasta_ensemble.mkdir(parents=True, exist_ok=True)

    dados = (
        dataset.filter(pl.col("divisao").is_in(["treino", "validacao"]))
        .sort(["dia", "aluno_id"])
        .with_row_index("linha")
    )
    dias_unicos = sorted(dados["dia"].unique().to_list())
    particoes = _dobras_temporais(dias_unicos, dobras, purga)
    if not particoes:
        msg = "Dias insuficientes para dobras temporais com purga do horizonte. Gere mais dias letivos."
        raise ErroValidacao(msg)

    x_tudo = dados.select(NOMES_FEATURES).to_numpy()
    y_tudo = dados["rotulo"].cast(pl.Int32).to_numpy()
    dias_tudo = dados["dia"].to_list()
    linhas_oof: list[int] = []

    membros = _criar_membros(semente)
    previsoes_membros: dict[str, list[float]] = {nome: [] for nome in membros}
    rotulos_oof: list[int] = []

    for dias_treino, dias_validacao in particoes:
        mascara_treino = np.isin(dias_tudo, dias_treino)
        mascara_validacao = np.isin(dias_tudo, dias_validacao)
        x_tr, y_tr = x_tudo[mascara_treino], y_tudo[mascara_treino]
        x_va, y_va = x_tudo[mascara_validacao], y_tudo[mascara_validacao]
        rotulos_oof.extend(int(valor) for valor in y_va.tolist())
        linhas_oof.extend(int(valor) for valor in np.flatnonzero(mascara_validacao))
        for nome, fabrica in membros.items():
            modelo = fabrica()
            if nome == NOME_BASELINE:
                probabilidades = baseline.pontuar(x_va)
            else:
                modelo.fit(x_tr, y_tr)
                probabilidades = modelo.predict_proba(x_va)[:, 1]
            previsoes_membros[nome].extend(probabilidades.tolist())

    matriz_oof = np.column_stack([np.array(previsoes_membros[nome]) for nome in membros])
    rotulos = np.array(rotulos_oof)

    meta = LogisticRegression(C=1.0, random_state=semente, max_iter=500)
    meta.fit(matriz_oof, rotulos)
    pesos_brutos = meta.coef_[0]
    positivos = np.clip(pesos_brutos, 0, None)
    normalizador = positivos.sum() if positivos.sum() > 0 else 1.0
    pesos = {
        nome: round(float(peso / normalizador), 4) for nome, peso in zip(membros, positivos, strict=True)
    }

    blend = meta.predict_proba(matriz_oof)[:, 1]
    discordancia = matriz_oof.std(axis=1)
    metricas = {
        "auc_ensemble": round(float(roc_auc_score(rotulos, blend)), 4),
        "ap_ensemble": round(float(average_precision_score(rotulos, blend)), 4),
        "auc_baseline": round(
            float(roc_auc_score(rotulos, np.array(previsoes_membros[NOME_BASELINE]))),
            4,
        ),
    }

    # Reajusta os membros finais com todos os dados de treino+validação.
    for nome, fabrica in _criar_membros(semente).items():
        if nome == NOME_BASELINE:
            continue
        modelo = fabrica()
        modelo.fit(x_tudo, y_tudo)
        joblib.dump(modelo, pasta_ensemble / f"{nome}.joblib")

    chaves_oof = dados.filter(pl.col("linha").is_in(linhas_oof))
    np.savez(
        pasta_ensemble / "oof.npz",
        previsoes=matriz_oof,
        rotulos=rotulos,
        blend=blend,
        discordancia=discordancia,
        nomes=np.array(list(membros)),
        linhas_oof=np.array(linhas_oof),
        series=np.array(chaves_oof["serie_id"].to_list()),
        historico=chaves_oof["historico_dias"].to_numpy(),
        alunos=np.array(chaves_oof["aluno_id"].to_list()),
        dias=np.array(chaves_oof["dia"].to_list()),
    )
    chaves_oof.select(
        "linha", "aluno_id", "dia", "turma_do_dia", "serie_id", "historico_dias", "rotulo"
    ).write_parquet(pasta_ensemble / "chaves.parquet")
    joblib.dump(meta, pasta_ensemble / "meta.joblib")

    logs.registrar(
        "experimentos.ensemble",
        estagio="ensemble",
        membros=list(membros),
        metricas=metricas,
        detalhado=detalhado,
    )
    return ResultadoEnsemble(
        membros=list(membros),
        pesos=pesos,
        metricas=metricas,
        discordancia_media=round(float(discordancia.mean()), 4),
        previsoes_oof=blend,
        duracao_segundos=round(time.time() - inicio, 2),
    )


class MembroCurto:
    """Membro de base com vista curta: só features de janela imediata."""

    def __init__(self, semente: int, indices: list[int]) -> None:
        self._indices = indices
        self._semente = semente
        self._modelo = None

    def fit(self, x, y):
        import lightgbm as lgb

        self._modelo = lgb.LGBMClassifier(
            n_estimators=80,
            max_depth=3,
            num_leaves=16,
            learning_rate=0.1,
            random_state=self._semente,
            verbose=-1,
        )
        self._modelo.fit(x[:, self._indices], y)
        return self

    def predict_proba(self, x):
        return self._modelo.predict_proba(x[:, self._indices])


def _criar_membros(semente: int) -> dict[str, Callable[[], Any]]:
    """Fábrica dos membros de base com diversidade de família e de vista."""
    import lightgbm as lgb
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from xgboost import XGBClassifier

    from frequencia.features.catalogo import NOMES_FEATURES

    curtas = [
        "faltas_7d",
        "faltas_consecutivas",
        "dias_desde_ultima_falta",
        "media_movel_faltas_7d",
        "chamada_realizada_no_dia",
        "historico_dias",
        "dia_semana_seno",
        "dia_semana_cosseno",
    ]
    indices_curtas = [list(NOMES_FEATURES).index(nome) for nome in curtas]

    fabrica_catboost: Callable[[], Any] | None
    try:
        from catboost import CatBoostClassifier

        def _criar_catboost() -> Any:
            return CatBoostClassifier(
                iterations=150,
                depth=4,
                learning_rate=0.08,
                random_seed=semente,
                verbose=0,
                allow_writing_files=False,
            )

        fabrica_catboost = _criar_catboost
    except ImportError:  # pragma: no cover - catboost é dependência fixada
        fabrica_catboost = None

    membros: dict[str, Callable[[], Any]] = {
        "lightgbm_medio": lambda: lgb.LGBMClassifier(
            n_estimators=140,
            max_depth=4,
            num_leaves=24,
            learning_rate=0.08,
            random_state=semente,
            verbose=-1,
        ),
        "lightgbm_curto": lambda: MembroCurto(semente, indices_curtas),
        "xgboost_base": lambda: XGBClassifier(
            n_estimators=140,
            max_depth=4,
            learning_rate=0.08,
            random_state=semente,
            eval_metric="logloss",
            verbosity=0,
        ),
        "histograma_sklearn": lambda: HistGradientBoostingClassifier(
            max_iter=140,
            max_depth=4,
            learning_rate=0.08,
            random_state=semente,
        ),
        "regressao_logica": lambda: make_pipeline(StandardScaler(), LogisticRegression(C=0.5, max_iter=500)),
        NOME_BASELINE: lambda: None,
    }
    if fabrica_catboost is not None:
        membros["catboost_base"] = fabrica_catboost
    return membros
