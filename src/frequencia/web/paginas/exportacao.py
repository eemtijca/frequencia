# Página de exportação: runtime, tamanho, latência, paridade e ONNX.
"""Artefato de inferência no navegador sob a ótica da governança."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from frequencia.web import estado as estado_mod
from frequencia.web import tarefas as tarefas_mod


def renderizar() -> None:
    """Renderiza a validação do artefato exportado."""
    st.title("Exportação")
    st.caption("Destino: navegador de celular modesto, offline, sem dependências.")

    experimentos = estado_mod.experimentos()
    if not experimentos:
        st.caption("Nenhum experimento exportado ainda.")
        return
    escolha = st.selectbox("Experimento", [c["identificador"] for c in experimentos])
    corpo = next(c for c in experimentos if c["identificador"] == escolha)
    pasta_experimento = Path(corpo["pasta"])
    alvo_validacao = pasta_experimento / "exportacoes" / "validacao.json"
    if not alvo_validacao.is_file():
        st.caption("Etapa de exportação não concluída.")
        return

    from frequencia.web.estado import ler_json

    validacao = ler_json(alvo_validacao) or {}
    colunas = st.columns(4)
    colunas[0].metric("Tamanho (bytes)", validacao.get("tamanho_bytes"))
    colunas[1].metric("Tamanho dentro do limite", "sim" if validacao.get("tamanho_ok") else "não")
    colunas[2].metric("Latência (ms)", validacao.get("latencia_ms"))
    colunas[3].metric("Paridade Python e JS", "ok" if validacao.get("paridade_ok") else "falhou")

    onnx = validacao.get("onnx", {})
    if "arquivo" in onnx:
        st.caption(f"Caminho alternativo ONNX disponível: {onnx['arquivo']} ({onnx['tamanho_bytes']} bytes).")
    elif "erro" in onnx:
        st.caption(f"ONNX não gerado nesta execução: {onnx['erro'][:120]}.")

    st.subheader("Casos sintéticos de autoverificação")
    alvo_dados = pasta_experimento / "exportacoes" / "dados-teste.json"
    if alvo_dados.is_file():
        import json

        dados = json.loads(alvo_dados.read_text(encoding="utf-8"))
        st.caption(f"{dados['total']} casos com saídas esperadas; o app roda na ativação.")
        with st.expander("Primeiro caso"):
            st.json(dados["casos"][0], expanded=False)

    pacotes = sorted((pasta_experimento.parents[2] / "var" / "pacotes").glob("risco-infrequencia-*"))
    _ = pacotes
    st.subheader("Revalidar paridade com Node")
    pasta_pacote = st.text_input("Pasta do pacote", value=str(_ultimo_pacote()) or "")
    if st.button("Rodar testes sintéticos") and pasta_pacote:
        recibo = tarefas_mod.disparar(
            ["exportacao", "testar-sinteticos", pasta_pacote],
            rotulo="paridade node",
        )
        st.success(f"Tarefa {recibo['id']} disparada.")


def _ultimo_pacote() -> str | None:
    """Localiza o pacote mais recente do workspace."""
    from frequencia.infra import caminhos

    pasta = caminhos.caminho("pacotes")
    pacotes = sorted(pasta.glob("risco-infrequencia-*"))
    return str(pacotes[-1]) if pacotes else None
