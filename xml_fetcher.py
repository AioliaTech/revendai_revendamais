import requests
import xmltodict
import json
import os

XML_URL = os.getenv("XML_URL")
JSON_FILE = "data.json"

# ✅ Encurtador com cache em memória
encurtador_cache = {}

def encurtar_url(url_original):
    if url_original in encurtador_cache:
        return encurtador_cache[url_original]
    try:
        response = requests.get(
            "https://is.gd/create.php",
            params={"format": "simple", "url": url_original},
            timeout=2
        )
        if response.status_code == 200:
            short_url = response.text.strip()
            encurtador_cache[url_original] = short_url
            return short_url
    except:
        pass
    return url_original

def fetch_and_convert_xml():
    try:
        if not XML_URL:
            raise ValueError("Variável XML_URL não definida")

        response = requests.get(XML_URL)
        data_dict = xmltodict.parse(response.content)

        # ✅ Acesse a lista de veículos e encurte imagens
        try:
            vehicles = data_dict["ADS"]["AD"]
            for v in vehicles:
                if "IMAGES" in v and "IMAGE_URL" in v["IMAGES"]:
                    imagens = v["IMAGES"]["IMAGE_URL"]
                    if isinstance(imagens, list) and imagens and isinstance(imagens[0], str):
                        # Encurtar só a primeira imagem
                        v["IMAGES"]["IMAGE_URL"][0] = encurtar_url(imagens[0])
        except Exception as e:
            print(f"[WARNING] Falha ao encurtar imagens: {e}")

        # ✅ Salva o JSON localmente
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(data_dict, f, ensure_ascii=False, indent=2)

        print("[INFO] XML convertido e salvo como JSON com URLs encurtadas")
        return data_dict

    except Exception as e:
        print(f"[ERRO] Falha geral no processamento: {e}")
        return {}
