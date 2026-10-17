# ADR-009: presidio em modo padrão reforçado por regras próprias

## Estado

Aceita.

## Contexto

O briefing exige detecção de PII em textos livres de português e alerta que o suporte do presidio a português é limitado. Na prática, a criação do AnalyzerEngine padrão tenta carregar um modelo spaCy de inglês grande, com download automático de centenas de megabytes, e o suporte a `pt` depende de modelo de linguagem separado. O portão de privacidade precisa rodar offline, rápido e sem downloads surpresa.

## Decisão

- O presidio-analyzer 2.2 é usado em modo padrão: motor NLP leve, construído sobre o tokenizador `spacy.blank("pt")` local, sem modelo treinado e sem download.
- Os reconhecedores registrados são `PatternRecognizer` com regex brasileiras (CPF, CNPJ, e-mail, telefone) rodando com idioma pt; a detecção de nomes de pessoas fica com regra própria (duas palavras capitalizadas com sobrenome da lista de mais comuns do Brasil).
- A camada `examinar_tabelas` combina os dois motores e é a entrada única do portão de privacidade; o presidio é camada complementar, e falha dele degrada sem derrubar a detecção de regras próprias.
- A pseudonimização é própria: hash SHA-256 com sal, determinístico, para manter junções entre tabelas sem expor o original.

## Consequências

- O detector roda em milissegundos por tabela, offline, com zero download de modelo.
- A cobertura de documentos e contatos brasileiros fica forte; nomes dependem da heurística de sobrenomes, documentada como limitação.
- O identificador sintético (Estudante NNNN) é explicitamente isento, para não gerar falso positivo em todo pacote de teste.

## Alternativas consideradas

- Modelo spaCy pt_core_news_lg: melhor cobertura de entidades, porém download de dezenas de megabytes em runtime e dependência de rede no primeiro uso.
- Só regras próprias, sem presidio: perderia a camada pedida pelo briefing e a infraestrutura de reconhecedores com contexto.
