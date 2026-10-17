# Guia de dados do MEC

Fontes externas de contexto educacional usadas pelo FrequencIA, com licenças, granularidade e limitações. O repositório carrega metadados, esquemas e amostras sintéticas; microdados reais ficam fora do controle de versão, referenciados por hash e manifesto no momento da importação.

## Catálogo de fontes

| Fonte | Órgão | Granularidade | Periodicidade | Uso no FrequencIA |
| --- | --- | --- | --- | --- |
| Censo Escolar da Educação Básica | INEP | Escola, turma e aluno (agregado nos indicadores) | Anual | Contexto agregado por série e escola |
| SAEB | INEP | Escola e série de avaliação | Bienal | Variável de contexto opcional, agregada |
| IDEB | INEP | Escola, rede, município e estado | Bienal | Contexto por série no catálogo de features |
| Indicadores de rendimento escolar | INEP | Escola e série | Anual | Taxas de abandono, aprovação e reprovação agregadas |

As URLs oficiais e as condições completas estão no catálogo interno (`frequencia dados listar-fontes`) e em `src/frequencia/dados/mec.py`.

## Licenças e restrições

- Os dados do INEP são abertos, com licença internacional CC BY 4.0 declarada pelo órgão para os microdados do Censo; cada importação registra a licença declarada no manifesto de importação.
- Três regras inegociáveis do uso: nenhum microdado real entra no repositório; importações registram data, origem, licença e hash antes do uso em treino; a agregação é por escola e série, e linha por aluno do MEC nunca vira feature.

## Formato esperado do contexto

A tabela contexto_mec carrega uma linha por série com os agregados que alimentam o grupo de features mec:

| Campo | Tipo | Faixa esperada |
| --- | --- | --- |
| serie_id | texto | Identificador da série do FrequencIA |
| taxa_abandono_historica | fração | 0 a 1 |
| taxa_reprovacao | fração | 0 a 1 |
| distorcao_idade_serie | fração | 0 a 1 |
| ideb | índice | 0 a 10 |

O pacote publicado carrega esses valores em contexto-mec.json para uso offline do app: o app não consulta o MEC, lê a tabela do pacote.

## Importação de dados reais

```bash
frequencia dados importar <pasta> --origem mec --licenca "CC BY 4.0"
```

O fluxo valida o esquema, roda o detector de PII, grava a cópia em var/dados/importados com hash da pasta inteira e registra o manifesto de importação. A base legal não é exigida para origem mec (dados abertos agregados), mas é obrigatória para origem institucional.

## Limitações

- Os indicadores do INEP vêm por escola e série do ano anterior: o contexto é estático dentro do ano letivo, e a defasagem entra como limitação declarada no cartão do modelo.
- A distorção idade-série não existe por aluno no contrato do FrequencIA (o app não guarda idade), então o valor agregado da série é a única forma permitida.
- Amostras sintéticas de contexto acompanham o gerador (valores plausíveis por série), documentadas como referência de formato.
