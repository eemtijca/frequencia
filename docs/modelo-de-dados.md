# Modelo de dados

Esquema sintético usado pelo FrequencIA, fiel ao modelo soberano do FrequenciApp (`docs/modelo-de-dados.md` do aplicativo). Este documento descreve as onze tabelas do contrato, a derivação da marca e o mapeamento com os dados reais exportados pelo app.

## Fonte da verdade

O documento de dados do FrequenciApp é soberano sobre semântica: a marca S é evento de ruptura de fluxo, célula vazia é ausência de frequência (nunca presença), uma chamada por turma e dia com revisão otimista, saída e entrada únicas por aluno e dia, catálogos com código estável. O gerador sintético e o diário do FrequencIA reproduzem essas regras, e os testes de dados as verificam.

## Tabelas do contrato

### Escolas

| Campo | Tipo | Observação |
| --- | --- | --- |
| escola_id | texto | Identificador sintético estável. |
| nome | texto | Nome claramente sintético. |
| frequencia_por_aula | booleano | Perfil: liga chips de aula e a marca S. |
| saida_antecipada | booleano | Perfil: liga a área de saídas e entradas. |
| origem_na_chamada | booleano | Perfil: liga a indicação de origem. |

### Séries, turmas e horários

| Tabela | Campos | Observação |
| --- | --- | --- |
| series | serie_id, escola_id, nome, ordem | Organiza as turmas por ano. |
| turmas | turma_id, serie_id, escola_id, nome | Letra ou rótulo curto. |
| horarios | horario_id, turma_id, ordem, inicio, fim, dias_semana, ativo | Grade da turma; escolas sem chamada por aula têm uma única aula padrão. |

### Alunos

| Campo | Tipo | Observação |
| --- | --- | --- |
| aluno_id | texto | Identificador sintético; nunca CPF ou matrícula. |
| nome | texto | Nome sintético do tipo Estudante NNNN. |
| turma_id | texto | Turma atual; origem da frequência diária. |
| turma_original_id | texto | Turma de origem para consulta agrupada. |
| ordem | inteiro | Ordem de apresentação na turma. |
| ativo | booleano | Desativado sai das chamadas futuras. |
| desistente_em | data | Desistência preserva histórico e para as marcas. |
| transferido_em | data | Momento da transferência entre turmas. |
| criado_em | data | Matrícula; base do aluno novo. |

### Frequências, faltas e listas

| Tabela | Campos | Observação |
| --- | --- | --- |
| frequencias | frequencia_id, turma_id, dia, revisao, criado_em, atualizado_em | Uma por turma e dia; criado_em pode ser posterior ao dia (chamada salva com atraso). |
| faltas | falta_id, frequencia_id, aluno_id, horario_id, justificativa, justificativa_inicial, observacao, criado_em, atualizado_em, removida_em | Presença é implícita; justificativa_inicial guarda o valor de criação e removida_em marca correção retroativa. |

### Saídas, entradas, feriados e contexto

| Tabela | Campos | Observação |
| --- | --- | --- |
| saidas | saida_id, aluno_id, turma_id, dia, momento, horario, justificativa, texto, liberado_por_codigo, criado_em | Momento de aula_1 a aula_5, intervalo_1, intervalo_2 e almoco. |
| entradas | entrada_id, aluno_id, turma_id, dia, horario, momento, motivo, responsavel_codigo, criado_em | Momento de aula_1, aula_2 ou pausa. |
| feriados | dia, nome, origem | Base do calendário letivo. |
| contexto_mec | serie_id, taxa_abandono_historica, taxa_reprovacao, distorcao_idade_serie, ideb | Agregados por série, no formato das fontes do INEP. |

### Verdade oculta

A pasta `verdade_oculta/` guarda, por aluno, a propensão latente e os perfis de comportamento que dirigem a simulação. Ela fica fora do contrato de dados: nunca entra como feature, e a avaliação usa só para métricas de sanidade.

## Derivação da marca no diário

O diário materializa uma linha por aluno e dia letivo, com a marca conforme o documento soberano, computada no instante pedido (ponto-in-tempo):

1. **FJ** quando todas as faltas do dia têm justificativa do catálogo (versão vigente no instante).
2. **F** quando o aluno falta em todas as aulas do dia sem justificativa completa.
3. **S** quando falta em parte das aulas e esteve presente no restante; só no modo por aula.
4. **P** quando estava na lista de uma chamada daquele dia e não há falta.
5. **Vazia** quando não havia chamada visível no instante: ausência de frequência, nunca presença.

O modo por aula define o número de aulas da turma; escolas sem o recurso têm uma aula única e nunca geram marca S.

## Mapeamento com exportações do FrequenciApp

| Tabela do FrequencIA | Origem no app |
| --- | --- |
| escolas, series, turmas | Cadastro e Configuracao (frequenciaPorAula, saidaAntecipada, origemNaChamada). |
| alunos | Aluno com turmaId, turmaOriginalId, desistenteEm e criadoEm. |
| horarios | Horario ativo por turma. |
| frequencias | Frequencia com dia, revisao, criadoEm e atualizadoEm. |
| faltas | Falta por aluno e aula; a coluna justificativa_inicial não existe no app e nasce nula na importação (o histórico real de correção é o atualizado_em). |
| saidas | SaidaAntecipada com momento, justificativa e liberadoPorCodigo. |
| entradas | EntradaAtrasada com horario, momento e responsavel. |
| feriados | Feriado com dia e nome. |
| contexto_mec | Agregados por série derivados das fontes do INEP (ver guia de dados do MEC). |

## Catálogos

Justificativas com código estável: D, Dat, LM, G, T, Vi, CM, De, Lt, O, C, S. Códigos raros (LM, G, Lt, C, S) são agrupados em OUTROS na feature ordinal de justificativa, e código desconhecido na inferência também cai em OUTROS: o vazamento de inferência por categoria rara fica fechado. Liberadores S1 a S4. Momentos de saída e entrada conforme as tabelas acima. Texto livre (observacao, texto, motivo) nunca entra como feature, por contrato.
