# Instruções de execução

Guia direto para quem recebe este repositório: como executar o ciclo completo em poucos minutos, com Docker como caminho padrão e o venv como fallback. Todo o fluxo usa apenas dados sintéticos, sem dado pessoal real.

## Pré-requisitos

- Docker com Compose v2, recomendado para execução, testes e validação.
- Git.
- Cerca de 2 GB de espaço livre.
- Python 3.12 e Node.js 20 ou superior apenas no caminho venv de fallback.

O host com Python 3.15 não satisfaz `requires-python` e não deve ser usado.

## Caminho Docker, recomendado

```bash
docker compose up --build -d
docker compose ps
```

O painel fica em http://localhost:8501 e o MLflow em http://localhost:5000. Aguarde os serviços aparecerem como `healthy`. Para customizar variáveis, copie `.env.example` para `.env`.

### Serviços

| Serviço | Papel | Porta | Healthcheck |
| --- | --- | --- | --- |
| `mlflow` | servidor de rastreamento com SQLite em volume | 5000 | GET /health |
| `app` | painel Streamlit de governança | 8501 | GET /_stcore/health |
| `cli` | comandos pontuais na imagem de desenvolvimento | sem porta | código de saída |
| `smoke` | ciclo completo na imagem de desenvolvimento | sem porta | código de saída |

O volume `dados` compartilha `var/` entre os serviços. Experimento feito na CLI aparece no painel e no smoke.

### Smoke completo

```bash
docker compose --profile ciclo up smoke
```

O que o smoke faz, na ordem:

1. Gera o pacote sintético (perfil fumaca: 2 escolas, 4 turmas, 100 alunos, cerca de 90 dias letivos) em `var/dados/sinteticos/smoke`.
2. Valida o esquema das onze tabelas com pandera e roda o portão de privacidade.
3. Constrói o dataset temporal em `var/dados/processados/smoke` com ponto-in-tempo estrito e separação treino, validação e teste com purga.
4. Executa o ciclo completo do experimento em `var/artefatos/experimentos/smoke`: treino com MLflow, ensemble de sete membros com validação fora da dobra, calibração de Platt com conformal, destilação, avaliação com subgrupos e fairness, exportação do modelo.js e empacotamento com manifesto.
5. Confere os gates de promoção.
6. Verifica a ausência de futuro numa amostra do dataset por reconstrução.
7. Executa os casos sintéticos no Node e compara com a saída Python.
8. Roda a suíte pytest completa.

Tempo esperado em uma máquina comum: 3 a 5 minutos. Em Docker Desktop com o repositório em OneDrive, a primeira execução pode demorar mais.

### Comandos essenciais no Docker

```bash
# Ajuda
docker compose --profile cli run --rm -T --no-deps cli frequencia --help
docker compose --profile cli run --rm -T --no-deps cli frequencia experimentos --help

# Ciclo mínimo
docker compose --profile cli run --rm cli frequencia dados gerar-sintetico --perfil padrao
docker compose --profile cli run --rm cli frequencia datasets construir <pasta-de-dados> --versao v1
docker compose --profile cli run --rm cli frequencia experimentos executar var/dados/processados/v1 --identificador exp1
docker compose --profile cli run --rm cli frequencia avaliacao validar-gates var/artefatos/experimentos/exp1
docker compose --profile cli run --rm cli frequencia exportacao testar-sinteticos var/pacotes/risco-infrequencia-<versao>

# Testes e qualidade
docker compose --profile cli run --rm -T --no-deps cli python -m pytest tests -q
docker compose --profile cli run --rm -T --no-deps cli ruff check src tests
docker compose --profile cli run --rm -T --no-deps cli mypy src/frequencia
docker compose --profile cli run --rm -T --no-deps cli ruff format --check src tests
```

### Atalhos com Makefile

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

Os alvos `make` usam Docker por padrão. Os alvos `venv-*` usam o fallback com Python 3.12.

### Inspecionar artefatos

```bash
docker compose --profile cli run --rm -T --no-deps cli ls -la var/artefatos/experimentos
docker compose --profile cli run --rm -T --no-deps cli ls -la var/pacotes
docker compose exec app ls -la /app/var/artefatos/experimentos
docker compose cp app:/app/var/pacotes ./var-pacotes
```

### Backup do volume

```bash
# Backup
docker run --rm \
  -v frequencia_dados:/dados \
  -v "$PWD":/backup \
  alpine tar czf /backup/var-docker.tar.gz -C /dados .

# Restore, com cuidado
docker run --rm \
  -v frequencia_dados:/dados \
  -v "$PWD":/backup \
  alpine sh -c "rm -rf /dados/* && tar xzf /backup/var-docker.tar.gz -C /dados"
```

Confirme o nome do volume antes do backup:

```bash
docker volume ls
```

A restauração apaga o conteúdo atual do volume.

## Caminho venv, fallback

Use apenas quando Docker não estiver disponível e houver Python 3.12.

```bash
python3.12 --version
bash scripts/setup.sh
source .venv/bin/activate
bash scripts/smoke.sh
```

No Windows, o caminho venv exige Git Bash ou WSL. O caminho Docker é o mais simples.

### Comandos essenciais no venv

```bash
source .venv/bin/activate
frequencia --help
frequencia dados gerar-sintetico --perfil padrao
frequencia datasets construir <pasta-de-dados> --versao v1
frequencia experimentos executar var/dados/processados/v1 --identificador exp1
frequencia avaliacao validar-gates var/artefatos/experimentos/exp1
frequencia exportacao testar-sinteticos var/pacotes/risco-infrequencia-<versao>
streamlit run src/frequencia/web/app.py
```

## Quando usar cada caminho

| Situação | Caminho |
| --- | --- |
| Docker disponível | Docker |
| Docker indisponível e Python 3.12 disponível | venv |
| Docker indisponível e só Python 3.15 | instalar Docker ou Python 3.12; não usar o host |

O volume `dados` do Docker é separado do `var/` local do venv. Não misture os dois sem ajustar `FREQUENCIA_WORKSPACE`.

## Onde fica cada coisa

| Camada | Pasta |
| --- | --- |
| Código-fonte do motor | `src/frequencia/` com infra, dados, privacidade, features, pipelines, modelos, distribuicao, monitoramento, integracao, cli e web |
| Amostra sintética versionada | `dados/sinteticos/amostra/` |
| Dados, artefatos, pacotes e logs de execução | `var/` (criado em tempo de execução, fora do controle de versão) |
| Experimentos e registro | `var/artefatos/experimentos/` e `var/estado/registro.json` |
| Pacotes prontos para o app | `var/pacotes/` |
| Publicações locais | `var/publicacoes/` |
| Documentação | `docs/` com guias, templates e ADRs |
| Testes | `tests/` com dados, privacidade, features, pipelines, exportação, CLI, web e propriedades |
| Skill de agentes | `.agents/skills/frequencia/` |

## Navegando pelas interfaces

### CLI

Doze grupos com `--help` detalhado: dados, privacidade, features, datasets, experimentos, avaliacao, exportacao, empacotamento, registro, publicacao, monitoramento e auditoria. Bandeiras transversais: `--json`, `--seco`, `--detalhado`, `--silencioso`, `--perfil`, `--workspace`, `--forca` com `--justificativa`, `--ator` e `--papel`.

### Painel web

Dezesseis páginas: visão geral, dados, features, datasets, experimentos, comparação, ensemble, calibração, fairness e impacto, exportação, manifesto e pacote, registro e promoção, publicação, monitoramento, governança e privacidade e configurações. O papel é escolhido na barra lateral e libera as ações correspondentes; operações longas rodam como tarefas de fundo disparando a própria CLI.

### Ciclo mínimo de governança

1. Execute o experimento.
2. Confira os gates na avaliação.
3. Promova com papel de aprovador: experimental para candidato, candidato para homologado.
4. Publique o pacote homologado.
5. Entregue o zip ao FrequenciApp.

## Solução de problemas

- **Docker ausente**: instale Docker Desktop ou Docker Engine com Compose v2; o caminho venv exige Python 3.12.
- **Python 3.12 ausente**: use Docker. O Python 3.15 do host não serve.
- **Node ausente**: a imagem de desenvolvimento já inclui Node. No venv, instale Node 20 ou superior para a paridade.
- **Porta ocupada**: pare o serviço conflitante ou ajuste a porta no `docker-compose.yml`.
- **Painel sem dados**: rode o smoke ou o ciclo pela CLI; o volume `dados` é compartilhado.
- **Volume e venv misturados**: escolha um caminho. O volume `dados` do Docker não é o `var/` local.
- **FREQUENCIA_MLFLOW_URI inválida**: no compose, use `http://mlflow:5000`; no venv, o padrão é SQLite em `var/mlflow/`.
- **Experimento travado**: etapas concluídas não reexecutam sem `--forca` com justificativa. Use o bloco de recuperação abaixo.
- **Gates reprovados**: leia `gates.json` e `avaliacao.json`; não afrouxe o gate. Gere mais volume ou investigue vazamento e subgrupos.
- **Dicionário desatualizado**: gere novamente e confira o diff com o bloco abaixo.

```bash
# Recuperar experimento interrompido
docker compose --profile cli run --rm cli frequencia experimentos recuperar <id>

# Regenerar o dicionário de features
make dicionario
```
