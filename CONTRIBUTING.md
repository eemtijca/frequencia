# Contribuindo

Guia de desenvolvimento do FrequencIA: como preparar o ambiente, abrir issues, propor mudanças, escrever código, testar, documentar e publicar. Dúvidas e propostas podem ser abertas como issue; o detalhamento técnico está em [docs/](docs/README.md). Para vulnerabilidades, siga [SECURITY.md](SECURITY.md), e para a convivência, o [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Antes de começar

- Abra uma issue antes de funcionalidades novas, mudanças estruturais e correções grandes. Ajustes pequenos e evidentes podem seguir direto para um pull request.
- Procure issues abertas e fechadas antes de criar uma nova. Havendo uma equivalente, comente para assumir a tarefa e evitar trabalho duplicado.
- Aplique as etiquetas de tipo e de área em toda issue e todo pull request, conforme a seção [Etiquetas](#etiquetas).
- Descreva o contexto com clareza: passos de reprodução, comportamento observado, comportamento esperado e versão ou commit afetado.
- Mantenha a conversa pública nas issues e nos pull requests. Canais privados ficam reservados para vulnerabilidades e assuntos de conduta.
- Nunca inclua segredos, credenciais, dados reais de alunos ou dados pessoais em issues, comandos, commits, capturas ou logs.
- Vulnerabilidades seguem [SECURITY.md](SECURITY.md), nunca uma issue pública.
- A convenção de identificadores está na ADR-006: domínio em português, infraestrutura consagrada em inglês.

## Ambiente de desenvolvimento

Pré-requisitos: Docker com Compose v2. Python 3.12 e Node.js 20 ou superior são necessários apenas no caminho venv de fallback. O host com Python 3.15 não é suportado.

O caminho padrão é Docker:

```bash
docker compose up --build -d
docker compose --profile ciclo up smoke
docker compose --profile cli run --rm -T --no-deps cli python -m pytest tests -q
```

O painel fica em http://localhost:8501 e o MLflow em http://localhost:5000.

O fallback com venv existe apenas para ambientes sem Docker:

```bash
bash scripts/setup.sh
source .venv/bin/activate
bash scripts/smoke.sh
streamlit run src/frequencia/web/app.py
```

O `setup.sh` exige Python 3.12 e instala as dependências fixadas. O `smoke.sh` gera dados sintéticos, executa o ciclo completo, confere os gates, valida a paridade e roda a suíte.

O volume `dados` do Docker é separado do `var/` local do venv. Escolha um caminho e registre qual foi usado.

### Comandos úteis na raiz

Os alvos `make` usam Docker por padrão. Os alvos `venv-*` usam o fallback com Python 3.12.

```bash
# Docker
make help
make setup
make up
make smoke
make test
make lint
make tipo
make formato
make formato-check
make dicionario
make pacote
make down

# Fallback venv
make venv-setup
make venv-test
make venv-lint
make venv-tipo
make venv-formato-check
make venv-smoke
make venv-demo
```

`make etiquetas` roda no host, pois exige `gh` autenticado.

## Fluxo de contribuição e pull requests

### GitHub CLI

Opere issues, pull requests, execuções de workflow e releases pelo GitHub CLI (`gh`), não pela interface web. Antes de operar, confirme a sessão e autentique quando necessário. Nunca inclua segredos, credenciais ou dados de alunos em comandos, títulos, corpos ou comentários.

Comandos do dia a dia:

```bash
gh auth status
gh status
gh auth login
gh issue create
gh issue list
gh issue view
gh pr create
gh pr view
gh pr checks --watch
gh pr ready --undo
gh pr ready
gh pr edit <numero> --add-label <etiqueta>
gh run list
gh run watch
gh run view --log-failed
gh release create
gh release view
gh api <rota>
```

Ajustes de rulesets e de configurações do repositório também passam pelo GitHub CLI. Nunca inclua segredos, credenciais ou dados de alunos em comandos, títulos, corpos ou comentários.

### Issues

Abra uma issue quando:

- encontrar um comportamento incorreto que não consegue corrigir;
- propor uma funcionalidade ou melhoria de escopo;
- discutir uma decisão estrutural ou de arquitetura;
- apontar falha ou lacuna de documentação.

Antes de abrir, procure issues abertas e fechadas com termos relacionados. Os modelos disponíveis são Bug, Melhoria, Tarefa e os contatos para segurança, documentação e contribuição; escolha o mais adequado e preencha os campos obrigatórios.

Uma boa issue contém:

- o problema e o resultado esperado;
- passos de reprodução numerados, com o menor exemplo possível;
- ambiente envolvido (sistema, Python, Node, Docker e versão ou commit);
- contexto adicional, sem dados reais nem segredos.

A triagem acontece em até 7 dias. Uma issue pode ser fechada sem correção quando estiver fora do escopo, duplicada ou sem informação; nesse caso o motivo é explicado e a porta fica aberta para uma proposta mais precisa. Se a issue aberta for resolvida por conta própria, comente o desfecho e feche.

Relacione a issue ao pull request com `Closes #123` quando a mudança encerrar o assunto, ou `Refs #123` quando apenas caminhar na direção dele. A ligação com `Closes` só funciona no pull request que aponta para a branch padrão.

### Etiquetas

Toda issue e todo pull request recebe ao menos uma etiqueta de tipo e uma de área. A prioridade é definida na triagem, e a etiqueta `triagem` sai quando o tipo, a área e a prioridade estiverem confirmados. Pull requests do Dependabot recebem `dependencies` e `area: infra` automaticamente e dispensam a validação de título.

| Grupo | Etiquetas | Uso |
| --- | --- | --- |
| Tipo | `bug`, `enhancement`, `documentation`, `refactor`, `testes`, `ci`, `desempenho`, `manutencao` | Natureza da mudança. |
| Área | `area: dados`, `area: features`, `area: treino`, `area: modelos`, `area: exportacao`, `area: monitoramento`, `area: privacidade`, `area: cli`, `area: painel`, `area: infra` | Parte do sistema afetada. |
| Prioridade | `prioridade: alta`, `prioridade: media`, `prioridade: baixa` | Urgência definida na triagem. |
| Triagem | `triagem` | Aguardando confirmação de tipo, área e prioridade. |
| Versão | `versao: maior`, `versao: menor`, `versao: correcao` | Impacto de versão indicado pelo título. |

O catálogo fica em [.github/labels.json](.github/labels.json) e é aplicado com `make etiquetas`, que cria ou atualiza as etiquetas pelo GitHub CLI. O workflow `etiquetas.yml` aplica `area:` pelos caminhos alterados e o tipo pelo prefixo do título, e o check `validar` reprova pull requests sem etiqueta obrigatória ou com título fora do padrão Conventional Commits. Pull requests do tipo `docs` dispensam etiqueta de área.

Antes de criar uma etiqueta nova, confirme que ela tem público, dono e regra automatizada no mesmo pull request, seja pelo catálogo, pelo mapeamento de caminhos ou pelo título. Etiqueta sem automação tende a não ser aplicada.

Para aplicar:

```bash
gh issue create --label "bug" --label "area: treino"
gh pr create --label "refactor" --label "area: infra"
gh pr edit 123 --add-label "prioridade: alta"
gh pr view 123 --json labels
```

### Branches

Parta da `main` atualizada e use `tipo/descricao-curta`, em minúsculas, com hífens e sem acento:

- `feat/` para funcionalidades novas.
- `fix/` para correções.
- `hotfix/` para correções urgentes em produção.
- `docs/`, `test/`, `refactor/`, `perf/`, `chore/` e `ci/` para os demais casos.
- `release/` para linhas de manutenção, como `release/1.x`, criadas apenas quando houver uma linha antiga a suportar.

Branches criadas por agentes de IA seguem esta mesma convenção de tipo, conforme a [Conventional Branch](https://conventional-branch.github.io/). A autoria assistida fica registrada no rodapé `Assisted-by` do commit e no corpo do pull request.

As branches `dependabot/...` são a exceção: pertencem ao bot e não seguem a convenção de tipo.

### Commits

Siga o [Conventional Commits](https://www.conventionalcommits.org/pt-br/v1.0.0/), em português, no presente do indicativo (3ª pessoa), descrevendo o efeito da mudança:

```text
<tipo>(<escopo opcional>): <descrição>

[corpo opcional]

[rodapé opcional]
```

Tipos usados:

| Tipo | Uso |
| --- | --- |
| `feat` | Funcionalidade nova. |
| `fix` | Correção de comportamento. |
| `docs` | Documentação. |
| `test` | Testes. |
| `refactor` | Mudança interna sem alterar comportamento. |
| `perf` | Desempenho. |
| `chore` | Manutenção e dependências. |
| `ci` | Workflows e automação. |
| `build` | Build e empacotamento. |
| `revert` | Reversão de commit anterior. |

Escopos comuns: `dados`, `features`, `pipelines`, `modelos`, `exportacao`, `cli`, `painel`, `privacidade`, `monitoramento`, `infra`, `docs`, `test`, `ci`.

Regras:

- Cada commit é atômico: contém uma única mudança lógica, completa e autossuficiente. O código compila e as verificações passam em cada commit.
- Não misture contextos no mesmo commit, como formatação, refatoração e mudança de comportamento. Se o commit cabe em mais de um tipo, divida.
- O histórico exposto não contém trabalho em andamento nem correção de revisão. Use commits de fixup durante o desenvolvimento e limpe a branch antes de publicar, com os comandos do bloco abaixo.
- Todos os commits do mesmo assunto ficam em uma única branch e um único pull request.
- Prefira mudanças pequenas e revisáveis, na linha do [Google Engineering Practices](https://google.github.io/eng-practices/review/developer/small-cls.html): cerca de 100 linhas é um tamanho razoável e 1000 é grande demais.
- Use o corpo para explicar o porquê quando a descrição não bastar.
- Use rodapé para referências: `Closes #123`, `Refs #123`.
- Mudança incompatível usa `!` depois do tipo ou escopo, ou o rodapé `BREAKING CHANGE:`.
- Commits com geração relevante por ferramenta de IA levam o rodapé `Assisted-by: ferramenta:modelo`. A responsabilidade pela mudança é de quem envia.
- Evite commits de trabalho em andamento na `main`; o histórico da `main` vem de pull requests.

```bash
# Durante o desenvolvimento
git commit --fixup <commit>

# Antes de publicar
git rebase -i --autosquash
```

Exemplos:

```text
feat(features): adiciona feature de reincidência mensal
fix(calibracao): corrige quantil com amostra pequena
docs: descreve a grade por turma de origem
test(exportacao): cobre a histerese do pacote
```

O sujeito da descrição é a mudança: leia `fix(calibracao): corrige ...` como o commit que corrige o problema. Use o presente do indicativo, não o imperativo, que soa como ordem a quem lê. Prefira `corrige`, `adiciona` e `estende`; evite `corrija`, `adicione` e `estenda`.

### Pull requests

Um pull request resolve um assunto e reúne todos os commits dele. Se a mudança misturar refatoração e comportamento, separe em pull requests menores. Refatorações grandes andam em pull request próprio, sem misturar com correção ou funcionalidade.

Abra o pull request somente quando o trabalho estiver finalizado: verificações locais passando, título em Conventional Commits no presente do indicativo, documentação e CHANGELOG atualizados, etiquetas definidas e revisão do próprio diff feita. Não use o preenchimento automático do corpo, porque ele deve vir do template.

Se o CI falhar ou surgir algo novo depois da abertura, converta o pull request para rascunho, faça os commits atômicos e rode as verificações de novo. Marque como pronto somente com tudo verde. Enquanto o pull request estiver em rascunho, não peça revisão. Depois que a revisão começar, prefira commits novos que respondem ao feedback; se precisar reescrever a história, use `git push --force-with-lease` e explique o motivo na conversa.

A descrição deve conter:

- o problema e o resultado esperado;
- o que mudou e por quê;
- as etiquetas aplicadas;
- como validar: comandos executados e, quando aplicável, passos de interface;
- riscos, mudanças de contrato, variáveis de ambiente novas ou migrações de artefatos;
- a issue relacionada, com `Closes #123` quando aplicável.

Quando a mudança tocar dependências, workflows, privacidade, contratos de features, manifesto ou dados sensíveis, descreva o risco e como ele foi tratado.

Antes de abrir, rode as verificações locais no Docker:

```bash
make formato-check
make lint
make tipo
make test
make smoke
```

No fallback venv:

```bash
make venv-formato-check
make venv-lint
make venv-tipo
make venv-test
make venv-smoke
```

Preencha o checklist do template de pull request. Ao alterar comportamento, atualize a documentação correspondente, o dicionário de features e os testes.

### Revisão e integração contínua

Toda mudança passa por revisão e pelos workflows do GitHub Actions:

| Workflow | Etapas |
| --- | --- |
| `qualidade.yml` | `ruff format --check`, `ruff check`, `mypy`, `pytest` e verificação do dicionário. |
| `testes.yml` | Ciclo completo com dados sintéticos e paridade Python e Node. |
| `testes.yml` | Compose e imagem: build e ciclo em container. |
| `build.yml` | Wheel, sdist, conteúdo do pacote e instalação limpa. |
| `etiquetas.yml` | Aplica etiquetas de área e de tipo e valida o título e as etiquetas em pull requests fora de rascunho. |
| `codeql.yml` | Análise de segurança de Python em push, pull request e agenda semanal. |
| `publicacao.yml` | Publica wheel, sdist e imagem de runtime em release estável. |

A `main` é protegida por rulesets: pull request obrigatório, checks verdes, conversas resolvidas e squash como único método. Todo pull request precisa da aprovação de um mantenedor do [CODEOWNERS](.github/CODEOWNERS); depois da aprovação, quem abriu pode mesclar. A autoaprovação não existe no GitHub; donos da organização podem mesclar com o bypass da regra de revisão, mas continuam sujeitos aos checks de qualidade.

Corrija as falhas antes de pedir nova revisão. Pull requests sem verificações verdes não são mesclados. O check `validar` volta a rodar quando o título ou as etiquetas mudam; se faltar etiqueta, aplique com `gh pr edit --add-label`. Evite force-push depois que a revisão começar; se precisar reescrever a história, explique o motivo na conversa.

### Estratégia de merge

Mescle por squash, em um único commit por pull request. Apague a branch após o merge. Não faça force-push em `main` nem reescreva o histórico já mesclado.

## Padrões de código

- Código e comentários em português, curtos e diretos.
- Domínio em português (`faltas`, `taxa_infrequencia`, `manifesto`); infraestrutura consagrada em inglês (`prisma`, `middleware`, `workspace`).
- Camadas com dependência apontando para dentro: `infra` não conhece dados; `features` não conhece pipelines; `pipelines` não conhece CLI nem painel.
- Type hints em todo o pacote; mypy e ruff são obrigatórios. Nenhuma regra é desativada sem justificativa registrada em ADR.
- Erros de domínio usam `ExcecaoFrequencia` com mensagem curta e dica acionável; a CLI traduz qualquer exceção para português sem stack trace (salvo `--detalhado`).
- Segredos apenas via ambiente, documentados em `.env.example`.
- Sem travessão, meia-risca, reticências tipográficas, aspas curvas e setas em texto de código e documentação: a guarda editorial em `tests/test_editorial.py` reprova. Use ponto, vírgula, parênteses e aspas retas. Cercas de código são isentas.
- Cada arquivo próprio começa com um cabeçalho curto, de uma a duas linhas, descrevendo seu papel.
- Comente apenas trechos não óbvios, como decisões de segurança e cálculos.
- Complexidade precisa de justificativa: o princípio de leveza vale para o código também.

### Dados e artefatos

- Dados pessoais reais nunca entram em teste, semente, fixture, log, issue ou artefato. A massa é sintética e determinística.
- `var/` guarda dados de execução, artefatos, pacotes e logs e nunca é versionado.
- A amostra sintética versionada fica em `dados/sinteticos/amostra/` e é rastreada pelo DVC em modo sem Git (ADR-010).
- O modelo de dados soberano do FrequenciApp governa a derivação de marca: célula vazia é ausência de frequência, nunca presença.
- Mudanças de contrato de features, manifesto, limiares ou inferência exigem catálogo, dicionário, testes de contrato e ADR quando muda semântica.

### Formatação e análise estática

O ruff cuida do estilo e do lint; o mypy cobre a tipagem. Rode `make formato` e `make lint` antes de commitar. Esses alvos usam Docker por padrão; `make venv-formato` e `make venv-lint` são o fallback. A CI também roda `ruff format --check`, e a versão do ruff no `pyproject.toml` precisa ser a mesma do `rev` do pre-commit.

### Contribuições assistidas por IA

Ferramentas de IA são bem-vindas como apoio, mas a responsabilidade pela mudança é de quem envia, e a autoria dos commits é humana. Revise o resultado linha a linha, garanta que ele segue as convenções do repositório, rode as verificações locais e nunca cole segredos, credenciais ou dados reais em ferramentas externas, issues ou commits. Commits com geração relevante levam o rodapé `Assisted-by: ferramenta:modelo`, e o template de pull request tem a seção "Uso de IA". Agentes seguem o [AGENTS.md](AGENTS.md) no desenvolvimento e o [SKILL.md](.agents/skills/frequencia/SKILL.md) na operação, com as mesmas obrigações de etiquetas, commits atômicos, um único pull request e ciclo de rascunho. O caminho padrão de execução é Docker; o venv com Python 3.12 é fallback.

## Testes e qualidade

Os alvos `make` usam Docker por padrão. Os alvos `venv-*` são o fallback com Python 3.12.

```bash
# Docker
make test
make smoke
make dicionario-check
docker compose --profile ciclo up smoke

# Fallback venv
make venv-test
make venv-smoke
make venv-dicionario-check
```

Regras:

- Cada arquivo de teste cria e limpa a própria massa; nunca dependa de dados reais.
- Nenhum teste depende de ordem de execução.
- Ao corrigir um bug, adicione um teste que falharia antes da correção.
- Ao adicionar texto de interface, confira que a guarda editorial passa.
- Testes que tocam o Node pulam com aviso quando ele está ausente; a validação completa exige Node 20 ou superior na imagem de desenvolvimento.

A convenção e a cobertura estão em [docs/testes.md](docs/testes.md).

## Documentação e ADRs

Mudanças estruturais ganham uma nota curta em [docs/adr/](docs/adr/), com estado, contexto, decisão, alternativas e consequências. Novas notas seguem a numeração sequencial e o formato dos ADRs existentes. O índice fica em [docs/README.md](docs/README.md).

### Padrão da documentação

Toda a documentação usa português brasileiro com acentuação e cedilha corretas, em tom técnico e impessoal. Evite primeira pessoa, exclamações e frases de preenchimento.

Restrições de formatação:

- Não use travessão, meia-risca, reticências tipográficas, aspas curvas, setas ou símbolos decorativos. Use dois-pontos, vírgula, parênteses, `...` e aspas retas.
- Evite segunda pessoa explícita e pluralização com parênteses.
- Siga a sintaxe Markdown do GitHub: um único título de nível 1 por arquivo, hierarquia de títulos sem saltos, listas com `-`, cercas de código com linguagem e texto alternativo em imagens.
- Use links relativos para arquivos do repositório e mantenha o texto do link em uma única linha.
- Use alertas (`> [!NOTE]`, `> [!WARNING]`) com parcimônia, no máximo um ou dois por documento.
- Valide com `make formato-check` antes de enviar.

### Comandos e blocos de código

- Todo comando que o leitor deve executar vai em um bloco de código bash, não inline.
- Use inline code apenas para nomes de comandos, flags, caminhos, campos e valores.
- Cada bloco deve ser copiável, sem prompt `$`.
- Use comentários `#` para explicar o efeito de cada comando.
- Use `<placeholder>` para valores que o leitor precisa substituir.
- Separe comandos de saída: `bash` para comandos e `text` para saídas.
- No caminho Docker, use `docker compose`; no fallback, use o venv com Python 3.12.
- ADRs históricos não são reescritos por estilo; apenas correções factuais.

### Dicionário de features

O dicionário é gerado por `scripts/gerar_dicionario.py` a partir de `src/frequencia/features/catalogo.py`. Mude o catálogo, rode `make dicionario` e confira o diff. A CI reprova quando o documento está fora de sincronia.

### Documentação de contratos

Mudanças de rota, contrato de features, manifesto, limiares ou inferência atualizam o documento correspondente em `docs/` e os testes de contrato. A documentação de contratos é parte do entregável, não um apêndice.

## Releases e changelog

As mudanças relevantes são registradas em [CHANGELOG.md](CHANGELOG.md), no formato [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/), com versionamento semântico. Mova as entradas da seção Não publicado para a versão correspondente ao publicar.

Enquanto a primeira versão pública não é lançada, a versão do projeto permanece fixada em `0.1.0` e as mudanças ficam na seção Não publicado. A primeira release será a `v1.0.0`; a partir dela, o versionamento semântico passa a reger as versões.

O fluxo de releases e a política de suporte estão em [docs/releases.md](docs/releases.md).

Crie releases pelo GitHub CLI:

```bash
gh release create vX.Y.Z --generate-notes
```

O workflow `publicacao.yml` valida a tag contra o `pyproject.toml`, anexa wheel e sdist à release e publica a imagem de runtime no GHCR. A tag `vX.Y.Z` é imutável pela ruleset de tags.

## Suporte e dúvidas

Use as issues para dúvidas, sugestões e problemas. A triagem acontece em até 7 dias. Para vulnerabilidades, siga [SECURITY.md](SECURITY.md); para conduta, o [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
