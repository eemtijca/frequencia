# Layout de diretórios do workspace: separa código, dados, artefatos e estado.
"""Caminhos canônicos do FrequencIA.

Todo artefato de execução vive sob var/, dentro do workspace. O código e a
documentação ficam na árvore do repositório; nada de estado entra no pacote
de distribuição.
"""

from __future__ import annotations

import os
from pathlib import Path


def raiz_repositorio() -> Path:
    """Retorna a raiz do repositório (pasta que contém o pyproject.toml)."""
    pasta = Path(__file__).resolve()
    for ascendente in pasta.parents:
        if (ascendente / "pyproject.toml").exists():
            return ascendente
    msg = "Raiz do repositório não encontrada: pyproject.toml ausente."
    raise RuntimeError(msg)


def raiz_workspace() -> Path:
    """Retorna a raiz do workspace (padrão: a raiz do repositório)."""
    explicita = os.environ.get("FREQUENCIA_WORKSPACE")
    if explicita:
        caminho = Path(explicita).expanduser().resolve()
        caminho.mkdir(parents=True, exist_ok=True)
        return caminho
    return raiz_repositorio()


PASTAS_VAR = {
    "dados": "var/dados",
    "sinteticos": "var/dados/sinteticos",
    "processados": "var/dados/processados",
    "importados": "var/dados/importados",
    "artefatos": "var/artefatos",
    "modelos": "var/artefatos/modelos",
    "exportacoes": "var/artefatos/exportacoes",
    "pacotes": "var/pacotes",
    "publicacoes": "var/publicacoes",
    "logs": "var/logs",
    "mlflow": "var/mlflow",
    "estado": "var/estado",
    "relatorios": "var/relatorios",
    "dvc_cache": "var/dvc-cache",
}


def caminho(papel: str, criar: bool = True) -> Path:
    """Retorna um caminho canônico do workspace pelo papel da pasta."""
    try:
        relativa = PASTAS_VAR[papel]
    except KeyError:
        msg = f"Papel de pasta desconhecido: {papel}. Use um de {sorted(PASTAS_VAR)}."
        raise ValueError(msg) from None
    caminho_final = raiz_workspace() / relativa
    if criar:
        caminho_final.mkdir(parents=True, exist_ok=True)
    return caminho_final


def preparar_workspace() -> Path:
    """Cria a estrutura completa de pastas do workspace e a devolve."""
    for papel in PASTAS_VAR:
        caminho(papel)
    return raiz_workspace()


def caminho_dados_repositorio() -> Path:
    """Pasta de dados versionados no repositório (amostras sintéticas)."""
    return raiz_repositorio() / "dados"
