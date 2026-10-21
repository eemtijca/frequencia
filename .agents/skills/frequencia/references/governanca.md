# Governança, promoção e publicação

Regras de decisão para levar uma versão do experimental ao publicado, com aprovação, auditoria, rollback e resposta a incidente.

## Papéis e separação de deveres

| Papel | Pode | Não pode |
| --- | --- | --- |
| observador | ler painel, relatórios e auditoria | executar mudanças de estado |
| cientista | analisar, treinar, avaliar e comparar | promover a homologado ou publicado |
| engenheiro | operar a CLI, empacotar, publicar com aprovação e monitorar | aprovar a própria versão |
| aprovador | aprovar, promover a homologado, publicar, reverter e revogar | delegar a decisão ao agente |

- O agente propõe, executa e documenta. A pessoa aprova.
- O agente registra suas ações com `--ator agente:<nome>`.
- A aprovação usa `--ator <pessoa>` e `--papel aprovador`.
- O agente nunca usa `--papel aprovador` sem autorização humana explícita.
- O revisor de uma versão não deve ser o mesmo agente que a construiu.
- A trilha de auditoria é append-only. Não edite `auditoria.jsonl`.

## Estados e transições

| Estado | Significado | Próximos |
| --- | --- | --- |
| experimental | ciclo concluído, gates avaliados | candidato, descontinuado, arquivado |
| candidato | gates aprovados, aguardando revisão | homologado, experimental, descontinuado, arquivado |
| homologado | revisão concluída e aprovação registrada | publicado, candidato, descontinuado, arquivado |
| publicado | no canal local de releases | descontinuado, arquivado |
| descontinuado | retirado por rollback, revogação ou substituição | arquivado |
| arquivado | fora do ciclo ativo, apenas histórico | nenhum |

Promoção a homologado ou publicado exige papel de aprovador. A aprovação é um registro separado, feito com `registro aprovar`. O comando de promoção não verifica a lista de aprovações; a responsabilidade é do operador e do processo.

## Checklist de promoção

- [ ] O experimento concluiu as sete etapas.
- [ ] `gates.json` tem `aprovado` verdadeiro.
- [ ] A calibração foi revisada e o ECE está dentro do limite.
- [ ] A cobertura conformal está dentro do limite.
- [ ] A taxa de alerta é compatível com a capacidade da coordenação.
- [ ] O ganho sobre o baseline é positivo.
- [ ] Subgrupos e fairness foram analisados.
- [ ] O tamanho e a latência estão dentro do limite.
- [ ] A paridade Python e JavaScript é zero.
- [ ] O pacote está íntegro e o manifesto é válido.
- [ ] A documentação e o cartão do modelo estão atualizados.
- [ ] A aprovação humana foi registrada com ator e comentário.
- [ ] Há plano de rollback e versão anterior disponível.

## Fluxo de promoção

```bash
# 1. Conferir o estado atual
docker compose --profile cli run --rm -T --no-deps cli frequencia registro listar

# 2. Registrar a aprovação humana
docker compose --profile cli run --rm cli frequencia \
  --ator <pessoa> --papel aprovador \
  registro aprovar \
  risco-infrequencia <versao> \
  --comentario "gates e documentação revisados"

# 3. Promover para candidato
docker compose --profile cli run --rm cli frequencia \
  --ator <pessoa> --papel aprovador \
  registro promover \
  risco-infrequencia <versao> \
  --estado candidato \
  --justificativa "gates aprovados"

# 4. Promover para homologado
docker compose --profile cli run --rm cli frequencia \
  --ator <pessoa> --papel aprovador \
  registro promover \
  risco-infrequencia <versao> \
  --estado homologado \
  --justificativa "revisão concluída"
```

## Checklist de publicação

- [ ] A versão está homologada.
- [ ] O pacote está no caminho `var/pacotes/risco-infrequencia-<versao>`.
- [ ] `empacotamento validar` confirma hashes e manifesto.
- [ ] `exportacao testar-sinteticos` tem divergência zero.
- [ ] `publicacao verificar-compatibilidade` confirma a versão mínima do app.
- [ ] As notas de mudança estão escritas em português claro.
- [ ] A versão anterior está presente no canal para rollback.
- [ ] A aprovação humana está registrada.
- [ ] A publicação usa `--papel aprovador`.
- [ ] O hash é conferido depois da publicação.
- [ ] A auditoria registra a ação.

## Fluxo de publicação

```bash
docker compose --profile cli run --rm -T --no-deps cli frequencia publicacao listar

docker compose --profile cli run --rm cli frequencia \
  --ator <pessoa> --papel aprovador \
  publicacao publicar \
  var/pacotes/risco-infrequencia-<versao> \
  <versao> \
  --notas "o que mudou para a escola"

docker compose --profile cli run --rm -T --no-deps cli frequencia publicacao verificar-hash <versao>
docker compose --profile cli run --rm -T --no-deps cli frequencia publicacao verificar-compatibilidade \
  <versao> \
  --versao-app 1.4.0
docker compose --profile cli run --rm -T --no-deps cli frequencia publicacao instrucoes <versao>
```

## Rollback e revogação

- `publicacao reverter <versao_anterior>` descontinua a versão atual e restaura a anterior.
- O comando remove a pasta da versão atual antes de validar se a anterior existe. Confirme a versão anterior no canal antes de reverter.
- `publicacao revogar <versao>` remove o canal e descontinua a versão. O app cai no fallback.
- Use `--papel aprovador` e registre o motivo.
- Depois do rollback, confira o hash e a compatibilidade da versão restaurada.
- `marcar-producao` só altera o registro. Não copia arquivos nem cria canal.

```bash
docker compose --profile cli run --rm -T --no-deps cli frequencia publicacao listar

docker compose --profile cli run --rm cli frequencia \
  --ator <pessoa> --papel aprovador \
  publicacao reverter \
  <versao-anterior> \
  --motivo "regressão observada no piloto"
```

## Auditoria e linhagem

```bash
docker compose --profile cli run --rm -T --no-deps cli frequencia auditoria listar --limite 50
docker compose --profile cli run --rm -T --no-deps cli frequencia auditoria filtrar \
  --ator <pessoa> \
  --acao modelo \
  --inicio 2026-10-01 \
  --fim 2026-10-31
docker compose --profile cli run --rm -T --no-deps cli frequencia auditoria exportar
docker compose --profile cli run --rm -T --no-deps cli frequencia auditoria verificar-integridade
docker compose --profile cli run --rm -T --no-deps cli frequencia auditoria reconstruir-linhagem \
  var/artefatos/experimentos/<id>
```

A trilha mostra quem agiu, com qual papel, quando e sobre qual alvo. Ela não guarda conteúdo de frequência nem dado pessoal.

## Incidente de privacidade

1. Pare qualquer treino, promoção ou publicação.
2. Rode o relatório de risco e a varredura de sensíveis.
3. Se houver achado, corrija na fonte ou pseudonimize.
4. Reimporte o pacote e repita o portão.
5. Registre o incidente e a decisão.
6. Não treine, não promova e não publique enquanto o portão estiver vermelho.

```bash
docker compose --profile cli run --rm -T --no-deps cli frequencia privacidade relatorio-risco <pasta>
docker compose --profile cli run --rm -T --no-deps cli frequencia privacidade verificar-sensiveis <pasta>
docker compose --profile cli run --rm cli frequencia \
  --ator <pessoa> \
  privacidade bloquear \
  <pasta> \
  --motivo "suspeita de dado pessoal em texto livre"
```

`privacidade bloquear` apenas registra auditoria. O bloqueio efetivo é `privacidade validar-entrada-treino`.

## Armadilhas de governança

- O ciclo completo termina mesmo com gates reprovados. Leia `gates.json`.
- `empacotamento homologacao` não pula estados. Use candidato antes de homologado.
- `empacotamento publicacao` e `publicacao publicar` exigem papel de aprovador.
- `publicacao revogar` não verifica papel no código, mas a política exige aprovação humana.
- `publicacao reverter` remove a versão atual antes de validar a anterior.
- `marcar-producao` não publica arquivos.
- `registro registrar` é para artefatos manuais ou externos. O ciclo completo registra automaticamente em experimental.
- `registro atualizar-estado` é um alias de promoção; use com cuidado.
- `dados importar` copia o pacote para `var/dados/importados`. Use o caminho do manifesto.
- `pseudonimizar` invalida os hashes do `meta.json`. Reimporte.
- O presidio só roda em `privacidade verificar-sensiveis`.
- O host com Python 3.15 não serve. Use Docker ou Python 3.12.
- O volume `dados` do Docker é separado do `var/` local do venv.

## Modelos de relatório

### Resumo de experimento

```text
# Experimento <id>

## Objetivo
<problema e decisão apoiada>

## Dados e contrato
<dataset, versão, hash, features e privacidade>

## Configuração
<semente, dobras, tentativas, versão do modelo>

## Métricas globais
<AUC, AP, logloss, Brier, ECE, cobertura, taxa de alerta, Top-10>

## Subgrupos e fairness
<séries, faixas de histórico, dispersão>

## Gates
<vereditos e evidência>

## Riscos e limitações
<o que não foi medido, o que pode mudar>

## Próximo passo
<adotar, iterar, estacionar ou rejeitar>
```

### Diagnóstico de gates

```text
# Diagnóstico de gates

| Gate | Valor | Limite | Veredito | Evidência |
| --- | --- | --- | --- | --- |

## Causa provável
<hipótese principal e alternativas>

## Ação recomendada
<o que fazer antes de repetir>

## O que não fazer
<não afrouxar gate, não ajustar no teste, não esconder resultado>
```

### Prontidão de publicação

```text
# Prontidão de publicação <versao>

- Gates:
- Aprovação:
- Integridade:
- Compatibilidade:
- Paridade:
- Rollback:
- Riscos:
- Decisão: pronta ou bloqueada
```
