from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import boto3
import json
from IPython.display import clear_output
from scrape_and_summarize import run as run_scraper

BUCKET = "jd-finance-news"
PREFIX = "runs/"

s3 = boto3.client("s3")

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

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/resumen/latest")
def endpoint_latest():
    fecha = get_latest_date()
    if not fecha:
        raise HTTPException(404, "No hay fechas en S3")
    key = get_one_jsonl_for_date(fecha)
    if not key:
        raise HTTPException(404, "No hay archivos jsonl para esa fecha")
    datos = read_jsonl_s3(key)
    return JSONResponse({"fecha": fecha, "articulos": datos})

@app.get("/resumen/{fecha}")
def endpoint_fecha(fecha: str):
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
def endpoint_historico():
    fechas = list_dates()
    master = {}
    for f in fechas:
        key = get_one_jsonl_for_date(f)
        if key:
            master[f] = read_jsonl_s3(key)
    return JSONResponse(master)

@app.get("/rss/list")
def endpoint_rss():
    return JSONResponse(list_rss_feeds())

@app.post("/forzar-scrape")
def endpoint_forzar_scrape():
    try:
        run_scraper()
        return JSONResponse({"status": "ok"})
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/")
def root():
    return {"status": "ok", "message": "FinanceNews API activa"}