# Guia da coordenação

Guia de bolso para usar o indicador de risco de infrequência no dia a dia da escola. O indicador é uma sugestão de apoio, não uma decisão. A política completa está em [uso-responsavel.md](../projetos/risco-infrequencia/uso-responsavel.md).

## O que é o indicador

É uma probabilidade entre 0 e 1 de o estudante acumular duas ou mais faltas nos próximos sete dias letivos, ou de deixar a escola nesse período. Ele vem do histórico de chamadas, faltas, saídas e entradas que a escola já registra. O cálculo acontece no aparelho da coordenação; nada é enviado a servidores externos.

O indicador é calculado a partir de padrões de frequência. Ele não mede caráter, família, esforço ou intenção.

## O que o indicador não é

- Não é uma decisão sobre o estudante.
- Não é um diagnóstico.
- Não é um rótulo permanente.
- Não é vigilância de localização, relacionamento ou conteúdo.
- Não é prova de que o estudante vai faltar.
- Não é um substituto do olhar da coordenação, da professora ou da família.

## Como ler a tela

| Elemento | Como ler |
| --- | --- |
| Probabilidade | chance estimada de faltas na próxima semana |
| Intervalo | faixa de incerteza; quanto maior, mais cautela |
| Faixa de risco | baixo, médio ou alto, pelos limiares do modelo |
| Estado de confiança | indica se o histórico é suficiente e se o modelo está atualizado |
| Alerta | indica persistência do padrão, com histerese |
| Lista Top-K | estudantes com maior chance de precisar de apoio |

## O que fazer

### Risco alto

- Comece pelo topo da lista diária.
- Leia a probabilidade com o intervalo.
- Verifique o estado de confiança.
- Converse com a professora e a equipe pedagógica.
- Procure entender o contexto antes de agir.
- Registre o feedback e o descarte.

### Risco médio

- Observe nos próximos dias.
- Combine com a professora se há mudança recente.
- Use o indicador como um sinal a mais, não como conclusão.

### Risco baixo

- Mantenha o acompanhamento normal.
- Se houver preocupação da equipe, priorize o olhar humano.
- O indicador não substitui a observação da escola.

## O que nunca fazer

- Exibir o indicador para estudantes ou familiares como rótulo.
- Usar o indicador como único critério de comunicação à família.
- Usar o indicador para medida disciplinar.
- Decorar listas antigas.
- Compartilhar listas fora da equipe autorizada.
- Tratar o número como sentença sobre o estudante.
- Ignorar o intervalo e o estado de confiança.
- Usar um modelo desatualizado.

## Como registrar feedback

- Use a função de descarte quando a realidade contradisser o indicador.
- Registre o que aconteceu de forma agregada, nunca com dados individuais desnecessários.
- O feedback melhora a calibração e a qualidade do apoio.
- O descarte é dado de treino e de melhoria, não motivo de discussão com o estudante.

## Privacidade

- A escola é controladora dos dados.
- O indicador roda localmente; nada sai do aparelho.
- Listas de risco são sensíveis; compartilhe apenas com a equipe autorizada.
- Não exporte nomes ou listas para canais pessoais.
- Em caso de dúvida, consulte a política da escola e o [guia de privacidade](privacidade-lgpd.md).

## Cenários práticos

### O estudante está no topo da lista

Leia o intervalo e o estado de confiança. Converse com a professora. Procure entender se houve mudança recente. Registre o que foi observado. O objetivo é apoio, não vigilância.

### O indicador está alto, mas a professora diz que o estudante está vindo bem

A realidade da escola tem prioridade. Pode ser um falso positivo. Registre o descarte e observe. Não comunique à família com base apenas no número.

### O modelo está desatualizado

Não use o número. Siga a orientação de fallback e solicite atualização à equipe responsável. O indicador desatualizado deve ser suprimido.

### A família pergunta por que o estudante está na lista

Explique que a escola usa um indicador de apoio para organizar o acompanhamento. Não apresente o número como rótulo. Fale sobre apoio, presença e diálogo, não sobre punição.

### Posso compartilhar a lista com outra equipe?

Somente com a equipe autorizada e conforme a política da escola. Listas de risco são dados sensíveis.

### O que faço se perceber um erro nos dados?

Informe a coordenação e a equipe responsável. O dado de chamada ausente ou atrasado pode afetar o indicador. Não tente corrigir o modelo.

## Perguntas frequentes

- **O modelo decide alguma coisa?** Não. Ele estima uma probabilidade e sugere prioridade.
- **O estudante pode ver o número?** Não. O indicador é para a coordenação.
- **O indicador é sempre certo?** Não. Ele erra, e a incerteza está visível.
- **Posso usar para nota ou disciplina?** Não.
- **Posso usar para conversar com a família?** Sim, como apoio e com cuidado, nunca como rótulo.
- **O que faço se a coordenação discordar?** A decisão é humana. Registre o descarte e investigue.
- **Como sei se o modelo está funcionando?** Acompanhe o relatório de saúde, a calibração e o feedback.
- **O que faço se o sistema falhar?** Use o fallback de regras e informe a equipe responsável.

## Quem procurar

- Dúvidas pedagógicas: coordenação e direção.
- Dúvidas sobre dados: equipe responsável pelo FrequenciApp.
- Dúvidas sobre o modelo: equipe do FrequencIA.
- Suspeita de privacidade: canal indicado em [SECURITY.md](../SECURITY.md) e política da escola.

## Lembrete

O indicador ajuda a decidir onde olhar primeiro. A decisão, o cuidado e a relação com o estudante continuam humanos.
