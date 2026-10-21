# Documentação

Índice da documentação do FrequencIA. Tudo em português brasileiro, no tom direto e sem ruído herdado do FrequenciApp.

| Documento | Conteúdo |
| --- | --- |
| [arquitetura.md](arquitetura.md) | Camadas, fluxo de execução e mapa entre responsabilidades e pastas. |
| [modelo-de-dados.md](modelo-de-dados.md) | Esquema sintético, derivação da marca e mapeamento com o app. |
| [catalogo-de-modelos.md](catalogo-de-modelos.md) | Modelos, estados do registro e projetos futuros. |
| [dicionario-de-features.md](dicionario-de-features.md) | As 47 features do contrato com semântica completa. |
| [contrato-de-inferencia.md](contrato-de-inferencia.md) | Entrada, saída, fallback e casos de teste do pacote. |
| [contrato-de-manifesto.md](contrato-de-manifesto.md) | Campos do manifest.json e validação aplicada. |
| [mlops.md](mlops.md) | Como treinar, avaliar, calibrar e publicar. |
| [ciencia-e-inovacao.md](ciencia-e-inovacao.md) | Método científico, funil de inovação e critérios de decisão. |
| [guia-do-cientista.md](guia-do-cientista.md) | Guia humano do time de ML e ciência de dados. |
| [guia-da-coordenacao.md](guia-da-coordenacao.md) | Guia humano de uso do indicador na escola. |
| [templates/](templates/) | Brief, protocolo, nota de pesquisa, revisão, rubrica e pacote de evidências. |
| [guia-de-dados-mec.md](guia-de-dados-mec.md) | Fontes do INEP, licenças, granularidade e limitações. |
| [guia-de-exportacao.md](guia-de-exportacao.md) | Como preparar exportações autorizadas do app. |
| [privacidade-lgpd.md](privacidade-lgpd.md) | Dados tratados, bases legais, portões e direitos. |
| [publicacao-de-modelos.md](publicacao-de-modelos.md) | Gates, promoção, release, rollback e revogação. |
| [releases.md](releases.md) | Política de versões, tags, artefatos e suporte. |
| [retreinamento-e-recalibracao.md](retreinamento-e-recalibracao.md) | Sinais, cadência e procedimentos de reanálise. |
| [runbooks.md](runbooks.md) | Procedimentos operacionais passo a passo. |
| [testes.md](testes.md) | Suítes, convenções e cobertura das exigências. |
| [integracao-frequenciapp.md](integracao-frequenciapp.md) | Mapa de features, UX, feature flags e atualização atômica. |
| [adr/](adr/) | Decisões de arquitetura registradas. |

## Decisões registradas

| ADR | Decisão |
| --- | --- |
| [001](adr/001-uso-de-polars.md) | polars 2.0 como motor de dados. |
| [002](adr/002-exportacao-via-m2cgen.md) | m2cgen como exportação primária, ONNX como alternativa. |
| [003](adr/003-calibracao-e-conformal.md) | Platt regularizado, aquecimento e conformal Mondrian. |
| [004](adr/004-pandera-para-esquemas.md) | pandera com backend polars. |
| [005](adr/005-estrutura-fisica-e-camadas.md) | Esqueleto físico por domínios com camadas mapeadas. |
| [006](adr/006-convencao-de-identificadores.md) | Convenção híbrida de identificadores. |
| [007](adr/007-stack-fixada.md) | Stack do Prompt 2 fixada com substituição por ADR. |
| [008](adr/008-mlflow-sqlite.md) | MLflow com backend SQLite local. |
| [009](adr/009-presidio-modo-padrao.md) | presidio em modo padrão com regras próprias. |
| [010](adr/010-dvc-sem-git.md) | DVC sem repositório Git. |
| [011](adr/011-verdade-oculta-sintetica.md) | Verdade oculta no gerador sintético. |
| [012](adr/012-ensemble-destilado.md) | Ensemble offline destilado para estudante leve. |
| [013](adr/013-atualizacao-atomica-pwa.md) | Atualização atômica do modelo no PWA. |
| [014](adr/014-ponto-no-tempo-estrito.md) | Ponto-in-tempo estrito com purga temporal. |
| [015](adr/015-estado-json-auditoria.md) | Registro JSON com auditoria JSONL. |
| [016](adr/016-governanca-e-qualidade.md) | Governança do repositório, portões de qualidade e fluxo de release. |
| [017](adr/017-diretrizes-de-ciencia-e-inovacao.md) | Diretrizes de ciência e inovação e modo pesquisa dos agentes. |
| [018](adr/018-promocao-verificada-no-motor.md) | Requisitos de promoção verificados no motor e trava do registro. |
| [019](adr/019-desistencia-no-rotulo.md) | Desistência dentro da janela conta como desfecho positivo. |
| [020](adr/020-calibracao-unica-fora-da-amostra.md) | Calibração única, fora da amostra, sobre o preditor publicado. |
| [021](adr/021-conjuntos-conformes.md) | Conjuntos de predição conformes por classe no lugar do intervalo. |
| [022](adr/022-partida-a-frio.md) | Alunos reservados para avaliar a partida a frio. |
| [023](adr/023-limiar-de-alerta-por-taxa-alvo.md) | Limiar de alerta derivado da taxa-alvo. |
| [024](adr/024-excecoes-de-lint-e-tipos.md) | Exceções de lint e nível de verificação de tipos. |
