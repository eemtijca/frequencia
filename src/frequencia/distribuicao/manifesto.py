# Contrato do manifesto de modelo: o documento lido pelo FrequenciApp.
"""Manifesto versionado de compatibilidade e configuração do pacote.

O app nunca adivinha compatibilidade: lê o manifesto e decide. O manifesto
declara versões, hash, tamanho, validade, perfis de dados suportados,
contrato de features com padrões, parâmetros de calibração e conformal,
limiares, mensagens e limitações. A validação confere todos os campos
obrigatórios e os tipos.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any

from frequencia.infra.erros import ErroContrato

VERSAO_FORMATO = "1"
# Versão 2: a saída troca intervalo_conformal por conjunto_conformal (ADR-021).
VERSAO_CONTRATO = "2"

CAMPOS_OBRIGATORIOS = (
    "versao_manifesto",
    "identificador",
    "versao_modelo",
    "versao_contrato",
    "versao_catalogo_features",
    "criado_em",
    "min_app_versao",
    "runtime_alvo",
    "hash_modelo",
    "tamanho_bytes",
    "validade_ate",
    "dataset",
    "contrato",
    "calibracao",
    "conformal",
    "limiares_alerta",
    "confianca",
    "mensagens",
    "perfis_dados",
    "metricas",
    "limitacoes",
    "cartao",
    "fallback",
    "licenca",
    "arquivos",
    "identificacao",
)

RUNTIMES_ACEITOS = ("js-m2cgen",)

PERFIS_BASE = (
    {
        "frequencia_por_aula": True,
        "saida_antecipada": True,
        "origem_na_chamada": True,
        "confiabilidade": "plena",
    },
    {
        "frequencia_por_aula": False,
        "saida_antecipada": False,
        "origem_na_chamada": False,
        "confiabilidade": "reduzida",
    },
)

LICENCA = "MIT"


def montar(
    *,
    identificador: str,
    versao_modelo: str,
    criado_em: str,
    dataset: dict,
    contrato: dict,
    calibracao: dict,
    conformal: dict,
    metricas: dict,
    limitacoes: list[str],
    hash_modelo: str,
    tamanho_bytes: int,
    arquivos: dict[str, str],
    min_app_versao: str = "1.4.0",
    validade_dias: int = 180,
    versao_contrato: str = VERSAO_CONTRATO,
    versao_catalogo_features: str = "1.0.0",
    perfis: list[dict] | None = None,
    mensagens: dict[str, str] | None = None,
    limiares_alerta: dict | None = None,
    confianca: dict | None = None,
) -> dict:
    """Monta o manifesto completo de um pacote pronto para publicação."""
    from frequencia.features import confianca as confianca_mod

    validade = (date.fromisoformat(criado_em[:10]) + timedelta(days=validade_dias)).isoformat()
    corpo: dict[str, Any] = {
        "versao_manifesto": VERSAO_FORMATO,
        "identificador": identificador,
        "versao_modelo": versao_modelo,
        "versao_contrato": versao_contrato,
        "versao_catalogo_features": versao_catalogo_features,
        "criado_em": criado_em,
        "min_app_versao": min_app_versao,
        "runtime_alvo": "js-m2cgen",
        "hash_modelo": hash_modelo,
        "tamanho_bytes": tamanho_bytes,
        "validade_ate": validade,
        "dataset": dataset,
        "contrato": contrato,
        "calibracao": calibracao,
        "conformal": conformal,
        "limiares_alerta": limiares_alerta or dict(confianca_mod.LIMIARES_ALERTA),
        "confianca": confianca
        or {
            "aquecimento_dias": confianca_mod.LIMIARES_CONFIANCA["aquecimento_dias"],
            "validade_modelo_dias": confianca_mod.LIMIARES_CONFIANCA["validade_modelo_dias"],
        },
        "mensagens": mensagens or dict(confianca_mod.VOCABULARIO_MENSAGENS),
        "perfis_dados": perfis or [dict(perfil) for perfil in PERFIS_BASE],
        "metricas": metricas,
        "limitacoes": limitacoes,
        "cartao": "modelo-cartao.md",
        "fallback": "fallback.js",
        "licenca": LICENCA,
        "arquivos": arquivos,
        "identificacao": {
            "identificador": identificador,
            "versao_modelo": versao_modelo,
        },
    }
    validar(corpo)
    return corpo


def validar(manifesto: dict) -> None:
    """Confere campos obrigatórios, formatos e consistência interna."""
    ausentes = [campo for campo in CAMPOS_OBRIGATORIOS if campo not in manifesto]
    if ausentes:
        msg = (
            f"Manifesto incompleto. Campos ausentes: {', '.join(ausentes)}. "
            "Regenere o pacote com a CLI de empacotamento."
        )
        raise ErroContrato(msg)
    if manifesto["runtime_alvo"] not in RUNTIMES_ACEITOS:
        msg = f"Runtime alvo não suportado: {manifesto['runtime_alvo']}. Esperado um de {RUNTIMES_ACEITOS}."
        raise ErroContrato(msg)
    contrato = manifesto["contrato"]
    for campo in ("features", "padroes", "tipos"):
        if campo not in contrato:
            msg = f"Contrato de features sem o campo {campo}."
            raise ErroContrato(msg)
    if len(contrato["features"]) != len(contrato["padroes"]):
        msg = "Contrato com número diferente de features e padrões."
        raise ErroContrato(msg)
    for campo in ("a_platt", "b_platt", "taxa_base"):
        if campo not in manifesto["calibracao"]:
            msg = f"Calibração sem o parâmetro {campo}."
            raise ErroContrato(msg)
    if "limiares" not in manifesto["conformal"]:
        msg = "Conformal sem os limiares dos conjuntos por grupo."
        raise ErroContrato(msg)
    for chave in ("entrada", "saida", "dias_consecutivos_entrada"):
        if chave not in manifesto["limiares_alerta"]:
            msg = f"Limiares de alerta sem a chave {chave}."
            raise ErroContrato(msg)
    try:
        date.fromisoformat(manifesto["validade_ate"])
    except ValueError as exc:
        msg = f"Validade com formato inválido: {manifesto['validade_ate']}."
        raise ErroContrato(msg) from exc


def gravar(manifesto: dict, destino) -> None:
    """Grava o manifesto em JSON com ordenação estável."""
    from pathlib import Path

    alvo = Path(destino)
    alvo.parent.mkdir(parents=True, exist_ok=True)
    with alvo.open("w", encoding="utf-8") as saida:
        json.dump(manifesto, saida, ensure_ascii=False, indent=2, sort_keys=True)
        saida.write("\n")


def carregar(origem) -> dict:
    """Lê e valida um manifesto gravado."""
    from pathlib import Path

    alvo = Path(origem)
    if not alvo.is_file():
        msg = f"Manifesto não encontrado: {alvo}."
        raise ErroContrato(msg)
    corpo = json.loads(alvo.read_text(encoding="utf-8"))
    validar(corpo)
    return corpo
