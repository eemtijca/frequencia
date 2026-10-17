#!/usr/bin/env bash
# Prepara o venv do FrequencIA com Python 3.12 e dependências pinadas.
# Uso: bash scripts/setup.sh
set -euo pipefail

if ! command -v python3.12 >/dev/null 2>&1; then
  echo "Python 3.12 não encontrado. Instale-o antes de continuar."
  exit 1
fi

if [ ! -d .venv ]; then
  python3.12 -m venv .venv
fi

. .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
pip check

echo
echo "Ambiente pronto. Ative com: source .venv/bin/activate"
echo "Smoke test completo: bash scripts/smoke.sh"
echo "Aplicação de governança: streamlit run src/frequencia/web/app.py"
