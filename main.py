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
    campos_com_fuzzy = ["modelo"]
    campos_exatos = ["titulo"]
    vehicles_filtrados = vehicles.copy()

    # Comparação exata para categoria
    if filtros.get("categoria"):
        categoria_filtrada = normalizar(filtros["categoria"])
        vehicles_filtrados = [
            v for v in vehicles_filtrados
            if normalizar(v.get("categoria", "")) == categoria_filtrada
        ]

    for chave, valor in filtros.items():
        if not valor or chave == "categoria":
            continue
        termo_busca = normalizar(valor)
        termos = termo_busca.split()
        resultados = []

        for v in vehicles_filtrados:
            match = False
            for campo in campos_com_fuzzy + campos_exatos:
                conteudo = v.get(campo, "")
                if not conteudo:
                    continue
                texto = normalizar(str(conteudo))

                if campo in campos_exatos:
                    if termo_busca in texto or texto in termo_busca:
                        match = True
                        break

                elif campo in campos_com_fuzzy:
                    # Cada termo da busca precisa bater com algo no texto
                    for termo in termos:
                        if termo in texto or texto in termo:
                            match = True
                            break
                        score_ratio = fuzz.ratio(termo, texto)
                        score_token = fuzz.token_set_ratio(termo, texto)
                        score_partial = fuzz.partial_ratio(termo, texto)
                        if score_ratio >= 70 or score_token >= 70 or score_partial >= 70:
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
        "marca": query_params.get("marca"),
        "categoria": query_params.get("categoria")
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
