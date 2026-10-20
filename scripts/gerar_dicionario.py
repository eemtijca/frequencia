# Gera e confere o dicionário de features a partir do catálogo versionado.
from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from frequencia.features.catalogo import (  # noqa: E402
    CATALOGO,
    VERSAO_CATALOGO,
    catalogo_por_grupo,
    dependentes_de_configuracao,
)

DESTINO = RAIZ / "docs" / "dicionario-de-features.md"

DESCRICOES_GRUPO = {
    "faltas": "Histórico de faltas do aluno em janelas letivas.",
    "saidas": "Saídas antecipadas e entradas atrasadas recentes.",
    "coletivo": "Relatividade frente à turma e à série no mesmo dia.",
    "estrutura": "Cobertura de chamada, matrícula e vínculo com a turma.",
    "perfil": "Flags do perfil de recursos da escola.",
    "calendario": "Sazonalidade e calendário letivo do primeiro dia do horizonte.",
    "mec": "Contexto agregado por série das fontes do INEP.",
    "ordinais": "Códigos de catálogo tratados como ordinais estáveis.",
}

DESCRICOES_DEPENDENCIA = {
    "frequencia_por_aula": "chamada por aula ligada (marca S e aulas por dia)",
    "saida_antecipada": "área de saídas e entradas ligada",
    "origem_na_chamada": "origem da chamada configurada",
}


def formatar_padrao(valor: float) -> str:
    """Formata o valor padrão com uma casa decimal, como no contrato."""
    return f"{valor:.1f}"


def gerar() -> str:
    """Monta o documento completo a partir do catálogo."""
    linhas: list[str] = [
        "# Dicionário de features",
        "",
        (
            f"Versão do catálogo: {VERSAO_CATALOGO}. Fonte da verdade: "
            "`src/frequencia/features/catalogo.py`; este documento é gerado a partir "
            "dele para leitura humana. Toda feature documenta nome, tipo, janela, "
            "origem, sensibilidade, dependência de configuração do FrequenciApp e "
            "valor padrão quando o dado não existe no app."
        ),
        "",
        "## Como ler",
        "",
        "- **Tipo**: numerico (contagem, fração ou índice), binario (flag 0 ou 1) ou ordinal (código de catálogo mapeado em índice fixo).",
        "- **Janela**: quantidade de dias letivos considerada; soma parcial quando o histórico é menor que a janela.",
        "- **Padrão**: valor assumido na inferência quando o app não tem o dado; nunca nulo no modelo.",
        "- **Dependência**: flag do FrequenciApp que precisa estar ligada para a feature ter sentido pleno; com a flag desligada o valor cai no padrão e o manifesto declara confiabilidade reduzida.",
        "",
    ]

    for grupo, features in catalogo_por_grupo().items():
        linhas.extend(
            [
                f"## Grupo {grupo}",
                "",
                DESCRICOES_GRUPO.get(grupo, "Features do grupo."),
                "",
                "| Feature | Amigável | Tipo | Unidade | Janela | Origem | Padrão | Dependência |",
                "| --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for feature in features:
            linhas.append(
                "| `{nome}` | {amigavel} | {tipo} | {unidade} | {janela} | {origem} | {padrao} | {dependencia} |".format(
                    nome=feature.nome,
                    amigavel=feature.nome_amigavel,
                    tipo=feature.tipo,
                    unidade=feature.unidade,
                    janela=feature.janela,
                    origem=feature.origem,
                    padrao=formatar_padrao(feature.padrao),
                    dependencia=feature.dependencia or "",
                )
            )
        linhas.append("")

    linhas.extend(["## Ordinais e vocabulários", ""])
    for feature in CATALOGO:
        if feature.tipo != "ordinal" or not feature.vocabulario:
            continue
        itens = ", ".join(
            f"{indice} é {valor}" for indice, valor in enumerate(feature.vocabulario)
        )
        linhas.append(f"- `{feature.nome}`: {itens}.")
    linhas.extend(
        [
            "",
            "Códigos raros de justificativa (LM, G, Lt, C, S) caem no índice de OUTROS; código desconhecido na inferência também. Momento de saída desconhecido cai em NENHUM. Esses agrupamentos fecham o vazamento de inferência por categoria rara, exigência do briefing.",
            "",
            "## Dependências de configuração do FrequenciApp",
            "",
        ]
    )
    for dependencia, features in dependentes_de_configuracao().items():
        descricao = DESCRICOES_DEPENDENCIA.get(dependencia, "configuração do app")
        nomes = ", ".join(f"`{nome}`" for nome in features)
        linhas.append(f"- **{dependencia}** ({descricao}): {nomes}.")
    linhas.extend(
        [
            "",
            "## Texto livre fora do contrato",
            "",
            "observacao, texto e motivo nunca entram como feature, em nenhuma hipótese; o detector de privacidade os varre antes do treino e o catálogo não os declara.",
            "",
        ]
    )
    return "\n".join(linhas)


def main() -> int:
    """Escreve o documento ou confere se ele está em sincronia."""
    parser = argparse.ArgumentParser(description="Gera o dicionário de features.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Confere o documento sem alterá-lo.",
    )
    argumentos = parser.parse_args()

    gerado = gerar()
    if argumentos.check:
        if not DESTINO.exists():
            print(f"Documento ausente: {DESTINO}", file=sys.stderr)
            return 1
        atual = DESTINO.read_text(encoding="utf-8")
        if atual == gerado:
            print("Dicionário de features em sincronia.")
            return 0
        diferencas = list(
            difflib.unified_diff(
                atual.splitlines(),
                gerado.splitlines(),
                fromfile="docs/dicionario-de-features.md",
                tofile="gerado",
                lineterm="",
            )
        )
        print("\n".join(diferencas[:80]), file=sys.stderr)
        print(
            "O dicionário está desatualizado. Rode make dicionario e confira o diff.",
            file=sys.stderr,
        )
        return 1

    DESTINO.write_text(gerado, encoding="utf-8")
    print(f"Dicionário atualizado em {DESTINO.relative_to(RAIZ)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
