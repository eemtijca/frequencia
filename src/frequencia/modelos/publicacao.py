# Publicação de pacotes: release local, rollback e revogação.
"""Canal de publicação consumido pelo FrequenciApp.

A publicação copia o pacote validado para var/publicacoes/<versao>/ com
notas de mudança e instruções, marca a versão como publicada no registro e
mantém a anterior reversível. Revogação remove o canal e registra motivo.
"""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from frequencia.infra import caminhos, logs
from frequencia.infra import estado as estado_infra
from frequencia.infra.erros import ErroEstado
from frequencia.modelos import registro as registro_mod


def publicar(
    pasta_pacote: Path,
    *,
    versao_modelo: str,
    notas: str = "",
    ator: str = "cli",
    papel: str = "aprovador",
    detalhado: bool = False,
) -> dict:
    """Publica um pacote empacotado e promovido a homologado ou publicado."""
    pasta_pacote = Path(pasta_pacote)
    alvo_manifesto = pasta_pacote / "manifest.json"
    if not alvo_manifesto.is_file():
        msg = f"manifest.json ausente em {pasta_pacote}. Empacote antes de publicar."
        raise ErroEstado(msg)

    from frequencia.distribuicao import pacote as pacote_mod

    integridade = pacote_mod.validar_pacote(pasta_pacote)
    if not integridade["integro"]:
        falhas = [nome for nome, ok in integridade["integridade"].items() if not ok]
        msg = f"Pacote com integridade violada: {', '.join(falhas)}. Regenere o pacote."
        raise ErroEstado(msg)

    destino = caminhos.caminho("publicacoes") / versao_modelo
    if destino.exists():
        shutil.rmtree(destino)
    destino.mkdir(parents=True)
    for arquivo in pasta_pacote.iterdir():
        if arquivo.is_file():
            shutil.copy2(arquivo, destino / arquivo.name)
    with (destino / "notas-de-mudanca.md").open("w", encoding="utf-8") as saida:
        saida.write(_notas(versao_modelo, notas))
    with (destino / "instrucoes-de-consumo.md").open("w", encoding="utf-8") as saida:
        saida.write(_instrucoes(versao_modelo))

    versao_registrada = registro_mod.promover_modelo(
        "risco-infrequencia",
        versao_modelo,
        "publicado",
        ator=ator,
        papel=papel,
        justificativa="publicação via CLI",
    )
    logs.registrar(
        "publicacao.publicar",
        estagio="publicacao",
        versao=versao_modelo,
        hash=versao_registrada["hash_artefato"],
        detalhado=detalhado,
    )
    return {
        "versao": versao_modelo,
        "pasta": str(destino),
        "hash": versao_registrada["hash_artefato"],
        "arquivos": sorted(arquivo.name for arquivo in destino.iterdir()),
    }


def listar_publicacoes() -> list[dict]:
    """Lista as versões publicadas com data e hash."""
    pasta = caminhos.caminho("publicacoes")
    saida: list[dict] = []
    if not pasta.exists():
        return saida
    for filho in sorted(pasta.iterdir(), reverse=True):
        alvo = filho / "manifest.json"
        if alvo.is_file():
            manifesto = json.loads(alvo.read_text(encoding="utf-8"))
            saida.append(
                {
                    "versao": manifesto.get("versao_modelo", filho.name),
                    "criado_em": manifesto.get("criado_em", ""),
                    "hash": manifesto.get("hash_modelo", ""),
                    "validade_ate": manifesto.get("validade_ate", ""),
                    "pasta": str(filho),
                }
            )
    return saida


def versao_atual() -> dict | None:
    """Versão marcada como atual no registro."""
    registro = estado_infra.ler_registro()
    corpo = registro.get("modelos", {}).get("risco-infrequencia", {})
    atual = corpo.get("atual")
    if not atual:
        return None
    detalhe = corpo.get("versoes", {}).get(atual, {})
    return {"versao": atual, **detalhe}


def reverter(
    versao_anterior: str,
    *,
    ator: str = "cli",
    papel: str = "aprovador",
    motivo: str = "",
) -> dict:
    """Reverte a publicação para uma versão anterior ainda presente."""
    atual = versao_atual()
    if atual:
        descontinuar = caminhos.caminho("publicacoes") / atual["versao"]
        if descontinuar.exists():
            shutil.rmtree(descontinuar)
        registro_mod.descontinuar(
            "risco-infrequencia", atual["versao"], ator=ator, motivo=motivo or "rollback"
        )
    pasta = caminhos.caminho("publicacoes") / versao_anterior
    if not pasta.is_dir():
        msg = f"Versão anterior inexistente para reverter: {versao_anterior}."
        raise ErroEstado(msg)
    versoes = registro_mod.listar_versoes("risco-infrequencia")
    detalhe = next((v for v in versoes if v["versao"] == versao_anterior), None)
    if detalhe is None:
        msg = f"Versão {versao_anterior} não consta no registro."
        raise ErroEstado(msg)
    if detalhe["situacao"] != "publicado":
        registro_mod.promover_modelo(
            "risco-infrequencia", versao_anterior, "publicado", ator=ator, papel=papel
        )
    estado_infra.registrar_auditoria(
        "publicacao.reverter",
        alvo=versao_anterior,
        ator=ator,
        detalhe=motivo,
    )
    return {"versao_restaurada": versao_anterior}


def revogar(
    versao: str,
    *,
    ator: str = "cli",
    motivo: str = "",
) -> dict:
    """Revoga uma versão publicada: remove o canal e descontinua."""
    pasta = caminhos.caminho("publicacoes") / versao
    if pasta.exists():
        shutil.rmtree(pasta)
    registro_mod.descontinuar("risco-infrequencia", versao, ator=ator, motivo=motivo or "revogação")
    estado_infra.registrar_auditoria(
        "publicacao.revogar",
        alvo=versao,
        ator=ator,
        detalhe=motivo,
    )
    return {"versao_revogada": versao, "momento": datetime.now(UTC).isoformat()}


def _notas(versao: str, notas: str) -> str:
    return f"# Notas de mudança da versão {versao}\n\n" + (notas or "Sem notas adicionais informadas.") + "\n"


def _instrucoes(versao: str) -> str:
    return (
        "# Instruções de consumo\n\n"
        "1. O app lê manifest.json e confere min_app_versao, validade e hash.\n"
        "2. A atualização é atômica pelo Service Worker: nunca durante a chamada.\n"
        "3. dados-teste.json precisa bater antes de ativar a versão.\n"
        "4. Em falha de carregamento, o fallback.js assume com a mesma interface.\n\n"
        f"Versão: {versao}\n"
    )
