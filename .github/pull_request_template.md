## Descrição

Descreva o problema, a solução e o motivo da mudança.

## Issue relacionada

Closes #

## Tipo de mudança

- [ ] Correção de bug
- [ ] Funcionalidade nova
- [ ] Refatoração ou manutenção
- [ ] Documentação
- [ ] Testes ou CI

## Etiquetas

Aplique ao menos uma etiqueta de tipo e uma de área com `gh pr edit --add-label`. Pull requests do Dependabot recebem `dependencies` e `area: infra` e dispensam a validação de título.

- Tipo: `bug`, `enhancement`, `documentation`, `refactor`, `testes`, `ci`, `desempenho` ou `manutencao`
- Área: `area: dados`, `area: features`, `area: treino`, `area: modelos`, `area: exportacao`, `area: monitoramento`, `area: privacidade`, `area: cli`, `area: painel` ou `area: infra`

## Commits

- [ ] Cada commit é uma mudança lógica completa e revisável, sem trabalho em andamento.
- [ ] O histórico exposto passou por `git rebase -i --autosquash` e está limpo.
- [ ] Todos os commits do assunto estão neste único pull request.
- [ ] O título segue Conventional Commits, no formato `tipo(escopo): descrição`, no presente do indicativo; com o merge por squash, o título é o commit que entra na `main`.

## Como validar

Informe os comandos executados e, quando aplicável, os passos de interface. Capturas de antes e depois ficam anexadas ao pull request, sem entrar nos commits.

## Riscos e migrações

Descreva riscos, variáveis de ambiente novas, mudanças de contrato de features, manifesto ou pacote e mudanças incompatíveis. Use "Não se aplica" quando não houver.

## Impacto de versão

Aplique a etiqueta `versao:` correspondente ao impacto: `versao: maior` para mudança incompatível, `versao: menor` para funcionalidade nova compatível e `versao: correcao` para correção compatível. Enquanto a primeira versão pública não é lançada, a versão permanece em `0.1.0` e o changelog acumula na seção Não publicado.

## Uso de IA

Informe se houve apoio de ferramentas de IA e como o resultado foi revisado. A responsabilidade pela mudança é de quem envia. Commits com geração relevante levam o rodapé `Assisted-by: ferramenta:modelo`.

## Checklist

- [ ] Abri o pull request somente com o trabalho finalizado.
- [ ] Se precisei mexer depois da abertura, converti para rascunho com `gh pr ready --undo` e só marquei como pronto com tudo verde.
- [ ] Segui o padrão de branches e commits do [CONTRIBUTING.md](../CONTRIBUTING.md).
- [ ] Revisei o próprio diff antes de pedir revisão.
- [ ] Rodei `make formato-check`, `make lint`, `make tipo` e `make test`.
- [ ] Rodei `make smoke` quando a mudança afeta dados, features, pipelines, exportação ou pacote.
- [ ] Atualizei a documentação correspondente, o dicionário de features e o CHANGELOG.md.
- [ ] Atualizei os testes de contrato quando features, manifesto ou limiares mudaram.
- [ ] Registrei ADR quando a mudança é estrutural.
- [ ] Revisei a segurança quando a mudança toca dependências, workflows, privacidade ou dados sensíveis.
- [ ] Não incluí segredos nem dados reais de alunos.
