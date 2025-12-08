

import os
import requests

API_KEY = os.environ.get("OPENAI_API_KEY") 

url = "https://api.openai.com/v1/responses"
headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
data = {
"model": "gpt-4",
"input": [
{"role": "system", "content": "Sos un asistente financiero."},
{"role": "user", "content": "Dame un resumen corto de las bolsas globales."}
]
}

resp = requests.post(url, headers=headers, json=data, timeout=30)
print(resp.json())