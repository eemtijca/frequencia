# Imagem do FrequencIA em estágios: base, node, desenvolvimento e runtime.
# O runtime serve a CLI, o painel e o MLflow; o desenvolvimento acrescenta
# testes, scripts e Node para a paridade da inferência.
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    FREQUENCIA_WORKSPACE=/app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1001 frequencia

WORKDIR /app

FROM node:20-slim AS node

FROM base AS dev

COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY dados ./dados
COPY scripts ./scripts
COPY tests ./tests
COPY config ./config

RUN pip install --upgrade pip \
    && pip install -e ".[dev]" \
    && node --version

RUN mkdir -p /app/var \
    && chown -R frequencia:frequencia /app

USER frequencia

CMD ["bash"]

FROM base AS runtime

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY dados ./dados
COPY config ./config

RUN pip install --upgrade pip \
    && pip install . \
    && mkdir -p /app/var /dados/mlflow \
    && chown -R frequencia:frequencia /app /dados

USER frequencia

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import frequencia" || exit 1

CMD ["python", "-m", "frequencia.cli.app", "--help"]
