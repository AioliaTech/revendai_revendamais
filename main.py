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


# 🟡 Filtro por valor máximo
    valor_max = request.query_params.get("VALORMAXIMO")
    if valor_max:
        try:
            valor_max = float(valor_max)

            def converter_preco(valor_str):
                try:
                    valor_str = valor_str.strip()
                    valor_str = valor_str.replace("R$", "")
                    valor_str = valor_str.replace(".", "")
                    valor_str = valor_str.replace(",", ".")
                    return float(valor_str)
                except:
                    return None

            vehicles = [
                v for v in vehicles
                if "PRICE" in v and converter_preco(v["PRICE"]) is not None and converter_preco(v["PRICE"]) <= valor_max
            ]
            vehicles.sort(
                key=lambda x: converter_preco(x["PRICE"]),
                reverse=True
            )
        except:
            return {"error": "Formato inválido para VALORMAXIMO"}

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
