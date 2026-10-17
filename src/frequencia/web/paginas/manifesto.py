# Página de manifesto e pacote: contrato lido pelo FrequenciApp.
"""Inspecção do manifesto de compatibilidade do pacote."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from frequencia.web import estado as estado_mod


def renderizar() -> None:
    """Renderiza o manifesto do pacote mais recente ou publicado."""
    st.title("Manifesto e pacote")
    st.caption("O app lê o manifesto e decide: versão, validade, perfis e fallback.")

    versao = None
    atual = estado_mod.versao_atual()
    if atual:
        versao = atual["versao"]
        st.success(f"Versão publicada atual: {versao}.")
    from frequencia.infra import caminhos

    pacotes = sorted(caminhos.caminho("pacotes").glob("risco-infrequencia-*"))
    if pacotes:
        escolha = st.selectbox("Pacote", [p.name for p in pacotes], index=len(pacotes) - 1)
        pasta = next(p for p in pacotes if p.name == escolha)
    elif versao:
        pasta = caminhos.caminho("publicacoes") / versao
    else:
        st.caption("Nenhum pacote montado no workspace ainda.")
        return

    alvo = Path(pasta) / "manifest.json"
    if not alvo.is_file():
        st.caption(f"manifest.json ausente em {pasta}.")
        return
    manifesto = json.loads(alvo.read_text(encoding="utf-8"))

    colunas = st.columns(4)
    colunas[0].metric("Versão do modelo", manifesto["versao_modelo"])
    colunas[1].metric("Mínimo do app", manifesto["min_app_versao"])
    colunas[2].metric("Tamanho (bytes)", manifesto["tamanho_bytes"])
    colunas[3].metric("Válido até", manifesto["validade_ate"])

    st.subheader("Perfis de dados suportados")
    st.dataframe(manifesto["perfis_dados"], use_container_width=True, hide_index=True)

    st.subheader("Contrato de features")
    st.caption(
        f"{len(manifesto['contrato']['features'])} features na ordem fixa; "
        "padrões preenchem valores ausentes no app."
    )

    st.subheader("Calibração e limiares")
    st.json(
        {
            "calibracao": manifesto["calibracao"],
            "limiares_alerta": manifesto["limiares_alerta"],
        },
        expanded=False,
    )

    st.subheader("Limitações declaradas")
    for limite in manifesto["limitacoes"]:
        st.markdown(f"- {limite}")

    st.subheader("Arquivos e hashes")
    st.dataframe(
        [{"arquivo": nome, "hash": valor[:16]} for nome, valor in manifesto["arquivos"].items()],
        use_container_width=True,
        hide_index=True,
    )
