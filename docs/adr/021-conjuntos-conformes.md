# ADR-021: conjuntos de predição conformes por classe no lugar do intervalo

## Estado

Aceita. Substitui o intervalo conforme da ADR-003. Muda o contrato de inferência para a versão 2.

## Contexto

O pacote publicava `intervalo_conformal = [p - q, p + q]`, com q o quantil do resíduo |y - p|. Como y é binário, esse objeto é um intervalo de predição para o rótulo, não um intervalo de confiança para a probabilidade, que é como a documentação o apresentava. No perfil `padrao`, a largura média no teste foi 0,88: o intervalo quase sempre cobria quase todo o [0, 1]. A única informação que ele carrega é quais rótulos ficam dentro dele, e a forma de intervalo escondia isso.

Além disso, a garantia era marginal: com 15% de positivos, a cobertura de 90% se atinge errando boa parte dos positivos. Grupos com menos de oito linhas recebiam quantil 0,5 e cobertura 1,0 declarada sem medição, e a cobertura reportada era medida nos mesmos dados do ajuste, onde ela é de pelo menos 90% por construção.

## Decisão

- A saída passa a ser `conjunto_conformal`, um subconjunto de {0, 1}: `[1]` indica risco no nível de confiança do manifesto, `[0]` indica ausência de risco e `[0, 1]` indica que o modelo não decide nesse nível.
- A garantia é condicional à classe dentro de cada grupo Mondrian (série por faixa de histórico): para cada grupo e classe, o quantil conforme do escore 1 - p(classe verdadeira) vira um limiar em p. O manifesto carrega `negativo` (a classe 0 entra quando p <= negativo) e `positivo` (a classe 1 entra quando p >= positivo).
- Grupo com menos de 20 linhas de uma classe inclui essa classe sempre; quantil cujo posto passa de n é infinito. Grupo desconhecido e conjunto vazio devolvem `[0, 1]`. Nenhuma cobertura é declarada sem medição.
- A cobertura e a eficiência (fração de conjuntos unitários) são medidas no teste, sobre o preditor publicado, e o gate de cobertura usa a menor cobertura por classe no teste.
- O fallback de regras devolve sempre `[0, 1]`, porque não tem garantia conforme.
- `versao_contrato` sobe para 2. O FrequenciApp precisa ler `conjunto_conformal` antes de ativar pacotes desta versão.

## Consequências

- O produto ganha uma leitura honesta e acionável: no perfil `fumaca`, 46% dos conjuntos no teste são unitários, com cobertura de 0,89 na classe 0 e de 0,96 na classe 1.
- A cobertura no teste pode ficar abaixo do nível nominal quando o período de teste difere do de calibração, porque a trocabilidade no tempo não é perfeita. Isso passa a aparecer no relatório e no gate, em vez de ficar escondido pela medição dentro da amostra.
- Pacotes da versão 1 do contrato continuam legíveis pelo app antigo, mas pacotes novos exigem app atualizado.

## Alternativas consideradas

- Venn-Abers, que dá um intervalo para a própria probabilidade: é a resposta teoricamente certa para "quão incerta é esta probabilidade", mas exige embarcar a calibração isotônica do conjunto de calibração no modelo.js e substituiria o Platt. Fica como candidato para uma decisão futura, com experimento próprio.
- Manter o intervalo com outro nome: preservaria a forma enganosa de um objeto cuja informação é apenas o conjunto de rótulos.
- Cobertura marginal sem condicionar à classe: atinge 90% dizendo `[0]` para quase todos.
