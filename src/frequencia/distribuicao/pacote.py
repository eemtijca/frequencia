# Pacote de distribuição: ZIP pronto para consumo pelo PWA.
"""Montagem do pacote final com modelo, manifesto, fallback e instruções.

O pacote carrega modelo.js (núcleo transpilado e invólucro de confiança),
fallback.js (regras espelhadas), manifest.json, dados-teste.json para
autoverificação, modelo-cartao.md e LEIA-ME.md em português. Hashes de todos
os arquivos entram no manifesto: assinatura lógica do pacote.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from frequencia.infra import hash as hash_infra
from frequencia.infra import logs
from frequencia.infra.erros import ErroContrato
from frequencia.pipelines import baseline
from frequencia.pipelines.exportacao import montar_modelo_js


def montar_pacote(
    *,
    pasta_destino: Path,
    nucleo_js: str,
    params: dict,
    versao_modelo: str,
    dados_teste: dict,
    cartao_markdown: str,
    contexto_mec_json: dict | None = None,
    identificador: str = "risco-infrequencia",
) -> dict:
    """Monta a pasta do pacote e o ZIP final; devolve o manifesto gravado."""
    from frequencia.distribuicao import manifesto as manifesto_mod

    pasta = Path(pasta_destino)
    pasta.mkdir(parents=True, exist_ok=True)

    modelo_js = montar_modelo_js(nucleo_js, params=params)
    (pasta / "modelo.js").write_text(modelo_js, encoding="utf-8")

    fallback_js = gerar_fallback_js(params)
    (pasta / "fallback.js").write_text(fallback_js, encoding="utf-8")

    with (pasta / "dados-teste.json").open("w", encoding="utf-8") as saida:
        json.dump(dados_teste, saida, ensure_ascii=False, indent=2)
        saida.write("\n")

    (pasta / "modelo-cartao.md").write_text(cartao_markdown, encoding="utf-8")
    (pasta / "LEIA-ME.md").write_text(_leiame(versao_modelo, identificador), encoding="utf-8")

    if contexto_mec_json is not None:
        with (pasta / "contexto-mec.json").open("w", encoding="utf-8") as saida:
            json.dump(contexto_mec_json, saida, ensure_ascii=False, indent=2)
            saida.write("\n")

    arquivos = {
        "modelo.js": hash_infra.hash_arquivo(pasta / "modelo.js"),
        "fallback.js": hash_infra.hash_arquivo(pasta / "fallback.js"),
        "dados-teste.json": hash_infra.hash_arquivo(pasta / "dados-teste.json"),
        "modelo-cartao.md": hash_infra.hash_arquivo(pasta / "modelo-cartao.md"),
        "LEIA-ME.md": hash_infra.hash_arquivo(pasta / "LEIA-ME.md"),
    }

    tamanho_modelo = (pasta / "modelo.js").stat().st_size
    manifesto_final = _manifesto_final(params, versao_modelo, identificador, arquivos, tamanho_modelo)
    manifesto_mod.gravar(manifesto_final, pasta / "manifest.json")
    # O manifesto não carrega o próprio hash (auto-referência impossível):
    # a integridade dele vem do hash_modelo e do arquivo gravado no ZIP.

    alvo_zip = pasta.parent / f"{pasta.name}.zip"
    with zipfile.ZipFile(alvo_zip, "w", zipfile.ZIP_DEFLATED) as pacote:
        for arquivo in sorted(pasta.iterdir()):
            if arquivo.is_file():
                pacote.write(arquivo, arquivo.name)

    logs.registrar(
        "empacotamento.montar",
        estagio="empacotamento",
        pacote=str(alvo_zip),
        tamanho=alvo_zip.stat().st_size,
    )
    return {
        "pasta": str(pasta),
        "zip": str(alvo_zip),
        "manifesto": manifesto_final,
        "tamanho_zip_bytes": alvo_zip.stat().st_size,
    }


def _manifesto_final(
    params: dict,
    versao_modelo: str,
    identificador: str,
    arquivos: dict,
    tamanho_modelo: int,
) -> dict:
    """Levanta o manifesto final a partir dos params de exportação."""
    from frequencia.distribuicao import manifesto as manifesto_mod

    calibracao = dict(params["calibracao"])
    conformal = {
        "nivel": params["conformal"].get("nivel", 0.9),
        "quantis": params["conformal"]["quantis"],
        "cobertura_por_grupo": params["conformal"].get("cobertura_por_grupo", {}),
    }
    return manifesto_mod.montar(
        identificador=identificador,
        versao_modelo=versao_modelo,
        criado_em=params["identificacao"].get("criado_em", ""),
        dataset=params.get("dataset", {}),
        contrato={
            "features": params["contrato"]["features"],
            "padroes": params["contrato"]["padroes"],
            "tipos": params["contrato"].get("tipos", []),
        },
        calibracao=calibracao,
        conformal=conformal,
        metricas=params.get("metricas", {}),
        limitacoes=params.get("limitacoes", []),
        hash_modelo=arquivos["modelo.js"],
        tamanho_bytes=tamanho_modelo,
        arquivos=arquivos,
        min_app_versao=params.get("min_app_versao", "1.4.0"),
        mensagens=params.get("mensagens"),
    )


def gerar_fallback_js(params: dict) -> str:
    """Gera o fallback.js com as regras espelhadas do baseline Python."""
    import json as json_mod

    from frequencia.features.catalogo import NOMES_FEATURES

    pesos = {
        "faltas_7d": baseline.PESOS_REGRAS["faltas_7d"],
        "faltas_consecutivas": baseline.PESOS_REGRAS["faltas_consecutivas"],
        "faltas_30d": baseline.PESOS_REGRAS["faltas_30d"],
        "recencia_ultima_falta": baseline.PESOS_REGRAS["recencia_ultima_falta"],
        "media_movel_faltas_7d": baseline.PESOS_REGRAS["media_movel_faltas_7d"],
        "taxa_infrequencia_30d": baseline.PESOS_REGRAS["taxa_infrequencia_30d"],
        "saidas_30d": baseline.PESOS_REGRAS["saidas_30d"],
        "entradas_atrasadas_30d": baseline.PESOS_REGRAS["entradas_atrasadas_30d"],
        "desvio_faltas_turma_7d": baseline.PESOS_REGRAS["desvio_faltas_turma_7d"],
        "chamada_realizada_no_dia_off": baseline.PESOS_REGRAS["chamada_realizada_no_dia_off"],
        "historico_dias": baseline.PESOS_REGRAS["historico_dias"],
        "taxa_abandono_historica": baseline.PESOS_REGRAS["taxa_abandono_historica"],
    }
    vies = baseline.VIÉS_REGRAS
    ordem = list(NOMES_FEATURES)
    cabecalho = (
        "// Fallback de regras do FrequencIA: usado quando o modelo principal\n"
        "// não carrega, está corrompido ou incompatível com a versão do app.\n"
        "// Mesma interface de modelo.js: prever(vetor, contexto).\n"
    )
    return f"""{cabecalho}
(function (raiz) {{
'use strict';
var PARAMS = {json_mod.dumps(params.get("limiares_alerta", {}), sort_keys=True)};
var PESOS = {json_mod.dumps(pesos, sort_keys=True)};
var VIÉS = {vies};
var ORDEM = {json_mod.dumps(ordem)};
var PADROES = {json_mod.dumps(params.get("contrato", {}).get("padroes", []), sort_keys=True)};

function score(entrada) {{
  var idx = {{}};
  for (var i = 0; i < ORDEM.length; i += 1) {{ idx[ORDEM[i]] = i; }}
  var e = 0.0;
  e += PESOS.faltas_7d * entrada[idx.faltas_7d];
  e += PESOS.faltas_consecutivas * entrada[idx.faltas_consecutivas];
  e += PESOS.faltas_30d * entrada[idx.faltas_30d];
  e += PESOS.recencia_ultima_falta * (30 - entrada[idx.dias_desde_ultima_falta]) / 30;
  e += PESOS.media_movel_faltas_7d * entrada[idx.media_movel_faltas_7d];
  e += PESOS.taxa_infrequencia_30d * entrada[idx.taxa_infrequencia_30d];
  e += PESOS.saidas_30d * entrada[idx.saidas_30d];
  e += PESOS.entradas_atrasadas_30d * entrada[idx.entradas_atrasadas_30d];
  e += PESOS.desvio_faltas_turma_7d * entrada[idx.desvio_faltas_turma_7d];
  e += PESOS.chamada_realizada_no_dia_off * (1 - entrada[idx.chamada_realizada_no_dia]);
  e += PESOS.historico_dias * entrada[idx.historico_dias];
  e += PESOS.taxa_abandono_historica * entrada[idx.taxa_abandono_historica];
  return 1 / (1 + Math.exp(-(e + VIÉS)));
}}

function prever(vetor, contexto) {{
  contexto = contexto || {{}};
  var entrada = [];
  for (var j = 0; j < ORDEM.length; j += 1) {{
    var valor = vetor[j];
    entrada.push(valor === null || valor === undefined || isNaN(valor) ? PADROES[j] : valor);
  }}
  var idx = {{}};
  for (var k = 0; k < ORDEM.length; k += 1) {{ idx[ORDEM[k]] = k; }}
  var p = score(entrada);
  var hist = entrada[idx.historico_dias];
  var limiar = PARAMS;
  var anterior = contexto.estado_alerta || null;
  var diasAcima = anterior ? (anterior.dias_acima || 0) : 0;
  var emAlerta = anterior ? !!anterior.em_alerta : false;
  var acima = p >= (limiar.entrada || 0.65);
  diasAcima = acima ? diasAcima + 1 : 0;
  if (!emAlerta && diasAcima >= (limiar.dias_consecutivos_entrada || 2)) {{ emAlerta = true; }}
  else if (emAlerta && p < (limiar.saida || 0.45)) {{ emAlerta = false; diasAcima = 0; }}
  return {{
    probabilidade: p,
    probabilidade_nucleo: p,
    risco: p >= (limiar.entrada || 0.65) ? 'alto' : (p >= (limiar.saida || 0.45) ? 'medio' : 'baixo'),
    intervalo_conformal: [Math.max(0, p - 0.2), Math.min(1, p + 0.2)],
    estado_confianca: 'confianca_moderada',
    mensagem: 'Indicador pelo modo de segurança de regras.',
    alerta: {{ em_alerta: emAlerta, dias_acima: diasAcima }},
    fallback: true,
    versao_modelo: 'regras'
  }};
}}

raiz.prever = prever;
raiz.ordem = ORDEM;
}})(typeof module !== 'undefined' ? module.exports : (window.FrequenciaFallback = {{}}));
"""


def _leiame(versao: str, identificador: str) -> str:
    """Instruções curtas de consumo, em português, para o pacote."""
    return f"""# Pacote do modelo {identificador}

Versão do modelo: {versao}

## Como consumir no FrequenciApp

1. Leia o `manifest.json` antes de qualquer coisa: ele diz a versão mínima do
   app (`min_app_versao`), a validade e o contrato de features.
2. Carregue `modelo.js` no Service Worker cacheado pelo app; nunca durante o
   fluxo de chamada (atualização atômica, ver ADR-013).
3. Monte o vetor de features na ordem de `contrato.features`, usando os
   padrões de `contrato.padroes` para valores ausentes.
4. Chame `prever(vetor, contexto)` e respeite `estado_confianca`,
   `intervalo_conformal` e `alerta` da saída.
5. Se `modelo.js` falhar ao carregar ou o hash divergir, use `fallback.js`
   com a mesma interface.
6. Rode `dados-teste.json` na inicialização: a saída precisa bater com
   `esperado` em todos os casos, ou o pacote deve ser descartado.

## Privacidade

A inferência acontece inteiramente no navegador. Nenhum dado pessoal sai do
dispositivo: o modelo recebe apenas números derivados de frequência.

## Licença

MIT, com os dados de treinamento sintéticos documentados no manifesto.
"""


def validar_pacote(pasta: Path) -> dict:
    """Confere integridade do pacote: arquivos e hashes do manifesto."""
    pasta = Path(pasta)
    alvo = pasta / "manifest.json"
    if not alvo.is_file():
        msg = f"manifest.json ausente em {pasta}."
        raise ErroContrato(msg)
    from frequencia.distribuicao import manifesto as manifesto_mod

    manifesto = manifesto_mod.carregar(alvo)
    integridade = {}
    for relativo, esperado in manifesto.get("arquivos", {}).items():
        arquivo = pasta / relativo
        integridade[relativo] = arquivo.is_file() and hash_infra.hash_arquivo(arquivo) == esperado
    obrigatórios = ["modelo.js", "fallback.js", "manifest.json", "LEIA-ME.md"]
    ausentes = [nome for nome in obrigatórios if not (pasta / nome).is_file()]
    if ausentes:
        msg = f"Pacote incompleto: faltam {', '.join(ausentes)}."
        raise ErroContrato(msg)
    return {
        "manifesto_valido": True,
        "integridade": integridade,
        "integro": all(integridade.values()),
        "ausentes": ausentes,
    }
