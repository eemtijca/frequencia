# Calendário letivo: bimestres, feriados e features cíclicas.
"""Derivações temporais compartilhadas pelo treino e pela inferência.

As funções recebem e devolvem valores simples (dias ISO e números), o que
permite espelhar a lógica em JavaScript no pacote de inferência.
"""

from __future__ import annotations

from datetime import date, timedelta

BIMESTRES = ((2, 4), (5, 6), (8, 9), (10, 12))
CAP_DIAS_FERIADO = 15


def mes_para_fase_bimestre(dia: date) -> tuple[int, float, int]:
    """Devolve (bimestre, fase decorrida de 0 a 1, dias restantes no bimestre)."""
    for indice, (inicio, fim) in enumerate(BIMESTRES, start=1):
        if inicio <= dia.month <= fim:
            primeiro = date(dia.year, inicio, 1)
            ultimo = date(dia.year, 12, 31) if fim == 12 else date(dia.year, fim + 1, 1) - timedelta(days=1)
            total = (ultimo - primeiro).days + 1
            decorridos = (dia - primeiro).days + 1
            fase = min(1.0, max(0.0, decorridos / max(total, 1)))
            return indice, round(fase, 4), max(0, (ultimo - dia).days)
    # Recesso de julho cai fora dos bimestres; usa o anterior encerrado.
    return 2, 1.0, 0


def distancias_feriado(dia: date, feriados: list[date]) -> tuple[float, float]:
    """Distância em dias até o feriado anterior e o próximo, com teto."""
    anterior = 365.0
    proximo = 365.0
    for feriado in feriados:
        delta = (dia - feriado).days
        if 0 <= delta < anterior:
            anterior = delta
        if 0 < -delta < proximo:
            proximo = -delta
    return (
        min(anterior, CAP_DIAS_FERIADO),
        min(proximo, CAP_DIAS_FERIADO),
    )


def ciclo_dia_semana(dia: date) -> tuple[float, float]:
    """Seno e cosseno do dia da semana (segunda 1 a sexta 5)."""
    import math

    posicao = min(max(dia.weekday() + 1, 1), 6)
    angulo = 2 * math.pi * posicao / 7
    return round(math.sin(angulo), 4), round(math.cos(angulo), 4)


def ciclo_mes(dia: date) -> tuple[float, float]:
    """Seno e cosseno do mês."""
    import math

    angulo = 2 * math.pi * (dia.month - 1) / 12
    return round(math.sin(angulo), 4), round(math.cos(angulo), 4)


def semana_do_mes(dia: date) -> int:
    """Índice da semana dentro do mês, de 1 a 5."""
    return min(5, (dia.day - 1) // 7 + 1)


def dias_uteis_entre(inicio: date, fim: date, feriados: set[date]) -> list[date]:
    """Dias letivos entre duas datas: seg a sex, sem feriados."""
    dias = []
    cursor = inicio
    while cursor <= fim:
        if cursor.weekday() < 5 and cursor not in feriados:
            dias.append(cursor)
        cursor += timedelta(days=1)
    return dias
