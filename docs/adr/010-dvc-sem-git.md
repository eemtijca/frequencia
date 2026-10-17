# ADR-010: DVC sem repositório Git

## Estado

Aceita.

## Contexto

O entregável final é uma árvore limpa sem histórico Git, e o briefing pede DVC para versionamento de dados e artefatos, reconhecendo que a integração canônica dele é com Git. O comando `dados versionar` precisa funcionar no venv do engenheiro e no smoke test.

## Decisão

- O versionamento usa `dvc init --no-scm`, confirmado na prática: o DVC 3.67 cria `.dvc/` e opera sem repositório Git, com aviso documentado.
- `dvc add` gera o arquivo `.dvc` (declaração com hash md5 e caminho) e move o conteúdo para o cache local, configurado em `var/dvc-cache` para manter a árvore limpa.
- O comando da CLI registra o hash retornado no log estruturado e na auditoria, junto com o hash SHA-256 do pacote, que é o identificador primário de linhagem.
- Quando o consumidor colocar o repositório sob Git, os arquivos `.dvc` já existem e o fluxo canônico (commit dos ponteiros, cache fora da árvore) encaixa sem retrabalho.

## Consequências

- A amostra sintética versionada (`dados/sinteticos/amostra`) tem declaração DVC e hash auditável desde o primeiro dia.
- Recursos avançados do DVC (pipelines declarativas, exp push) ficam disponíveis para o futuro dono do repositório, sem custo agora.
- O hash SHA-256 do manifesto continua sendo a âncora de integridade; o DVC complementa com cache endereçável por conteúdo.

## Alternativas consideradas

- Abandonar DVC e usar só hashes manuais: perderia a ferramenta pedida no briefing e a infraestrutura de cache.
- Criar um Git só para o DVC: violaria a restrição de entrega sem histórico.
