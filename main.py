from fastapi import FastAPI
from fastapi.responses import JSONResponse
from apscheduler.schedulers.background import BackgroundScheduler
import json, os
from xml_fetcher import fetch_and_convert_xml

app = FastAPI()

@app.get("/api/data")
def get_data():
    if os.path.exists("data.json"):
        with open("data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(content=data)
    return {"error": "Nenhum dado disponível"}

scheduler = BackgroundScheduler()
scheduler.add_job(fetch_and_convert_xml, "cron", hour="0,12")
scheduler.start()

fetch_and_convert_xml()
