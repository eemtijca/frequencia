# Testes da CLI: ajuda de todos os grupos, modo seco, JSON e ciclo completo.
"""A interface de engenharia roda sem quebrar em todos os grupos."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

CAMINHO_APP = ["-m", "frequencia.cli.app"]


def _rodar(argumentos: list[str], workspace: Path) -> subprocess.CompletedProcess:
    ambiente = os.environ.copy()
    ambiente["FREQUENCIA_WORKSPACE"] = str(workspace)
    ambiente["HOME"] = str(workspace)
    return subprocess.run(
        [sys.executable, *CAMINHO_APP, "--workspace", str(workspace), *argumentos],
        capture_output=True,
        text=True,
        timeout=600,
        env=ambiente,
    )


def test_ajuda_da_raiz_e_de_todos_os_grupos() -> None:
    """Cada grupo responde ao --help sem erro."""
    grupos = [
        "dados",
        "privacidade",
        "features",
        "datasets",
        "experimentos",
        "avaliacao",
        "exportacao",
        "empacotamento",
        "registro",
        "publicacao",
        "monitoramento",
        "auditoria",
    ]
    from typer.testing import CliRunner

    from frequencia.cli.app import app

    corredor = CliRunner()
    resultado = corredor.invoke(app, ["--help"])
    assert resultado.exit_code == 0
    for grupo in grupos:
        saida = corredor.invoke(app, [grupo, "--help"])
        assert saida.exit_code == 0, f"{grupo}: {saida.output}"


def test_comando_invalido_erro_claro(tmp_path: Path) -> None:
    """Comando desconhecido devolve código 2 com ajuda, sem stack trace."""
    concluido = _rodar(["dados", "comando-inexistente"], tmp_path)
    assert concluido.returncode != 0
    assert "Traceback" not in concluido.stderr


def test_erro_amigavel_sem_stack_trace(tmp_path: Path) -> None:
    """Falha de arquivo vira frase curta, sem stack trace."""
    concluido = _rodar(["dados", "validar", str(tmp_path / "inexistente")], tmp_path)
    assert concluido.returncode == 1
    assert "Traceback" not in concluido.stderr
    assert "não encontrada" in concluido.stderr or "ausente" in concluido.stderr


def test_saida_json_estruturada(tmp_path: Path, pacote_sintetico: Path) -> None:
    """A bandeira --json devolve JSON puro na saída padrão."""
    concluido = _rodar(
        ["--json", "--silencioso", "dados", "detectar-pii", str(pacote_sintetico)],
        tmp_path,
    )
    assert concluido.returncode == 0
    corpo = json.loads(concluido.stdout.strip().splitlines()[-1])
    assert corpo == []


def test_modo_seco_nao_grava(tmp_path: Path, pacote_sintetico: Path) -> None:
    """O modo seco ensaia sem tocar o workspace."""
    concluido = _rodar(
        ["--seco", "dados", "gerar-sintetico", "--destino", str(tmp_path / "nada")],
        tmp_path,
    )
    assert concluido.returncode == 0
    assert not (tmp_path / "nada").exists()


def test_forca_exige_justificativa(tmp_path: Path) -> None:
    """--forca sem justificativa é recusado com mensagem clara."""
    concluido = _rodar(["--forca", "features", "listar"], tmp_path)
    assert concluido.returncode == 1
    assert "justificativa" in concluido.stderr.lower()


def test_fluxo_completo_pela_cli(tmp_path: Path) -> None:
    """Importação, dataset, ciclo, gates e inferência de ponta a ponta."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    from frequencia.dados import sintetico

    pasta_dados = tmp_path / "dados"
    sintetico.gerar(sintetico.ConfigSintetico(perfil="amostra", destino=pasta_dados))

    # 1. portão de privacidade
    concluido = _rodar(["--json", "privacidade", "validar-entrada-treino", str(pasta_dados)], workspace)
    assert concluido.returncode == 0, concluido.stderr

    # 2. dataset
    concluido = _rodar(
        [
            "--json",
            "datasets",
            "construir",
            str(pasta_dados),
            "--versao",
            "cli",
        ],
        workspace,
    )
    assert concluido.returncode == 0, concluido.stderr
    pasta_dataset = workspace / "var" / "dados" / "processados" / "cli"

    # 3. ciclo completo
    concluido = _rodar(
        [
            "--json",
            "experimentos",
            "executar",
            str(pasta_dataset),
            "--identificador",
            "ciclo",
            "--versao-modelo",
            "2026.10.18-cli",
        ],
        workspace,
    )
    assert concluido.returncode == 0, concluido.stderr

    # 4. gates
    concluido = _rodar(
        ["avaliacao", "validar-gates", str(workspace / "var" / "artefatos" / "experimentos" / "ciclo")],
        workspace,
    )
    assert concluido.returncode == 0
    assert "True" in concluido.stdout

    # 5. paridade
    if _node_disponivel():
        concluido = _rodar(
            [
                "--json",
                "exportacao",
                "testar-sinteticos",
                str(workspace / "var" / "pacotes" / "risco-infrequencia-2026.10.18-cli"),
            ],
            workspace,
        )
        assert concluido.returncode == 0, concluido.stderr
        corpo = json.loads(concluido.stdout.strip().splitlines()[-1])
        assert corpo["paridade_ok"] and corpo["divergencias"] == 0


def _node_disponivel() -> bool:
    try:
        subprocess.run(["node", "--version"], capture_output=True, check=True, timeout=15)
        return True
    except (OSError, subprocess.SubprocessError):
        return False
