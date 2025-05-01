from fastapi import FastAPI
from fastapi.responses import JSONResponse
import json, os
from unidecode import unidecode
from apscheduler.schedulers.background import BackgroundScheduler
from xml_fetcher import fetch_and_convert_xml

app = FastAPI()

def normalizar(texto: str) -> str:
    return unidecode(texto).lower()

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
def get_data():
    if not os.path.exists("data.json"):
        return {"error": "Nenhum dado disponível"}

    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        return JSONResponse(content=data["ADS"]["AD"])
    except:
        return {"error": "Formato de dados inválido"}
