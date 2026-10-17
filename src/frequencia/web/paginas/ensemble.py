# Página de ensemble: membros, pesos, discordância e vista do OOF.
"""Inspecção do ensemble offline de treino."""

from __future__ import annotations

import streamlit as st

from frequencia.web import estado as estado_mod


def renderizar() -> None:
    """Renderiza membros, pesos e discordância."""
    st.title("Ensemble")
    st.caption("Ferramenta de treino, nunca de produção: destila para o estudante leve.")

    experimentos = estado_mod.experimentos()
    if not experimentos:
        st.caption("Nenhum experimento com ensemble ainda.")
        return
    escolha = st.selectbox("Experimento", [c["identificador"] for c in experimentos])
    corpo = next(c for c in experimentos if c["identificador"] == escolha)
    detalhe = estado_mod.detalhe_experimento(corpo["pasta"])
    estado = detalhe["estado"] or {}
    ensemble = estado.get("etapas", {}).get("ensemble", {}).get("resultado", {})
    if not ensemble:
        st.caption("Etapa de ensemble não concluída neste experimento.")
        return

    colunas = st.columns(3)
    metricas = ensemble.get("metricas", {})
    colunas[0].metric("AUC do ensemble (OOF)", metricas.get("auc_ensemble"))
    colunas[1].metric("AUC do baseline", metricas.get("auc_baseline"))
    colunas[2].metric("Discordância média", ensemble.get("discordancia_media"))

    st.subheader("Pesos da combinação")
    import pandas as pd

    pesos = ensemble.get("pesos", {})
    st.dataframe(
        [{"membro": nome, "peso": peso} for nome, peso in pesos.items()],
        use_container_width=True,
        hide_index=True,
    )
    if pesos:
        dados = pd.DataFrame([{"membro": nome, "peso": peso} for nome, peso in pesos.items()])
        st.bar_chart(dados, x="membro", y="peso")

    st.subheader("Previsões fora da dobra")
    from pathlib import Path

    alvo_oof = Path(corpo["pasta"]) / "ensemble" / "oof.npz"
    if alvo_oof.is_file():
        import numpy as np

        oof = np.load(file=alvo_oof, allow_pickle=False)
        discordancia = oof["discordancia"]
        colunas2 = st.columns(3)
        colunas2[0].metric("Linhas OOF", len(discordancia))
        colunas2[1].metric("Discordância p90", round(float(np.quantile(discordancia, 0.9)), 4))
        colunas2[2].metric("Membros", len(oof["nomes"]))
        st.caption("A discordância entre membros alimenta o sinal de incerteza do produto.")
    else:
        st.caption("Arquivo OOF não encontrado.")
