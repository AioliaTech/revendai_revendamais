import requests, xmltodict, json, os
from datetime import datetime

XML_URL = os.getenv("XML_URL")
JSON_FILE = "data.json"

def fetch_and_convert_xml():
    try:
        if not XML_URL:
            raise ValueError("Variável XML_URL não definida")
        response = requests.get(XML_URL)
        data_dict = xmltodict.parse(response.content)

        parsed_vehicles = []

        for v in data_dict["ADS"]["AD"]:
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
    "fotos": {
        "url_fotos": v.get("IMAGES", {}).get("IMAGE_URL", [])
    }
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
