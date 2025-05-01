from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from unidecode import unidecode
from rapidfuzz import fuzz
import json, os

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

    # Função auxiliar para normalizar texto
    def normalizar(texto: str) -> str:
        return unidecode(texto).lower().replace("-", "").replace(" ", "")

    # 🔍 Busca por similaridade
    for chave, valor in query_params.items():
        valor_normalizado = normalizar(valor)
        resultado_aproximado = []

        for v in vehicles:
            if chave in v and v[chave]:
                texto_alvo = normalizar(str(v[chave]))
                score = fuzz.partial_ratio(valor_normalizado, texto_alvo)
                if score >= 80:  # Sensibilidade ajustável
                    resultado_aproximado.append(v)

        vehicles = resultado_aproximado

    # 💰 Filtro por ValorMax
    def converter_preco(valor_str):
        try:
            return float(str(valor_str).replace(",", "").replace("R$", "").strip())
        except:
            return None

    if valormax:
        try:
            teto = float(valormax)
            vehicles = [
                v for v in vehicles
                if "preco" in v and converter_preco(v["preco"]) is not None and converter_preco(v["preco"]) <= teto
            ]
        except:
            return {"error": "Formato inválido para ValorMax"}

    # 🔽 Ordena por preço decrescente
    vehicles.sort(
        key=lambda v: converter_preco(v["preco"]) if "preco" in v else 0,
        reverse=True
    )

    return JSONResponse(content=vehicles)
