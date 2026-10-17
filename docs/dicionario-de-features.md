# Dicionário de features

Versão do catálogo: 1.0.0. Fonte da verdade: `src/frequencia/features/catalogo.py`; este documento é gerado a partir dele para leitura humana. Toda feature documenta nome, tipo, janela, origem, sensibilidade, dependência de configuração do FrequenciApp e valor padrão quando o dado não existe no app.

## Como ler

- **Tipo**: numerico (contagem, fração ou índice), binario (flag 0 ou 1) ou ordinal (código de catálogo mapeado em índice fixo).
- **Janela**: quantidade de dias letivos considerada; soma parcial quando o histórico é menor que a janela.
- **Padrão**: valor assumido na inferência quando o app não tem o dado; nunca nulo no modelo.
- **Dependência**: flag do FrequenciApp que precisa estar ligada para a feature ter sentido pleno; com a flag desligada o valor cai no padrão e o manifesto declara confiabilidade reduzida.

## Grupo faltas

Histórico de faltas do aluno em janelas letivas.

| Feature | Amigável | Tipo | Unidade | Janela | Origem | Padrão | Dependência |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `faltas_7d` | Faltas nos últimos 7 dias letivos | numerico | dias | 7d | app | 0.0 |  |
| `faltas_14d` | Faltas nos últimos 14 dias letivos | numerico | dias | 14d | app | 0.0 |  |
| `faltas_30d` | Faltas nos últimos 30 dias letivos | numerico | dias | 30d | app | 0.0 |  |
| `faltas_consecutivas` | Faltas consecutivas até a referência | numerico | dias | nenhuma | app | 0.0 |  |
| `faltas_justificadas_30d` | Faltas justificadas em 30 dias | numerico | dias | 30d | app | 0.0 |  |
| `proporcao_fj_30d` | Proporção de faltas justificadas | numerico | fração | 30d | app | 0.0 |  |
| `dias_desde_ultima_falta` | Dias letivos desde a última falta | numerico | dias | nenhuma | app | 30.0 |  |
| `media_movel_faltas_7d` | Média móvel de faltas (7 dias) | numerico | faltas/dia | 7d | app | 0.0 |  |
| `taxa_infrequencia_30d` | Taxa de infrequência em 30 dias | numerico | fração | 30d | app | 0.0 |  |
| `presencas_parciais_30d` | Presenças parciais (S) em 30 dias | numerico | dias | 30d | app | 0.0 | frequencia_por_aula |

## Grupo saidas

Saídas antecipadas e entradas atrasadas recentes.

| Feature | Amigável | Tipo | Unidade | Janela | Origem | Padrão | Dependência |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `saidas_30d` | Saídas antecipadas em 30 dias | numerico | registros | 30d | app | 0.0 | saida_antecipada |
| `saidas_7d` | Saídas antecipadas em 7 dias | numerico | registros | 7d | app | 0.0 | saida_antecipada |
| `dias_desde_ultima_saida` | Dias letivos desde a última saída | numerico | dias | nenhuma | app | 30.0 | saida_antecipada |
| `entradas_atrasadas_30d` | Entradas atrasadas em 30 dias | numerico | registros | 30d | app | 0.0 | saida_antecipada |
| `entradas_atrasadas_7d` | Entradas atrasadas em 7 dias | numerico | registros | 7d | app | 0.0 | saida_antecipada |

## Grupo coletivo

Relatividade frente à turma e à série no mesmo dia.

| Feature | Amigável | Tipo | Unidade | Janela | Origem | Padrão | Dependência |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `media_faltas_turma_7d` | Média de faltas da turma (7 dias) | numerico | dias | 7d | app | 0.0 |  |
| `desvio_faltas_turma_7d` | Desvio do aluno frente à turma | numerico | dias | 7d | app | 0.0 |  |
| `percentil_faltas_turma_30d` | Posição do aluno na turma | numerico | percentil | 30d | app | 0.5 |  |
| `taxa_infrequencia_turma_7d` | Taxa de infrequência da turma | numerico | fração | 7d | app | 0.0 |  |
| `desvio_relativo_serie_30d` | Desvio relativo frente à série | numerico | fração | 30d | app | 0.0 |  |

## Grupo estrutura

Cobertura de chamada, matrícula e vínculo com a turma.

| Feature | Amigável | Tipo | Unidade | Janela | Origem | Padrão | Dependência |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `dias_com_chamada_30d` | Dias com chamada registrada em 30 dias | numerico | dias | 30d | app | 0.0 |  |
| `cobertura_chamada_7d` | Cobertura de chamada em 7 dias | numerico | fração | 7d | app | 0.0 |  |
| `chamada_realizada_no_dia` | Chamada do dia de referência realizada | numerico | binário | nenhuma | app | 0.0 |  |
| `historico_dias` | Dias letivos de histórico do aluno | numerico | dias | nenhuma | app | 0.0 |  |
| `aluno_novo` | Aluno matriculado há menos de 30 dias | numerico | binário | nenhuma | app | 0.0 |  |
| `transferencia_recente` | Transferência nos últimos 30 dias letivos | numerico | binário | nenhuma | app | 0.0 |  |
| `dias_na_turma_atual` | Dias letivos na turma atual | numerico | dias | nenhuma | app | 0.0 |  |
| `historico_insuficiente` | Histórico abaixo do mínimo de treino | numerico | binário | nenhuma | app | 0.0 |  |

## Grupo perfil

Flags do perfil de recursos da escola.

| Feature | Amigável | Tipo | Unidade | Janela | Origem | Padrão | Dependência |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `perfil_chamada_por_aula` | Escola com chamada por aula ligada | numerico | binário | nenhuma | app | 0.0 |  |
| `perfil_saida_antecipada` | Escola com saídas antecipadas ligadas | numerico | binário | nenhuma | app | 0.0 |  |
| `perfil_origem_na_chamada` | Escola com origem na chamada ligada | numerico | binário | nenhuma | app | 0.0 |  |

## Grupo calendario

Sazonalidade e calendário letivo do primeiro dia do horizonte.

| Feature | Amigável | Tipo | Unidade | Janela | Origem | Padrão | Dependência |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `dia_semana_seno` | Dia da semana (seno) | numerico | adimensional | nenhuma | calendario | 0.0 |  |
| `dia_semana_cosseno` | Dia da semana (cosseno) | numerico | adimensional | nenhuma | calendario | 0.0 |  |
| `mes_seno` | Mês (seno) | numerico | adimensional | nenhuma | calendario | 0.0 |  |
| `mes_cosseno` | Mês (cosseno) | numerico | adimensional | nenhuma | calendario | 0.0 |  |
| `semana_do_mes` | Semana dentro do mês | numerico | índice | nenhuma | calendario | 0.0 |  |
| `fase_bimestre` | Fase do bimestre | numerico | fração | nenhuma | calendario | 0.0 |  |
| `dias_ate_fim_bimestre` | Dias até o fim do bimestre | numerico | dias | nenhuma | calendario | 0.0 |  |
| `dias_desde_feriado` | Dias desde o último feriado | numerico | dias | nenhuma | calendario | 15.0 |  |
| `dias_ate_proximo_feriado` | Dias até o próximo feriado | numerico | dias | nenhuma | calendario | 15.0 |  |
| `dias_ate_fim_periodo_letivo` | Dias letivos até o fim do período | numerico | dias | nenhuma | calendario | 0.0 |  |

## Grupo mec

Contexto agregado por série das fontes do INEP.

| Feature | Amigável | Tipo | Unidade | Janela | Origem | Padrão | Dependência |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `taxa_abandono_historica` | Taxa histórica de abandono da série | numerico | fração | nenhuma | mec | 0.0 |  |
| `taxa_reprovacao_serie` | Taxa de reprovação da série | numerico | fração | nenhuma | mec | 0.0 |  |
| `distorcao_idade_serie` | Distorção idade-série | numerico | fração | nenhuma | mec | 0.0 |  |
| `ideb_serie` | IDEB da série | numerico | índice | nenhuma | mec | 0.0 |  |

## Grupo ordinais

Códigos de catálogo tratados como ordinais estáveis.

| Feature | Amigável | Tipo | Unidade | Janela | Origem | Padrão | Dependência |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `justificativa_recente` | Justificativa mais recente do aluno | ordinal | código | 30d | app | 0.0 |  |
| `momento_saida_recente` | Momento da saída mais recente | ordinal | código | 30d | app | 0.0 | saida_antecipada |

## Ordinais e vocabulários

- `justificativa_recente`: 0 é NENHUMA, 1 é D, 2 é Dat, 3 é T, 4 é Vi, 5 é CM, 6 é De, 7 é O, 8 é OUTROS.
- `momento_saida_recente`: 0 é NENHUM, 1 é aula_1, 2 é aula_2, 3 é aula_3, 4 é aula_4, 5 é aula_5, 6 é intervalo_1, 7 é intervalo_2, 8 é almoco.

Códigos raros de justificativa (LM, G, Lt, C, S) caem no índice de OUTROS; código desconhecido na inferência também. Momento de saída desconhecido cai em NENHUM. Esses agrupamentos fecham o vazamento de inferência por categoria rara, exigência do briefing.

## Dependências de configuração do FrequenciApp

- **frequencia_por_aula** (chamada por aula ligada (marca S e aulas por dia)): `presencas_parciais_30d`.
- **saida_antecipada** (área de saídas e entradas ligada): `saidas_30d`, `saidas_7d`, `dias_desde_ultima_saida`, `entradas_atrasadas_30d`, `entradas_atrasadas_7d`, `momento_saida_recente`.

## Texto livre fora do contrato

observacao, texto e motivo nunca entram como feature, em nenhuma hipótese; o detector de privacidade os varre antes do treino e o catálogo não os declara.
