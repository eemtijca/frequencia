# ADR-001: uso de polars como motor de dados

## Estado

Aceita.

## Contexto

O pipeline precisa computar janelas deslizantes, agregações por grupo (aluno, turma, série e dia) e junções sobre tabelas de frequência, com volumes que vão de milhares de linhas no smoke test a milhões no uso real. O pandas 3.0 mantém APIs que o ecossistema espera, mas o custo por linha nas operações de janela e a fragmentação de índices pesam no ciclo de construção de dataset, que roda uma vez por dia de referência. O briefing do Prompt 2 indica polars pela performance e avaliação preguiçosa, e o critério de desempate recomenda seguir o Prompt 2 em questões de stack.

## Decisão

- polars 2.0 é o motor primário de dados: diário ponto-in-tempo, features, dataset, ensamblagem e drift usam DataFrames e expressões polars.
- pandas 3.0 permanece no ambiente para bibliotecas que o exigem (skl2onnx, onnxmltools e ferramentas do ecossistema sklearn), mas não entra no caminho quente.
- As expressões usam `over` para janelas por grupo e `rolling_sum` com `min_samples=1`, o que dá soma parcial no começo do histórico, coerente com a leitura natural de janela de últimos N dias letivos.
- A migração para polars 2.0 incorporou as quebras conhecidas: `min_periods` renomeado para `min_samples` e leitura eager delegada ao motor de fluxo.

## Consequências

- O cálculo de features do smoke test (94 dias de referência, cerca de 8 mil linhas) roda em segundos, e o perfil padrão escala linearmente.
- O time precisa dominar o vocabulário de expressões polars; o ganho é código declarativo e sem loops por aluno.
- O formato intermediário é parquet nativo, sem dependência de pyarrow no caminho de leitura e gravação do pipeline.

## Alternativas consideradas

- pandas puro: interoperável, porém mais lento nas janelas por grupo e com índice emaranhado no caminho quente.
- DuckDB via consultas SQL: forte para agregações, porém a lógica de marcas e janelas por aluno fica espalhada em texto SQL de difícil teste de propriedade.
- pyarrow puro: rápido, porém verboso demais para a derivação de marcas e janelas.
