# Integração com o FrequenciApp

Contrato e orientações para o lado do app consumir o pacote. Este documento não contém código do aplicativo: é orientação de produto e engenharia para a equipe do FrequenciApp.

## Mapa de features

Cada feature do contrato mapeia para os dados que o app já guarda. O mapa executável vive em `src/frequencia/integracao/contrato.py`, e a versão JSON é gerada por `gravar_contrato`; aqui vai o resumo por grupo.

| Grupo do contrato | De onde o app calcula |
| --- | --- |
| faltas | Marcas diárias derivadas das chamadas salvas (F, FJ, S por dia e por aula) |
| saidas | Registro de saídas antecipadas e entradas atrasadas |
| coletivo | Mesmas marcas dos colegas de turma e da série no dia |
| estrutura | Cadastro (matrícula, transferência, desistência) e cobertura de chamadas |
| perfil | Configuração da escola (chamada por aula, saídas, origem) |
| calendario | Feriados da escola e período letivo |
| mec | Tabela contexto-mec.json do pacote |
| ordinais | Última justificativa de falta e último momento de saída em 30 dias |

O app computa as features no dispositivo a partir dos próprios dados: o modelo recebe só números, e nada sai do navegador.

## Recomendações de UX

- Exibir o indicador como sugestão com incerteza: probabilidade, faixa de risco e a leitura do conjunto conforme (risco, sem risco ou indefinido) quando houver espaço.
- Respeitar o estado_confianca: sem_historico e dados_insuficientes escondem o número; em_observacao mostra com o aviso curto; modelo_desatualizado suprime com a mensagem aprovada.
- Usar o vocabulário de mensagens do manifesto, sem criar frases novas na interface.
- Priorizar Top-K diário no painel em vez de limiar fixo: a capacidade da coordenação é o limite operacional real.
- O alerta com histerese liga após dois dias acima do limiar: não reler o dia anterior anula a histerese.

## Vocabulário aprovado

| Chave | Mensagem |
| --- | --- |
| risco_alto | Atenção sugerida: acompanhar este estudante na próxima semana. |
| risco_medio | Indicador moderado: vale observar nos próximos dias. |
| risco_baixo | Indicador tranquilo. |
| sem_historico | Sem histórico de chamadas para avaliar o risco. |
| dados_insuficientes | Histórico ainda curto: indicador em observação. |
| modelo_desatualizado | Modelo desatualizado: use o indicador com cautela até a atualização. |
| fallback | Indicador pelo modo de segurança de regras. |

## Plano de feature flag

1. O app libera o indicador por flag de série, desligado por padrão.
2. Primeiro mês em modo sombra: o modelo roda e nada é exibido (aquecimento com a taxa base).
3. Após a sombra, a coordenação decide a ativação por série.
4. Rollback por flag: desligar o indicador não exige release nova do app.

## Atualização atômica

O Service Worker baixa o pacote no evento de atualização, nunca durante o fluxo de chamada; confere min_app_versao, validade, hash do modelo e roda os dados-teste; só então troca o cache ativo. Falha em qualquer etapa mantém a versão anterior ou o fallback. Detalhes em ADR-13.

## Cenários de compatibilidade

| Cenário | Comportamento esperado |
| --- | --- |
| Perfil com saídas desligadas | Features de saída no padrão; confiabilidade reduzida declarada |
| Perfil sem chamada por aula | Marca S nunca ocorre; features parciais no padrão |
| Modelo ausente ou corrompido | Fallback de regras com a mesma interface |
| Versão do app abaixo da mínima | Pacote retido até atualizar o aplicativo |
| Validade vencida | Estado modelo_desatualizado com a mensagem aprovada |

## Testes de compatibilidade do lado do app

O app roda dados-teste.json na ativação e pode incorporar os mesmos casos na suíte própria; a fonte é o pacote, e o expected é gerado pelo FrequencIA com a mesma semântica da inferência no navegador.
