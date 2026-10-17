# Página de visão geral: estado do ecossistema e ações pendentes.
"""Painel inicial de governança."""

from __future__ import annotations

import streamlit as st

from frequencia.web import estado as estado_mod


def renderizar() -> None:
    """Renderiza a visão geral do ecossistema."""
    st.title("Visão geral")
    st.caption(
        "Estado do ecossistema de risco de infrequência. "
        "Nenhum dado individual de aluno entra nesta interface."
    )

    contagens = estado_mod.contagens_workspace()
    colunas = st.columns(5)
    metricas = [
        ("Experimentos", contagens["experimentos"]),
        ("Datasets", contagens["datasets"]),
        ("Publicações", contagens["publicacoes"]),
        ("Importações", contagens["importacoes"]),
        ("Eventos de auditoria", contagens["auditoria"]),
    ]
    for coluna, (rotulo, valor) in zip(colunas, metricas, strict=True):
        coluna.metric(rotulo, valor)

    atual = estado_mod.versao_atual()
    if atual:
        st.success(f"Versão em produção: **{atual['versao']}**, válida até {atual.get('validade_ate')}.")
    else:
        st.info("Nenhuma versão publicada ainda. Execute o ciclo pela CLI ou pela página de Experimentos.")

    registro = estado_mod.registro().get("modelos", {}).get("risco-infrequencia", {})
    if registro:
        st.subheader("Situação das versões")
        linhas = [
            {
                "versao": versao,
                "situação": detalhe["situacao"],
                "treinado em": detalhe["treinado_em"],
                "AUC": detalhe.get("metricas", {}).get("auc", ""),
            }
            for versao, detalhe in sorted(registro.get("versoes", {}).items(), reverse=True)
        ]
        st.dataframe(linhas, use_container_width=True, hide_index=True)

    st.subheader("Últimas ações")
    eventos = estado_mod.auditoria(limite=8)
    if eventos:
        st.dataframe(
            [
                {
                    "momento": evento["momento"],
                    "ator": evento.get("ator", ""),
                    "ação": evento["acao"],
                    "alvo": evento.get("alvo", ""),
                }
                for evento in eventos
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("Sem ações registradas ainda.")

    st.subheader("Alertas")
    risco = estado_mod.resumo_risco()
    nivel = risco.get("nivel", "sem relatório")
    if nivel in ("medio", "critico"):
        st.warning(f"Relatório de privacidade com nível {nivel}. Veja a página de Governança.")
    else:
        st.caption(f"Relatório de privacidade: nível {nivel}.")
