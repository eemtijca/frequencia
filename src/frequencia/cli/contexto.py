# Modos transversais da CLI: seco, JSON, detalhado, silencioso e perfil.
"""Contexto de execução compartilhado por todos os comandos.

A CLI é a interface primária de engenharia: saída legível para humanos,
saída estruturada para scripts (--json), modo seco para ensaio, idempotência
por padrão e força apenas com justificativa registrada em auditoria.
"""

from __future__ import annotations

import json as json_mod
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from frequencia.infra import estado as estado_infra
from frequencia.infra.erros import ExcecaoFrequencia, traduzir_erro


@dataclass
class Contexto:
    """Bandeiras transversais resolvidas na partida da CLI."""

    json: bool = False
    seco: bool = False
    detalhado: bool = False
    silencioso: bool = False
    perfil: str = "padrao"
    forca: bool = False
    justificativa: str = ""
    ator: str = "cli"
    papel: str = "engenheiro"

    def exigir_justificativa(self) -> None:
        """Força exige justificativa registrada; recusa sem ela."""
        if self.forca and not self.justificativa:
            msg = "Use --forca apenas com --justificativa informada."
            raise ExcecaoFrequencia(msg, dica="Explique o motivo da reexecução completa.")

    def auditar(self, acao: str, alvo: str = "", **detalhes: Any) -> None:
        """Registra a ação na trilha de auditoria com papel e ator."""
        estado_infra.registrar_auditoria(
            acao,
            alvo=alvo,
            ator=self.ator,
            papel=self.papel,
            **detalhes,
        )


def emitir(contexto: Contexto | None, resultado: Any, *, titulo: str = "") -> None:
    """Emite o resultado para humano ou para script, conforme o modo.

    A bandeira --json vence o silêncio: saída estruturada é o contrato com
    scripts, e o silêncio cala apenas a saída humana.
    """
    if contexto is not None and contexto.json:
        corpo = _para_json(resultado)
        print(json_mod.dumps(corpo, ensure_ascii=False, default=str, sort_keys=True))
        return
    if contexto is not None and contexto.silencioso:
        return
    _imprimir_humano(resultado, titulo=titulo)


def _para_json(valor: Any) -> Any:
    """Converte estruturas do motor em JSON puro."""
    if hasattr(valor, "para_dict"):
        return _para_json(valor.para_dict())
    if isinstance(valor, dict):
        return {chave: _para_json(corpo) for chave, corpo in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_para_json(item) for item in valor]
    if isinstance(valor, Path):
        return str(valor)
    return valor


def _imprimir_humano(valor: Any, *, titulo: str) -> None:
    """Impressão legível: tabelas simples para listas de dicionários."""
    if titulo:
        print(titulo)
    if isinstance(valor, list) and valor and isinstance(valor[0], dict):
        chaves = list(valor[0].keys())
        larguras = {
            chave: max(len(str(chave)), *(len(str(linha.get(chave, ""))) for linha in valor))
            for chave in chaves
        }
        cabecalho = " | ".join(str(chave).ljust(larguras[chave]) for chave in chaves)
        print(cabecalho)
        print("-" * len(cabecalho))
        for linha in valor:
            print(" | ".join(str(linha.get(chave, "")).ljust(larguras[chave]) for chave in chaves))
        return
    if isinstance(valor, dict):
        for chave, corpo in valor.items():
            if isinstance(corpo, (dict, list)):
                print(f"{chave}:")
                _imprimir_humano(corpo, titulo="")
            else:
                print(f"{chave}: {corpo}")
        return
    if isinstance(valor, list):
        for item in valor:
            _imprimir_humano(item, titulo="")
        return
    print(valor)


def falha(contexto: Contexto | None, exc: Exception) -> None:
    """Converte exceção em mensagem curta e código de saída 1."""
    if contexto is not None and contexto.detalhado:
        import traceback

        traceback.print_exception(type(exc), exc, exc.__traceback__)
    mensagem = traduzir_erro(exc)
    if contexto is not None and contexto.json:
        print(
            json_mod.dumps(
                {"erro": mensagem, "tipo": type(exc).__name__},
                ensure_ascii=False,
            )
        )
    else:
        print(f"Erro: {mensagem}", file=sys.stderr)
    raise SystemExit(1) from exc
