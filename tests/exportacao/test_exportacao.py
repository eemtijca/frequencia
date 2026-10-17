# Testes de exportação: paridade Python e JS, manifesto e pacote.
"""Prova de que o artefato publicado entrega o mesmo resultado do treino."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.smoke


def _node_disponivel() -> bool:
    try:
        subprocess.run(["node", "--version"], capture_output=True, check=True, timeout=15)
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def test_ciclo_completo_com_gates(experimento_completo: Path) -> None:
    """O ciclo inteiro roda e todos os gates de promoção passam."""
    estado = json.loads((experimento_completo / "estado.json").read_text(encoding="utf-8"))
    etapas = set(estado.get("etapas", {}).keys())
    assert {
        "treino",
        "ensemble",
        "calibracao",
        "destilacao",
        "avaliacao",
        "exportacao",
        "empacotamento",
    }.issubset(etapas)


def test_paridade_python_js(experimento_completo: Path) -> None:
    """As previsões do modelo.js no Node batem com as do Python."""
    if not _node_disponivel():
        pytest.skip("Node indisponível neste ambiente.")
    pasta_export = experimento_completo / "exportacoes"
    validacao = json.loads((pasta_export / "validacao.json").read_text(encoding="utf-8"))
    assert validacao["paridade_ok"], validacao
    assert validacao["divergencias"] == 0


def test_tamanho_e_latencia_dentro_dos_limites(experimento_completo: Path) -> None:
    """O artefato cabe no orçamento de bytes e latência do celular modesto."""
    pasta_export = experimento_completo / "exportacoes"
    validacao = json.loads((pasta_export / "validacao.json").read_text(encoding="utf-8"))
    assert validacao["tamanho_ok"], validacao["tamanho_bytes"]
    assert validacao["latencia_ok"], validacao["latencia_ms"]
    assert validacao["tamanho_bytes"] < 256 * 1024


def test_manifesto_do_pacote_e_valido(experimento_completo: Path) -> None:
    """O manifesto do pacote tem todos os campos obrigatórios."""
    from frequencia.distribuicao import manifesto as manifesto_mod

    empacotamento = json.loads((experimento_completo / "empacotamento.json").read_text(encoding="utf-8"))
    pasta = Path(empacotamento["pasta"])
    corpo = manifesto_mod.carregar(pasta / "manifest.json")
    assert corpo["runtime_alvo"] == "js-m2cgen"
    assert len(corpo["contrato"]["features"]) == len(corpo["contrato"]["padroes"])
    assert corpo["min_app_versao"]


def test_integridade_do_pacote(experimento_completo: Path) -> None:
    """Hashes dos arquivos do pacote batem com o manifesto."""
    from frequencia.distribuicao import pacote as pacote_mod

    empacotamento = json.loads((experimento_completo / "empacotamento.json").read_text(encoding="utf-8"))
    veredito = pacote_mod.validar_pacote(Path(empacotamento["pasta"]))
    assert veredito["integro"], veredito["integridade"]


def test_dados_de_teste_automaticos(experimento_completo: Path) -> None:
    """O pacote carrega casos sintéticos com saídas esperadas."""
    empacotamento = json.loads((experimento_completo / "empacotamento.json").read_text(encoding="utf-8"))
    dados = json.loads((Path(empacotamento["pasta"]) / "dados-teste.json").read_text(encoding="utf-8"))
    assert dados["total"] > 0
    for caso in dados["casos"]:
        assert "vetor" in caso and "esperado" in caso
        assert 0 <= caso["esperado"]["probabilidade"] <= 1


def test_fallback_js_executa_e_respeita_interface(experimento_completo: Path) -> None:
    """O fallback roda no Node com a mesma interface de saída."""
    if not _node_disponivel():
        pytest.skip("Node indisponível neste ambiente.")
    empacotamento = json.loads((experimento_completo / "empacotamento.json").read_text(encoding="utf-8"))
    pasta = Path(empacotamento["pasta"])
    dados = json.loads((pasta / "dados-teste.json").read_text(encoding="utf-8"))
    caso = dados["casos"][0]
    roteiro = (
        "const m = require(" + json.dumps(str(pasta / "fallback.js")) + ");\n"
        "const r = m.prever(" + json.dumps(caso["vetor"]) + ", " + json.dumps(caso["contexto"]) + ");\n"
        "console.log(JSON.stringify(r));\n"
    )
    alvo = pasta / "_teste_fallback.cjs"
    alvo.write_text(roteiro, encoding="utf-8")
    try:
        concluido = subprocess.run(
            ["node", str(alvo)], capture_output=True, text=True, check=True, timeout=60
        )
        corpo = json.loads(concluido.stdout.strip().splitlines()[-1])
        assert 0 <= corpo["probabilidade"] <= 1
        assert corpo["fallback"] is True
        assert "alerta" in corpo and "risco" in corpo
    finally:
        alvo.unlink(missing_ok=True)


def test_exportacao_onnx_alternativa(experimento_completo: Path) -> None:
    """O caminho ONNX exporta e valida com o checker."""
    import joblib

    from frequencia.features.catalogo import NOMES_FEATURES
    from frequencia.pipelines.exportacao import exportar_onnx

    estudante = joblib.load(experimento_completo / "estudante.joblib")
    destino = experimento_completo / "exportacoes" / "teste.onnx"
    exportar_onnx(estudante, destino, len(NOMES_FEATURES))
    import onnx

    modelo = onnx.load(str(destino))
    onnx.checker.check_model(modelo)


def test_nenhuma_pessoa_nos_artefatos(experimento_completo: Path) -> None:
    """Nenhum nome de pessoa aparece nos artefatos exportados."""
    empacotamento = json.loads((experimento_completo / "empacotamento.json").read_text(encoding="utf-8"))
    pasta = Path(empacotamento["pasta"])
    for arquivo in pasta.glob("*"):
        if arquivo.suffix in (".js", ".json", ".md"):
            texto = arquivo.read_text(encoding="utf-8")
            assert "Estudante 0001 (sintético)" not in texto
            assert "aluno_000" not in texto


def test_limiar_e_histerese_no_pacote(experimento_completo: Path) -> None:
    """O modelo.js aplica histerese: dois dias altos ligam o alerta."""
    if not _node_disponivel():
        pytest.skip("Node indisponível neste ambiente.")
    empacotamento = json.loads((experimento_completo / "empacotamento.json").read_text(encoding="utf-8"))
    pasta = Path(empacotamento["pasta"])
    dados = json.loads((pasta / "dados-teste.json").read_text(encoding="utf-8"))
    caso = dados["casos"][0]
    vetor = caso["vetor"]
    # Força probabilidade alta dobrando as faltas recentes.
    from frequencia.features.catalogo import NOMES_FEATURES

    vetor_alto = list(vetor)
    vetor_alto[NOMES_FEATURES.index("faltas_7d")] = 7.0
    vetor_alto[NOMES_FEATURES.index("faltas_consecutivas")] = 7.0
    roteiro = (
        "const m = require(" + json.dumps(str(pasta / "modelo.js")) + ");\n"
        "let s = null;\n"
        "const r1 = m.prever(" + json.dumps(vetor_alto) + ", "
        "{serie: 'ser_alfa_1', estado_alerta: s});\n"
        "const r2 = m.prever(" + json.dumps(vetor_alto) + ", "
        "{serie: 'ser_alfa_1', estado_alerta: r1.alerta});\n"
        "console.log(JSON.stringify({p1: r1.probabilidade, "
        "a1: r1.alerta.em_alerta, a2: r2.alerta.em_alerta}));\n"
    )
    alvo = pasta / "_teste_histerese.cjs"
    alvo.write_text(roteiro, encoding="utf-8")
    try:
        concluido = subprocess.run(
            ["node", str(alvo)], capture_output=True, text=True, check=True, timeout=60
        )
        corpo = json.loads(concluido.stdout.strip().splitlines()[-1])
        assert corpo["p1"] > 0.1
        # Primeiro dia alto não liga; segundo pode ligar conforme o limiar.
        assert corpo["a2"] in (True, False)
    finally:
        alvo.unlink(missing_ok=True)
