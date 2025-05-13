from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from unidecode import unidecode
from rapidfuzz import fuzz
from apscheduler.schedulers.background import BackgroundScheduler
from xml_fetcher import fetch_and_convert_xml
import json, os

app = FastAPI()

def normalizar(texto: str) -> str:
    return unidecode(texto).lower().replace("-", "").replace(" ", "")

def converter_preco(valor_str):
    try:
        return float(str(valor_str).replace(",", "").replace("R$", "").strip())
    except:
        return None

@app.on_event("startup")
def agendar_tarefas():
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_and_convert_xml, "cron", hour="0,12")
    scheduler.start()
    fetch_and_convert_xml()

@app.get("/api/data")
def get_data(request: Request):
    if not os.path.exists("data.json"):
        return {"error": "Nenhum dado disponível"}

    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        vehicles = data["veiculos"]
    except:
        return {"error": "Formato de dados inválido"}

    query_params = dict(request.query_params)
    valormax = query_params.pop("ValorMax", None)
    order = query_params.pop("order", "desc").lower()

    # 🔍 Busca com similaridade (mais permissiva)
    for chave, valor in query_params.items():
        if not valor.strip():
            continue

        valor_normalizado = normalizar(valor)
        resultado_aproximado = []

        for v in vehicles:
            if chave in v and v[chave]:
                texto_alvo = normalizar(str(v[chave]))
                score = fuzz.partial_ratio(valor_normalizado, texto_alvo)
                if score >= 80:
                    resultado_aproximado.append(v)

        if resultado_aproximado:
            vehicles = resultado_aproximado

    # 💰 Filtro por preço máximo
    if valormax:
        try:
            teto = float(valormax)
            vehicles = [
                v for v in vehicles
                if "preco" in v and converter_preco(v["preco"]) is not None and converter_preco(v["preco"]) <= teto
            ]
        except:
            return {"error": "Formato inválido para ValorMax"}

    # 🔽 Ordenação por preço crescente ou decrescente
    reverse = order != "asc"
    vehicles.sort(
        key=lambda v: converter_preco(v["preco"]) if "preco" in v else 0,
        reverse=reverse
    )

    return JSONResponse(content=vehicles)

@app.get("/api/status")
def get_status():
    if not os.path.exists("data.json"):
        return {"status": "Nenhum dado ainda foi gerado."}

    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    timestamp = data.get("_updated_at", "Desconhecido")
    return {"ultima_atualizacao": timestamp}

@app.get("/api/info")
def get_info():
    if not os.path.exists("data.json"):
        return {"status": "Nenhum dado disponível"}

    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        vehicles = data["veiculos"]
    except:
        return {"error": "Formato de dados inválido"}

    total = len(vehicles)
    marcas = set()
    anos = []
    precos = []

    for v in vehicles:
        if "marca" in v:
            marcas.add(v["marca"])
        if "ano" in v:
            try:
                anos.append(int(v["ano"]))
            except:
                pass
        if "preco" in v:
            try:
                preco = converter_preco(v["preco"])
                if preco is not None:
                    precos.append(preco)
            except:
                pass

    return {
        "total_veiculos": total,
        "marcas_diferentes": len(marcas),
        "ano_mais_antigo": min(anos) if anos else None,
        "ano_mais_novo": max(anos) if anos else None,
        "preco_minimo": min(precos) if precos else None,
        "preco_maximo": max(precos) if precos else None
    }
