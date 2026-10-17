# Importação de dados com validação, licença, hash, PII e linhagem.
"""Portão de entrada do fluxo de dados do FrequencIA.

Toda importação registra origem, data, licença e hash, valida o esquema,
executa a verificação de privacidade e só então libera o pacote para uso no
pipeline. Importações de dados institucionais exigem base legal declarada.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from frequencia.dados import sintetico
from frequencia.infra import caminhos, logs
from frequencia.infra import hash as hash_infra
from frequencia.infra.erros import ErroPrivacidade, ErroValidacao

ORIGENS_ACEITAS = ("sintetico", "mec", "institucional")

BASES_LEGAIS = ("execucao-de-politica-publica", "obrigacao-legal", "consentimento", "tutelar")


def registrar_importacao(
    pasta: Path,
    *,
    origem: str,
    licenca: str,
    base_legal: str = "",
    finalidade: str = "treino de modelos com dados pseudonimizados ou sintéticos",
    detalhado: bool = False,
) -> dict:
    """Registra um pacote de dados importado com validação completa.

    Devolve o manifesto de importação com hash, contagens e veredito de
    privacidade. O pacote validado fica referenciado em var/dados/importados.
    """
    pasta = Path(pasta)
    if origem not in ORIGENS_ACEITAS:
        msg = f"Origem inválida: {origem}. Use uma de {ORIGENS_ACEITAS}."
        raise ErroValidacao(msg)
    if origem == "institucional" and base_legal not in BASES_LEGAIS:
        msg = f"Dados institucionais exigem base legal declarada. Use uma de {BASES_LEGAIS}."
        raise ErroPrivacidade(msg)

    pacote = sintetico.carregar_pacote(pasta)
    contagens = pacote["contagens"]
    digestao = hash_infra.hash_pasta(pasta)
    identificador = f"{origem}-{digestao[:12]}"
    destino = caminhos.caminho("importados") / identificador
    if not destino.exists():
        _copiar_pasta(pasta, destino)

    from frequencia.privacidade import detector

    achados = detector.examinar_tabelas(pacote["tabelas"])
    if achados:
        detalhes = "; ".join(
            f"{achado['tabela']}.{achado['coluna']}: {achado['ocorrencias']} ocorrências"
            for achado in achados
        )
        msg = f"Dados pessoais detectados na importação. Corrija antes de registrar: {detalhes}."
        raise ErroPrivacidade(msg)

    manifesto = {
        "identificador": identificador,
        "origem": origem,
        "licenca": licenca,
        "base_legal": base_legal,
        "finalidade": finalidade,
        "importado_em": datetime.now(UTC).isoformat(timespec="seconds"),
        "hash_pasta": digestao,
        "contagens": contagens,
        "pasta": str(destino),
        "privacidade": "sem achados de dados pessoais",
    }
    with (destino / "importacao.json").open("w", encoding="utf-8") as saida:
        json.dump(manifesto, saida, ensure_ascii=False, indent=2, sort_keys=True)
        saida.write("\n")

    logs.registrar(
        "dados.importar",
        estagio="dados",
        origem=origem,
        identificador=identificador,
        hash=digestao,
        contagens=contagens,
        detalhado=detalhado,
    )
    return manifesto


def listar_importacoes() -> list[dict]:
    """Lista os manifestos de importação registrados no workspace."""
    pasta = caminhos.caminho("importados")
    manifestos: list[dict] = []
    if not pasta.exists():
        return manifestos
    for filho in sorted(pasta.iterdir()):
        alvo = filho / "importacao.json"
        if alvo.is_file():
            manifestos.append(json.loads(alvo.read_text(encoding="utf-8")))
    return manifestos


def verificar_integridade(identificador: str) -> dict:
    """Confere o hash atual da pasta importada contra o manifesto."""
    pasta = caminhos.caminho("importados") / identificador
    alvo = pasta / "importacao.json"
    if not alvo.is_file():
        msg = f"Importação desconhecida: {identificador}."
        raise ErroValidacao(msg)
    manifesto = json.loads(alvo.read_text(encoding="utf-8"))
    atual = hash_infra.hash_pasta(pasta)
    return {
        "identificador": identificador,
        "hash_registrado": manifesto["hash_pasta"],
        "hash_atual": atual,
        "integra": atual == manifesto["hash_pasta"],
    }


def gerar_perfil(pasta: Path) -> dict:
    """Gera o perfil estatístico de cada tabela do pacote."""
    pacote = sintetico.carregar_pacote(pasta)
    perfis: dict[str, dict] = {}
    for nome, dados in pacote["tabelas"].items():
        resumo: dict[str, dict] = {}
        for coluna, tipo in dados.schema.items():
            descricao = {
                "tipo": str(tipo),
                "nulos": dados[coluna].null_count(),
                "distintos": dados[coluna].n_unique(),
            }
            if tipo in (pl.Int64, pl.Float64):
                descricao.update(
                    {
                        "minimo": float(dados[coluna].min()) if dados.height else None,
                        "maximo": float(dados[coluna].max()) if dados.height else None,
                        "media": round(float(dados[coluna].mean()), 4) if dados.height else None,
                    }
                )
            resumo[coluna] = descricao
        perfis[nome] = {"linhas": dados.height, "colunas": resumo}
    return {"pasta": str(pasta), "tabelas": perfis}


def _copiar_pasta(origem: Path, destino: Path) -> None:
    """Copia os CSVs e o meta.json do pacote para o workspace."""
    import shutil

    destino.mkdir(parents=True, exist_ok=True)
    for arquivo in origem.iterdir():
        if arquivo.suffix in (".csv", ".json") and arquivo.is_file():
            shutil.copy2(arquivo, destino / arquivo.name)
        elif arquivo.is_dir() and arquivo.name == "verdade_oculta":
            alvo = destino / "verdade_oculta"
            alvo.mkdir(exist_ok=True)
            for interno in arquivo.iterdir():
                shutil.copy2(interno, alvo / interno.name)
