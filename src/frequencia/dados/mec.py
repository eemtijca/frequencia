# Metadados das fontes do MEC: catálogo de datasets públicos de educação.
"""Guia de dados externos: Censo Escolar, SAEB, IDEB e indicadores.

O repositório guarda apenas metadados, esquemas e amostras sintéticas; os
microdados reais ficam fora do controle de versão, referenciados por hash
e manifesto no momento da importação.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from frequencia.infra import caminhos
from frequencia.infra.erros import ErroValidacao

FONTES_MEC: list[dict[str, str]] = [
    {
        "id": "censo-escolar",
        "nome": "Censo Escolar da Educação Básica",
        "orgao": "INEP",
        "url": "https://www.gov.br/inep/pt-br/areas-de-atuacao/pesquisas-estatisticas-e-indicadores/censo-escolar",
        "licenca": "Dados abertos (Licença Internacional CC BY 4.0 declarada pelo INEP)",
        "granularidade": "Escola, turma, aluno (agregado nos indicadores)",
        "periodicidade": "Anual",
        "campos_de_interesse": "abandono, reprovação, distorção idade-série, infraestrutura, docentes",
        "uso_no_frequencia": "Contexto agregado por série e escola para o modelo de risco",
    },
    {
        "id": "saeb",
        "nome": "Sistema de Avaliação da Educação Básica",
        "orgao": "INEP",
        "url": "https://www.gov.br/inep/pt-br/areas-de-atuacao/pesquisas-estatisticas-e-indicadores/saeb",
        "licenca": "Dados abertos",
        "granularidade": "Escola e série de avaliação (5º e 9º ano, 3ª e 4ª série)",
        "periodicidade": "Bienal",
        "campos_de_interesse": "proficiência média por escola",
        "uso_no_frequencia": "Variável de contexto opcional, apenas em agregado",
    },
    {
        "id": "ideb",
        "nome": "Índice de Desenvolvimento da Educação Básica",
        "orgao": "INEP",
        "url": "https://www.gov.br/inep/pt-br/areas-de-atuacao/pesquisas-estatisticas-e-indicadores/indices/ideb",
        "licenca": "Dados abertos",
        "granularidade": "Escola, rede, município, estado",
        "periodicidade": "Bienal",
        "campos_de_interesse": "ideb, metas de melhoria",
        "uso_no_frequencia": "Contexto agregado por série no catálogo de features",
    },
    {
        "id": "indicadores-rendimento",
        "nome": "Indicadores de rendimento escolar",
        "orgao": "INEP",
        "url": "https://www.gov.br/inep/pt-br/areas-de-atuacao/pesquisas-estatisticas-e-indicadores/indicadores-educacionais",
        "licenca": "Dados abertos",
        "granularidade": "Escola e série",
        "periodicidade": "Anual",
        "campos_de_interesse": "taxa de abandono, aprovação, reprovação",
        "uso_no_frequencia": "Agregados por série no modelo de risco",
    },
]

_RESTRICOES = (
    "Nenhum microdado real entra no repositório; apenas metadados e amostras sintéticas.",
    "Importações registradas com data, origem, licença e hash antes do uso em treino.",
    "Agregação por escola e série: nunca usar linha por aluno do MEC como feature.",
)


def catalogo_fontes() -> list[dict[str, str]]:
    """Devolve o catálogo de fontes externas documentadas."""
    return FONTES_MEC


def fonte_por_identificador(identificador: str) -> dict[str, str]:
    """Localiza uma fonte do catálogo pelo identificador curto."""
    for fonte in FONTES_MEC:
        if fonte["id"] == identificador:
            return fonte
    identificadores = ", ".join(fonte["id"] for fonte in FONTES_MEC)
    msg = f"Fonte desconhecida: {identificador}. Disponíveis: {identificadores}."
    raise ErroValidacao(msg)


def restricoes_de_uso() -> tuple[str, ...]:
    """Regras inegociáveis de uso dos dados do MEC."""
    return _RESTRICOES


def gravar_catalogo_local() -> Path:
    """Espelha o catálogo de fontes em JSON dentro do workspace."""
    import json

    destino = caminhos.caminho("dados") / "mec" / "fontes.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    corpo = {"fontes": FONTES_MEC, "restricoes": list(_RESTRICOES)}
    with destino.open("w", encoding="utf-8") as saida:
        json.dump(corpo, saida, ensure_ascii=False, indent=2)
        saida.write("\n")
    return destino


def amostra_sintetica_contexto() -> dict[str, Any]:
    """Amostra sintética do formato esperado do contexto do MEC."""
    return {
        "serie_id": "ser_alfa_1",
        "taxa_abandono_historica": 0.042,
        "taxa_reprovacao": 0.08,
        "distorcao_idade_serie": 0.18,
        "ideb": 4.9,
    }
