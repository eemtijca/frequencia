# Contrato de integração com o FrequenciApp: mapa, cenários e mensagens.
"""Documento executável da fronteira entre o modelo e o aplicativo.

Define como cada feature do contrato mapeia para os dados do FrequenciApp,
quais cenários sintéticos o app deve rodar na ativação e o vocabulário de
mensagens aprovado. Não contém código do aplicativo: é orientação e contrato.
"""

from __future__ import annotations

import json
from pathlib import Path

from frequencia.features.catalogo import CATALOGO, dependentes_de_configuracao

MAPA_FONTES = {
    "app": {
        "faltas": "Tabela de faltas da chamada diária (F, FJ, S por dia e aula)",
        "saidas": "Registro de saídas antecipadas com momento e justificativa",
        "entradas": "Registro de entradas atrasadas",
        "turmas": "Séries, turmas e turma de origem do aluno",
        "calendario": "Feriados e período letivo da escola",
    },
    "mec": {
        "contexto": "Tabela contexto-mec.json do pacote (agregados por série)",
    },
}

MENSAGENS_APROVADAS = {
    "risco_alto": "Atenção sugerida: acompanhar este estudante na próxima semana.",
    "risco_medio": "Indicador moderado: vale observar nos próximos dias.",
    "risco_baixo": "Indicador tranquilo.",
    "sem_historico": "Sem histórico de chamadas para avaliar o risco.",
    "dados_insuficientes": "Histórico ainda curto: indicador em observação.",
    "modelo_desatualizado": "Modelo desatualizado: use o indicador com cautela até a atualização.",
    "fallback": "Indicador pelo modo de segurança de regras.",
}

PLANO_FEATURE_FLAG = [
    "FrequenciApp libera o indicador por flag de série, desligado por padrão.",
    "Primeiro mês em modo sombra: o modelo roda e nada é exibido (aquecimento).",
    "Após o período de sombra, a coordenação decide a ativação por série.",
    "Rollback por flag: desligar o indicador não exige nova release do app.",
]


def mapa_features() -> list[dict]:
    """Mapa de cada feature para a fonte de dados do FrequenciApp."""
    mapa = []
    for spec in CATALOGO:
        origem = MAPA_FONTES.get("app" if spec.origem in ("app", "calendario") else "mec", {})
        mapa.append(
            {
                "feature": spec.nome,
                "tipo": spec.tipo,
                "origem": spec.origem,
                "dependencia_config": spec.dependencia,
                "fonte": origem.get("contexto" if spec.origem == "mec" else spec.grupo, "app"),
                "padrao_quando_ausente": spec.padrao,
            }
        )
    return mapa


def dependentes_config() -> dict:
    """Features que exigem flags do FrequenciApp ligadas."""
    return dependentes_de_configuracao()


def cenarios_sinteticos(pasta_pacote: Path) -> list[dict]:
    """Lê os casos de teste do pacote para o app rodar na ativação."""
    alvo = Path(pasta_pacote) / "dados-teste.json"
    if not alvo.is_file():
        return []
    corpo = json.loads(alvo.read_text(encoding="utf-8"))
    return corpo.get("casos", [])


def gravar_contrato(destino: Path) -> Path:
    """Grava o contrato de integração completo em JSON."""
    corpo = {
        "versao": "1",
        "mapa_features": mapa_features(),
        "dependentes_config": dependentes_config(),
        "mensagens": MENSAGENS_APROVADAS,
        "plano_feature_flag": PLANO_FEATURE_FLAG,
        "fontes": MAPA_FONTES,
    }
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8") as saida:
        json.dump(corpo, saida, ensure_ascii=False, indent=2)
        saida.write("\n")
    return destino
