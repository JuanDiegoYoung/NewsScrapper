# FinanceNews API - Guía de Uso

## Autenticación

Todas las peticiones requieren el header de autenticación:

```
X-API-Key: api-newscrapper-key01
```

## URL Base

```
http://ac29f9f9f63c4457c9520557b01bcab9-369530971.us-east-1.elb.amazonaws.com
```

---

## Endpoints Disponibles

### 1. Obtener el resumen más reciente

**Endpoint:** `GET /resumen/latest`

**Descripción:** Retorna los artículos de noticias financieras de la fecha más reciente disponible.

**Ejemplo:**
```bash
curl -H "X-API-Key: api-newscrapper-key01" \
  http://ac29f9f9f63c4457c9520557b01bcab9-369530971.us-east-1.elb.amazonaws.com/resumen/latest
```

**Respuesta:**
```json
{
  "fecha": "2024-12-01",
  "articulos": [
    {
      "title": "...",
      "summary": "...",
      "link": "...",
      "published": "..."
    }
  ]
}
```

---

### 2. Obtener resumen de una fecha específica

**Endpoint:** `GET /resumen/{fecha}`

**Descripción:** Retorna los artículos de una fecha específica.

**Formato de fecha:** `YYYY-MM-DD`

**Ejemplo:**
```bash
curl -H "X-API-Key: api-newscrapper-key01" \
  http://ac29f9f9f63c4457c9520557b01bcab9-369530971.us-east-1.elb.amazonaws.com/resumen/2024-12-01
```

**Respuesta:**
```json
{
  "fecha": "2024-12-01",
  "articulos": [...]
}
```

---

### 3. Obtener todo el histórico

**Endpoint:** `GET /historico`

**Descripción:** Retorna todos los artículos de todas las fechas disponibles.

**Ejemplo:**
```bash
curl -H "X-API-Key: api-newscrapper-key01" \
  http://ac29f9f9f63c4457c9520557b01bcab9-369530971.us-east-1.elb.amazonaws.com/historico
```

**Respuesta:**
```json
{
  "2024-11-28": [...],
  "2024-11-29": [...],
  "2024-12-01": [...]
}
```

---

### 4. Listar los feeds RSS configurados

**Endpoint:** `GET /rss/list`

**Descripción:** Retorna la lista de feeds RSS que se están scrapeando.

**Ejemplo:**
```bash
curl -H "X-API-Key: api-newscrapper-key01" \
  http://ac29f9f9f63c4457c9520557b01bcab9-369530971.us-east-1.elb.amazonaws.com/rss/list
```

**Respuesta:**
```json
[
  "https://www.bloomberg.com/feeds/rss/news.rss",
  "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
  "https://www.reutersagency.com/feed/?taxonomy=best-sectors&post_type=best"
]
```

---

### 5. Forzar un scrape inmediato

**Endpoint:** `POST /forzar-scrape`

**Descripción:** Ejecuta el scraper manualmente y guarda los resultados en S3.

**Ejemplo:**
```bash
curl -X POST -H "X-API-Key: api-newscrapper-key01" \
  http://ac29f9f9f63c4457c9520557b01bcab9-369530971.us-east-1.elb.amazonaws.com/forzar-scrape
```

**Respuesta:**
```json
{
  "status": "ok"
}
```

---

### 6. Verificar estado de la API

**Endpoint:** `GET /`

**Descripción:** Verifica que la API esté funcionando correctamente.

**Ejemplo:**
```bash
curl -H "X-API-Key: api-newscrapper-key01" \
  http://ac29f9f9f63c4457c9520557b01bcab9-369530971.us-east-1.elb.amazonaws.com/
```

**Respuesta:**
```json
{
  "status": "ok",
  "message": "FinanceNews API activa"
}
```

---

## Códigos de Error

- **401 Unauthorized:** El header `X-API-Key` es incorrecto o no está presente
- **404 Not Found:** No se encontraron datos para la fecha solicitada
- **400 Bad Request:** Formato de fecha inválido (debe ser YYYY-MM-DD)
- **500 Internal Server Error:** Error en el servidor

---

## Notas Importantes

- Todas las respuestas están en formato JSON
- Sin el header `X-API-Key` correcto, recibirás un error 401 (Unauthorized)
- Los datos se actualizan automáticamente mediante un cronjob en Kubernetes
- Los artículos incluyen título, resumen, enlace y fecha de publicación
- El resumen es generado automáticamente usando IA

---

## Ejemplo de Uso en Python

```python
import requests

API_KEY = "api-newscrapper-key01"
BASE_URL = "http://ac29f9f9f63c4457c9520557b01bcab9-369530971.us-east-1.elb.amazonaws.com"

headers = {
    "X-API-Key": API_KEY
}

# Obtener el resumen más reciente
response = requests.get(f"{BASE_URL}/resumen/latest", headers=headers)
data = response.json()

print(f"Fecha: {data['fecha']}")
print(f"Artículos: {len(data['articulos'])}")

for articulo in data['articulos']:
    print(f"\n- {articulo['title']}")
    print(f"  {articulo['summary']}")
```

---

## Ejemplo de Uso en JavaScript

```javascript
const API_KEY = "api-newscrapper-key01";
const BASE_URL = "http://ac29f9f9f63c4457c9520557b01bcab9-369530971.us-east-1.elb.amazonaws.com";

fetch(`${BASE_URL}/resumen/latest`, {
  headers: {
    "X-API-Key": API_KEY
  }
})
  .then(response => response.json())
  .then(data => {
    console.log(`Fecha: ${data.fecha}`);
    console.log(`Artículos: ${data.articulos.length}`);
    
    data.articulos.forEach(articulo => {
      console.log(`\n- ${articulo.title}`);
      console.log(`  ${articulo.summary}`);
    });
  });
```

---

## Soporte

Para cualquier problema o pregunta, contactar al administrador del sistema.
