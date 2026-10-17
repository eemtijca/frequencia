# Contribuindo

Guia de desenvolvimento do FrequencIA: como preparar o ambiente, propor mudanças, escrever código, testar e documentar. Para vulnerabilidades, siga o [SECURITY.md](SECURITY.md).

## Antes de começar

- Abra uma issue antes de funcionalidades novas, mudanças estruturais e correções grandes; ajustes pequenos e evidentes podem seguir direto.
- Toda mudança estrutural ganha ADR em docs/adr/ com estado, contexto, decisão, alternativas e consequências.
- Nunca inclua segredos, credenciais, dados reais de alunos ou dados pessoais em issues, commits, logs ou capturas.
- A convenção de identificadores está na ADR-006: domínio em português, infraestrutura consagrada em inglês.

## Ambiente de desenvolvimento

```bash
bash scripts/setup.sh      # venv com Python 3.12 e dependências pinadas
bash scripts/smoke.sh      # ciclo completo mais suíte de testes
streamlit run src/frequencia/web/app.py
```

Sem Docker, o mesmo fluxo roda no venv; com Docker, `docker compose up --build` sobe mlflow e o painel. As variáveis de ambiente estão em [.env.example](.env.example).

| Comando | Efeito |
| --- | --- |
| `make test` | Suíte pytest completa. |
| `make lint` | ruff no código e nos testes. |
| `make tipo` | mypy no pacote. |
| `make smoke` | Ciclo completo com dados sintéticos. |
| `make demo` | Painel de governança com dados de demonstração. |

## Padrões de código

- Cada arquivo próprio começa com comentário de cabeçalho de uma a duas linhas descrevendo o papel, em português.
- Docstrings em português nas funções de domínio; type hints em todo o pacote.
- Sem travessão, meia-risca, reticências tipográficas, aspas curvas e setas em texto de código e documentação: a guarda editorial em tests/test_editorial.py reprova. Use ponto, vírgula, parênteses e aspas retas. Cercas de código (blocos) são isentas porque diagramas exigem setas.
- Erros de domínio usam ExcecaoFrequencia com mensagem curta e dica acionável; a CLI traduz qualquer exceção para português sem stack trace (salvo --detalhado).
- Complexidade precisa de justificativa: o princípio de leveza vale para o código também.

## Testes

- Cada teste cria e limpa a própria massa; nada depende de ordem de execução.
- Ao corrigir defeito, adicione o teste que falharia antes da correção.
- Mudança de feature exige atualização do catálogo, do dicionário gerado e dos testes de contrato.
- Testes que tocam o Node pulam com aviso quando ele está ausente; a validação completa exige Node 20 ou superior.

## Documentação

- Mudança de comportamento atualiza o documento correspondente e o CHANGELOG.md.
- O dicionário de features é gerado por scripts/gerar_dicionario.py a partir do catálogo: mude o catálogo e regenere.
- Texto de interface e mensagens usam o vocabulário aprovado; mensagens novas passam pela revisão de produto antes de entrar no contrato.

## Fluxo de mudança

1. Branch a partir da principal com formato tipo/descricao-curta em minúsculas e hífens.
2. Commits atômicos em Conventional Commits, no presente do indicativo e em português: `feat(features): adiciona feature de reincidência mensal`.
3. Verificações locais verdes: make lint, make tipo, make test.
4. Pull request com problema, mudança, como validar e riscos; etiqueta de área.
5. Revisão por um mantenedor; correções entram como commits novos.

## Commits assistidos por IA

Ferramentas de IA são bem-vindas como apoio, e a responsabilidade pela mudança é de quem envia. Revise linha a linha, rode as verificações e nunca cole segredos ou dados reais em ferramentas externas.
