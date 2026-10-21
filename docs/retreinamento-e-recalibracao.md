# Retreinamento e recalibração

Quando e como retreinar, recalibrar e desativar. O modelo tem prazo de validade e critérios objetivos para continuar ativo.

## Sinais que pedem ação

| Sinal | Limite | Ação |
| --- | --- | --- |
| Validade vencida | 180 dias da montagem | Suprimir o indicador (estado modelo_desatualizado) e retreinar |
| Drift de features | PSI acima de 0,20 em qualquer feature | Retreinar com dados recentes |
| Acurácia observada | Feedback agregado abaixo de 0,60 | Revisar modelo ou qualidade do registro |
| Taxa de descarte | Feedback acima de 0,50 | Revisar limiares e mensagens com a coordenação |
| Mudança de contrato | Nova feature ou novo rótulo | Novo experimento com versão de contrato incrementada |

O relatório de saúde (`monitoramento relatorio-saude`) resume os sinais e recomenda a ação; a página Monitoramento do painel mostra o mesmo conteúdo. Quando a decisão for de retreinamento ou mudança de contrato, registre a hipótese e o protocolo conforme [ciencia-e-inovacao.md](ciencia-e-inovacao.md).

## Recalibração leve

Quando o modelo segue útil mas a escala deslocou (sazonalidade nova, mudança de catálogo de justificativas), recalibrar basta. Os comandos usam Docker; no fallback venv, troque o prefixo Docker por `frequencia`.

```bash
docker compose --profile cli run --rm cli frequencia monitoramento recalibrar \
  var/artefatos/experimentos/<experimento>

docker compose --profile cli run --rm cli frequencia avaliacao validar-gates \
  var/artefatos/experimentos/<experimento>

docker compose --profile cli run --rm cli frequencia empacotamento montar \
  var/artefatos/experimentos/<experimento>
```

A etapa recalcula Platt e os quantis conformes sobre o OOF existente e atualiza calibracao.json. Reavalie os gates e reexporte o pacote antes de publicar. O `empacotamento montar` usa cartão mínimo e sem contexto MEC; confira o conteúdo gerado.

## Retreinamento completo

1. Gerar ou importar dados recentes (base legal registrada para institucionais).
2. Construir o dataset com ponto-in-tempo estrito e o passo adequado ao volume.
3. Executar o ciclo completo com identificador novo:

```bash
docker compose --profile cli run --rm cli frequencia experimentos executar \
  var/dados/processados/<novo> \
  --identificador retreino-<mes> \
  --versao-modelo <versao-modelo>
```

4. Comparar com a versão atual:

```bash
docker compose --profile cli run --rm -T --no-deps cli frequencia registro comparar \
  risco-infrequencia <atual> <nova>

docker compose --profile cli run --rm -T --no-deps cli frequencia experimentos comparar \
  var/artefatos/experimentos/<pasta-atual> \
  var/artefatos/experimentos/<pasta-nova>
```

5. Promover, publicar e planejar o rollback para a versão anterior, mantendo-a no canal até a nova mostrar estabilidade por duas semanas de feedback.

## Importar feedback agregado

```bash
docker compose --profile cli run --rm cli frequencia monitoramento importar-feedback \
  feedback.json \
  --fonte painel
```

O arquivo carrega dias, acuracia_observada e taxa_descarte por dia, em contagens agregadas. Nenhum registro individual entra: o vocabulário do arquivo é o contrato mínimo.

## Desativação

A desativação segue o caminho da revogação com motivo documentado, e o app passa a exibir o fallback até nova versão. O estado arquivado preserva o histórico no registro para prestação de contas.

## Cadência recomendada

- Trimestral: avaliação de saúde e decisão de recalibrar.
- Semestral ou por drift: retreinamento completo com dados recentes.
- Contínua: monitoramento da validade pelo próprio app (estado modelo_desatualizado) e pelo painel.
