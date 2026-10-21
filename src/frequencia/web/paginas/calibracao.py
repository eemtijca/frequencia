# Página de calibração: Platt, ECE, conformal e curva de aprendizado.
"""Inspeção da confiança estatística da saída."""

from __future__ import annotations

import streamlit as st

from frequencia.web import estado as estado_mod


def renderizar() -> None:
    """Renderiza parâmetros e cobertura da calibração."""
    st.title("Calibração")
    st.caption("Platt regularizado em direção à identidade, aquecimento e conformal por grupo.")

    experimentos = estado_mod.experimentos()
    if not experimentos:
        st.caption("Nenhum experimento com calibração ainda.")
        return
    escolha = st.selectbox("Experimento", [c["identificador"] for c in experimentos])
    corpo = next(c for c in experimentos if c["identificador"] == escolha)
    detalhe = estado_mod.detalhe_experimento(corpo["pasta"])
    calibracao = detalhe["calibracao"]
    if not calibracao:
        st.caption("Etapa de calibração não concluída.")
        return

    colunas = st.columns(4)
    colunas[0].metric("a (Platt)", calibracao.get("a_platt"))
    colunas[1].metric("b (Platt)", calibracao.get("b_platt"))
    colunas[2].metric("ECE antes", calibracao.get("ece_antes"))
    colunas[3].metric("ECE depois", calibracao.get("ece_depois"))

    st.subheader("Taxa base e aquecimento")
    st.caption(
        f"Taxa base do rótulo: {calibracao.get('taxa_base')}. No primeiro mês, a previsão "
        "ancora na taxa base e ganha peso do modelo conforme o histórico cresce."
    )

    st.subheader("Conjuntos conformes por grupo")
    limiares = calibracao.get("limiares_conformal", {})
    contagens = calibracao.get("linhas_por_grupo", {})
    cobertura = ((detalhe.get("avaliacao") or {}).get("conformal") or {}).get("cobertura_por_grupo", {})
    if limiares:
        import pandas as pd

        linhas = [
            {
                "grupo": grupo,
                "inclui 0 se p até": valor["negativo"],
                "inclui 1 se p a partir de": valor["positivo"],
                "linhas de calibração (0 / 1)": f"{contagens.get(grupo, {}).get('0', 0)} / "
                f"{contagens.get(grupo, {}).get('1', 0)}",
                "cobertura no teste (0 / 1)": f"{cobertura.get(grupo, {}).get('0', 'n/d')} / "
                f"{cobertura.get(grupo, {}).get('1', 'n/d')}",
            }
            for grupo, valor in limiares.items()
        ]
        st.dataframe(pd.DataFrame(linhas), use_container_width=True, hide_index=True)
        st.caption(
            "Grupos Mondrian por série e faixa de histórico (curto, medio, longo), com limiar por classe. "
            "O conjunto {1} indica risco no nível de confiança, {0} ausência de risco e {0, 1} indecisão. "
            "A cobertura é medida no teste; n/d indica classe com poucas linhas no grupo."
        )

    st.subheader("Curva de aprendizado")
    curva = calibracao.get("curva_aprendizado", [])
    if curva:
        dados = [{"faixa": ponto["faixa"], "auc": ponto["auc"], "linhas": ponto["linhas"]} for ponto in curva]
        st.dataframe(dados, use_container_width=True, hide_index=True)
    else:
        st.caption("Sem curva registrada.")
