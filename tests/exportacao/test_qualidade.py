# Teste lento de qualidade: o ciclo no perfil padrão aprova todos os gates.
"""Exigência de qualidade com volume suficiente para o veredito significar algo.

O perfil de fumaça tem cem alunos e serve à mecânica do ciclo; nele, a
diferença entre modelo e baseline fica dentro do erro-padrão da AUC. Este
teste roda o perfil padrão (720 alunos, ano letivo inteiro) e exige todos os
gates aprovados e a partida a frio avaliada. Leva vários minutos: roda com
FREQUENCIA_TESTES_LENTOS=1.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.lento,
    pytest.mark.skipif(
        os.environ.get("FREQUENCIA_TESTES_LENTOS") != "1",
        reason="teste lento: defina FREQUENCIA_TESTES_LENTOS=1",
    ),
]


def test_perfil_padrao_aprova_todos_os_gates(workspace: Path, tmp_path: Path) -> None:
    from frequencia.dados import sintetico
    from frequencia.pipelines import dataset as dataset_mod
    from frequencia.pipelines import experimento

    destino = tmp_path / "dados"
    sintetico.gerar(sintetico.ConfigSintetico(perfil="padrao", semente=20261018, destino=destino))
    construido = dataset_mod.construir(dataset_mod.ConfigDataset(pasta_dados=destino, versao="qualidade"))
    resumo = experimento.executar(
        experimento.ConfigExperimento(
            pasta_dataset=construido["pasta"],
            identificador="qualidade",
            versao_modelo="2026.10.21-qualidade",
        )
    )
    gates = resumo["gates"]
    assert gates["aprovado"], gates
    assert not gates.get("nao_avaliados"), gates
