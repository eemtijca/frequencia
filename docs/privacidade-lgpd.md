# Privacidade e LGPD

Como o FrequencIA trata dados pessoais à luz da Lei Geral de Proteção de Dados. O objetivo é documentar de forma transparente o que existe, por que existe e como a escola, controladora, exerce seus deveres.

## Princípios aplicados

1. **Privacidade por padrão**: dados pessoais reais nunca entram no repositório, em artefatos versionados, em logs públicos ou em pacotes distribuídos.
2. **Inferência local e offline**: o artefato final roda no navegador do usuário, sem envio de dados pessoais a servidores externos.
3. **Minimização**: o modelo consome apenas números derivados de frequência; nome, texto livre e identificadores diretos ficam fora do contrato.
4. **Modelo como apoio**: toda saída é sugestão com incerteza visível, sujeita a revisão e descarte humano.
5. **Reprodutibilidade e rastreabilidade**: experimento, dataset, feature e modelo rastreáveis até configuração, linhagem e hash.

## Dados tratados

| Dado | Finalidade | Retenção |
| --- | --- | --- |
| Amostras sintéticas (nomes sintéticos, sem pessoas reais) | Testes, validação de contrato e demonstração | No repositório, sob MIT |
| Exportações institucionais autorizadas | Treino e recalibração sob base legal registrada | Conforme política da escola; cópias em var/ são removíveis |
| Contexto agregado do MEC | Features de ambiente por série | No pacote, dados abertos |
| Logs estruturados | Operação e auditoria | Agregados, sem dados de alunos |
| Trilha de auditoria | Prestação de contas de ações | Quem agiu, o quê e quando; sem conteúdo de frequência |
| Feedback agregado de uso | Acurácia observada, taxa de descarte e drift | Contagens por dia, nunca registros individuais |

## Bases legais

Dados institucionais só entram com base legal declarada na importação: execução de política pública, obrigação legal, consentimento ou tutelar. A importação recusa origem institucional sem base. O consentimento, quando usado, precisa ser gerenciado pela escola conforme sua política, e a revogação interrompe novos usos.

## Direitos do titular

- **Acesso e portabilidade**: a escola exporta do FrequenciApp tudo o que existe; o FrequencIA não guarda nada além do que a escola importou.
- **Correção**: corrige-se no FrequenciApp e reexporta; o FrequencIA reprocessa a partir da nova exportação.
- **Eliminação**: remover a pasta de importação em var/dados/importados remove a cópia local; artefatos treinados não contêm dados pessoais, e a redestilação parte de dados novos.
- **Informação**: este documento e o diálogo do app explicam o tratamento.

## Papel da escola e do FrequencIA

A escola é a controladora: define finalidade, base legal, retenção e quem acessa. O FrequencIA é a ferramenta que processa sob instrução, sem telemetria externa, sem dependência de terceiros e com execução local. O desenvolvedor do FrequencIA não tem acesso a dados de produção.

## Portões técnicos

- **Detector de PII**: regex própria de português (CPF, CNPJ, telefone, e-mail, CEP, RG, data de nascimento) mais presidio em modo padrão, varrendo campos de texto em toda importação e antes de todo treino.
- **Bloqueio de dataset**: dataset com achado não entra no treino; a mensagem aponta tabela, campo e contagem.
- **Identificadores proibidos**: colunas como cpf, telefone, e-mail e matrícula são barradas na validação de esquema.
- **Pseudonimização determinística**: hash SHA-256 com sal, estável para manter junções.
- **Testes**: a suíte inclui a garantia de que nenhum nome sintético ou identificador de aluno vaza para artefatos exportados.

## Incidentes

Suspeita de vazamento é tratada como incidente da escola: conter (remover a pasta importada e regenerar artefatos), notificar os titulares conforme a lei e registrar no canal interno. A trilha de auditoria mostra o que foi importado, por quem e quando. Vulnerabilidades da ferramenta seguem SECURITY.md.

## Repositório limpo

O histórico e os arquivos atuais não contêm dados reais de pessoas: o gerador é sintético e determinístico, a amostra versionada usa nomes sintéticos, e a verificação de integridade acompanha cada pacote.
