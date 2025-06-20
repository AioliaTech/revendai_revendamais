from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from unidecode import unidecode
from rapidfuzz import fuzz
from apscheduler.schedulers.background import BackgroundScheduler
from xml_fetcher import fetch_and_convert_xml # Presumo que este arquivo exista
import json, os, re

app = FastAPI()

MAPEAMENTO_CATEGORIAS = {
    # (Seu MAPEAMENTO_CATEGORIAS aqui - omitido para brevidade, mas deve ser incluído)
    # Hatch
    "gol": "Hatch", "uno": "Hatch", "palio": "Hatch", "celta": "Hatch", "ka": "Hatch",
    "fiesta": "Hatch", "march": "Hatch", "sandero": "Hatch", "onix": "Hatch", "hb20": "Hatch",
    "i30": "Hatch", "golf": "Hatch", "polo": "Hatch", "fox": "Hatch", "up": "Hatch",
    "fit": "Hatch", "city": "Hatch", "yaris": "Hatch", "etios": "Hatch", "clio": "Hatch",
    "corsa": "Hatch", "bravo": "Hatch", "punto": "Hatch", "208": "Hatch", "argo": "Hatch",
    "mobi": "Hatch", "c3": "Hatch", "picanto": "Hatch", "astra hatch": "Hatch", "stilo": "Hatch",
    "focus hatch": "Hatch", "206": "Hatch", "c4 vtr": "Hatch", "kwid": "Hatch", "soul": "Hatch",
    "agile": "Hatch", "sonic hatch": "Hatch", "fusca": "Hatch",

    # Sedan
    "civic": "Sedan", "corolla": "Sedan", "sentra": "Sedan", "versa": "Sedan", "jetta": "Sedan",
    "prisma": "Sedan", "voyage": "Sedan", "siena": "Sedan", "grand siena": "Sedan", "cruze": "Sedan",
    "cobalt": "Sedan", "logan": "Sedan", "fluence": "Sedan", "cerato": "Sedan", "elantra": "Sedan",
    "virtus": "Sedan", "accord": "Sedan", "altima": "Sedan", "fusion": "Sedan", "mazda3": "Sedan",
    "mazda6": "Sedan", "passat": "Sedan", "city sedan": "Sedan", "astra sedan": "Sedan", "vectra sedan": "Sedan",
    "classic": "Sedan", "cronos": "Sedan", "linea": "Sedan", "focus sedan": "Sedan", "ka sedan": "Sedan",
    "408": "Sedan", "c4 pallas": "Sedan", "polo sedan": "Sedan", "bora": "Sedan", "hb20s": "Sedan",
    "lancer": "Sedan", "camry": "Sedan", "onix plus": "Sedan",

    # SUV
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

    # Caminhonete
    "hilux": "Caminhonete", "ranger": "Caminhonete", "s10": "Caminhonete", "l200": "Caminhonete", "triton": "Caminhonete",
    "saveiro": "Utilitário", "strada": "Utilitário", "montana": "Utilitário", "oroch": "Utilitário", 
    "toro": "Caminhonete", 
    "frontier": "Caminhonete", "amarok": "Caminhonete", "gladiator": "Caminhonete", "maverick": "Caminhonete", "colorado": "Caminhonete",
    "dakota": "Caminhonete", "montana (nova)": "Caminhonete", "f-250": "Caminhonete", "courier (pickup)": "Caminhonete", "hoggar": "Caminhonete",
    "ram 1500": "Caminhonete",

    # Utilitário
    "kangoo": "Utilitário", "partner": "Utilitário", "doblo": "Utilitário", "fiorino": "Utilitário", "berlingo": "Utilitário",
    "express": "Utilitário", "combo": "Utilitário", "kombi": "Utilitário", "doblo cargo": "Utilitário", "kangoo express": "Utilitário",

    # Furgão
    "master": "Furgão", "sprinter": "Furgão", "ducato": "Furgão", "daily": "Furgão", "jumper": "Furgão",
    "boxer": "Furgão", "trafic": "Furgão", "transit": "Furgão", "vito": "Furgão", "expert (furgão)": "Furgão",
    "jumpy (furgão)": "Furgão", "scudo (furgão)": "Furgão",

    # Coupe
    "camaro": "Coupe", "mustang": "Coupe", "tt": "Coupe", "supra": "Coupe", "370z": "Coupe",
    "rx8": "Coupe", "challenger": "Coupe", "corvette": "Coupe", "veloster": "Coupe", "cerato koup": "Coupe",
    "clk coupe": "Coupe", "a5 coupe": "Coupe", "gt86": "Coupe", "rcz": "Coupe", "brz": "Coupe",

    # Conversível
    "z4": "Conversível", "boxster": "Conversível", "miata": "Conversível", "beetle cabriolet": "Conversível", "slk": "Conversível",
    "911 cabrio": "Conversível", "tt roadster": "Conversível", "a5 cabrio": "Conversível", "mini cabrio": "Conversível", "206 cc": "Conversível",
    "eos": "Conversível",

    # Minivan / Station Wagon
    "spin": "Minivan", "livina": "Minivan", "caravan": "Minivan", "touran": "Minivan", "parati": "Station Wagon",
    "quantum": "Station Wagon", "sharan": "Minivan", "zafira": "Minivan", "picasso": "Minivan", "grand c4": "Minivan",
    "meriva": "Minivan", "scenic": "Minivan", "xsara picasso": "Minivan", "carnival": "Minivan", "idea": "Minivan",
    "spacefox": "Station Wagon", "golf variant": "Station Wagon", "palio weekend": "Station Wagon", "astra sw": "Station Wagon", "206 sw": "Station Wagon",
    "a4 avant": "Station Wagon", "fielder": "Station Wagon",

    # Off-road
    "wrangler": "Off-road", "troller": "Off-road", "defender": "Off-road", "bronco": "Off-road", "samurai": "Off-road",
    "jimny": "Off-road", "land cruiser": "Off-road", "grand vitara": "Off-road", "jimny sierra": "Off-road", "bandeirante (ate 2001)": "Off-road"
}

# ... (restante do código permanece inalterado, exceto pela inclusão abaixo)

def filtrar_veiculos(vehicles, filtros, valormax=None, anomax=None):
    # ... (toda a lógica anterior mantida)

    # Aplicar filtro de valormax (mantendo a lógica original de teto * 1.3)
    if valormax:
        try:
            teto = float(valormax)
            max_price_limit = teto * 1.3 
            vehicles_processados = [
                v for v in vehicles_processados
                if (converter_preco(v.get("preco")) or 0) <= max_price_limit
            ]
        except ValueError:
            return [] 

    # Aplicar filtro de anomax (ano com tolerância de até +2 anos)
    if anomax:
        try:
            ano_limite = int(anomax) + 2
            filtrados = []
            for v in vehicles_processados:
                ano_raw = str(v.get("ano", "")).strip()
                if not ano_raw.isdigit():
                    continue
                ano = int(ano_raw)
                if ano <= ano_limite:
                    filtrados.append(v)
            vehicles_processados = filtrados
        except ValueError:
            return []

    # ... (continuação do código como está)
    return vehicles_processados

@app.get("/api/data")
def get_data(request: Request):
    # ...
    query_params = dict(request.query_params)
    valormax = query_params.pop("ValorMax", None)
    anomax = query_params.pop("AnoMax", None)

    # ...
    resultado = filtrar_veiculos(vehicles, filtros_ativos, valormax, anomax)
    # ...
