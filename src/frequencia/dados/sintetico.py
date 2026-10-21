# Gerador de dados sintéticos: um ano letivo simulado, sem dados pessoais.
"""Simulação estatisticamente coerente com o domínio do FrequenciApp.

Estrutura relacional (series, turmas, alunos, frequências, faltas, saídas,
entradas, feriados, contexto MEC) com sazonalidade escolar, transferências,
perfis de recursos por escola, correções retroativas de chamada e verdade
oculta por aluno (propensão latente que dirige o comportamento simulado).

O gerador é determinístico: mesma semente, mesmos dados. Nenhum dado pessoal
real entra em qualquer artefato produzido aqui.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import TypedDict

import numpy as np

from frequencia.infra import hash as hash_infra
from frequencia.infra import logs
from frequencia.infra.erros import ErroValidacao


class VolumePerfil(TypedDict):
    """Parâmetros de volume de um perfil de geração sintética."""

    escolas: int
    series_por_escola: int
    turmas_por_serie: int
    alunos_por_turma: int
    inicio: str
    fim: str
    aulas_por_dia: int


PERFIS_VOLUME: dict[str, VolumePerfil] = {
    "amostra": {
        "escolas": 1,
        "series_por_escola": 2,
        "turmas_por_serie": 1,
        "alunos_por_turma": 15,
        "inicio": "02-02",
        "fim": "03-31",
        "aulas_por_dia": 4,
    },
    "fumaca": {
        "escolas": 2,
        "series_por_escola": 2,
        "turmas_por_serie": 1,
        "alunos_por_turma": 25,
        "inicio": "02-02",
        "fim": "06-30",
        "aulas_por_dia": 5,
    },
    "padrao": {
        "escolas": 2,
        "series_por_escola": 3,
        "turmas_por_serie": 3,
        "alunos_por_turma": 40,
        "inicio": "02-02",
        "fim": "12-18",
        "aulas_por_dia": 5,
    },
}

NOMES_SERIES = ("1º ano", "2º ano", "3º ano")
LETRAS_TURMA = ("A", "B", "C")

# Perfis de recursos por escola (chamada por aula, saída antecipada, origem).
PERFIS_ESCOLA = {
    "alfa": (True, True, True),
    "beta": (False, False, False),
    "gama": (True, False, True),
}

FATOR_DIA_SEMANA = {0: 1.35, 1: 1.0, 2: 0.95, 3: 1.0, 4: 1.25}
FATOR_MES = {
    2: 1.0,
    3: 1.0,
    4: 1.05,
    5: 1.10,
    6: 1.20,
    7: 1.25,
    8: 1.20,
    9: 1.05,
    10: 1.0,
    11: 1.10,
    12: 1.15,
}

# Feriados nacionais dentro do ano letivo, com datas aproximadas para 2026.
FERIADOS_ANO = (
    ("02-16", "Carnaval"),
    ("02-17", "Carnaval"),
    ("04-03", "Sexta-feira da Paixão"),
    ("04-21", "Tiradentes"),
    ("05-01", "Dia do Trabalho"),
    ("06-04", "Corpus Christi"),
    ("09-07", "Independência"),
    ("10-12", "Nossa Senhora Aparecida"),
    ("11-02", "Finados"),
    ("11-15", "Proclamação da República"),
    ("11-20", "Dia de Zumbi"),
)
RECESSO_JULHO = (7, 1, 7, 31)

MOTIVOS_JUSTIFICATIVA_PESO = (
    ("Dat", 30),
    ("D", 24),
    ("CM", 12),
    ("De", 8),
    ("T", 10),
    ("Vi", 5),
    ("Lt", 3),
    ("O", 4),
    ("LM", 2),
    ("C", 2),
    ("G", 1),
    ("S", 1),
)
MOMENTOS_SAIDA_PESO = (
    ("aula_3", 22),
    ("aula_4", 18),
    ("aula_5", 12),
    ("intervalo_1", 10),
    ("intervalo_2", 14),
    ("almoco", 24),
)
HORARIO_POR_MOMENTO = {
    "aula_1": "07:25",
    "aula_2": "08:15",
    "aula_3": "09:15",
    "aula_4": "10:25",
    "aula_5": "11:15",
    "intervalo_1": "09:00",
    "intervalo_2": "10:10",
    "almoco": "12:40",
}
LIBERADOR_PESO = (("S1", 45), ("S2", 25), ("S3", 20), ("S4", 10))
MOMENTOS_ENTRADA_PESO = (("aula_1", 30), ("aula_2", 30), ("pausa", 40))

PROBABILIDADE_TRANSFERENCIA = 0.05
PROBABILIDADE_DESISTENCIA = 0.025
# A desistência acompanha a propensão a faltar (risco relativo proporcional,
# com média da população perto de PROBABILIDADE_DESISTENCIA) e é precedida
# por escalada de faltas, como nos sistemas de alerta precoce de abandono.
PROPENSAO_MEDIA = 0.05
DIAS_ESCALADA_DESISTENCIA = 10
FATOR_ESCALADA_DESISTENCIA = 2.5
PROBABILIDADE_ALUNO_NOVO = 0.05
PROBABILIDADE_CHAMADA_TARDIA = 0.05
PROBABILIDADE_JUSTIFICATIVA_TARDIA = 0.08
PROBABILIDADE_FALTA_REMOVIDA = 0.03
PROPORCAO_CRONICA = 0.08
LIMITE_ANO = 2020, 2100


def chance_desistencia(propensao: float) -> float:
    """Probabilidade de desistir no ano, proporcional à propensão a faltar."""
    return min(0.5, PROBABILIDADE_DESISTENCIA * propensao / PROPENSAO_MEDIA)


@dataclass
class ConfigSintetico:
    """Parâmetros declarativos da geração sintética."""

    semente: int = 20261018
    perfil: str = "fumaca"
    ano: int = 2026
    alunos_por_turma: int | None = None
    destino: Path | None = None
    detalhes: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.perfil not in PERFIS_VOLUME:
            msg = f"Perfil de volume desconhecido: {self.perfil}. Use um de {sorted(PERFIS_VOLUME)}."
            raise ErroValidacao(msg)
        if not (LIMITE_ANO[0] <= self.ano <= LIMITE_ANO[1]):
            msg = f"Ano fora da faixa aceita ({LIMITE_ANO[0]} a {LIMITE_ANO[1]})."
            raise ErroValidacao(msg)


def _escolher_ponderado(opcoes: tuple[tuple[str, int], ...], sorteio: float) -> str:
    """Escolhe uma opção por peso acumulado; sorteio em [0, 1)."""
    total = sum(peso for _, peso in opcoes)
    alvo = sorteio * total
    acumulado = 0
    for rotulo, peso in opcoes:
        acumulado += peso
        if alvo <= acumulado:
            return rotulo
    return opcoes[-1][0]


def calendario_letivo(ano: int, inicio: str, fim: str) -> list[date]:
    """Devolve os dias letivos: seg a sex, sem feriados e sem recesso de julho."""
    mes_ini, dia_ini = (int(parte) for parte in inicio.split("-"))
    mes_fim, dia_fim = (int(parte) for parte in fim.split("-"))
    data_inicial = date(ano, mes_ini, dia_ini)
    data_final = date(ano, mes_fim, dia_fim)
    feriados = {
        date(ano, int(mes_dia.split("-")[0]), int(mes_dia.split("-")[1])) for mes_dia, _ in FERIADOS_ANO
    }
    dias: list[date] = []
    cursor = data_inicial
    while cursor <= data_final:
        em_recesso = cursor.month == RECESSO_JULHO[0] and RECESSO_JULHO[1] <= cursor.day <= RECESSO_JULHO[3]
        if cursor.weekday() < 5 and cursor not in feriados and not em_recesso:
            dias.append(cursor)
        cursor += timedelta(days=1)
    return dias


def _horarios_padrao(quantidade: int) -> list[tuple[str, str]]:
    """Grade padrão de aulas por dia para uma turma."""
    base = [
        ("07:00", "07:50"),
        ("07:50", "08:40"),
        ("08:40", "09:30"),
        ("09:50", "10:40"),
        ("10:40", "11:30"),
    ]
    return base[:quantidade]


def gerar(
    config: ConfigSintetico,
    *,
    detalhado: bool = False,
) -> dict:
    """Gera o pacote completo de dados sintéticos e grava em CSV.

    Devolve um dicionário com os dados em memória (polars DataFrame por
    tabela), a verdade oculta e os metadados da execução.
    """
    import polars as pl

    volume = PERFIS_VOLUME[config.perfil].copy()
    if config.alunos_por_turma is not None:
        volume["alunos_por_turma"] = config.alunos_por_turma
    rng = np.random.default_rng(config.semente)
    dias = calendario_letivo(config.ano, volume["inicio"], volume["fim"])
    if not dias:
        msg = "O período informado não contém dias letivos. Ajuste início e fim."
        raise ErroValidacao(msg)

    escolas_rows: list[dict] = []
    series_rows: list[dict] = []
    turmas_rows: list[dict] = []
    horarios_rows: list[dict] = []
    alunos_rows: list[dict] = []
    frequencias_rows: list[dict] = []
    faltas_rows: list[dict] = []
    saidas_rows: list[dict] = []
    entradas_rows: list[dict] = []
    feriados_rows = [
        {"dia": f"{config.ano}-{mes_dia}", "nome": nome, "origem": "API"}
        for mes_dia, nome in FERIADOS_ANO
        if date(config.ano, int(mes_dia.split("-")[0]), int(mes_dia.split("-")[1])) <= dias[-1]
    ]
    contexto_rows: list[dict] = []
    verdade_rows: list[dict] = []

    nome_escolas = list(PERFIS_ESCOLA)[: volume["escolas"]]
    mapa_aulas_por_turma: dict[str, list[str]] = {}
    chamadas_por_turma_dia: dict[tuple[str, str], dict] = {}
    sequencia_aluno = 0

    for nome_escola in nome_escolas:
        sufixo = nome_escola
        escola_id = f"escola_{sufixo}"
        por_aula, com_saidas, com_origem = PERFIS_ESCOLA[nome_escola]
        escolas_rows.append(
            {
                "escola_id": escola_id,
                "nome": f"Escola {sufixo.capitalize()} (sintética)",
                "frequencia_por_aula": por_aula,
                "saida_antecipada": com_saidas,
                "origem_na_chamada": com_origem,
            }
        )
        aulas_por_dia = volume["aulas_por_dia"] if por_aula else 1

        for indice_serie in range(volume["series_por_escola"]):
            nome_serie = NOMES_SERIES[indice_serie]
            serie_id = f"ser_{sufixo}_{indice_serie + 1}"
            series_rows.append(
                {
                    "serie_id": serie_id,
                    "escola_id": escola_id,
                    "nome": nome_serie,
                    "ordem": indice_serie + 1,
                }
            )
            contexto_rows.append(
                {
                    "serie_id": serie_id,
                    "taxa_abandono_historica": round(float(rng.uniform(0.01, 0.12)), 4),
                    "taxa_reprovacao": round(float(rng.uniform(0.02, 0.20)), 4),
                    "distorcao_idade_serie": round(float(rng.uniform(0.05, 0.35)), 4),
                    "ideb": round(float(rng.uniform(3.5, 6.5)), 2),
                }
            )
            for indice_turma in range(volume["turmas_por_serie"]):
                letra = LETRAS_TURMA[indice_turma]
                turma_id = f"tur_{sufixo}_{indice_serie + 1}{letra.lower()}"
                turmas_rows.append(
                    {
                        "turma_id": turma_id,
                        "serie_id": serie_id,
                        "escola_id": escola_id,
                        "nome": letra,
                    }
                )
                for ordem_aula, (inicio, fim) in enumerate(_horarios_padrao(aulas_por_dia), start=1):
                    horarios_rows.append(
                        {
                            "horario_id": f"hor_{turma_id}_{ordem_aula}",
                            "turma_id": turma_id,
                            "ordem": ordem_aula,
                            "inicio": inicio,
                            "fim": fim,
                            "dias_semana": "1,2,3,4,5",
                            "ativo": True,
                        }
                    )
                aulas_da_turma = [f"hor_{turma_id}_{ordem}" for ordem in range(1, aulas_por_dia + 1)]
                # Registra as aulas de todas as turmas da série para transferências.
                for indice_outra in range(volume["turmas_por_serie"]):
                    letra_outra = LETRAS_TURMA[indice_outra]
                    outra_turma = f"tur_{sufixo}_{indice_serie + 1}{letra_outra.lower()}"
                    mapa_aulas_por_turma[outra_turma] = [
                        f"hor_{outra_turma}_{ordem}" for ordem in range(1, aulas_por_dia + 1)
                    ]

                # Matrícula inicial da turma.
                quantidade = volume["alunos_por_turma"]
                for indice_aluno in range(quantidade):
                    sequencia_aluno += 1
                    aluno_id = f"aluno_{sequencia_aluno:05d}"
                    base = float(rng.random())
                    cronico = bool(rng.random() < PROPORCAO_CRONICA)
                    propensao = (0.12 + 0.07 * base) if cronico else (0.005 + 0.11 * base * base)
                    aluno_novo = bool(rng.random() < PROBABILIDADE_ALUNO_NOVO)
                    if aluno_novo:
                        indice_inicio = int(rng.integers(15, max(16, len(dias) // 2)))
                        criado_em = dias[indice_inicio].isoformat()
                    else:
                        criado_em = dias[0].isoformat()
                    perfil_justifica_valor = 0.25 + 0.5 * float(rng.random())
                    transferido = bool(rng.random() < PROBABILIDADE_TRANSFERENCIA)
                    turma_atual = turma_id
                    transferido_em = None
                    if transferido and volume["turmas_por_serie"] > 1:
                        outra = LETRAS_TURMA[(indice_turma + 1) % volume["turmas_por_serie"]]
                        turma_atual = f"tur_{sufixo}_{indice_serie + 1}{outra.lower()}"
                        indice_transferencia = int(
                            rng.integers(len(dias) // 4, max(len(dias) // 4 + 1, 3 * len(dias) // 4))
                        )
                        transferido_em = dias[indice_transferencia].isoformat()
                    desiste = bool(rng.random() < chance_desistencia(propensao))
                    desistente_em = None
                    if desiste:
                        indice_desistencia = int(
                            rng.integers(len(dias) // 2, max(len(dias) // 2 + 1, 4 * len(dias) // 5))
                        )
                        desistente_em = dias[indice_desistencia].isoformat()
                    alunos_rows.append(
                        {
                            "aluno_id": aluno_id,
                            "nome": f"Estudante {sequencia_aluno:04d} (sintético)",
                            "turma_id": turma_atual,
                            "turma_original_id": turma_id,
                            "ordem": indice_aluno + 1,
                            "ativo": True,
                            "desistente_em": desistente_em,
                            "transferido_em": transferido_em,
                            "criado_em": criado_em,
                        }
                    )
                    verdade_rows.append(
                        {
                            "aluno_id": aluno_id,
                            "propensao_latente": round(propensao, 5),
                            "cronico": cronico,
                            "perfil_justifica": round(perfil_justifica_valor, 4),
                            "perfil_saida": round(propensao * 0.5 + 0.02, 5),
                            "perfil_entrada": round(propensao * 0.3 + 0.015, 5),
                        }
                    )
                    _simular_aluno(
                        aluno_id=aluno_id,
                        turma_de_origem=turma_id,
                        turma_atual=turma_atual,
                        transferido_em=transferido_em,
                        desistente_em=desistente_em,
                        criado_em=criado_em,
                        aulas_da_turma=aulas_da_turma,
                        mapa_aulas=mapa_aulas_por_turma,
                        com_saidas=com_saidas,
                        dias=dias,
                        rng=rng,
                        propensao=propensao,
                        cronico=cronico,
                        perfil_justifica=perfil_justifica_valor,
                        perfil_saida=propensao * 0.5 + 0.02,
                        perfil_entrada=propensao * 0.3 + 0.015,
                        frequencias_rows=frequencias_rows,
                        faltas_rows=faltas_rows,
                        saidas_rows=saidas_rows,
                        entradas_rows=entradas_rows,
                        chamadas_por_turma_dia=chamadas_por_turma_dia,
                    )

    # Atribui identificadores sequenciais estáveis e resolve as ligações.
    mapa_chamadas = {}
    for indice, linha in enumerate(frequencias_rows, start=1):
        linha["frequencia_id"] = f"freq_{indice:06d}"
        mapa_chamadas[(linha["turma_id"], linha["dia"])] = linha["frequencia_id"]
    for indice, linha in enumerate(faltas_rows, start=1):
        linha["falta_id"] = f"falta_{indice:07d}"
    for indice, linha in enumerate(saidas_rows, start=1):
        linha["saida_id"] = f"saida_{indice:06d}"
    for indice, linha in enumerate(entradas_rows, start=1):
        linha["entrada_id"] = f"entrada_{indice:06d}"
    for linha in faltas_rows:
        chave = linha.pop("chave_chamada")
        linha["frequencia_id"] = mapa_chamadas[chave]

    def _normalizar(dados_pl):
        # Colunas inteiramente nulas nascem com dtype Null; converte para Utf8.
        ajustes = [pl.col(nome).cast(pl.Utf8) for nome, tipo in dados_pl.schema.items() if tipo == pl.Null]
        return dados_pl.with_columns(ajustes) if ajustes else dados_pl

    tabelas = {
        "escolas": _normalizar(pl.DataFrame(escolas_rows, infer_schema_length=None)),
        "series": _normalizar(pl.DataFrame(series_rows, infer_schema_length=None)),
        "turmas": _normalizar(pl.DataFrame(turmas_rows, infer_schema_length=None)),
        "alunos": _normalizar(pl.DataFrame(alunos_rows, infer_schema_length=None)),
        "horarios": _normalizar(pl.DataFrame(horarios_rows, infer_schema_length=None)),
        "frequencias": _normalizar(pl.DataFrame(frequencias_rows, infer_schema_length=None)),
        "faltas": _normalizar(pl.DataFrame(faltas_rows, infer_schema_length=None)),
        "saidas": _normalizar(pl.DataFrame(saidas_rows, infer_schema_length=None)),
        "entradas": _normalizar(pl.DataFrame(entradas_rows, infer_schema_length=None)),
        "feriados": _normalizar(pl.DataFrame(feriados_rows, infer_schema_length=None)),
        "contexto_mec": pl.DataFrame(contexto_rows),
    }
    verdade_oculta = _normalizar(pl.DataFrame(verdade_rows, infer_schema_length=None))

    meta = {
        "gerador": "frequencia.dados.sintetico",
        "perfil": config.perfil,
        "semente": config.semente,
        "ano": config.ano,
        "dias_letivos": len(dias),
        "periodo": [dias[0].isoformat(), dias[-1].isoformat()],
        "sem_dados_pessoais": True,
        "perfis_escola": {
            escola["escola_id"]: {
                "frequencia_por_aula": escola["frequencia_por_aula"],
                "saida_antecipada": escola["saida_antecipada"],
                "origem_na_chamada": escola["origem_na_chamada"],
            }
            for escola in escolas_rows
        },
        "contagens": {nome: df.height for nome, df in tabelas.items()},
    }
    if config.destino is not None:
        _gravar_pacote(config.destino, tabelas, verdade_oculta, meta)
        meta["destino"] = str(config.destino)
    logs.registrar(
        "dados.sintetico.gerar",
        estagio="dados",
        perfil=config.perfil,
        semente=config.semente,
        contagens=meta["contagens"],
        detalhado=detalhado,
    )
    return {"tabelas": tabelas, "verdade_oculta": verdade_oculta, "meta": meta}


def _simular_aluno(
    *,
    aluno_id: str,
    turma_de_origem: str,
    turma_atual: str,
    transferido_em: str | None,
    desistente_em: str | None,
    criado_em: str,
    aulas_da_turma: list[str],
    mapa_aulas: dict[str, list[str]] | None = None,
    com_saidas: bool,
    dias: list[date],
    rng: np.random.Generator,
    propensao: float,
    cronico: bool,
    perfil_justifica: float,
    perfil_saida: float,
    perfil_entrada: float,
    frequencias_rows: list[dict],
    faltas_rows: list[dict],
    saidas_rows: list[dict],
    entradas_rows: list[dict],
    chamadas_por_turma_dia: dict[tuple[str, str], dict],
) -> None:
    """Simula o ano letivo de um aluno: chamadas, faltas, saídas e entradas."""
    turmas_do_dia: dict[str, str] = {}
    if transferido_em is None:
        for dia in dias:
            turmas_do_dia[dia.isoformat()] = turma_atual
    else:
        for dia in dias:
            turmas_do_dia[dia.isoformat()] = (
                turma_de_origem if dia.isoformat() < transferido_em else turma_atual
            )
    aulas_por_turma: dict[str, list[str]] = dict(mapa_aulas or {})
    aulas_por_turma.setdefault(turma_atual, aulas_da_turma)
    aulas_por_turma.setdefault(turma_de_origem, aulas_da_turma)

    posicao_dia = {dia.isoformat(): indice for indice, dia in enumerate(dias)}
    posicao_desistencia = posicao_dia.get(desistente_em) if desistente_em is not None else None

    sequencia = 0
    for dia in dias:
        iso = dia.isoformat()
        if iso < criado_em:
            continue
        if desistente_em is not None and iso >= desistente_em:
            break
        turma_do_dia = turmas_do_dia[iso]
        chave = (turma_do_dia, iso)
        if chave not in chamadas_por_turma_dia:
            tardia = bool(rng.random() < PROBABILIDADE_CHAMADA_TARDIA)
            indice_dia = dias.index(dia)
            if tardia and indice_dia + 1 < len(dias):
                momento_criacao = f"{dias[indice_dia + 1].isoformat()}T08:30:00"
            else:
                minuto = int(rng.integers(0, 40))
                momento_criacao = f"{iso}T17:{minuto:02d}:00"
            chamada = {
                "frequencia_id": "PENDENTE",
                "turma_id": turma_do_dia,
                "dia": iso,
                "revisao": 1,
                "criado_em": momento_criacao,
                "atualizado_em": momento_criacao,
            }
            chamadas_por_turma_dia[chave] = chamada
            frequencias_rows.append(chamada)

        dia_semana = dia.weekday()
        mes = dia.month
        fator = FATOR_DIA_SEMANA.get(dia_semana, 1.0) * FATOR_MES.get(mes, 1.0)
        vesp_feriado = _dias_ate_feriado(dia) == 1
        if vesp_feriado:
            fator *= 1.3
        if (
            posicao_desistencia is not None
            and 0 < posicao_desistencia - posicao_dia[iso] <= DIAS_ESCALADA_DESISTENCIA
        ):
            fator *= FATOR_ESCALADA_DESISTENCIA

        if sequencia > 0:
            ausente = bool(rng.random() < (0.55 if cronico else 0.35))
        else:
            probabilidade = min(0.9, propensao * fator)
            ausente = bool(rng.random() < probabilidade)

        chamada_atual = chamadas_por_turma_dia[chave]
        aulas_da_turma = aulas_por_turma[turma_do_dia]
        if ausente:
            sequencia += 1
            parcial = bool(len(aulas_da_turma) > 1 and rng.random() < 0.30)
            if parcial:
                quantidade_aulas = max(1, int(rng.integers(1, len(aulas_da_turma))))
                aulas_faltadas = aulas_da_turma[:quantidade_aulas]
            else:
                aulas_faltadas = aulas_da_turma
            justificar = bool(rng.random() < (0.65 if sequencia >= 2 else 0.30) * perfil_justifica * 1.6)
            justificativa_final = None
            justificativa_inicial = None
            atualizado_em = None
            if justificar:
                justificativa_final = _escolher_ponderado(MOTIVOS_JUSTIFICATIVA_PESO, float(rng.random()))
                justificativa_inicial = justificativa_final
                if rng.random() < PROBABILIDADE_JUSTIFICATIVA_TARDIA:
                    justificativa_inicial = None
                    atraso = int(rng.integers(1, 4))
                    indice_dia = dias.index(dia)
                    if indice_dia + atraso < len(dias):
                        dia_correcao = dias[indice_dia + atraso]
                        atualizado_em = f"{dia_correcao.isoformat()}T10:00:00"
            removida_em = None
            if rng.random() < PROBABILIDADE_FALTA_REMOVIDA:
                atraso = int(rng.integers(1, 4))
                indice_dia = dias.index(dia)
                if indice_dia + atraso < len(dias):
                    dia_remocao = dias[indice_dia + atraso]
                    removida_em = f"{dia_remocao.isoformat()}T11:00:00"
            for horario_id in aulas_faltadas:
                faltas_rows.append(
                    {
                        "falta_id": "PENDENTE",
                        "frequencia_id": "PENDENTE",
                        "chave_chamada": (turma_do_dia, iso),
                        "aluno_id": aluno_id,
                        "horario_id": horario_id,
                        "justificativa": justificativa_final,
                        "justificativa_inicial": justificativa_inicial,
                        "observacao": None,
                        "criado_em": chamada_atual["criado_em"],
                        "atualizado_em": atualizado_em,
                        "removida_em": removida_em,
                    }
                )
            if removida_em is not None or atualizado_em is not None:
                chamada_atual["revisao"] = 2
                momento = removida_em or atualizado_em
                if momento > chamada_atual["atualizado_em"]:
                    chamada_atual["atualizado_em"] = momento
        else:
            sequencia = 0

        if com_saidas:
            if rng.random() < perfil_saida * fator:
                momento = _escolher_ponderado(MOMENTOS_SAIDA_PESO, float(rng.random()))
                saidas_rows.append(
                    {
                        "saida_id": "PENDENTE",
                        "aluno_id": aluno_id,
                        "turma_id": turma_do_dia,
                        "dia": iso,
                        "momento": momento,
                        "horario": HORARIO_POR_MOMENTO[momento],
                        "justificativa": (
                            _escolher_ponderado(MOTIVOS_JUSTIFICATIVA_PESO, float(rng.random()))
                            if rng.random() < 0.6
                            else None
                        ),
                        "texto": None,
                        "liberado_por_codigo": _escolher_ponderado(LIBERADOR_PESO, float(rng.random())),
                        "criado_em": f"{iso}T16:30:00",
                    }
                )
            elif rng.random() < perfil_entrada * fator:
                momento = _escolher_ponderado(MOMENTOS_ENTRADA_PESO, float(rng.random()))
                minuto = int(rng.integers(10, 90))
                hora = 7 + minuto // 60
                entradas_rows.append(
                    {
                        "entrada_id": "PENDENTE",
                        "aluno_id": aluno_id,
                        "turma_id": turma_do_dia,
                        "dia": iso,
                        "horario": f"{hora:02d}:{minuto % 60:02d}",
                        "momento": momento,
                        "motivo": None,
                        "responsavel_codigo": _escolher_ponderado(LIBERADOR_PESO, float(rng.random())),
                        "criado_em": f"{iso}T16:35:00",
                    }
                )


def _dias_ate_feriado(dia: date) -> int:
    """Distância em dias até o próximo feriado dentro do ano letivo."""
    candidatos = []
    for mes_dia, _ in FERIADOS_ANO:
        partes = mes_dia.split("-")
        feriado = date(dia.year, int(partes[0]), int(partes[1]))
        if feriado >= dia:
            candidatos.append((feriado - dia).days)
    return min(candidatos) if candidatos else 365


def _gravar_pacote(
    destino: Path,
    tabelas: dict,
    verdade_oculta,
    meta: dict,
) -> None:
    """Grava o pacote em CSV com metadados e hashes por arquivo."""
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    hashes: dict[str, str] = {}
    for nome, dados in tabelas.items():
        alvo = destino / f"{nome}.csv"
        dados.write_csv(alvo)
        hashes[f"{nome}.csv"] = hash_infra.hash_arquivo(alvo)
    pasta_oculta = destino / "verdade_oculta"
    pasta_oculta.mkdir(exist_ok=True)
    alvo_oculto = pasta_oculta / "verdade_oculta.csv"
    verdade_oculta.write_csv(alvo_oculto)
    hashes["verdade_oculta/verdade_oculta.csv"] = hash_infra.hash_arquivo(alvo_oculto)
    meta_completo = {**meta, "hashes": hashes}
    with (destino / "meta.json").open("w", encoding="utf-8") as saida:
        json.dump(meta_completo, saida, ensure_ascii=False, indent=2, sort_keys=True)
        saida.write("\n")


def carregar_pacote(destino: Path) -> dict:
    """Lê o pacote de dados gravado em CSV e valida os esquemas."""
    import polars as pl

    from frequencia.dados.esquemas import validar_pacote_tabelas

    destino = Path(destino)
    if not destino.is_dir():
        msg = f"Pasta de dados não encontrada: {destino}. Gere ou importe antes de usar."
        raise ErroValidacao(msg)
    tabelas: dict[str, pl.DataFrame] = {}
    for nome in (
        "escolas",
        "series",
        "turmas",
        "alunos",
        "horarios",
        "frequencias",
        "faltas",
        "saidas",
        "entradas",
        "feriados",
        "contexto_mec",
    ):
        alvo = destino / f"{nome}.csv"
        if not alvo.exists():
            msg = f"Arquivo ausente no pacote: {alvo}."
            raise ErroValidacao(msg)
        tabelas[nome] = pl.read_csv(alvo, null_values=[""])
    contagens = validar_pacote_tabelas(tabelas)
    meta: dict = {}
    alvo_meta = destino / "meta.json"
    if alvo_meta.exists():
        meta = json.loads(alvo_meta.read_text(encoding="utf-8"))
    return {"tabelas": tabelas, "meta": meta, "contagens": contagens}
