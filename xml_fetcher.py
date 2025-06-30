import requests, xmltodict, json, os
from datetime import datetime

JSON_FILE = "data.json"

# Busca todas as variáveis de ambiente do tipo XML_URL, XML_URL_1, XML_URL_2...
def get_xml_urls():
    urls = []
    for var, val in os.environ.items():
        if var.startswith("XML_URL") and val:
            urls.append(val)
    # compatível com variável única chamada XML_URL
    if "XML_URL" in os.environ and os.environ["XML_URL"] not in urls:
        urls.append(os.environ["XML_URL"])
    return urls

def extrair_fotos(v):
    # O campo pode ser {'IMAGES': {'IMAGE_URL': [...ou string...]}}
    imagens = v.get("IMAGES")
    if not imagens:
        return []
    image_url = imagens.get("IMAGE_URL")
    if not image_url:
        return []
    # pode ser uma lista ou uma string única
    if isinstance(image_url, list):
        return image_url
    return [image_url]

def fetch_and_convert_xml():
    try:
        XML_URLS = get_xml_urls()
        if not XML_URLS:
            raise ValueError("Nenhuma variável XML_URL definida")
        
        parsed_vehicles = []

        for XML_URL in XML_URLS:
            response = requests.get(XML_URL)
            data_dict = xmltodict.parse(response.content)
            # suporta diferentes formatos (ADS/AD padrão)
            ads = data_dict.get("ADS", {}).get("AD", [])
            # garante que seja lista
            if isinstance(ads, dict):
                ads = [ads]
            for v in ads:
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
                        "preco": float(str(v.get("PRICE", "0")).replace(",", "").strip() or 0),
                        "opcionais": v.get("ACCESSORIES"),
                        "fotos": extrair_fotos(v)
                    }
                    parsed_vehicles.append(parsed)
                except Exception as e:
                    print(f"[ERRO ao converter veículo ID {v.get('ID')}] {e}")

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
