# Catálogos do domínio: justificativas, liberadores e momentos de saída.
"""Códigos estáveis herdados do FrequenciApp.

O código é estável e o rótulo pode mudar; o pipeline treina sempre sobre o
código, nunca sobre o rótulo. Códigos raros são agrupados durante a
engenharia de features para evitar vazamento de inferência.
"""

from __future__ import annotations

# Catálogo inicial de justificativas, igual ao aplicativo de referência.
JUSTIFICATIVAS: tuple[tuple[str, str, bool], ...] = (
    # (codigo, rotulo, rara) - raras são agrupadas em OUTROS no treino
    ("D", "Doente", False),
    ("Dat", "Doente com atestado", False),
    ("LM", "Licença Maternidade", True),
    ("G", "Grávida", True),
    ("T", "Transporte", False),
    ("Vi", "Viagem", False),
    ("CM", "Consulta Médica", False),
    ("De", "Dentista", False),
    ("Lt", "Luto", True),
    ("O", "Outros", False),
    ("C", "Consulta", True),
    ("S", "Suspensão", True),
)

# Catálogo de quem libera as saídas antecipadas.
LIBERADORES: tuple[tuple[str, str], ...] = (
    ("S1", "Coordenação"),
    ("S2", "Direção"),
    ("S3", "Portaria"),
    ("S4", "Secretaria"),
)

# Momentos de saída antecipada para jornada de cinco aulas.
MOMENTOS_SAIDA: tuple[str, ...] = (
    "aula_1",
    "aula_2",
    "aula_3",
    "aula_4",
    "aula_5",
    "intervalo_1",
    "intervalo_2",
    "almoco",
)

CODIGOS_JUSTIFICATIVA = tuple(codigo for codigo, _, _ in JUSTIFICATIVAS)
CODIGOS_LIBERADOR = tuple(codigo for codigo, _ in LIBERADORES)
JUSTIFICATIVAS_RARAS = frozenset(codigo for codigo, _, rara in JUSTIFICATIVAS if rara)

MARCAS_VALIDAS = ("F", "FJ", "S", "P")  # marcas de um dia com chamada; vazia é ausência de chamada


def rotulo_justificativa(codigo: str) -> str:
    """Devolve o rótulo de exibição de um código de justificativa."""
    for codigo_catalogo, rotulo, _ in JUSTIFICATIVAS:
        if codigo_catalogo == codigo:
            return rotulo
    return "Outros"


def agrupar_rara(codigo: str | None) -> str | None:
    """Agrupa códigos raros em OUTROS e devolve o código estável."""
    if codigo is None:
        return None
    if codigo in JUSTIFICATIVAS_RARAS:
        return "OUTROS"
    return codigo
