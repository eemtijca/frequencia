# ADR-012: ensemble offline destilado para estudante leve

## Estado

Aceita.

## Contexto

O briefing é claro: o ensemble é ferramenta de treino, nunca de produção; o artefato publicado é leve. O TabFM referencia ensemble diversificado com vistas de dados, blending por pesos e calibração regularizada. O LightGBM 4.7, além disso, rejeita rótulos fracionários no objetivo binário pelo caminho sklearn, o que afeta a destilação com alvos suaves.

## Decisão

- Sete membros de base: LightGBM médio (todas as features), LightGBM curto (oito features de janela imediata), XGBoost, CatBoost, histogramas do scikit-learn, regressão logística com padronização e baseline de regras puro.
- Validação fora da dobra em dobras temporais expansivas (padrão 3); o blending é regressão logística regularizada sobre as probabilidades dos membros, com pesos normalizados e registrados; a discordância entre membros vira o sinal de incerteza.
- A destilação treina o estudante (LightGBM profundidade 3, 60 iterações, 15 folhas) sobre os alvos suaves calibrados, codificados por duplicação ponderada: cada linha entra duas vezes, com rótulo 1 e peso p e com rótulo 0 e peso 1-p, reproduzindo o gradiente esperado do alvo suave sem tocar a restrição do wrapper sklearn.
- O membro baseline de regras é o mesmo código do fallback.js publicado, mantendo a família de comportamento quando o modelo principal não carrega.

## Consequências

- O estudante destilado fica em torno de 60 KB como joblib e gera um modelo.js abaixo de 70 KB, com paridade exata com a saída Python.
- O ensemble fica em var/artefatos para reanálise e redestilação, mas não é publicado.
- A duplicação ponderada dobra as linhas do treino do estudante: custo linear aceito pelo ganho de fidelidade ao professor.

## Alternativas consideradas

- Publicar o ensemble em cascata: pesado para o navegador e contra o briefing.
- Destilar com rótulos duros: perde a informação de confiança do professor.
- Amostragem de Bernoulli dos alvos suaves: ruído de amostragem sem ganho sobre a duplicação ponderada.
