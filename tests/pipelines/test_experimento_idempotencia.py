# Testes da idempotência do experimento: reaproveitamento e invalidação.
"""Etapas reaproveitadas precisam corresponder à configuração registrada."""

from __future__ import annotations

from pathlib import Path

import pytest

from frequencia.pipelines import experimento

ETAPAS = list(experimento.ETAPAS)


@pytest.fixture()
def ciclo_simulado(workspace: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Experimento com etapas substituídas por registros de chamada."""
    pasta_dataset = tmp_path / "dataset"
    pasta_dataset.mkdir()
    (pasta_dataset / "dataset.parquet").write_bytes(b"conteudo-1")
    chamadas: list[str] = []

    def etapa(nome: str, corpo: dict):
        def _executar(*_args, **_kwargs):
            chamadas.append(nome)
            return corpo

        return _executar

    resumo = {"resumo": {"tamanho_bytes": 1, "latencia_ms": 0.1, "versao_modelo": "v"}}
    monkeypatch.setattr(experimento, "_executar_treino", etapa("treino", {}))
    monkeypatch.setattr(experimento, "_executar_ensemble", etapa("ensemble", {}))
    monkeypatch.setattr(experimento, "_executar_calibracao", etapa("calibracao", resumo))
    monkeypatch.setattr(experimento, "_executar_destilacao", etapa("destilacao", {}))
    monkeypatch.setattr(experimento, "_executar_avaliacao", etapa("avaliacao", resumo))
    monkeypatch.setattr(experimento, "_executar_exportacao", etapa("exportacao", resumo))
    monkeypatch.setattr(experimento, "_executar_empacotamento", etapa("empacotamento", resumo))
    monkeypatch.setattr(experimento.dataset_mod, "carregar_dataset", lambda _p: {"dataset": None, "meta": {}})
    monkeypatch.setattr(
        experimento.avaliacao_mod, "validar_gates", lambda *_a, **_k: {"aprovado": True, "vereditos": {}}
    )
    monkeypatch.setattr(experimento.estado_infra, "registrar_gates", lambda *_a, **_k: None)
    monkeypatch.setattr(experimento, "_registrar_mlflow_publicado", lambda *_a, **_k: "sem-rastreamento")
    return pasta_dataset, chamadas


def _config(pasta: Path, semente: int = 1) -> experimento.ConfigExperimento:
    return experimento.ConfigExperimento(pasta_dataset=pasta, identificador="idem", semente=semente)


def test_mesma_configuracao_reaproveita_todas_as_etapas(ciclo_simulado) -> None:
    pasta, chamadas = ciclo_simulado
    experimento.executar(_config(pasta))
    assert chamadas == ETAPAS
    chamadas.clear()
    experimento.executar(_config(pasta))
    assert chamadas == []


def test_configuracao_diferente_refaz_todas_as_etapas(ciclo_simulado) -> None:
    """Outra semente com o mesmo identificador não reaproveita artefatos."""
    pasta, chamadas = ciclo_simulado
    experimento.executar(_config(pasta, semente=1))
    chamadas.clear()
    experimento.executar(_config(pasta, semente=2))
    assert chamadas == ETAPAS


def test_dataset_alterado_refaz_todas_as_etapas(ciclo_simulado) -> None:
    pasta, chamadas = ciclo_simulado
    experimento.executar(_config(pasta))
    chamadas.clear()
    (pasta / "dataset.parquet").write_bytes(b"conteudo-2")
    experimento.executar(_config(pasta))
    assert chamadas == ETAPAS


def test_etapa_refeita_invalida_as_seguintes(ciclo_simulado) -> None:
    """Refazer uma etapa do meio refaz também todas as que dependem dela."""
    import json

    from frequencia.infra import caminhos

    pasta, chamadas = ciclo_simulado
    experimento.executar(_config(pasta))
    chamadas.clear()
    alvo = caminhos.caminho("artefatos") / "experimentos" / "idem" / "estado.json"
    estado = json.loads(alvo.read_text(encoding="utf-8"))
    meio = ETAPAS[3]
    del estado["etapas"][meio]
    alvo.write_text(json.dumps(estado), encoding="utf-8")
    experimento.executar(_config(pasta))
    assert chamadas == ETAPAS[3:]
