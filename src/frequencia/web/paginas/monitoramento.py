# Página de monitoramento: feedback, drift, validade e recomendações.
"""Saúde pós-publicação na interface."""

from __future__ import annotations

import streamlit as st

from frequencia.web import estado as estado_mod


def renderizar() -> None:
    """Renderiza saúde, feedback e recomendações."""
    st.title("Monitoramento")
    st.caption("Acompanhamento com dados agregados; nada individual é registrado.")

    from frequencia.monitoramento import saude

    corpo = saude.relatorio_saude()
    atual = corpo.get("versao_atual")
    if atual:
        colunas = st.columns(3)
        colunas[0].metric("Versão atual", atual)
        colunas[1].metric("Válido até", corpo.get("validade_ate", ""))
        colunas[2].metric("Recomendações", len(corpo["recomendacoes"]))
    else:
        st.caption("Nenhuma versão publicada para monitorar.")

    st.subheader("Recomendações")
    for item in corpo["recomendacoes"]:
        st.markdown(f"- {item}")

    st.subheader("Feedback agregado")
    feedback = estado_mod.feedback()
    if feedback:
        import pandas as pd

        ultimo = feedback[-1]
        dados = pd.DataFrame(
            {
                "dia": ultimo["dias"],
                "acurácia observada": ultimo["acuracia_observada"],
                "taxa de descarte": ultimo["taxa_descarte"],
            }
        )
        st.line_chart(dados.set_index("dia"))
    else:
        st.caption("Nenhum feedback importado. Use a CLI monitoramento importar-feedback.")

    st.subheader("Drift")
    drift = corpo.get("drift")
    if drift:
        st.dataframe(drift.get("piores", []), use_container_width=True, hide_index=True)
    else:
        st.caption("Sem cálculo de drift registrado. Use a CLI monitoramento drift.")
