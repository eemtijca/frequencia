# Runbooks operacionais

Procedimentos passo a passo para as situações do dia a dia. Todos usam a CLI com `--json` quando precisam de saída para script, e o painel quando a operação é visual.

## RB-01: primeiro ciclo numa máquina nova

```bash
bash scripts/setup.sh
bash scripts/smoke.sh
```

Verde em tudo: ambiente pronto. Em caso de falha de pyarrow ou numpy, conferir o Python 3.12 e rodar `pip check` no venv.

## RB-02: rodar o ciclo com dados novos

```bash
frequencia dados importar <pasta> --origem <sintetico|mec|institucional> [--base-legal <base>]
frequencia datasets construir <pasta-importada> --versao v<N>
frequencia experimentos executar var/dados/processados/v<N> --identificador exp<N>
frequencia avaliacao validar-gates var/artefatos/experimentos/exp<N>
```

Cada etapa é idempotente: reexecutar pula o que concluiu. Interrompido no meio, `experimentos recuperar <id>` retoma do ponto de parada.

## RB-03: publicar uma versão homologada

Seguir docs/publicacao-de-modelos.md. Resumo: gates verdes, promover a candidato e homologado com papel de aprovador, publicar o pacote, conferir hash e compatibilidade, entregar o zip ao app.

## RB-04: investigar queda de qualidade

1. `frequencia monitoramento relatorio-saude` para ver validade, drift e feedback.
2. `frequencia monitoramento drift <experimento> <fotografia-atual>` para o detalhe por feature.
3. `frequencia avaliacao subgrupos <experimento>` e `frequencia avaliacao fairness <experimento>` para dispersão entre séries.
4. Decidir entre recalibração leve (RB-05) e retreinamento (RB-06) conforme docs/retreinamento-e-recalibracao.md.

## RB-05: recalibrar sem retreinar

```bash
frequencia monitoramento recalibrar var/artefatos/experimentos/<exp>
frequencia empacotamento montar var/artefatos/experimentos/<exp>
```

O pacote regravado carrega os parâmetros novos; seguir a publicação do RB-03.

## RB-06: retreinar com dados recentes

Seguir docs/retreinamento-e-recalibracao.md: dataset novo, experimento novo, comparação com a versão atual, promoção com rollback planejado.

## RB-07: rollback de emergência

```bash
frequencia publicacao reverter <versao-anterior> --papel aprovador
```

A versão atual é descontinuada com motivo e a anterior volta ao canal. Se não houver versão anterior, revogar e deixar o fallback ativo:

```bash
frequencia publicacao revogar <versao> --papel aprovador
```

## RB-08: suspeita de dado pessoal no fluxo

1. Não treinar nem promover nada.
2. `frequencia privacidade relatorio-risco <pasta>` para o relatório completo.
3. Se houver achado, corrigir na fonte e reimportar; se precisar manter o texto, pseudonimizar com `privacidade pseudonimizar`.
4. Registrar o incidente conforme docs/privacidade-lgpd.md.

## RB-09: experimento travado ou interrompido

```bash
frequencia experimentos interromper <id>     # marca o estado
frequencia experimentos recuperar <id>       # retoma do ponto de parada
```

O estado por etapa fica em var/artefatos/experimentos/<id>/estado.json; etapas concluídas não reexecutam sem --forca com justificativa.

## RB-10: backup do workspace

Copiar a pasta var inteira cobre dados importados, experimentos, registro, auditoria, pacotes, publicações e o banco do MLflow. Restaurar é copiar de volta. O repositório em si não guarda estado.

## RB-11: verificação de integridade periódica

```bash
frequencia auditoria verificar-integridade
frequencia publicacao verificar-hash <versao-atual>
frequencia dados verificar-integridade <pasta-de-dados>
```

Três ângulos: manifestos das publicações, modelo publicado e pacotes de dados importados.
