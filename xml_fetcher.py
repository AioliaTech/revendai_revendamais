import requests, xmltodict, json, os
 
 XML_URL = os.getenv("XML_URL")
 JSON_FILE = "data.json"
 
 def fetch_and_convert_xml():
     if not XML_URL:
         raise ValueError("Variável XML_URL não configurada")
     response = requests.get(XML_URL)
     data_dict = xmltodict.parse(response.content)
     with open(JSON_FILE, "w", encoding="utf-8") as f:
         json.dump(data_dict, f, ensure_ascii=False, indent=2)
     return data_dict
