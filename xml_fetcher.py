import requests, xmltodict, json, os, re
from datetime import datetime
from unidecode import unidecode

JSON_FILE = "data.json"

MAPEAMENTO_CILINDRADAS = {
    "g 310": 300, "f 750 gs": 850, "f 850 gs": 850, "f 900": 900, "r 1250": 1250,
    "r 1300": 1300, "r 18": 1800, "k 1300": 1300, "k 1600": 1650, "s 1000": 1000,
    "g 650 gs": 650, "cb 300": 300, "cb 500": 500, "cb 650": 650, "cb 1000r": 1000,
    "cb twister": 300, "twister": 300, "cbr 250": 250, "cbr 500": 500, "cbr 600": 600,
    "cbr 650": 650, "cbr 1000": 1000, "hornet 600": 600, "cb 600f": 600, "xre 190": 190,
    "xre 300": 300, "xre 300 sahara": 300, "sahara 300": 300, "sahara 300 rally": 300,
    "nxr 160": 160, "bros 160": 160, "cg 160": 160, "cg 160 titan": 160, "cg 160 fan": 160,
    "cg 160 start": 160, "cg 160 titan s": 160, "cg 125": 125, "cg 125 fan ks": 125,
    "biz 125": 125, "biz 125 es": 125, "biz 110": 110, "pop 110": 110, "pop 110i": 110,
    "pcx 150": 150, "pcx 160": 160, "xj6": 600, "mt 03": 300, "mt 07": 690, "mt 09": 890,
    "mt 01": 1700, "fazer 150": 150, "fazer 250": 250, "ys 250": 250, "factor 125": 125,
    "factor 150": 150, "xtz 150": 150, "xtz 250": 250, "xtz 250 tenere": 250, "tenere 250": 250,
    "lander 250": 250, "yzf r3": 300, "yzf r-3": 300, "r15": 150, "r1": 1000,
    "nmax 160": 160, "xmax 250": 250, "gs500": 500, "bandit 600": 600, "bandit 650": 650,
    "bandit 1250": 1250, "gsx 650f": 650, "gsx-s 750": 750, "gsx-s 1000": 1000,
    "hayabusa": 1350, "gixxer 250": 250, "burgman 125": 125, "z300": 300, "z400": 400,
    "z650": 650, "z750": 750, "z800": 800, "z900": 950, "z1000": 1000, "ninja 300": 300,
    "ninja 400": 400, "ninja 650": 650, "ninja 1000": 1050, "ninja zx-10r": 1000,
    "er6n": 650, "versys 300": 300, "versys 650": 650, "xt 660": 660, "meteor 350": 350,
    "classic 350": 350, "hunter 350": 350, "himalayan": 400, "interceptor 650": 650,
    "continental gt 650": 650, "tiger 800": 800, "tiger 900": 900, "street triple": 750,
    "speed triple": 1050, "bonneville": 900, "trident 660": 660, "monster 797": 800,
    "monster 821": 820, "monster 937": 940, "panigale v2": 950, "panigale v4": 1100,
    "iron 883": 883, "forty eight": 1200, "sportster s": 1250, "fat bob": 1140,
    "road glide": 2150, "street glide": 1750, "next 300": 300, "commander 250": 250,
    "dafra citycom 300": 300, "dr 160": 160, "dr 160 s": 160, "cforce 1000": 1000,
    "trx 420": 420, "t350 x": 350, "xr300l tornado": 300, "fz25 fazer": 250, "fz15 fazer": 150,
    "biz es": 125, "elite 125": 125, "crf 230f": 230, "cg150 fan": 150, "cg150 titan": 150, "diavel 1260": 1260,
    "cg150 titan": 150, "YZF R-6": 600, "MT-03": 300, "MT03": 300, "ER-6N": 650, "xt 600": 600, "biz 125": 125,
    "cg 125": 125
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
                        parsed = {
                        "id": v.get("ID"),
                        "tipo": v.get("CATEGORY"),
                        "titulo": v.get("TITLE"),
                        "marca": v.get("MAKE"),
                        "modelo": v.get("MODEL"),
                        "ano": v.get("YEAR"),
                        "ano_fabricacao": v.get("FABRIC_YEAR"),
                        "km": v.get("MILEAGE"),
                        "cor": v.get("COLOR"),
                        "combustivel": v.get("FUEL"),
                        "cambio": v.get("GEAR"),
                        "motor": v.get("MOTOR"),
                        "portas": v.get("DOORS"),
                        "categoria": v.get("BODY_TYPE"),
                        "preco": float(v.get("PRICE", "0").replace(",", "").strip()),
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
