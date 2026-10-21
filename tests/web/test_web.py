# Testes da interface web: páginas importam e a visão geral renderiza.
"""A aplicação Streamlit como janela do mesmo motor da CLI."""

from __future__ import annotations


def test_paginas_importam() -> None:
    """As 16 páginas da seção 5.2 existem e expõem renderizar."""
    paginas = [
        "visao_geral",
        "dados",
        "features",
        "datasets",
        "experimentos",
        "comparacao",
        "ensemble",
        "calibracao",
        "fairness",
        "exportacao",
        "manifesto",
        "registro",
        "publicacao",
        "monitoramento",
        "governanca",
        "configuracoes",
    ]
    for nome in paginas:
        modulo = __import__(f"frequencia.web.paginas.{nome}", fromlist=["renderizar"])
        assert callable(modulo.renderizar), nome


def test_visao_geral_renderiza_com_app_test(workspace) -> None:
    """A página inicial renderiza com o AppTest do Streamlit."""
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    pagina = Path(__file__).resolve().parents[2] / "src" / "frequencia" / "web" / "paginas" / "visao_geral.py"
    aplicacao = AppTest.from_file(str(pagina), default_timeout=60)
    aplicacao.run()
    assert not aplicacao.exception


def test_tarefas_disparam_cli_em_fundo(workspace, pacote_sintetico) -> None:
    """Uma tarefa de fundo roda a CLI e registra o desfecho."""
    import time

    from frequencia.infra import estado as estado_infra
    from frequencia.web import tarefas as tarefas_mod

    recibo = tarefas_mod.disparar(["features", "listar"], rotulo="listar features", workspace=workspace)
    limite = time.time() + 90
    desfecho = None
    while time.time() < limite:
        eventos = [t for t in estado_infra.ler_tarefas() if t["id"] == recibo["id"]]
        if eventos and eventos[0].get("estado") in ("concluida", "falhou"):
            desfecho = eventos[0]
            break
        time.sleep(0.5)
    assert desfecho is not None
    assert desfecho["estado"] == "concluida", desfecho


def test_tarefa_com_papel_passa_opcoes_globais_antes_do_grupo(workspace, monkeypatch) -> None:
    """Papel e ator vão antes do grupo, onde a CLI os aceita."""
    import subprocess

    from frequencia.web import tarefas as tarefas_mod

    capturados: list[list[str]] = []

    class _Processo:
        pid = 1

        def wait(self) -> int:
            return 0

    def _popen(comando, **_kwargs):
        capturados.append(comando)
        return _Processo()

    monkeypatch.setattr(subprocess, "Popen", _popen)
    tarefas_mod.disparar(["registro", "listar", "risco-infrequencia"], papel="aprovador", workspace=workspace)
    comando = capturados[0]
    assert comando.index("--papel") < comando.index("registro")
    assert comando[comando.index("--papel") + 1] == "aprovador"
    assert comando.index("--ator") < comando.index("registro")
