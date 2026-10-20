# AGENTS.md

FrequencIA: motor de MLOps do FrequenciApp. Um pacote Python 3.12 (polars, LightGBM, MLflow, DVC) com CLI typer, painel Streamlit e artefato de inferência JavaScript transpilado por m2cgen. Código, comentários, documentação, testes e mensagens são em português brasileiro.

## Diretrizes do repositório

- Leia o `CONTRIBUTING.md`: ele reúne todas as diretrizes do repositório (ambiente, issues, etiquetas, branches, commits, pull requests, dados, padrões de código, testes, documentação e releases).
- A guarda editorial em `tests/test_editorial.py` varre código, documentação e configuração: reprova travessão, meia-risca, reticências tipográficas, aspas curvas e setas fora de blocos cercados. Rode a suíte depois de escrever texto.
- Todo arquivo próprio começa com cabeçalho de uma a duas linhas em português descrevendo o papel.
- Decisões estruturais ganham ADR em `docs/adr/` com numeração sequencial e o formato dos existentes.
- A convenção de identificadores está na ADR-006: domínio em português (`faltas_7d`, `taxa_infrequencia`, chaves do manifesto), infraestrutura consagrada em inglês (`FREQUENCIA_WORKSPACE`, `manifest.json`).
- Nenhuma regra de ruff ou mypy é desativada sem justificativa registrada em ADR.

## Padrões de código

- Camadas com dependência apontando para dentro: infra não conhece dados; features não conhece pipelines; pipelines não conhece cli nem web.
- Erros de domínio são `ExcecaoFrequencia` com mensagem curta e dica; a CLI traduz qualquer exceção para português, sem stack trace salvo `--detalhado`.
- Dados pessoais reais nunca entram em teste, semente, fixture ou log; a massa é sintética e determinística.
- O modelo de dados soberano do FrequenciApp governa a derivação de marca: célula vazia é ausência de frequência, nunca presença (ver `docs/modelo-de-dados.md`).
- Features mudam no catálogo (`src/frequencia/features/catalogo.py`), o dicionário é regenerado com `scripts/gerar_dicionario.py` e os testes de contrato acompanham.
- Type hints em todo o pacote; ruff e mypy são obrigatórios.
- Segredos apenas via ambiente, documentados em `.env.example`.

## Comandos

Pré-requisitos: Python 3.12 e Node 20 ou superior (Node executa a paridade do `modelo.js`). O CI usa Python 3.12.

- Ambiente: `bash scripts/setup.sh`; smoke completo: `bash scripts/smoke.sh`; painel: `bash scripts/demo.sh` ou `streamlit run src/frequencia/web/app.py`.
- Suíte: `python -m pytest tests -q` (cerca de 45 segundos; exigem Node apenas os testes de paridade, que pulam com aviso).
- CLI: `frequencia --help` e por grupo; o ciclo inteiro é `frequencia experimentos executar <dataset> --identificador <id>`.
- Verificação antes de entregar: `make formato-check`, `make lint`, `make tipo`, `make test` e `make smoke` quando a mudança afeta dados, features, pipelines, exportação ou pacote.
- Dicionário: `make dicionario`; a CI confere com `python scripts/gerar_dicionario.py --check`.
- Etiquetas: `make etiquetas` ou `python scripts/sincronizar_etiquetas.py`; requer `gh auth status`.
- Pacote: `make pacote`; requer `build` do extra dev.
- Docker: `docker compose up --build`; ciclo completo em container: `docker compose --profile ciclo up smoke`.

## Ferramentas externas

- GitHub: opere issues, pull requests, execuções de workflow, releases e configurações pelo GitHub CLI (`gh`), não pela interface web. Antes de operar, confirme a sessão com `gh auth status` (ou `gh status`) e, se não houver conexão, rode `gh auth login`. Exemplos: `gh issue create`, `gh pr create`, `gh pr checks --watch`, `gh run watch`, `gh release create` e `gh api`. Nunca inclua segredos ou dados de alunos em comandos, títulos ou corpos.
- Node: execute a paridade Python e JavaScript com Node 20 ou superior. O CI usa Node 24.
- Docker: use containers para validar o ciclo em ambiente isolado. O caminho Docker é validado no workflow `testes.yml` e não substitui o smoke no venv.

## Fluxo de issues e pull requests

- Aplique etiquetas em toda issue e todo pull request: uma de tipo e, fora do tipo `docs`, uma de área. Use `gh issue create --label "bug" --label "area: treino"` e `gh pr edit <número> --add-label "area: infra"`. O catálogo fica em `.github/labels.json` e é sincronizado com `make etiquetas`. Pull requests do Dependabot recebem `dependencies` e `area: infra` e dispensam a validação de título.
- Faça apenas commits atômicos: uma mudança lógica completa por commit, sem trabalho em andamento nem correção de revisão. Use `git commit --fixup` durante o desenvolvimento e `git rebase -i --autosquash` antes de publicar.
- Organize todos os commits do assunto em uma única branch e um único pull request. Abra o pull request somente quando estiver finalizado, com título em Conventional Commits, verificações locais, documentação e CHANGELOG prontos. Não use `gh pr create --fill`.
- Todo pull request precisa da aprovação de um mantenedor do `.github/CODEOWNERS` antes do merge; quem abriu pode mesclar depois da aprovação. Agentes não mesclam sem essa aprovação.
- Se o CI falhar ou surgir algo novo depois de aberto, converta para rascunho com `gh pr ready --undo`, faça os commits e só marque como pronto com `gh pr ready` quando tudo estiver verde.
- Nunca peça revisão com o pull request em rascunho nem abra pull request incompleto.
- Commits com geração relevante por IA levam o rodapé `Assisted-by: ferramenta:modelo`; a autoria e a responsabilidade são humanas.
- Branches criadas por agentes seguem `tipo/descricao-curta`; branches `dependabot/...` são a exceção.

## Dependabot

- O Dependabot cobre pip, pre-commit, GitHub Actions, Docker e Docker Compose.
- Versões menores e correções entram agrupadas por domínio; versões maiores ficam individuais.
- Atualizações de segurança são individuais e têm prioridade alta na triagem.
- Aumentos de versão maior de dependências de runtime exigem ADR-007, `make smoke` e revisão. O Dependabot propõe; a decisão é humana.
- `pyproject.toml` mantém versões exatas. Não relaxe um pin para resolver conflito sem decisão registrada.

## Arquitetura

- A dependência aponta para dentro: `src/frequencia/dados`, `privacidade`, `features`, `pipelines`, `modelos`, `distribuicao`, `integracao`, `monitoramento`, `infra`, `cli` e `web`.
- O motor compartilha o catálogo de features entre treino e inferência; o pacote publicado carrega `modelo.js`, `fallback.js`, `manifest.json` e `dados-teste.json`.
- A CLI e o painel usam o mesmo motor; o painel não implementa cálculo próprio.
- O ambiente é validado na partida e o workspace vem de `FREQUENCIA_WORKSPACE`.

## Armadilhas

- m2cgen suporta LightGBM com booster gbdt; a saída para classificação binária devolve o vetor de probabilidades por classe, e o invólucro toma a última posição.
- LightGBM 4.7 rejeita rótulos fracionários no objetivo binário pelo caminho sklearn: a destilação usa duplicação ponderada (ADR-012).
- polars 2.0 renomeou `min_periods` para `min_samples` em rolling; pandera polars não tem checagem composta nativa, feita em código (ADR-004).
- MLflow 3.17 recusa file store: o rastreamento usa SQLite (ADR-008).
- O pytest precisa do `FREQUENCIA_WORKSPACE` apontando para pasta temporária nos testes; as fixtures cuidam disso, código novo não deve gravar fora de `var/`.
- Caminhos relativos na CLI resolvem pelo diretório corrente, não pelo workspace: em automação, prefira caminhos absolutos ou `--workspace`.
- O Dockerfile instala Node para a paridade; a imagem de runtime não precisa de Node, apenas a de desenvolvimento.
- O serviço `smoke` do Compose precisa de `FREQUENCIA_MLFLOW_URI=http://mlflow:5000` para validar o servidor de rastreamento.
- O projeto exige Python 3.12. Python 3.15 no host não satisfaz `requires-python`; use o venv correto ou o container.

## Fluxo de mudança

- Commits atômicos em Conventional Commits no presente do indicativo, em português: `fix(calibracao): corrige quantil com amostra pequena`.
- Mudança de contrato (features, manifesto, limiares) exige atualização de catálogo, dicionário, testes de contrato e ADR quando muda semântica.
- Nunca promova versão sem gates verdes e aprovação registrada; o papel de aprovador é obrigatório nas transições finais.
- A `main` é protegida por rulesets; mudanças entram por pull request com checks verdes e revisão de CODEOWNERS.
