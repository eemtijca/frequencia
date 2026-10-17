# Guarda editorial: varre o repositório atrás de caracteres proibidos.
"""Padrão herdado do FrequenciApp para tom de texto consistente.

Reprova travessão, meia-risca, reticências tipográficas, aspas curvas e
setas em documentação e strings de código; o texto do projeto usa ponto,
vírgula, parênteses e aspas retas.
"""

from __future__ import annotations

from pathlib import Path

PROIBIDOS = {
    chr(0x2014): "travessão",
    chr(0x2013): "meia-risca",
    chr(0x2026): "reticências tipográficas",
    chr(0x201C): "aspas curvas de abertura",
    chr(0x201D): "aspas curvas de fechamento",
    chr(0x2018): "aspas simples curvas",
    chr(0x2019): "apóstrofo curvo",
    chr(0x2192): "seta",
    chr(0x2190): "seta",
    chr(0x21D2): "seta dupla",
}

EXTENSOES = (".py", ".md", ".toml", ".yml", ".yaml", ".sh", ".json", ".js")
PASTAS_IGNORADAS = {".venv", "var", "node_modules", ".git", "__pycache__", ".mypy_cache", ".ruff_cache"}
ARQUIVOS_IGNORADOS = {"uv.lock"}


def _arquivos_alvo(raiz: Path) -> list[Path]:
    alvos: list[Path] = []
    for caminho in raiz.rglob("*"):
        if not caminho.is_file():
            continue
        if any(parte in PASTAS_IGNORADAS for parte in caminho.parts):
            continue
        if caminho.name in ARQUIVOS_IGNORADOS:
            continue
        if caminho.suffix.lower() in EXTENSOES:
            alvos.append(caminho)
    return alvos


def _sem_cercas(texto: str) -> str:
    """Remove blocos cercados: diagramas e exemplos de código são isentos."""
    linhas = texto.splitlines()
    saida: list[str] = []
    dentro = False
    for linha in linhas:
        if linha.strip().startswith("```"):
            dentro = not dentro
            continue
        if not dentro:
            saida.append(linha)
    return "\n".join(saida)


def test_guarda_editorial() -> None:
    """Nenhum arquivo do repositório usa os caracteres proibidos."""
    raiz = Path(__file__).resolve().parents[1]
    violacoes: list[str] = []
    for arquivo in _arquivos_alvo(raiz):
        try:
            texto = arquivo.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        corpo = _sem_cercas(texto)
        for caractere, nome in PROIBIDOS.items():
            if caractere in corpo:
                relativo = arquivo.relative_to(raiz)
                violacoes.append(f"{relativo}: {nome}")
    assert not violacoes, "Caracteres proibidos encontrados: " + "; ".join(violacoes[:10])


def test_cabecalho_de_arquivos_proprios() -> None:
    """Cada módulo próprio começa com comentário de cabeçalho em português."""
    raiz = Path(__file__).resolve().parents[1] / "src"
    sem_cabecalho: list[str] = []
    for arquivo in raiz.rglob("*.py"):
        if "__pycache__" in arquivo.parts:
            continue
        linhas = arquivo.read_text(encoding="utf-8").splitlines()
        corpo = next((linha for linha in linhas if linha.strip()), "")
        if not (corpo.startswith("#") or corpo.startswith('"""')):
            sem_cabecalho.append(str(arquivo.relative_to(raiz)))
    assert not sem_cabecalho, "Sem cabeçalho: " + "; ".join(sem_cabecalho[:10])
