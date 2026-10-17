# Detector de dados pessoais: regras próprias de PT-BR reforçadas pelo presidio.
"""Filtro de privacidade do fluxo de dados.

Combina dois motores: regras próprias de expressão regular para documentos e
contatos brasileiros, e o presidio-analyzer em modo padrão (sem modelo de
linguagem pesado, com motor NLP leve baseado no tokenizador do spaCy em
branco). Nomes de pessoas são detectados por heurística própria porque o
suporte do presidio ao português é limitado (ADR-009).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import polars as pl

CAMPOS_DE_TEXTO = ("nome", "observacao", "texto", "motivo", "justificativa_livre")

PADROES_BR = (
    ("cpf", re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")),
    ("cnpj", re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b")),
    ("telefone", re.compile(r"\(\d{2}\)\s?9?\d{4}-\d{4}")),
    ("telefone_alternativo", re.compile(r"\b9?\d{4}-\d{4}\b")),
    ("email", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b")),
    ("cep", re.compile(r"\b\d{5}-\d{3}\b")),
    ("rg", re.compile(r"\b\d{1,2}\.\d{3}\.\d{3}-[0-9Xx]\b")),
    ("data_nascimento", re.compile(r"\bnascido?\s+(?:em\s+)?\d{2}/\d{2}/\d{4}\b", re.I)),
)

SOBRENOMES_COMUNS = (
    "silva",
    "santos",
    "oliveira",
    "souza",
    "lima",
    "pereira",
    "costa",
    "almeida",
    "ferreira",
    "rodrigues",
    "gomes",
    "martins",
    "araujo",
    "barbosa",
    "ribeiro",
    "carvalho",
    "moreira",
    "cardoso",
    "teixeira",
    "correia",
    "monteiro",
    "nunes",
    "alves",
    "bezerro",
    "cavalcante",
    "mendes",
    "freitas",
    "melo",
    "duarte",
    "sampaio",
    "vasconcelos",
)

_PADRAO_NOME = re.compile(r"\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+\b")


@dataclass
class Achado:
    """Um achado de dado pessoal em campo de texto."""

    tabela: str
    coluna: str
    tipo: str
    ocorrencias: int
    exemplos: tuple[str, ...] = ()

    def para_dict(self) -> dict:
        return {
            "tabela": self.tabela,
            "coluna": self.coluna,
            "tipo": self.tipo,
            "ocorrencias": self.ocorrencias,
            "exemplos": list(self.exemplos[:3]),
        }


def _motor_presidio():
    """Cria o motor presidio em modo padrão; devolve None quando indisponível."""
    try:
        import spacy
        from presidio_analyzer import (
            AnalyzerEngine,
            Pattern,
            PatternRecognizer,
            RecognizerRegistry,
        )
        from presidio_analyzer.nlp_engine import NlpArtifacts, NlpEngine
    except ImportError:
        return None

    class MotorNlpLeve(NlpEngine):
        """Motor sem modelo treinado: só tokenizador local, sem download."""

        def __init__(self) -> None:
            self._nlp = spacy.blank("pt")

        def load(self) -> None:
            return None

        def is_loaded(self) -> bool:
            return True

        def get_supported_languages(self) -> list[str]:
            return ["pt"]

        def get_supported_entities(self) -> list[str]:
            return []

        def process_text(self, text: str, language: str):
            documento = self._nlp(text)
            return NlpArtifacts(
                entities=[],
                tokens=documento,
                tokens_indices=[t.idx for t in documento],
                lemmas=[t.lemma_ for t in documento],
                nlp_engine=self,
                language=language,
            )

        def process_batch(
            self,
            texts,
            language: str,
            batch_size: int = 1,
            n_process: int = 1,
            **kwargs,
        ):
            return [(texto, self.process_text(texto, language)) for texto in texts]

        def is_stopword(self, word: str, language: str) -> bool:
            return False

        def is_punct(self, word: str, language: str) -> bool:
            return False

    reconhecedores = []
    for tipo in ("cpf", "cnpj", "email", "telefone"):
        padrao_dict = dict(PADROES_BR)
        padrao = Pattern(name=f"{tipo}_br", regex=padrao_dict[tipo].pattern, score=0.85)
        reconhecedores.append(
            PatternRecognizer(
                supported_entity=f"BR_{tipo}".upper(),
                patterns=[padrao],
                supported_language="pt",
                name=f"{tipo} pt",
            )
        )
    registro = RecognizerRegistry(recognizers=reconhecedores, supported_languages=["pt"])
    return AnalyzerEngine(nlp_engine=MotorNlpLeve(), registry=registro, supported_languages=["pt"])


_MOTOR = None


def motor_presidio():
    """Instância única do motor presidio em modo padrão."""
    global _MOTOR
    if _MOTOR is None:
        _MOTOR = _motor_presidio()
    return _MOTOR


def examinar_texto(texto: str) -> list[tuple[str, str]]:
    """Examina um texto livre e devolve pares (tipo, trecho) encontrados."""
    if not texto:
        return []
    achados: list[tuple[str, str]] = []
    for tipo, padrao in PADROES_BR:
        for correspondencia in padrao.finditer(texto):
            achados.append((tipo, correspondencia.group(0)))
    for correspondencia in _PADRAO_NOME.finditer(texto):
        partes = correspondencia.group(0).split()
        if any(parte.lower() in SOBRENOMES_COMUNS for parte in partes):
            achados.append(("nome_pessoa", correspondencia.group(0)))
    return achados


def examinar_texto_presidio(texto: str) -> list[tuple[str, str]]:
    """Examina com o presidio em modo padrão; complementa as regras próprias."""
    motor = motor_presidio()
    if motor is None or not texto:
        return []
    try:
        resultados = motor.analyze(text=texto, language="pt")
    except Exception:
        return []
    return [(r.entity_type, texto[r.start : r.end]) for r in resultados]


def examinar_tabelas(tabelas: dict[str, pl.DataFrame], *, com_presidio: bool = False) -> list[dict]:
    """Varre os campos de texto das tabelas atrás de dados pessoais.

    Devolve a lista de achados; lista vazia significa pacote liberado. Os
    identificadores sintéticos (Estudante NNNN) não são dados pessoais.
    """
    achados: list[Achado] = []
    for nome_tabela, dados in tabelas.items():
        for coluna in dados.columns:
            if coluna not in CAMPOS_DE_TEXTO:
                continue
            valores = dados[coluna].drop_nulls().unique().to_list()
            contagens: dict[str, int] = {}
            exemplos: dict[str, list[str]] = {}
            for valor in valores:
                if not isinstance(valor, str):
                    continue
                texto = valor.strip()
                if not texto or "sintétic" in texto.lower():
                    continue
                pares = examinar_texto(texto)
                if com_presidio:
                    pares += examinar_texto_presidio(texto)
                for tipo, trecho in pares:
                    contagens[tipo] = contagens.get(tipo, 0) + 1
                    exemplos.setdefault(tipo, []).append(trecho)
            for tipo, quantidade in sorted(contagens.items()):
                achados.append(
                    Achado(
                        tabela=nome_tabela,
                        coluna=coluna,
                        tipo=tipo,
                        ocorrencias=quantidade,
                        exemplos=tuple(exemplos[tipo]),
                    )
                )
    return [achado.para_dict() for achado in achados]


def verificar_identificadores(tabelas: dict[str, pl.DataFrame]) -> list[dict]:
    """Confere que nenhuma coluna é identificadora direta proibida."""
    from frequencia.dados.esquemas import CAMPOS_PROIBIDOS

    problemas = []
    for nome_tabela, dados in tabelas.items():
        colunas = set(dados.columns)
        for proibida in CAMPOS_PROIBIDOS:
            if proibida in colunas:
                problemas.append(
                    {
                        "tabela": nome_tabela,
                        "coluna": proibida,
                        "tipo": "identificador_proibido",
                        "ocorrencias": dados.height,
                    }
                )
    return problemas
