# ADR-020: calibração única, fora da amostra, sobre o preditor publicado

## Estado

Aceita. Substitui partes da ADR-003 (força do prior e conjunto de ajuste) e da ADR-012 (alvo da destilação e papel da discordância).

## Contexto

A auditoria do ciclo encontrou três defeitos que se mascaravam:

- O prior de Platt era somado à perda média, então seu peso não caía com o volume de dados. Numa simulação com correção verdadeira a=2, b=1,6, o ajuste ficava em a≈0,97, b≈0,07 tanto com 300 quanto com 300 mil linhas, e o ECE parava em 0,093. No perfil `padrao`, o ajuste real saiu a=1,0001, b=0,00008: a calibração estava desligada.
- O estudante era destilado a partir de alvos já calibrados, e a avaliação e o modelo.js aplicavam Platt de novo sobre a saída dele. Hoje o efeito era nulo só porque o Platt estava congelado na identidade; corrigir o primeiro defeito sozinho teria ativado a dupla calibração.
- Platt e quantis conformes eram ajustados nas previsões fora da dobra do blend, não na saída do estudante que vai para o navegador, e ensemble, calibração e métricas de calibração compartilhavam os mesmos dados.

## Decisão

- Papéis das divisões: o treino alimenta modelo de referência, ensemble e estudante; a validação calibra o estudante; o teste avalia e decide os gates.
- O ensemble estima os pesos do blending nas previsões fora da dobra do treino e reajusta os membros em todo o treino. O alvo da destilação é a previsão desse ensemble final, sem calibração. As previsões fora da dobra da primeira dobra vêm de membros treinados com poucos dias; no perfil `fumaca`, destilar delas deu AUC de teste 0,700 contra 0,720 com o ensemble final.
- A calibração é ajustada uma única vez, na validação, sobre a saída do estudante. O Platt minimiza a perda somada mais λ((a-1)² + b²), com λ=10 em pseudo-observações. Os quantis conformes usam a probabilidade final, depois do aquecimento, que é exatamente o que o modelo.js devolve.
- `calibracao.prever_publicado` é a implementação vetorizada do preditor publicado, testada contra o espelho Python do modelo.js; calibração, conformal e avaliação passam por ela.
- A discordância entre membros fica como diagnóstico offline no painel. Como o ensemble não é publicado, ela não chega ao navegador, e a documentação deixa de dizer que chega.

## Consequências

- A calibração volta a corrigir o que os dados mostram, com proteção proporcional à escassez.
- O ensemble treina com menos dias que antes (a validação deixou de alimentá-lo). No perfil `fumaca`, que é pequeno, a diferença entre o estudante e o baseline de regras fica dentro do erro-padrão da AUC (cerca de 0,02 com 980 linhas de teste); o perfil serve para validar o ciclo, não para comparar modelos.
- Experimentos anteriores a esta decisão não são comparáveis em calibração e devem ser refeitos.

## Alternativas consideradas

- Manter λ na perda média e reduzir seu valor: continuaria independente de n, só que com outro ponto de congelamento.
- Destilar alvos calibrados e exportar calibração identidade: elimina a dupla aplicação, mas deixa a calibração ajustada no blend e não no preditor publicado.
- Validação cruzada aninhada para calibrar o estudante em todos os dados: mais eficiente em dados, mas multiplica o custo do ciclo pelo número de dobras.
