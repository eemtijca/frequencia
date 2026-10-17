# ADR-007: stack fixada com substituição por ADR

## Estado

Aceita.

## Contexto

O Prompt 1 declara soberania total sobre escolhas de biblioteca (seção 11), e o Prompt 2 fixa uma stack obrigatória (seção 2.1). O critério de desempate resolve: a lista do Prompt 2 é o padrão, e substituições exigem ganho mensurável documentado. Todas as bibliotecas da lista foram instaladas com versão exata e testadas na prática antes desta decisão.

## Decisão

- O pyproject.toml fixa versão exata de todas as dependências de runtime e dev, todas vindas da lista do Prompt 2: polars, pandas, pandera, scikit-learn, lightgbm, xgboost, catboost, optuna, mlflow, dvc, onnx, skl2onnx, onnxmltools, m2cgen, typer, streamlit, presidio-analyzer, pytest, hypothesis, ruff, mypy e pre-commit.
- Ajustes de compatibilidade encontrados na prática: pyarrow limitado a 25.x por restrição do mlflow 3.17 e numpy limitado a 2.4.x por restrição do presidio-analyzer 2.2.
- Duas adaptações de uso, sem troca de biblioteca: MLflow roda com backend SQLite porque o file store entrou em modo manutenção no mlflow 3.17; presidio roda em modo padrão (sem modelo de linguagem pesado) reforçado por regras próprias de português, detalhado na ADR-009.
- Substituição futura de qualquer biblioteca exige ganho mensurável (tamanho, latência, acurácia ou manutenção) registrado em ADR nova.

## Consequências

- O caminho venv e o caminho Docker instalam exatamente o mesmo conjunto, e a reprodutibilidade é verificável por `pip check`.
- Atualizações de versão passam a ser decisões deliberadas, não efeito de resolver faixas abertas.
- O tamanho total do ambiente (cerca de 1,5 GB com catboost e xgboost) é o preço da diversidade do ensemble, aceito porque só o estudante destilado vai ao artefato publicado.

## Alternativas consideradas

- Faixas abertas de versão: mais fácil de manter no curto prazo, porém quebra a reprodutibilidade que o briefing exige.
- Trocar catboost ou xgboost por mais variedades de lightgbm: encolheria o ambiente, mas perderia diversidade de família no ensemble, que é o motor da robustez.
