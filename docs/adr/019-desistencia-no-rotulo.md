# ADR-019: desistência dentro da janela conta como desfecho positivo

## Estado

Aceita. Altera a definição de rótulo das ADRs 011 e 014 e do catálogo de modelos.

## Contexto

O rótulo era "duas ou mais faltas nos sete dias letivos seguintes, contando enquanto matriculado". O diário deixa de ter linhas a partir de `desistente_em`, então as faltas de quem desiste no meio da janela eram truncadas: quem desistia no segundo dia tendia a receber rótulo negativo, e quem desistia no primeiro dia não tinha nenhuma linha na janela e saía do dataset pela junção interna. O efeito é sistemático e aponta na direção errada: o desfecho mais grave do domínio, o abandono, era contado como ausência de risco.

O gerador sintético não revelava o problema porque sorteava a desistência com probabilidade fixa de 2,5%, independente da propensão a faltar. Nos dados reais, infrequência crescente é o preditor clássico de abandono; um gerador sem essa ligação não exercita o caso.

## Decisão

- O rótulo é positivo quando há duas ou mais faltas na janela ou quando `desistente_em` cai dentro dela (depois do dia de referência e até o último dia da janela). O dataset ganha a coluna `desistiu_na_janela`, que não é feature.
- Os rótulos partem dos alunos presentes no dia de referência (junção pela esquerda), com zero faltas para quem não tem linha na janela.
- No gerador, a chance anual de desistir é proporcional à propensão latente (`chance_desistencia`), com média da população perto de 2,5%, e as faltas escalam nos dez dias letivos anteriores à desistência.
- O resumo do dataset informa quantos positivos vêm apenas da desistência.

## Consequências

- A taxa do rótulo sobe ligeiramente, e o modelo passa a ser cobrado justamente nos casos que motivam o indicador.
- O significado do indicador muda para a coordenação: "duas ou mais faltas ou deixar a escola nos próximos sete dias letivos". Guias, cartão do modelo e catálogo foram atualizados.
- A amostra versionada em `dados/sinteticos/amostra` não muda: com 30 alunos, nenhum desiste em nenhuma das versões do gerador.

## Alternativas consideradas

- Excluir do dataset as linhas cuja janela contém desistência: evita o viés, mas joga fora exatamente os exemplos mais importantes.
- Modelar abandono como desfecho separado: mais preciso, mas exige um segundo modelo e um segundo contrato no app, sem dados reais para calibrar.
