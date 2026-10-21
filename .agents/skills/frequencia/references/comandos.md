# Catálogo de comandos do FrequencIA

Referência completa dos 94 comandos da CLI, organizados pelos 12 grupos funcionais. A fonte de verdade é o próprio CLI:

```bash
frequencia <grupo> <comando> --help
```

Este catálogo resume quando usar, quais flags importam e qual efeito esperar.

## Ambiente de execução

Prefira Docker. Use o venv com Python 3.12 apenas como fallback.

```bash
# Ambiente completo
docker compose up --build -d
docker compose --profile ciclo up smoke

# Comando pontual
docker compose --profile cli run --rm cli frequencia --help

# Testes e qualidade
docker compose --profile cli run --rm -T --no-deps cli python -m pytest tests -q
docker compose --profile cli run --rm -T --no-deps cli ruff check src tests
docker compose --profile cli run --rm -T --no-deps cli mypy src/frequencia
docker compose --profile cli run --rm -T --no-deps cli ruff format --check src tests
```

Fallback com venv, somente quando Docker não estiver disponível:

```bash
source .venv/bin/activate
frequencia --help
```

O host com Python 3.15 não é suportado. O volume `dados` do Docker é separado do `var/` local do venv.

## Flags globais

As flags globais vêm antes do grupo.

| Flag | Efeito |
| --- | --- |
| `--json` | saída estruturada para scripts; vence `--silencioso` |
| `--seco` | ensaia sem gravar, quando o comando suporta |
| `--detalhado` | logs detalhados e stack trace para diagnóstico |
| `--silencioso` | suprime a saída humana |
| `--perfil` | perfil de ambiente: `padrao`, `fumaca` ou `ciclo` |
| `--workspace` | pasta raiz do workspace |
| `--forca` | reexecuta etapas concluídas; exige `--justificativa` |
| `--justificativa` | motivo registrado na auditoria |
| `--ator` | identidade que opera; use `agente:<nome>` para ações de agente |
| `--papel` | `observador`, `cientista`, `engenheiro` ou `aprovador` |

```bash
# A flag global vem antes do grupo
docker compose --profile cli run --rm cli frequencia --json dados validar var/dados/sinteticos/demo
```

## Dados

| Comando | Quando usar | Flags e efeitos |
| --- | --- | --- |
| `dados listar-fontes` | Ver o catálogo de fontes MEC e INEP | sem flags específicas |
| `dados importar <pasta>` | Registrar importação com validação, hash e PII | `--origem sintetico,mec,institucional`; `--licenca`; `--base-legal` obrigatória para institucional |
| `dados validar <pasta>` | Validar o esquema das onze tabelas | sem flags específicas |
| `dados verificar-licenca <identificador>` | Conferir licença e restrições de uma fonte | sem flags específicas |
| `dados registrar-hash <pasta>` | Calcular SHA-256 da pasta | grava o hash no log estruturado |
| `dados gerar-perfil <pasta>` | Gerar perfil estatístico por tabela | sem flags específicas |
| `dados detectar-pii <pasta>` | Varrer PII com as regras próprias | não aciona o presidio; use também `privacidade verificar-sensiveis` |
| `dados versionar <pasta>` | Versionar com DVC sem Git | depende do DVC e do formato do `.dvc` |
| `dados gerar-sintetico` | Gerar pacote sintético determinístico | `--perfil amostra,fumaca,padrao`; `--semente`; `--ano`; `--alunos`; `--destino` |
| `dados verificar-integridade <pasta>` | Conferir hashes contra o `meta.json` | sem flags específicas |

## Privacidade

| Comando | Quando usar | Flags e efeitos |
| --- | --- | --- |
| `privacidade verificar-identificadores <pasta>` | Barrar colunas identificadoras diretas | sem flags específicas |
| `privacidade verificar-sensiveis <pasta>` | Varrer textos com regex e presidio | mais profundo que `dados detectar-pii` |
| `privacidade pseudonimizar <pasta>` | Aplicar hash determinístico | `--colunas`; `--destino`; invalida hashes do `meta.json` |
| `privacidade relatorio-risco <pasta>` | Gerar relatório de risco | `--base-legal` |
| `privacidade validar-entrada-treino <pasta>` | Executar o portão antes do treino | `--exigir-base-legal` para institucional |
| `privacidade bloquear <pasta>` | Registrar bloqueio na auditoria | `--motivo`; não impede tecnicamente o treino |

## Features

| Comando | Quando usar | Flags e efeitos |
| --- | --- | --- |
| `features listar` | Listar as 47 features do catálogo | sem flags específicas |
| `features validar-contrato` | Validar nomes, tipos e vocabulários | sem flags específicas |
| `features gerar-dicionario` | Exportar o catálogo em JSON | `--destino`; não gera o Markdown |
| `features verificar-dependencia` | Ver features por flag do FrequenciApp | sem flags específicas |
| `features gerar-distribuicao <pasta_dataset>` | Resumir distribuição das features | `--feature` para uma única feature |
| `features detectar-constantes <pasta_dataset>` | Apontar features sem variação | sem flags específicas |
| `features detectar-nulos <pasta_dataset>` | Contar nulos após os padrões | sem flags específicas |
| `features verificar-vazamento <pasta_dataset>` | Verificar ausência de futuro | sem flags específicas |
| `features congelar` | Congelar a versão do catálogo | `--destino`; grava auditoria |

## Datasets

| Comando | Quando usar | Flags e efeitos |
| --- | --- | --- |
| `datasets construir <pasta_dados>` | Construir o dataset temporal | `--horizonte`; `--limiar-rotulo`; `--min-historico`; `--passo`; `--ponto-no-tempo estrito,atual`; `--perfil`; `--versao` |
| `datasets separar <pasta_dataset>` | Ver fronteiras temporais e divisão | sem flags específicas |
| `datasets gerar-por-perfil <pasta_dados>` | Restringir o dataset a um perfil de escola | `--perfil`; `--versao` |
| `datasets validar-ausencia-futuro <pasta_dataset>` | Verificar vazamento por reconstrução | sem flags específicas |
| `datasets registrar-linhagem <pasta_dataset>` | Registrar linhagem na auditoria | sem flags específicas |
| `datasets listar` | Listar datasets no workspace | sem flags específicas |

Use `ponto_no_tempo estrito` para treino. `atual` serve apenas para avaliação retrospectiva.

## Experimentos

| Comando | Quando usar | Flags e efeitos |
| --- | --- | --- |
| `experimentos criar <pasta_dataset>` | Gravar configuração declarativa | `--identificador`; `--semente`; `--versao-modelo`; `--config` |
| `experimentos executar <pasta_dataset>` | Executar o ciclo completo | `--identificador`; `--semente`; `--tentativas`; `--dobras`; `--versao-modelo`; `--min-app`; `--forca` exige `--justificativa` |
| `experimentos treinar <pasta_dataset>` | Executar apenas o treino | baixo nível; prefira o ciclo completo |
| `experimentos ensemble <pasta_experimento>` | Executar apenas o ensemble | exige dataset e estado do experimento |
| `experimentos destilar <pasta_experimento>` | Executar apenas a destilação | exige a etapa de ensemble (`ensemble/oof.npz`); a calibração vem depois |
| `experimentos listar` | Listar experimentos do workspace | sem flags específicas |
| `experimentos comparar <experimentos...>` | Comparar métricas lado a lado | aceita duas ou mais pastas |
| `experimentos interromper <identificador>` | Marcar experimento como interrompido | grava auditoria |
| `experimentos recuperar <identificador>` | Retomar do ponto de parada | remove a marca de interrupção |
| `experimentos relatorio <pasta_experimento>` | Ler o relatório de avaliação | exige `relatorio-avaliacao.md` |

## Avaliação

| Comando | Quando usar | Flags e efeitos |
| --- | --- | --- |
| `avaliacao modelo <pasta_experimento>` | Ver métricas globais | lê `avaliacao.json` |
| `avaliacao calibracao <pasta_experimento>` | Ver calibração e conformal | lê `calibracao.json` |
| `avaliacao ensemble <pasta_experimento>` | Ver pesos e discordância | lê o estado da etapa de ensemble |
| `avaliacao subgrupos <pasta_experimento>` | Ver desempenho por série e histórico | lê `avaliacao.json` |
| `avaliacao fairness <pasta_experimento>` | Ver dispersão de recall e alerta | exige grupos com amostra mínima |
| `avaliacao curva-aprendizado <pasta_experimento>` | Ver qualidade por volume de histórico | lê `avaliacao.json` |
| `avaliacao custo-operacional <pasta_experimento>` | Ver alertas por dia e falsos positivos | foco na capacidade da coordenação |
| `avaliacao baseline <pasta_experimento>` | Comparar com o baseline de regras | lê `avaliacao.json` |
| `avaliacao validar-gates <pasta_experimento>` | Aplicar os gates de promoção | usa tamanho e latência de `exportacoes/validacao.json` quando existir |
| `avaliacao relatorio <pasta_experimento>` | Ler o relatório em Markdown | exige `relatorio-avaliacao.md` |

O ciclo grava `gates.json` mesmo quando o veredito é reprovado. `avaliacao validar-gates` recalcula e emite o veredito, mas não substitui o arquivo do ciclo.

## Exportação

| Comando | Quando usar | Flags e efeitos |
| --- | --- | --- |
| `exportacao validar-contratos <pacote>` | Validar o contrato do manifesto | exige `manifest.json` |
| `exportacao verificar-tamanho-latencia <pasta_experimento>` | Conferir tamanho e latência | lê `exportacoes/validacao.json` |
| `exportacao artefato-teste <pasta_experimento>` | Ver os casos sintéticos | lê `exportacoes/dados-teste.json` |
| `exportacao testar-sinteticos <pacote>` | Rodar paridade no Node | exige Node; espera divergência zero |
| `exportacao verificar-compatibilidade <pacote>` | Conferir versão mínima do app | `--versao-app` |
| `exportacao hash <pasta_experimento>` | Ver hashes do modelo e do estudante | sem flags específicas |
| `exportacao registrar <pasta_experimento>` | Registrar a exportação na auditoria | lê `validacao.json` |

## Empacotamento

| Comando | Quando usar | Flags e efeitos |
| --- | --- | --- |
| `empacotamento montar <pasta_experimento>` | Remontar o pacote a partir dos artefatos | usa cartão mínimo e sem contexto MEC |
| `empacotamento validar <pacote>` | Conferir arquivos e hashes do manifesto | sem flags específicas |
| `empacotamento homologacao <pacote>` | Tentar promover para homologado | `--versao`; a transição válida exige candidato antes |
| `empacotamento publicacao <pacote> <versao>` | Publicar pelo atalho de empacotamento | `--notas`; exige papel de aprovador |
| `empacotamento assinar <pacote>` | Conferir assinatura lógica | compara hashes do manifesto |

## Registro

| Comando | Quando usar | Flags e efeitos |
| --- | --- | --- |
| `registro registrar <identificador> <versao>` | Registrar artefato manual ou externo | `--artefato`; `--validade` |
| `registro promover <identificador> <versao>` | Promover entre estados | `--estado`; `--justificativa`; candidato exige gates aprovados; homologado e publicado exigem aprovação vigente e a opção global `--papel aprovador`, antes do grupo |
| `registro descontinuar <identificador> <versao>` | Descontinuar com motivo | `--motivo` |
| `registro arquivar <identificador> <versao>` | Retirar do ciclo ativo | sem flags específicas |
| `registro atualizar-estado <identificador> <versao>` | Atualizar situação com validação | `--situacao` |
| `registro listar [identificador]` | Listar versões e situações | padrão `risco-infrequencia` |
| `registro comparar <identificador> <versao_a> <versao_b>` | Comparar métricas de duas versões | sem flags específicas |
| `registro aprovar <identificador> <versao>` | Registrar aprovação | `--comentario` |
| `registro rejeitar <identificador> <versao>` | Registrar rejeição | `--comentario` |

## Publicação

| Comando | Quando usar | Flags e efeitos |
| --- | --- | --- |
| `publicacao publicar <pacote> <versao>` | Publicar no canal local | `--notas`; exige a opção global `--papel aprovador`, antes do grupo; recusa pacote com hash diferente do registrado |
| `publicacao release <versao>` | Listar arquivos do release local | sem flags específicas |
| `publicacao verificar-compatibilidade <versao>` | Conferir versão mínima do app | `--versao-app` |
| `publicacao verificar-hash <versao>` | Conferir hash do modelo publicado | sem flags específicas |
| `publicacao instrucoes <versao>` | Ler as instruções de consumo | sem flags específicas |
| `publicacao marcar-producao <versao>` | Marcar a versão como publicada no registro | `--justificativa`; não copia arquivos |
| `publicacao reverter <versao_anterior>` | Fazer rollback para versão anterior | `--motivo`; confirme a versão anterior antes |
| `publicacao revogar <versao>` | Revogar uma versão publicada | `--motivo`; use papel de aprovador por política |
| `publicacao listar` | Listar versões publicadas | sem flags específicas |

## Monitoramento

| Comando | Quando usar | Flags e efeitos |
| --- | --- | --- |
| `monitoramento importar-feedback <arquivo>` | Registrar feedback agregado por dia | `--fonte`; nunca importe registro individual |
| `monitoramento acuracia-observada` | Resumir acurácia do feedback recente | sem flags específicas |
| `monitoramento taxa-descarte` | Resumir taxa de descarte | sem flags específicas |
| `monitoramento drift <pasta_experimento> <pasta_atual>` | Calcular PSI por feature | grava `drift.json` no experimento |
| `monitoramento validade` | Conferir validade da versão publicada | sem flags específicas |
| `monitoramento recalibrar <pasta_experimento>` | Recalcular Platt e conformal | exige estudante e dataset do experimento; não reexporta nem reempacota |
| `monitoramento relatorio-saude` | Gerar relatório de saúde | `--pasta-experimento` para incluir drift |
| `monitoramento recomendar-retreinamento` | Recomendar ação com base na saúde | sem `--pasta-experimento`, não vê drift |

## Auditoria

| Comando | Quando usar | Flags e efeitos |
| --- | --- | --- |
| `auditoria listar` | Ver eventos recentes | `--limite` |
| `auditoria filtrar` | Filtrar por ator, ação, alvo e período | `--ator`; `--acao`; `--alvo`; `--inicio`; `--fim` |
| `auditoria exportar` | Exportar a trilha em JSON | `--destino` |
| `auditoria verificar-integridade` | Conferir hashes das publicações | sem flags específicas |
| `auditoria reconstruir-linhagem <pasta_experimento>` | Reconstruir dados, dataset e etapas | sem flags específicas |

## Exemplos canônicos

```bash
# Ciclo completo com dados sintéticos
docker compose --profile cli run --rm cli frequencia dados gerar-sintetico \
  --perfil fumaca \
  --destino var/dados/sinteticos/demo

docker compose --profile cli run --rm cli frequencia privacidade validar-entrada-treino \
  var/dados/sinteticos/demo

docker compose --profile cli run --rm cli frequencia datasets construir \
  var/dados/sinteticos/demo \
  --versao demo

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

```bash
# Aprovação, promoção e publicação, sempre com pessoa aprovadora
docker compose --profile cli run --rm cli frequencia \
  --ator <pessoa> --papel aprovador \
  registro aprovar \
  risco-infrequencia 2026.10.20-demo \
  --comentario "gates conferidos e documentação revisada"

docker compose --profile cli run --rm cli frequencia \
  --ator <pessoa> --papel aprovador \
  registro promover \
  risco-infrequencia 2026.10.20-demo \
  --estado candidato \
  --justificativa "gates aprovados"

docker compose --profile cli run --rm cli frequencia \
  --ator <pessoa> --papel aprovador \
  registro promover \
  risco-infrequencia 2026.10.20-demo \
  --estado homologado \
  --justificativa "revisão concluída"

docker compose --profile cli run --rm cli frequencia \
  --ator <pessoa> --papel aprovador \
  publicacao publicar \
  var/pacotes/risco-infrequencia-2026.10.20-demo \
  2026.10.20-demo \
  --notas "primeira versão homologada"
```

## Manutenção

Esta tabela reflete a CLI da versão 0.1.0. Se um comando não aparecer aqui, consulte:

```bash
frequencia <grupo> --help
```

Ao mudar a CLI, atualize este catálogo no mesmo pull request e rode a guarda editorial.
