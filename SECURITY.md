# Segurança

## Versões com suporte

O projeto roda em uma branch principal. Use a última revisão.

## Como reportar uma vulnerabilidade

Escreva para o mantenedor pelo canal privado indicado no perfil do repositório. Não abra issue pública com detalhes da falha, exploit, dados de acesso ou logs que contenham dados pessoais.

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
- **Segredos**: apenas variáveis de ambiente documentadas em .env.example; nenhuma credencial no controle de versão.
- **Auditoria**: trilha em acréscimo com ator, papel e alvo; logs estruturados sem dados de alunos.
- **Dependências**: versões exatas fixadas; atualização é decisão deliberada com ADR.

## Limitações conhecidas

- O limitador de papel (aprovador) é contrato de processo na CLI e no painel local, não autenticação forte: ambientes compartilhados devem restringir o acesso ao sistema operacional.
- O painel Streamlit é interno e sem autenticação própria: rodar em rede confiável ou atrás de controle de acesso.
- A assinatura do pacote é lógica (hashes no manifesto), não criptográfica: o canal de entrega do zip deve ser protegido pela escola.
