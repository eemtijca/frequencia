# Testes de registro e publicação: transições, integridade, trava e rollback.
"""A governança vale no motor, não apenas na documentação."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from frequencia.infra import caminhos
from frequencia.infra import estado as estado_infra
from frequencia.infra.erros import ErroEstado, ErroPermissao, traduzir_erro
from frequencia.modelos import publicacao

IDENTIFICADOR = "risco-infrequencia"


def _pacote_falso(raiz: Path, versao: str) -> tuple[Path, str]:
    """Pacote mínimo com manifesto válido e hashes coerentes."""
    from frequencia.distribuicao import manifesto as manifesto_mod
    from frequencia.infra import hash as hash_infra

    pasta = raiz / f"pacote-{versao}"
    pasta.mkdir(parents=True)
    conteudos = {
        "modelo.js": f"// modelo {versao}\n",
        "fallback.js": "// fallback\n",
        "LEIA-ME.md": "# Pacote\n",
        "dados-teste.json": "{}\n",
        "modelo-cartao.md": "# Cartão\n",
    }
    for nome, texto in conteudos.items():
        (pasta / nome).write_text(texto, encoding="utf-8")
    arquivos = {nome: hash_infra.hash_arquivo(pasta / nome) for nome in conteudos}
    manifesto = manifesto_mod.montar(
        identificador=IDENTIFICADOR,
        versao_modelo=versao,
        criado_em="2026-10-21T10:00:00",
        dataset={},
        contrato={"features": ["x"], "padroes": [0.0], "tipos": ["contagem"]},
        calibracao={"a_platt": 1.0, "b_platt": 0.0, "taxa_base": 0.1},
        conformal={"nivel": 0.9, "limiares": {}},
        metricas={},
        limitacoes=[],
        hash_modelo=arquivos["modelo.js"],
        tamanho_bytes=10,
        arquivos=arquivos,
    )
    manifesto_mod.gravar(manifesto, pasta / "manifest.json")
    return pasta, arquivos["modelo.js"]


def _registrar(versao: str, hash_modelo: str) -> None:
    estado_infra.registrar_modelo(
        IDENTIFICADOR,
        versao,
        runtime_alvo="js-m2cgen",
        hash_artefato=hash_modelo,
        tamanho_bytes=10,
        dataset={},
        metricas={},
        limitacoes=[],
        referencia_artefato="",
        validade_ate="2027-04-19",
    )


def _homologar(versao: str) -> None:
    estado_infra.registrar_gates(IDENTIFICADOR, versao, {"aprovado": True, "vereditos": {}})
    estado_infra.promover_modelo(IDENTIFICADOR, versao, "candidato", ator="ana", papel="cientista")
    estado_infra.aprovar_modelo(IDENTIFICADOR, versao, True, ator="bia", comentario="revisado")
    estado_infra.promover_modelo(IDENTIFICADOR, versao, "homologado", ator="bia", papel="aprovador")


def test_publicacao_recusada_nao_grava_nada(workspace: Path, tmp_path: Path) -> None:
    """Versão ainda experimental não chega ao canal, nem parcialmente."""
    pasta, hash_modelo = _pacote_falso(tmp_path, "v1")
    _registrar("v1", hash_modelo)
    with pytest.raises(ValueError, match="Transição não permitida"):
        publicacao.publicar(pasta, versao_modelo="v1", ator="bia")
    canal = caminhos.caminho("publicacoes")
    assert not canal.exists() or not any(canal.iterdir())


def test_publicacao_recusa_pacote_com_hash_diferente_do_registrado(workspace: Path, tmp_path: Path) -> None:
    """Um zip qualquer não pode ser publicado sob a versão aprovada."""
    pasta, _ = _pacote_falso(tmp_path, "v1")
    _registrar("v1", "hash-do-artefato-aprovado")
    _homologar("v1")
    with pytest.raises(ErroEstado, match="hash"):
        publicacao.publicar(pasta, versao_modelo="v1", ator="bia")
    assert not (caminhos.caminho("publicacoes") / "v1").exists()


def test_publicacao_valida_marca_atual(workspace: Path, tmp_path: Path) -> None:
    """Pacote íntegro e homologado vira a versão atual do canal."""
    pasta, hash_modelo = _pacote_falso(tmp_path, "v1")
    _registrar("v1", hash_modelo)
    _homologar("v1")
    resultado = publicacao.publicar(pasta, versao_modelo="v1", ator="bia")
    assert "notas-de-mudanca.md" in resultado["arquivos"]
    assert publicacao.versao_atual()["versao"] == "v1"
    assert [item["versao"] for item in publicacao.listar_publicacoes()] == ["v1"]


def test_rollback_para_versao_inexistente_preserva_a_atual(workspace: Path, tmp_path: Path) -> None:
    """Rollback inválido não pode deixar o app sem versão publicada."""
    pasta, hash_modelo = _pacote_falso(tmp_path, "v1")
    _registrar("v1", hash_modelo)
    _homologar("v1")
    publicacao.publicar(pasta, versao_modelo="v1", ator="bia")
    with pytest.raises(ErroEstado):
        publicacao.reverter("v0", ator="bia")
    assert (caminhos.caminho("publicacoes") / "v1").is_dir()
    assert publicacao.versao_atual()["situacao"] == "publicado"


def test_rollback_redefine_a_versao_atual(workspace: Path, tmp_path: Path) -> None:
    """Depois do rollback, a versão atual do registro é a restaurada."""
    for versao in ("v1", "v2"):
        pasta, hash_modelo = _pacote_falso(tmp_path, versao)
        _registrar(versao, hash_modelo)
        _homologar(versao)
        publicacao.publicar(pasta, versao_modelo=versao, ator="bia")
    assert publicacao.versao_atual()["versao"] == "v2"
    publicacao.reverter("v1", ator="bia", motivo="regressão")
    atual = publicacao.versao_atual()
    assert atual["versao"] == "v1"
    assert atual["situacao"] == "publicado"
    versoes = {
        item["versao"]: item["situacao"] for item in publicacao.registro_mod.listar_versoes(IDENTIFICADOR)
    }
    assert versoes["v2"] == "descontinuado"


def test_registro_nao_perde_escritas_concorrentes(workspace: Path) -> None:
    """Aprovações paralelas ficam todas registradas, sem sobrescrita."""
    _registrar("v1", "h")

    def aprovar(indice: int) -> None:
        estado_infra.aprovar_modelo(IDENTIFICADOR, "v1", True, ator=f"pessoa-{indice}")

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(aprovar, range(40)))
    registro = json.loads(estado_infra.caminho_registro().read_text(encoding="utf-8"))
    assert len(registro["modelos"][IDENTIFICADOR]["versoes"]["v1"]["aprovacoes"]) == 40


def test_recusa_de_papel_nao_vira_erro_de_arquivo(workspace: Path) -> None:
    """A recusa por papel diz o motivo real, não falta de acesso a pasta."""
    _registrar("v1", "h")
    estado_infra.registrar_gates(IDENTIFICADOR, "v1", {"aprovado": True, "vereditos": {}})
    estado_infra.promover_modelo(IDENTIFICADOR, "v1", "candidato", ator="ana", papel="cientista")
    with pytest.raises(ErroPermissao) as excecao:
        estado_infra.promover_modelo(IDENTIFICADOR, "v1", "homologado", ator="ana", papel="cientista")
    assert "aprovador" in traduzir_erro(excecao.value)


def test_mensagem_de_valor_invalido_sem_ponto_duplo() -> None:
    """A tradução não acrescenta ponto a mensagem que já termina em ponto."""
    assert not traduzir_erro(ValueError("Transição não permitida.")).endswith("..")


def test_candidato_exige_gates_aprovados(workspace: Path) -> None:
    """Sem gates aprovados registrados, a versão não vira candidata."""
    _registrar("v1", "h")
    with pytest.raises(ErroEstado, match="gates"):
        estado_infra.promover_modelo(IDENTIFICADOR, "v1", "candidato", ator="ana", papel="cientista")
    estado_infra.registrar_gates(IDENTIFICADOR, "v1", {"aprovado": False, "vereditos": {"auc": False}})
    with pytest.raises(ErroEstado, match="gates"):
        estado_infra.promover_modelo(IDENTIFICADOR, "v1", "candidato", ator="ana", papel="cientista")


def test_homologado_exige_aprovacao_vigente(workspace: Path) -> None:
    """Sem aprovação, ou com rejeição posterior, a homologação é bloqueada."""
    _registrar("v1", "h")
    estado_infra.registrar_gates(IDENTIFICADOR, "v1", {"aprovado": True, "vereditos": {}})
    estado_infra.promover_modelo(IDENTIFICADOR, "v1", "candidato", ator="ana", papel="cientista")
    with pytest.raises(ErroEstado, match="aprovação"):
        estado_infra.promover_modelo(IDENTIFICADOR, "v1", "homologado", ator="bia", papel="aprovador")
    estado_infra.aprovar_modelo(IDENTIFICADOR, "v1", True, ator="bia")
    estado_infra.aprovar_modelo(IDENTIFICADOR, "v1", False, ator="caio", comentario="calibração ruim")
    with pytest.raises(ErroEstado, match="aprovação"):
        estado_infra.promover_modelo(IDENTIFICADOR, "v1", "homologado", ator="bia", papel="aprovador")
    estado_infra.aprovar_modelo(IDENTIFICADOR, "v1", True, ator="caio", comentario="recalibrado")
    estado_infra.promover_modelo(IDENTIFICADOR, "v1", "homologado", ator="bia", papel="aprovador")


def test_retirar_versao_nunca_fica_bloqueado(workspace: Path) -> None:
    """Descontinuar não depende de gates nem de aprovação."""
    _registrar("v1", "h")
    estado_infra.promover_modelo(IDENTIFICADOR, "v1", "descontinuado", ator="ana", papel="engenheiro")


def test_rollback_depois_de_revogacao(workspace: Path, tmp_path: Path) -> None:
    """Revogar a atual não impede restaurar a anterior."""
    for versao in ("v1", "v2"):
        pasta, hash_modelo = _pacote_falso(tmp_path, versao)
        _registrar(versao, hash_modelo)
        _homologar(versao)
        publicacao.publicar(pasta, versao_modelo=versao, ator="bia")
    publicacao.revogar("v2", ator="bia", motivo="erro no pacote")
    assert publicacao.versao_atual() is None
    publicacao.reverter("v1", ator="bia", motivo="volta à anterior")
    assert publicacao.versao_atual()["versao"] == "v1"


def test_novo_ciclo_nao_regrava_versao_promovida(workspace: Path) -> None:
    """Versão já promovida não volta a experimental nem troca de gates."""
    _registrar("v1", "h")
    estado_infra.registrar_gates(IDENTIFICADOR, "v1", {"aprovado": True, "vereditos": {"auc": True}})
    estado_infra.promover_modelo(IDENTIFICADOR, "v1", "candidato", ator="ana", papel="cientista")
    with pytest.raises(ErroEstado, match="candidato"):
        _registrar("v1", "outro-hash")
    estado_infra.registrar_gates(IDENTIFICADOR, "v1", {"aprovado": False, "vereditos": {"auc": False}})
    versao = estado_infra.ler_registro()["modelos"][IDENTIFICADOR]["versoes"]["v1"]
    assert versao["situacao"] == "candidato"
    assert versao["hash_artefato"] == "h"
    assert versao["gates"]["aprovado"] is True


def test_versao_experimental_pode_ser_regravada(workspace: Path) -> None:
    """Reexecutar o ciclo de uma versão ainda experimental continua possível."""
    _registrar("v1", "h1")
    _registrar("v1", "h2")
    assert estado_infra.ler_registro()["modelos"][IDENTIFICADOR]["versoes"]["v1"]["hash_artefato"] == "h2"
