# ADR-017: diretrizes de ciência e inovação

## Estado

Aceita.

## Contexto

O FrequencIA já tem documentação técnica do ciclo, gates objetivos, runbooks e um registro de modelos com estados. Falta um método explícito para transformar ideias em hipóteses, hipóteses em experimentos, experimentos em evidência e evidência em decisão. Sem esse método, o risco é aceitar mudanças por entusiasmo, ajustar métricas depois de ver resultados, repetir hipóteses rejeitadas, esconder resultados negativos e confundir predição com causalidade.

O projeto também precisa diferenciar manutenção de inovação. Recalibrar, retreinar e corrigir bugs seguem o fluxo existente. Mudanças de contrato, de rótulo, de família de features, de modelo, de runtime ou de uso exigem mais evidência e revisão.

## Decisão

- Adotar as diretrizes de ciência e inovação em `docs/ciencia-e-inovacao.md`.
- Organizar a inovação em um funil de sete estágios: ideia, protocolo, offline, sombra, piloto, adoção e aprendizado.
- Separar a trilha leve, para ajustes dentro do contrato aprovado, da trilha estrutural, para mudanças de contrato ou risco.
- Exigir protocolo antes do experimento, com hipótese falsificável, métricas, limiares, splits, critério de parada e regra de decisão.
- Exigir revisão científica independente para mudanças estruturais, com rubrica própria.
- Registrar o experimento em `projetos/risco-infrequencia/experimentos/<ano-mes>-<slug>/`, com protocolo, resultados, decisão e evidências.
- Registrar resultados negativos e atualizar o portfólio em `projetos/README.md`.
- Exigir ADR para mudanças estruturais e para alteração de gates.
- Adotar o modo pesquisa na skill de agentes, com o mesmo método, separação de deveres e pacote de evidências.
- Manter a decisão final e a aprovação de promoção e publicação com pessoas, nunca com agentes.

## Consequências

- O time passa a distinguir manutenção de inovação e a dimensionar o esforço de cada uma.
- Experimento sem protocolo deixa de ser aceito como evidência.
- Resultados negativos passam a ser documentados e reaproveitados.
- A revisão científica adiciona uma etapa, mas reduz retrabalho e decisões por entusiasmo.
- O portfólio em `projetos/README.md` passa a ser a visão viva das iniciativas.
- A skill de agentes ganha um modo pesquisa, com regras de isolamento e separação de deveres.
- O custo de documentação aumenta para mudanças estruturais; os templates reduzem o esforço.
- Gates continuam obrigatórios e não podem ser afrouxados para uma ideia passar.

## Alternativas consideradas

- Manter apenas os gates técnicos: não cobre problema, hipótese, fairness, ética e impacto humano.
- Criar um comitê pesado para toda mudança: burocracia incompatível com a leveza do projeto.
- Copiar um framework genérico de MLOps: não captura os comandos, artefatos, gates e riscos específicos do FrequencIA.
- Usar ADR para todo experimento: dá peso excessivo a decisões que não mudam a arquitetura.
- Deixar a pesquisa apenas na skill de agentes: humanos também precisam do método e dos critérios de decisão.
