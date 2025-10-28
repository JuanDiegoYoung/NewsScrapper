# ===== save_bucket.py =====
import os, io, json, datetime
import boto3
from logger_utils import logger  # reutilizamos el logger global

S3_BUCKET = os.getenv("S3_BUCKET", "")
S3_PREFIX = os.getenv("S3_PREFIX", "runs")
s3 = boto3.client("s3")

def _results_to_jsonl_bytes(results):
    buf = io.StringIO()
    for r in results:
        buf.write(json.dumps(r, ensure_ascii=False) + "\n")
    return buf.getvalue().encode("utf-8")

def upload_results_to_s3(results, request_id: str) -> bool:
    if not S3_BUCKET:
        logger.warning("s3.skip_no_bucket")
        return False
    date_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    key = f"{S3_PREFIX}/dt={date_str}/run={request_id}.jsonl"
    body = _results_to_jsonl_bytes(results)
    try:
        s3.put_object(Bucket=S3_BUCKET, Key=key, Body=body, ContentType="application/json")
        logger.info("s3.put.ok", extra={"bucket": S3_BUCKET, "key": key, "bytes": len(body)})
        return True
    except Exception:
        logger.exception("s3.put.error", extra={"bucket": S3_BUCKET, "key": key})
        return False
