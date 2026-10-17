# Makefile do FrequencIA: atalhos do dia a dia no venv.
.PHONY: setup smoke test lint tipo formato demo ciclos limpar

setup:
	bash scripts/setup.sh

smoke:
	bash scripts/smoke.sh

test:
	bash scripts/preparar-venv.sh && python -m pytest tests -q

lint:
	bash scripts/preparar-venv.sh && ruff check src tests

tipo:
	bash scripts/preparar-venv.sh && mypy src/frequencia

formato:
	bash scripts/preparar-venv.sh && ruff format src tests

demo:
	bash scripts/demo.sh

ciclos:
	bash scripts/preparar-venv.sh && frequencia --help

limpar:
	rm -rf var .pytest_cache .ruff_cache .mypy_cache
	find . -name "__pycache__" -type d -not -path "./.venv/*" -exec rm -rf {} +
