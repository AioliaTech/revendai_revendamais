from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from unidecode import unidecode
from rapidfuzz import fuzz
from apscheduler.schedulers.background import BackgroundScheduler
from xml_fetcher import fetch_and_convert_xml
import json, os

app = FastAPI()

MAPEAMENTO_CATEGORIAS = {
    "gol": "Hatch", "uno": "Hatch", "palio": "Hatch", "celta": "Hatch", "ka": "Hatch",
    "fiesta": "Hatch", "march": "Hatch", "sandero": "Hatch", "onix": "Hatch", "hb20": "Hatch",
    "i30": "Hatch", "golf": "Hatch", "polo": "Hatch", "fox": "Hatch", "up": "Hatch",
    "fit": "Hatch", "city": "Hatch", "yaris": "Hatch", "etios": "Hatch", "clio": "Hatch",
    "corsa": "Hatch", "bravo": "Hatch", "punto": "Hatch", "208": "Hatch", "argo": "Hatch",
    "mobi": "Hatch", "c3": "Hatch", "picanto": "Hatch", "astra hatch": "Hatch", "stilo": "Hatch",
    "focus hatch": "Hatch", "206": "Hatch", "c4 vtr": "Hatch", "kwid": "Hatch", "soul": "Hatch",
    "agile": "Hatch", "sonic hatch": "Hatch", "fusca": "Hatch",
    "civic": "Sedan", "corolla": "Sedan", "sentra": "Sedan", "versa": "Sedan", "jetta": "Sedan",
    "prisma": "Sedan", "voyage": "Sedan", "siena": "Sedan", "grand siena": "Sedan", "cruze": "Sedan",
    "cobalt": "Sedan", "logan": "Sedan", "fluence": "Sedan", "cerato": "Sedan", "elantra": "Sedan",
    "virtus": "Sedan", "accord": "Sedan", "altima": "Sedan", "fusion": "Sedan", "mazda3": "Sedan",
    "mazda6": "Sedan", "passat": "Sedan", "city sedan": "Sedan", "astra sedan": "Sedan", "vectra sedan": "Sedan",
    "classic": "Sedan", "cronos": "Sedan", "linea": "Sedan", "focus sedan": "Sedan", "ka sedan": "Sedan",
    "408": "Sedan", "c4 pallas": "Sedan", "polo sedan": "Sedan", "bora": "Sedan", "hb20s": "Sedan",
    "lancer": "Sedan", "camry": "Sedan", "onix plus": "Sedan",
    "duster": "SUV", "ecosport": "SUV", "hrv": "SUV", "compass": "SUV", "renegade": "SUV",
    "tracker": "SUV", "kicks": "SUV", "captur": "SUV", "creta": "SUV", "tucson": "SUV",
    "santa fe": "SUV", "sorento": "SUV", "sportage": "SUV", "outlander": "SUV", "asx": "SUV",
    "pajero": "SUV", "tr4": "SUV", "aircross": "SUV", "tiguan": "SUV", "t-cross": "SUV",
    "rav4": "SUV", "cx5": "SUV", "forester": "SUV", "wrx": "SUV", "land cruiser": "SUV",
    "cherokee": "SUV", "grand cherokee": "SUV", "xtrail": "SUV", "murano": "SUV", "cx9": "SUV",
    "edge": "SUV", "trailblazer": "SUV", "pulse": "SUV", "fastback": "SUV", "territory": "SUV",
    "bronco sport": "SUV", "2008": "SUV", "3008": "SUV", "c4 cactus": "SUV", "taos": "SUV",
    "cr-v": "SUV", "corolla cross": "SUV", "sw4": "SUV", "pajero sport": "SUV", "commander": "SUV",
    "xv": "SUV", "xc60": "SUV", "tiggo 5x": "SUV", "haval h6": "SUV", "nivus": "SUV",
    "hilux": "Caminhonete", "ranger": "Caminhonete", "s10": "Caminhonete", "l200": "Caminhonete", "triton": "Caminhonete",
    "saveiro": "Utilitário", "strada": "Utilitário", "montana": "Utilitário", "oroch": "Utilitário",
    "toro": "Caminhonete",
    "frontier": "Caminhonete", "amarok": "Caminhonete", "gladiator": "Caminhonete", "maverick": "Caminhonete", "colorado": "Caminhonete",
    "dakota": "Caminhonete", "montana (nova)": "Caminhonete", "f-250": "Caminhonete", "courier (pickup)": "Caminhonete", "hoggar": "Caminhonete",
    "ram 1500": "Caminhonete",
    "kangoo": "Utilitário", "partner": "Utilitário", "doblo": "Utilitário", "fiorino": "Utilitário", "berlingo": "Utilitário",
    "express": "Utilitário", "combo": "Utilitário", "kombi": "Utilitário", "doblo cargo": "Utilitário", "kangoo express": "Utilitário",
    "master": "Furgão", "sprinter": "Furgão", "ducato": "Furgão", "daily": "Furgão", "jumper": "Furgão",
    "boxer": "Furgão", "trafic": "Furgão", "transit": "Furgão", "vito": "Furgão", "expert (furgão)": "Furgão",
    "jumpy (furgão)": "Furgão", "scudo (furgão)": "Furgão",
    "camaro": "Coupe", "mustang": "Coupe", "tt": "Coupe", "supra": "Coupe", "370z": "Coupe",
    "rx8": "Coupe", "challenger": "Coupe", "corvette": "Coupe", "veloster": "Coupe", "cerato koup": "Coupe",
    "clk coupe": "Coupe", "a5 coupe": "Coupe", "gt86": "Coupe", "rcz": "Coupe", "brz": "Coupe",
    "z4": "Conversível", "boxster": "Conversível", "miata": "Conversível", "beetle cabriolet": "Conversível", "slk": "Conversível",
    "911 cabrio": "Conversível", "tt roadster": "Conversível", "a5 cabrio": "Conversível", "mini cabrio": "Conversível", "206 cc": "Conversível",
    "eos": "Conversível",
    "spin": "Minivan", "livina": "Minivan", "caravan": "Minivan", "touran": "Minivan", "parati": "Station Wagon",
    "quantum": "Station Wagon", "sharan": "Minivan", "zafira": "Minivan", "picasso": "Minivan", "grand c4": "Minivan",
    "meriva": "Minivan", "scenic": "Minivan", "xsara picasso": "Minivan", "carnival": "Minivan", "idea": "Minivan",
    "spacefox": "Station Wagon", "golf variant": "Station Wagon", "palio weekend": "Station Wagon", "astra sw": "Station Wagon", "206 sw": "Station Wagon",
    "a4 avant": "Station Wagon", "fielder": "Station Wagon",
    "wrangler": "Off-road", "troller": "Off-road", "defender": "Off-road", "bronco": "Off-road", "samurai": "Off-road",
    "jimny": "Off-road", "land cruiser": "Off-road", "grand vitara": "Off-road", "jimny sierra": "Off-road", "bandeirante (ate 2001)": "Off-road"
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

def filtrar_veiculos(vehicles, filtros, valormax=None):
    campos_fuzzy = ["modelo", "titulo", "cor", "opcionais"]
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
                    best_score_for_this_q_word_in_vehicle = 0.0
                    for nome_campo_fuzzy_veiculo in campos_fuzzy:
                        conteudo_original_campo_veiculo = v.get(nome_campo_fuzzy_veiculo, "")
                        if not conteudo_original_campo_veiculo:
                            continue
                        texto_normalizado_campo_veiculo = normalizar(str(conteudo_original_campo_veiculo))
                        if not texto_normalizado_campo_veiculo:
                            continue
                        current_field_match_score = 0.0
                        if palavra_q_norm in texto_normalizado_campo_veiculo:
                            current_field_match_score = 100.0
                        elif len(palavra_q_norm) >= 4:
                            score_partial = fuzz.partial_ratio(texto_normalizado_campo_veiculo, palavra_q_norm)
                            score_ratio = fuzz.ratio(texto_normalizado_campo_veiculo, palavra_q_norm)
                            achieved_score = max(score_partial, score_ratio)
                            if achieved_score >= 85:
                                current_field_match_score = achieved_score
                        if current_field_match_score > best_score_for_this_q_word_in_vehicle:
                            best_score_for_this_q_word_in_vehicle = current_field_match_score
                    if best_score_for_this_q_word_in_vehicle > 0:
                        vehicle_score_for_this_filter += best_score_for_this_q_word_in_vehicle
                        vehicle_matched_words_for_this_filter += 1
                if vehicle_matched_words_for_this_filter > 0:
                    v['_relevance_score'] += vehicle_score_for_this_filter
                    v['_matched_word_count'] += vehicle_matched_words_for_this_filter
                    veiculos_que_passaram_nesta_chave.append(v)
        else:
            termo_normalizado_para_comparacao = normalizar(valor_filtro)
            for v in vehicles_processados:
                valor_campo_veiculo = v.get(chave_filtro, "")
                if normalizar(str(valor_campo_veiculo)) == termo_normalizado_para_comparacao:
                    veiculos_que_passaram_nesta_chave.append(v)
        vehicles_processados = veiculos_que_passaram_nesta_chave
        if not vehicles_processados:
            break
    if active_fuzzy_filter_applied:
        vehicles_processados = [v for v in vehicles_processados if v['_matched_word_count'] > 0]
    if active_fuzzy_filter_applied:
        vehicles_processados.sort(
            key=lambda v: (
                v['_matched_word_count'],
                v['_relevance_score'],
                get_price_for_sort(v.get("preco"))
            ),
            reverse=True
        )
    else:
        vehicles_processados.sort(
            key=lambda v: get_price_for_sort(v.get("preco")),
            reverse=True
        )
    if valormax:
        try:
            teto = float(valormax)
            max_price_limit = teto * 1.2
            vehicles_filtrados_preco = []
            for v_dict in vehicles_processados:
                price = converter_preco(v_dict.get("preco"))
                if price is not None and price <= max_price_limit:
                    vehicles_filtrados_preco.append(v_dict)
            vehicles_processados = vehicles_filtrados_preco
        except ValueError:
            return []
    for v in vehicles_processados:
        v.pop('_relevance_score', None)
        v.pop('_matched_word_count', None)
    return vehicles_processados

def buscar_alternativas_cilindrada(vehicles, cilindrada_str, limite=5):
    try:
        cilindrada_base = int(float(cilindrada_str))
    except Exception:
        return []
    cilindrada_veiculos = []
    for v in vehicles:
        c = v.get("cilindrada")
        if c is not None:
            try:
                cilindrada_val = int(float(c))
                cilindrada_veiculos.append((cilindrada_val, v))
            except Exception:
                pass
    if not cilindrada_veiculos:
        return []
    cilindrada_veiculos.sort(key=lambda x: (abs(x[0] - cilindrada_base), x[0]))
    proximos = []
    usados = set()
    for c_val, v in cilindrada_veiculos:
        vid = v.get("id") or id(v)
        if vid not in usados:
            proximos.append(v)
            usados.add(vid)
        if len(proximos) >= limite:
            break
    return proximos

def sugerir_mais_proximo_acima(vehicles, valormax, limite=5):
    try:
        teto = float(valormax)
    except Exception:
        return []
    precos_acima = sorted(set(
        converter_preco(v.get("preco")) for v in vehicles
        if converter_preco(v.get("preco")) and converter_preco(v.get("preco")) > teto
    ))
    if not precos_acima:
        return []
    resultados = []
    for preco in precos_acima:
        matches = [v for v in vehicles if converter_preco(v.get("preco")) == preco]
        resultados.extend(matches)
        if len(resultados) >= limite:
            break
    return resultados[:limite]

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
    simples = query_params.pop("simples", None)
    filtros_originais = {
        "id": query_params.get("id"),
        "tipo": query_params.get("tipo"),
        "modelo": query_params.get("modelo"),
        "marca": query_params.get("marca"),
        "cilindrada": query_params.get("cilindrada"),
        "categoria": query_params.get("categoria"),
        "motor": query_params.get("motor"),
        "opcionais": query_params.get("opcionais"),
        "cor": query_params.get("cor"),
        "combustivel": query_params.get("combustivel"),
        "ano": query_params.get("ano"),
        "km": query_params.get("km")
    }
    filtros_ativos = {k: v for k, v in filtros_originais.items() if v}
    resultado = filtrar_veiculos(vehicles, filtros_ativos, valormax)

    # PROCESSA FOTOS SE SIMPLES=1
    if simples == "1":
        for v in resultado:
            if "fotos" in v and isinstance(v["fotos"], dict) and "url_fotos" in v["fotos"] and isinstance(v["fotos"]["url_fotos"], list):
                if v["fotos"]["url_fotos"]:
                    v["fotos"]["url_fotos"] = [v["fotos"]["url_fotos"][0]]
                else:
                    v["fotos"]["url_fotos"] = []
            elif "fotos" in v and isinstance(v["fotos"], dict):
                v["fotos"]["url_fotos"] = []

    if resultado:
        return JSONResponse(content={
            "resultados": resultado,
            "total_encontrado": len(resultado)
        })

    alternativas = []
    filtros_alternativa1 = {k: v for k, v in filtros_originais.items() if v}
    alt1 = filtrar_veiculos(vehicles, filtros_alternativa1, valormax)
    if alt1:
        alternativas = alt1
    else:
        if filtros_originais.get("modelo"):
            filtros_so_modelo = {"modelo": filtros_originais["modelo"]}
            alt2 = filtrar_veiculos(vehicles, filtros_so_modelo, valormax)
            if alt2:
                alternativas = alt2
            else:
                modelo_para_inferencia = filtros_originais.get("modelo")
                if modelo_para_inferencia:
                    categoria_inferida = inferir_categoria_por_modelo(modelo_para_inferencia)
                    if categoria_inferida:
                        filtros_categoria_inferida = {"categoria": categoria_inferida}
                        alt3 = filtrar_veiculos(vehicles, filtros_categoria_inferida, valormax)
                        if alt3:
                            alternativas = alt3
                        else:
                            alt4 = filtrar_veiculos(vehicles, filtros_categoria_inferida, valormax)
                            if alt4:
                                alternativas = alt4
    if alternativas:
        alternativas_formatadas = [
            {"titulo": v.get("titulo", ""), "cor": v.get("cor", ""), "preco": v.get("preco", "")}
            for v in alternativas[:10]
        ]
        return JSONResponse(content={
            "resultados": [],
            "total_encontrado": 0,
            "instrucao_ia": "Não encontramos veículos com os parâmetros informados dentro do valor desejado. Seguem as opções mais próximas.",
            "alternativa": {
                "resultados": alternativas_formatadas,
                "total_encontrado": len(alternativas_formatadas)
            }
        })
    if filtros_originais.get("cilindrada"):
        alternativas_cilindrada = buscar_alternativas_cilindrada(vehicles, filtros_originais["cilindrada"], limite=5)
        if valormax:
            try:
                teto = float(valormax)
                max_price_limit = teto * 1.2
                alternativas_cilindrada = [
                    v for v in alternativas_cilindrada
                    if converter_preco(v.get("preco")) is not None and converter_preco(v.get("preco")) <= max_price_limit
                ]
            except ValueError:
                alternativas_cilindrada = []
        if alternativas_cilindrada:
            alternativas_formatadas = [
                {"marca": v.get("marca", ""), "modelo": v.get("modelo", ""), "ano": v.get("ano", ""), "preco": v.get("preco", ""), "cilindrada": v.get("cilindrada", "")}
                for v in alternativas_cilindrada
            ]
            return JSONResponse(content={
                "resultados": [],
                "total_encontrado": 0,
                "instrucao_ia": f"Não encontramos motos exatamente com {filtros_originais['cilindrada']}cc, mas seguem opções com cilindradas mais próximas.",
                "alternativa": {
                    "resultados": alternativas_formatadas,
                    "total_encontrado": len(alternativas_formatadas)
                }
            })
    if valormax:
        sugestao_acima = sugerir_mais_proximo_acima(vehicles, valormax, limite=5)
        if sugestao_acima:
            alternativas_formatadas = [
                {"titulo": v.get("titulo", ""), "cor": v.get("cor", ""), "preco": v.get("preco", "")}
                for v in sugestao_acima
            ]
            return JSONResponse(content={
                "resultados": [],
                "total_encontrado": 0,
                "instrucao_ia": f"Não encontramos veículos dentro do valor desejado, mas seguem as opções mais próximas logo acima do valor.",
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
