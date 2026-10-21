# Ciência e inovação

Diretrizes para transformar dúvidas em hipóteses, hipóteses em experimentos, experimentos em evidência e evidência em decisões. Este documento não substitui [mlops.md](mlops.md), que descreve a execução, nem [publicacao-de-modelos.md](publicacao-de-modelos.md), que descreve os gates. Ele organiza o método e a governança da inovação.

## Propósito e escopo

Aplicam-se a:

- nova feature, nova família de features ou novo rótulo;
- novo modelo, novo ensemble ou nova técnica de calibração;
- nova fonte de dados ou novo uso de dados existentes;
- nova métrica, novo gate ou novo critério de avaliação;
- novo produto, nova visualização ou novo processo de apoio à coordenação;
- investigação de queda de qualidade, drift ou feedback negativo.

Não se aplicam a:

- correção de bug sem mudança de comportamento;
- recalibração de rotina;
- retreinamento com o mesmo contrato e os mesmos gates;
- ajuste de hiperparâmetro dentro do espaço já aprovado;
- atualização de dependência ou documentação.

Esses casos seguem o fluxo normal de manutenção e os gates existentes.

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
- Inovação com rollback.
- Humano no circuito.
- Decisão documentada, não apenas resultado registrado.

## Funil de inovação

| Estágio | Pergunta | Evidência mínima | Decisão |
| --- | --- | --- | --- |
| 0. Ideia | Qual problema real e para quem? | Brief de inovação, alternativas, dor documentada | Autorizar protocolo |
| 1. Protocolo | A hipótese é testável, ética e viável? | Protocolo, dados, base legal, métricas, critérios de parada | Autorizar experimento |
| 2. Offline | Supera o baseline em validação temporal? | Experimento reproduzível, gates, calibração, subgrupos, fairness | Autorizar sombra |
| 3. Sombra | Funciona no fluxo real sem ser exibido? | Paridade, latência, custo, aderência, ausência de vazamento | Autorizar piloto |
| 4. Piloto | Ajuda a coordenação sem causar dano? | Uso real, feedback, fairness, incidentes, entrevistas | Autorizar adoção |
| 5. Adoção | Vale manter e escalar? | Cartão do modelo, monitoramento, rollback, custo, plano de suporte | Publicar e monitorar |
| 6. Aprendizado | O que funcionou e o que não funcionou? | Relatório final, resultado negativo, decisão registrada | Encerrar ou iterar |

Cada estágio tem um dono, uma decisão e um artefato. Não se avança por entusiasmo; avança-se por evidência.

## Hierarquia de evidência

Da mais fraca para a mais forte:

1. Opinião e relato isolado.
2. Análise retrospectiva.
3. Validação temporal offline com holdout.
4. Sombra prospectiva.
5. Piloto controlado.
6. Produção monitorada.

Quanto mais perto da decisão real, mais forte a evidência. Um AUC alto em teste retrospectivo não substitui um piloto com a coordenação.

## Duas trilhas

| Trilha | Quando usar | O que exigir |
| --- | --- | --- |
| Leve | Ajuste dentro do contrato aprovado: janela de feature, hiperparâmetro, recalibração, correção | Brief de uma página, experimento, resultados e decisão |
| Estrutural | Novo rótulo, família de features, modelo, runtime, fonte sensível ou produto | Protocolo completo, revisão independente, ADR, contrato, testes e piloto |

A maior parte das ideias deve caber na trilha leve. A trilha estrutural existe para o que muda o contrato ou o risco.

## Protocolo de experimento

O protocolo é escrito antes do experimento e registrado em `projetos/risco-infrequencia/experimentos/<ano-mes>-<slug>/protocolo.md`. Use [templates/protocolo-de-experimento.md](templates/protocolo-de-experimento.md).

Ele deve conter:

- problema, público e decisão apoiada;
- hipótese e predição falsificável;
- hipóteses alternativas;
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

Alterações depois do início devem ser datadas e justificadas. Trocar a métrica depois de ver o resultado é proibido; se ocorrer análise exploratória, ela deve ser rotulada como exploratória.

## Revisão científica

A revisão é feita por alguém que não seja o autor. Use [templates/revisao-cientifica.md](templates/revisao-cientifica.md).

O revisor responde:

- o problema é real e relevante?
- a hipótese é falsificável?
- o baseline é adequado?
- os dados e o ponto-in-tempo estão corretos?
- a purga está correta?
- há risco de vazamento?
- a amostra é suficiente?
- as métricas estão alinhadas à decisão?
- a análise de subgrupos e fairness foi planejada?
- o custo operacional foi estimado?
- o resultado é reprodutível?
- a privacidade e a ética foram revisadas?
- o rollback está claro?
- a conclusão está calibrada com a evidência?

O parecer é aprovar, revisar ou rejeitar. A decisão final é humana.

## Agentes como cientistas

- O agente pode propor hipóteses, escrever brief e protocolo, executar o experimento em isolamento, coletar evidências e recomendar uma decisão.
- O agente não aprova, não promove, não publica e não altera gates.
- O propositor não deve ser o único revisor. Use passes separados ou subagentes para o crítico e o revisor.
- O agente registra suas ações com `--ator agente:<nome>`.
- A pessoa responsável usa sua própria identidade na aprovação.
- A skill em [.agents/skills/frequencia/SKILL.md](../.agents/skills/frequencia/SKILL.md) implementa o modo pesquisa, com regras de isolamento, rubrica e pacote de evidências.

## Registro de inovação

O registro humano fica em:

```text
projetos/
├── README.md
├── risco-infrequencia/
│   ├── README.md
│   ├── uso-responsavel.md
│   ├── historico-de-versoes.md
│   └── experimentos/
│       └── 2026-11-saidas-recentes/
│           ├── protocolo.md
│           ├── resultados.md
│           ├── decisao.md
│           └── evidencias.md
```

Regras:

- O nome segue `AAAA-MM-slug`, em minúsculas, com hífens e sem acento.
- O mesmo identificador é usado em `experimentos executar --identificador`.
- O protocolo é escrito antes do experimento.
- Os resultados e a decisão são escritos depois.
- O `projetos/README.md` funciona como índice do portfólio.
- Os artefatos de máquina continuam em `var/artefatos/experimentos/<id>/`.
- O ADR registra mudanças estruturais; o protocolo e a decisão registram o experimento.

## Artefatos de decisão

| Artefato | Pergunta que responde | Quando criar |
| --- | --- | --- |
| Brief | Vale investigar? | Ideia |
| Protocolo | Como testar? | Antes do experimento |
| Nota de pesquisa | Qual é o raciocínio e a evidência? | Antes e depois do experimento |
| Resultados | O que aconteceu? | Depois do experimento |
| Decisão | O que faremos? | Depois da revisão |
| ADR | Por que mudar a estrutura? | Mudança estrutural |
| Cartão do modelo | O que esta versão faz e não faz? | Cada versão |
| Notas de mudança | O que muda para a escola? | Cada publicação |
| Auditoria | Quem fez o quê? | Sempre |

## Métricas do programa

Não medir apenas AUC. Medir também:

- percentual de experimentos com protocolo registrado antes da execução;
- percentual de experimentos reproduzíveis a partir dos artefatos;
- resultados negativos documentados;
- revisões concluídas antes de promoção;
- adoção real pela coordenação;
- incidentes de privacidade;
- drift e calibração em produção;
- dispersão de fairness entre subgrupos;
- tempo de ideia até decisão;
- correções humanas em relatórios de agentes.

## Ética de experimentação

- Não retirar apoio essencial de um grupo para testar.
- Não randomizar quando isso puder prejudicar estudantes.
- Preferir sombra, stepped-wedge ou comparação histórica quando a randomização não for ética.
- A escola pode interromper o piloto a qualquer momento.
- Privacidade, base legal e revisão ética entram antes do experimento.
- O benefício deve ser para a escola e para os estudantes, não apenas para a métrica.
- Não usar o indicador como rótulo, punição, diagnóstico ou critério único de comunicação à família.

## Agenda de pesquisa

- O indicador melhora a chance de apoio tempestivo?
- Quais features são realmente acionáveis pela coordenação?
- Como a calibração varia entre escolas e séries?
- Como a coordenação interpreta incerteza e estados de confiança?
- Qual é o impacto na equidade entre turmas e séries?
- Modelos de turma ajudam sem estigmatizar?
- Como usar feedback sem criar ciclos viciosos?
- Quais mudanças de interface reduzem a fadiga de alerta?
- Qual é o efeito de diferentes protocolos de apoio?
- Como medir impacto sem confundir predição com causalidade?

Essas perguntas alimentam o portfólio e os projetos futuros de [catalogo-de-modelos.md](catalogo-de-modelos.md).

## Anti-padrões

- "Vamos testar X" sem hipótese.
- Ajustar no conjunto de teste.
- Adicionar complexidade sem ganho sobre o baseline.
- Ignorar subgrupos porque a média está boa.
- Afrouxar um gate para a versão passar.
- Usar dados reais sem base legal.
- Publicar sem rollback.
- Tratar a saída do agente como decisão.
- Medir só o modelo e não o efeito humano.
- Criar um comitê eterno para qualquer ajuste pequeno.
- Repetir uma hipótese rejeitada sem nova evidência.
- Esconder resultado negativo.

## Integração com o ciclo

```bash
# Ciclo técnico
docker compose --profile cli run --rm cli frequencia experimentos executar \
  var/dados/processados/<versao> \
  --identificador <id> \
  --versao-modelo <versao-modelo>

# Gates
docker compose --profile cli run --rm cli frequencia avaliacao validar-gates \
  var/artefatos/experimentos/<id>

# Publicação
docker compose --profile cli run --rm cli frequencia publicacao publicar \
  var/pacotes/risco-infrequencia-<versao-modelo> \
  <versao-modelo> \
  --notas "<notas>" \
  --ator <pessoa> \
  --papel aprovador
```

O método científico não substitui os gates. Ele responde "devemos?"; os gates respondem "podemos?".

## Templates

- [brief-de-inovacao.md](templates/brief-de-inovacao.md)
- [protocolo-de-experimento.md](templates/protocolo-de-experimento.md)
- [nota-de-pesquisa.md](templates/nota-de-pesquisa.md)
- [revisao-cientifica.md](templates/revisao-cientifica.md)
- [relatorio-de-experimento.md](templates/relatorio-de-experimento.md)
- [rubrica-de-pesquisa.md](templates/rubrica-de-pesquisa.md)
- [pacote-de-evidencias.md](templates/pacote-de-evidencias.md)

## Referências

- [mlops.md](mlops.md)
- [publicacao-de-modelos.md](publicacao-de-modelos.md)
- [retreinamento-e-recalibracao.md](retreinamento-e-recalibracao.md)
- [privacidade-lgpd.md](privacidade-lgpd.md)
- [runbooks.md](runbooks.md)
- [README do projeto de risco](../projetos/risco-infrequencia/README.md)
- [Uso responsável](../projetos/risco-infrequencia/uso-responsavel.md)
- [ADR-017](adr/017-diretrizes-de-ciencia-e-inovacao.md)
