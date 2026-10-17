# Página de datasets: construção, divisão temporal e verificação de vazamento.
"""Datasets de treino na interface, com disparo em fundo."""

from __future__ import annotations

import streamlit as st

from frequencia.web import estado as estado_mod
from frequencia.web import tarefas as tarefas_mod


def renderizar() -> None:
    """Renderiza datasets construídos e o formulário de construção."""
    st.title("Datasets de treino")
    st.caption("Unidade aluno-dia, rótulo futuro e separação temporal estrita.")

    st.subheader("Construir dataset")
    importacoes = estado_mod.importacoes()
    origens = [corpo["pasta"] for corpo in importacoes]
    from pathlib import Path

    amostra = Path(__file__).resolve().parents[4] / "dados" / "sinteticos" / "amostra"
    if amostra.is_dir():
        origens.append(str(amostra))
    pasta_dados = st.text_input("Pasta do pacote de dados", value=origens[0] if origens else "")
    colunas = st.columns(4)
    horizonte = colunas[0].number_input("Horizonte (dias letivos)", 1, 30, 7)
    limiar = colunas[1].number_input("Faltas para rótulo 1", 1, 10, 2)
    minimo = colunas[2].number_input("Histórico mínimo", 1, 60, 10)
    ponto = colunas[3].selectbox("Ponto no tempo", ["estrito", "atual"])
    versao = st.text_input("Identificador do dataset", value="web-v1")
    if st.button("Construir em fundo", type="primary"):
        if not pasta_dados:
            st.error("Informe a pasta do pacote de dados.")
        else:
            recibo = tarefas_mod.disparar(
                [
                    "datasets",
                    "construir",
                    pasta_dados,
                    "--horizonte",
                    str(int(horizonte)),
                    "--limiar-rotulo",
                    str(int(limiar)),
                    "--min-historico",
                    str(int(minimo)),
                    "--ponto-no-tempo",
                    ponto,
                    "--versao",
                    versao,
                ],
                rotulo=f"construir dataset {versao}",
            )
            st.success(f"Tarefa {recibo['id']} disparada.")

    st.subheader("Datasets construídos")
    datasets = estado_mod.datasets()
    if not datasets:
        st.caption("Nenhum dataset no workspace ainda.")
        return
    st.dataframe(datasets, use_container_width=True, hide_index=True)

    escolha = st.selectbox("Dataset para detalhar", [c["identificador"] for c in datasets])
    alvo = next(c for c in datasets if c["identificador"] == escolha)

    from frequencia.web.estado import ler_json

    meta = ler_json(Path(alvo["pasta"]) / "meta.json")
    if meta:
        colunas2 = st.columns(3)
        colunas2[0].metric("Linhas", meta["resumo"]["linhas"])
        colunas2[1].metric("Taxa do rótulo", meta["resumo"]["taxa_rotulo"])
        colunas2[2].metric("Dias de referência", meta["resumo"]["dias_referencia"])
        st.json(meta["resumo"]["fronteiras"], expanded=False)
        if st.button("Verificar ausência de futuro (amostra)"):
            recibo = tarefas_mod.disparar(
                ["datasets", "validar-ausencia-futuro", alvo["pasta"]],
                rotulo="verificar vazamento",
            )
            st.success(f"Verificação disparada: {recibo['id']}.")
