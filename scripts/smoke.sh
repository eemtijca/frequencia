#!/usr/bin/env bash
# Smoke test completo do FrequencIA: dados, dataset, ciclo, gates e paridade.
# Uso: bash scripts/smoke.sh (no venv) ou docker compose --profile ciclo up smoke.
set -euo pipefail

cd "$(dirname "$0")/.."
if [ -d .venv ]; then
  # shellcheck disable=SC1091
  . .venv/bin/activate
fi

FREQUENCIA="${FREQUENCIA:-frequencia}"
command -v "$FREQUENCIA" >/dev/null 2>&1 || FREQUENCIA="python -m frequencia.cli.app"

WORKSPACE="${FREQUENCIA_WORKSPACE:-$PWD}"
PASTA_DADOS="$WORKSPACE/var/dados/sinteticos/smoke"
PERFIL="${FREQUENCIA_PERFIL:-fumaca}"

mkdir -p "$WORKSPACE/var/relatorios"

echo "== FrequencIA: smoke test do ciclo completo =="
echo "Workspace: $WORKSPACE"

echo "1/8 gerando dados sintéticos ($PERFIL)"
$FREQUENCIA --silencioso dados gerar-sintetico --perfil "$PERFIL" --destino "$PASTA_DADOS" --semente 20261018

echo "2/8 validando esquema e privacidade"
$FREQUENCIA --json dados validar "$PASTA_DADOS" >/dev/null
$FREQUENCIA --json privacidade validar-entrada-treino "$PASTA_DADOS" >/dev/null

echo "3/8 construindo dataset temporal"
$FREQUENCIA --json datasets construir "$PASTA_DADOS" --versao smoke >/dev/null
PASTA_DATASET="$WORKSPACE/var/dados/processados/smoke"

echo "4/8 executando o ciclo completo do experimento"
$FREQUENCIA --json experimentos executar "$PASTA_DATASET" --identificador smoke --versao-modelo "$(date +%Y.%m.%d)-smoke" >/dev/null

echo "5/8 conferindo gates de promoção"
$FREQUENCIA --json avaliacao validar-gates "$WORKSPACE/var/artefatos/experimentos/smoke" > "$WORKSPACE/var/relatorios/gates-smoke.json"
python - <<'PY'
import json
import os
workspace = os.environ.get("FREQUENCIA_WORKSPACE", os.getcwd())
corpo = json.load(open(f"{workspace}/var/relatorios/gates-smoke.json", encoding="utf-8"))
assert corpo["aprovado"], corpo
print("gates aprovados: " + ", ".join(corpo["vereditos"]))
PY

echo "6/8 verificando ausência de futuro no dataset"
$FREQUENCIA --json datasets validar-ausencia-futuro "$PASTA_DATASET" >/dev/null

echo "7/8 testando paridade Python e JS no pacote"
PACOTE=$(ls -d "$WORKSPACE"/var/pacotes/risco-infrequencia-* | head -1)
$FREQUENCIA --json exportacao testar-sinteticos "$PACOTE" > "$WORKSPACE/var/relatorios/paridade-smoke.json"
python - <<'PY'
import json
import os
workspace = os.environ.get("FREQUENCIA_WORKSPACE", os.getcwd())
corpo = json.load(open(f"{workspace}/var/relatorios/paridade-smoke.json", encoding="utf-8"))
assert corpo["paridade_ok"] and corpo["divergencias"] == 0, corpo
print(f"paridade ok: {corpo['casos']} casos, latência {corpo['latencia_ms']} ms")
PY

echo "8/8 rodando a suíte de testes automatizada"
python -m pytest tests -q

echo "== Smoke test concluído com sucesso =="
