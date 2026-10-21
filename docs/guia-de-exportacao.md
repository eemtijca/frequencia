# Guia de exportação do FrequenciApp

Como preparar uma exportação autorizada do aplicativo para uso no treino do FrequencIA. Este guia é para a equipe da escola que opera o FrequenciApp; o lado do FrequencIA está em docs/mlops.md.

## Princípios

- A exportação sai do app por vontade da escola, com base legal registrada; o FrequencIA nunca puxa dados do app.
- O conteúdo segue o modelo de dados soberano: frequências com data de salvamento, faltas por aula com justificativa de catálogo, saídas e entradas com momento e autoria.
- Texto livre (observação, texto de saída, motivo de entrada) pode vir na exportação para conferência, mas o portão de privacidade do FrequencIA o varra e o bloqueia se contiver dado pessoal; o treino nunca o consome.
- O identificador de aluno na exportação é o id interno do app; nomes podem vir para conferência da escola e são pseudonimizáveis antes de qualquer uso.

## Passo a passo

1. Na área de exportação do FrequenciApp, gere o pacote do período desejado no formato de tabelas (CSV por entidade).
2. Reúna os arquivos numa pasta com os nomes esperados: escolas, series, turmas, alunos, horarios, frequencias, faltas, saidas, entradas, feriados e contexto_mec (este último vem do FrequencIA, não do app).
3. Registre a base legal do tratamento (por exemplo, execução de política pública ou obrigação legal) para uso na importação.
4. Importe no FrequencIA. Os comandos usam Docker; no fallback venv, troque o prefixo Docker por `frequencia`:

```bash
docker compose --profile cli run --rm cli frequencia dados importar \
  <pasta> \
  --origem institucional \
  --base-legal execucao-de-politica-publica \
  --licenca "uso institucional autorizado"
```

5. O portão de privacidade roda na importação e de novo antes do treino; qualquer achado de PII bloqueia com mensagem indicando tabela e campo.
6. Para reduzir a exposição, aplique a pseudonimização determinística antes do treino:

```bash
docker compose --profile cli run --rm cli frequencia privacidade pseudonimizar \
  <pasta> \
  --colunas nome
```

## Campos que interessam ao modelo

| Grupo | Campos do app |
| --- | --- |
| Frequência | dia, turma, revisão, criado_em, atualizado_em, faltas por aluno e aula com justificativa |
| Saídas | dia, momento, horário, justificativa de catálogo, quem liberou |
| Entradas | dia, horário, momento, responsável |
| Estrutura | séries, turmas, turma de origem, horários ativos, desistências e transferências |

O campo criado_em de cada chamada é essencial para o ponto-in-tempo: sem ele, o FrequencIA trata o pacote como estado final e só serve para avaliação retrospectiva, não para treino sem vazamento (ADR-14).

## O que nunca deve ser exportado

- CPF, telefone, e-mail, endereço ou matrícula de qualquer pessoa.
- Textos livres com diagnóstico, laudo ou detalhe clínico: o catálogo de justificativas existe justamente para evitar isso.
- Dados de alunos desativados além do necessário para o histórico de frequência da época ativa.

## Verificação

Após a importação, rode o perfil e o relatório de risco:

```bash
docker compose --profile cli run --rm cli frequencia dados gerar-perfil <pasta>
docker compose --profile cli run --rm cli frequencia privacidade relatorio-risco \
  <pasta> \
  --base-legal <base>
```

O relatório de nível baixo com achados vazios é o pré-requisito para o dataset de treino.
