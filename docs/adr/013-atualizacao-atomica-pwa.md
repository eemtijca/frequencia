# ADR-013: atualização atômica do modelo no PWA

## Estado

Aceita.

## Contexto

O ponto cego 7 do briefing exige que o modelo novo nunca seja carregado durante o fluxo de chamada, que o Service Worker só ative modelo compatível com a versão instalada do app e que a atualização seja atômica. O FrequenciApp controla o próprio Service Worker, e o contrato de distribuição precisa sustentar isso sem código do app aqui.

## Decisão

- O manifest.json declara `min_app_versao`: o app compara com a própria versão antes de ativar o cache novo; incompatível fica retido até a atualização do aplicativo.
- O hash SHA-256 do modelo.js vai no manifesto: o app confere o hash após o download e descarta o arquivo em divergência, caindo no fallback.
- O pacote carrega `dados-teste.json` com casos e saídas esperadas: o app roda na ativação e só promove o modelo com todas as saídas batendo.
- O LEIA-ME do pacote instrui o carregamento pelo Service Worker fora do fluxo de chamada (no evento de atualização, nunca durante a navegação ativa da Chamada) e o fallback.js com a mesma interface para falha de carregamento, corrupção ou incompatibilidade.
- Publicação e revogação no canal local mantêm uma versão atual por vez, com rollback para a anterior ainda presente.

## Consequências

- A ativação tem três barreiras (versão mínima, hash e autoverificação), e a falha de qualquer uma cai no modo de segurança sem quebrar o painel.
- O teste de paridade com Node roda exatamente os casos que o app rodará, antecipando a autoverificação.
- A interface de prever é idêntica entre modelo.js e fallback.js, o que mantém o contrato único para o app.

## Alternativas consideradas

- Ativação por flag de servidor: exigiria infraestrutura externa contra o princípio de inferência local.
- Versionamento só por nome de arquivo: sem barreira de compatibilidade e sem autoverificação, o ponto cego ficaria aberto.
