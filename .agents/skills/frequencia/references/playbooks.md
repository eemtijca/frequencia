# Playbooks operacionais do FrequencIA

Fluxos passo a passo para as tarefas mais comuns. O caminho padrão é Docker. O fallback venv com Python 3.12 existe apenas para ambientes sem Docker; para usá-lo, ative o venv e remova o prefixo `docker compose --profile cli run --rm cli` dos comandos.

## PB-01: primeiro contato e saúde do ambiente

Objetivo: confirmar que a CLI, o workspace e os serviços respondem antes de qualquer mudança.

```bash
docker --version
docker compose version
docker compose ps
docker compose --profile cli run --rm -T --no-deps cli frequencia --help
docker compose --profile cli run --rm -T --no-deps cli frequencia registro listar
docker compose --profile cli run --rm -T --no-deps cli frequencia publicacao listar
docker compose --profile cli run --rm -T --no-deps cli frequencia monitoramento validade
docker compose --profile cli run --rm -T --no-deps cli frequencia auditoria listar --limite 20
```

Se o ambiente ainda não existe:

```bash
docker compose up --build -d
docker compose --profile ciclo up smoke
```

Sucesso: ajuda responde, serviços ficam `healthy`, smoke termina com sucesso e a auditoria mostra eventos.

Falha: leia a mensagem, rode o comando com `--detalhado` e não use `--forca` para contornar. Se Docker e Python 3.12 faltarem, pare e peça um ambiente adequado.

## PB-02: ciclo sintético completo

Objetivo: gerar dados, construir dataset, treinar, avaliar, exportar e empacotar sem usar dado real.

```bash
docker compose --profile cli run --rm cli frequencia dados gerar-sintetico \
  --perfil fumaca \
  --destino var/dados/sinteticos/demo \
  --semente 20261018

docker compose --profile cli run --rm cli frequencia dados validar \
  var/dados/sinteticos/demo

docker compose --profile cli run --rm cli frequencia privacidade validar-entrada-treino \
  var/dados/sinteticos/demo

docker compose --profile cli run --rm cli frequencia datasets construir \
  var/dados/sinteticos/demo \
  --versao demo \
  --ponto-no-tempo estrito

docker compose --profile cli run --rm cli frequencia datasets validar-ausencia-futuro \
  var/dados/processados/demo

docker compose --profile cli run --rm cli frequencia experimentos executar \
  var/dados/processados/demo \
  --identificador demo \
  --versao-modelo 2026.10.20-demo

docker compose --profile cli run --rm cli frequencia avaliacao validar-gates \
  var/artefatos/experimentos/demo

docker compose --profile cli run --rm cli frequencia exportacao testar-sinteticos \
  var/pacotes/risco-infrequencia-2026.10.20-demo

docker compose --profile cli run --rm cli frequencia empacotamento validar \
  var/pacotes/risco-infrequencia-2026.10.20-demo
```

Sucesso: sete etapas concluídas, gates aprovados, paridade zero, pacote íntegro e modelo registrado como experimental.

Falha: consulte `estado.json`, `avaliacao.json`, `gates.json` e `exportacoes/validacao.json` antes de repetir qualquer etapa.

## PB-03: dados institucionais e privacidade

Objetivo: importar uma exportação autorizada da escola com base legal e portão de privacidade.

Pré-condições: autorização da escola, base legal definida e as onze tabelas no formato do contrato.

```bash
docker compose --profile cli run --rm cli frequencia dados importar \
  <pasta-da-exportacao> \
  --origem institucional \
  --base-legal execucao-de-politica-publica \
  --licenca "uso institucional autorizado"

docker compose --profile cli run --rm cli frequencia dados gerar-perfil \
  var/dados/importados/<id>

docker compose --profile cli run --rm cli frequencia privacidade relatorio-risco \
  var/dados/importados/<id> \
  --base-legal execucao-de-politica-publica

docker compose --profile cli run --rm cli frequencia privacidade verificar-sensiveis \
  var/dados/importados/<id>

docker compose --profile cli run --rm cli frequencia privacidade validar-entrada-treino \
  var/dados/importados/<id> \
  --exigir-base-legal
```

Use o campo `pasta` do `importacao.json` como caminho de entrada. A importação copia o pacote para `var/dados/importados/<id>`.

Sucesso: relatório de risco baixo, nenhum achado de PII e portão liberado.

Falha: não treine. Corrija na fonte ou pseudonimize, reimporte e repita o portão. `privacidade bloquear` só registra auditoria; o bloqueio efetivo é o portão.

## PB-04: dataset temporal e contrato de features

Objetivo: construir o dataset sem vazamento e conferir o contrato antes do treino.

```bash
docker compose --profile cli run --rm -T --no-deps cli frequencia features validar-contrato
docker compose --profile cli run --rm -T --no-deps cli frequencia features listar

docker compose --profile cli run --rm cli frequencia datasets construir \
  <pasta-de-dados> \
  --versao v1 \
  --horizonte 7 \
  --limiar-rotulo 2 \
  --min-historico 10 \
  --passo 1 \
  --ponto-no-tempo estrito

docker compose --profile cli run --rm cli frequencia datasets separar \
  var/dados/processados/v1

docker compose --profile cli run --rm cli frequencia datasets validar-ausencia-futuro \
  var/dados/processados/v1

docker compose --profile cli run --rm cli frequencia features gerar-distribuicao \
  var/dados/processados/v1

docker compose --profile cli run --rm cli frequencia features detectar-constantes \
  var/dados/processados/v1

docker compose --profile cli run --rm cli frequencia features detectar-nulos \
  var/dados/processados/v1

docker compose --profile cli run --rm cli frequencia features verificar-vazamento \
  var/dados/processados/v1

docker compose --profile cli run --rm cli frequencia datasets registrar-linhagem \
  var/dados/processados/v1
```

Sucesso: ausência de futuro, divisão temporal coerente, taxa de rótulo plausível, sem nulos ou constantes inesperados.

Falha: não treine. Corrija a configuração ou a qualidade dos dados. Mudar `horizonte`, `limiar-rotulo` ou `min-historico` muda o problema e exige novo experimento e documentação.

## PB-05: experimento completo e retomada

Objetivo: executar o ciclo de sete etapas com parâmetros registrados e recuperar interrupções.

```bash
docker compose --profile cli run --rm cli frequencia experimentos criar \
  var/dados/processados/v1 \
  --identificador exp1 \
  --config config/experimento.yaml

docker compose --profile cli run --rm cli frequencia experimentos executar \
  var/dados/processados/v1 \
  --identificador exp1 \
  --semente 20261018 \
  --tentativas 0 \
  --dobras 3 \
  --versao-modelo 2026.10.20-exp1 \
  --min-app 1.4.0

docker compose --profile cli run --rm -T --no-deps cli frequencia experimentos listar
docker compose --profile cli run --rm -T --no-deps cli frequencia experimentos relatorio \
  var/artefatos/experimentos/exp1
docker compose --profile cli run --rm -T --no-deps cli frequencia avaliacao ensemble \
  var/artefatos/experimentos/exp1
```

Recuperação:

```bash
docker compose --profile cli run --rm cli frequencia experimentos interromper exp1
docker compose --profile cli run --rm cli frequencia experimentos recuperar exp1
```

Reexecução completa, apenas quando necessário:

```bash
docker compose --profile cli run --rm cli frequencia experimentos executar \
  var/dados/processados/v1 \
  --identificador exp1 \
  --forca \
  --justificativa "reconstrução após correção registrada na issue 123"
```

Sucesso: sete etapas em `estado.json`, `gates.json` presente e pacote registrado como experimental.

Falha: `experimentos criar` grava configuração, mas `experimentos executar` usa as flags da linha. Confira os valores no `estado.json`. O ciclo termina mesmo com gates reprovados; leia o veredito antes de promover.

## PB-06: avaliação e diagnóstico de gates

Objetivo: decidir se a versão pode seguir para candidata, com evidência de qualidade, calibração, fairness e custo.

```bash
docker compose --profile cli run --rm -T --no-deps cli frequencia avaliacao modelo \
  var/artefatos/experimentos/exp1
docker compose --profile cli run --rm -T --no-deps cli frequencia avaliacao calibracao \
  var/artefatos/experimentos/exp1
docker compose --profile cli run --rm -T --no-deps cli frequencia avaliacao subgrupos \
  var/artefatos/experimentos/exp1
docker compose --profile cli run --rm -T --no-deps cli frequencia avaliacao fairness \
  var/artefatos/experimentos/exp1
docker compose --profile cli run --rm -T --no-deps cli frequencia avaliacao curva-aprendizado \
  var/artefatos/experimentos/exp1
docker compose --profile cli run --rm -T --no-deps cli frequencia avaliacao custo-operacional \
  var/artefatos/experimentos/exp1
docker compose --profile cli run --rm -T --no-deps cli frequencia avaliacao baseline \
  var/artefatos/experimentos/exp1
docker compose --profile cli run --rm cli frequencia avaliacao validar-gates \
  var/artefatos/experimentos/exp1
```

Comparação:

```bash
docker compose --profile cli run --rm -T --no-deps cli frequencia experimentos comparar \
  var/artefatos/experimentos/exp0 \
  var/artefatos/experimentos/exp1
```

Sucesso: todos os vereditos verdadeiros, ECE e cobertura adequados, custo aceitável e nenhum subgrupo com lacuna grave.

Falha: diagnostique a causa em `references/engenharia.md`. Não ajuste o conjunto de teste, não afrouxe o gate e não escolha hiperparâmetro depois de ver o resultado.

## PB-07: exportação, pacote e paridade

Objetivo: validar o artefato JavaScript, o manifesto e a compatibilidade antes da promoção.

```bash
docker compose --profile cli run --rm -T --no-deps cli frequencia exportacao validar-contratos \
  var/pacotes/risco-infrequencia-2026.10.20-exp1
docker compose --profile cli run --rm -T --no-deps cli frequencia exportacao verificar-tamanho-latencia \
  var/artefatos/experimentos/exp1
docker compose --profile cli run --rm -T --no-deps cli frequencia exportacao artefato-teste \
  var/artefatos/experimentos/exp1
docker compose --profile cli run --rm cli frequencia exportacao testar-sinteticos \
  var/pacotes/risco-infrequencia-2026.10.20-exp1
docker compose --profile cli run --rm -T --no-deps cli frequencia exportacao hash \
  var/artefatos/experimentos/exp1
docker compose --profile cli run --rm -T --no-deps cli frequencia empacotamento validar \
  var/pacotes/risco-infrequencia-2026.10.20-exp1
docker compose --profile cli run --rm -T --no-deps cli frequencia empacotamento assinar \
  var/pacotes/risco-infrequencia-2026.10.20-exp1
docker compose --profile cli run --rm -T --no-deps cli frequencia exportacao verificar-compatibilidade \
  var/pacotes/risco-infrequencia-2026.10.20-exp1 \
  --versao-app 1.4.0
```

Sucesso: paridade zero, tamanho até 256 KiB, latência até 5 ms, manifesto íntegro e compatível.

Falha: se tamanho ou latência falharem, simplifique o estudante ou o invólucro, sem remover calibração, conformal ou histerese. Se a paridade falhar, não publique.

`empacotamento montar` é um atalho de remontagem e usa cartão mínimo, sem contexto MEC. Para publicação, prefira o pacote gerado pelo ciclo completo.

## PB-08: promoção, publicação e rollback

Objetivo: levar uma versão homologada ao canal local com aprovação registrada e rollback pronto.

Pré-condições: gates aprovados, pacote íntegro, paridade zero, compatibilidade confirmada, aprovação humana e versão anterior presente no canal.

```bash
docker compose --profile cli run --rm -T --no-deps cli frequencia registro listar
docker compose --profile cli run --rm -T --no-deps cli frequencia publicacao listar

docker compose --profile cli run --rm cli frequencia registro aprovar \
  risco-infrequencia 2026.10.20-exp1 \
  --comentario "gates conferidos e documentação revisada" \
  --ator <pessoa> \
  --papel aprovador

docker compose --profile cli run --rm cli frequencia registro promover \
  risco-infrequencia 2026.10.20-exp1 \
  --estado candidato \
  --justificativa "gates aprovados" \
  --ator <pessoa> \
  --papel aprovador

docker compose --profile cli run --rm cli frequencia registro promover \
  risco-infrequencia 2026.10.20-exp1 \
  --estado homologado \
  --justificativa "revisão concluída" \
  --ator <pessoa> \
  --papel aprovador

docker compose --profile cli run --rm cli frequencia publicacao publicar \
  var/pacotes/risco-infrequencia-2026.10.20-exp1 \
  2026.10.20-exp1 \
  --notas "primeira versão homologada" \
  --ator <pessoa> \
  --papel aprovador

docker compose --profile cli run --rm -T --no-deps cli frequencia publicacao verificar-hash \
  2026.10.20-exp1
docker compose --profile cli run --rm -T --no-deps cli frequencia publicacao verificar-compatibilidade \
  2026.10.20-exp1 \
  --versao-app 1.4.0
docker compose --profile cli run --rm -T --no-deps cli frequencia publicacao listar
```

Rollback:

```bash
# Confirme antes que a versão anterior existe no canal
docker compose --profile cli run --rm -T --no-deps cli frequencia publicacao listar

docker compose --profile cli run --rm cli frequencia publicacao reverter \
  <versao-anterior> \
  --motivo "regressão observada no piloto" \
  --ator <pessoa> \
  --papel aprovador
```

Revogação:

```bash
docker compose --profile cli run --rm cli frequencia publicacao revogar \
  <versao> \
  --motivo "versão retirada por decisão da coordenação" \
  --ator <pessoa> \
  --papel aprovador
```

Sucesso: versão publicada, hash conferido, compatibilidade confirmada, versão anterior disponível e auditoria registrada.

Falha: `publicacao reverter` remove a versão atual antes de validar a anterior. Confirme a versão anterior no canal antes do rollback. `marcar-producao` só altera o registro; não publica arquivos.

## PB-09: monitoramento, drift, recalibração e retreinamento

Objetivo: acompanhar a saúde do modelo e decidir entre manter, recalibrar, retreinar ou revogar.

```bash
docker compose --profile cli run --rm -T --no-deps cli frequencia monitoramento validade
docker compose --profile cli run --rm -T --no-deps cli frequencia monitoramento acuracia-observada
docker compose --profile cli run --rm -T --no-deps cli frequencia monitoramento taxa-descarte

docker compose --profile cli run --rm cli frequencia monitoramento drift \
  var/artefatos/experimentos/exp1 \
  var/dados/importados/<fotografia-atual>

docker compose --profile cli run --rm -T --no-deps cli frequencia monitoramento relatorio-saude \
  --pasta-experimento var/artefatos/experimentos/exp1

docker compose --profile cli run --rm -T --no-deps cli frequencia monitoramento recomendar-retreinamento
```

Recalibração leve:

```bash
docker compose --profile cli run --rm cli frequencia monitoramento recalibrar \
  var/artefatos/experimentos/exp1
docker compose --profile cli run --rm cli frequencia avaliacao validar-gates \
  var/artefatos/experimentos/exp1
docker compose --profile cli run --rm cli frequencia empacotamento montar \
  var/artefatos/experimentos/exp1
docker compose --profile cli run --rm -T --no-deps cli frequencia empacotamento validar \
  var/pacotes/risco-infrequencia-<versao>
```

Retreinamento:

```bash
docker compose --profile cli run --rm cli frequencia datasets construir \
  var/dados/importados/<novo-periodo> \
  --versao retreino-2026-11 \
  --ponto-no-tempo estrito

docker compose --profile cli run --rm cli frequencia experimentos executar \
  var/dados/processados/retreino-2026-11 \
  --identificador retreino-2026-11 \
  --versao-modelo 2026.11.20-retreino

docker compose --profile cli run --rm -T --no-deps cli frequencia experimentos comparar \
  var/artefatos/experimentos/exp1 \
  var/artefatos/experimentos/retreino-2026-11
```

Sucesso: relatório de saúde com recomendação clara e decisão registrada.

Falha: `recalibrar` atualiza apenas `calibracao.json`; reavalie, reexporte e reempacote. `recomendar-retreinamento` sem `--pasta-experimento` não vê o drift.

## PB-10: auditoria, linhagem e incidente de privacidade

Objetivo: prestar contas, reconstruir a linhagem e responder a suspeita de dado pessoal.

```bash
docker compose --profile cli run --rm -T --no-deps cli frequencia auditoria listar --limite 50
docker compose --profile cli run --rm -T --no-deps cli frequencia auditoria filtrar \
  --ator agente:<nome> \
  --acao experimentos \
  --inicio 2026-10-01 \
  --fim 2026-10-31
docker compose --profile cli run --rm -T --no-deps cli frequencia auditoria exportar
docker compose --profile cli run --rm -T --no-deps cli frequencia auditoria verificar-integridade
docker compose --profile cli run --rm -T --no-deps cli frequencia auditoria reconstruir-linhagem \
  var/artefatos/experimentos/exp1
```

Incidente:

```bash
# Pare qualquer treino ou promoção em andamento
docker compose --profile cli run --rm -T --no-deps cli frequencia privacidade relatorio-risco \
  <pasta>
docker compose --profile cli run --rm -T --no-deps cli frequencia privacidade verificar-sensiveis \
  <pasta>
docker compose --profile cli run --rm -T --no-deps cli frequencia privacidade bloquear \
  <pasta> \
  --motivo "suspeita de dado pessoal em texto livre"
```

Sucesso: trilha completa, linhagem reconstruída, incidente registrado e nenhum artefato novo com PII.

Falha: não tente "limpar" a auditoria. Corrija na fonte, reimporte, rode o portão e registre a decisão.

## PB-11: propor e validar uma ideia

Objetivo: atuar como cientista de dados, propor uma hipótese e validá-la de ponta a ponta.

Pré-condições: ler `docs/ciencia-e-inovacao.md` e `references/pesquisa.md`.

Sequência resumida:

1. Varrer monitoramento, avaliação, histórico, limitações, issues e feedback agregado.
2. Propor de 3 a 5 hipóteses, incluindo alternativas simples e não-modelos.
3. Fazer o passe adversarial de vazamento, confusão, seleção, amostra, fairness, custo e ética.
4. Escrever o brief e priorizar com impacto, confiança, esforço e risco.
5. Escrever o protocolo com métricas, limiares, splits, critério de parada e regra de decisão.
6. Pedir aprovação humana antes de executar.
7. Rodar em workspace isolado, com identificador próprio.

```bash
docker compose --profile cli run --rm \
  -e FREQUENCIA_WORKSPACE=/app/var/pesquisa/<slug> \
  -e FREQUENCIA_MLFLOW_URI=sqlite:////app/var/pesquisa/<slug>/mlflow.db \
  --no-deps \
  cli frequencia experimentos executar \
  /app/var/pesquisa/<slug>/dados/processados/<versao> \
  --identificador pesquisa-<slug> \
  --versao-modelo 2026.11.20-pesquisa
```

8. Validar dados, privacidade, features, dataset, gates, paridade, pacote e reprodutibilidade.
9. Montar o pacote de evidências e a nota de pesquisa.
10. Pedir revisão independente com a rubrica.
11. Registrar a decisão, inclusive se for rejeitar.

Sucesso: uma pessoa consegue reproduzir o experimento a partir do pacote de evidências e tomar a decisão sem refazer a análise.

Falha: se o baseline não for superado, se houver vazamento, se a amostra for pequena, se houver lacuna de fairness ou se o custo operacional for alto, pare e registre o resultado negativo. Não ajuste o gate para a ideia passar.
