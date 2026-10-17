# ADR-002: exportação via m2cgen com ONNX como alternativa

## Estado

Aceita.

## Contexto

O destino do modelo é o navegador de um celular modesto, offline, dentro do PWA do FrequenciApp. As opções de runtime do briefing eram ONNX Runtime Web, m2cgen e TensorFlow.js. O critério operacional do projeto é obsessivo com tamanho em bytes e latência: cada kilobyte de runtime conta, e o app já controla o próprio Service Worker sem dependências pesadas.

## Decisão

- O caminho primário de exportação é m2cgen 0.10: o estudante LightGBM vira uma função `score` em JavaScript puro, sem dependências, com tamanho medido e teto de 256 KiB para o modelo.js completo.
- O invólucro gerado pelo FrequencIA (calibração, aquecimento, conformal, estados de confiança, histerese) vive no mesmo arquivo, espelhado por uma função Python idêntica usada no teste de paridade com Node.
- O caminho ONNX fica implementado e testado como alternativa documentada (onnxmltools com opset 15), para consumidores não web ou ferramentas de validação externa; ele não entra no pacote publicado.
- TensorFlow.js foi descartado: exigiria runtime adicional e conversão com ganho nenhum para árvores pequenas.

## Consequências

- O pacote publicado carrega um único arquivo de modelo com zero dependências: a latência medida fica abaixo de 0,1 ms por previsão no Node, ordem de grandeza abaixo do teto de 5 ms.
- O teste de paridade roda o JavaScript real no Node e compara com a saída Python casa por casa, o que valida o caminho de produção de verdade.
- m2cgen suporta LightGBM com booster gbdt (a configuração usada); boosters rf e dart não são suportados e ficam fora do contrato.
- A saída do m2cgen para classificação binária devolve o vetor de probabilidades por classe; o invólucro toma o último elemento, e o teste cobre essa convenção.

## Alternativas consideradas

- ONNX Runtime Web como primário: runtime de cerca de 10 MB (ou ~2 MB no build enxuto), peso inaceitável para o público-alvo e complexidade de carregamento no Service Worker.
- Lógica traduzida à mão (scorecard ou regressão): perderia a acurácia do estudante destilado e criaria dois modelos para manter.
