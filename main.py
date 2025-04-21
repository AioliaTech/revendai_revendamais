from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from apscheduler.schedulers.background import BackgroundScheduler
import json, os
from xml_fetcher import fetch_and_convert_xml

app = FastAPI()

# Rota com filtro GET
@app.get("/api/data")
def get_data(request: Request):
    if not os.path.exists("data.json"):
        return {"error": "Nenhum dado disponível"}

    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Ajuste isso conforme a estrutura real do seu JSON
    try:
        vehicles = data["root"]["vehicle"]  # Ex: {'root': {'vehicle': [ {car1}, {car2}, ... ]}}
    except KeyError:
        return {"error": "Formato inválido de dados"}

    # Filtros via query params (ex: ?MAKE=chevrolet)
    query_params = dict(request.query_params)

    # Filtro aplicado (case-insensitive)
    for key, value in query_params.items():
        vehicles = [
            v for v in vehicles if key in v and v[key].lower() == value.lower()
        ]

    return JSONResponse(content=vehicles)
