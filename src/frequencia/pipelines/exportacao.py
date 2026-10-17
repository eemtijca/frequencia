# Exportação para o navegador: JS via m2cgen com invólucro de confiança.
"""Conversão do modelo destilado em artefato leve para o PWA.

O núcleo é transpilado por m2cgen (LightGBM para JavaScript puro, sem
dependências) e embrulhado por calibração, aquecimento, intervalo conforme,
estados de confiança e histerese, todos espelhados entre Python e JS. O
caminho ONNX fica como alternativa documentada para consumidores não web.

O tamanho em bytes e a latência de inferência são medidos e portados nos
gates de promoção: o destino é um navegador de celular modesto.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import numpy as np

from frequencia.infra import logs
from frequencia.infra.erros import ErroContrato

LIMITE_TAMANHO_BYTES = 262144  # 256 KiB para o modelo.js publicado
LIMITE_LATENCIA_MS = 5.0
AMOSTRAS_LATENCIA = 500

_ROTEIRO_PARIDADE = """
const modelo = require(caminho_modelo);
const vetores = require(caminho_dados);
const inicio = process.hrtime.bigint();
const saidas = [];
for (const item of vetores.casos) {
  saidas.push(modelo.prever(item.vetor, item.contexto));
}
const fim = process.hrtime.bigint();
const duracao_ms = Number(fim - inicio) / 1e6 / Math.max(1, saidas.length);
console.log(JSON.stringify({
  saidas: saidas.map(function (s) { return s.probabilidade; }),
  duracao_ms: duracao_ms,
  estados: saidas.map(function (s) { return s.estado_confianca; }),
  alertas: saidas.map(function (s) { return s.alerta.em_alerta; })
}));
"""


def gerar_nucleo_js(estudante) -> str:
    """Transpila o modelo destilado para o núcleo JavaScript."""
    import m2cgen

    return m2cgen.export_to_javascript(estudante)


def montar_modelo_js(
    nucleo_js: str,
    *,
    params: dict[str, Any],
) -> str:
    """Monta o modelo.js completo a partir do núcleo e dos parâmetros.

    O arquivo final expõe prever(vetor, contexto) com a mesma semântica da
    função Python prever_em_python, usada no teste de paridade.
    """
    ordem = params["contrato"]["features"]
    padroes = params["contrato"]["padroes"]
    cabecalho = (
        "// Modelo de risco de infrequência do FrequencIA.\n"
        "// Núcleo LightGBM destilado, transpilado por m2cgen; o invólucro aplica\n"
        "// calibração, aquecimento, intervalo conforme, estados de confiança e\n"
        "// histerese. Executa inteiramente no navegador, sem rede.\n"
    )
    blocos = [
        cabecalho,
        "(function (raiz) {",
        "'use strict';",
        "var PARAMS = " + json.dumps(params, ensure_ascii=False, sort_keys=True) + ";",
        "var ORDEM = " + json.dumps(ordem) + ";",
        "var PADROES = " + json.dumps(padroes) + ";",
        nucleo_js,
        "function logit(p) {",
        "  p = Math.min(1 - 1e-6, Math.max(1e-6, p));",
        "  return Math.log(p / (1 - p));",
        "}",
        _funcao_prever_js(),
        "raiz.prever = prever;",
        "raiz.ordem = ORDEM;",
        "raiz.padroes = PADROES;",
        "raiz.versao_modelo = PARAMS.identificacao.versao_modelo;",
        "raiz.limites_conhecidos = Object.keys(PARAMS.conformal.quantis);",
        "})(typeof module !== 'undefined' ? module.exports : (window.FrequenciaModelo = {}));",
    ]
    return "\n".join(blocos) + "\n"


def _funcao_prever_js() -> str:
    """Corpo da função prever em JS, espelho da lógica Python."""
    return """function prever(vetor, contexto) {
  contexto = contexto || {};
  var idx = {};
  for (var i = 0; i < ORDEM.length; i += 1) { idx[ORDEM[i]] = i; }
  var entrada = [];
  for (var j = 0; j < ORDEM.length; j += 1) {
    var valor = vetor[j];
    entrada.push(valor === null || valor === undefined || isNaN(valor) ? PADROES[j] : valor);
  }
  var bruto = score(entrada);
  var nucleo = Array.isArray(bruto) ? bruto[bruto.length - 1] : bruto;
  nucleo = Math.min(1 - 1e-6, Math.max(1e-6, nucleo));
  var cal = PARAMS.calibracao;
  var p_cal = 1 / (1 + Math.exp(-(cal.a_platt * logit(nucleo) + cal.b_platt)));
  var hist = entrada[idx.historico_dias];
  var cobertura = entrada[idx.cobertura_chamada_7d];
  var aquecimento = PARAMS.confianca.aquecimento_dias;
  var peso = Math.min(1, Math.max(0, hist / Math.max(1, aquecimento)));
  var p = peso * p_cal + (1 - peso) * cal.taxa_base;
  p = Math.min(1, Math.max(0, p));
  var serie = contexto.serie || 'geral';
  var chave = serie + '|' + faixaDe(hist);
  var largura = PARAMS.conformal.quantis.hasOwnProperty(chave) ? PARAMS.conformal.quantis[chave] : 0.5;
  var intervalo = [Math.max(0, p - largura), Math.min(1, p + largura)];
  var idade = contexto.idade_modelo_dias || 0;
  var estado = estadoDe(hist, idade, cobertura);
  var limiar = PARAMS.limiares_alerta;
  var anterior = contexto.estado_alerta || null;
  var diasAcima = anterior ? (anterior.dias_acima || 0) : 0;
  var emAlerta = anterior ? !!anterior.em_alerta : false;
  var acima = p >= limiar.entrada;
  diasAcima = acima ? diasAcima + 1 : 0;
  if (!emAlerta && diasAcima >= limiar.dias_consecutivos_entrada) { emAlerta = true; }
  else if (emAlerta && p < limiar.saida) { emAlerta = false; diasAcima = 0; }
  return {
    probabilidade: p,
    probabilidade_nucleo: nucleo,
    probabilidade_calibrada: p_cal,
    risco: p >= limiar.entrada ? 'alto' : (p >= limiar.saida ? 'medio' : 'baixo'),
    intervalo_conformal: intervalo,
    estado_confianca: estado,
    mensagem: PARAMS.mensagens[estado] || '',
    alerta: { em_alerta: emAlerta, dias_acima: diasAcima },
    chave_grupo: chave,
    versao_modelo: PARAMS.identificacao.versao_modelo
  };
}

function faixaDe(hist) {
  if (hist < 14) { return 'curto'; }
  if (hist < 30) { return 'medio'; }
  return 'longo';
}

function estadoDe(hist, idade, cobertura) {
  if (!hist || hist <= 0) { return 'sem_historico'; }
  if (idade > PARAMS.confianca.validade_modelo_dias) { return 'modelo_desatualizado'; }
  if (hist < 7) { return 'dados_insuficientes'; }
  if (hist < 14) { return 'em_observacao'; }
  if (hist >= 30 && cobertura >= 0.6) { return 'confianca_alta'; }
  return 'confianca_moderada';
}
"""


def prever_em_python(
    vetor: list[float],
    contexto: dict | None,
    nucleo: Any,
    params: dict,
) -> dict:
    """Espelho Python da função prever do modelo.js, para o teste de paridade.

    nucleo é um objeto com predict(vetor) que devolve a probabilidade do
    núcleo; em produção o teste usa o próprio modelo LightGBM.
    """
    from frequencia.features import confianca

    ordem = params["contrato"]["features"]
    padroes = params["contrato"]["padroes"]
    entrada = [(vetor[i] if vetor[i] is not None else padroes[i]) for i in range(len(ordem))]
    idx = {nome: posicao for posicao, nome in enumerate(ordem)}
    prob_nucleo = float(nucleo.predict([entrada])[0])
    prob_nucleo = min(1 - 1e-6, max(1e-6, prob_nucleo))
    cal = params["calibracao"]
    logit = float(np.log(prob_nucleo / (1 - prob_nucleo)))
    p_cal = 1.0 / (1.0 + float(np.exp(-(cal["a_platt"] * logit + cal["b_platt"]))))
    historico = float(entrada[idx["historico_dias"]])
    cobertura = float(entrada[idx["cobertura_chamada_7d"]])
    peso = confianca.peso_historico(int(historico), params["confianca"]["aquecimento_dias"])
    p = peso * p_cal + (1 - peso) * cal["taxa_base"]
    p = min(1.0, max(0.0, p))

    from frequencia.pipelines.calibracao import chave_grupo, intervalo_conformal

    serie = (contexto or {}).get("serie", "geral")
    chave = chave_grupo(serie, int(historico))
    lo, hi = intervalo_conformal(p, chave, params["conformal"]["quantis"])

    idade = (contexto or {}).get("idade_modelo_dias", 0)
    estado = confianca.estado_confianca(
        int(historico), idade_modelo_dias=int(idade), cobertura_chamada=cobertura
    )
    limiares = params["limiares_alerta"]
    anterior = (contexto or {}).get("estado_alerta")
    alerta = confianca.atualizar_alerta(
        p,
        anterior,
        limiar_entrada=limiares["entrada"],
        limiar_saida=limiares["saida"],
        dias_consecutivos=limiares["dias_consecutivos_entrada"],
    )
    risco = "alto" if p >= limiares["entrada"] else ("medio" if p >= limiares["saida"] else "baixo")
    return {
        "probabilidade": p,
        "probabilidade_nucleo": prob_nucleo,
        "probabilidade_calibrada": p_cal,
        "risco": risco,
        "intervalo_conformal": [lo, hi],
        "estado_confianca": estado,
        "alerta": alerta,
        "chave_grupo": chave,
        "versao_modelo": params["identificacao"]["versao_modelo"],
    }


def exportar_onnx(estudante, destino: Path, n_features: int) -> Path:
    """Exporta o modelo destilado para ONNX (caminho alternativo)."""
    from onnxmltools import convert_lightgbm
    from onnxmltools.convert.common.data_types import FloatTensorType

    tipo_inicial = ("input", FloatTensorType([None, n_features]))
    modelo_onnx = convert_lightgbm(estudante, initial_types=[tipo_inicial], target_opset=15)
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    from onnx import save

    save(modelo_onnx, str(destino))
    return destino


def medir_latencia_js(
    caminho_modelo: Path,
    casos: list[dict],
    *,
    executavel_node: str = "node",
) -> dict:
    """Roda o pacote JS com Node e mede latência média por previsão."""
    roteiro = _montar_roteiro(caminho_modelo, casos)
    alvo = caminho_modelo.parent / "medir_latencia.cjs"
    alvo.write_text(roteiro, encoding="utf-8")
    alvo_dados = caminho_modelo.parent / "_dados_latencia.json"
    try:
        concluido = subprocess.run(
            [executavel_node, str(alvo)],
            capture_output=True,
            text=True,
            timeout=120,
            check=True,
        )
        corpo = json.loads(concluido.stdout.strip().splitlines()[-1])
    finally:
        alvo.unlink(missing_ok=True)
        alvo_dados.unlink(missing_ok=True)
    return corpo


def _montar_roteiro(caminho_modelo: Path, casos: list[dict]) -> str:
    """Gera o roteiro CommonJS de latência e saídas para o Node."""
    alvo_dados = caminho_modelo.parent / "_dados_latencia.json"
    alvo_dados.write_text(json.dumps({"casos": casos}, ensure_ascii=False), encoding="utf-8")
    return (
        "const caminho_modelo = "
        + json.dumps(str(caminho_modelo))
        + ";\n"
        + "const caminho_dados = "
        + json.dumps(str(alvo_dados))
        + ";\n"
        + _ROTEIRO_PARIDADE
    )


def validar_artefato_js(
    caminho_modelo: Path,
    casos: list[dict],
    esperados: list[dict] | None = None,
    *,
    tolerancia: float = 1e-6,
    executavel_node: str = "node",
) -> dict:
    """Valida o modelo.js: executa, confere paridade, tamanho e latência."""
    if not caminho_modelo.is_file():
        msg = f"Arquivo de modelo ausente: {caminho_modelo}."
        raise ErroContrato(msg)
    tamanho = caminho_modelo.stat().st_size
    resultado = medir_latencia_js(caminho_modelo, casos, executavel_node=executavel_node)
    saidas = resultado["saidas"]
    estados = resultado["estados"]
    alertas = resultado["alertas"]
    divergencias = 0
    if esperados is not None:
        for obtido, alvo in zip(saidas, esperados, strict=False):
            if abs(float(obtido) - float(alvo["probabilidade"])) > tolerancia:
                divergencias += 1
        for obtido, alvo in zip(estados, esperados, strict=False):
            if obtido != alvo["estado_confianca"]:
                divergencias += 1
        for obtido, alvo in zip(alertas, esperados, strict=False):
            if bool(obtido) != bool(alvo["alerta"]["em_alerta"]):
                divergencias += 1
    veredito = {
        "executou": True,
        "tamanho_bytes": tamanho,
        "tamanho_ok": tamanho <= LIMITE_TAMANHO_BYTES,
        "latencia_ms": round(float(resultado["duracao_ms"]), 4),
        "latencia_ok": float(resultado["duracao_ms"]) <= LIMITE_LATENCIA_MS,
        "casos": len(casos),
        "divergencias": divergencias,
        "paridade_ok": esperados is None or divergencias == 0,
    }
    logs.registrar(
        "exportacao.validar_js",
        estagio="exportacao",
        tamanho=tamanho,
        latencia_ms=veredito["latencia_ms"],
        divergencias=divergencias,
    )
    return veredito


def gerar_dados_teste(
    vetores: list[list[float]],
    contextos: list[dict],
    esperados: list[dict],
) -> dict:
    """Monta o arquivo de casos sintéticos para autoverificação do app."""
    casos = [
        {"vetor": vetor, "contexto": contexto, "esperado": esperado}
        for vetor, contexto, esperado in zip(vetores, contextos, esperados, strict=True)
    ]
    return {
        "descricao": "Casos sintéticos de verificação do pacote de inferência.",
        "total": len(casos),
        "casos": casos,
    }
