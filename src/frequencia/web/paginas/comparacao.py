# Página de comparação: métricas lado a lado entre experimentos.
"""Comparação de versões e experimentos."""

from __future__ import annotations

import streamlit as st

from frequencia.web import estado as estado_mod


def renderizar() -> None:
    """Renderiza a comparação de experimentos."""
    st.title("Comparação")
    st.caption("Métricas lado a lado, curva de aprendizado e calibração entre experimentos.")

    experimentos = estado_mod.experimentos()
    if len(experimentos) < 1:
        st.caption("Nenhum experimento para comparar ainda.")
        return
    identificadores = [c["identificador"] for c in experimentos]
    escolha = st.multiselect(
        "Experimentos", identificadores, default=identificadores[: min(2, len(identificadores))]
    )
    if len(escolha) < 1:
        st.caption("Escolha ao menos um experimento.")
        return

    linhas = []
    detalhes = {}
    for identificador in escolha:
        corpo = next(c for c in experimentos if c["identificador"] == identificador)
        detalhe = estado_mod.detalhe_experimento(corpo["pasta"])
        detalhes[identificador] = detalhe
        if detalhe["avaliacao"]:
            linha = {"experimento": identificador}
            linha.update(detalhe["avaliacao"]["metricas"])
            linhas.append(linha)
    if linhas:
        st.subheader("Métricas globais")
        st.dataframe(linhas, use_container_width=True, hide_index=True)

    st.subheader("Curva de aprendizado por histórico")
    import pandas as pd

    frames = []
    for identificador, detalhe in detalhes.items():
        curva = (detalhe["avaliacao"] or {}).get("curva_aprendizado", [])
        for ponto in curva:
            frames.append(
                {
                    "experimento": identificador,
                    "faixa": ponto["faixa"],
                    "auc": ponto["auc"],
                }
            )
    if frames:
        dados = pd.DataFrame(frames)
        st.line_chart(dados, x="faixa", y="auc", color="experimento")
    else:
        st.caption("Sem curva de aprendizado registrada.")

    st.subheader("Estabilidade temporal")
    for identificador, detalhe in detalhes.items():
        estabilidade = (detalhe["avaliacao"] or {}).get("estabilidade_temporal", [])
        if estabilidade:
            dados = pd.DataFrame([{"mes": p["mes"], "auc": p["auc"]} for p in estabilidade])
            st.caption(f"{identificador}: AUC por mês")
            st.bar_chart(dados, x="mes", y="auc")
