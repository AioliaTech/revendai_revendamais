from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from unidecode import unidecode
from rapidfuzz import fuzz
from apscheduler.schedulers.background import BackgroundScheduler
from xml_fetcher import fetch_and_convert_xml
import json, os

app = FastAPI()

def normalizar(texto: str) -> str:
    return unidecode(texto).lower().replace("-", "").replace(" ", "").strip()

def converter_preco(valor_str):
    try:
        return float(str(valor_str).replace(",", "").replace("R$", "").strip())
    except:
        return None

def fuzzy_match(conteudo, termos):
    texto = normalizar(conteudo)
    palavras = texto.split()

    for termo in termos:
        termo = normalizar(termo)
        if termo in texto or texto in termo:
            return True

        score_total = max(
            fuzz.partial_ratio(texto, termo),
            fuzz.token_sort_ratio(texto, termo)
        )
        if score_total >= 70:
            return True

        for palavra in palavras:
            score = max(
                fuzz.partial_ratio(palavra, termo),
                fuzz.token_sort_ratio(palavra, termo)
            )
            if score >= 70:
                return True
    return False

def filtrar_veiculos(vehicles, filtros, valormax=None):
    vehicles_filtrados = vehicles.copy()
    campos_textuais = ["modelo", "titulo"]  # fuzzy nestes campos

    for chave, valor in filtros.items():
        if not valor:
            continue

        termos = normalizar(valor).split()
        resultados = []

        for v in vehicles_filtrados:
            match = False

            if chave in campos_textuais:
                for campo in campos_textuais:
                    if campo in v and fuzzy_match(v.get(campo, ""), termos):
                        match = True
                        break
            else:
                campo_valor = normalizar(v.get(chave, ""))
                termo_busca = normalizar(valor)
                if termo_busca in campo_valor or campo_valor in termo_busca:
                    match = True

            if match:
                resultados.append(v)

        vehicles_filtrados = resultados

    if valormax:
        try:
            teto = float(valormax)
            maximo = teto * 1.3
            vehicles_filtrados = [
                v for v in vehicles_filtrados
                if "preco" in v and converter_preco(v["preco"]) is not None and converter_preco(v["preco"]) <= maximo
            ]
        except:
            return []

    vehicles_filtrados.sort(
        key=lambda v: converter_preco(v["preco"]) if "preco" in v else float('inf'),
        reverse=True
    )
    return vehicles_filtrados

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

    filtros = {
        "modelo": query_params.get("modelo"),
        "marca": query_params.get("marca"),
        "categoria": query_params.get("categoria")
    }

    resultado = filtrar_veiculos(vehicles, filtros, valormax)

    if resultado:
        return JSONResponse(content={
            "resultados": resultado,
            "total_encontrado": len(resultado)
        })

    return JSONResponse(content={
        "resultados": [],
        "total_encontrado": 0,
        "instrucao_ia": "Não encontramos veículos com os parâmetros informados."
    })
