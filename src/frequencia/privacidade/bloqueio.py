# Portão de privacidade: bloqueia datasets não aprovados antes do treino.
"""Etapa obrigatória do pipeline antes de qualquer treinamento.

O portão verifica a presença de dados pessoais, identificadores proibidos e
a base legal declarada. Dataset reprovado não entra no fluxo de treino, em
nenhuma circunstância (princípio 1 do ecossistema).
"""

from __future__ import annotations

from pathlib import Path

from frequencia.dados import sintetico
from frequencia.infra.erros import ErroPrivacidade
from frequencia.privacidade import detector


def validar_entrada_treino(pasta: Path, *, exigir_base_legal: bool = False) -> dict:
    """Executa o portão de privacidade sobre um pacote de dados.

    Devolve o veredito com os achados; lança ErroPrivacidade quando o pacote
    não pode alimentar o treino.
    """
    pacote = sintetico.carregar_pacote(pasta)
    achados = detector.examinar_tabelas(pacote["tabelas"])
    identificadores = detector.verificar_identificadores(pacote["tabelas"])
    meta = pacote.get("meta", {})
    base_legal = meta.get("base_legal", "")

    problemas: list[str] = []
    if achados:
        detalhe = ", ".join(f"{a['tabela']}.{a['coluna']}({a['tipo']})" for a in achados)
        problemas.append(f"Dados pessoais detectados: {detalhe}.")
    if identificadores:
        detalhe = ", ".join(f"{i['tabela']}.{i['coluna']}" for i in identificadores)
        problemas.append(f"Identificadores proibidos: {detalhe}.")
    if exigir_base_legal and not base_legal:
        problemas.append("Base legal ausente no manifesto do pacote.")

    if problemas:
        msg = "Pacote bloqueado pelo portão de privacidade. " + " ".join(problemas)
        raise ErroPrivacidade(
            msg,
            dica="Corrija os dados ou registre a base legal antes do treinamento.",
        )
    return {
        "liberado": True,
        "pasta": str(pasta),
        "contagens": pacote["contagens"],
        "achados": achados,
        "identificadores": identificadores,
        "base_legal": base_legal,
    }
