# ADR-018: requisitos de promoção verificados no motor

## Estado

Aceita. Complementa a ADR-015.

## Contexto

As diretrizes do projeto dizem que nenhuma versão é promovida sem gates verdes e aprovação registrada, mas o motor verificava apenas a transição de estado e o papel declarado. Uma versão com gates reprovados virava candidata, uma rejeição registrada não impedia a homologação e o checklist do painel recalculava por conta própria um limiar de AUC, divergente dos gates reais. A regra existia na documentação e dependia da disciplina de quem operava.

A ADR-015 também assumia uma pessoa operando por vez, mas o painel dispara a CLI em subprocessos paralelos que leem e regravam o mesmo `registro.json`; a gravação atômica impede arquivo corrompido, não a perda de uma escrita concorrente.

## Decisão

- O experimento grava o veredito dos gates na versão registrada (`gates.aprovado`, `gates.vereditos`, `gates.avaliado_em`).
- `infra/estado.py` expõe `requisitos_promocao`, a única fonte dos requisitos objetivos: candidato exige gates aprovados; homologado e publicado exigem também aprovação vigente, isto é, a decisão mais recente registrada sobre a versão precisa ser aprovação (uma rejeição posterior cancela aprovações anteriores).
- Descontinuar e arquivar não têm requisito: retirar uma versão nunca fica bloqueado.
- Uma versão fora do estado experimental não pode ser regravada por um novo ciclo, e o veredito de gates com que foi promovida fica preservado. Retirar a versão atual (descontinuar ou arquivar) limpa o ponteiro de versão atual.
- A promoção recusa com `ErroEstado` listando as pendências; a recusa por papel usa `ErroPermissao`.
- O painel exibe o checklist de `requisitos_promocao`, sem cálculo próprio.
- Toda alteração do registro passa por `registro_travado`, que segura uma trava exclusiva de arquivo durante leitura, alteração e gravação.
- Publicação e rollback validam versão, hash do `modelo.js` contra o registro e transição antes de gravar ou remover qualquer arquivo; a release é montada em pasta temporária e trocada no fim.

## Consequências

- A regra de governança passa a valer para CLI, painel e automação igualmente; operar fora do fluxo exige editar o registro à mão, o que fica visível na auditoria.
- Versões registradas antes desta decisão não têm `gates` gravado e precisam passar de novo pelo ciclo, ou pela validação de gates, para virar candidatas.
- A trava usa `fcntl`, disponível em Linux e macOS, que são os ambientes suportados (Docker e venv). Windows nativo não é suportado.

## Alternativas consideradas

- Manter a verificação na CLI: deixaria o painel e qualquer chamada direta ao motor fora da regra.
- Exigir aprovadores distintos de quem treinou (quatro olhos): desejável, mas depende de identidade autenticada, que o projeto ainda não tem; com `--ator` declarado, a regra seria contornável e daria falsa segurança.
- Migrar o registro para SQLite para obter transações: resolve a concorrência, mas antecipa a migração prevista na ADR-015 sem necessidade imediata.
