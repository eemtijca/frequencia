# ADR-023: limiar de alerta derivado da taxa-alvo

## Estado

Aceita.

## Contexto

O alerta ligava com probabilidade de pelo menos 0,65 e desligava abaixo de 0,45, valores fixos e escritos em três módulos. Com prevalência de 15,5% e um modelo calibrado, quase nenhuma linha passa de 0,65: no perfil `padrao`, a taxa de alerta no teste foi de 0,84%, com 60 falsos positivos e 3.155 falsos negativos, o que dá revocação de cerca de 3,6%. O único gate sobre o alerta limitava a taxa máxima e não exigia que ele alcançasse ninguém.

Um limiar absoluto de probabilidade só faz sentido se a prevalência e a calibração forem estáveis entre escolas e anos. A grandeza que a escola controla é outra: quantos estudantes a coordenação consegue acompanhar.

## Decisão

- A configuração do experimento declara `taxa_alerta_alvo` (padrão 0,10). O limiar de entrada é o quantil 1 - taxa_alvo da probabilidade publicada no conjunto de calibração; o de saída é 70% da entrada, mantendo a razão anterior entre 0,45 e 0,65 e com ela a histerese.
- Os limiares são gravados no pacote (`modelo.js` e manifesto) e usados pela avaliação; `confianca.LIMIARES_ALERTA` passa a ser só o padrão para pacotes sem calibração.
- A avaliação mede precisão, revocação e lift do alerta no limiar de entrada, antes da histerese. Novos gates: lift mínimo de 2,0 e revocação mínima de 0,15. Com taxa-alvo de 10%, revocação de 0,2 equivale a lift de 2.

## Consequências

- O alerta passa a disparar na proporção que a escola definiu, e a qualidade dele vira gate.
- O limiar numérico muda de versão para versão do modelo. O app não pode fixá-lo: precisa ler `limiares_alerta` do manifesto, como o contrato já exigia.
- O fallback de regras usa os mesmos limiares, embora o escore de regras não seja calibrado. A taxa de alerta do fallback pode diferir da taxa-alvo; isso fica registrado como limitação.

## Alternativas consideradas

- Manter o limiar absoluto e reduzi-lo: troca um número arbitrário por outro e continua cego à prevalência.
- Escolher o limiar que maximiza F1 na calibração: otimiza uma métrica sem relação com a capacidade da coordenação.
- Alerta só pelo Top-K diário: já está no painel, mas não dá histerese entre dias nem uma probabilidade de corte para o app.
