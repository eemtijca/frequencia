# Erros amigáveis: exceções com mensagem curta em português, sem stack trace.
"""Tradução de falhas para mensagens acionáveis.

A interface nunca expõe stack trace ao usuário não técnico: cada erro do
domínio carrega uma frase curta em português com uma ação sugerida.
"""

from __future__ import annotations


class ExcecaoFrequencia(Exception):
    """Erro de domínio com mensagem amigável em português."""

    def __init__(self, mensagem: str, *, dica: str = "") -> None:
        self.mensagem = mensagem
        self.dica = dica
        super().__init__(mensagem)

    def para_usuario(self) -> str:
        """Mensagem final apresentada ao usuário não técnico."""
        if self.dica:
            return f"{self.mensagem} {self.dica}"
        return self.mensagem


class ErroValidacao(ExcecaoFrequencia):
    """Dados não passaram na validação de esquema ou de conteúdo."""


class ErroPrivacidade(ExcecaoFrequencia):
    """Bloqueio do portão de privacidade antes do fluxo de treino."""


class ErroContrato(ExcecaoFrequencia):
    """Violação de contrato de features, manifesto ou pacote."""


class ErroEstado(ExcecaoFrequencia):
    """Operação inválida sobre o estado de modelos ou publicações."""


class ErroConfiguracao(ExcecaoFrequencia):
    """Configuração declarativa ausente ou inválida."""


def traduzir_erro(exc: Exception) -> str:
    """Converte qualquer exceção em frase curta e acionável."""
    if isinstance(exc, ExcecaoFrequencia):
        return exc.para_usuario()
    if isinstance(exc, FileNotFoundError):
        return f"Arquivo não encontrado: {exc.filename}. Verifique o caminho informado."
    if isinstance(exc, PermissionError):
        return "Sem permissão para ler ou gravar o arquivo. Verifique o acesso da pasta."
    if isinstance(exc, IsADirectoryError):
        return "O caminho informado é uma pasta, mas um arquivo era esperado."
    if isinstance(exc, ValueError):
        return f"Valor inválido: {exc}."
    if isinstance(exc, KeyError):
        return f"Chave ausente: {exc}. Verifique o contrato do documento."
    if isinstance(exc, TimeoutError):
        return "A operação demorou demais e foi interrompida. Tente de novo com menos dados."
    nome = type(exc).__name__
    return f"Falha inesperada ({nome}). Rode com --detalhado para investigar."
