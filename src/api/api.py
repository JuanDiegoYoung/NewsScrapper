from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import boto3
import json
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.scraper.scrape_and_summarize import run_once as run_scraper
from config.config import BUCKET, PREFIX, SECRET_NAME, REGION

s3 = boto3.client("s3")

# =========================
#  Cargar API key desde Secrets Manager
# =========================

def load_api_key():
    sm = boto3.client("secretsmanager", region_name=REGION)
    raw = sm.get_secret_value(SecretId=SECRET_NAME)["SecretString"]
    data = json.loads(raw)
    return data["NEWSCRAPPER-API-KEY"]

API_KEY = load_api_key()

def verify_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

# =========================
#  Funciones internas
# =========================
def list_dates():
    resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=PREFIX, Delimiter="/")
    prefixes = resp.get("CommonPrefixes", [])
    fechas = []
    for p in prefixes:
        key = p["Prefix"]
        if key.startswith("runs/dt=") and key.endswith("/"):
            fechas.append(key.replace("runs/dt=", "").replace("/", ""))
    return fechas

def get_one_jsonl_for_date(fecha):
    prefix = f"{PREFIX}dt={fecha}/"
    resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
    archivos = resp.get("Contents", [])
    jsonls = [x["Key"] for x in archivos if x["Key"].endswith(".jsonl")]
    if not jsonls:
        return None
    jsonls.sort()
    return jsonls[0]

def read_jsonl_s3(key):
    obj = s3.get_object(Bucket=BUCKET, Key=key)
    contenido = obj["Body"].read().decode("utf-8").splitlines()
    datos = []
    for linea in contenido:
        try:
            datos.append(json.loads(linea))
        except:
            pass
    return datos

def get_latest_date():
    fechas = list_dates()
    if not fechas:
        return None
    fechas.sort()
    return fechas[-1]

def list_rss_feeds():
    return [
        "https://www.bloomberg.com/feeds/rss/news.rss",
        "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
        "https://www.reutersagency.com/feed/?taxonomy=best-sectors&post_type=best"
    ]


# =========================
#  FastAPI
# =========================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/resumen/latest")
def endpoint_latest(auth=Depends(verify_key)):
    fecha = get_latest_date()
    if not fecha:
        raise HTTPException(404, "No hay fechas en S3")
    key = get_one_jsonl_for_date(fecha)
    if not key:
        raise HTTPException(404, "No hay archivos jsonl para esa fecha")
    datos = read_jsonl_s3(key)
    return JSONResponse({"fecha": fecha, "articulos": datos})

@app.get("/resumen/{fecha}")
def endpoint_fecha(fecha: str, auth=Depends(verify_key)):
    try:
        datetime.strptime(fecha, "%Y-%m-%d")
    except:
        raise HTTPException(400, "Formato de fecha inválido YYYY-MM-DD")
    key = get_one_jsonl_for_date(fecha)
    if not key:
        raise HTTPException(404, "No hay archivo jsonl para esa fecha")
    datos = read_jsonl_s3(key)
    return JSONResponse({"fecha": fecha, "articulos": datos})

@app.get("/historico")
def endpoint_historico(auth=Depends(verify_key)):
    fechas = list_dates()
    master = {}
    for f in fechas:
        key = get_one_jsonl_for_date(f)
        if key:
            master[f] = read_jsonl_s3(key)
    return JSONResponse(master)

@app.get("/rss/list")
def endpoint_rss(auth=Depends(verify_key)):
    return JSONResponse(list_rss_feeds())

@app.post("/forzar-scrape")
def endpoint_forzar_scrape(auth=Depends(verify_key)):
    try:
        run_scraper()
        return JSONResponse({"status": "ok"})
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/")
def root(auth=Depends(verify_key)):
    return {"status": "ok", "message": "FinanceNews API activa"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )