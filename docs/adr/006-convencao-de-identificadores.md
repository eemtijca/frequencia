# ADR-006: convenção híbrida de identificadores

## Estado

Aceita.

## Contexto

Os prompts divergem em idioma de identificadores: o Prompt 1 pede português brasileiro em tudo e mantém nomes de arquivo, variáveis de ambiente, comandos e identificadores técnicos em inglês, enquanto o Prompt 2 pede variáveis de domínio em português com sintaxe e bibliotecas em inglês. O critério de desempate sugere o híbrido: domínio em português (taxa_infrequencia, dias_letivos, colunas de dataset, chaves de manifesto) e técnico em inglês (módulos, classes, funções utilitárias, variáveis de ambiente, comandos CLI). A convenção do FrequenciApp de referência é nomes de domínio em português e termos de infraestrutura consagrados em inglês.

## Decisão

A convenção adotada, explícita em README e CONTRIBUTING:

- **Português brasileiro**: colunas de dataset, nomes de features, chaves do manifest.json, grupos e subcomandos da CLI (dados, privacidade, gerar-sintetico, validar-gates), páginas do painel, docstrings e comentários, mensagens de erro e saídas para humanos.
- **Inglês consagrado**: nomes de variáveis de ambiente (FREQUENCIA_WORKSPACE), artefatos de infraestrutura (Dockerfile, docker-compose.yml), nomes de arquivo de protocolo (manifest.json, modelo.js, fallback.js), termos técnicos de ferramentas (Service Worker, PWA, ONNX) e identificadores de biblioteca exigidos por contrato externo (run_id do MLflow, por exemplo).
- **Módulos de domínio** recebem nomes em português (dados, features, pipelines, privacidade), herdados do esqueleto do Prompt 2; **classes e funções utilitárias puramente técnicas** podem usar inglês quando o nome é de vocabulário de infraestrutura, e funções de caso de uso de domínio usam português (gerar, construir, exportar, montar).
- O nome do pacote e do comando CLI é `frequencia`, conforme correção do mantenedor sobre o nome do repositório.

## Consequências

- O vocabulário de domínio lê-se igual na CLI, no manifesto, no banco de dados do app e na documentação, o que reduz atrito na fronteira entre equipes.
- Identificadores de protocolo estável ficam em inglês onde o ecossistema externo espera (variáveis de ambiente, arquivos de runtime), evitando surpresas de codificação.
- A guarda editorial garante tom e caracteres, e o teste de cabeçalho garante contexto em português em cada arquivo.

## Alternativas consideradas

- Tudo em inglês: perderia o alinhamento de vocabulário com o FrequenciApp e o briefing de língua.
- Tudo em português: criaria nomes de variáveis de ambiente e nomes de arquivo exóticos para ferramentas do ecossistema.
