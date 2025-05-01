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
📄 xml_fetcher.py
python
Copiar
Editar
import requests, xmltodict, json, os

XML_URL = os.getenv("XML_URL")
JSON_FILE = "data.json"

def fetch_and_convert_xml():
    try:
        if not XML_URL:
            raise ValueError("Variável XML_URL não definida")
        response = requests.get(XML_URL)
        data_dict = xmltodict.parse(response.content)

        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(data_dict, f, ensure_ascii=False, indent=2)

        print("[OK] Dados atualizados com sucesso.")
        return data_dict

    except Exception as e:
        print(f"[ERRO] Falha ao converter XML: {e}")
        return {}
