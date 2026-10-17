# ADR-015: registro de metadados em JSON com auditoria JSONL

## Estado

Aceita.

## Contexto

O briefing pede estrutura de banco de metadados leve no início e expansível, com registro versionado de modelos, estados, aprovações e trilha de auditoria. As operações são de baixa concorrência (uma pessoa da equipe por vez) e o conteúdo precisa ser legível, auditável e simples de copiar junto com o workspace.

## Decisão

- O registro de modelos e publicações é um JSON único em `var/estado/registro.json`, gravado de forma atômica (arquivo temporário mais renomeação).
- A auditoria é JSONL só de acréscimo em `var/estado/auditoria.jsonl`: cada linha carrega momento, ator, papel, ação e alvo; nenhuma escrita apaga história.
- As tarefas de fundo da interface web seguem o mesmo padrão em `var/estado/tarefas.jsonl`, com estado mais recente por identificador.
- As transições de estado do modelo são validadas em código (experimental para candidato para homologado para publicado, com descontinuação e arquivamento), e promoção a homologado ou publicado exige papel de aprovador.

## Consequências

- Qualquer operação é inspecionável com editor de texto, e o backup é cópia de pasta.
- A gravação atômica evita registro corrompido por interrupção; o acréscimo puro garante trilha contínua.
- Migração futura para SQLite é direta: o JSON já tem forma de tabela e a fachada em `modelos/registro.py` isola o acesso.

## Alternativas consideradas

- SQLite desde o primeiro dia: consultas mais ricas, porém binário para leitura humana e mais peças para o backup do workspace.
- Banco externo: contra a execução local sem credenciais.
