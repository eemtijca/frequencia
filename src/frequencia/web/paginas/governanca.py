# Página de governança e privacidade: cartões, relatórios e auditoria.
"""Documentação viva das políticas de privacidade e prestação de contas."""

from __future__ import annotations

import streamlit as st

from frequencia.web import estado as estado_mod


def renderizar() -> None:
    """Renderiza governança, privacidade e a trilha de auditoria."""
    st.title("Governança e privacidade")
    st.caption("Regras explícitas: dado pessoal não entra no modelo publicado.")

    st.subheader("Regras inegociáveis")
    regras = [
        "Nome nunca é feature; dado sensível só com salvaguarda declarada.",
        "Dados pessoais não entram no modelo publicado nem em telemetria externa.",
        "Treino com dados reais exige autorização e base legal registrada.",
        "Dataset institucional não é publicado sem revisão de privacidade.",
        "Inputs individuais não são registrados fora do dispositivo.",
    ]
    for regra in regras:
        st.markdown(f"- {regra}")

    st.subheader("Relatório de risco atual")
    risco = estado_mod.resumo_risco()
    nivel = risco.get("nivel")
    if nivel in ("medio", "critico"):
        st.warning(f"Nível de risco: {nivel}.")
    else:
        st.caption(f"Nível de risco: {nivel}.")
    achados = risco.get("achados", [])
    if achados:
        st.dataframe(achados, use_container_width=True, hide_index=True)

    st.subheader("Cartão do modelo publicado")
    atual = estado_mod.versao_atual()
    if atual:
        from frequencia.infra import caminhos

        alvo = caminhos.caminho("publicacoes") / atual["versao"] / "modelo-cartao.md"
        if alvo.is_file():
            st.markdown(alvo.read_text(encoding="utf-8"))
        else:
            st.caption("Cartão não encontrado no release.")
    else:
        st.caption("Nenhuma versão publicada; o cartão vem com o pacote.")

    st.subheader("Bases legais e retenção")
    st.markdown(
        "- Exportações institucionais: base legal registrada no momento da importação.\n"
        "- Retenção: enquanto a escola mantiver o cadastro; exclusão a pedido.\n"
        "- Logs: agregados, sem dados de alunos, conforme docs/privacidade-lgpd.md."
    )

    st.subheader("Auditoria")
    eventos = estado_mod.auditoria(limite=30)
    if eventos:
        st.dataframe(
            [
                {
                    "momento": evento["momento"],
                    "ator": evento.get("ator", ""),
                    "ação": evento["acao"],
                    "alvo": evento.get("alvo", ""),
                    "papel": evento.get("papel", ""),
                }
                for evento in eventos
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("Sem eventos de auditoria ainda.")
