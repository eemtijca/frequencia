# Registro de modelos: estados, promoções, aprovações e histórico.
"""Fachada do registro versionado sobre o estado do workspace.

O registro vive em var/estado/registro.json com gravação atômica e auditoria
em acréscimo. Estados: experimental, candidato, homologado, publicado,
descontinuado, arquivado. Os requisitos de promoção são verificados aqui, no
motor: candidato exige gates aprovados; homologado e publicado exigem papel
de aprovador e aprovação registrada vigente (ADR-018).
"""

from __future__ import annotations

from frequencia.infra import estado as estado_infra


def registrar_modelo(*args, **kwargs):
    """Registra uma versão nova no registro de modelos."""
    return estado_infra.registrar_modelo(*args, **kwargs)


def promover_modelo(
    identificador: str,
    versao: str,
    novo_estado: str,
    *,
    ator: str = "cli",
    papel: str = "aprovador",
    justificativa: str = "",
):
    """Promove uma versão entre estados com validação de transição."""
    return estado_infra.promover_modelo(
        identificador,
        versao,
        novo_estado,
        ator=ator,
        papel=papel,
        justificativa=justificativa,
    )


def requisitos_promocao(identificador: str, versao: str, novo_estado: str) -> dict[str, bool]:
    """Checklist objetivo da promoção, o mesmo que o motor aplica."""
    corpo = estado_infra.ler_registro().get("modelos", {}).get(identificador, {})
    detalhe = corpo.get("versoes", {}).get(versao)
    if detalhe is None:
        return {"versão registrada": False}
    return estado_infra.requisitos_promocao(detalhe, novo_estado)


def aprovar_modelo(
    identificador: str, versao: str, aprovado: bool, *, ator: str = "cli", comentario: str = ""
):
    """Registra aprovação ou rejeição da versão."""
    return estado_infra.aprovar_modelo(identificador, versao, aprovado, ator=ator, comentario=comentario)


def descontinuar(identificador: str, versao: str, *, ator: str = "cli", motivo: str = ""):
    """Descontinua uma versão publicada, com motivo auditado."""
    return estado_infra.promover_modelo(
        identificador,
        versao,
        "descontinuado",
        ator=ator,
        justificativa=motivo,
    )


def listar_versoes(identificador: str) -> list[dict]:
    """Lista as versões registradas do modelo com situação atual."""
    registro = estado_infra.ler_registro()
    corpo = registro.get("modelos", {}).get(identificador)
    if not corpo:
        return []
    versoes = []
    for versao, detalhe in sorted(corpo["versoes"].items(), reverse=True):
        linha = {"versao": versao, **detalhe}
        versoes.append(linha)
    return versoes


def ler_registro() -> dict:
    """Lê o registro completo de modelos e publicações."""
    return estado_infra.ler_registro()


def gravar_relatorio_versoes(identificador: str) -> str:
    """Renderiza o histórico de versões em Markdown para a interface."""
    versoes = listar_versoes(identificador)
    linhas = ["# Versões registradas", ""]
    for linha in versoes:
        linhas.append(
            f"- {linha['versao']}: {linha['situacao']}, "
            f"treinado em {linha['treinado_em']}, "
            f"AUC {linha.get('metricas', {}).get('auc', 'n/d')}"
        )
    return "\n".join(linhas) + "\n"
