# Makefile do FrequencIA: Docker como caminho padrão, venv como fallback.
.PHONY: help setup up down logs ps smoke smoke-image test lint tipo formato formato-check dicionario dicionario-check pacote ciclos demo etiquetas limpar limpar-tudo venv-setup venv-test venv-lint venv-tipo venv-formato venv-formato-check venv-dicionario venv-dicionario-check venv-pacote venv-ciclos venv-demo venv-smoke venv-limpar

DOCKER_COMPOSE ?= docker compose

help:
	@echo "Docker (padrao):"
	@echo "  make setup              Constroi as imagens de runtime e desenvolvimento"
	@echo "  make up                 Sobe MLflow e painel em segundo plano"
	@echo "  make down               Para os servicos e preserva o volume"
	@echo "  make logs               Acompanha os logs do painel"
	@echo "  make ps                 Mostra o estado dos servicos"
	@echo "  make smoke              Ciclo completo na arvore de trabalho"
	@echo "  make smoke-image        Ciclo completo na imagem construida"
	@echo "  make test               Suite pytest"
	@echo "  make lint               ruff"
	@echo "  make tipo               mypy"
	@echo "  make formato            Corrige a formatacao"
	@echo "  make formato-check      Confere a formatacao"
	@echo "  make dicionario         Gera o dicionario de features"
	@echo "  make dicionario-check   Confere o dicionario de features"
	@echo "  make pacote             Constroi wheel e sdist em dist/"
	@echo "  make ciclos             Ajuda da CLI"
	@echo "  make demo               Sobe o painel de governanca"
	@echo "  make limpar             Para containers e remove caches"
	@echo "  make limpar-tudo        Remove o volume de dados do Docker"
	@echo ""
	@echo "Venv (fallback, Python 3.12):"
	@echo "  make venv-setup"
	@echo "  make venv-test"
	@echo "  make venv-lint"
	@echo "  make venv-tipo"
	@echo "  make venv-formato-check"
	@echo "  make venv-smoke"
	@echo "  make venv-demo"
	@echo ""
	@echo "Host:"
	@echo "  make etiquetas          Requer gh autenticado"

setup:
	$(DOCKER_COMPOSE) build
	$(DOCKER_COMPOSE) --profile cli build cli

up:
	$(DOCKER_COMPOSE) up --build -d

down:
	$(DOCKER_COMPOSE) down

logs:
	$(DOCKER_COMPOSE) logs -f app

ps:
	$(DOCKER_COMPOSE) ps

smoke:
	$(DOCKER_COMPOSE) --profile cli run --rm cli bash scripts/smoke.sh

smoke-image:
	$(DOCKER_COMPOSE) --profile ciclo up --build smoke

test:
	$(DOCKER_COMPOSE) --profile cli run --rm -T --no-deps cli python -m pytest tests -q

lint:
	$(DOCKER_COMPOSE) --profile cli run --rm -T --no-deps cli ruff check src tests

tipo:
	$(DOCKER_COMPOSE) --profile cli run --rm -T --no-deps cli mypy src/frequencia

formato:
	$(DOCKER_COMPOSE) --profile cli run --rm -T --no-deps cli ruff format src tests

formato-check:
	$(DOCKER_COMPOSE) --profile cli run --rm -T --no-deps cli ruff format --check src tests

dicionario:
	$(DOCKER_COMPOSE) --profile cli run --rm -T --no-deps cli python scripts/gerar_dicionario.py

dicionario-check:
	$(DOCKER_COMPOSE) --profile cli run --rm -T --no-deps cli python scripts/gerar_dicionario.py --check

pacote:
	$(DOCKER_COMPOSE) --profile cli run --rm -T --no-deps cli python -m build

ciclos:
	$(DOCKER_COMPOSE) --profile cli run --rm -T --no-deps cli frequencia --help

demo:
	$(DOCKER_COMPOSE) up --build -d
	@echo "Painel: http://localhost:8501"
	@echo "MLflow: http://localhost:5000"
	@echo "Rode make smoke antes para gerar dados de demonstracao."

etiquetas:
	python scripts/sincronizar_etiquetas.py

limpar:
	$(DOCKER_COMPOSE) down
	rm -rf .pytest_cache .ruff_cache .mypy_cache dist build
	find . -name "__pycache__" -type d -not -path "./.venv/*" -exec rm -rf {} +

limpar-tudo:
	@echo "Isso remove o volume de dados do Docker. Use com cuidado."
	$(DOCKER_COMPOSE) down -v

venv-setup:
	bash scripts/setup.sh

venv-test:
	bash scripts/preparar-venv.sh && python -m pytest tests -q

venv-lint:
	bash scripts/preparar-venv.sh && ruff check src tests

venv-tipo:
	bash scripts/preparar-venv.sh && mypy src/frequencia

venv-formato:
	bash scripts/preparar-venv.sh && ruff format src tests

venv-formato-check:
	bash scripts/preparar-venv.sh && ruff format --check src tests

venv-dicionario:
	bash scripts/preparar-venv.sh && python scripts/gerar_dicionario.py

venv-dicionario-check:
	bash scripts/preparar-venv.sh && python scripts/gerar_dicionario.py --check

venv-pacote:
	bash scripts/preparar-venv.sh && python -m build

venv-ciclos:
	bash scripts/preparar-venv.sh && frequencia --help

venv-demo:
	bash scripts/demo.sh

venv-smoke:
	bash scripts/smoke.sh

venv-limpar:
	rm -rf .venv var .pytest_cache .ruff_cache .mypy_cache dist build
