# ADR-011: verdade oculta no gerador sintético

## Estado

Aceita.

## Contexto

Sem dados reais no repositório, a avaliação do modelo precisa de sinal aprendível e de referência de qualidade. Um gerador puramente aleatório não ensina nada ao modelo; um gerador que expõe a causa direta do rótulo vaza a resposta. O briefing pede ground truth oculto para treinar modelos de risco com base em padrões históricos simulados.

## Decisão

- Cada aluno sintético nasce com propensão latente (crônicos em cerca de 8%, com propensão entre 0,12 e 0,19; episódicos com propensão quadrática baixa), perfil de justificativa, perfil de saída e perfil de entrada, tudo derivado da semente.
- O comportamento diário mistura a propensão latente com sazonalidade (dia da semana, mês, véspera de feriado), persistência de sequência (0,55 para crônicos e 0,35 para episódicos) e correções retroativas (justificativa adicionada depois, falta removida, chamada salva com atraso).
- A tabela `verdade_oculta/verdade_oculta.csv` guarda a propensão e os perfis por aluno e fica FORA das tabelas do contrato: nunca entra como feature, e a validação de esquema e os testes confirmam o isolamento.
- O rótulo do dataset continua derivado do comportamento observado (duas ou mais faltas nos próximos sete dias letivos), não da propensão: o modelo aprende o comportamento, e a verdade oculta serve para avaliar ordenação (correlação entre risco previsto e propensão latente) em análises da camada de avaliação.

## Consequências

- O sinal é aprendível de verdade: o ensemble do smoke test alcança AUC perto de 0,72 fora da dobra e o estudante destilado acima de 0,75 no teste, com prevalência realista de rótulo em torno de 13 a 22%.
- A correlação entre previsão e propensão latente dá métrica de sanidade independente do rótulo observado.
- Qualquer uso da verdade oculta em treino seria pego pelos testes de contrato e pelo teste que varre colunas.

## Alternativas consideradas

- Rótulo direto da propensão (classificação da causa): vazamento puro, inviável.
- Gerador sem latente (ruído puro): sem sinal, sem avaliação significativa.
