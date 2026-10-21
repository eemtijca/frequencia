# Testes

Convenção e cobertura das suítes do FrequencIA. Toda execução cria e limpa a própria massa; nenhum teste depende de ordem ou de dados reais.

## Famílias

| Família | Pasta | O que garante |
| --- | --- | --- |
| Guarda editorial | tests/test_editorial.py | Tom de texto: sem travessão, aspas curvas, reticências tipográficas e setas fora de cercas de código; cabeçalho nos módulos de `src/` |
| Dados | tests/dados/ | Esquema das onze tabelas, determinismo da semente, sazonalidade por dia da semana, perfis de escola, eventos retroativos, isolamento da verdade oculta, calendário com feriados e recesso |
| Privacidade | tests/privacidade/ | Detector com regex própria e presidio, portão que bloqueia PII, identificadores proibidos, pseudonimização estável, relatório de risco graduado, logs sem dado pessoal |
| Features | tests/features/ | Catálogo válido, derivação das marcas conforme o documento soberano, célula vazia como ausência, marca S só com chamada por aula, ordem do contrato sem nulos, ordinal agrupando raras, estados de confiança, histerese, aquecimento, calendário cíclico, ponto-in-tempo |
| Pipelines | tests/pipelines/ | Separação temporal estrita com purga, alunos reservados para partida a frio fora do treino, rótulo com desistência na janela, verificação de futuro por reconstrução, treino com métricas, ensemble com pesos, OOF e purga nas dobras, calibração protegendo a identidade e corrigindo com muita evidência, preditor publicado igual ao espelho do modelo.js, conjuntos conformes cobrindo cada classe, gates reprovando medida ausente, idempotência sensível à configuração, curva de aprendizado |
| Exportação | tests/exportacao/ | Ciclo completo com veredito de todos os gates, paridade Python e Node com divergência zero, tamanho e latência nos limites, manifesto válido, integridade do pacote, dados-teste automáticos, fallback com a mesma interface, ONNX válido, nenhum nome de pessoa nos artefatos, histerese encadeada igual em JS e Python; com `FREQUENCIA_TESTES_LENTOS=1`, aprovação de todos os gates no perfil padrão |
| Compose | workflow `testes.yml` | Build das imagens de runtime e desenvolvimento, saúde do MLflow e do painel, ciclo completo no container |
| Registro e publicação | tests/modelos/ | Publicação recusada sem gravar nada, hash do pacote contra o registro, rollback seguro, trava contra escrita concorrente, gates e aprovação exigidos na promoção |
| CLI | tests/cli/ | Comandos citados na documentação conferidos contra a CLI, ajuda de todos os grupos, erro amigável sem stack trace, JSON estruturado, modo seco sem gravar, força exigindo justificativa, fluxo completo por subprocesso |
| Web | tests/web/ | Importação das dezesseis páginas, renderização da visão geral com AppTest, tarefa de fundo executando a CLI e registrando desfecho |
| Propriedades | tests/properties/ | Invariantes com Hypothesis: estado de confiança no vocabulário, pesos e misturas no intervalo unitário, histerese monotona, baseline determinístico e limitado, regras crescem com falta recente |

## Execução

```bash
# Docker, caminho padrão
docker compose --profile cli run --rm -T --no-deps cli python -m pytest tests -q
docker compose --profile ciclo up smoke
docker compose --profile cli run --rm -T --no-deps cli python -m pytest tests/exportacao -q -m smoke
docker compose --profile cli run --rm -T --no-deps cli python scripts/gerar_dicionario.py --check

# Fallback venv, com Python 3.12
source .venv/bin/activate
python -m pytest tests -q
bash scripts/smoke.sh
python scripts/gerar_dicionario.py --check
```

O perfil de fumaça do smoke valida a mecânica do ciclo: com cem alunos, a diferença entre o modelo e o baseline de regras fica dentro do erro-padrão da AUC, e o veredito dos gates oscila com o ruído. Por isso o smoke exige os gates calculados, não aprovados. A exigência de qualidade roda no perfil padrão, que leva vários minutos:

```bash
make qualidade
make venv-qualidade
FREQUENCIA_TESTES_LENTOS=1 python -m pytest tests/exportacao/test_qualidade.py -q
```

A suíte completa leva alguns minutos: a medição de referência, num contêiner de desenvolvimento em outubro de 2026, foi de cerca de 12 minutos. Em Docker Desktop com o repositório em OneDrive, o bind mount pode deixar a execução mais lenta. Os testes que exigem Node pulam com aviso quando ele está ausente; a imagem de desenvolvimento já inclui Node.

O dicionário de features é gerado por `scripts/gerar_dicionario.py` e conferido no workflow de qualidade. O ciclo em Docker é validado pelo job `Compose e imagem` do workflow `testes.yml`.

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
