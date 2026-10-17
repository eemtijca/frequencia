# Hashes SHA-256 de arquivos e pastas para integridade e linhagem.
"""Cálculo de hashes estáveis de artefatos.

O hash de pasta percorre os arquivos em ordem alfabética e alimenta o
manifesto do modelo e a auditoria de integridade.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

_TAM_BLOCO = 1 << 20

EXTENSOES_IGNORADAS = {".pyc", ".DS_Store", ".tmp"}


def hash_arquivo(caminho: Path) -> str:
    """Devolve o hash SHA-256 do conteúdo do arquivo."""
    alvo = Path(caminho)
    if not alvo.is_file():
        msg = f"Arquivo inexistente para hash: {alvo}"
        raise FileNotFoundError(msg)
    calculo = hashlib.sha256()
    with alvo.open("rb") as origem:
        while bloco := origem.read(_TAM_BLOCO):
            calculo.update(bloco)
    return calculo.hexdigest()


def hash_pasta(caminho: Path) -> str:
    """Devolve o hash SHA-256 da pasta: nome e conteúdo de cada arquivo."""
    raiz = Path(caminho)
    if not raiz.is_dir():
        msg = f"Pasta inexistente para hash: {raiz}"
        raise NotADirectoryError(msg)
    calculo = hashlib.sha256()
    for arquivo in sorted(p for p in raiz.rglob("*") if p.is_file()):
        if arquivo.suffix in EXTENSOES_IGNORADAS:
            continue
        relativo = arquivo.relative_to(raiz).as_posix().encode("utf-8")
        calculo.update(relativo + b"\0")
        calculo.update(hash_arquivo(arquivo).encode("ascii"))
    return calculo.hexdigest()


def resumo_integridade(raiz: Path, manifestos: dict[str, str]) -> dict[str, bool]:
    """Confere os hashes declarados contra o estado atual dos arquivos."""
    resultado: dict[str, bool] = {}
    for relativo, esperado in manifestos.items():
        alvo = raiz / relativo
        resultado[relativo] = alvo.is_file() and hash_arquivo(alvo) == esperado
    return resultado
