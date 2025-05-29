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

def filtrar_veiculos(vehicles, filtros, valormax=None):
    campos_textuais = ["modelo", "titulo", "marca", "cor", "categoria", "cambio", "combustivel"]
    vehicles_filtrados = vehicles.copy()

    for chave, valor in filtros.items():
        if not valor:
            continue
        termo_busca = normalizar(valor)
        termos = termo_busca.split()
        resultados = []

        for v in vehicles_filtrados:
            match = False
            for campo in campos_textuais:
                conteudo = v.get(campo, "")
                if not conteudo:
                    continue
                texto = normalizar(str(conteudo))

                for termo in termos:
                    score_ratio = fuzz.ratio(texto, termo)
                    score_token = fuzz.token_set_ratio(texto, termo)
                    if termo in texto or texto in termo or score_ratio >= 70 or score_token >= 70:
                        match = True
                        break
                if match:
                    break

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
        "marca": query_params.get("marca")
    }

    resultado = filtrar_veiculos(vehicles, filtros, valormax)

    if resultado:
        return JSONResponse(content={
            "resultados": resultado,
            "total_encontrado": len(resultado)
        })

    alternativas = []

    alternativa1 = filtrar_veiculos(vehicles, filtros)
    if alternativa1:
        alternativas = alternativa1
    else:
        filtros_sem_marca = {"modelo": filtros.get("modelo")}
        alternativa2 = filtrar_veiculos(vehicles, filtros_sem_marca, valormax)
        if alternativa2:
            alternativas = alternativa2
        else:
            modelo = filtros.get("modelo")
            categoria_inferida = inferir_categoria_por_modelo(modelo) if modelo else None
            if categoria_inferida:
                filtros_categoria = {"categoria": categoria_inferida}
                alternativa3 = filtrar_veiculos(vehicles, filtros_categoria, valormax)
                if alternativa3:
                    alternativas = alternativa3
                else:
                    alternativa4 = filtrar_veiculos(vehicles, filtros_categoria)
                    if alternativa4:
                        alternativas = alternativa4

    if alternativas:
        alternativa = [
            {"titulo": v.get("titulo", ""), "preco": v.get("preco", "")}
            for v in alternativas
        ]
        return JSONResponse(content={
            "resultados": [],
            "total_encontrado": 0,
            "instrucao_ia": "Não encontramos veículos com os parâmetros informados dentro do valor desejado. Seguem as opções mais próximas.",
            "alternativa": {
                "resultados": alternativa,
                "total_encontrado": len(alternativa)
            }
        })

    return JSONResponse(content={
        "resultados": [],
        "total_encontrado": 0,
        "instrucao_ia": "Não encontramos veículos com os parâmetros informados e também não encontramos opções próximas."
    })
