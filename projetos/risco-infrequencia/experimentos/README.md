# Experimentos do projeto de risco de infrequência

Registro humano dos experimentos de pesquisa do modelo principal. O artefato de máquina fica em `var/artefatos/experimentos/<id>/`; o registro de decisão fica aqui, versionado no Git.

## Estrutura

```text
projetos/risco-infrequencia/experimentos/<ano-mes>-<slug>/
├── protocolo.md
├── resultados.md
├── decisao.md
└── evidencias.md
```

## Nomes

- Use `AAAA-MM-slug`, em minúsculas, com hífens e sem acento.
- Exemplo: `2026-11-saidas-recentes`.
- Use o mesmo identificador em `experimentos executar --identificador pesquisa-<slug>`.

## Fluxo

1. Escrever o brief e o protocolo.
2. Pedir revisão humana antes de executar.
3. Rodar em workspace isolado.
4. Registrar resultados, inclusive negativos.
5. Montar o pacote de evidências.
6. Aplicar a rubrica de pesquisa.
7. Registrar a decisão.
8. Atualizar o portfólio em `projetos/README.md`.

## Templates

- [Brief de inovação](../../../docs/templates/brief-de-inovacao.md)
- [Protocolo de experimento](../../../docs/templates/protocolo-de-experimento.md)
- [Nota de pesquisa](../../../docs/templates/nota-de-pesquisa.md)
- [Revisão científica](../../../docs/templates/revisao-cientifica.md)
- [Relatório de experimento](../../../docs/templates/relatorio-de-experimento.md)
- [Rubrica de pesquisa](../../../docs/templates/rubrica-de-pesquisa.md)
- [Pacote de evidências](../../../docs/templates/pacote-de-evidencias.md)

## Regras

- Nenhum experimento começa sem protocolo.
- O conjunto de teste não é usado para escolher hiperparâmetro ou limiar.
- O resultado negativo é registrado.
- Mudança de contrato exige ADR.
- Aprovação e publicação são humanas.
