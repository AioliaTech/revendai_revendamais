from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from unidecode import unidecode
from rapidfuzz import fuzz
from apscheduler.schedulers.background import BackgroundScheduler
from xml_fetcher import fetch_and_convert_xml
import json, os

app = FastAPI()

# ... (MAPEAMENTO_CATEGORIAS permanece como enviado)

# ... (funções auxiliares)

def filtrar_veiculos(vehicles, filtros, valormax=None, anomax=None):
    campos_fuzzy = ["modelo", "titulo"]
    vehicles_processados = list(vehicles)

    for v in vehicles_processados:
        v['_relevance_score'] = 0.0
        v['_matched_word_count'] = 0

    active_fuzzy_filter_applied = False

    for chave_filtro, valor_filtro in filtros.items():
        if not valor_filtro:
            continue

        veiculos_que_passaram_nesta_chave = []

        if chave_filtro in campos_fuzzy:
            active_fuzzy_filter_applied = True
            palavras_query_normalizadas = [normalizar(p) for p in valor_filtro.split() if p.strip()]

            if not palavras_query_normalizadas:
                vehicles_processados = []
                break

            for v in vehicles_processados:
                vehicle_score_for_this_filter = 0.0
                vehicle_matched_words_for_this_filter = 0

                for palavra_q_norm in palavras_query_normalizadas:
                    best_score = 0.0
                    for campo in campos_fuzzy:
                        conteudo = v.get(campo, "")
                        texto_normalizado = normalizar(str(conteudo))
                        if palavra_q_norm in texto_normalizado:
                            best_score = 100.0
                        elif len(palavra_q_norm) >= 4:
                            partial = fuzz.partial_ratio(texto_normalizado, palavra_q_norm)
                            ratio = fuzz.ratio(texto_normalizado, palavra_q_norm)
                            score = max(partial, ratio)
                            if score >= 75:
                                best_score = score
                    if best_score > 0:
                        vehicle_score_for_this_filter += best_score
                        vehicle_matched_words_for_this_filter += 1

                if vehicle_matched_words_for_this_filter > 0:
                    v['_relevance_score'] += vehicle_score_for_this_filter
                    v['_matched_word_count'] += vehicle_matched_words_for_this_filter
                    veiculos_que_passaram_nesta_chave.append(v)
        else:
            termo_normalizado = normalizar(valor_filtro)
            for v in vehicles_processados:
                if normalizar(str(v.get(chave_filtro, ""))) == termo_normalizado:
                    veiculos_que_passaram_nesta_chave.append(v)

        vehicles_processados = veiculos_que_passaram_nesta_chave
        if not vehicles_processados:
            break

    if active_fuzzy_filter_applied:
        vehicles_processados = [v for v in vehicles_processados if v['_matched_word_count'] > 0]

    if active_fuzzy_filter_applied:
        vehicles_processados.sort(key=lambda v: (
            v['_matched_word_count'],
            v['_relevance_score'],
            get_price_for_sort(v.get("preco"))
        ), reverse=True)
    else:
        vehicles_processados.sort(key=lambda v: get_price_for_sort(v.get("preco")), reverse=True)

    if valormax:
        try:
            max_price_limit = float(valormax) * 1.3
            vehicles_processados = [
                v for v in vehicles_processados
                if (converter_preco(v.get("preco")) or 0) <= max_price_limit
            ]
        except ValueError:
            return []

    if anomax:
        try:
            ano_limite = int(anomax) + 2
            vehicles_processados = [
                v for v in vehicles_processados
                if str(v.get("ano", "")).strip().isdigit() and int(v.get("ano")) <= ano_limite
            ]
        except ValueError:
            return []

    for v in vehicles_processados:
        v.pop('_relevance_score', None)
        v.pop('_matched_word_count', None)

    return vehicles_processados

@app.on_event("startup")
def agendar_tarefas():
    scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")
    scheduler.add_job(fetch_and_convert_xml, "cron", hour="0,12")
    scheduler.start()
    fetch_and_convert_xml()

@app.get("/api/data")
def get_data(request: Request):
    if not os.path.exists("data.json"):
        return JSONResponse(content={"error": "Nenhum dado disponível", "resultados": [], "total_encontrado": 0}, status_code=404)

    try:
        with open("data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        vehicles = data["veiculos"]
        if not isinstance(vehicles, list):
            return JSONResponse(content={"error": "Formato de dados inválido (veiculos não é uma lista)", "resultados": [], "total_encontrado": 0}, status_code=500)
    except (json.JSONDecodeError, KeyError):
        return JSONResponse(content={"error": "Erro ao ler os dados (JSON inválido ou chave faltando)", "resultados": [], "total_encontrado": 0}, status_code=500)

    query_params = dict(request.query_params)
    valormax = query_params.pop("ValorMax", None)
    anomax = query_params.pop("AnoMax", None)

    filtros_originais = {
        "id": query_params.get("id"),
        "modelo": query_params.get("modelo"),
        "marca": query_params.get("marca"),
        "categoria": query_params.get("categoria")
    }
    filtros_ativos = {k: v for k, v in filtros_originais.items() if v}

    resultado = filtrar_veiculos(vehicles, filtros_ativos, valormax, anomax)

    if resultado:
        return JSONResponse(content={
            "resultados": resultado,
            "total_encontrado": len(resultado)
        })

    alternativas = []
    filtros_alternativa1 = {k: v for k, v in filtros_originais.items() if v}
    alt1 = filtrar_veiculos(vehicles, filtros_alternativa1)
    if alt1:
        alternativas = alt1
    elif filtros_originais.get("modelo"):
        alt2 = filtrar_veiculos(vehicles, {"modelo": filtros_originais["modelo"]}, valormax)
        if alt2:
            alternativas = alt2
        else:
            categoria_inferida = inferir_categoria_por_modelo(filtros_originais.get("modelo"))
            if categoria_inferida:
                alt3 = filtrar_veiculos(vehicles, {"categoria": categoria_inferida}, valormax)
                if alt3:
                    alternativas = alt3
                else:
                    alt4 = filtrar_veiculos(vehicles, {"categoria": categoria_inferida})
                    if alt4:
                        alternativas = alt4

    if alternativas:
        alternativas_formatadas = [
            {"titulo": v.get("titulo", ""), "preco": v.get("preco", "")}
            for v in alternativas[:10]
        ]
        return JSONResponse(content={
            "resultados": [],
            "total_encontrado": 0,
            "instrucao_ia": "Não encontramos veículos com os parâmetros informados dentro do valor ou ano desejado. Seguem as opções mais próximas.",
            "alternativa": {
                "resultados": alternativas_formatadas,
                "total_encontrado": len(alternativas_formatadas)
            }
        })

    return JSONResponse(content={
        "resultados": [],
        "total_encontrado": 0,
        "instrucao_ia": "Não encontramos veículos com os parâmetros informados e também não encontramos opções próximas."
    })
