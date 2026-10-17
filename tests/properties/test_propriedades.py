# Testes de propriedade com Hypothesis: invariantes das features.
"""Propriedades que valem para qualquer entrada do domínio."""

from __future__ import annotations

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from frequencia.features import confianca
from frequencia.pipelines import baseline


@given(
    historico=st.integers(min_value=0, max_value=400),
    idade=st.integers(min_value=0, max_value=1000),
    cobertura=st.floats(min_value=0.0, max_value=1.0),
)
def test_estado_de_confianca_e_sempre_valido(historico: int, idade: int, cobertura: float) -> None:
    """O estado devolvido sempre pertence ao vocabulário fechado."""
    resultado = confianca.estado_confianca(historico, idade_modelo_dias=idade, cobertura_chamada=cobertura)
    assert resultado in confianca.ESTADOS_CONFIANCA


@given(probabilidade=st.floats(min_value=0.0, max_value=1.0))
def test_peso_historico_fica_entre_zero_e_um(probabilidade: float) -> None:
    """O peso do aquecimento nunca sai do intervalo unitário."""
    peso = confianca.peso_historico(int(probabilidade * 100))
    assert 0.0 <= peso <= 1.0


@given(probabilidade=st.floats(min_value=0.0, max_value=1.0))
def test_combinacao_de_aquecimento_fica_no_intervalo(probabilidade: float) -> None:
    """A mistura com a taxa base devolve probabilidade válida."""
    valor = confianca.combinacao_aquecimento(probabilidade, 0.3, 15)
    assert 0.0 <= valor <= 1.0


@given(
    p1=st.floats(min_value=0.0, max_value=1.0),
    p2=st.floats(min_value=0.0, max_value=1.0),
)
def test_histerese_e_monotona_com_dias_acima(p1: float, p2: float) -> None:
    """Dois dias consecutivos acima do limiar sempre ligam o alerta."""
    estado = confianca.atualizar_alerta(p1, None)
    estado = confianca.atualizar_alerta(p2, estado)
    acima_duas = p1 >= 0.65 and p2 >= 0.65
    if acima_duas:
        assert estado["em_alerta"]


@given(
    semente=st.integers(min_value=0, max_value=2**31),
    valores=st.lists(st.floats(min_value=-5.0, max_value=5.0), min_size=47, max_size=47),
)
@settings(max_examples=25, deadline=None)
def test_baseline_e_deterministico_e_limitado(semente: int, valores: list[float]) -> None:
    """O baseline devolve probabilidade em (0, 1) e é determinístico."""
    matriz = np.array([valores])
    primeira = baseline.pontuar(matriz)
    segunda = baseline.pontuar(matriz)
    assert np.allclose(primeira, segunda)
    assert np.all(primeira > 0) and np.all(primeira < 1)


@given(
    dias_desde=st.integers(min_value=0, max_value=30),
    faltas7=st.integers(min_value=0, max_value=7),
)
def test_regras_crescem_com_falta_recente(dias_desde: int, faltas7: int) -> None:
    """Menos dias desde a última falta nunca reduz o escore, demais igual."""
    from frequencia.features.catalogo import NOMES_FEATURES

    indice = {nome: posicao for posicao, nome in enumerate(NOMES_FEATURES)}
    base = [0.0] * len(NOMES_FEATURES)
    vetor_recente = list(base)
    vetor_antigo = list(base)
    vetor_recente[indice["dias_desde_ultima_falta"]] = dias_desde
    vetor_antigo[indice["dias_desde_ultima_falta"]] = min(30, dias_desde + 5)
    for vetor in (vetor_recente, vetor_antigo):
        vetor[indice["faltas_7d"]] = float(faltas7)
    p_recente = baseline.pontuar(np.array([vetor_recente]))[0]
    p_antiga = baseline.pontuar(np.array([vetor_antigo]))[0]
    assert p_recente >= p_antiga - 1e-9
