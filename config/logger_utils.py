# ---- Logging estructurado para Lambda (JSON + contexto) ----
import logging, json, time, os, sys, traceback
from typing import Optional, Dict, Any

# JSON formatter minimalista (sin libs externas)
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = {
            "ts": int(time.time() * 1000),
            "level": record.levelname,
            "msg": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
        }
        # Adjunta 'extra' si viene como dict en record.__dict__
        for k, v in record.__dict__.items():
            if k in base or k.startswith("_"):
                continue
            # Solo serializables
            try:
                json.dumps(v)
                base[k] = v
            except Exception:
                base[k] = str(v)
        # Adjunta stack si es excepción
        if record.exc_info:
            base["exc_type"] = str(record.exc_info[0].__name__)
            base["exc"] = self.formatException(record.exc_info)
        return json.dumps(base, ensure_ascii=False)

def get_logger(name: str = "scraper", level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.propagate = False
    return logger

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
ENV_STAGE = os.getenv("STAGE", "prod")
logger = get_logger(level=LOG_LEVEL)

def log_info(msg: str, extra: Optional[Dict[str, Any]] = None):
    logger.info(msg, extra={"stage": ENV_STAGE, **(extra or {})})

def log_warn(msg: str, extra: Optional[Dict[str, Any]] = None):
    logger.warning(msg, extra={"stage": ENV_STAGE, **(extra or {})})

def log_error(msg: str, extra: Optional[Dict[str, Any]] = None):
    logger.error(msg, extra={"stage": ENV_STAGE, **(extra or {})})

# ---- Ejemplos de integración con tu código existente ----
# 1) Loggear inicio/fin de scraping de cada feed y medir latencias
def timed_call(fn, *args, **kwargs):
    t0 = time.time()
    err = None
    try:
        res = fn(*args, **kwargs)
        return res, None, time.time() - t0
    except Exception as e:
        err = e
        raise
    finally:
        if err is not None:
            log_error("call_failed", {"func": getattr(fn, "__name__", "unknown"), "latency_s": round(time.time() - t0, 3)})

# 8) (Opcional avanzado) Métricas embebidas (EMF) para CloudWatch Metrics sin código extra:
def emit_metric(name: str, value: float, unit: str = "Count", dims: Optional[Dict[str, str]] = None):
    # CloudWatch Embedded Metric Format
    blob = {
        "_aws": {
            "Timestamp": int(time.time() * 1000),
            "CloudWatchMetrics": [
                {"Namespace": "FinanceScraper", "Dimensions": [list((dims or {"Stage": ENV_STAGE}).keys())], "Metrics": [{"Name": name, "Unit": unit}]}
            ],
        },
        name: value,
    }
    blob.update(dims or {"Stage": ENV_STAGE})
    print(json.dumps(blob))  # EMF requiere stdout en JSON plano

# Ejemplos de uso de métricas:
# emit_metric("OpenAIRequests", 1)
# emit_metric("ScrapeLatencyMs", 1234, unit="Milliseconds", dims={"Stage": ENV_STAGE, "Feed": "Reuters"})
