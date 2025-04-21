from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from apscheduler.schedulers.background import BackgroundScheduler
from xml_fetcher import fetch_and_convert_xml
from unidecode import unidecode
import os, json

app = FastAPI()

# Remove acentos e deixa tudo em minúsculas
def normalizar(texto: str) -> str:
    return unidecode(texto).lower()

# Converte campo PRICE para float com segurança
def converter_preco(valor_str):
    try:
        return float(str(valor_str).replace(",", "").replace("R$", "").strip())
    except:
        return None

@app.get("/api/data")
def get_data(request: Request):
    if not os.path.exists("data.json"):
        return {"error": "Nenhum dado disponível"}

    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        vehicles = data["ADS"]["AD"]
    except KeyError:
        return {"error": "Formato de dados inválido"}

    query_params = dict(request.query_params)
    valormax = query_params.pop("ValorMax", None)

    # Filtros padrão (MAKE, MODEL, etc)
    for chave, valor in query_params.items():
        valor_normalizado = normalizar(valor)
        vehicles = [
            v for v in vehicles
            if chave in v and valor_normalizado in normalizar(str(v[chave]))
        ]

    # Filtro por ValorMax no campo PRICE
    if valormax:
        try:
            teto = float(valormax)
            vehicles = [
                v for v in vehicles
                if "PRICE" in v and converter_preco(v["PRICE"]) is not None and converter_preco(v["PRICE"]) <= teto
            ]
        except ValueError:
            return {"error": "Formato inválido para ValorMax"}

    return JSONResponse(content=vehicles)

# Agendamento de atualização do XML
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_and_convert_xml, "cron", hour="0,12")
scheduler.start()

# Atualiza ao iniciar
fetch_and_convert_xml()
