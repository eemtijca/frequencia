# ADR-005: estrutura física por domínios com camadas mapeadas

## Estado

Aceita.

## Contexto

O Prompt 1 organiza o ecossistema em camadas conceituais (dados, features, pipelines, projetos, avaliação, modelos, distribuição, integração, segurança, testes e automação) e declara a estrutura de diretórios sugestiva. O Prompt 2 propõe o esqueleto físico `src/frequencia/dados/`, `features/`, `pipelines/`, `modelos/`, `distribuicao/`, `cli/` e `web/`. O critério de desempate recomenda seguir o Prompt 2 no esqueleto físico mantendo as camadas do Prompt 1 mapeadas em documentação, com camadas de projetos e integração existindo conceitualmente mesmo sem virar pastas de primeiro nível.

## Decisão

- O esqueleto físico segue o Prompt 2: `src/frequencia/` com infra, dados, privacidade, features, pipelines, modelos, distribuicao, monitoramento, integracao, cli e web.
- As camadas conceituais do Prompt 1 vivem mapeadas na tabela de docs/arquitetura.md: a camada de projetos vira a pasta `projetos/risco-infrequencia/` com cartão, problema, métricas e plano; a camada de avaliação vira o módulo `pipelines/avaliacao.py` mais os gates do experimento; a camada de automação vira scripts, Makefile, pre-commit e compose.
- Camadas transversais (infraestrutura, privacidade e monitoramento) ganham pastas próprias de primeiro nível porque têm dependências que apontam para dentro.
- A dependência entre camadas aponta para dentro: features não conhece pipelines; pipelines não conhece cli nem web.

## Consequências

- O repositório fica navegável por domínio de implementação, e o documento de arquitetura mantém o rastreio conceitual pedido pelo Prompt 1.
- A camada de projetos fica fora de `src/`, o que a torna material de documentação viva e não código.
- Avaliação transversal não é pasta separada: cada experimento grava o relatório e o mesmo módulo serve a qualquer projeto futuro.

## Alternativas consideradas

- Pastas de primeiro nível por camada do Prompt 1: espalharia responsabilidades de treino por dados, features e pipelines ao mesmo tempo.
- Estrutura plana: perderia a leitura por domínio que o Prompt 2 pede.
