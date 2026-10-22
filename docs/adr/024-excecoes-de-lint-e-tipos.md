# ADR-024: exceções de lint e nível de verificação de tipos

## Estado

Aceita.

## Contexto

O AGENTS.md exige que nenhuma regra de ruff ou mypy seja desativada sem justificativa em ADR e que todo o pacote tenha type hints. O `pyproject.toml` desativava regras do ruff com justificativa só em comentário, o mypy rodava fora do modo strict sem registro do motivo, e 37 funções do pacote não tinham anotação completa.

## Decisão

Exceções do ruff mantidas:

- `N803` e `N806`: argumentos e variáveis locais seguem o domínio em português e a convenção numérica de matrizes (`X`), ambos previstos na ADR-006.
- `N818`: exceções de domínio terminam em nome português (`ErroValidacao`), não em `Error`.
- `B008`: `typer.Option` como valor padrão é a forma documentada do typer.
- `SIM117` nos testes: `with` aninhados deixam explícita a ordem de contextos nas fixtures.
- `E402` em `web/app.py`: o Streamlit executa o arquivo como script, e o caminho do pacote precisa entrar em `sys.path` antes das importações do FrequencIA.

Verificação de tipos:

- O mypy passa a exigir anotação completa em toda função (`disallow_untyped_defs` e `disallow_incomplete_defs`); as 37 funções sem anotação foram anotadas.
- O modo strict continua desligado. Medição de outubro de 2026: 240 erros em 31 arquivos, sendo 168 `type-arg` (`dict` e `list` sem parâmetros), 37 `no-untyped-def` (resolvidos por esta decisão), 19 `no-any-return`, 13 `no-untyped-call` e 3 outros. A maior parte vem de bibliotecas de ML sem tipos (LightGBM, m2cgen, presidio) e de dicionários JSON do manifesto e do estado.

## Consequências

- Função nova sem anotação reprova no CI.
- Ligar o strict exige tipar os documentos JSON (`TypedDict` para manifesto, estado e relatório de avaliação) antes; esse é o próximo passo, a ser feito por módulo, ligando o strict por arquivo à medida que cada um fica limpo.

## Alternativas consideradas

- Ligar o strict de uma vez: 240 correções mecânicas num único pull request, com `Any` espalhado para calar as bibliotecas sem tipos, o que esconderia mais do que mostraria.
- Manter tudo como estava: deixaria a regra do AGENTS.md sem cumprimento verificável.
