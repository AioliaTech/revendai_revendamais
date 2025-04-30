import requests
import xmltodict
import json
import os

XML_URL = os.getenv("XML_URL")
JSON_FILE = "data.json"

def fetch_and_convert_xml():
    try:
        if not XML_URL:
            raise ValueError("Variável XML_URL não definida")

        response = requests.get(XML_URL)
        data_dict = xmltodict.parse(response.content)

        # Salva o JSON no disco
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(data_dict, f, ensure_ascii=False, indent=2)

        print("[INFO] XML convertido e salvo como JSON")
        return data_dict

    except Exception as e:
        print(f"[ERRO] Falha ao converter XML: {e}")
        return {}
