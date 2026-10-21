# Projeto: risco individual de infrequência

Definição do modelo generalista principal do FrequencIA. O cartão completo por versão acompanha o pacote em modelo-cartao.md; aqui vive a definição do problema, as métricas de sucesso e o plano de manutenção.

## Definição do problema

A coordenação escolar tem minutos por dia para decidir onde olhar. O painel mostra a infrequência do dia e o acumulado por turma, mas o sinal de que um estudante vai faltar na semana que vem já existe no histórico recente e fica espalhado demais para leitura manual. O modelo estima, ao fim de cada dia com chamada salva, a probabilidade de o estudante acumular duas ou mais faltas (F ou FJ) nos próximos sete dias letivos, e entrega uma lista curta e calibrada de onde a atenção tem mais chance de prevenir.

## Unidade e horizonte

| Aspecto | Definição |
| --- | --- |
| Unidade de previsão | estudante por dia de referência |
| Horizonte | sete dias letivos seguintes |
| Rótulo | duas ou mais faltas no horizonte, ou desistência dentro dele (ADR-019) |
| Saída | probabilidade calibrada, conjunto conforme, faixa de risco, estado de confiança e alerta com histerese |

## Público e uso

Coordenação e direção, no painel do dia e no relatório por aluno. O indicador é sugestão de apoio com incerteza visível: nunca rotula pessoas, nunca decide ação, sempre sujeito a revisão e descarte humano. O produto prioriza Top-K diário, porque a capacidade operacional da coordenação é o limite real.

## Métricas de sucesso

| Métrica | Alvo | Por quê |
| --- | --- | --- |
| AUC no teste | mínimo 0,70 (gate) | Ordenação útil acima do acaso e do baseline |
| Precisão Top-10 diário | alvo 0,50 ou mais | Uma lista curta em que metade merece o olhar |
| ECE | máximo 0,10 (gate) | Probabilidade que se pode ler como probabilidade |
| Taxa de alerta | máximo 0,35 (gate) | Não saturar a coordenação |
| Tamanho do modelo.js | máximo 256 KiB | Celular modesto, atualização barata |
| Latência por previsão | máximo 5 ms | Painel fluido no navegador |

## Dados

Treino inicial com dados sintéticos determinísticos (perfil fumaça no smoke, padrão em produção), com sazonalidade, perfis de escola, transferências e eventos retroativos. Substituição por exportações institucionais autorizadas conforme o guia de exportação, sempre com base legal registrada e portão de privacidade verde.

## Ciclo de execução

```bash
docker compose --profile cli run --rm cli frequencia experimentos executar \
  var/dados/processados/<dataset> \
  --identificador <id>
```

O método científico e os critérios de decisão estão em [docs/ciencia-e-inovacao.md](../../docs/ciencia-e-inovacao.md).

## Limitações conhecidas

- Treinado com sintéticos até a primeira importação autorizada: validar com dados reais antes de produção.
- Confiabilidade reduzida quando o perfil da escola desliga saídas ou chamada por aula (declarado no manifesto).
- A calibração é por série e faixa de histórico; escolas muito pequenas ficam no grupo conforme genérico.
- O contexto MEC defasa um ano: mudança brusca de rede não entra no modelo.
- Sem histórico (primeiras semanas de uso), o indicador ancora na taxa base e se declara em observação.

## Plano de retreinamento

- Recalibração leve trimestral, ou quando o drift por PSI passar de 0,20.
- Retreinamento completo semestral, ou por drift persistente e queda de acurácia observada abaixo de 0,60.
- Publicação sempre com rollback para a versão anterior no canal por duas semanas de estágio.
- Procedimentos detalhados em docs/retreinamento-e-recalibracao.md.

## Configuração de referência

A configuração declarativa padrão está em config/experimento.yaml (semente 20261018, três dobras de ensemble, LightGBM 120 iterações de profundidade 4, estudante destilado de profundidade 3 com 60 iterações). Mudanças de parâmetro entram como opção de linha ou arquivo de configuração novo; mudanças de arquitetura entram como ADR.
