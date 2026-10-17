# ADR-004: pandera para validação de esquemas

## Estado

Aceita.

## Contexto

O pipeline consome pacotes de dados de três origens (sintética, MEC e institucional) e precisa barrar esquema quebrado antes de qualquer computação, com mensagens de erro acionáveis em português. O briefing offerceu pandera ou great_expectations. O caminho de dados já é polars, e a validação roda em cada importação e em cada teste de dados.

## Decisão

- pandera 0.34 com o backend polars (`pandera.polars.DataFrameSchema`) valida as onze tabelas do domínio: escolas, séries, turmas, alunos, horários, frequências, faltas, saídas, entradas, feriados e contexto MEC.
- Colunas nullable recebem checagens por argumento nomeado `checks=` (o backend polars rejeita checagem posicional após kwargs).
- A unicidade composta (uma frequência por turma e dia, uma saída e uma entrada por aluno e dia) é verificada em código com `n_unique`, porque a checagem `unique_combination_of_columns` do pandera não existe no backend polars 0.34.
- Campos proibidos (cpf, telefone, e-mail, matrícula e afins) são barrados antes da validação de esquema, com erro próprio.

## Consequências

- A validação é declarativa, legível e roda em milissegundos sobre os volumes do domínio.
- Uma quebra de esquema vira mensagem curta com a coluna e a regra violadas, sem stack trace.
- Se uma checagem composta nativa chegar ao backend polars no futuro, o código pode trocar a verificação manual sem mudar contrato.

## Alternativas consideradas

- great_expectations: suíte rica e painéis, porém dependência pesada e fluxo orientado a projeto para o que aqui é validação de esquema pontual.
- Checagens manuais em polars puro: perderia a declaração formal do contrato de dados e a mensagem de erro estruturada.
