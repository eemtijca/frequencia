# Página de features: catálogo, dependências e distribuição.
"""Contrato de features na interface."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from frequencia.web import estado as estado_mod


def renderizar() -> None:
    """Renderiza catálogo e distribuições."""
    st.title("Features")
    st.caption("Catálogo versionado tratado como contrato entre treino e inferência.")

    from frequencia.features.catalogo import (
        VERSAO_CATALOGO,
        catalogo_por_grupo,
        dependentes_de_configuracao,
        validar_contrato,
    )

    veredito = validar_contrato()
    colunas = st.columns(3)
    colunas[0].metric("Versão do catálogo", VERSAO_CATALOGO)
    colunas[1].metric("Features", veredito["total"])
    colunas[2].metric("Grupos", len(veredito["grupos"]))

    st.subheader("Catálogo")
    grupos = catalogo_por_grupo()
    escolha = st.selectbox("Grupo", list(grupos.keys()))
    specs = grupos[escolha]
    st.dataframe(
        [
            {
                "nome": spec.nome,
                "amigável": spec.nome_amigavel,
                "tipo": spec.tipo,
                "janela": spec.janela,
                "origem": spec.origem,
                "padrão": spec.padrao,
                "dependência": spec.dependencia or "",
            }
            for spec in specs
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Dependência das flags do FrequenciApp")
    mapa = dependentes_de_configuracao()
    for flag, nomes in mapa.items():
        st.markdown(f"- **{flag}**: {', '.join(nomes)}")

    st.subheader("Distribuição em um dataset")
    datasets = estado_mod.datasets()
    if not datasets:
        st.caption("Construa um dataset para ver distribuições.")
        return
    escolha_dataset = st.selectbox("Dataset", [corpo["identificador"] for corpo in datasets])
    if st.button("Resumir distribuição"):
        import polars as pl

        pasta = next(c for c in datasets if c["identificador"] == escolha_dataset)["pasta"]
        dados = pl.read_parquet(Path(pasta) / "dataset.parquet")
        resumo = dados.describe()
        st.dataframe(resumo, use_container_width=True)
        from frequencia.infra import caminhos

        destino = caminhos.caminho("relatorios") / "distribuicao.csv"
        resumo.write_csv(destino)
        st.caption(f"Resumo gravado em {destino}")
