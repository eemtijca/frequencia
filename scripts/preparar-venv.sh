#!/usr/bin/env bash
# Carrega o venv do projeto, criando-o quando necessário.
set -euo pipefail
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ"
if [ ! -d .venv ]; then
  bash scripts/setup.sh
fi
# shellcheck disable=SC1091
. .venv/bin/activate
