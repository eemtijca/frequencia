# Semente e ciclo de demonstração em uma sessão do Streamlit.
# Uso: bash scripts/demo.sh (sobe dados, ciclo e o painel de governança).
set -euo pipefail

. "$(dirname "$0")/preparar-venv.sh"

WORKSPACE="${FREQUENCIA_WORKSPACE:-$PWD}"
PASTA_DADOS="$WORKSPACE/var/dados/sinteticos/demo"

if [ ! -f "$PASTA_DADOS/meta.json" ]; then
  frequencia --silencioso dados gerar-sintetico --perfil fumaca --destino "$PASTA_DADOS" --semente 20261018
  frequencia --json datasets construir "$PASTA_DADOS" --versao demo >/dev/null
  frequencia --json experimentos executar "$WORKSPACE/var/dados/processados/demo" --identificador demo >/dev/null
  echo "Ciclo de demonstração concluído."
fi

echo "Abrindo o painel em http://localhost:8501"
streamlit run src/frequencia/web/app.py --server.address 0.0.0.0 --server.port 8501 --browser.gatherUsageStats false
