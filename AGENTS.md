# AGENTS.md

FrequencIA: motor de MLOps do FrequenciApp. Um pacote Python 3.12 (polars, LightGBM, MLflow, DVC) com CLI typer, painel Streamlit e artefato de inferência JavaScript transpilado por m2cgen. Código, comentários, documentação, testes e mensagens são em português brasileiro.

## Diretrizes do repositório

- Leia o `CONTRIBUTING.md`: ele reúne todas as diretrizes do repositório (ambiente, issues, etiquetas, branches, commits, pull requests, dados, padrões de código, testes, documentação e releases).
- Para operar o motor como engenheiro de ML ou cientista de dados, siga o [SKILL.md](.agents/skills/frequencia/SKILL.md); este arquivo governa o desenvolvimento do projeto.
- Pesquisa e inovação seguem as diretrizes em [docs/ciencia-e-inovacao.md](docs/ciencia-e-inovacao.md); a versão humana do processo está em [docs/guia-do-cientista.md](docs/guia-do-cientista.md) e o uso escolar em [docs/guia-da-coordenacao.md](docs/guia-da-coordenacao.md).
- A guarda editorial em `tests/test_editorial.py` varre código, documentação e configuração: reprova travessão, meia-risca, reticências tipográficas, aspas curvas e setas fora de blocos cercados. Rode a suíte depois de escrever texto.
- Comandos executáveis em documentação vão em blocos de código bash, não inline. Use inline apenas para nomes de comandos, flags, caminhos, campos e valores.
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

O caminho padrão é Docker. O venv com Python 3.12 é fallback e só deve ser usado quando Docker não estiver disponível. O host com Python 3.15 não é suportado.

### Docker

```bash
docker compose up --build -d
docker compose ps
docker compose --profile ciclo up smoke
docker compose --profile cli run --rm -T --no-deps cli python -m pytest tests -q
docker compose --profile cli run --rm -T --no-deps cli ruff check src tests
docker compose --profile cli run --rm -T --no-deps cli mypy src/frequencia
docker compose --profile cli run --rm -T --no-deps cli ruff format --check src tests
docker compose --profile cli run --rm -T --no-deps cli python scripts/gerar_dicionario.py --check
docker compose --profile cli run --rm -T --no-deps cli python -m build
```

Atalhos:

```bash
make help
make setup
make up
make smoke
make test
make lint
make tipo
make formato-check
make dicionario
make pacote
make down
```

### Fallback venv

```bash
bash scripts/setup.sh
source .venv/bin/activate
python -m pytest tests -q
ruff check src tests
mypy src/frequencia
ruff format --check src tests
python scripts/gerar_dicionario.py --check
python -m build
```

### Observações

- O volume `dados` do Docker é separado do `var/` local do venv. Não misture os dois sem ajustar `FREQUENCIA_WORKSPACE`.
- Os testes de paridade exigem Node 20 ou superior; a imagem de desenvolvimento já inclui Node.
- O serviço `cli` usa a imagem de desenvolvimento e a árvore de trabalho montada. O `smoke` valida a imagem construída.
- `make etiquetas` roda no host, pois exige `gh` autenticado.
- A CLI fica disponível dentro do container; para comandos pontuais, use o prefixo `docker compose --profile cli run --rm cli frequencia`.

## Ferramentas externas

- GitHub: opere issues, pull requests, execuções de workflow, releases e configurações pelo GitHub CLI (`gh`), não pela interface web. Antes de operar, confirme a sessão e nunca inclua segredos ou dados de alunos em comandos, títulos ou corpos.

```bash
gh auth status
gh issue create
gh pr create
gh pr checks --watch
gh run watch
gh release create
gh api <rota>
```

- Node: execute a paridade Python e JavaScript com Node 20 ou superior. O CI usa Node 24. A imagem de desenvolvimento já inclui Node.
- Docker: é o caminho padrão para execução, testes e validação. O serviço `cli` roda a árvore de trabalho; o serviço `smoke` valida a imagem construída. O caminho Docker é validado no workflow `testes.yml`.
- Venv: fallback com Python 3.12, apenas quando Docker não estiver disponível.

## Fluxo de issues e pull requests

- Aplique etiquetas em toda issue e todo pull request: uma de tipo e, fora do tipo `docs`, uma de área. O catálogo fica em `.github/labels.json` e é sincronizado com `make etiquetas`. Pull requests do Dependabot recebem `dependencies` e `area: infra` e dispensam a validação de título.

```bash
gh issue create --label "bug" --label "area: treino"
gh pr edit <numero> --add-label "area: infra"
gh pr ready --undo
gh pr ready
```

- Faça apenas commits atômicos: uma mudança lógica completa por commit, sem trabalho em andamento nem correção de revisão. Use commits de fixup durante o desenvolvimento e limpe a branch antes de publicar.
- Organize todos os commits do assunto em uma única branch e um único pull request. Abra o pull request somente quando estiver finalizado, com título em Conventional Commits, verificações locais, documentação e CHANGELOG prontos. Não use o preenchimento automático do corpo.
- Todo pull request precisa da aprovação de um mantenedor do `.github/CODEOWNERS` antes do merge; quem abriu pode mesclar depois da aprovação. Agentes não mesclam sem essa aprovação.
- Se o CI falhar ou surgir algo novo depois de aberto, converta para rascunho, faça os commits e só marque como pronto quando tudo estiver verde.
- Nunca peça revisão com o pull request em rascunho nem abra pull request incompleto.
- Commits com geração relevante por IA levam o rodapé `Assisted-by: ferramenta:modelo`; a autoria e a responsabilidade são humanas.
- Branches criadas por agentes seguem `tipo/descricao-curta`; branches `dependabot/...` são a exceção.

```bash
# Durante o desenvolvimento
git commit --fixup <commit>

# Antes de publicar
git rebase -i --autosquash
```

## Dependabot

- O Dependabot cobre pip, pre-commit, GitHub Actions, Docker e Docker Compose.
- Versões menores e correções entram agrupadas por domínio; versões maiores ficam individuais.
- Atualizações de segurança são individuais e têm prioridade alta na triagem.
- Aumentos de versão maior de dependências de runtime exigem ADR-007, smoke completo e revisão. O Dependabot propõe; a decisão é humana.
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
- O serviço `cli` roda a árvore de trabalho montada em `/app`; o `smoke` valida a imagem construída. O volume `dados` do Docker é separado do `var/` local do venv; não misture os dois.
- Os alvos `make` usam Docker por padrão. Os alvos `venv-*` são o fallback com Python 3.12. `make etiquetas` roda no host, pois exige `gh`.
- O estágio `dev` do Dockerfile copia `docs`, `projetos`, os Markdown da raiz e `.agents`; o `.dockerignore` precisa permitir esses caminhos para a guarda editorial rodar completa no container.
- O projeto exige Python 3.12. Python 3.15 no host não satisfaz `requires-python`; use o container ou o venv correto.

## Fluxo de mudança

- Commits atômicos em Conventional Commits no presente do indicativo, em português: `fix(calibracao): corrige quantil com amostra pequena`.
- Mudança de contrato (features, manifesto, limiares) exige atualização de catálogo, dicionário, testes de contrato e ADR quando muda semântica.
- Nunca promova versão sem gates verdes e aprovação registrada; o papel de aprovador é obrigatório nas transições finais.
- A `main` é protegida por rulesets; mudanças entram por pull request com checks verdes e revisão de CODEOWNERS.
