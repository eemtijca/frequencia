# Página de dados: fontes do MEC, importações, semente sintética e privacidade.
"""Camada de dados sob a ótica da interface."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from frequencia.web import estado as estado_mod
from frequencia.web import tarefas as tarefas_mod


def renderizar() -> None:
    """Renderiza fontes, importações e geração sintética."""
    st.title("Dados")
    st.caption("Fontes do MEC, importações registradas e semente sintética, sem dados pessoais.")

    st.subheader("Fontes do MEC documentadas")
    from frequencia.dados import mec

    fontes = mec.catalogo_fontes()
    st.dataframe(
        [
            {
                "id": fonte["id"],
                "nome": fonte["nome"],
                "órgão": fonte["orgao"],
                "granularidade": fonte["granularidade"],
                "uso": fonte["uso_no_frequencia"],
            }
            for fonte in fontes
        ],
        use_container_width=True,
        hide_index=True,
    )
    st.caption("Restrições: " + " ".join(mec.restricoes_de_uso()))

    st.subheader("Importações registradas")
    importacoes = estado_mod.importacoes()
    if importacoes:
        st.dataframe(
            [
                {
                    "identificador": corpo["identificador"],
                    "origem": corpo["origem"],
                    "licença": corpo["licenca"],
                    "hash": corpo["hash_pasta"][:12],
                    "linhas": sum(corpo["contagens"].values()),
                }
                for corpo in importacoes
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("Nenhuma importação registrada. Use a CLI dados importar.")

    st.subheader("Gerar dados sintéticos")
    colunas = st.columns(4)
    perfil = colunas[0].selectbox("Perfil", ["amostra", "fumaca", "padrao"], index=1)
    semente = colunas[1].number_input("Semente", min_value=1, value=20261018, step=1)
    ano = colunas[2].number_input("Ano letivo", min_value=2020, max_value=2100, value=2026)
    destino = colunas[3].text_input("Destino", value="")
    if st.button("Disparar geração em fundo", type="primary"):
        argumentos = [
            "dados",
            "gerar-sintetico",
            "--perfil",
            perfil,
            "--semente",
            str(int(semente)),
            "--ano",
            str(int(ano)),
        ]
        if destino:
            argumentos += ["--destino", destino]
        recibo = tarefas_mod.disparar(argumentos, rotulo=f"gerar sintético {perfil}")
        st.success(f"Tarefa {recibo['id']} disparada. Acompanhe na barra lateral.")

    st.subheader("Amostra sintética versionada no repositório")
    amostra = Path(__file__).resolve().parents[4] / "dados" / "sinteticos" / "amostra"
    if amostra.is_dir():
        arquivos = sorted(p.name for p in amostra.glob("*.csv"))
        st.caption(f"{len(arquivos)} tabelas em {amostra}")
        st.dataframe(arquivos, hide_index=True, use_container_width=True)
    else:
        st.caption("Amostra ainda não gerada.")
