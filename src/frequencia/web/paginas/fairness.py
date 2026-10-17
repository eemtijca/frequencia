# Página de fairness: dispersão de revogação e taxa de alerta por série.
"""Impacto desigual do indicador entre grupos."""

from __future__ import annotations

import streamlit as st

from frequencia.web import estado as estado_mod


def renderizar() -> None:
    """Renderiza métricas por subgrupo e fairness básico."""
    st.title("Fairness e impacto")
    st.caption("Desempenho e taxa de alerta por série, turma e faixa de histórico.")

    experimentos = estado_mod.experimentos()
    if not experimentos:
        st.caption("Nenhum experimento para inspecionar.")
        return
    escolha = st.selectbox("Experimento", [c["identificador"] for c in experimentos])
    corpo = next(c for c in experimentos if c["identificador"] == escolha)
    detalhe = estado_mod.detalhe_experimento(corpo["pasta"])
    avaliacao = detalhe["avaliacao"]
    if not avaliacao:
        st.caption("Etapa de avaliação não concluída.")
        return

    fairness = avaliacao.get("fairness", {})
    colunas = st.columns(2)
    colunas[0].metric("Dispersão de revocação", fairness.get("dispersao_revocacao"))
    colunas[1].metric("Dispersão de taxa de alerta", fairness.get("dispersao_taxa_alerta"))
    if fairness.get("revocacoes_por_serie"):
        st.caption(
            "Revocação por série (ordem alfabética): "
            + ", ".join(str(v) for v in fairness["revocacoes_por_serie"])
        )

    st.subheader("Desempenho por série")
    por_serie = avaliacao.get("por_serie", [])
    if por_serie:
        st.dataframe(por_serie, use_container_width=True, hide_index=True)

    st.subheader("Por faixa de histórico")
    por_faixa = avaliacao.get("por_faixa_historico", [])
    if por_faixa:
        st.dataframe(por_faixa, use_container_width=True, hide_index=True)

    st.subheader("Leitura responsável")
    st.info(
        "Dispersão alta entre séries pede investigação antes de ampliar o uso: "
        "o indicador pode estar aprendendo desigualdade de registro de chamadas "
        "em vez de risco real. A decisão final é sempre humana e revisível."
    )
