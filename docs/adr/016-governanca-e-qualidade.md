# ADR-016: governança do repositório e portões de qualidade

## Estado

Aceita.

## Contexto

O FrequencIA nasceu como derivado do FrequenciApp, mas não herdou a camada de governança do repositório de origem: não havia código de conduta, templates de issue e pull request, catálogo de etiquetas, CODEOWNERS, Dependabot, workflows de qualidade e proteção da branch principal. A ausência desses controles deixava o histórico exposto a commits diretos, padronização apenas informal e publicação sem validação automática.

O projeto tem particularidades que impedem copiar o FrequenciApp sem adaptação: é um pacote Python 3.12 com dependências de ML fixadas, usa DVC em modo sem Git, publica um artefato JavaScript e um pacote Python, e não tem banco de dados nem implantação contínua.

## Decisão

- Adotar o modelo de governança do FrequenciApp, adaptado ao stack Python e ao ciclo de MLOps: CONTRIBUTING, AGENTS, CODE_OF_CONDUCT, SECURITY, templates, CODEOWNERS e catálogo de etiquetas.
- Automatizar a classificação e a validação de pull requests com `labeler.yml` e `etiquetas.yml`, incluindo o check `validar`.
- Cobrir qualidade, ciclo completo, empacotamento, Compose, CodeQL e publicação em workflows separados.
- Proteger a `main` com rulesets de qualidade, revisão e tags: pull request obrigatório, checks verdes, revisão de CODEOWNERS, conversas resolvidas, squash e tags `v*` imutáveis.
- Usar Dependabot para pip, pre-commit, GitHub Actions, Docker e Docker Compose. Versões menores e correções entram agrupadas por domínio; versões maiores ficam individuais. Security updates ficam ativados e têm prioridade, uma decisão consciente que diverge do FrequenciApp.
- Publicar wheel, sdist e imagem de runtime no GHCR em release estável, com ambiente `release` restrito a tags `v*`.
- Validar o caminho Docker no CI, incluindo o ciclo completo com MLflow em containers separados.
- Gerar e conferir o dicionário de features a partir do catálogo, eliminando a promessa de um script que não existia.

## Consequências

- A `main` passa a receber mudanças apenas por pull request, com checks e revisão. O histórico fica linear e auditável.
- O custo de CI aumenta porque a stack de ML é instalada em mais de um job; o cache de pip, os grupos do Dependabot e os limites de PR reduzem o volume.
- Toda issue e todo pull request precisam de etiquetas; o workflow corrige o que for possível e reprova o restante.
- PRs do Dependabot são revisados como qualquer outra mudança, mas com prioridade diferente para correções de segurança.
- A publicação deixa de depender de passos manuais não registrados: a tag, o changelog, o wheel e a imagem passam por validação.
- O caminho Docker deixa de ser apenas documentado e passa a ser exercitado no CI.
- A governança exige manutenção: catálogo de etiquetas, versões do ruff no pyproject e no pre-commit, e visibilidade do pacote GHCR.

## Alternativas consideradas

- Manter apenas revisão manual, sem rulesets: não impede commit direto na `main` nem garante checks verdes.
- Copiar os workflows do FrequenciApp sem adaptação: dependem de Next.js, Prisma, Vercel e banco, que não existem aqui.
- Usar proteção clássica de branch em vez de rulesets: perderia a proteção de tags e a granularidade de bypass por ator.
- Deixar o Dependabot apenas com security updates: reduziria o ruído, mas perderia a manutenção regular de uma stack fixada.
- Publicar apenas wheel e sdist, sem imagem: simplificaria o release, mas não entregaria o caminho containerizado que o projeto documenta.
