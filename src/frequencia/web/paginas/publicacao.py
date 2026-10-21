# Página de publicação: releases, rollback e revogação com confirmação dupla.
"""Canal de publicação na interface, com dupla confirmação."""

from __future__ import annotations

import streamlit as st

from frequencia.web import estado as estado_mod
from frequencia.web import tarefas as tarefas_mod


def renderizar() -> None:
    """Renderiza publicações e ações de rollback e revogação."""
    st.title("Publicação")
    st.caption("Canal local de releases; o app atualiza pelo Service Worker, nunca na chamada.")

    publicacoes = estado_mod.publicacoes()
    if not publicacoes:
        st.caption("Nenhuma versão publicada no workspace.")
        return
    st.dataframe(
        [
            {
                "versão": corpo["versao"],
                "publicada em": corpo["criado_em"],
                "hash": corpo["hash"][:16],
                "validade": corpo["validade_ate"],
            }
            for corpo in publicacoes
        ],
        use_container_width=True,
        hide_index=True,
    )

    atual = estado_mod.versao_atual()
    if atual:
        st.success(f"Versão atual em produção: {atual['versao']}.")

    papel = st.session_state.get("papel_sessao", "observador")
    if papel != "aprovador":
        st.info("Publicar, reverter e revogar exigem o papel de aprovador.")
        return

    st.subheader("Publicar pacote homologado")
    from frequencia.infra import caminhos

    pacotes = sorted(caminhos.caminho("pacotes").glob("risco-infrequencia-*"))
    if pacotes:
        escolha = st.selectbox("Pacote", [p.name for p in pacotes])
        pasta = next(p for p in pacotes if p.name == escolha)
        versao = st.text_input("Versão", value=escolha.replace("risco-infrequencia-", ""))
        if st.button("Publicar"):
            recibo = tarefas_mod.disparar(
                [
                    "publicacao",
                    "publicar",
                    str(pasta),
                    versao,
                ],
                rotulo=f"publicar {versao}",
                papel=papel,
            )
            st.success(f"Tarefa {recibo['id']} disparada.")

    st.subheader("Rollback e revogação")
    colunas = st.columns(2)
    versao_anterior = colunas[0].selectbox("Reverter para", [corpo["versao"] for corpo in publicacoes])
    versao_revogar = colunas[1].selectbox("Revogar", [corpo["versao"] for corpo in publicacoes])
    confirmacao = st.checkbox("Confirmo a operação destrutiva após revisão")
    colunas2 = st.columns(2)
    if colunas2[0].button("Reverter", disabled=not confirmacao):
        recibo = tarefas_mod.disparar(
            ["publicacao", "reverter", versao_anterior],
            rotulo=f"reverter para {versao_anterior}",
            papel=papel,
        )
        st.success(f"Tarefa {recibo['id']} disparada.")
    if colunas2[1].button("Revogar", disabled=not confirmacao):
        recibo = tarefas_mod.disparar(
            ["publicacao", "revogar", versao_revogar],
            rotulo=f"revogar {versao_revogar}",
            papel=papel,
        )
        st.success(f"Tarefa {recibo['id']} disparada.")
