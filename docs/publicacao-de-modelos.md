# Publicação de modelos

Do experimento aprovado ao pacote ativo no FrequenciApp, com critérios objetivos, confirmação dupla e rollback. A publicação local usa var/publicacoes como canal; a entrega ao app é cópia do zip pelo canal que a escola escolher.

## Gates de promoção

Uma versão só anda para frente com todos os gates aprovados. Os limites vivem em `pipelines/avaliacao.py` e a mudança deles exige ADR.

| Gate | Limite padrão | Mede |
| --- | --- | --- |
| auc | AUC mínima 0,70 no teste | Capacidade de ordenação |
| ece | ECE máximo 0,10 | Calibração da probabilidade |
| cobertura_conformal | Cobertura mínima 0,80 | Menor cobertura por classe dos conjuntos conformes, medida no teste |
| taxa_alerta | Máxima 0,35 | Custo operacional da coordenação |
| melhora_sobre_baseline | Mínima 0 | Ganho sobre as regras simples |
| tamanho_pacote | Máximo 256 KiB | Leveza para celular modesto |
| latencia | Máxima 5 ms | Resposta no navegador |

O comando `avaliacao validar-gates` aplica os gates com o tamanho e a latência medidos da exportação, e o resultado fica gravado em gates.json do experimento.

O veredito também é gravado na versão do registro, e o motor recusa a promoção quando falta requisito: candidato exige gates aprovados; homologado e publicado exigem ainda aprovação registrada vigente, em que a decisão mais recente sobre a versão é aprovação (ADR-018). Descontinuar e arquivar nunca ficam bloqueados.

Os gates respondem "podemos?". A revisão científica responde "devemos?". Mudanças estruturais precisam das duas; o método está em [ciencia-e-inovacao.md](ciencia-e-inovacao.md).

## Fluxo de promoção

Os comandos abaixo usam Docker. No fallback venv, ative o ambiente e troque o prefixo Docker por `frequencia`.

```bash
# 1. Ciclo completo com gates aprovados
docker compose --profile cli run --rm cli frequencia experimentos executar \
  var/dados/processados/<dataset> \
  --identificador exp1 \
  --versao-modelo <versao-modelo>

# 2. Aprovação e promoção com papel de aprovador
docker compose --profile cli run --rm cli frequencia \
  --ator <pessoa> --papel aprovador \
  registro aprovar \
  risco-infrequencia <versao> \
  --comentario "gates e documentação revisados"

docker compose --profile cli run --rm cli frequencia \
  --ator <pessoa> --papel aprovador \
  registro promover \
  risco-infrequencia <versao> \
  --estado candidato \
  --justificativa "gates aprovados"

docker compose --profile cli run --rm cli frequencia \
  --ator <pessoa> --papel aprovador \
  registro promover \
  risco-infrequencia <versao> \
  --estado homologado \
  --justificativa "revisão concluída"

# 3. Publicação do pacote homologado
docker compose --profile cli run --rm cli frequencia \
  --ator <pessoa> --papel aprovador \
  publicacao publicar \
  var/pacotes/risco-infrequencia-<versao> \
  <versao> \
  --notas "<notas>"

# 4. Conferência pós-publicação
docker compose --profile cli run --rm -T --no-deps cli frequencia publicacao verificar-hash <versao>
docker compose --profile cli run --rm -T --no-deps cli frequencia publicacao verificar-compatibilidade \
  <versao> \
  --versao-app 1.4.0
```

No painel web, o mesmo fluxo mora na página Registro e promoção (com checklist e confirmação dupla) e na página Publicação (com rollback e revogação).

## Conteúdo do release local

| Arquivo | Papel |
| --- | --- |
| modelo.js, fallback.js, manifest.json, dados-teste.json | O pacote de inferência completo |
| modelo-cartao.md | Cartão de governança da versão |
| LEIA-ME.md, contexto-mec.json | Instruções de consumo e contexto MEC |
| notas-de-mudanca.md | O que mudou nesta versão |
| instrucoes-de-consumo.md | Passo a passo para o app |

## Rollback e revogação

- **Rollback** (`publicacao reverter <versao_anterior>`): descontinua a atual e restaura a anterior ainda presente no canal, com motivo auditado.
- **Revogação** (`publicacao revogar <versao>`): remove o canal e descontinua a versão; o app cai no fallback quando a versão desaparece.
- Ambas exigem papel de aprovador e ficam na trilha de auditoria.

## Checklist de publicação

1. Gates aprovados e gravados no experimento e no registro (verificado pelo motor).
2. Aprovação registrada e não revogada por rejeição posterior (verificado pelo motor).
3. Integridade do pacote conferida (hashes do manifesto e hash do `modelo.js` igual ao registrado, verificado pelo motor).
4. Compatibilidade com a versão mínima do app confirmada.
5. Dados-teste rodando no Node com divergência zero.
6. Notas de mudança escritas para a coordenação em português claro.
7. Plano de rollback identificado (versão anterior presente no canal).
