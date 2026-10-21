# Orquestração do ciclo completo: treino, ensemble, calibração, destilação.
"""Execução idempotente do experimento de risco de infrequência.

Cada etapa grava seu resultado dentro do experimento e registra conclusão no
estado interno; execuções repetidas pulam etapas concluídas (ou as refazem
com --forca e justificativa auditada). O ciclo termina com pacote pronto,
avaliação com gates e registro do modelo no estado experimental.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from frequencia.infra import caminhos, logs
from frequencia.infra import estado as estado_infra
from frequencia.infra import hash as hash_infra
from frequencia.infra.erros import ErroEstado
from frequencia.pipelines import (
    avaliacao as avaliacao_mod,
)
from frequencia.pipelines import (
    baseline,
)
from frequencia.pipelines import (
    calibracao as calibracao_mod,
)
from frequencia.pipelines import (
    dataset as dataset_mod,
)
from frequencia.pipelines import (
    ensemble as ensemble_mod,
)
from frequencia.pipelines import (
    exportacao as exportacao_mod,
)
from frequencia.pipelines import (
    treino as treino_mod,
)
from frequencia.pipelines.treino import ConfigTreino

ETAPAS = ("treino", "ensemble", "calibracao", "destilacao", "avaliacao", "exportacao", "empacotamento")


@dataclass
class ConfigExperimento:
    """Configuração declarativa do experimento completo."""

    pasta_dataset: Path
    identificador: str = ""
    semente: int = 20261018
    tentativas_optuna: int = 0
    dobras_ensemble: int = 3
    versao_modelo: str = ""
    min_app_versao: str = "1.4.0"
    detalhes: dict = field(default_factory=dict)


def executar(
    config: ConfigExperimento,
    *,
    forcar: bool = False,
    justificativa: str = "",
    detalhado: bool = False,
) -> dict:
    """Executa o ciclo completo com idempotência por etapa."""
    identificador = config.identificador or f"exp-{hash_infra.hash_pasta(config.pasta_dataset)[:10]}"
    pasta = caminhos.caminho("artefatos") / "experimentos" / identificador
    pasta.mkdir(parents=True, exist_ok=True)
    caminho_estado = pasta / "estado.json"
    estado = _ler_estado(caminho_estado)
    estado["identificador"] = identificador
    estado["config"] = {
        "pasta_dataset": str(config.pasta_dataset),
        "semente": config.semente,
        "tentativas_optuna": config.tentativas_optuna,
        "dobras_ensemble": config.dobras_ensemble,
        "versao_modelo": config.versao_modelo,
        "min_app_versao": config.min_app_versao,
    }
    chave = _chave_configuracao(estado["config"], config.pasta_dataset)
    if forcar:
        estado["etapas"] = {}
        estado_infra.registrar_auditoria(
            "experimento.forcar",
            alvo=identificador,
            detalhe=justificativa or "sem justificativa informada",
        )
    elif estado.get("etapas") and estado.get("chave_configuracao") != chave:
        # Reaproveitar etapas de outra configuração gravaria artefatos que
        # não correspondem à configuração registrada no estado.
        estado["etapas"] = {}
        estado_infra.registrar_auditoria(
            "experimento.invalidar",
            alvo=identificador,
            detalhe="configuração ou dataset diferente da execução anterior",
        )
    estado["chave_configuracao"] = chave
    execucao = _Execucao(estado, caminho_estado)

    pacote = dataset_mod.carregar_dataset(config.pasta_dataset)
    dados = pacote["dataset"]

    resumo: dict[str, Any] = {"identificador": identificador, "pasta": str(pasta)}

    resultado_treino = execucao.rodar(
        "treino",
        lambda: _executar_treino(config, pasta, dados, detalhado),
    )
    resumo["treino"] = _resumir_treino(resultado_treino)

    resultado_ensemble = execucao.rodar(
        "ensemble",
        lambda: _executar_ensemble(config, pasta, dados, detalhado),
    )
    resumo["ensemble"] = _resumir_ensemble(resultado_ensemble)

    resultado_calibracao = execucao.rodar(
        "calibracao",
        lambda: _executar_calibracao(config, pasta, detalhado),
    )
    resumo["calibracao"] = resultado_calibracao["resumo"]

    resultado_destilacao = execucao.rodar(
        "destilacao",
        lambda: _executar_destilacao(config, pasta, dados, resultado_calibracao, detalhado),
    )
    resumo["destilacao"] = resultado_destilacao

    resultado_avaliacao = execucao.rodar(
        "avaliacao",
        lambda: _executar_avaliacao(config, pasta, dados, resultado_calibracao, detalhado),
    )
    resumo["avaliacao"] = resultado_avaliacao["resumo"]

    resultado_exportacao = execucao.rodar(
        "exportacao",
        lambda: _executar_exportacao(
            config, pasta, dados, resultado_calibracao, resultado_avaliacao, detalhado
        ),
    )
    resumo["exportacao"] = resultado_exportacao["resumo"]

    resultado_pacote = execucao.rodar(
        "empacotamento",
        lambda: _executar_empacotamento(
            config, pasta, resultado_exportacao, resultado_calibracao, resultado_avaliacao, pacote, detalhado
        ),
    )
    resumo["empacotamento"] = resultado_pacote["resumo"]

    # Gates finais: avaliação combinada com tamanho e latência medidos.
    veredito = avaliacao_mod.validar_gates(
        resultado_avaliacao["resumo"],
        tamanho_pacote_bytes=resultado_exportacao["resumo"]["tamanho_bytes"],
        latencia_ms=resultado_exportacao["resumo"]["latencia_ms"],
    )
    resumo["gates"] = veredito
    with (pasta / "gates.json").open("w", encoding="utf-8") as saida:
        json.dump(veredito, saida, ensure_ascii=False, indent=2, sort_keys=True)
        saida.write("\n")
    # A promoção a candidato lê o veredito do registro (ADR-018).
    estado_infra.registrar_gates("risco-infrequencia", resultado_pacote["resumo"]["versao_modelo"], veredito)

    logs.registrar(
        "experimentos.ciclo",
        estagio="experimentos",
        identificador=identificador,
        etapas=list(estado.get("etapas", {})),
        detalhado=detalhado,
    )
    return resumo


def _executar_treino(config: ConfigExperimento, pasta: Path, dados: pl.DataFrame, detalhado: bool):
    resultado = treino_mod.treinar(
        ConfigTreino(
            pasta_dataset=config.pasta_dataset,
            semente=config.semente,
            tentativas_optuna=config.tentativas_optuna,
            identificador=pasta.name,
            pasta_destino=pasta,
        ),
        detalhado=detalhado,
    )
    return {
        "metricas": resultado.metricas,
        "parametros": resultado.parametros,
        "run_mlflow": resultado.run_mlflow,
        "duracao_segundos": resultado.duracao_segundos,
        "tamanho_modelo_bytes": resultado.tamanho_modelo_bytes,
    }


def _executar_ensemble(config: ConfigExperimento, pasta: Path, dados: pl.DataFrame, detalhado: bool):
    resultado = ensemble_mod.montar(
        pasta, dados, semente=config.semente, dobras=config.dobras_ensemble, detalhado=detalhado
    )
    return {
        "membros": resultado.membros,
        "pesos": resultado.pesos,
        "metricas": resultado.metricas,
        "discordancia_media": resultado.discordancia_media,
        "duracao_segundos": resultado.duracao_segundos,
    }


def _executar_calibracao(config: ConfigExperimento, pasta: Path, detalhado: bool) -> dict:
    arquivo_oof = pasta / "ensemble" / "oof.npz"
    if not arquivo_oof.is_file():
        msg = "OOF do ensemble ausente: execute a etapa de ensemble antes."
        raise ErroEstado(msg)
    oof = np.load(file=arquivo_oof, allow_pickle=False)
    ajuste = calibracao_mod.ajustar(
        oof["blend"],
        oof["rotulos"],
        [str(valor) for valor in oof["series"].tolist()],
        oof["historico"].astype(float),
    )
    curva = calibracao_mod.curva_aprendizado(oof["blend"], oof["rotulos"], oof["historico"].astype(float))
    corpo = {
        "resumo": {
            **ajuste.para_dict(),
            "curva_aprendizado": curva,
        },
        "ajuste": ajuste.para_dict(),
    }
    with (pasta / "calibracao.json").open("w", encoding="utf-8") as saida:
        json.dump(corpo["resumo"], saida, ensure_ascii=False, indent=2, sort_keys=True)
        saida.write("\n")
    return corpo


def _executar_destilacao(
    config: ConfigExperimento,
    pasta: Path,
    dados: pl.DataFrame,
    resultado_calibracao: dict,
    detalhado: bool,
) -> dict:
    oof = np.load(file=pasta / "ensemble" / "oof.npz", allow_pickle=False)
    calibradas = calibracao_mod.aplicar_platt(
        oof["blend"],
        resultado_calibracao["ajuste"]["a_platt"],
        resultado_calibracao["ajuste"]["b_platt"],
    )
    ajuste_treino = (
        dados.filter(pl.col("divisao").is_in(["treino", "validacao"]))
        .sort(["dia", "aluno_id"])
        .with_row_index("linha")
    )
    from frequencia.features.catalogo import NOMES_FEATURES

    x_tudo = ajuste_treino.select(NOMES_FEATURES).to_numpy()
    linhas_oof = oof["linhas_oof"].astype(int)
    x = x_tudo[linhas_oof]
    if len(x) != len(calibradas):
        msg = (
            "Divergência de linhas entre OOF e dataset na destilação. "
            "Reconstrua o dataset com o mesmo passo do experimento."
        )
        raise ErroEstado(msg)
    corpo = treino_mod.destilar(pasta, alvos=calibradas, x=x, semente=config.semente)
    logs.registrar(
        "experimentos.destilar",
        estagio="destilacao",
        tamanho=corpo["tamanho_bytes"],
        detalhado=detalhado,
    )
    return corpo


def _executar_avaliacao(
    config: ConfigExperimento,
    pasta: Path,
    dados: pl.DataFrame,
    resultado_calibracao: dict,
    detalhado: bool,
) -> dict:
    teste = dados.filter(pl.col("divisao") == "teste")
    from frequencia.features.catalogo import NOMES_FEATURES

    x_teste = teste.select(NOMES_FEATURES).to_numpy()
    y_teste = teste["rotulo"].cast(pl.Int32).to_numpy()
    estudante = treino_mod.carregar_estudante(pasta)
    bruto = estudante.predict_proba(x_teste)[:, 1]
    ajuste = resultado_calibracao["ajuste"]
    calibradas = calibracao_mod.aplicar_platt(bruto, ajuste["a_platt"], ajuste["b_platt"])
    baseline_prob = baseline.pontuar(x_teste)

    ajuste_dict = resultado_calibracao["resumo"]
    relatorio = avaliacao_mod.avaliar(
        calibradas,
        y_teste,
        series=teste["serie_id"].to_list(),
        turmas=teste["turma_do_dia"].to_list(),
        historico=teste["historico_dias"].to_numpy(),
        dias=teste["dia"].to_list(),
        probabilidades_baseline=baseline_prob,
        ajuste_calibracao=ajuste_dict,
    )
    relatorio["curva_aprendizado"] = ajuste_dict.get("curva_aprendizado", [])
    corpo = {"resumo": relatorio, "relatorio": relatorio}
    with (pasta / "avaliacao.json").open("w", encoding="utf-8") as saida:
        json.dump(relatorio, saida, ensure_ascii=False, indent=2, sort_keys=True)
        saida.write("\n")
    avaliacao_mod.gerar_relatorio_markdown(relatorio, pasta / "relatorio-avaliacao.md")
    logs.registrar(
        "avaliacao.modelo",
        estagio="avaliacao",
        metricas=relatorio["metricas"],
        detalhado=detalhado,
    )
    return corpo


def _executar_exportacao(
    config: ConfigExperimento,
    pasta: Path,
    dados: pl.DataFrame,
    resultado_calibracao: dict,
    resultado_avaliacao: dict,
    detalhado: bool,
) -> dict:
    from frequencia.features.catalogo import CATALOGO, NOMES_FEATURES

    estudante = treino_mod.carregar_estudante(pasta)
    nucleo_js = exportacao_mod.gerar_nucleo_js(estudante)
    versao_modelo = config.versao_modelo or _versao_por_data()
    ajuste = resultado_calibracao["resumo"]

    pasta_export = pasta / "exportacoes"
    pasta_export.mkdir(parents=True, exist_ok=True)

    params = {
        "identificacao": {
            "identificador": "risco-infrequencia",
            "versao_modelo": versao_modelo,
            "criado_em": time.strftime("%Y-%m-%dT%H:%M:%S"),
        },
        "contrato": {
            "features": list(NOMES_FEATURES),
            "padroes": [float(spec.padrao) for spec in CATALOGO],
            "tipos": [spec.tipo for spec in CATALOGO],
        },
        "calibracao": {
            "a_platt": ajuste["a_platt"],
            "b_platt": ajuste["b_platt"],
            "taxa_base": ajuste["taxa_base"],
        },
        "conformal": {
            "nivel": ajuste["nivel_conformal"],
            "quantis": ajuste["quantis_conformal"],
            "cobertura_por_grupo": ajuste.get("cobertura_por_grupo", {}),
        },
        "limiares_alerta": {
            "entrada": 0.65,
            "saida": 0.45,
            "dias_consecutivos_entrada": 2,
        },
        "confianca": {
            "aquecimento_dias": 30,
            "validade_modelo_dias": 180,
        },
        "mensagens": None,
        "dataset": {
            "identificador": pasta.name,
            "linhas": int(dados.height),
            "taxa_rotulo": float(dados.select(pl.col("rotulo").cast(pl.Float64).mean()).item(0, 0) or 0),
        },
        "metricas": resultado_avaliacao["resumo"]["metricas"],
        "limitacoes": [
            "Treinado apenas com dados sintéticos: validar com dados autorizados antes de produção.",
            "Indicador de apoio à coordenação: nunca decisão automática, sempre sujeito a revisão humana.",
            "Confiabilidade reduzida quando a escola desliga saídas antecipadas ou a chamada por aula.",
            "Perfis de dados não declarados no manifesto devem usar o fallback de regras.",
        ],
        "min_app_versao": config.min_app_versao,
    }
    from frequencia.features import confianca as confianca_mod

    params["mensagens"] = dict(confianca_mod.VOCABULARIO_MENSAGENS)

    # Casos de teste sintéticos para paridade e autoverificação do app.
    teste = dados.filter(pl.col("divisao") == "teste")
    amostra = teste.sample(n=min(24, teste.height), seed=config.semente)
    x_amostra = amostra.select(NOMES_FEATURES).to_numpy()
    contextos = [
        {
            "serie": linha["serie_id"],
            "idade_modelo_dias": 12,
            "estado_alerta": None,
        }
        for linha in amostra.iter_rows(named=True)
    ]
    esperados = [
        exportacao_mod.prever_em_python(
            x_amostra[indice].tolist(), contextos[indice], _NucleoEstudante(estudante), params
        )
        for indice in range(len(x_amostra))
    ]
    dados_teste = exportacao_mod.gerar_dados_teste(
        [vetor.tolist() for vetor in x_amostra], contextos, esperados
    )

    modelo_js = exportacao_mod.montar_modelo_js(nucleo_js, params=params)
    alvo_js = pasta_export / "modelo.js"
    alvo_js.write_text(modelo_js, encoding="utf-8")

    casos = [
        {"vetor": vetor.tolist(), "contexto": contexto}
        for vetor, contexto in zip(x_amostra, contextos, strict=True)
    ]
    validacao = exportacao_mod.validar_artefato_js(
        alvo_js, casos, esperados=[_resumir_esperado(e) for e in esperados]
    )

    onnx_info = {}
    try:
        alvo_onnx = exportacao_mod.exportar_onnx(estudante, pasta_export / "modelo.onnx", len(NOMES_FEATURES))
        onnx_info = {"arquivo": str(alvo_onnx), "tamanho_bytes": alvo_onnx.stat().st_size}
    except Exception as exc:
        onnx_info = {"erro": str(exc)[:200]}

    corpo = {
        "resumo": {
            "versao_modelo": versao_modelo,
            "modelo_js": str(alvo_js),
            "tamanho_bytes": validacao["tamanho_bytes"],
            "latencia_ms": validacao["latencia_ms"],
            "paridade_ok": validacao["paridade_ok"],
            "tamanho_ok": validacao["tamanho_ok"],
            "latencia_ok": validacao["latencia_ok"],
            "onnx": onnx_info,
            "casos_teste": len(casos),
        },
        "params": params,
        "nucleo_js": nucleo_js,
        "dados_teste": dados_teste,
        "validacao": validacao,
    }
    with (pasta_export / "validacao.json").open("w", encoding="utf-8") as saida:
        json.dump(validacao, saida, ensure_ascii=False, indent=2, sort_keys=True)
        saida.write("\n")
    with (pasta_export / "dados-teste.json").open("w", encoding="utf-8") as saida:
        json.dump(dados_teste, saida, ensure_ascii=False, indent=2)
        saida.write("\n")
    logs.registrar(
        "exportacao.exportar",
        estagio="exportacao",
        versao=versao_modelo,
        tamanho=validacao["tamanho_bytes"],
        latencia_ms=validacao["latencia_ms"],
        detalhado=detalhado,
    )
    return corpo


def _executar_empacotamento(
    config: ConfigExperimento,
    pasta: Path,
    resultado_exportacao: dict,
    resultado_calibracao: dict,
    resultado_avaliacao: dict,
    pacote_dataset: dict,
    detalhado: bool,
) -> dict:
    from frequencia.distribuicao import pacote as pacote_mod

    params = resultado_exportacao["params"]
    versao = resultado_exportacao["resumo"]["versao_modelo"]
    pasta_pacotes = caminhos.caminho("pacotes")
    destino = pasta_pacotes / f"risco-infrequencia-{versao}"
    if destino.exists():
        destino = pasta_pacotes / f"risco-infrequencia-{versao}-{pasta.name}"
    cartao = _cartao_modelo(params, resultado_avaliacao["resumo"], pacote_dataset)
    contexto_mec = _contexto_mec_para_pacote(config)
    nucleo_js = resultado_exportacao.get("nucleo_js") or _ler_nucleo(
        resultado_exportacao["resumo"]["modelo_js"]
    )
    resultado = pacote_mod.montar_pacote(
        pasta_destino=destino,
        nucleo_js=nucleo_js,
        params=params,
        versao_modelo=versao,
        dados_teste=resultado_exportacao["dados_teste"],
        cartao_markdown=cartao,
        contexto_mec_json=contexto_mec,
        identificador="risco-infrequencia",
    )
    with (pasta / "empacotamento.json").open("w", encoding="utf-8") as saida:
        json.dump(
            {
                "pacote": resultado["zip"],
                "pasta": resultado["pasta"],
                "tamanho_zip_bytes": resultado["tamanho_zip_bytes"],
                "versao_modelo": resultado["manifesto"]["versao_modelo"],
            },
            saida,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        saida.write("\n")

    versao_modelo = resultado["manifesto"]["versao_modelo"]
    estado_infra.registrar_modelo(
        "risco-infrequencia",
        versao_modelo,
        runtime_alvo="js-m2cgen",
        hash_artefato=resultado["manifesto"]["hash_modelo"],
        tamanho_bytes=resultado["manifesto"]["tamanho_bytes"],
        dataset=params.get("dataset", {}),
        metricas=params.get("metricas", {}),
        limitacoes=params.get("limitacoes", []),
        referencia_artefato=resultado["zip"],
        validade_ate=resultado["manifesto"]["validade_ate"],
        situacao="experimental",
    )
    return {
        "resumo": {
            "pacote": resultado["zip"],
            "pasta": resultado["pasta"],
            "tamanho_zip_bytes": resultado["tamanho_zip_bytes"],
            "versao_modelo": versao_modelo,
        },
        "pacote": resultado,
    }


def _contexto_mec_para_pacote(config: ConfigExperimento) -> dict | None:
    """Contexto MEC agregado por série, para uso offline no app."""
    try:
        pacote = dataset_mod.carregar_dataset(config.pasta_dataset)
        origem = Path(pacote["meta"]["config"]["pasta_dados"])
        from frequencia.dados import sintetico

        tabelas = sintetico.carregar_pacote(origem)["tabelas"]
        return {
            "series": tabelas["contexto_mec"].to_dicts(),
            "nota": "Valores sintéticos de referência; substituir por agregados reais do MEC.",
        }
    except Exception:
        return None


def _cartao_modelo(params: dict, relatorio: dict, pacote_dataset: dict) -> str:
    """Cartão do modelo em Markdown, para publicação e governança."""
    metricas = relatorio.get("metricas", {})
    linhas = [
        "# Cartão do modelo: risco de infrequência",
        "",
        "## Identificação",
        "",
        "- Identificador: risco-infrequencia",
        f"- Versão: {params['identificacao']['versao_modelo']}",
        "- Runtime alvo: js-m2cgen (navegador, offline)",
        f"- Criado em: {params['identificacao']['criado_em']}",
        "",
        "## Finalidade e público",
        "",
        "Estima a probabilidade de um estudante acumular pelo menos duas faltas nos",
        "próximos sete dias letivos, ou de desistir nesse período, para apoiar a",
        "priorização da coordenação no painel e no relatório por aluno. É",
        "sugestão de apoio, nunca decisão:",
        "toda ação pedagógica passa por revisão humana.",
        "",
        "## Dados de treinamento",
        "",
        "- Origem: dados sintéticos, determinísticos, sem dados pessoais reais",
        f"- Linhas: {params.get('dataset', {}).get('linhas', 'n/d')}",
        f"- Taxa do rótulo: {params.get('dataset', {}).get('taxa_rotulo', 'n/d')}",
        "",
        "## Métricas de validação",
        "",
        "| Métrica | Valor |",
        "| --- | --- |",
    ]
    for chave, valor in metricas.items():
        linhas.append(f"| {chave} | {valor} |")
    linhas.extend(
        [
            "",
            "## Calibração e confiança",
            "",
            f"- Platt regularizado: a={params['calibracao']['a_platt']}, b={params['calibracao']['b_platt']}",
            f"- Taxa base de aquecimento: {params['calibracao']['taxa_base']}",
            f"- Conformal Mondrian por série e faixa de histórico, nível {params['conformal']['nivel']}",
            "- Estados de confiança, aquecimento de 30 dias e histerese de alerta embutidos no pacote",
            "",
            "## Limitações",
            "",
        ]
    )
    for limite in params.get("limitacoes", []):
        linhas.append(f"- {limite}")
    linhas.extend(
        [
            "",
            "## Uso responsável e LGPD",
            "",
            "A inferência roda no navegador e nenhum dado pessoal sai do dispositivo.",
            "O indicador não rotula pessoas: orienta o olhar da coordenação. Descartes e",
            "feedback alimentam a recalibração sem registrar entradas individuais.",
            "",
            "## Retreinamento",
            "",
            "Recomendação: reavaliar a cada trimestre ou quando o drift de features",
            "exceder 0,2 de PSI, e recalibrar em diante. O procedimento completo está",
            "em docs/retreinamento-e-recalibracao.md.",
            "",
        ]
    )
    return "\n".join(linhas) + "\n"


class _NucleoEstudante:
    """Adaptador do estudante para o paralelo com o JS."""

    def __init__(self, estudante) -> None:
        self._estudante = estudante

    def predict(self, entrada: list[list[float]]) -> list[float]:
        return self._estudante.predict_proba(entrada)[:, 1].tolist()


def _resumir_esperado(esperado: dict) -> dict:
    return {
        "probabilidade": esperado["probabilidade"],
        "estado_confianca": esperado["estado_confianca"],
        "alerta": esperado["alerta"],
    }


def _ler_nucleo(caminho_modelo_js: str) -> str:
    """Recupera o núcleo a partir do modelo.js gravado na exportação."""
    texto = Path(caminho_modelo_js).read_text(encoding="utf-8")
    inicio = texto.index("function score(")
    fim = texto.index("function logit(")
    return texto[inicio:fim].rstrip() + "\n"


def _versao_por_data() -> str:
    return time.strftime("%Y.%m.%d-1")


def _ler_estado(caminho: Path) -> dict:
    if caminho.is_file():
        return json.loads(caminho.read_text(encoding="utf-8"))
    return {"identificador": "", "etapas": {}}


def _gravar_estado(caminho: Path, estado: dict) -> None:
    with caminho.open("w", encoding="utf-8") as saida:
        json.dump(estado, saida, ensure_ascii=False, indent=2, sort_keys=True)
        saida.write("\n")


def _chave_configuracao(config: dict, pasta_dataset: Path) -> str:
    """Impressão digital da configuração e do conteúdo do dataset."""
    import hashlib

    alvo = Path(pasta_dataset) / "dataset.parquet"
    conteudo = hash_infra.hash_arquivo(alvo) if alvo.is_file() else ""
    corpo = json.dumps({"config": config, "dataset": conteudo}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(corpo.encode("utf-8")).hexdigest()


class _Execucao:
    """Controla a idempotência das etapas em ordem.

    Uma etapa concluída é reaproveitada só enquanto nenhuma anterior foi
    refeita: a partir da primeira etapa executada, todas as seguintes rodam
    de novo, porque dependem dos artefatos recém-gravados.
    """

    def __init__(self, estado: dict, caminho: Path) -> None:
        self._estado = estado
        self._caminho = caminho
        self._refazer = False

    def rodar(self, nome: str, acao):
        info = self._estado.get("etapas", {}).get(nome)
        concluida = bool(info) and info.get("estado") == "concluida"
        if concluida and not self._refazer:
            return info.get("resultado")
        resultado = acao()
        _concluir_etapa(self._estado, self._caminho, nome, _serializavel(resultado))
        self._refazer = True
        return resultado


def _serializavel(valor: Any) -> Any:
    """Converte o resultado da etapa em estrutura gravável em JSON."""
    import dataclasses

    if dataclasses.is_dataclass(valor) and not isinstance(valor, type):
        return dataclasses.asdict(valor)
    if isinstance(valor, dict):
        return {chave: _serializavel(corpo) for chave, corpo in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_serializavel(item) for item in valor]
    if isinstance(valor, (str, int, float, bool)) or valor is None:
        return valor
    return str(valor)


def _concluir_etapa(estado: dict, caminho: Path, nome: str, resultado) -> None:
    estado.setdefault("etapas", {})[nome] = {
        "estado": "concluida",
        "momento": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "resultado": resultado,
    }
    _gravar_estado(caminho, estado)


def _resumir_treino(resultado: dict) -> dict:
    return {
        "metricas": resultado.get("metricas", {}),
        "run_mlflow": resultado.get("run_mlflow", ""),
        "tamanho_modelo_bytes": resultado.get("tamanho_modelo_bytes", 0),
    }


def _resumir_ensemble(resultado: dict) -> dict:
    return {
        "membros": resultado.get("membros", []),
        "pesos": resultado.get("pesos", {}),
        "metricas": resultado.get("metricas", {}),
        "discordancia_media": resultado.get("discordancia_media", 0.0),
    }
