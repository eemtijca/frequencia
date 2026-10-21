# Testes do docker-compose.yml: o servidor MLflow aceita os hosts dos clientes.
"""O servidor de rastreamento do Compose recusa Host não listado.

O MLflow 3.17 responde 403 a qualquer Host fora de localhost e de IPs privados.
O código de rastreamento engole a falha e devolve "sem-rastreamento", então o
ciclo no Compose passou meses sem registrar nada. Este teste impede a volta
do problema sem precisar subir containers.

A imagem de desenvolvimento não leva o docker-compose.yml (o .dockerignore o
exclui), então aqui os testes pulam quando o arquivo não existe. Eles rodam
na árvore de trabalho, no job de qualidade do CI e no venv local.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[2]
ARQUIVO = RAIZ / "docker-compose.yml"

pytestmark = pytest.mark.skipif(
    not ARQUIVO.is_file(), reason="docker-compose.yml fora da imagem de desenvolvimento"
)


def _compose() -> dict:
    return yaml.safe_load(ARQUIVO.read_text(encoding="utf-8"))


def _hosts_permitidos(comando: str) -> set[str]:
    partes = comando.split()
    assert "--allowed-hosts" in partes, "o servidor MLflow do Compose precisa declarar --allowed-hosts"
    return set(partes[partes.index("--allowed-hosts") + 1].split(","))


def test_mlflow_do_compose_aceita_o_host_de_todo_cliente() -> None:
    """Todo FREQUENCIA_MLFLOW_URI do Compose aponta para um host liberado."""
    servicos = _compose()["services"]
    liberados = _hosts_permitidos(servicos["mlflow"]["command"])
    clientes = {}
    for nome, servico in servicos.items():
        uri = (servico.get("environment") or {}).get("FREQUENCIA_MLFLOW_URI", "")
        if uri.startswith("http"):
            analise = urlparse(uri)
            clientes[nome] = f"{analise.hostname}:{analise.port}"
    assert clientes, "nenhum serviço do Compose usa o servidor MLflow"
    for nome, host in clientes.items():
        assert host in liberados, f"o serviço {nome} usa o Host {host}, fora de {sorted(liberados)}"


def test_mlflow_do_compose_aceita_o_acesso_pelo_navegador_e_pelo_healthcheck() -> None:
    """A porta publicada (navegador, CI) e o healthcheck usam hosts liberados."""
    liberados = _hosts_permitidos(_compose()["services"]["mlflow"]["command"])
    assert {"localhost:5000", "127.0.0.1:5000"} <= liberados
