# Guia do cientista e do engenheiro de ML

Manual humano para quem trabalha com dados, modelos e avaliação no FrequencIA. O foco é julgamento, método e decisão. Para comandos, use [INSTRUCOES.md](../INSTRUCOES.md) e a skill de agentes em [.agents/skills/frequencia/SKILL.md](../.agents/skills/frequencia/SKILL.md).

## Para quem é este guia

- Cientistas de dados que formulam hipóteses e avaliam modelos.
- Engenheiros de ML que operam o ciclo, empacotam e publicam.
- Revisores que precisam julgar evidência, fairness e reprodutibilidade.
- Pessoas que colaboram com agentes de IA e precisam saber o que delegar.

## Seu papel

- Formular perguntas melhores, não apenas rodar comandos.
- Desenhar experimentos que possam refutar a hipótese.
- Comparar com baseline antes de adicionar complexidade.
- Olhar calibração, subgrupos, fairness, custo e impacto humano.
- Documentar o que foi medido, o que foi assumido e o que ficou de fora.
- Comunicar decisões em português claro.
- Nunca tratar o modelo como decisão automática sobre estudantes.

## O que ler primeiro

1. [README](../README.md), para a visão geral.
2. [arquitetura](arquitetura.md), para as camadas.
3. [modelo-de-dados](modelo-de-dados.md), para as onze tabelas e as marcas.
4. [mlops](mlops.md), para o ciclo de treino, avaliação e publicação.
5. [ciencia-e-inovacao](ciencia-e-inovacao.md), para o método.
6. [README do projeto de risco](../projetos/risco-infrequencia/README.md), para o problema e as limitações.
7. [uso-responsavel](../projetos/risco-infrequencia/uso-responsavel.md), para o uso na escola.
8. [contrato-de-inferencia](contrato-de-inferencia.md) e [contrato-de-manifesto](contrato-de-manifesto.md), para o artefato publicado.

## Ambiente

Docker é o caminho padrão. O venv com Python 3.12 é fallback.

```bash
docker compose up --build -d
docker compose --profile ciclo up smoke
docker compose --profile cli run --rm -T --no-deps cli python -m pytest tests -q
```

```bash
# Fallback, apenas sem Docker
python3.12 --version
bash scripts/setup.sh
source .venv/bin/activate
bash scripts/smoke.sh
```

O volume `dados` do Docker é separado do `var/` local do venv. Registre qual caminho foi usado no pacote de evidências.

## O ciclo de trabalho

```text
observar -> enquadrar -> hipótese -> criticar -> protocolar -> executar -> validar -> revisar -> decidir -> aprender
```

- Observar: monitoramento, avaliação, histórico, limitações, issues e feedback agregado.
- Enquadrar: problema, público, decisão e evidência atual.
- Hipótese: predição falsificável e alternativas.
- Criticar: vazamento, confusão, seleção, amostra, fairness, custo e ética.
- Protocolar: métricas, limiares, splits, critério de parada e regra de decisão.
- Executar: workspace isolado, identificador próprio, semente registrada.
- Validar: gates, calibração, subgrupos, fairness, paridade, pacote e reprodutibilidade.
- Revisar: rubrica independente.
- Decidir: adotar, iterar, estacionar ou rejeitar.
- Aprender: registrar resultado, inclusive negativo, e atualizar o portfólio.

## Como formular uma hipótese

Uma hipótese útil tem:

- enunciado claro;
- predição falsificável;
- hipóteses alternativas;
- o que mudaria a opinião;
- impacto esperado;
- confiança;
- esforço;
- risco;
- dados necessários;
- o que aprenderíamos mesmo se falhar.

Evite hipóteses que não podem ser refutadas. Evite "vamos testar X" sem problema e sem critério de decisão.

## Como usar a CLI e o painel

- Para comandos, use os blocos de código bash da [skill](../.agents/skills/frequencia/SKILL.md) e do [catálogo de comandos](../.agents/skills/frequencia/references/comandos.md).
- Para uma visão humana, use o painel em http://localhost:8501.
- Prefira `--json` em automação.
- Use `--seco` antes de comandos que mudam estado, quando disponível.
- Leia o caminho do artefato e o veredito dos gates, não apenas a mensagem final.
- Não use `--forca` para contornar erro.

## Como ler resultados

| Métrica | O que responde | Cuidado |
| --- | --- | --- |
| AUC | ordenação | não mede calibração nem utilidade |
| AP | classe desbalanceada | sensível à prevalência |
| logloss | qualidade da probabilidade | penaliza confiança errada |
| Brier | erro da probabilidade | útil para calibração |
| ECE | calibração | depende de bins e amostra |
| cobertura conformal | conjuntos por classe, medidos no teste | grupos pequenos devolvem {0, 1} |
| precisão Top-10 | utilidade da lista | depende da capacidade da coordenação |
| taxa de alerta | custo operacional | alerta demais é inútil |
| dispersão de recall | fairness | exige amostra mínima |
| latência e tamanho | deployabilidade | meça no pacote real |

- Um bom número global pode esconder uma série com recall baixo.
- Um AUC maior com ECE pior pode ser uma regressão de produto.
- Um modelo que alerta 50% dos estudantes não ajuda a coordenação.
- Um resultado sem intervalo de confiança é uma promessa frágil.
- Um resultado que não se reproduz não é evidência.

## Como ler o cartão do modelo

O `modelo-cartao.md` acompanha cada pacote. Leia:

- versão, data e identificador do modelo;
- dados de treino, período e limitações;
- métricas globais, calibração e cobertura;
- uso pretendido e uso não pretendido;
- estados de confiança e mensagens aprovadas;
- compatibilidade mínima com o app e validade;
- plano de rollback e contato responsável.

O cartão não é marketing. Ele declara o que a versão faz, o que não faz e onde pode falhar.

## Como revisar um experimento

1. Leia o protocolo antes dos resultados.
2. Confira se a hipótese era falsificável.
3. Confira baseline, splits, purga e vazamento.
4. Confira métricas, limiares e subgrupos.
5. Confira fairness, custo e ética.
6. Tente reproduzir uma parte do resultado.
7. Procure overclaim e conclusão maior que a evidência.
8. Aplique a [rubrica de pesquisa](templates/rubrica-de-pesquisa.md).
9. Recomende aprovar, revisar ou rejeitar.

## Como decidir

| Situação | Ação |
| --- | --- |
| Gates aprovados e baseline superado | seguir para pacote e revisão de publicação |
| AUC baixa | investigar rótulo, volume, vazamento e features |
| ECE alto | revisar calibração e amostra por grupo |
| Cobertura conformal baixa | revisar grupos e quantis |
| Taxa de alerta alta | revisar limiar, política e capacidade |
| Baseline não superado | simplificar ou abandonar a mudança |
| Fairness com lacuna | investigar e mitigar antes de promover |
| Resultado não reproduzível | não publicar |
| Custo de manutenção alto | reconsiderar a adoção |

## Como documentar

- Use [brief-de-inovacao](templates/brief-de-inovacao.md) para a ideia.
- Use [protocolo-de-experimento](templates/protocolo-de-experimento.md) antes de executar.
- Use [nota-de-pesquisa](templates/nota-de-pesquisa.md) para o raciocínio.
- Use [relatorio-de-experimento](templates/relatorio-de-experimento.md) para os resultados.
- Use [revisao-cientifica](templates/revisao-cientifica.md) para o parecer.
- Use [rubrica-de-pesquisa](templates/rubrica-de-pesquisa.md) para a nota.
- Use [pacote-de-evidencias](templates/pacote-de-evidencias.md) para o conjunto.
- Registre a decisão em `decisao.md` no experimento.
- Mudança estrutural ganha ADR.

## Como trabalhar com agentes

| Delegar ao agente | Não delegar ao agente |
| --- | --- |
| Rodar comandos e ciclos | Aprovar promoção ou publicação |
| Coletar métricas e comparar experimentos | Julgar eticamente um uso novo |
| Preparar relatórios e resumos | Comunicar famílias e estudantes |
| Verificar artefatos, hashes e gates | Decidir o que fazer com um estudante |
| Organizar protocolos e evidências | Assinar a decisão final |

- Peça ao agente para mostrar o comando, o caminho do artefato e o JSON.
- Exija que ele registre o caminho de execução: Docker ou venv.
- Não aceite resumo sem número e fonte.
- Use o agente para explorar, não para aprovar.
- Se o agente errar, consulte a auditoria e corrija o processo.

## Como pedir uma pesquisa ao agente

- "Leia `docs/ciencia-e-inovacao.md` e proponha 3 hipóteses para melhorar o Top-10 diário, com evidência, risco e esforço."
- "Não execute nada ainda. Escreva o brief e o protocolo da hipótese escolhida."
- "Execute apenas o protocolo aprovado, em workspace isolado, e registre os comandos."
- "Prepare a nota de pesquisa e o pacote de evidências. Não promova nem publique."
- "Aplique a rubrica e aponte o que ainda falta para uma decisão."

O agente deve devolver comandos, caminhos de artefato, números e limitações. A pessoa revisa e decide.

## Ética e privacidade

- O modelo é apoio, não decisão.
- Não use o indicador como rótulo, punição ou diagnóstico.
- Não compartilhe listas fora da equipe autorizada.
- Dados reais exigem base legal, minimização e portão de privacidade.
- Não prometa causalidade sem desenho causal.
- Considere o impacto desproporcional em grupos vulneráveis.
- Em dúvida, pare e peça revisão humana.

## Primeiros 30 dias

| Semana | Foco |
| --- | --- |
| 1 | Ler README, arquitetura, modelo de dados, MLOps e ciência; rodar o smoke |
| 2 | Rodar um experimento sintético e inspecionar estado, avaliação e gates |
| 3 | Revisar um experimento anterior com a rubrica |
| 4 | Escrever um protocolo pequeno e apresentar um memorando de decisão |

## Perguntas frequentes

- Posso mudar um gate? Não. Mudança de gate exige ADR e revisão humana.
- Posso testar uma feature nova? Sim, com protocolo, catálogo, dicionário, testes de contrato e ADR se estrutural.
- Posso usar dados reais? Apenas com base legal, autorização, minimização e portão verde.
- Posso publicar sem aprovação? Não.
- Posso confiar no agente? Verifique comandos, artefatos, gates e auditoria. A decisão é humana.
- O que faço com resultado negativo? Documente e compartilhe. Ele evita retrabalho.
- O modelo pode ser usado para punir? Não. O uso é apoio à decisão e sujeito a revisão humana.
- O que faço se a coordenação discordar? A realidade da escola tem prioridade; registre o descarte e investigue.

## Checklists

Antes do experimento:

- [ ] Problema e decisão estão claros.
- [ ] Hipótese é falsificável.
- [ ] Baseline está definido.
- [ ] Dados e privacidade estão resolvidos.
- [ ] Métricas e limiares foram definidos antes.
- [ ] Subgrupos e fairness estão planejados.
- [ ] Critério de parada está claro.
- [ ] Protocolo foi revisado.

Antes da promoção:

- [ ] Gates aprovados.
- [ ] Calibração e conformal revisados.
- [ ] Fairness revisada.
- [ ] Pacote íntegro e paridade zero.
- [ ] Aprovação registrada.
- [ ] Rollback pronto.

## Glossário

- aluno-dia: unidade de previsão.
- F, FJ, S, P: falta, falta justificada, saída parcial e presença.
- ponto-in-tempo: snapshot do diário como visível em um instante.
- purga: intervalo entre splits do tamanho do horizonte.
- OOF: previsão fora da dobra.
- ECE: erro esperado de calibração.
- conformal: conjunto de classes plausíveis com cobertura mínima por classe.
- PSI: índice de estabilidade populacional.
- histerese: alerta liga após dois dias acima do limiar de entrada e desliga abaixo do limiar de saída.
