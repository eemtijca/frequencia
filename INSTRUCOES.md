# Instruções de execução

Guia direto para o engenheiro que recebe este repositório: como executar o ciclo completo em poucos minutos, em venv e em Docker, e onde encontrar cada camada. Todo o fluxo abaixo usa apenas dados sintéticos, sem dado pessoal real.

## Pré-requisitos

- Python 3.12 (obrigatório) e Node.js 20 ou superior (executa o teste de paridade do modelo.js no navegador-alvo simulado).
- Docker com Compose para o caminho containerizado, opcional ao caminho venv.
- Espaço de disco: cerca de 2 GB para o venv completo.

## Caminho venv (validado ponta a ponta)

```bash
cp .env.example .env
bash scripts/setup.sh
bash scripts/smoke.sh
```

O que o smoke.sh faz, na ordem:

1. Gera o pacote sintético (perfil fumaca: 2 escolas, 4 turmas, 100 alunos, cerca de 90 dias letivos) em `var/dados/sinteticos/smoke`.
2. Valida o esquema das onze tabelas com pandera e roda o portão de privacidade (detector de PII com regras próprias e presidio).
3. Constrói o dataset temporal em `var/dados/processados/smoke` com ponto-in-tempo estrito e separação treino, validação e teste com purga.
4. Executa o ciclo completo do experimento em `var/artefatos/experimentos/smoke`: treino com MLflow, ensemble de sete membros com validação fora da dobra, calibração de Platt com conformal, destilação, avaliação com subgrupos e fairness, exportação do modelo.js e empacotamento com manifesto.
5. Confere os gates de promoção (AUC, ECE, cobertura conforme, taxa de alerta, tamanho em bytes e latência).
6. Verifica a ausência de futuro numa amostra do dataset por reconstrução.
7. Executa os casos sintéticos no Node e compara com a saída Python: paridade exata, com latência média por previsão.
8. Roda a suíte pytest completa (68 testes).

Tempo esperado em uma máquina comum: 3 a 5 minutos.

### Comandos essenciais no venv

```bash
source .venv/bin/activate
frequencia --help                          # visão geral da CLI
frequencia dados gerar-sintetico --perfil padrao
frequencia datasets construir <pasta-de-dados> --versao v1
frequencia experimentos executar var/dados/processados/v1 --identificador exp1
frequencia avaliacao validar-gates var/artefatos/experimentos/exp1
frequencia exportacao testar-sinteticos var/pacotes/risco-infrequencia-<versao>
streamlit run src/frequencia/web/app.py    # painel em http://localhost:8501
```

### Onde fica cada coisa

| Camada | Pasta |
| --- | --- |
| Código-fonte do motor | `src/frequencia/` com infra, dados, privacidade, features, pipelines, modelos, distribuicao, monitoramento, integracao, cli e web |
| Amostra sintética versionada | `dados/sinteticos/amostra/` |
| Dados, artefatos, pacotes e logs de execução | `var/` (criado em tempo de execução, fora do controle de versão) |
| Experimentos e registro | `var/artefatos/experimentos/` e `var/estado/registro.json` |
| Pacotes prontos para o app | `var/pacotes/` (zip com modelo.js, fallback.js e manifest.json) |
| Publicações locais | `var/publicacoes/` |
| Documentação | `docs/` com guias e ADRs |
| Testes | `tests/` com dados, privacidade, features, pipelines, exportação, CLI, web e propriedades |

## Caminho Docker (artefato implementado, não executado aqui)

O caminho Docker é construído e validado no CI. O workflow `testes.yml` sobe o MLflow e o painel, confere a saúde dos serviços e executa o ciclo completo no container. O serviço `mlflow` usa a imagem de runtime do projeto, que já instala o MLflow do `pyproject.toml`; o serviço `smoke` usa a imagem de desenvolvimento, com Node 20 e a suíte de testes. O caminho venv continua sendo o mais rápido para o desenvolvimento local.

```bash
cp .env.example .env
docker compose up --build               # MLflow em http://localhost:5000 e painel em http://localhost:8501
docker compose --profile ciclo up smoke # roda scripts/smoke.sh dentro do contêiner
docker compose down                     # derruba os serviços
```

Serviços do compose:

| Serviço | Papel | Porta | Healthcheck |
| --- | --- | --- | --- |
| mlflow | Servidor de rastreamento com SQLite em volume | 5000 | GET /health |
| app | Painel Streamlit de governança | 8501 | GET /_stcore/health |
| smoke | Perfil de ciclo único: smoke test completo que encerra | sem porta | código de saída |

O volume `dados` compartilha `var/` entre os serviços: experimentos feitos no painel aparecem para a CLI e para o smoke, e o rastreamento do MLflow fica persistente.

## Navegando pelas interfaces

### CLI

Doze grupos com `--help` detalhado: dados, privacidade, features, datasets, experimentos, avaliacao, exportacao, empacotamento, registro, publicacao, monitoramento e auditoria. Bandeiras transversais: `--json` para scripts, `--seco` para ensaiar sem gravar, `--detalhado` para investigação, `--silencioso` para automatização, `--perfil` para ambiente, `--forca` com `--justificativa` obrigatória para reexecutar etapas concluídas, `--ator` e `--papel` para auditoria.

### Painel web

Dezesseis páginas: visão geral, dados, features, datasets, experimentos, comparação, ensemble, calibração, fairness e impacto, exportação, manifesto e pacote, registro e promoção, publicação, monitoramento, governança e privacidade e configurações. O papel é escolhido na barra lateral (observador, cientista, engenheiro, aprovador) e libera as ações correspondentes; operações longas rodam como tarefas de fundo disparando a própria CLI, com painel de tarefas na barra lateral.

### Ciclo mínimo de governança

1. Execute o experimento (CLI ou página de Experimentos).
2. Confira os gates na avaliação: todos precisam estar aprovados.
3. Promova com papel de aprovador: experimental para candidato, candidato para homologado.
4. Publique o pacote homologado: o zip vai para `var/publicacoes/` com notas e instruções.
5. Entregue o zip ao FrequenciApp: o app lê o manifest.json, confere versão mínima, validade e hash, roda os dados-teste e só então ativa.

## Solução de problemas

- **Python 3.12 ausente**: instale-o (pyenv, apt ou brew) e rode `scripts/setup.sh` de novo.
- **Node ausente**: o teste de paridade e a medição de latência pulam com aviso; instale Node 20 ou superior para a validação completa.
- **FREQUENCIA_MLFLOW_URI inválida**: o padrão cria SQLite em `var/mlflow/`; com o compose, use `http://mlflow:5000`.
- **Experimento travado**: `frequencia experimentos recuperar <id>` retoma do ponto em que parou; as etapas concluídas não reexecutam.
- **Gates reprovados com AUC baixo**: gere mais volume (`--perfil padrao`) ou confira a taxa do rótulo; o gate de AUC mínimo é 0,70 e não deve ser rebaixado sem ADR.
