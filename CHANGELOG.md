# Changelog

## [Reorganización] - 2025-12-08

### Cambios Estructurales

#### ✨ Nueva Estructura de Carpetas
- **src/**: Todo el código fuente ahora está organizado en módulos
  - `src/api/`: API FastAPI
  - `src/scraper/`: Lógica de scraping y guardado
  - `src/streamlit/`: Dashboard web
- **config/**: Configuración y utilidades
  - Archivos de requirements
  - Configuración de logging
  - Políticas de secrets
- **docker/**: Todos los Dockerfiles centralizados
- **kubernetes/**: Manifiestos de Kubernetes organizados
- **scripts/**: Scripts de deployment
- **data/**: Archivos de datos generados
- **docs/**: Documentación
- **tests/**: Tests unitarios

#### 🔧 Archivos Actualizados
- Dockerfiles actualizados para nueva estructura
- Imports actualizados en todos los archivos Python
- README.md con documentación completa
- .gitignore mejorado
- Nuevo .env.example para configuración

#### 📦 Módulos Python
- Añadidos `__init__.py` en todos los paquetes
- Configurado PYTHONPATH para imports correctos

### Migración

Si tenías scripts o configuraciones que apuntaban a los archivos antiguos:

**Antes:**
```bash
python api.py
python scrape_and_summarize.py
streamlit run streamlit_app.py
```

**Ahora:**
```bash
export PYTHONPATH=$PWD
python src/api/api.py  # o uvicorn src.api.api:app
python src/scraper/scrape_and_summarize.py
streamlit run src/streamlit/streamlit_app.py
```

### Docker

Los Dockerfiles ahora están en `docker/` y copian los archivos desde las nuevas ubicaciones:

```bash
docker build -f docker/Dockerfile.api -t newscrapper-api .
docker build -f docker/Dockerfile.newscrapper -t newscrapper .
docker build -f docker/Dockerfile.streamlit -t newscrapper-streamlit .
```
