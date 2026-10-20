# Segurança

## Versões com suporte

O projeto é mantido em uma branch principal. Use a última revisão da `main` ou a última release estável.

## Como reportar uma vulnerabilidade

Use o canal privado de [advisories do GitHub](https://github.com/eemtijca/frequencia/security/advisories/new) ou escreva para o mantenedor pelo canal privado indicado no perfil do repositório. Não abra issue pública com detalhes da falha, exploit, dados de acesso ou logs que contenham dados pessoais.

Inclua na mensagem:

- Descrição do problema e impacto possível.
- Passos ou condições para reproduzir.
- Versões do FrequencIA, do Python e do Node envolvidas.
- Sugestão de correção, se houver.

O relato é respondido em até 7 dias. Correções de segurança entram como lançamento com aviso no changelog, sem detalhes de exploração antes da correção disponível.

## Práticas adotadas

- **Execução local sem credenciais**: nenhuma dependência de serviço externo no fluxo de treino ou inferência; o pacote publicado roda no navegador sem rede.
- **Validação de entrada**: esquemas pandera em toda importação; campos proibidos barrados antes do treino; datas e horários conferidos por expressão regular de formato.
- **Portão de privacidade**: detector de PII em dois motores (regras próprias e presidio) rodando na importação e antes de todo treino; dataset com achado é bloqueado.
- **Integridade**: hash SHA-256 de pastas de dados, do modelo e de cada arquivo do pacote; conferência na publicação e na ativação pelo app.
- **Segredos**: apenas variáveis de ambiente documentadas em `.env.example`; nenhuma credencial no controle de versão.
- **Auditoria**: trilha em acréscimo com ator, papel e alvo; logs estruturados sem dados de alunos.
- **Dependências**: versões exatas fixadas no `pyproject.toml`; Dependabot cobre pip, pre-commit, GitHub Actions, Docker e Docker Compose. Security updates estão ativados e têm prioridade na triagem. Aumentos de versão maior exigem decisão registrada na ADR-007.
- **Análise estática**: CodeQL para Python em push, pull request e agenda semanal.
- **Varredura de segredos**: secret scanning ativado no repositório, com alertas de credenciais expostas.
- **Workflows**: permissões mínimas, ações fixadas por SHA e nenhuma execução de código de pull request em contexto com escrita (`pull_request_target`).
- **Revisão**: a branch principal exige pull request, checks verdes e aprovação de um mantenedor do CODEOWNERS.

## Limitações conhecidas

- O limitador de papel (aprovador) é contrato de processo na CLI e no painel local, não autenticação forte: ambientes compartilhados devem restringir o acesso ao sistema operacional.
- O painel Streamlit é interno e sem autenticação própria: rodar em rede confiável ou atrás de controle de acesso.
- A assinatura do pacote é lógica (hashes no manifesto), não criptográfica: o canal de entrega do zip deve ser protegido pela escola.
- A imagem publicada no GHCR depende da visibilidade configurada no pacote; o consumo por terceiros exige que o pacote seja público.
- Não há segundo fator de autenticação no GitHub; contas de mantenedores devem usar credenciais individuais e 2FA.
