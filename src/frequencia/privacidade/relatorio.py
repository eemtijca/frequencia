# Pseudonimização determinística e relatório de risco de privacidade.
"""Salvaguardas de LGPD aplicadas sob autorização.

A pseudonimização substitui identificadores por códigos estáveis derivados de
hash com sal; o relatório de risco resume dados tratados, base legal e
recomendações para a escola controladora.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from frequencia.infra import caminhos, logs
from frequencia.privacidade import detector


def pseudonimizar_tabela(
    dados: pl.DataFrame, colunas: list[str], *, sal: str = "frequencia-sal-2026"
) -> pl.DataFrame:
    """Substitui colunas identificadoras por pseudônimos estáveis.

    O mesmo valor de entrada sempre gera o mesmo pseudônimo, o que mantém a
    junção entre tabelas sem expor o identificador original.
    """
    ajustes = []
    for coluna in colunas:
        if coluna not in dados.columns:
            continue

        def _trocar(valor: str | None) -> str | None:
            if valor is None:
                return None
            digestao = hashlib.sha256(f"{sal}:{valor}".encode()).hexdigest()
            return f"pseudo-{digestao[:12]}"

        ajustes.append(pl.col(coluna).map_elements(_trocar, return_dtype=pl.Utf8))
    return dados.with_columns(ajustes) if ajustes else dados


def gerar_relatorio_risco(tabelas: dict[str, pl.DataFrame], *, base_legal: str = "") -> dict:
    """Gera o relatório de risco de privacidade de um pacote de dados."""
    achados = detector.examinar_tabelas(tabelas)
    identificadores = detector.verificar_identificadores(tabelas)
    nivel = "baixo"
    if identificadores:
        nivel = "critico"
    elif achados:
        nivel = "medio"
    recomendacoes: list[str] = []
    if achados:
        recomendacoes.append(
            "Remover ou pseudonimizar os campos de texto com dados pessoais antes do treino."
        )
    if identificadores:
        recomendacoes.append(
            "Excluir colunas identificadoras diretas (CPF, telefone, e-mail, matrícula)."
        )
    if not base_legal:
        recomendacoes.append("Registrar a base legal do tratamento junto à escola controladora.")
    return {
        "gerado_em": datetime.now(UTC).isoformat(timespec="seconds"),
        "nivel": nivel,
        "base_legal": base_legal,
        "achados": achados,
        "identificadores_proibidos": identificadores,
        "recomendacoes": recomendacoes,
    }


def gravar_relatorio(relatorio: dict, nome: str = "relatorio-privacidade.json") -> Path:
    """Grava o relatório de privacidade em var/relatorios."""
    destino = caminhos.caminho("relatorios") / nome
    with destino.open("w", encoding="utf-8") as saida:
        json.dump(relatorio, saida, ensure_ascii=False, indent=2, sort_keys=True)
        saida.write("\n")
    logs.registrar("privacidade.relatorio", estagio="privacidade", nivel=relatorio["nivel"])
    return destino
