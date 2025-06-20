from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from unidecode import unidecode
from rapidfuzz import fuzz
from apscheduler.schedulers.background import BackgroundScheduler
from xml_fetcher import fetch_and_convert_xml # Presumo que este arquivo exista
import json, os

app = FastAPI()

MAPEAMENTO_CATEGORIAS = {
    # (Categorias omitidas para brevidade — mantenha as mesmas)
}

def inferir_categoria_por_modelo(modelo_buscado):
    modelo_norm = normalizar(modelo_buscado)
    return MAPEAMENTO_CATEGORIAS.get(modelo_norm)

def normalizar(texto: str) -> str:
    return unidecode(texto).lower().replace("-", "").replace(" ", "").strip()

def converter_preco(valor_str):
    try:
        return float(str(valor_str).replace(",", "").replace("R$", "").strip())
    except (ValueError, TypeError):
        return None

def get_price_for_sort(price_val):
    converted = converter_preco(price_val)
    return converted if converted is not None else float('-inf')

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
            palavras_query_originais = valor_filtro.split()
            palavras_query_normalizadas = [normalizar(p) for p in palavras_query_originais if p.strip()]
            palavras_query_normalizadas = [p for p in palavras_query_normalizadas if p]

            if not palavras_query_normalizadas:
                vehicles_processados = [] 
                break

            for v in vehicles_processados:
                vehicle_score_for_this_filter = 0.0
                vehicle_matched_words_for_this_filter = 0

                for palavra_q_norm in palavras_query_normalizadas:
                    if not palavra_q_norm:
                        continue

                    best_score = 0.0

                    for campo in campos_fuzzy:
                        texto = normalizar(str(v.get(campo, "")))
                        if not texto:
                            continue

                        score = 0.0
                        if palavra_q_norm in texto:
                            score = 100.0
                        elif len(palavra_q_norm) >= 4:
                            score = max(fuzz.partial_ratio(texto, palavra_q_norm), fuzz.ratio(texto, palavra_q_norm))
                            if score < 75:
                                score = 0.0

                        if score > best_score:
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
        vehicles_processados.sort(key=lambda v: (v['_matched_word_count'], v['_relevance_score'], get_price_for_sort(v.get("preco"))), reverse=True)
    else:
        vehicles_processados.sort(key=lambda v: get_price_for_sort(v.get("preco")), reverse=True)

    if valormax:
        try:
            teto = float(valormax)
            max_price = teto * 1.3
            vehicles_processados = [v for v in vehicles_processados if converter_preco(v.get("preco")) is not None and converter_preco(v.get("preco")) <= max_price]
        except ValueError:
            return []

    if anomax:
        try:
            limite = int(anomax) + 2
            vehicles_processados = [v for v in vehicles_processados if str(v.get("ano", "")).isdigit() and int(v.get("ano")) <= limite]
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
    except json.JSONDecodeError:
        return JSONResponse(content={"error": "Erro ao ler os dados (JSON inválido)", "resultados": [], "total_encontrado": 0}, status_code=500)

    try:
        vehicles = data["veiculos"]
        if not isinstance(vehicles, list):
             return JSONResponse(content={"error": "Formato de dados inválido (veiculos não é uma lista)", "resultados": [], "total_encontrado": 0}, status_code=500)
    except KeyError:
        return JSONResponse(content={"error": "Formato de dados inválido (chave 'veiculos' não encontrada)", "resultados": [], "total_encontrado": 0}, status_code=500)

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
        return JSONResponse(content={"resultados": resultado, "total_encontrado": len(resultado)})

    alternativas = []
    alt1 = filtrar_veiculos(vehicles, filtros_originais)
    if alt1:
        alternativas = alt1
    else:
        if filtros_originais.get("modelo"):
            alt2 = filtrar_veiculos(vehicles, {"modelo": filtros_originais["modelo"]}, valormax)
            if alt2:
                alternativas = alt2
            else:
                categoria = inferir_categoria_por_modelo(filtros_originais.get("modelo"))
                if categoria:
                    alt3 = filtrar_veiculos(vehicles, {"categoria": categoria}, valormax)
                    if alt3:
                        alternativas = alt3
                    else:
                        alt4 = filtrar_veiculos(vehicles, {"categoria": categoria})
                        if alt4:
                            alternativas = alt4

    if alternativas:
        alternativas_formatadas = [{"titulo": v.get("titulo", ""), "preco": v.get("preco", "")} for v in alternativas[:10]]
        return JSONResponse(content={
            "resultados": [],
            "total_encontrado": 0,
            "instrucao_ia": "Não encontramos veículos com os parâmetros informados dentro do valor desejado. Seguem as opções mais próximas.",
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
