# Testes de privacidade: detector, portão de bloqueio e pseudonimização.
"""Garantia de que dado pessoal não entra no fluxo de treino."""

from __future__ import annotations

import polars as pl

from frequencia.infra.erros import ErroPrivacidade
from frequencia.privacidade import bloqueio, detector, relatorio


def _tabela_com_texto(textos: list[str | None]) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "aluno_id": [f"aluno_{i}" for i in range(len(textos))],
            "nome": textos,
        }
    )


def test_detector_encontra_cpf_e_telefone() -> None:
    """Padrões brasileiros são detectados nas colunas de texto."""
    tabela = _tabela_com_texto(["contato do responsável 123.456.789-00", "ligar (85) 98765-4321"])
    achados = detector.examinar_tabelas({"alunos": tabela})
    tipos = {achado["tipo"] for achado in achados}
    assert "cpf" in tipos
    assert "telefone" in tipos


def test_detector_ignora_nomes_sinteticos(pacote_sintetico) -> None:
    """Identificadores sintéticos não contam como dado pessoal."""
    tabela = _tabela_com_texto(["Estudante 0001 (sintético)"])
    achados = detector.examinar_tabelas({"alunos": tabela})
    assert achados == []


def test_detector_com_presidio_funciona() -> None:
    """O motor presidio em modo padrão complementa as regras próprias."""
    achados_texto = detector.examinar_texto_presidio("cpf 123.456.789-00")
    tipos = {tipo for tipo, _ in achados_texto}
    assert "BR_CPF" in tipos


def test_portao_bloqueia_pacote_com_pii(pacote_sintetico) -> None:
    """Pacote com PII injetada é bloqueado com erro amigável."""
    import shutil

    destino = pacote_sintetico.parent / "pacote_pii"
    shutil.rmtree(destino, ignore_errors=True)
    shutil.copytree(pacote_sintetico, destino)
    alunos = pl.read_csv(destino / "alunos.csv", null_values=[""])
    alunos = alunos.with_columns(
        pl.when(pl.col("nome").str.len_chars() > 0)
        .then(pl.lit("Maria Silva telefone (85) 98765-4321"))
        .otherwise(pl.col("nome"))
        .alias("nome")
    )
    alunos.write_csv(destino / "alunos.csv")
    try:
        bloqueio.validar_entrada_treino(destino)
        raise AssertionError("O portão deveria ter bloqueado o pacote.")
    except ErroPrivacidade as exc:
        assert "bloqueado" in str(exc).lower()
    finally:
        shutil.rmtree(destino, ignore_errors=True)


def test_portao_libera_pacote_limpo(pacote_sintetico) -> None:
    """Pacote sintético limpo passa pelo portão."""
    veredito = bloqueio.validar_entrada_treino(pacote_sintetico)
    assert veredito["liberado"]


def test_identificadores_proibidos_sao_apontados() -> None:
    """Colunas identificadoras diretas são apontadas."""
    tabela = pl.DataFrame({"aluno_id": ["a"], "email": ["x@y.br"], "nome": ["Aluno Sintético 1"]})
    problemas = detector.verificar_identificadores({"alunos": tabela})
    assert any(p["coluna"] == "email" for p in problemas)


def test_pseudonimizacao_e_estavel() -> None:
    """Pseudônimos são estáveis e mascaram o original."""
    tabela = pl.DataFrame({"nome": ["Estudante 1", "Estudante 2"]})
    primeira = relatorio.pseudonimizar_tabela(tabela, ["nome"])
    segunda = relatorio.pseudonimizar_tabela(tabela, ["nome"])
    assert primeira["nome"].to_list() == segunda["nome"].to_list()
    assert "Estudante 1" not in primeira["nome"].to_list()


def test_relatorio_de_risco_gradua_nivel() -> None:
    """Relatório sobe o nível conforme os achados."""
    limpo = relatorio.gerar_relatorio_risco({"alunos": _tabela_com_texto(["Estudante 1"])})
    sujo = relatorio.gerar_relatorio_risco({"alunos": _tabela_com_texto(["cpf 123.456.789-00"])})
    assert limpo["nivel"] == "baixo"
    assert sujo["nivel"] in ("medio", "critico")


def test_logs_nao_registram_dados_pessoais(workspace, pacote_sintetico) -> None:
    """Nenhum log estruturado carrega valor de campo de texto pessoal."""
    from frequencia.infra import logs as logs_mod

    logs_mod.registrar("teste.privacidade", estagio="privacidade", msg="ok")
    eventos = logs_mod.ler_eventos()
    for evento in eventos:
        for valor in str(evento.values()).lower().split():
            assert "cpf" not in valor or "@" not in valor
