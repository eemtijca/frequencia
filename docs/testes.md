# Testes

Convenção e cobertura das suítes do FrequencIA. Toda execução cria e limpa a própria massa; nenhum teste depende de ordem ou de dados reais.

## Famílias

| Família | Pasta | O que garante |
| --- | --- | --- |
| Guarda editorial | tests/test_editorial.py | Tom de texto: sem travessão, aspas curvas, reticências tipográficas e setas fora de cercas de código; cabeçalho em português em cada arquivo |
| Dados | tests/dados/ | Esquema das onze tabelas, determinismo da semente, sazonalidade por dia da semana, perfis de escola, eventos retroativos, isolamento da verdade oculta, calendário com feriados e recesso |
| Privacidade | tests/privacidade/ | Detector com regex própria e presidio, portão que bloqueia PII, identificadores proibidos, pseudonimização estável, relatório de risco graduado, logs sem dado pessoal |
| Features | tests/features/ | Catálogo válido, derivação das marcas conforme o documento soberano, célula vazia como ausência, marca S só com chamada por aula, ordem do contrato sem nulos, ordinal agrupando raras, estados de confiança, histerese, aquecimento, calendário cíclico, ponto-in-tempo |
| Pipelines | tests/pipelines/ | Separação temporal estrita com purga, rótulo só com janela futura, verificação de futuro por reconstrução, treino com métricas, ensemble com pesos e OOF, calibração protegendo a identidade, conformal com cobertura, curva de aprendizado |
| Exportação | tests/exportacao/ | Ciclo completo com gates, paridade Python e Node com divergência zero, tamanho e latência nos limites, manifesto válido, integridade do pacote, dados-teste automáticos, fallback com a mesma interface, ONNX válido, nenhum nome de pessoa nos artefatos, histerese no pacote |
| CLI | tests/cli/ | Ajuda de todos os grupos, erro amigável sem stack trace, JSON estruturado, modo seco sem gravar, força exigindo justificativa, fluxo completo por subprocesso |
| Web | tests/web/ | Importação das dezesseis páginas, renderização da visão geral com AppTest, tarefa de fundo executando a CLI e registrando desfecho |
| Propriedades | tests/properties/ | Invariantes com Hypothesis: estado de confiança no vocabulário, pesos e misturas no intervalo unitário, histerese monotona, baseline determinístico e limitado, regras crescem com falta recente |

## Execução

```bash
python -m pytest tests -q          # suíte completa
bash scripts/smoke.sh              # ciclo completo mais suíte
python -m pytest tests/exportacao -q -m smoke
```

A suíte completa roda em cerca de 45 segundos numa máquina comum. Os testes que exigem Node pulam com aviso quando ele está ausente.

## Convenções

- Fixtures leves têm escopo de função; pacote, dataset e ciclo completo têm escopo de módulo para rodar uma vez por arquivo.
- O workspace de teste é pasta temporária isolada por FREQUENCIA_WORKSPACE, sem shared state.
- Ao corrigir defeito, o teste que o pegaria entra na mesma mudança.
- Testes de propriedade documentam invariantes de domínio, não implementação.

## Cobertura das exigências de pronto

| Exigência do briefing | Prova |
| --- | --- |
| Ingestão sintética com validação de esquema | tests/dados |
| Dataset temporal sem vazamento | tests/pipelines, comando validar-ausencia-futuro |
| Features com ordem e tipos | tests/features |
| Treino rápido e avaliação mínima | fixture experimento_completo com gates |
| Exportação com tamanho e hash | tests/exportacao |
| Empacotamento com manifesto válido | tests/exportacao |
| Inferência com paridade | tests/exportacao no Node |
| Calibração | tests/pipelines |
| Fluxo completo da CLI | tests/cli |
| Fluxo da aplicação web | tests/web |
| Privacidade sem dados pessoais | tests/privacidade e varredura de artefatos |
| Perfis de dados | gerador com perfis por escola e filtro de dataset |
| Fallback | tests/exportacao com fallback.js |
