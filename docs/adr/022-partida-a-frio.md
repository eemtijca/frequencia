# ADR-022: alunos reservados para avaliar a partida a frio

## Estado

Aceita.

## Contexto

A maquinaria de confiança do produto existe para o começo do histórico: o encolhimento para a taxa base nos primeiros 30 dias, os grupos conformes de histórico curto e os estados `dados_insuficientes` e `em_observacao`. O teste, porém, é o último bloco do período, quando todo aluno já tem mais de 30 dias de histórico. No perfil `padrao`, nenhuma linha de teste tinha histórico abaixo de 30 dias: os mecanismos feitos para a partida a frio nunca eram medidos.

## Decisão

- Uma fração dos alunos (padrão 20%, configurável por `--fracao-reserva-frio`) é reservada por hash estável do `aluno_id`, independente de semente e de ordem. Esses alunos saem de treino, validação e teste.
- Das linhas dos alunos reservados, ficam só as de histórico abaixo do aquecimento: metade dos alunos forma `frio_calibracao`, a outra metade `frio_teste`. As demais linhas são descartadas.
- `frio_calibracao` entra no conjunto de calibração com a validação, o que dá dados aos grupos conformes de histórico curto.
- `frio_teste` é avaliado à parte (`partida_a_frio` no relatório), com o mesmo preditor publicado. O gate `ece_partida_a_frio` (máximo 0,15) entra quando há pelo menos 300 linhas com as duas classes; abaixo disso, o veredito registra o gate em `nao_avaliados`, com o motivo, em vez de aprová-lo em silêncio.
- O smoke no perfil `fumaca` passa a exigir que os gates sejam calculados, não aprovados: com cem alunos, a diferença entre o modelo e o baseline fica dentro do erro-padrão da AUC, e o veredito oscila com o ruído. A aprovação de todos os gates, sem pendências, é exigida no perfil `padrao` (`make qualidade` e teste lento).

## Consequências

- A partida a frio passa a ter número: no perfil `padrao`, ela fica abaixo do regime maduro, o que é esperado e agora visível.
- O treino perde os alunos reservados. No perfil `fumaca`, isso basta para o modelo de árvores perder para o baseline de regras, o que o gate `melhora_sobre_baseline` registra corretamente.
- A avaliação da partida a frio mede o começo do histórico de cada aluno, mas no mesmo calendário dos alunos de treino: ela não mede extrapolação para outro ano letivo, que exige dados de mais de um ano.

## Alternativas consideradas

- Teste no início do ano seguinte: mede a partida a frio e a extrapolação no tempo juntas, mas exige dados sintéticos de dois anos e não existe nos dados reais do primeiro ano.
- Usar no teste os alunos que se matriculam tarde: são poucos (5% no gerador) e concentrados no meio do período.
- Não reservar e só relatar a curva de aprendizado: a curva era medida nos dados de ajuste e não cobria o aquecimento.
