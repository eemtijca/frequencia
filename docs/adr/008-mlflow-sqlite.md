# ADR-008: MLflow com backend SQLite local

## Estado

Aceita.

## Contexto

O rastreamento de experimentos precisa rodar local, sem servidor externo e sem credenciais, tanto no venv quanto no Docker Compose. Na validação do stack, o mlflow 3.17 recusou o file store clássico: o backend de arquivos entrou em modo manutenção e lança exceção a menos que a variável MLFLOW_ALLOW_FILE_STORE=true seja usada, com migração recomendada para banco de dados.

## Decisão

- O tracking padrão é SQLite em `var/mlflow/mlflow.db`, resolvido pela variável FREQUENCIA_MLFLOW_URI e criado sob demanda.
- A criação do experimento passa por `create_experiment` com `artifact_location` explícito em `var/mlflow/artifacts` quando a URI é local (sqlite ou file): sem isso, o MLflow 3.17 resolve o local de artefatos do experimento relativo ao diretório de trabalho e espalha `mlruns/` na raiz do projeto mesmo com tracking em SQLite. Com URI http, o experimento é criado sem local explícito e os artefatos seguem o destino do servidor (`--artifacts-destination` no compose).
- O Docker Compose sobe um serviço dedicado `mlflow server` com backend SQLite e artefatos em volume compartilhado, apontado pelo serviço do painel via http://mlflow:5000.
- O registro do experimento loga parâmetros, métricas e o artefato do modelo; falha de rastreamento nunca derruba o treino: o evento vira aviso no log estruturado e a execução continua com run identificado como sem-rastreamento.

## Consequências

- A suíte de testes roda sem servidor: o cliente MLflow conversa com SQLite por URI de arquivo, e o experimento de smoke cria o banco no workspace temporário.
- No compose, o painel e a CLI compartilham o mesmo servidor e o histórico sobrevive a reinícios pelo volume.
- O servidor do compose só aceita os `Host` listados em `--allowed-hosts` (`mlflow:5000`, `localhost:5000` e `127.0.0.1:5000`), proteção do MLflow 3 contra DNS rebinding. Como a falha de rastreamento é silenciosa por desenho, um host faltando faz o ciclo rodar sem registrar nada; o teste `tests/infra/test_compose.py` confere que todo cliente do compose usa um host liberado.
- Backup do histórico é cópia de arquivo (mlflow.db mais a pasta de artefatos), sem infraestrutura adicional.

## Alternativas consideradas

- Manter file store com a variável de escape: funcionaria, porém contra o caminho recomendado pelo fornecedor e sem ganho.
- Backend PostgreSQL dedicado no compose: peso adicional para um rastreamento de equipe pequena; a troca é só a URI se o volume crescer.
