# AGENTS.md

FrequencIA: motor de MLOps do FrequenciApp. Um pacote Python 3.12 (polars, LightGBM, MLflow, DVC) com CLI typer, painel Streamlit e artefato de inferência JavaScript transpilado por m2cgen. Código, comentários, documentação, testes e mensagens são em português brasileiro.

## Diretrizes do repositório

- Leia o CONTRIBUTING.md: reúne ambiente, padrões de código, testes e fluxo de mudança.
- A guarda editorial em tests/test_editorial.py varre código, documentação e configuração: reprova travessão, meia-risca, reticências tipográficas, aspas curvas e setas fora de blocos cercados. Rode a suíte depois de escrever texto.
- Todo arquivo próprio começa com cabeçalho de uma a duas linhas em português descrevendo o papel.
- Decisões estruturais ganham ADR em docs/adr/ com numeração sequencial e o formato dos existentes.
- A convenção de identificadores está na ADR-006: domínio em português (faltas_7d, taxa_infrequencia, chaves do manifesto), infraestrutura consagrada em inglês (FREQUENCIA_WORKSPACE, manifest.json).

## Padrões de código

- Camadas com dependência apontando para dentro: infra não conhece dados; features não conhece pipelines; pipelines não conhece cli nem web.
- Erros de domínio são ExcecaoFrequencia com mensagem curta e dica; a CLI traduz qualquer exceção para português, sem stack trace salvo --detalhado.
- Dados pessoais reais nunca entram em teste, semente, fixture ou log; a massa é sintética e determinística.
- O modelo de dados soberano do FrequenciApp governa a derivação de marca: célula vazia é ausência de frequência, nunca presença (ver docs/modelo-de-dados.md).
- Features mudam no catálogo (src/frequencia/features/catalogo.py) e o dicionário é regenerado com scripts/gerar_dicionario.py.

## Comandos

Pré-requisitos: Python 3.12 e Node 20 ou superior (Node executa a paridade do modelo.js).

- Ambiente: `bash scripts/setup.sh`; smoke completo: `bash scripts/smoke.sh`; painel: `bash scripts/demo.sh` ou `streamlit run src/frequencia/web/app.py`.
- Suíte: `python -m pytest tests -q` (cerca de 45 segundos; exigem Node apenas os testes de paridade, que pulam com aviso).
- CLI: `frequencia --help` e por grupo; o ciclo inteiro é `frequencia experimentos executar <dataset> --identificador <id>`.
- Verificação antes de entregar: `make lint`, `make tipo`, `make test`.

## Armadilhas

- m2cgen suporta LightGBM com booster gbdt; a saída para classificação binária devolve o vetor de probabilidades por classe, e o invólucro toma a última posição.
- LightGBM 4.7 rejeita rótulos fracionários no objetivo binário pelo caminho sklearn: a destilação usa duplicação ponderada (ADR-12).
- polars 2.0 renomeou min_periods para min_samples em rolling; pandera polars não tem checagem composta nativa, feita em código (ADR-004).
- MLflow 3.17 recusa file store: o rastreamento usa SQLite (ADR-008).
- O pytest precisa do FREQUENCIA_WORKSPACE apontando para pasta temporária nos testes; as fixtures cuidam disso, código novo não deve gravar fora de var/.
- Caminhos relativos na CLI resolvem pelo diretório corrente, não pelo workspace: em automação, prefira caminhos absolutos ou --workspace.

## Fluxo de mudança

- Commits atômicos em Conventional Commits no presente do indicativo, em português: `fix(calibracao): corrige quantil com amostra pequena`.
- Mudança de contrato (features, manifesto, limiares) exige atualização de catálogo, dicionário, testes de contrato e ADR quando muda semântica.
- Nunca promova versão sem gates verdes e aprovação registrada; o papel de aprovador é obrigatório nas transições finais.
