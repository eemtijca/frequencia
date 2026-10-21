# Contrato do manifesto

O manifest.json é o documento que o FrequenciApp lê antes de qualquer coisa. O app nunca adivinha compatibilidade: decide pela versão mínima, pela validade, pelo hash e pela autoverificação. Este contrato define os campos e a validação aplicada no empacotamento e na publicação.

## Campos obrigatórios

| Campo | Tipo | Papel |
| --- | --- | --- |
| versao_manifesto | texto | Versão do formato do manifesto (hoje 1). |
| identificador | texto | Nome estável do modelo (risco-infrequencia). |
| versao_modelo | texto | Versão desta publicação. |
| versao_contrato | texto | Versão do contrato de inferência; a versão 2 troca `intervalo_conformal` por `conjunto_conformal` (ADR-021). |
| versao_catalogo_features | texto | Versão do catálogo de features. |
| criado_em | data e hora ISO | Momento da montagem do pacote. |
| min_app_versao | versão | Versão mínima do FrequenciApp compatível. |
| runtime_alvo | texto | js-m2cgen, o único runtime publicado. |
| hash_modelo | sha256 | Hash do modelo.js para conferência após download. |
| tamanho_bytes | inteiro | Tamanho do modelo.js. |
| validade_ate | data | Data em que o app passa a exibir modelo desatualizado. |
| dataset | objeto | Identificador, linhas e taxa do rótulo do treino. |
| contrato | objeto | features (ordem fixa), padroes e tipos. |
| calibracao | objeto | a_platt, b_platt e taxa_base, ajustados no conjunto de validação sobre a saída do estudante. |
| conformal | objeto | nível, método, limiares por grupo e classe (`negativo` e `positivo`) e cobertura medida no teste. |
| limiares_alerta | objeto | entrada, saída e dias_consecutivos_entrada. |
| confianca | objeto | aquecimento_dias e validade_modelo_dias. |
| mensagens | objeto | Vocabulário aprovado por estado de confiança. |
| perfis_dados | lista | Perfis suportados com confiabilidade. |
| metricas | objeto | Métricas da avaliação de validação. |
| limitacoes | lista | Limitações declaradas no cartão. |
| cartao | texto | Nome do arquivo do cartão no pacote. |
| fallback | texto | Nome do arquivo de fallback no pacote. |
| licenca | texto | MIT. |
| arquivos | objeto | Hash sha256 de cada arquivo do pacote. |
| identificacao | objeto | Identificador e versão para o invólucro JS. |

## Validação

A montagem e a publicação aplicam a validação de campos obrigatórios, de runtime aceito, de coerência do contrato (mesma quantidade de features e padrões), de parâmetros de calibração, de quantis conformes, de limiares de alerta e de formato de datas. Um manifesto que não passa na validação não sai do empacotamento.

## Assinatura lógica

O manifesto carrega o hash sha256 de cada arquivo do pacote (modelo.js, fallback.js, dados-teste.json, modelo-cartao.md, LEIA-ME.md e contexto-mec.json quando presente). O próprio manifesto não carrega o hash de si mesmo: a auto-referência é impossível; a integridade dele vem do hash_modelo espelhado e do arquivo gravado no zip. A conferência de integridade é o comando `empacotamento validar` e a página Manifesto e pacote do painel.

## Compatibilidade

A decisão de ativação no app é a sequência: comparar versão instalada com min_app_versao; conferir validade_ate contra a data corrente; baixar e conferir hash_modelo; rodar dados-teste.json; ativar. Falha em qualquer passo mantém a versão anterior ou o fallback, e nada é carregado durante o fluxo de chamada.

## Evolução

Mudança de campo obrigatório, de semântica de limiar ou de contrato de features exige incremento de versao_manifesto ou versao_contrato, com ADR registrando o motivo e a política de app versões mínimas envolvida.
