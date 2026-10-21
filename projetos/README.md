# Projetos e portfólio de inovação

Índice dos projetos do FrequencIA e das iniciativas de pesquisa. O método está em [docs/ciencia-e-inovacao.md](../docs/ciencia-e-inovacao.md), e as diretrizes de decisão estão em [docs/templates/](../docs/templates/).

## Projeto principal

| Projeto | Unidade | Situação | Pasta |
| --- | --- | --- | --- |
| Risco individual de infrequência | aluno-dia | em desenvolvimento | [risco-infrequencia](risco-infrequencia/README.md) |

## Portfólio de iniciativas

| Iniciativa | Estágio | Evidência | Impacto | Confiança | Esforço | Risco | Próxima decisão | Dono |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Risco individual de infrequência | experimental | gates e smoke | alto | média | alto | médio | piloto com dados institucionais | equipe FrequencIA |

Atualize a tabela a cada revisão mensal. Use os estágios do funil: ideia, protocolo, offline, sombra, piloto, adoção e aprendizado.

## Projetos futuros

| Projeto | Unidade | Gatilho de abertura |
| --- | --- | --- |
| Priorização de turmas no painel | turma | demanda da coordenação por visão coletiva com ganho medido sobre a infrequência simples |
| Anomalia de turma por dia | turma-dia | persistência de eventos coletivos invisíveis ao modelo individual |
| Risco de desistência | aluno | alto valor e alta delicadeza; exige governança reforçada e dados institucionais autorizados |
| Fluxo de saídas e entradas | aluno-dia | recurso de saídas amplamente ligado e sinal complementar comprovado |

Cada projeto futuro nasce com pasta própria, protocolo, revisão, ADR quando estrutural e cartão de modelo. Abrir um projeto não é compromisso de adotar um modelo; é compromisso de investigar com método.

## Convenção de experimentos

```text
projetos/risco-infrequencia/experimentos/<ano-mes>-<slug>/
├── protocolo.md
├── resultados.md
├── decisao.md
└── evidencias.md
```

- O nome segue `AAAA-MM-slug`, em minúsculas, com hífens e sem acento.
- O mesmo identificador é usado em `experimentos executar --identificador`.
- O protocolo é escrito antes do experimento.
- Os resultados, a decisão e as evidências são escritos depois.
- O resultado negativo também é registrado.
- O artefato de máquina fica em `var/artefatos/experimentos/<id>/`.

## Revisão mensal

1. Atualizar o estágio de cada iniciativa.
2. Revisar evidência, riscos e custo.
3. Decidir continuar, pivotar, estacionar ou encerrar.
4. Registrar a decisão no projeto.
5. Atualizar a agenda de pesquisa em [docs/ciencia-e-inovacao.md](../docs/ciencia-e-inovacao.md).
