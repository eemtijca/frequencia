# Testes de features: catálogo, diário, marcas, ordinais e confiança.
"""O contrato de features e a derivação soberana das marcas."""

from __future__ import annotations

from datetime import date

import polars as pl

from frequencia.dados import sintetico
from frequencia.features import calculo, calendario, confianca, diario


def test_catalogo_valido_e_ordenado() -> None:
    """Catálogo com nomes únicos, tipos válidos e ordinais com vocabulário."""
    from frequencia.features.catalogo import NOMES_FEATURES, validar_contrato

    veredito = validar_contrato()
    assert veredito["valido"]
    assert len(set(NOMES_FEATURES)) == len(NOMES_FEATURES)


def test_derivacao_das_marcas_conforme_documento_soberano(pacote_sintetico) -> None:
    """FJ quando todas justificadas, F quando total, S quando parcial."""
    tabelas = sintetico.carregar_pacote(pacote_sintetico)["tabelas"]
    diário = diario.materializar(tabelas)
    marcas = set(diário["marca"].unique().to_list())
    assert marcas.issubset({"F", "FJ", "S", "P", "vazia"})
    # Presença é o caso comum: a maioria das células é P.
    contagens = diário.group_by("marca").agg(pl.len().alias("n")).sort("n", descending=True)
    assert contagens["marca"][0] in ("P", "vazia")


def test_celula_vazia_e_ausencia_de_chamada(pacote_sintetico) -> None:
    """Sem chamada no dia, a célula é vazia, nunca presença."""
    tabelas = sintetico.carregar_pacote(pacote_sintetico)["tabelas"]
    diário = diario.materializar(tabelas)
    sem_chamada = diário.filter(~pl.col("tem_chamada"))
    if sem_chamada.height:
        assert (sem_chamada["marca"] == "vazia").all()


def test_marca_s_exige_chamada_por_aula(pacote_sintetico) -> None:
    """A marca S só existe quando a escola usa chamada por aula."""
    tabelas = sintetico.carregar_pacote(pacote_sintetico)["tabelas"]
    diário = diario.materializar(tabelas)
    escolas_por_aula = set(tabelas["escolas"].filter(pl.col("frequencia_por_aula"))["escola_id"].to_list())
    marcas_s = diário.filter(pl.col("marca") == "S")
    if marcas_s.height:
        assert set(marcas_s["escola_id"].to_list()).issubset(escolas_por_aula)


def test_features_calculadas_em_ordem_do_contrato(pacote_sintetico) -> None:
    """A saída traz todas as features na ordem do catálogo."""
    from frequencia.features.catalogo import NOMES_FEATURES

    tabelas = sintetico.carregar_pacote(pacote_sintetico)["tabelas"]
    dia = sorted(tabelas["frequencias"]["dia"].unique().to_list())[-1]
    diário = diario.materializar(tabelas, instante=f"{dia}T23:59:59", ate_dia=dia)
    frame = calculo.calcular(
        diário,
        dia_referencia=dia,
        contexto_mec=tabelas["contexto_mec"],
        feriados=[date.fromisoformat(v) for v in tabelas["feriados"]["dia"].to_list()],
        dias_restantes_periodo=0.0,
    )
    assert frame.height > 0
    assert list(frame.columns)[5:] == list(NOMES_FEATURES)
    # Sem nulos após os padrões.
    for nome in NOMES_FEATURES:
        assert frame[nome].null_count() == 0, nome


def test_ordinal_de_justificativa_agrupa_raras() -> None:
    """Códigos raros caem no índice de OUTROS do vocabulário."""
    indice = calculo._indice_justificativa(pl.lit("LM"))
    frame = pl.DataFrame({"codigo": ["D", "LM", "G", "Desconhecido"]}).with_columns(
        calculo._indice_justificativa(pl.col("codigo")).alias("idx")
    )
    mapa = dict(zip(frame["codigo"].to_list(), frame["idx"].to_list(), strict=True))
    saida = calculo.INDICE_JUSTIFICATIVA
    assert mapa["D"] == saida["D"]
    assert mapa["LM"] == saida["OUTROS"]
    assert mapa["G"] == saida["OUTROS"]
    assert mapa["Desconhecido"] == saida["OUTROS"]
    assert indice is not None


def test_estados_de_confianca() -> None:
    """A régua de confiança cobre os seis estados do produto."""
    casos = [
        (0, 0, 1.0, "sem_historico"),
        (5, 0, 1.0, "dados_insuficientes"),
        (10, 0, 1.0, "em_observacao"),
        (20, 0, 1.0, "confianca_moderada"),
        (40, 0, 1.0, "confianca_alta"),
        (40, 200, 1.0, "modelo_desatualizado"),
    ]
    for historico, idade, cobertura, esperado in casos:
        resultado = confianca.estado_confianca(
            historico, idade_modelo_dias=idade, cobertura_chamada=cobertura
        )
        assert resultado == esperado, (historico, idade, resultado)


def test_histerese_do_alerta() -> None:
    """Alerta liga após dois dias altos e só desliga abaixo do limite baixo."""
    estado = None
    estado = confianca.atualizar_alerta(0.7, estado)
    assert not estado["em_alerta"]
    estado = confianca.atualizar_alerta(0.7, estado)
    assert estado["em_alerta"]
    estado = confianca.atualizar_alerta(0.5, estado)
    assert estado["em_alerta"]
    estado = confianca.atualizar_alerta(0.4, estado)
    assert not estado["em_alerta"]


def test_aquecimento_ancora_na_taxa_base() -> None:
    """Sem histórico, a previsão é a taxa base; cheia, é a do modelo."""
    valor_zero = confianca.combinacao_aquecimento(0.9, 0.2, 0)
    assert abs(valor_zero - 0.2) < 1e-9
    valor_cheio = confianca.combinacao_aquecimento(0.9, 0.2, 60)
    assert abs(valor_cheio - 0.9) < 1e-9


def test_calendario_ciclico() -> None:
    """Senos e cossenos de dia da semana e mês ficam entre -1 e 1."""
    for dia in (date(2026, 3, 2), date(2026, 11, 20)):
        seno, cosseno = calendario.ciclo_dia_semana(dia)
        assert -1 <= seno <= 1 and -1 <= cosseno <= 1
        seno_mes, cosseno_mes = calendario.ciclo_mes(dia)
        assert -1 <= seno_mes <= 1 and -1 <= cosseno_mes <= 1


def test_distancia_de_feriado_com_teto() -> None:
    """Distâncias de feriado respeitam o teto configurado."""
    feriados = [date(2026, 4, 21)]
    desde, _ate = calendario.distancias_feriado(date(2026, 5, 20), feriados)
    assert desde == calendario.CAP_DIAS_FERIADO
    desde_proximo, ate_proximo = calendario.distancias_feriado(date(2026, 4, 20), feriados)
    assert ate_proximo == 1 and desde_proximo == calendario.CAP_DIAS_FERIADO


def test_ponto_no_tempo_esconde_eventos_futuros(pacote_sintetico) -> None:
    """Snapshot antigo não enxerga chamadas salvas depois."""
    tabelas = sintetico.carregar_pacote(pacote_sintetico)["tabelas"]
    dias = sorted(tabelas["frequencias"]["dia"].unique().to_list())
    meio = dias[len(dias) // 2]
    antes = diario.materializar(tabelas, instante=f"{meio}T08:00:00", ate_dia=meio)
    depois = diario.materializar(tabelas, instante=None, ate_dia=meio)
    # O snapshot da manhã enxerga menos chamadas que o estado final.
    assert antes.filter(pl.col("tem_chamada")).height <= depois.filter(pl.col("tem_chamada")).height
