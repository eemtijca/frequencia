# Aplicação Streamlit: console de governança sobre o mesmo motor da CLI.
"""Console científico e de governança do FrequencIA.

A interface é uma janela para o motor que a CLI opera: lê o mesmo estado em
var/ e dispara as mesmas operações em tarefas de fundo. Nunca substitui a
CLI para automação. Papéis: observador, cientista, engenheiro e aprovador.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="FrequencIA",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

RAIZ_FONTE = str(Path(__file__).resolve().parents[2])
sys.path.insert(0, RAIZ_FONTE)

from frequencia.infra import caminhos
from frequencia.web import estado as estado_mod
from frequencia.web import tarefas as tarefas_mod
from frequencia.web.paginas import (
    calibracao,
    comparacao,
    configuracoes,
    dados,
    datasets,
    ensemble,
    experimentos,
    exportacao,
    fairness,
    features,
    governanca,
    manifesto,
    monitoramento,
    publicacao,
    registro,
    visao_geral,
)


def seletor_papel() -> str:
    """Papel da sessão; usado para liberar ações sensíveis."""
    if "papel" not in st.session_state:
        st.session_state.papel = "observador"
    st.session_state.papel = st.sidebar.selectbox(
        "Papel nesta sessão",
        ["observador", "cientista", "engenheiro", "aprovador"],
        index=["observador", "cientista", "engenheiro", "aprovador"].index(st.session_state.papel),
        help="O papel libera ou barra ações de estado; a auditoria registra quem agiu.",
    )
    return st.session_state.papel


def painel_tarefas() -> None:
    """Resumo das tarefas de fundo na barra lateral."""
    with st.sidebar.expander("Tarefas de fundo", expanded=False):
        tarefas = estado_mod.tarefas()
        if not tarefas:
            st.caption("Nenhuma tarefa disparada nesta sessão do workspace.")
            return
        for tarefa in tarefas[:6]:
            estado = str(tarefa.get("estado") or "?")
            emoji = {"concluida": "ok", "falhou": "erro", "iniciada": "rodando"}.get(estado, "?")
            st.caption(
                f"{emoji} {tarefa.get('rotulo') or tarefa.get('comando', '')[:40]} ({tarefa.get('estado')})"
            )
        if st.button("Atualizar painel"):
            st.rerun()


def principal() -> None:
    """Monta a navegação multipágina e o contexto da sessão."""
    papel = seletor_papel()
    st.sidebar.divider()
    painel_tarefas()
    st.sidebar.caption(
        "Workspace: "
        f"{caminhos.raiz_workspace()}\n"
        "A inferência publicada roda no navegador; aqui é só governança."
    )

    paginas = {
        "Visão geral": visao_geral,
        "Dados": dados,
        "Features": features,
        "Datasets": datasets,
        "Experimentos": experimentos,
        "Comparação": comparacao,
        "Ensemble": ensemble,
        "Calibração": calibracao,
        "Fairness e impacto": fairness,
        "Exportação": exportacao,
        "Manifesto e pacote": manifesto,
        "Registro e promoção": registro,
        "Publicação": publicacao,
        "Monitoramento": monitoramento,
        "Governança e privacidade": governanca,
        "Configurações": configuracoes,
    }
    selecao = st.navigation(
        [
            st.Page(
                modulo.renderizar,
                title=titulo,
                icon="📌" if indice == 0 else None,
            )
            for indice, (titulo, modulo) in enumerate(paginas.items())
        ]
    )
    st.session_state.papel_sessao = papel
    st.session_state.disparar_tarefa = tarefas_mod.disparar
    selecao.run()


if __name__ == "__main__":
    principal()
