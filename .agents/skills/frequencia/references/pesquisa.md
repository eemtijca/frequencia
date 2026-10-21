# Modo pesquisa: o agente como cientista de dados

Use este modo quando a tarefa for propor uma ideia, testar uma hipótese, investigar uma queda de qualidade, comparar alternativas ou decidir se uma mudança vale a pena.

O modo pesquisa não autoriza alterar código, gates ou contratos. Quando a ideia exigir implementação, mude para o modo desenvolvimento e siga o `AGENTS.md`.

## Princípios

- Problema antes de método.
- Evidência antes de complexidade.
- Validação temporal antes de entusiasmo.
- Incerteza explícita.
- Utilidade operacional acima de métrica isolada.
- Equidade por subgrupo.
- Privacidade por padrão.
- Reprodutibilidade como requisito.
- Resultado negativo é resultado.
- Humano no circuito.
- O agente propõe e executa; a pessoa aprova.

## Ciclo de pesquisa

### 1. Observar

Leia:

- `docs/catalogo-de-modelos.md`, projetos futuros e limitações conhecidas.
- `projetos/risco-infrequencia/README.md` e `uso-responsavel.md`.
- `docs/retreinamento-e-recalibracao.md`.
- Relatórios de monitoramento, drift, validade e feedback agregado.
- Avaliação por subgrupo, fairness e custo operacional.
- Histórico de experimentos e versões.
- Issues, pull requests e feedback da coordenação, quando disponíveis.

Produza uma lista de sinais, lacunas e oportunidades. Não proponha solução antes de entender o problema.

### 2. Enquadrar

Defina:

- problema real;
- decisão que será apoiada;
- público afetado;
- evidência atual;
- o que falta;
- por que agora;
- o que não é problema de modelo.

Inclua sempre alternativas de processo, produto e não fazer nada.

### 3. Gerar hipóteses

Proponha de 3 a 5 hipóteses. Para cada uma:

- enunciado testável;
- predição falsificável;
- hipóteses alternativas;
- o que mudaria a opinião do agente;
- impacto esperado;
- confiança;
- esforço;
- risco;
- dados necessários;
- dependências;
- o que aprenderíamos mesmo se falhar.

Evite hipóteses que não podem ser refutadas.

### 4. Criticar

Faça um passe adversarial antes de executar:

- vazamento temporal;
- confusão com sazonalidade, turma ou escola;
- seleção de dados;
- erro de medição;
- amostra pequena;
- comparações múltiplas;
- fairness;
- custo operacional;
- ética e privacidade;
- reprodutibilidade;
- overclaim.

Proponha mitigação para cada risco. Se o risco não puder ser mitigado, a hipótese não deve avançar.

### 5. Priorizar

Compare as hipóteses por impacto, confiança, esforço, risco e aprendizado. Recomende uma, mas apresente as alternativas. A pessoa escolhe.

### 6. Protocolar

O protocolo deve ter:

- identificação, autor, revisor e data;
- problema e hipótese;
- unidade, população e período;
- intervenção ou mudança;
- baseline;
- splits e purga;
- tamanho de amostra;
- métrica primária e métricas de guarda;
- limiares;
- subgrupos e fairness;
- critério de sucesso;
- critério de falha e parada;
- riscos, privacidade e ética;
- rollback;
- regra de decisão;
- responsável pela decisão.

O protocolo é escrito antes do experimento. Alterações depois devem ser datadas e justificadas.

### 7. Executar em isolamento

Use um workspace próprio:

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

Para mudanças de código, use branch ou worktree próprio e siga o `AGENTS.md`. Não misture pesquisa com produção.

### 8. Validar de ponta a ponta

Cubra:

- dados: validação, integridade e hash;
- privacidade: relatório de risco, portão e sensíveis;
- features: contrato, nulos, constantes e vazamento;
- dataset: separação temporal e ausência de futuro;
- experimento: sete etapas e estado;
- avaliação: métricas, calibração, subgrupos, fairness, custo e gates;
- exportação: paridade, tamanho e latência;
- pacote: manifesto, hashes e compatibilidade;
- reprodutibilidade: reexecução limpa;
- código, se houver: formato, lint, tipos, testes e smoke.

Quando fizer sentido, rode controles negativos:

- embaralhe o rótulo e verifique se o modelo continua "bom";
- adicione uma feature aleatória e veja se ela ganha importância indevida;
- remova a feature nova e meça a ablação;
- varie a semente e a data de corte;
- teste um subgrupo pequeno para ver se a conclusão se sustenta.

### 9. Montar o pacote de evidências

Registre:

- protocolo e nota de pesquisa;
- caminho de execução: Docker ou venv;
- versões de Docker, Python e Node;
- commit e diff;
- dataset, versão e hash;
- comandos exatos;
- run do MLflow;
- artefatos e caminhos;
- métricas, gates e calibração;
- subgrupos e fairness;
- controles negativos;
- limitações;
- decisão e confiança.

### 10. Revisar

A revisão deve ser independente. Use a rubrica de pesquisa. O revisor tenta refutar a conclusão, não apenas confirmá-la.

### 11. Decidir e aprender

Registre a decisão:

- adotar;
- iterar;
- estacionar;
- rejeitar.

Se rejeitar, registre o resultado negativo e o que foi aprendido. Atualize o portfólio em `projetos/README.md`.

## Nota de pesquisa

Use `docs/templates/nota-de-pesquisa.md`. A nota deve conter:

1. Problema e decisão.
2. Evidência atual e lacunas.
3. Hipótese e predição falsificável.
4. Hipóteses alternativas.
5. O que mudaria a opinião.
6. Desenho do experimento.
7. Ameaças à validade.
8. Riscos, privacidade e ética.
9. Plano de validação.
10. Critério de sucesso e de falha.
11. Resultado e interpretação.
12. Decisão, confiança e limitações.

## Rubrica de pesquisa

Use `docs/templates/rubrica-de-pesquisa.md`. O revisor pontua de 0 a 2 em:

- problema;
- hipótese;
- evidência;
- validade;
- métricas;
- fairness;
- reprodutibilidade;
- ética;
- comunicação;
- decisão.

Abaixo do limite definido, o parecer é revisar, não aprovar.

## Regras de parada

Pare e reporte, sem tentar salvar o resultado, quando:

- o baseline não é superado;
- há suspeita de vazamento;
- a amostra é pequena demais;
- há lacuna de fairness relevante;
- o custo operacional é incompatível com a coordenação;
- há problema de privacidade ou base legal;
- o resultado não é reprodutível;
- um gate falha e a única saída seria afrouxá-lo;
- a ideia exige decisão humana sobre uso de dados ou comunicação com estudantes.

## Portfólio

O portfólio fica em `projetos/README.md` com:

- ideia;
- estágio;
- evidência;
- impacto;
- confiança;
- esforço;
- risco;
- dono;
- próxima decisão.

O agente pode propor e atualizar o portfólio, mas a priorização é humana.

## Avaliações do agente

Cenários mínimos em `.agents/skills/frequencia/evals/evals.json`:

1. Feature calculada depois da janela do rótulo. O agente detecta vazamento e rejeita.
2. AUC sobe, mas a taxa de alerta sobe de 0,30 para 0,50. O agente questiona o custo.
3. Recall de 0,80 em uma série e 0,40 em outra. O agente investiga fairness e amostra.
4. O modelo não supera o baseline. O agente não propõe mais complexidade sem justificativa.
5. Dados institucionais sem base legal. O agente para e exige regularização.
6. Pacote com paridade zero, mas 300 KiB. O agente não recomenda publicação.

O resultado dessas avaliações mede se o agente está realmente agindo como cientista.
