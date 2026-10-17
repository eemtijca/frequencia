# Página de experimentos: lista, detalhe e disparo do ciclo completo.
"""Experimentos do modelo de risco na interface."""

from __future__ import annotations

import streamlit as st

from frequencia.web import estado as estado_mod
from frequencia.web import tarefas as tarefas_mod


def renderizar() -> None:
    """Renderiza experimentos e o disparo do ciclo."""
    st.title("Experimentos")
    st.caption(
        "Ciclo idempotente por etapa: treino, ensemble, calibração, destilação, avaliação e empacotamento."
    )

    st.subheader("Executar ciclo")
    datasets = estado_mod.datasets()
    if not datasets:
        st.caption("Construa um dataset antes de executar o ciclo.")
    else:
        escolha = st.selectbox("Dataset", [c["identificador"] for c in datasets])
        pasta = next(c for c in datasets if c["identificador"] == escolha)["pasta"]
        colunas = st.columns(3)
        identificador = colunas[0].text_input("Identificador", value="web-ciclo")
        versao = colunas[1].text_input("Versão do modelo", value="")
        semente = colunas[2].number_input("Semente", min_value=1, value=20261018, step=1)
        papel = st.session_state.get("papel_sessao", "observador")
        if papel in ("cientista", "engenheiro", "aprovador"):
            if st.button("Executar ciclo em fundo", type="primary"):
                argumentos = [
                    "experimentos",
                    "executar",
                    pasta,
                    "--identificador",
                    identificador,
                    "--semente",
                    str(int(semente)),
                ]
                if versao:
                    argumentos += ["--versao-modelo", versao]
                recibo = tarefas_mod.disparar(argumentos, rotulo=f"ciclo {identificador}")
                st.success(f"Tarefa {recibo['id']} disparada.")
        else:
            st.info("Papel de observador não dispara treinos. Troque o papel na barra lateral.")

    st.subheader("Experimentos registrados")
    experimentos = estado_mod.experimentos()
    if not experimentos:
        st.caption("Nenhum experimento no workspace.")
        return
    st.dataframe(
        [
            {
                "identificador": corpo["identificador"],
                "AUC": corpo.get("metricas", {}).get("auc", ""),
                "semente": corpo.get("semente", ""),
                "dataset": corpo.get("dataset", ""),
            }
            for corpo in experimentos
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Detalhe")
    escolha2 = st.selectbox("Experimento", [c["identificador"] for c in experimentos])
    corpo = next(c for c in experimentos if c["identificador"] == escolha2)
    detalhe = estado_mod.detalhe_experimento(corpo["pasta"])
    if detalhe["avaliacao"]:
        colunas3 = st.columns(4)
        metricas = detalhe["avaliacao"]["metricas"]
        colunas3[0].metric("AUC", metricas.get("auc"))
        colunas3[1].metric("AP", metricas.get("ap"))
        colunas3[2].metric("Brier", metricas.get("brier"))
        colunas3[3].metric("Precisão Top-10/dia", metricas.get("precisao_top_10_diario"))
    if detalhe["gates"]:
        vereditos = detalhe["gates"]["vereditos"]
        aprovado = detalhe["gates"]["aprovado"]
        if aprovado:
            st.success("Todos os gates de promoção aprovados.")
        else:
            falhas = [nome for nome, ok in vereditos.items() if not ok]
            st.warning(f"Gates reprovados: {', '.join(falhas)}.")
    if detalhe["estado"]:
        etapas = detalhe["estado"].get("etapas", {})
        st.caption("Etapas concluídas: " + ", ".join(etapas.keys()))
