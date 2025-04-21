from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from apscheduler.schedulers.background import BackgroundScheduler
from xml_fetcher import fetch_and_convert_xml
from unidecode import unidecode
import os, json

app = FastAPI()


# ✅ Remove acentos e deixa tudo em minúsculas
def normalizar(texto: str) -> str:
    return unidecode(texto).lower()



# ✅ Endpoint com filtros flexíveis por query string
@app.get("/api/data")
def get_data(request: Request):
    if not os.path.exists("data.json"):
        return {"error": "Nenhum dado disponível"}

    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        vehicles = data["ADS"]["AD"]  # ajuste conforme estrutura real
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


# ✅ Agenda atualização 2x ao dia (00h e 12h)
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_and_convert_xml, "cron", hour="0,12")
scheduler.start()

# ✅ Atualiza uma vez ao subir o servidor
fetch_and_convert_xml()
