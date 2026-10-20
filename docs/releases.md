# Releases

Este documento descreve a política de versões, o fluxo de release e os artefatos publicados pelo FrequencIA.

## Política de versão

O projeto segue o [Versionamento Semântico](https://semver.org/lang/pt-BR/) e mantém o [CHANGELOG.md](../CHANGELOG.md) no formato [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).

- Versão maior: mudança incompatível em contrato de features, manifesto, formato do pacote ou configuração obrigatória.
- Versão menor: funcionalidade nova compatível com as versões anteriores.
- Versão de correção: correção de comportamento, segurança e dependências.

Enquanto a primeira versão pública não é lançada, a versão permanece fixada em `0.1.0` e as mudanças acumulam na seção Não publicado do changelog. A primeira release será a `v1.0.0`; a partir dela, o versionamento semântico passa a reger as versões.

## Tags

- As tags de release usam o formato `vX.Y.Z`, como `v1.0.0`.
- A ruleset `Tags de release` protege `refs/tags/v*` contra criação, atualização, exclusão e force-push fora do bypass de administrador da organização.
- Tags são imutáveis. Uma release com defeito recebe uma nova versão de correção; a tag anterior não é movida nem apagada.
- A release só é criada com a `main` verde e com o `CHANGELOG.md` atualizado.

## Fluxo de release

1. Atualize a versão em `pyproject.toml` e mova as entradas da seção Não publicado para a versão correspondente no `CHANGELOG.md`.
2. Abra um pull request com a mudança de versão e o changelog, no formato Conventional Commits.
3. Depois do merge, crie a tag e a release pelo GitHub CLI:

```bash
gh release create vX.Y.Z --generate-notes
```

4. O workflow `publicacao.yml` roda no evento de release estável e:
   - valida a tag contra a versão do `pyproject.toml`;
   - constrói wheel e sdist;
   - anexa os artefatos à release;
   - publica a imagem de runtime no GHCR.

O workflow também aceita `workflow_dispatch`, desde que a execução use a tag como ref:

```bash
gh workflow run publicacao.yml --ref vX.Y.Z -f versao=vX.Y.Z
```

Pré-releases não publicam artefatos.

## Artefatos

| Artefato | Conteúdo | Destino |
| --- | --- | --- |
| Wheel | Pacote `frequencia` e entry point da CLI | Anexo da release |
| Sdist | Código-fonte do pacote | Anexo da release |
| Imagem de runtime | CLI, painel e MLflow com dependências de produção | GHCR |
| Pacote de inferência | `modelo.js`, `fallback.js`, `manifest.json` e `dados-teste.json` | `var/pacotes/` e canal de publicação local |

O pacote de inferência tem versionamento próprio, gerado pelo ciclo de experimentos e publicação de modelos. Ele não é anexado automaticamente à release do repositório; o fluxo está em [publicacao-de-modelos.md](publicacao-de-modelos.md).

O projeto não publica no PyPI. O consumo do pacote Python acontece pelo código-fonte, pelo wheel da release ou pela imagem de runtime.

A imagem de runtime é construída e validada no workflow `testes.yml` antes de qualquer release. O Compose sobe o MLflow e o painel, confere a saúde dos dois serviços e executa o ciclo completo no container.

### Visibilidade do GHCR

A primeira publicação cria o pacote `ghcr.io/eemtijca/frequencia`. Se a visibilidade padrão for privada, um mantenedor deve torná-la pública nas configurações do pacote ou pela API de pacotes do GitHub, com um token que tenha permissão de administração do pacote. O workflow não altera a visibilidade.

## Suporte

- A `main` e a última release estável recebem correções.
- Correções de segurança entram primeiro na `main` e saem na próxima versão de correção.
- Quando existir uma linha antiga a manter, a branch `release/1.x` nasce da tag correspondente e recebe retroportes com a etiqueta `backport release/1.x`.
- A linha anterior recebe apenas segurança e correções críticas por 3 meses após o lançamento do próximo major.

## Rollback

- Não mova nem apague uma tag publicada. Publique uma versão de correção.
- Se a imagem publicada estiver incorreta, publique uma nova versão e ajuste o consumo para a tag correta.
- Se o pacote de inferência tiver problema, use o rollback local descrito em [publicacao-de-modelos.md](publicacao-de-modelos.md).
- O `CHANGELOG.md` registra a correção e o motivo do rollback.

## Etiquetas de versão

- `versao: maior`, `versao: menor` e `versao: correcao` são aplicadas pelo workflow de etiquetas conforme o título do pull request.
- O rodapé `Assisted-by` registra a autoria assistida por IA.
