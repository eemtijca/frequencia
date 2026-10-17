# ADR-014: ponto-in-tempo estrito com purga temporal

## Estado

Aceita.

## Contexto

O briefing trata vazamento temporal como portão obrigatório: correções retroativas de chamada (revisão, atualizadoEm) não podem contaminar o passado previsto, e a separação de conjuntos tem que ser estrita por tempo. O modelo de dados soberano do FrequenciApp registra o momento de criação e de atualização de cada chamada e de cada falta, e a semente sintética gera eventos com atraso de registro e correção posterior de propósito.

## Decisão

- A materialização do diário recebe um instante e só enxerga eventos conhecidos até ele: chamada existe a partir de criado_em; falta desaparece a partir de removida_em; justificativa vale pela versão vigente conforme atualizado_em.
- O dataset padrão usa ponto-in-tempo estrito: para cada dia de referência D, as features vêm do snapshot do fim de D e o rótulo vem dos sete dias letivos seguintes no estado final observado.
- A separação treino, validação e teste divide os dias por ordem temporal com faixas de purga do tamanho do horizonte: os dias de purga são descartados, porque os rótulos deles atravessariam a fronteira.
- A verificação por reconstrução (comando datasets validar-ausencia-futuro) reprocessa uma amostra de linhas com o diário truncado no dia de referência e confere igualdade exata de features.

## Consequências

- O teste de ausência de futuro passa com divergência zero na amostra, e os eventos retroativos da semente (chamada salva no dia seguinte, justificativa adicionada depois, falta removida) exercitam o caminho de verdade.
- Treino e validação nunca compartilham rótulo por causa da purga; o custo é perder cerca de duas semanas de dias de referência nas fronteiras, aceitável no volume do domínio.
- A opção ponto_no_tempo atual existe para diagnóstico e comparação, documentada como fora do contrato de treino.

## Alternativas consideradas

- Snapshot único do estado final: vazaria correção retroativa nas features, exatamente o ponto cego 4.
- Separação aleatória por linha: vazamento direto de futuro entre treino e teste.
