# ADR-003: calibração Platt regularizada e predição conforme

## Estado

Aceita, com a força do prior de Platt e o conjunto de ajuste substituídos pela ADR-020 e o intervalo conforme substituído por conjuntos de predição pela ADR-021.

## Contexto

O modelo nasce num ambiente de dados escassos: o primeiro mês de uma escola tem poucas centenas de linhas por série. Recalibrar sem restrições nessa situação deforma a escala de probabilidade e queima a confiança da coordenação com falsos alertas. O briefing exige calibração regularizada em direção à identidade, predição conforme Mondrian por série e por faixa de histórico, e estados de confiança visíveis no produto. O TabFM referencia Platt com regularização L2, o que reforça a família de solução.

## Decisão

- A calibração ajusta (a, b) do escalonamento de Platt por minimização da perda logística somada a λ((a-1)² + b²), com λ padrão 0,5 e limites de busca (0,2 a 5) para a e (-3 a 3) para b: sem evidência suficiente, o mapa converge para a identidade.
- O encolhimento de aquecimento mistura a probabilidade calibrada com a taxa base da escola com peso min(1, histórico/30): o primeiro mês ancora na realidade observada.
- A predição conforme usa quantis de resíduo absoluto com correção de amostra finita (posto ceil((n+1)(1-α))), por grupo Mondrian de série por faixa de histórico (curto, médio, longo), com nível padrão 0,90.
- Os estados de confiança do produto (sem histórico, dados insuficientes, em observação, confiança moderada, confiança alta, modelo desatualizado) são calculados tanto em Python quanto no modelo.js, com o mesmo vocabulário de mensagens aprovadas.

## Consequências

- O ECE medido no smoke test fica tipicamente abaixo de 0,03, e a cobertura conforme por grupo atinge o nível pedido.
- A calibração nunca amplifica confiança que os dados não sustentam; em contrapartida, o limiar fixo de alerta dispara pouco no começo, e o produto prioriza Top-K diário em vez de limiar absoluto, coerente com a assimetria de custo do briefing.
- Os parâmetros (a, b, taxa base, quantis por grupo) entram no manifest.json e são idênticos no JavaScript, garantidos pelo teste de paridade.

## Alternativas consideradas

- Isotônica: flexível demais com poucos dados, sem forma fechada para espelhar no navegador.
- Temperatura única: não corrige deslocamento de escala entre séries.
- Bayes beta calibration: mais parâmetros para estimar com dados escassos.
