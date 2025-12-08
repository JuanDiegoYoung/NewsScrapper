# NewsScrapper

Sistema de scraping y análisis de noticias financieras con API, dashboard Streamlit y despliegue en Kubernetes.

## Key Features

- **News scraper** para fuentes financieras
- **Resumen automático** usando modelos de lenguaje
- **Email reporting** con los insights más relevantes
- **API completa** para acceso en tiempo real
- **Completamente dockerizado** para deployment reproducible
- **Almacenamiento S3** para artículos, logs y outputs
- **Ejecución recurrente** mediante scheduled jobs
- **Dashboard Streamlit** para monitoreo y análisis
- **Integración continua** para testing y deployments
- **Control de tráfico** via load balancer y reglas de acceso

## 📁 Estructura del Proyecto

```
NewsScrapper/
├── src/                          # Código fuente
│   ├── api/                      # API FastAPI
│   │   └── api.py
│   ├── scraper/                  # Lógica de scraping
│   │   ├── scrape_and_summarize.py
│   │   └── save_bucket.py
│   └── streamlit/                # Dashboard web
│       └── streamlit_app.py
├── config/                       # Configuración
│   ├── config.py
│   ├── logger_utils.py
│   ├── requirements.txt
│   ├── requirements_api.txt
│   └── secret-policy.json
├── docker/                       # Dockerfiles
│   ├── Dockerfile.api
│   ├── Dockerfile.newscrapper
│   └── Dockerfile.streamlit
├── kubernetes/                   # Manifiestos K8s
│   ├── api-deployment.yaml
│   ├── api-service.yaml
│   ├── cronjob.yaml
│   ├── scraper-cronjob.yaml
│   ├── streamlit-deployment.yaml
│   ├── streamlit-service.yaml
│   └── debug.yaml
├── scripts/                      # Scripts de deployment
│   ├── deploy_lambda.sh
│   └── deploy_lambda.ps1
├── data/                         # Datos generados
│   ├── scraped_summaries.json
│   ├── scraped_summaries.jsonl
│   └── security_group.csv
├── tests/                        # Tests
│   ├── scrape_test.py
│   ├── test_athena.py
│   └── test_openai_local.py
├── docs/                         # Documentación
│   └── API_USAGE_GUIDE.md
└── README.md
```

## 🚀 Quick Start

### Instalación

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r config/requirements.txt
```

### Configuración

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env con tus credenciales
nano .env
```

### Ejecutar Scraper

```bash
# Desde la raíz del proyecto
export PYTHONPATH=$PWD
python src/scraper/scrape_and_summarize.py
```

### Ejecutar API

```bash
# Desde la raíz del proyecto
export PYTHONPATH=$PWD
uvicorn src.api.api:app --reload --host 0.0.0.0 --port 8000
```

### Ejecutar Dashboard

```bash
# Desde la raíz del proyecto
export PYTHONPATH=$PWD
streamlit run src/streamlit/streamlit_app.py
```

## 🐳 Docker

### Build

```bash
# Desde la raíz del proyecto

# API
docker build -f docker/Dockerfile.api -t newscrapper-api .

# Scraper
docker build -f docker/Dockerfile.newscrapper -t newscrapper .

# Streamlit
docker build -f docker/Dockerfile.streamlit -t newscrapper-streamlit .
```

### Run

```bash
# API (puerto 8000)
docker run -p 8000:8000 --env-file .env newscrapper-api

# Scraper (ejecución única)
docker run --env-file .env newscrapper

# Streamlit (puerto 8501)
docker run -p 8501:8501 --env-file .env newscrapper-streamlit
```

## ☸️ Kubernetes

```bash
# Deploy completo
kubectl apply -f kubernetes/

# Solo API
kubectl apply -f kubernetes/api-deployment.yaml
kubectl apply -f kubernetes/api-service.yaml

# CronJob
kubectl apply -f kubernetes/scraper-cronjob.yaml
```

## 📚 Documentación

Ver [API_USAGE_GUIDE.md](docs/API_USAGE_GUIDE.md) para más detalles sobre el uso de la API.

## 🧪 Tests

```bash
# Ejecutar todos los tests
pytest tests/

# Test específico
python tests/scrape_test.py
```

## 📝 Configuración

Las variables de entorno y configuraciones se encuentran en `config/config.py`.

## 🔐 Secrets

Los secretos se gestionan mediante AWS Secrets Manager. Ver `config/secret-policy.json`.
