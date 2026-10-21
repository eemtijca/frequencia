---
name: frequencia
description: "Opera o FrequencIA como engenheiro de ML, cientista de dados e operador de MLOps: ciclo de dados sintéticos e institucionais, construção de dataset temporal sem vazamento, treino e ensemble, calibração, avaliação com gates, exportação JavaScript, empacotamento, registro, promoção, publicação, monitoramento, drift, retreinamento e auditoria. Use quando a tarefa envolver comandos frequencia, o modelo de risco de infrequência, MLflow, DVC, pacote de inferência, análise de qualidade, proposta de novas ideias ou governança de modelo. Não use para alterar código-fonte, testes, workflows ou dependências do projeto; nesse caso, siga o AGENTS.md."
license: MIT
compatibility: "Requer a CLI frequencia em Python 3.12, Node.js 20 ou superior para a paridade do modelo.js e um workspace local com var/. Docker Compose é o caminho padrão; o venv com Python 3.12 é o fallback."
metadata:
  author: Equipe FrequencIA
  version: "1.0"
  repositorio: "https://github.com/eemtijca/frequencia"
---

# FrequencIA: manual de operação para agentes de ML e ciência de dados

Manual operacional para agentes de IA que usam o FrequencIA como engenheiros de ML, cientistas de dados e operadores de MLOps. A fonte de verdade dos comandos é o próprio CLI:

```bash
frequencia --help
frequencia <grupo> <comando> --help
```

## Escopo e fronteira com o AGENTS.md

O `AGENTS.md` governa o desenvolvimento: código, testes, workflows, dependências, ADRs, issues, pull requests, commits e releases.

Esta skill governa a operação e a pesquisa: dados, privacidade, features, datasets, experimentos, avaliação, exportação, empacotamento, registro, publicação, monitoramento, auditoria e propostas de novas ideias.

Se a tarefa pedir para alterar código, teste, workflow, catálogo de features, limiar de gate, rótulo ou contrato de inferência, pare e siga o `AGENTS.md`. Mudanças de contrato exigem ADR e testes de contrato. Inspecionar código para entender um comando é permitido; alterar não.

## Como usar esta skill

| Se a tarefa é | Leia |
| --- | --- |
| Descobrir comando, flag ou efeito | `references/comandos.md` |
| Executar um fluxo completo | `references/playbooks.md` |
| Interpretar métricas, gates, calibração ou fairness | `references/engenharia.md` |
| Promover, publicar, reverter, auditar ou tratar incidente | `references/governanca.md` |
| Propor, protocolar ou validar uma ideia nova | `references/pesquisa.md` |
| Entender o desenho do modelo | `docs/mlops.md` e `docs/arquitetura.md` |
| Alterar código, teste, workflow ou contrato | `AGENTS.md` e `CONTRIBUTING.md` |

## Regras que não se negociam

- Dados pessoais reais nunca entram em prompt, teste, fixture, log, commit ou artefato. A massa padrão é sintética e determinística.
- Dados institucionais exigem base legal declarada e portão de privacidade verde antes de qualquer treino.
- Nunca afrouxe um gate, um limiar ou uma métrica para a versão passar. Mudança de gate exige ADR e revisão humana.
- Nunca aprove, promova ou publique sozinho. O papel de aprovador pertence a uma pessoa responsável.
- Use `--forca` apenas com `--justificativa`. Prefira retomar a etapa com `experimentos recuperar`.
- Não edite `estado.json`, `registro.json`, `gates.json`, `manifest.json` nem `auditoria.jsonl` à mão.
- Não escreva fora de `var/`, salvo quando a tarefa for de desenvolvimento e seguir o `AGENTS.md`.
- Preserve a semente, o dataset, o hash e a run do MLflow. Resultado sem rastro não é evidência.
- Relatórios e logs usam dados agregados, nunca registros individuais de estudantes.
- Comandos executáveis em documentação vão em blocos de código bash, não inline. Use inline apenas para nomes, flags, caminhos e campos.
- Prefira Docker. Use o venv com Python 3.12 apenas como fallback.
- Não misture o volume `dados` do Docker com o `var/` local do venv.

## Modos de atuação

| Modo | Quando usar | Pode | Não pode |
| --- | --- | --- | --- |
| Operação | Rodar ciclo, avaliar, publicar, monitorar | Executar CLI, ler artefatos, preparar relatórios | Alterar código, aprovar, mudar gates |
| Pesquisa | Propor ideia, testar hipótese, investigar queda | Explorar, protocolar, experimentar em isolamento, propor decisão | Aprovar, publicar, alterar gate, usar PII real |
| Desenvolvimento | Implementar feature, corrigir código, mudar contrato | Alterar código, testes, docs e ADR, seguindo o `AGENTS.md` | Publicar sem gates, aprovar a própria mudança |

Anuncie o modo antes de agir. Se a tarefa misturar modos, separe: pesquisa, depois desenvolvimento, depois operação.

## Ambiente de execução

Prefira Docker. Use o venv apenas quando Docker não estiver disponível e houver Python 3.12.

```bash
docker compose up --build -d
docker compose --profile ciclo up smoke
docker compose --profile cli run --rm cli frequencia --help
```

O host com Python 3.15 não é suportado. Se Docker e Python 3.12 faltarem, pare e peça um ambiente adequado.

Fallback com venv, somente quando necessário:

```bash
python3.12 --version
bash scripts/setup.sh
source .venv/bin/activate
frequencia --help
```

O volume `dados` do Docker é separado do `var/` local do venv. Escolha um caminho e registre qual foi usado no pacote de evidências. Para inspecionar artefatos no Docker:

```bash
docker compose --profile cli run --rm -T --no-deps cli ls -la var/artefatos/experimentos
docker compose --profile cli run --rm -T --no-deps cli ls -la var/pacotes
```

## Mapa rápido

### Grupos da CLI

| Grupo | Comandos | Papel |
| --- | ---: | --- |
| `dados` | 10 | fontes, importação, validação, PII, hash, DVC e sintéticos |
| `privacidade` | 6 | identificadores, sensíveis, pseudonimização, risco, portão e bloqueio |
| `features` | 9 | catálogo, contrato, dicionário, distribuição, nulos, constantes, vazamento e congelamento |
| `datasets` | 6 | construção temporal, separação, perfis, ausência de futuro, linhagem e listagem |
| `experimentos` | 10 | ciclo completo, treino, ensemble, destilação, comparação, recuperação e relatório |
| `avaliacao` | 10 | métricas, calibração, ensemble, subgrupos, fairness, curva, custo, baseline, gates e relatório |
| `exportacao` | 7 | contratos, tamanho e latência, dados-teste, paridade, compatibilidade, hash e registro |
| `empacotamento` | 5 | montagem, validação, homologação, publicação e assinatura lógica |
| `registro` | 9 | registro, promoção, descontinuação, arquivamento, estado, listagem, comparação, aprovação e rejeição |
| `publicacao` | 9 | publicação, release, compatibilidade, hash, instruções, produção, rollback, revogação e listagem |
| `monitoramento` | 8 | feedback, acurácia, descarte, drift, validade, recalibração, saúde e retreinamento |
| `auditoria` | 5 | trilha, filtro, exportação, integridade e linhagem |

### As sete etapas do experimento

| Etapa | O que produz |
| --- | --- |
| treino | modelo principal, métricas e run do MLflow |
| ensemble | sete membros, OOF, pesos e discordância |
| calibracao | Platt, conformal e curva de aprendizado |
| destilacao | estudante LightGBM leve |
| avaliacao | métricas, subgrupos, fairness, custo e gates |
| exportacao | modelo.js, fallback.js, dados-teste e validação de paridade |
| empacotamento | manifesto, cartão, zip e registro experimental |

### Gates de promoção

| Gate | Limite | Mede |
| --- | --- | --- |
| auc | mínimo 0,70 | ordenação |
| ece | máximo 0,10 | calibração |
| cobertura_conformal | mínimo 0,80 | confiança dos intervalos |
| taxa_alerta | máximo 0,35 | custo operacional |
| melhora_sobre_baseline | mínimo 0 | ganho sobre regras simples |
| tamanho_pacote | máximo 262144 bytes | leveza |
| latencia | máximo 5 ms | resposta no navegador |

### Estados do registro

| Estado | Próximos estados |
| --- | --- |
| experimental | candidato, descontinuado, arquivado |
| candidato | homologado, experimental, descontinuado, arquivado |
| homologado | publicado, candidato, descontinuado, arquivado |
| publicado | descontinuado, arquivado |
| descontinuado | arquivado |
| arquivado | nenhum |

Promoção a homologado ou publicado exige papel de aprovador. A aprovação é um registro separado, feito com `registro aprovar`.

### Papéis

| Papel | Uso |
| --- | --- |
| observador | leitura de painel e relatórios |
| cientista | análise, treino e avaliação |
| engenheiro | operação da CLI, empacotamento e monitoramento |
| aprovador | promoção a homologado ou publicado, publicação, rollback e revogação |

O papel é registrado na auditoria. A CLI bloqueia alguns casos, mas a responsabilidade é humana. Nunca use `--papel aprovador` sem uma pessoa aprovadora real.

### Artefatos e caminhos

| Caminho | Conteúdo |
| --- | --- |
| `var/dados/sinteticos/<perfil>/` | pacote sintético |
| `var/dados/importados/<id>/` | cópia importada e `importacao.json` |
| `var/dados/processados/<versao>/` | `dataset.parquet`, `amostra.csv` e `meta.json` |
| `var/artefatos/experimentos/<id>/` | estado, modelo, ensemble, calibração, estudante, avaliação, gates, exportações e empacotamento |
| `var/pacotes/risco-infrequencia-<versao>/` | pacote zip e arquivos de distribuição |
| `var/publicacoes/<versao>/` | release local com notas e instruções |
| `var/estado/registro.json` | registro de modelos |
| `var/estado/auditoria.jsonl` | trilha de auditoria |
| `var/estado/feedback.jsonl` | feedback agregado |
| `var/mlflow/mlflow.db` | rastreamento SQLite |
| `var/relatorios/` | dicionário JSON, saúde, gates e auditoria |

### Features e dados

| Grupo de features | Features |
| --- | ---: |
| faltas | 10 |
| saidas | 5 |
| coletivo | 5 |
| estrutura | 8 |
| perfil | 3 |
| calendario | 10 |
| mec | 4 |
| ordinais | 2 |

As onze tabelas do contrato são escolas, series, turmas, horarios, alunos, frequencias, faltas, saidas, entradas, feriados e contexto_mec. A pasta `verdade_oculta/` fica fora do contrato.

### Variáveis de ambiente

| Variável | Padrão | Papel |
| --- | --- | --- |
| `FREQUENCIA_WORKSPACE` | raiz do repositório | onde fica `var/` |
| `FREQUENCIA_MLFLOW_URI` | SQLite em `var/mlflow/mlflow.db` | rastreamento |
| `FREQUENCIA_SEMENTE` | `20261018` | semente global |
| `FREQUENCIA_PERFIL` | `padrao` | perfil de ambiente |
| `FREQUENCIA_FUSO` | `America/Fortaleza` | fuso |

### Vocabulário mínimo

| Termo | Significado |
| --- | --- |
| aluno-dia | unidade de previsão, uma linha por estudante e dia de referência |
| F, FJ, S, P | falta, falta justificada, saída parcial e presença; vazio é ausência de chamada |
| ponto-in-tempo | snapshot do diário como visível em um instante |
| purga | intervalo entre treino, validação e teste do tamanho do horizonte |
| OOF | previsão fora da dobra, usada para calibrar e destilar |
| ECE | erro esperado de calibração |
| conformal | intervalo de predição com cobertura mínima por grupo |
| PSI | índice de estabilidade populacional, usado para drift |
| histerese | alerta liga após dois dias acima do limiar de entrada e desliga abaixo do limiar de saída |

## Armadilhas que mudam a decisão

- O ciclo completo termina mesmo com gates reprovados. Leia `gates.json` e confira `aprovado` antes de qualquer promoção.
- `publicacao reverter` remove a versão atual antes de validar a anterior. Confirme a versão anterior no canal antes do rollback.
- `empacotamento homologacao` não pula estados. A sequência válida é experimental, candidato, homologado.
- `marcar-producao` só altera o registro. Não copia arquivos para o canal.
- `privacidade bloquear` só registra auditoria. O bloqueio efetivo é `privacidade validar-entrada-treino`.
- O presidio só roda em `privacidade verificar-sensiveis`. Para dados institucionais, rode as duas verificações.
- `pseudonimizar` reescreve CSVs e deixa os hashes do `meta.json` desatualizados. Reimporte o pacote.
- `experimentos criar` grava configuração, mas `experimentos executar` recebe os parâmetros por flags.
- `monitoramento recalibrar` atualiza só a calibração. Reavalie, reexporte e reempacote.
- `empacotamento montar` usa cartão mínimo e sem contexto MEC. Para publicação, prefira o ciclo completo.
- `features gerar-dicionario` gera JSON. O Markdown é regenerado por `make dicionario`.
- `dados importar` copia o pacote para `var/dados/importados`. Use o caminho do manifesto na etapa seguinte.
- `ponto_no_tempo atual` serve para avaliação retrospectiva, nunca para treino.
- Flags globais vêm antes do grupo: `frequencia --json dados validar ...`.
- `--perfil` tem três significados: ambiente global, volume do sintético e filtro de escola no dataset.
- Caminhos relativos resolvem pelo diretório corrente, não pelo workspace.
- Python 3.12 é obrigatório. O host com 3.15 não serve.
- `bash scripts/*.sh` e `make` exigem bash. No Windows, prefira Docker.
- A guarda editorial reprova travessão, meia-risca, reticências tipográficas, aspas curvas e setas fora de cercas.
- `dados versionar` depende do DVC e do formato do `.dvc`. Confira o hash e, se falhar, use `dados registrar-hash`.

## Verificação antes de concluir

- [ ] O modo foi anunciado e a tarefa está no escopo correto.
- [ ] Docker foi usado, ou o fallback venv com Python 3.12 foi registrado.
- [ ] O portão de privacidade está verde, quando há dados institucionais.
- [ ] O dataset passou em `validar-ausencia-futuro`.
- [ ] O experimento concluiu as sete etapas e tem `estado.json`.
- [ ] `avaliacao validar-gates` foi lido e `aprovado` é verdadeiro.
- [ ] `exportacao testar-sinteticos` tem divergência zero.
- [ ] `empacotamento validar` confirma hashes e manifesto.
- [ ] A publicação tem aprovação registrada, compatibilidade e rollback.
- [ ] A auditoria mostra as ações com ator e papel.
- [ ] Nenhum dado pessoal real aparece em logs, relatórios ou artefatos.
- [ ] Todo comando em documentação está em bloco de código bash.

## Referências sob demanda

| Documento | Quando ler |
| --- | --- |
| `references/comandos.md` | Antes de montar qualquer sequência de comandos |
| `references/playbooks.md` | Ao executar um fluxo operacional completo |
| `references/engenharia.md` | Ao interpretar métricas, gates, calibração, fairness ou reprodutibilidade |
| `references/governanca.md` | Antes de promover, publicar, reverter, revogar ou auditar |
| `references/pesquisa.md` | Ao propor, protocolar ou validar uma ideia nova |
| `AGENTS.md` | Antes de alterar código, testes, workflows ou contratos |
| `CONTRIBUTING.md` | Antes de abrir issue, pull request ou release |
| `docs/mlops.md` | Para o racional do ciclo de treino e avaliação |
| `docs/modelo-de-dados.md` | Para as onze tabelas e a derivação das marcas |
| `docs/dicionario-de-features.md` | Para as 47 features e seus vocabulários |
| `docs/contrato-de-inferencia.md` | Para a entrada e a saída de `modelo.prever` |
| `docs/contrato-de-manifesto.md` | Para os campos e a validação do `manifest.json` |
| `docs/publicacao-de-modelos.md` | Para gates, promoção, publicação e rollback |
| `docs/retreinamento-e-recalibracao.md` | Para sinais, cadência e decisão de retreinar |
| `docs/privacidade-lgpd.md` | Para LGPD, PII e resposta a incidente |
| `docs/ciencia-e-inovacao.md` | Para o método científico e o funil de inovação |
| `docs/guia-do-cientista.md` | Para a versão humana do processo de pesquisa |
| `docs/guia-da-coordenacao.md` | Para a versão humana do uso do indicador na escola |
