# Changelog

Todas as mudanças relevantes deste projeto são registradas neste arquivo.

O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o projeto adota [Versionamento Semântico](https://semver.org/lang/pt-BR/).

Enquanto a primeira versão pública não é lançada, a versão do projeto permanece fixada em `0.1.0` e as mudanças ficam na seção Não publicado.

## [Não publicado]

### Adicionado

- Ecossistema completo de MLOps para o modelo de risco individual de infrequência: geração de dados sintéticos determinísticos, construção de dataset temporal com ponto-in-tempo estrito, catálogo de features versionado com 47 features contratadas, ensemble offline com sete membros e validação temporal, destilação para estudante leve, calibração de Platt regularizada, predição conforme Mondrian por série e faixa de histórico, avaliação com subgrupos, fairness e gates objetivos.
- Exportação do modelo destilado para JavaScript puro via m2cgen com invólucro de calibração, aquecimento, estados de confiança, histerese de alerta e fallback de regras espelhado; caminho alternativo ONNX documentado e testado.
- CLI `frequencia` com doze grupos funcionais (dados, privacidade, features, datasets, experimentos, avaliacao, exportacao, empacotamento, registro, publicacao, monitoramento e auditoria) e modos transversais: seco, JSON, detalhado, silencioso, perfil e força com justificativa auditada.
- Aplicação Streamlit com dezesseis páginas de governança, papéis de observador, cientista, engenheiro e aprovador, e tarefas de fundo que disparam a própria CLI.
- Registro de modelos com estados e transições (experimental, candidato, homologado, publicado, descontinuado, arquivado), aprovações, publicação local com rollback e revogação, e trilha de auditoria em acréscimo.
- Monitoramento com feedback agregado, drift por PSI, verificação de validade e relatório de saúde com recomendações de retreinamento.
- Rastreamento de experimentos no MLflow local com backend SQLite e integração com Optuna opcional; versionamento de dados com DVC em modo sem Git.
- Suíte de testes com 68 verificações: dados, privacidade, features, pipelines, exportação com paridade Python e Node, CLI, interface web, guarda editorial e propriedades com Hypothesis.
- Documentação institucional completa em português brasileiro, com quinze ADRs, guias de dados do MEC, privacidade e LGPD, publicação, retreinamento, runbooks e contrato de integração com o FrequenciApp.
