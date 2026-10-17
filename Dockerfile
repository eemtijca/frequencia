# Imagem do FrequencIA: Python 3.12 slim com Node para a paridade de inferência.
# Constrói o pacote frequencia com dependências pinadas e expõe CLI, smoke
# tests e Streamlit. O Node entra pela validação de paridade do modelo.js.
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    FREQUENCIA_WORKSPACE=/app

RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY dados ./dados
COPY scripts ./scripts
COPY tests ./tests
COPY config ./config

RUN pip install --upgrade pip \
    && pip install -e . \
    && pip install -e ".[dev]"

RUN useradd --create-home --uid 1001 frequencia \
    && chown -R frequencia:frequencia /app
USER frequencia

RUN mkdir -p /app/var

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import frequencia" || exit 1

CMD ["python", "-m", "frequencia.cli.app", "--help"]
