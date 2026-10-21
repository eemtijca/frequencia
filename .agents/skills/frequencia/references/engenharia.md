# Engenharia e ciência de dados no FrequencIA

Critérios para interpretar resultados, diagnosticar gates e decidir com evidência. Use junto de `docs/mlops.md`, `docs/publicacao-de-modelos.md` e `docs/ciencia-e-inovacao.md`.

## Formulação do problema

- A unidade é aluno-dia. O horizonte é de sete dias letivos.
- O rótulo é ter duas ou mais faltas, F ou FJ, no horizonte, contando enquanto o estudante está matriculado.
- A saída é uma probabilidade calibrada, com conjunto conforme, faixa de risco, estado de confiança e alerta com histerese.
- O produto é apoio à decisão da coordenação, nunca decisão automática, diagnóstico ou rótulo de estudante.
- A capacidade operacional da coordenação é o limite real. Priorize Top-K diário e taxa de alerta, não apenas AUC.
- O baseline de regras é o mínimo a superar. Complexidade sem ganho mensurável não se justifica.

## Dados e vazamento

- Use ponto-in-tempo estrito no treino. `ponto_no_tempo atual` serve apenas para avaliação retrospectiva.
- A purga entre treino, validação e teste deve ter o tamanho do horizonte.
- Célula vazia é ausência de frequência, nunca presença.
- Texto livre não entra como feature. O detector de privacidade varre, mas o contrato não consome.
- Verifique a cobertura de chamada e o histórico mínimo. Escolas com chamadas atrasadas ou ausentes podem ter features subestimadas.
- Desconfie de features calculadas depois do momento da previsão. Rode `features verificar-vazamento` e o teste de reconstrução.
- Desconfie de ganho concentrado em uma escola, série ou faixa de histórico. Verifique subgrupos antes de comemorar.

## Baseline e modelo

- O modelo principal é LightGBM com parâmetros declarativos.
- O ensemble tem sete membros, validação fora da dobra e blend logístico. O ensemble é professor, não produto.
- O estudante destilado é o artefato publicado. Ele precisa ser leve, calibrado e fiel ao professor.
- A destilação usa duplicação ponderada para contornar a restrição de rótulos fracionários do LightGBM 4.7.
- O m2cgen é o caminho de exportação principal. O ONNX é alternativa documentada.
- Aumente `--tentativas` do Optuna apenas depois de estabilizar o pipeline. Use validação temporal, nunca o teste, para escolher hiperparâmetros.
- Aumente `--dobras` quando houver dados suficientes. Mais dobras reduzem o viés do OOF, mas aumentam o custo.
- Ablação é obrigatória para uma feature nova: rode com e sem a feature, mesma semente e mesmos splits. Sem ganho consistente, não adote.

## Métricas e calibração

| Métrica | O que responde | Cuidado |
| --- | --- | --- |
| AUC | ordenação | não mede calibração nem utilidade operacional |
| AP | desempenho com classe desbalanceada | sensível à prevalência |
| logloss | qualidade da probabilidade | penaliza confiança errada |
| Brier | erro quadrático da probabilidade | útil para comparar calibração |
| ECE | erro esperado de calibração | depende do número de bins e da amostra |
| cobertura conformal | confiança dos conjuntos por classe | grupos pequenos devolvem {0, 1} |
| precisão Top-10 | utilidade da lista diária | depende da capacidade da coordenação |
| taxa de alerta | custo operacional | um modelo que alerta demais é inútil |
| dispersão de recall | fairness entre séries | exige amostra mínima por grupo |
| latência e tamanho | deployabilidade | meça no Node e no pacote real |

- Calibração não é enfeite. Uma probabilidade de 0,70 precisa se comportar como 0,70 na prática.
- O aquecimento de 30 dias encolhe a predição para a taxa base. Não trate os primeiros dias como confiança alta.
- O conjunto conforme é por série, faixa de histórico e classe. Grupos pequenos devolvem {0, 1}; isso é honestidade, não defeito.
- A histerese liga o alerta após dois dias acima do limiar de entrada e desliga abaixo do limiar de saída. Não releia o dia anterior de forma que anule a histerese.

## Subgrupos e fairness

- Analise por série, faixa de histórico, turma e perfil de escola.
- O código de fairness exige pelo menos 20 amostras por grupo. Abaixo disso, o resultado é inconclusivo.
- Uma AUC global alta pode esconder recall baixo em uma série. Verifique a dispersão.
- Não promova uma versão com lacuna sistemática de recall sem documentar a causa e a mitigação.
- Fairness básico não é auditoria completa. Evite overclaim: diga o que foi medido e o que não foi.
- Considere o contexto escolar: saúde, transporte, segurança, trabalho e clima escolar afetam frequência e não estão no modelo.

## Custo operacional

- A coordenação tem minutos por dia. O Top-K diário é mais realista que um limiar fixo.
- Taxa de alerta acima de 0,35 satura a operação.
- Falsos positivos consomem tempo e podem estigmatizar. Falsos negativos perdem oportunidade de apoio.
- O custo de um erro não é simétrico. O protocolo deve declarar o que pesa mais na decisão.
- Um modelo com AUC maior e custo operacional pior pode ser uma regressão de produto.

## Diagnóstico de gates

| Gate | Limite | Se falhar, investigue | Não faça |
| --- | --- | --- | --- |
| AUC | mínimo 0,70 | rótulo, prevalência, vazamento, volume, qualidade das features, baseline | ajustar no teste ou afrouxar o gate |
| ECE | máximo 0,10 | amostra de calibração, grupos pequenos, Platt, mudança de distribuição | recalibrar no teste e declarar sucesso |
| cobertura conformal | mínimo 0,80 | tamanho dos grupos, limiares por classe, séries e faixas | agrupar sem documentar |
| taxa de alerta | máximo 0,35 | limiar, prevalência, política de alerta, Top-K | subir o limiar apenas para passar |
| melhora sobre baseline | mínimo 0 | força do baseline, segmentos, valor real da feature | adicionar complexidade sem ganho |
| tamanho do pacote | máximo 256 KiB | profundidade do estudante, iterações, número de features, invólucro | remover calibração ou conformal |
| latência | máximo 5 ms | ambiente Node, invólucro, número de features | medir em máquina diferente da alvo |

O ciclo grava `gates.json` mesmo quando o veredito é reprovado. Verifique `aprovado` antes de qualquer promoção.

## Rigor estatístico

- Defina métrica primária, métricas de guarda e critério de parada antes do experimento.
- Não troque a métrica depois de ver o resultado. Se fizer análise exploratória, rotule como exploratória.
- Use intervalos de confiança e reporte a incerteza. Um número pontual sem intervalo é uma promessa frágil.
- Cuidado com comparações múltiplas. Muitos subgrupos aumentam a chance de falso positivo.
- Amostra pequena produz conclusão instável. Se o grupo é pequeno, diga que é inconclusivo.
- Prefira validação temporal a divisão aleatória. O futuro não é intercambiável com o passado.
- Controle negativo: embaralhe o rótulo e veja se o modelo continua "bom". Se continuar, há vazamento.
- Ablação: remova a mudança e veja se o ganho desaparece. Se desaparecer, a mudança não era a causa.
- Sensibilidade: varie semente, data de corte e limiar. Se a conclusão muda, ela é frágil.

## Reprodutibilidade

Registre no pacote de evidências:

- caminho de execução: Docker ou venv;
- versão do Docker, Python, Node e dependências;
- commit e diff;
- semente;
- dataset, versão e hash;
- comando exato;
- run do MLflow;
- artefatos e caminhos;
- métricas e gates;
- limitações e decisão.

Se outra pessoa não consegue reproduzir, não é evidência suficiente para promoção.

## Ética e uso responsável

- O modelo não decide sobre estudantes. A coordenação decide, com contexto que o modelo não tem.
- Não use o indicador como rótulo, punição, diagnóstico ou critério único de comunicação à família.
- Não compartilhe listas fora da equipe autorizada.
- Não use dados reais sem base legal, minimização e portão de privacidade.
- Não prometa causalidade. O modelo prediz risco; não explica por que o estudante falta.
- Considere o impacto desproporcional em grupos vulneráveis.
- Em caso de dúvida ética, pare e peça revisão humana.

## Red flags

- AUC alta com ECE alto ou cobertura conformal baixa.
- Ganho sobre baseline zero ou negativo.
- Taxa de alerta acima da capacidade da coordenação.
- Dispersão grande de recall entre séries.
- Drift alto sem plano de retreinamento.
- Validade vencida.
- Paridade Python e JavaScript diferente de zero.
- Tamanho ou latência acima do limite.
- Dados com PII ou base legal ausente.
- Publicação sem aprovação ou sem rollback.
- Experimento sem protocolo, sem semente ou sem artefato.
- Conclusão que não resiste a uma segunda execução.
