# Catálogo de modelos

Modelos do ecossistema, com estados, público e situação de manutenção. O lançamento traz um único modelo generalista, conforme o princípio de não construir suíte de especialistas antes de consolidar o principal.

## Risco individual de infrequência (generalista principal)

| Aspecto | Valor |
| --- | --- |
| Identificador | risco-infrequencia |
| Unidade | aluno por dia de referência |
| Horizonte | sete dias letivos seguintes |
| Rótulo | duas ou mais faltas (F ou FJ) no horizonte, contando enquanto matriculado |
| Runtime alvo | js-m2cgen no navegador do PWA |
| Consumo | painel do dia e relatório por aluno, como indicador de apoio |
| Artefato | estudante LightGBM destilado com invólucro de confiança |
| Projeto | projetos/risco-infrequencia/ |

A definição completa (problema, métricas de sucesso, limitações, plano de retreinamento e cartão) vive no projeto. O ciclo de execução é o mesmo da CLI: `experimentos executar`.

## Estados do registro

| Estado | Significado | Saídas permitidas |
| --- | --- | --- |
| experimental | Executado com dados sintéticos, gates avaliados | candidato, descontinuado, arquivado |
| candidato | Gates aprovados, aguardando revisão | homologado, experimental, descontinuado, arquivado |
| homologado | Revisado com aprovação registrada | publicado, candidato, descontinuado, arquivado |
| publicado | No canal local de releases, versão atual | descontinuado, arquivado |
| descontinuado | Retirado por rollback, revogação ou substituição | arquivado |
| arquivado | Fora do ciclo ativo, só histórico | nenhum |

Promoção a homologado ou publicado exige papel de aprovador, e toda transição grava auditoria com ator e justificativa.

## Projetos futuros (abrir só com evidência)

| Projeto | Unidade | Gatilho de abertura |
| --- | --- | --- |
| Priorização de turmas no painel | turma | Demanda da coordenação por visão coletiva com ganho medido sobre o ordenamento por infrequência simples |
| Anomalia de turma por dia | turma-dia | Persistência de eventos coletivos invisíveis ao modelo individual |
| Risco de desistência | aluno | Alto valor e alta delicadeza: exige governança reforçada e dados institucionais autorizados |
| Fluxo de saídas e entradas | aluno-dia | Recurso de saídas amplamente ligado nas escolas e sinal complementar comprovado |

Cada projeto futuro nasce com pasta própria em projetos/ seguindo o formato do principal, com ADR registrando a decisão de abertura e a evidência que a sustenta.
