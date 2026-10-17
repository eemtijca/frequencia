# Fixtures compartilhadas: workspace temporário e pacote sintético.
"""Base das suítes: cada teste cria e limpa a própria massa.

Fixtures pesadas (pacote, dataset, ciclo) têm escopo de módulo para rodar
uma única vez por arquivo de teste; nenhuma massa depende de outra suíte.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture()
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Workspace isolado por teste, com var/ preparado."""
    raiz = tmp_path / "ws"
    raiz.mkdir()
    monkeypatch.setenv("FREQUENCIA_WORKSPACE", str(raiz))
    (raiz / "var").mkdir(exist_ok=True)
    return raiz


@pytest.fixture()
def pacote_sintetico(tmp_path: Path) -> Path:
    """Pacote sintético mínimo, determinístico, em pasta temporária."""
    from frequencia.dados import sintetico

    destino = tmp_path / "dados"
    sintetico.gerar(sintetico.ConfigSintetico(perfil="amostra", semente=20261018, destino=destino))
    return destino


@pytest.fixture(scope="module")
def pacote_medio(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Pacote sintético com volume de fumaça, suficiente para os gates."""
    from frequencia.dados import sintetico

    destino = tmp_path_factory.mktemp("medio") / "dados"
    sintetico.gerar(sintetico.ConfigSintetico(perfil="fumaca", semente=20261018, destino=destino))
    return destino


class _Ambiente:
    """Gerencia FREQUENCIA_WORKSPACE com restauração no fim do módulo."""

    def __init__(self, raiz: Path) -> None:
        self.raiz = raiz
        self.anterior = os.environ.get("FREQUENCIA_WORKSPACE")

    def aplicar(self) -> Path:
        os.environ["FREQUENCIA_WORKSPACE"] = str(self.raiz)
        (self.raiz / "var").mkdir(parents=True, exist_ok=True)
        return self.raiz

    def restaurar(self) -> None:
        if self.anterior is None:
            os.environ.pop("FREQUENCIA_WORKSPACE", None)
        else:
            os.environ["FREQUENCIA_WORKSPACE"] = self.anterior


@pytest.fixture(scope="module")
def workspace_modulo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Workspace por módulo, para fixtures pesadas."""
    ambiente = _Ambiente(tmp_path_factory.mktemp("wsmod") / "ws")
    yield ambiente.aplicar()
    ambiente.restaurar()


@pytest.fixture(scope="module")
def dataset_construido(workspace_modulo: Path, pacote_medio: Path) -> Path:
    """Dataset construído sobre o pacote médio, uma vez por módulo."""
    from frequencia.pipelines import dataset as dataset_mod

    resultado = dataset_mod.construir(dataset_mod.ConfigDataset(pasta_dados=pacote_medio, versao="teste"))
    return resultado["pasta"]


@pytest.fixture(scope="module")
def experimento_completo(workspace_modulo: Path, dataset_construido: Path) -> Path:
    """Experimento com o ciclo completo executado (fumaça, ponta a ponta)."""
    from frequencia.pipelines import experimento

    config = experimento.ConfigExperimento(
        pasta_dataset=dataset_construido,
        identificador="smoke",
        versao_modelo="2026.10.18-smoke",
    )
    resumo = experimento.executar(config)
    pasta = Path(resumo["pasta"])
    assert resumo["gates"]["aprovado"], resumo["gates"]
    return pasta
