# Página de registro e promoção: estados, aprovações e checklist.
"""Fluxo de promoção entre estados com papel de aprovador."""

from __future__ import annotations

import streamlit as st

from frequencia.web import estado as estado_mod
from frequencia.web import tarefas as tarefas_mod


def renderizar() -> None:
    """Renderiza versões e o fluxo de promoção com confirmação dupla."""
    st.title("Registro e promoção")
    st.caption("Estados: experimental, candidato, homologado, publicado, descontinuado, arquivado.")

    registro = estado_mod.registro().get("modelos", {}).get("risco-infrequencia")
    if not registro:
        st.caption("Nenhuma versão registrada no workspace.")
        return

    linhas = [
        {
            "versão": versao,
            "situação": detalhe["situacao"],
            "treinado em": detalhe["treinado_em"],
            "validade": detalhe["validade_ate"],
            "AUC": detalhe.get("metricas", {}).get("auc", ""),
        }
        for versao, detalhe in sorted(registro["versoes"].items(), reverse=True)
    ]
    st.dataframe(linhas, use_container_width=True, hide_index=True)

    papel = st.session_state.get("papel_sessao", "observador")
    versoes = sorted(registro["versoes"].keys(), reverse=True)
    st.subheader("Promover versão")
    colunas = st.columns(2)
    versao = colunas[0].selectbox("Versão", versoes)
    alvo_estado = colunas[1].selectbox(
        "Estado destino",
        ["candidato", "homologado", "publicado", "descontinuado", "arquivado"],
    )
    detalhe = registro["versoes"].get(versao, {})

    # O checklist vem do motor: o painel exibe os mesmos requisitos que a
    # promoção aplica, sem cálculo próprio.
    from frequencia.modelos import registro as registro_mod

    st.markdown("**Checklist antes da promoção**")
    checklist = {
        **registro_mod.requisitos_promocao("risco-infrequencia", versao, alvo_estado),
        "Limitações documentadas": bool(detalhe.get("limitacoes")),
    }
    for item, ok in checklist.items():
        st.checkbox(item, value=ok, disabled=True)

    if papel != "aprovador":
        st.info("A promoção exige o papel de aprovador na barra lateral.")
        return
    confirmar = st.checkbox("Confirmo a promoção com revisão do checklist acima")
    if st.button("Promover", type="primary", disabled=not confirmar):
        recibo = tarefas_mod.disparar(
            [
                "registro",
                "promover",
                "risco-infrequencia",
                versao,
                "--estado",
                alvo_estado,
                "--papel",
                "aprovador",
            ],
            rotulo=f"promover {versao} para {alvo_estado}",
        )
        st.success(f"Tarefa {recibo['id']} disparada.")

    st.subheader("Aprovações registradas")
    for linha in linhas[:3]:
        versao_linha = linha["versão"]
        aprovacoes = registro["versoes"][versao_linha].get("aprovacoes", [])
        if aprovacoes:
            st.caption(
                f"{versao_linha}: "
                + "; ".join(
                    f"{'aprovado' if a['aprovado'] else 'rejeitado'} por {a['ator']}" for a in aprovacoes[-3:]
                )
            )
