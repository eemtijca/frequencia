# Contrato de inferência

Como o pacote publicado recebe entradas e devolve o indicador, na fronteira entre o FrequencIA e o FrequenciApp. Este contrato é a referência de implementação do consumidor; o manifesto do pacote carrega a versão e os parâmetros.

## Entrada

O app monta o vetor de features na ordem fixa de `contrato.features` do manifest.json, usando `contrato.padroes` para qualquer valor ausente (nulo, indefinido ou não numérico). O vetor é numérico puro: 47 posições, na ordem do catálogo de features.

```js
const vetor = new Array(47);
// posições conforme manifest.json: contrato.features
vetor[contrato.features.indexOf("faltas_7d")] = faltas7;
// valores ausentes: deixar undefined; o modelo aplica o padrão do contrato
```

O contexto complementa o vetor com o que não é feature:

| Campo | Tipo | Papel |
| --- | --- | --- |
| serie | texto | Chave do grupo conforme (série por faixa de histórico). |
| idade_modelo_dias | inteiro | Idade do modelo publicada; acima da validade vira modelo desatualizado. |
| estado_alerta | objeto ou nulo | Estado do dia anterior (em_alerta, dias_acima) para a histerese. |

## Saída

`modelo.prever(vetor, contexto)` devolve um objeto com tudo o que o produto precisa:

| Campo | Tipo | Significado |
| --- | --- | --- |
| probabilidade | fração | Probabilidade final após calibração e aquecimento. |
| probabilidade_nucleo | fração | Saída bruta do núcleo destilado, para telemetria interna. |
| probabilidade_calibrada | fração | Saída após Platt, antes do aquecimento. |
| risco | baixo, medio ou alto | Faixa pelos limiares de entrada e saída. |
| conjunto_conformal | lista de classes | `[1]`: risco no nível de confiança do manifesto; `[0]`: ausência de risco; `[0, 1]`: o modelo não decide nesse nível. |
| estado_confianca | estado | sem_historico, dados_insuficientes, em_observacao, confianca_moderada, confianca_alta ou modelo_desatualizado. |
| mensagem | texto | Frase aprovada do vocabulário, pronta para exibir. |
| alerta | objeto | em_alerta e dias_acima após a histerese. |
| chave_grupo | texto | Grupo conforme usado, para depuração. |
| versao_modelo | texto | Versão do modelo que respondeu. |

## Semântica do cálculo

A ordem é fixa e idêntica em Python e JavaScript, garantida pelo teste de paridade:

1. Preenchimento de padrões nos valores ausentes do vetor.
2. Núcleo: saída da função transpilada do LightGBM destilado (última posição do vetor de classes).
3. Platt: p_cal = sigmoide(a * logit(p_nucleo) + b) com (a, b) do manifesto.
4. Aquecimento: p = peso * p_cal + (1 - peso) * taxa_base, com peso = min(1, historico_dias / 30).
5. Conjunto conforme: com os limiares do grupo (série por faixa de histórico), a classe 0 entra quando p <= `negativo` e a classe 1 entra quando p >= `positivo`; grupo desconhecido ou conjunto vazio devolve `[0, 1]`.
6. Estado de confiança a partir de historico_dias, idade do modelo e cobertura de chamada.
7. Histerese: alerta liga após dois dias acima do limiar de entrada (padrão 0,65) e desliga abaixo do limiar de saída (padrão 0,45).

## Perfis de dados

O manifesto declara os perfis suportados com confiabilidade esperada. Perfil com chamada por aula e saídas ligadas tem confiabilidade plena; sem esses recursos, as features dependentes caem no padrão e a confiabilidade declarada é reduzida: o app rebaixa ou suprime o indicador conforme sua própria regra de produto.

## Fallback

`fallback.js` expõe a mesma interface `prever(vetor, contexto)` com o escore de regras no lugar do núcleo, os mesmos limiares de alerta e a mesma forma de saída, com campo fallback verdadeiro, estado confianca_moderada e `conjunto_conformal` sempre `[0, 1]`: as regras não têm calibração nem garantia conforme, e o fallback não aplica o aquecimento. O app usa quando o modelo.js falha ao carregar, o hash diverge ou a autoverificação dos dados-teste reprova.

## Casos de teste

`dados-teste.json` carrega casos sintéticos com vetor, contexto e saída esperada. O app roda todos na ativação: qualquer divergência além de 1e-6 descarta a versão e mantém a anterior (ou o fallback). Os mesmos casos rodam no teste de paridade da suíte, no Node, contra o modelo.js real.
