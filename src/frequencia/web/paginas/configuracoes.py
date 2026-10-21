# Página de configurações: ambiente, limites de gates, papéis e integração.
"""Parâmetros do ecossistema na interface."""

from __future__ import annotations

import streamlit as st


def renderizar() -> None:
    """Renderiza as configurações do ambiente e dos gates."""
    st.title("Configurações")
    st.caption("Ambiente, limites de gates, papéis e integração com o FrequenciApp.")

    from frequencia.infra import ambiente

    ambiente_resolvido = ambiente.validar()
    colunas = st.columns(3)
    colunas[0].metric("Perfil", ambiente_resolvido.perfil)
    colunas[1].metric("Fuso", ambiente_resolvido.fuso)
    colunas[2].metric("Semente padrão", ambiente_resolvido.semente)
    st.caption(f"Workspace: {ambiente_resolvido.workspace}")
    st.caption(f"MLflow: {ambiente_resolvido.mlflow_uri}")

    st.subheader("Limites de gates de promoção")
    from frequencia.pipelines.avaliacao import GATES_PADRAO

    nomes = {
        "auc_minimo": "AUC mínimo no teste",
        "ece_maximo": "ECE máximo no teste",
        "cobertura_conformal_minima": "Cobertura conforme mínima por classe",
        "taxa_alerta_maxima": "Taxa de alerta máxima",
        "melhora_sobre_baseline_minima": "Ganho mínimo de AUC sobre o baseline",
        "lift_alerta_minimo": "Lift mínimo do alerta",
        "revocacao_alerta_minima": "Revocação mínima do alerta",
        "tamanho_pacote_maximo_bytes": "Tamanho do pacote (bytes)",
        "latencia_maxima_ms": "Latência máxima (ms)",
        "ece_maximo_partida_a_frio": "ECE máximo na partida a frio",
    }
    # A tabela percorre todos os gates do motor: gate novo aparece aqui sem
    # depender de alguém lembrar de acrescentá-lo à página.
    tabela = [{"gate": nomes.get(chave, chave), "valor": valor} for chave, valor in GATES_PADRAO.items()]
    st.dataframe(tabela, use_container_width=True, hide_index=True)
    st.caption("Alterações de gates exigem ADR e vão pela CLI, não por aqui.")

    st.subheader("Papéis previstos")
    st.dataframe(
        [
            {"papel": "observador", "pode": "consultar todas as páginas"},
            {"papel": "cientista", "pode": "disparar experimentos e geração sintética"},
            {"papel": "engenheiro", "pode": "construir datasets, exportar e empacotar"},
            {"papel": "aprovador", "pode": "promover, publicar, reverter e revogar"},
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Integração com o FrequenciApp")
    from frequencia.integracao import contrato as contrato_mod

    st.markdown("**Plano de feature flag**")
    for passo in contrato_mod.PLANO_FEATURE_FLAG:
        st.markdown(f"- {passo}")
    st.markdown("**Vocabulário aprovado**")
    st.json(contrato_mod.MENSAGENS_APROVADAS, expanded=False)
