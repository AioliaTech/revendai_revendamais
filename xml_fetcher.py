import requests, xmltodict, json, os, re
from datetime import datetime
from unidecode import unidecode

JSON_FILE = "data.json"

# =================== MAPS =======================
MAPEAMENTO_CATEGORIAS = {
    # (seu dicionário inteiro aqui)
    "gol": "Hatch", "uno": "Hatch", "palio": "Hatch", # ...etc
}
MAPEAMENTO_CILINDRADAS = {
    # (seu dicionário inteiro aqui)
    "cb 300": 300, "xre 300": 300, # ...etc
}

# =================== UTILS =======================

def normalizar_modelo(modelo):
    if not modelo:
        return ""
    modelo_norm = unidecode(modelo).lower()
    modelo_norm = re.sub(r'[^a-z0-9]', '', modelo_norm)
    return modelo_norm

def inferir_categoria(modelo):
    if not modelo:
        return None
    modelo_norm = normalizar_modelo(modelo)
    for mapeado, categoria in MAPEAMENTO_CATEGORIAS.items():
        mapeado_norm = normalizar_modelo(mapeado)
        if mapeado_norm in modelo_norm:
            return categoria
    return None

def inferir_cilindrada(modelo):
    if not modelo:
        return None
    modelo_norm = normalizar_modelo(modelo)
    for mapeado, cilindrada in MAPEAMENTO_CILINDRADAS.items():
        mapeado_norm = normalizar_modelo(mapeado)
        if mapeado_norm in modelo_norm:
            return cilindrada
    return None

def converter_preco_xml(valor_str):
    if not valor_str:
        return None
    try:
        valor = str(valor_str).replace("R$", "").replace(".", "").replace(",", ".").strip()
        return float(valor)
    except ValueError:
        return None

# Para cada estrutura de XML: estoque/veiculo OU ADS/AD
def extrair_veiculos(data_dict):
    # Compatibiliza para qualquer estrutura
    veic = None
    if "estoque" in data_dict and "veiculo" in data_dict["estoque"]:
        veic = data_dict["estoque"]["veiculo"]
    elif "ADS" in data_dict and "AD" in data_dict["ADS"]:
        veic = data_dict["ADS"]["AD"]
    else:
        return []

    # Garante lista
    if isinstance(veic, dict):
        veic = [veic]
    return veic

def extrair_fotos(v):
    # Caso estoque/veiculo (motos Dominato)
    if "fotos" in v and v["fotos"]:
        fotos_foto = v["fotos"].get("foto")
        if not fotos_foto:
            return []
        if isinstance(fotos_foto, dict):
            fotos_foto = [fotos_foto]
        return [
            img["url"].split("?")[0]
            for img in fotos_foto
            if isinstance(img, dict) and "url" in img
        ]
    # Caso ADS/AD (exemplo XML com IMAGE_URL)
    if "IMAGES" in v:
        image_url = v.get("IMAGES", {}).get("IMAGE_URL")
        if not image_url:
            return []
        if isinstance(image_url, list):
            return image_url
        return [image_url]
    return []

# =================== FETCHER MULTI-XML =======================

def get_xml_urls():
    urls = []
    for var, val in os.environ.items():
        if var.startswith("XML_URL") and val:
            urls.append(val)
    if "XML_URL" in os.environ and os.environ["XML_URL"] not in urls:
        urls.append(os.environ["XML_URL"])
    return urls

def fetch_and_convert_xml():
    try:
        XML_URLS = get_xml_urls()
        if not XML_URLS:
            raise ValueError("Nenhuma variável XML_URL definida")

        parsed_vehicles = []

        for XML_URL in XML_URLS:
            response = requests.get(XML_URL)
            data_dict = xmltodict.parse(response.content)
            veiculos = extrair_veiculos(data_dict)
            for v in veiculos:
                try:
                    # Detecta formato Dominato (estoque/veiculo) ou ADS/AD e adapta
                    if "idveiculo" in v: # Dominato motos (estoque/veiculo)
                        parsed = {
                            "id": v.get("idveiculo"),
                            "tipo": v.get("tipoveiculo"),
                            "marca": v.get("marca"),
                            "modelo": v.get("modelo"),
                            "categoria": inferir_categoria(v.get("modelo")),
                            "cilindrada": inferir_cilindrada(v.get("modelo")),
                            "ano": v.get("anomodelo"),
                            "km": v.get("quilometragem"),
                            "cor": v.get("cor"),
                            "combustivel": v.get("combustivel"),
                            "cambio": v.get("cambio"),
                            "portas": v.get("numeroportas"),
                            "preco": converter_preco_xml(v.get("preco")),
                            "opcionais": v.get("opcionais").get("opcional") if v.get("opcionais") else None,
                            "fotos": extrair_fotos(v)
                        }
                    else: # ADS/AD padrão webmotors e afins
                        parsed = {
                            "id": v.get("ID"),
                            "tipo": v.get("CATEGORY"),
                            "titulo": v.get("TITLE"),
                            "marca": v.get("MAKE"),
                            "modelo": v.get("MODEL"),
                            "categoria": v.get("BODY_TYPE"),
                            "cilindrada": inferir_cilindrada(v.get("MODEL")),
                            "ano": v.get("YEAR"),
                            "ano_fabricacao": v.get("FABRIC_YEAR"),
                            "km": v.get("MILEAGE"),
                            "cor": v.get("COLOR"),
                            "combustivel": v.get("FUEL"),
                            "cambio": v.get("GEAR"),
                            "motor": v.get("MOTOR"),
                            "portas": v.get("DOORS"),
                            "preco": float(str(v.get("PRICE", "0")).replace(",", "").strip() or 0),
                            "opcionais": v.get("ACCESSORIES"),
                            "fotos": extrair_fotos(v)
                        }
                    parsed_vehicles.append(parsed)
                except Exception as e:
                    print(f"[ERRO ao converter veículo ID {v.get('ID', v.get('idveiculo', ''))}] {e}")

        data_dict = {
            "veiculos": parsed_vehicles,
            "_updated_at": datetime.now().isoformat()
        }

        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(data_dict, f, ensure_ascii=False, indent=2)

        print("[OK] Dados atualizados com sucesso.")
        return data_dict

    except Exception as e:
        print(f"[ERRO] Falha ao converter XML: {e}")
        return {}
