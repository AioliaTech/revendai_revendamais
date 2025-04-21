from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json, os
from xml_fetcher import fetch_and_convert_xml
from unidecode import unidecode

app = FastAPI()

def normalizar(texto: str) -> str:
    return unidecode(texto).lower()

@app.get("/api/data")
def get_data(request: Request):
    if not os.path.exists("data.json"):
        return {"error": "Nenhum dado disponível"}

    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        vehicles = data["root"]["vehicle"]
    except KeyError:
        return {"error": "Formato de dados inválido"}

    filtros = dict(request.query_params)

    for chave, valor in filtros.items():
        valor_normalizado = normalizar(valor)
        vehicles = [
            v for v in vehicles
            if chave in v and valor_normalizado in normalizar(v[chave])
        ]

    return JSONResponse(content=vehicles)
