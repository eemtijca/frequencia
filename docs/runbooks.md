# Runbooks operacionais

Procedimentos passo a passo para as situações do dia a dia. O caminho padrão é Docker. O venv com Python 3.12 é fallback e só deve ser usado quando Docker não estiver disponível. Em automação, use `--json` e caminhos absolutos.

## RB-01: primeiro ciclo numa máquina nova

```bash
docker compose up --build -d
docker compose ps
docker compose --profile ciclo up smoke
```

Verde em tudo: ambiente pronto. Se o build falhar, confira Docker, Compose v2 e espaço em disco. Se o smoke falhar, leia a etapa e rode o comando com `--detalhado`.

Fallback sem Docker, com Python 3.12:

```bash
bash scripts/setup.sh
source .venv/bin/activate
bash scripts/smoke.sh
```

## RB-02: rodar o ciclo com dados novos

```bash
docker compose --profile cli run --rm cli frequencia dados importar \
  <pasta> \
  --origem sintetico \
  --licenca "dados abertos"

docker compose --profile cli run --rm cli frequencia datasets construir \
  var/dados/importados/<id> \
  --versao v<N> \
  --ponto-no-tempo estrito

docker compose --profile cli run --rm cli frequencia experimentos executar \
  var/dados/processados/v<N> \
  --identificador exp<N> \
  --versao-modelo <versao-modelo>

docker compose --profile cli run --rm cli frequencia avaliacao validar-gates \
  var/artefatos/experimentos/exp<N>
```

Cada etapa é idempotente: reexecutar pula o que concluiu. Interrompido no meio, use `experimentos recuperar <id>`.

## RB-03: publicar uma versão homologada

Siga [publicacao-de-modelos.md](publicacao-de-modelos.md). Resumo:

```bash
docker compose --profile cli run --rm -T --no-deps cli frequencia registro listar
docker compose --profile cli run --rm -T --no-deps cli frequencia publicacao listar

docker compose --profile cli run --rm cli frequencia registro aprovar \
  risco-infrequencia <versao> \
  --comentario "gates e documentação revisados" \
  --ator <pessoa> \
  --papel aprovador

docker compose --profile cli run --rm cli frequencia registro promover \
  risco-infrequencia <versao> \
  --estado candidato \
  --justificativa "gates aprovados" \
  --ator <pessoa> \
  --papel aprovador

docker compose --profile cli run --rm cli frequencia registro promover \
  risco-infrequencia <versao> \
  --estado homologado \
  --justificativa "revisão concluída" \
  --ator <pessoa> \
  --papel aprovador

docker compose --profile cli run --rm cli frequencia publicacao publicar \
  var/pacotes/risco-infrequencia-<versao> \
  <versao> \
  --notas "<notas>" \
  --ator <pessoa> \
  --papel aprovador
```

## RB-04: investigar queda de qualidade

```bash
docker compose --profile cli run --rm -T --no-deps cli frequencia monitoramento relatorio-saude \
  --pasta-experimento var/artefatos/experimentos/<exp>

docker compose --profile cli run --rm cli frequencia monitoramento drift \
  var/artefatos/experimentos/<exp> \
  var/dados/importados/<fotografia-atual>

docker compose --profile cli run --rm -T --no-deps cli frequencia avaliacao subgrupos \
  var/artefatos/experimentos/<exp>

docker compose --profile cli run --rm -T --no-deps cli frequencia avaliacao fairness \
  var/artefatos/experimentos/<exp>
```

Decida entre recalibração leve (RB-05) e retreinamento (RB-06) conforme [retreinamento-e-recalibracao.md](retreinamento-e-recalibracao.md).

## RB-05: recalibrar sem retreinar

```bash
docker compose --profile cli run --rm cli frequencia monitoramento recalibrar \
  var/artefatos/experimentos/<exp>

docker compose --profile cli run --rm cli frequencia avaliacao validar-gates \
  var/artefatos/experimentos/<exp>

docker compose --profile cli run --rm cli frequencia empacotamento montar \
  var/artefatos/experimentos/<exp>

docker compose --profile cli run --rm -T --no-deps cli frequencia empacotamento validar \
  var/pacotes/risco-infrequencia-<versao>
```

O pacote regravado carrega os parâmetros novos. Siga a publicação do RB-03.

## RB-06: retreinar com dados recentes

Siga [retreinamento-e-recalibracao.md](retreinamento-e-recalibracao.md): dataset novo, experimento novo, comparação com a versão atual, promoção com rollback planejado.

```bash
docker compose --profile cli run --rm cli frequencia experimentos comparar \
  var/artefatos/experimentos/<exp-atual> \
  var/artefatos/experimentos/<exp-novo>

docker compose --profile cli run --rm -T --no-deps cli frequencia registro comparar \
  risco-infrequencia <versao-atual> <versao-nova>
```

## RB-07: rollback de emergência

```bash
# Confirme a versão anterior no canal antes de reverter
docker compose --profile cli run --rm -T --no-deps cli frequencia publicacao listar

docker compose --profile cli run --rm cli frequencia publicacao reverter \
  <versao-anterior> \
  --motivo "regressão observada no piloto" \
  --ator <pessoa> \
  --papel aprovador
```

Se não houver versão anterior, revogue e deixe o fallback ativo:

```bash
docker compose --profile cli run --rm cli frequencia publicacao revogar \
  <versao> \
  --motivo "versão retirada por decisão da coordenação" \
  --ator <pessoa> \
  --papel aprovador
```

## RB-08: suspeita de dado pessoal no fluxo

1. Não treine nem promova nada.
2. Rode o relatório de risco e a varredura de sensíveis.
3. Se houver achado, corrija na fonte e reimporte; se precisar manter o texto, pseudonimize.
4. Registre o incidente conforme [privacidade-lgpd.md](privacidade-lgpd.md).

```bash
docker compose --profile cli run --rm -T --no-deps cli frequencia privacidade relatorio-risco <pasta>
docker compose --profile cli run --rm -T --no-deps cli frequencia privacidade verificar-sensiveis <pasta>
docker compose --profile cli run --rm cli frequencia privacidade pseudonimizar <pasta> --colunas nome
docker compose --profile cli run --rm cli frequencia privacidade bloquear \
  <pasta> \
  --motivo "suspeita de dado pessoal em texto livre" \
  --ator <pessoa>
```

## RB-09: experimento travado ou interrompido

```bash
docker compose --profile cli run --rm cli frequencia experimentos interromper <id>
docker compose --profile cli run --rm cli frequencia experimentos recuperar <id>
```

O estado por etapa fica em `var/artefatos/experimentos/<id>/estado.json`; etapas concluídas não reexecutam sem `--forca` com justificativa.

## RB-10: backup do workspace

No Docker, o workspace está no volume `dados`.

```bash
# Backup do volume
docker run --rm \
  -v frequencia_dados:/dados \
  -v "$PWD":/backup \
  alpine tar czf /backup/var-docker.tar.gz -C /dados .
```

No venv, copie a pasta `var/` local:

```bash
tar czf var-venv.tar.gz var
```

Confirme o nome do volume antes do backup:

```bash
docker volume ls
```

## RB-11: verificação de integridade periódica

```bash
docker compose --profile cli run --rm -T --no-deps cli frequencia auditoria verificar-integridade
docker compose --profile cli run --rm -T --no-deps cli frequencia publicacao verificar-hash <versao-atual>
docker compose --profile cli run --rm -T --no-deps cli frequencia dados verificar-integridade <pasta-de-dados>
```

Três ângulos: manifestos das publicações, modelo publicado e pacotes de dados importados.

## RB-12: restore do volume Docker

A restauração apaga o conteúdo atual do volume. Use apenas com backup conferido.

```bash
docker compose down

docker run --rm \
  -v frequencia_dados:/dados \
  -v "$PWD":/backup \
  alpine sh -c "rm -rf /dados/* && tar xzf /backup/var-docker.tar.gz -C /dados"

docker compose up --build -d
docker compose ps
```

Depois do restore, rode a verificação de integridade do RB-11.
