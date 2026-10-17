# Validação de ambiente na partida: variáveis documentadas em .env.example.
"""Leitura e validação das variáveis de ambiente do FrequencIA.

A validação falha cedo com mensagem em português. Nenhuma variável é secreta
de produção: o ecossistema roda localmente e sem credenciais externas.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from frequencia.infra import caminhos
from frequencia.infra.erros import ErroConfiguracao

VALORES_PERFIL = ("padrao", "fumaca", "ciclo")


@dataclass(frozen=True)
class Ambiente:
    """Ambiente resolvido a partir das variáveis e de valores padrão."""

    workspace: Path
    mlflow_uri: str
    semente: int
    perfil: str
    fuso: str
    detalhado: bool = False

    def resolver(self, valor: str) -> str:
        """Substitui marcadores de caminho conhecidos em um valor de config."""
        tabela = {
            "{workspace}": str(self.workspace),
            "{dados}": str(self.workspace / "var" / "dados"),
            "{artefatos}": str(self.workspace / "var" / "artefatos"),
        }
        resultado = valor
        for marcador, caminho in tabela.items():
            resultado = resultado.replace(marcador, caminho)
        return resultado


def validar(perfil: str | None = None, detalhado: bool = False) -> Ambiente:
    """Valida o ambiente na partida e devolve a configuração resolvida."""
    perfil_escolhido = (perfil or os.environ.get("FREQUENCIA_PERFIL", "padrao")).lower()
    if perfil_escolhido not in VALORES_PERFIL:
        msg = (
            f"Perfil inválido: {perfil_escolhido}. "
            f"Use um de {VALORES_PERFIL} ou a variável FREQUENCIA_PERFIL."
        )
        raise ErroConfiguracao(msg)

    workspace = caminhos.raiz_workspace()
    mlflow_uri = os.environ.get(
        "FREQUENCIA_MLFLOW_URI",
        f"sqlite:///{(workspace / 'var' / 'mlflow' / 'mlflow.db').as_posix()}",
    )
    try:
        semente = int(os.environ.get("FREQUENCIA_SEMENTE", "20261018"))
    except ValueError:
        msg = "FREQUENCIA_SEMENTE deve ser um número inteiro."
        raise ErroConfiguracao(msg) from None

    fuso = os.environ.get("FREQUENCIA_FUSO", "America/Fortaleza")
    return Ambiente(
        workspace=workspace,
        mlflow_uri=mlflow_uri,
        semente=semente,
        perfil=perfil_escolhido,
        fuso=fuso,
        detalhado=detalhado,
    )
