# Changelog

Todas as mudanças relevantes deste projeto são registradas neste arquivo.

O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o projeto adota [Versionamento Semântico](https://semver.org/lang/pt-BR/).

Enquanto a primeira versão pública não é lançada, a versão do projeto permanece fixada em `0.1.0` e as mudanças ficam na seção Não publicado.

## [Não publicado]

### Corrigido

- Promoção verifica requisitos no motor: candidato exige gates aprovados gravados no registro; homologado e publicado exigem aprovação vigente, e uma rejeição posterior bloqueia. O checklist do painel passa a vir do motor (ADR-018).
- Publicação valida transição de estado, versão e hash do `modelo.js` contra o registro antes de gravar qualquer arquivo, monta a release em pasta temporária e só então a troca; uma publicação recusada não deixa mais release parcial no canal.
- Rollback valida a versão alvo antes de retirar a atual do canal e passa a apontar a versão atual do registro para a restaurada.
- Registro de modelos serializa leitura, alteração e gravação sob trava de arquivo, sem perder escritas de tarefas paralelas do painel.
- Recusa por papel ganha erro próprio (`ErroPermissao`) em vez de aparecer como falta de permissão de pasta, e a tradução de `ValueError` não duplica mais o ponto final.

### Adicionado

- Ecossistema completo de MLOps para o modelo de risco individual de infrequência: geração de dados sintéticos determinísticos, construção de dataset temporal com ponto-in-tempo estrito, catálogo de features versionado com 47 features contratadas, ensemble offline com sete membros e validação temporal, destilação para estudante leve, calibração de Platt regularizada, predição conforme Mondrian por série e faixa de histórico, avaliação com subgrupos, fairness e gates objetivos.
- Exportação do modelo destilado para JavaScript puro via m2cgen com invólucro de calibração, aquecimento, estados de confiança, histerese de alerta e fallback de regras espelhado; caminho alternativo ONNX documentado e testado.
- CLI `frequencia` com doze grupos funcionais (dados, privacidade, features, datasets, experimentos, avaliacao, exportacao, empacotamento, registro, publicacao, monitoramento e auditoria) e modos transversais: seco, JSON, detalhado, silencioso, perfil e força com justificativa auditada.
- Aplicação Streamlit com dezesseis páginas de governança, papéis de observador, cientista, engenheiro e aprovador, e tarefas de fundo que disparam a própria CLI.
- Registro de modelos com estados e transições (experimental, candidato, homologado, publicado, descontinuado, arquivado), aprovações, publicação local com rollback e revogação, e trilha de auditoria em acréscimo.
- Monitoramento com feedback agregado, drift por PSI, verificação de validade e relatório de saúde com recomendações de retreinamento.
- Rastreamento de experimentos no MLflow local com backend SQLite e integração com Optuna opcional; versionamento de dados com DVC em modo sem Git.
- Suíte de testes com 68 verificações: dados, privacidade, features, pipelines, exportação com paridade Python e Node, CLI, interface web, guarda editorial e propriedades com Hypothesis.
- Documentação institucional completa em português brasileiro, com dezessete ADRs, guias de dados do MEC, privacidade e LGPD, publicação, retreinamento, runbooks e contrato de integração com o FrequenciApp.
- Governança do repositório com guia de contribuição ampliado, código de conduta, templates de issue e pull request, CODEOWNERS, catálogo de etiquetas, Dependabot e política de releases.
- Automação de qualidade com workflows de formatação, lint, tipos, testes, ciclo completo, build, CodeQL, etiquetas e publicação de artefatos.
- Políticas de proteção da branch principal e das tags de release, com revisão obrigatória por CODEOWNERS, checks de qualidade, squash e ambiente de release.
- Verificação do dicionário de features e sincronização das etiquetas do GitHub pelo próprio repositório.
- ADR-016 registrando a governança, os portões de qualidade e o fluxo de release.
- Imagem Docker multi-stage com runtime enxuto, Node 20 no estágio de desenvolvimento e `libgomp1` para o LightGBM.
- Validação do Compose no CI, com MLflow e painel saudáveis e ciclo completo executado no container.
- Instalação limpa do wheel e publicação da imagem de runtime no GHCR.
- Skill de agentes em `.agents/skills/frequencia/`, com manual de operação, catálogo dos 94 comandos, playbooks, critérios de engenharia, governança, modo pesquisa e avaliações de comportamento científico.
- Diretrizes de ciência e inovação em `docs/ciencia-e-inovacao.md`, com funil de inovação, hierarquia de evidência, duas trilhas, protocolo, revisão independente, portfólio e resultados negativos.
- Templates de brief, protocolo, nota de pesquisa, revisão científica, relatório, rubrica e pacote de evidências em `docs/templates/`.
- ADR-017 registrando as diretrizes de ciência e inovação e o modo pesquisa dos agentes.
- Guia humano do cientista e guia da coordenação, com método, decisão, trabalho com agentes, uso responsável e cenários práticos.
- Serviço `cli` no Compose, imagens compartilhadas entre serviços e alvos Docker-first no Makefile, com `venv-*` como fallback.
- Estágio de desenvolvimento do Dockerfile com documentação, projetos, governança e skill, e `.dockerignore` ajustado para a guarda editorial completa no container.
- README com getting started Docker, ciclo pela CLI, serviços, testes e fallback venv; comandos executáveis em blocos bash.
- Runbooks atualizados para Docker, com inspeção de artefatos, backup e restore do volume.
