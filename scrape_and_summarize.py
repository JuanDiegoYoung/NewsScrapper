# scrape_and_summarize.py — RSS → HTML → OpenAI (local y Lambda)

import os, time, hashlib, json, requests, feedparser
from dateutil import parser as dateparser
from bs4 import BeautifulSoup
import boto3
from logger_utils import get_logger
from save_bucket import upload_results_to_s3

logger = get_logger(name="scraper")
ses = boto3.client("ses", region_name="us-east-1")

OPENAI_URL = "https://api.openai.com/v1/responses"
API_KEY = os.environ.get("OPENAI_API_KEY") or ""

RSS_FEEDS = [
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "https://www.reuters.com/finance/markets/rss"
]

def send_email(subject, body, recipient="young.juandiego@gmail.com"):
    t0 = time.time()
    logger.info("ses.send.start", extra={"recipient": recipient, "subject": subject[:80]})
    try:
        response = ses.send_email(
            Source=recipient,
            Destination={"ToAddresses": [recipient]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {"Text": {"Data": body, "Charset": "UTF-8"}}
            }
        )
        lat = round(time.time() - t0, 3)
        logger.info("ses.send.ok", extra={"recipient": recipient, "latency_s": lat, "message_id": response.get("MessageId")})
        return True
    except Exception as e:
        logger.exception("ses.send.error", extra={"recipient": recipient})
        return False

def fetch_article_text(url, timeout=25):
    logger.info("fetch_article.start", extra={"url": url})
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent":"Mozilla/5.0"})
        r.raise_for_status()
    except Exception:
        logger.exception("fetch_article.request_error", extra={"url": url})
        return ""
    try:
        soup = BeautifulSoup(r.text, "html.parser")
        for sel in ["article", "main", "div#main-content", "div.article__content", "div#content"]:
            node = soup.select_one(sel)
            if node:
                txt = " ".join(node.get_text(" ", strip=True).split())
                if len(txt) >= 200:
                    logger.info("fetch_article.done", extra={"url": url, "chars": len(txt)})
                    return txt[:8000]
        txt = " ".join(soup.get_text(" ", strip=True).split())
        logger.info("fetch_article.done_fallback", extra={"url": url, "chars": len(txt)})
        return txt[:8000]
    except Exception:
        logger.exception("fetch_article.parse_error", extra={"url": url})
        return ""

def robust_openai_extract(j):
    if isinstance(j, dict):
        if j.get("output_text"):
            return j["output_text"]
        if "output" in j and j["output"]:
            texts = []
            for block in j["output"]:
                content = block.get("content") or []
                for part in content:
                    if isinstance(part, dict) and part.get("text"):
                        texts.append(part["text"])
            if texts:
                return "\n".join(texts)
        if "choices" in j and j["choices"]:
            msg = j["choices"][0].get("message", {}).get("content")
            if msg:
                return msg
    return ""

def summarize_with_openai(title, url, body):
    if not API_KEY:
        logger.error("openai.missing_api_key")
        return "ERROR: falta OPENAI_API_KEY"
    prompt = (
        "Resumí en 2–3 líneas, listá 3 tópicos y tickers si aplica. Formato EXACTO:\n"
        "Resumen: ...\n"
        "Tópicos: a, b, c\n"
        "Tickers: ...\n\n"
        f"Título: {title}\nURL: {url}\n\nCuerpo:\n{body[:6000]}"
    )
    payload = {
        "model": "gpt-4.1-mini",
        "input": [
            {"role": "system", "content": "Sos un analista de noticias financieras, conciso y factual."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_output_tokens": 800
    }
    t0 = time.time()
    try:
        r = requests.post(OPENAI_URL, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=payload, timeout=40)
        r.raise_for_status()
        j = r.json()
        text = robust_openai_extract(j)
        logger.info("openai.ok", extra={"latency_s": round(time.time() - t0, 3), "title": title[:80]})
        return text if text.strip() else f"(respuesta cruda)\n{j}"
    except requests.HTTPError as e:
        logger.exception("openai.http_error", extra={"status": getattr(e.response, "status_code", None), "title": title[:80]})
        return f"ERROR HTTP {e.response.status_code}: {e.response.text[:400]}"
    except Exception as e:
        logger.exception("openai.error", extra={"title": title[:80]})
        return f"ERROR: {e}"
    

def fetch_rss(url):
    d = feedparser.parse(url)
    out = []
    for e in d.entries:
        link = e.get("link") or e.get("id") or ""
        title = (e.get("title") or "").strip()
        summary = (e.get("summary") or e.get("description") or "").strip()
        published = None
        for k in ("published", "updated", "pubDate"):
            if e.get(k):
                try:
                    published = dateparser.parse(e.get(k)).isoformat()
                except Exception:
                    published = e.get(k)
                break
        uid = hashlib.sha1((link + title).encode()).hexdigest()
        out.append({"uid": uid, "title": title, "summary": summary, "link": link, "published": published, "_source": url})
    return out


def dedupe(entries):
    seen = set()
    out = []
    for e in entries:
        if e["uid"] in seen:
            continue
        seen.add(e["uid"])
        out.append(e)
    return out

def run_once(top_n=5):
    logger.info("run_once.start", extra={"top_n": top_n, "feeds": len(RSS_FEEDS)})
    all_entries = []
    for feed in RSS_FEEDS:
        try:
            logger.info("fetch_rss.start", extra={"feed": feed})
            all_entries.extend(fetch_rss(feed))
            logger.info("fetch_rss.done", extra={"feed": feed})
        except Exception:
            logger.exception("fetch_rss.error", extra={"feed": feed})
        time.sleep(0.2)
    all_entries = dedupe(all_entries)
    all_entries.sort(key=lambda x: x.get("published") or "", reverse=True)
    top = all_entries[:top_n]
    results = []
    for e in top:
        logger.info("summarize.start", extra={"uid": e["uid"], "title": e["title"][:80], "link": e["link"]})
        body = fetch_article_text(e["link"]) or e["summary"]
        summary = summarize_with_openai(e["title"], e["link"], body)
        results.append({"title": e["title"], "link": e["link"], "published": e.get("published"), "summary": summary})
        logger.info("summarize.done", extra={"uid": e["uid"], "summary_len": len(summary)})
        time.sleep(0.3)
    logger.info("run_once.done", extra={"n_results": len(results)})
    return results

def lambda_handler(event, context):
    request_id = getattr(context, "aws_request_id", "local")
    logger.info("lambda.start", extra={"request_id": request_id})
    try:
        results = run_once(top_n=5)

        outpath = "/tmp/scraped_summaries.jsonl"
        with open(outpath, "a", encoding="utf-8") as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

        send_email(
            subject="Resultado ejecución Lambda finance-news-scraper",
            body=json.dumps(results, ensure_ascii=False, indent=2)
        )

        ok = upload_results_to_s3(results, request_id)
        if ok:
            logger.info("s3.success", extra={"request_id": request_id})
        else:
            logger.warning("s3.not_saved", extra={"request_id": request_id})

        logger.info("lambda.success", extra={"request_id": request_id, "n_results": len(results)})
        return {"statusCode": 200, "body": results}
    except Exception:
        logger.exception("lambda.failure", extra={"request_id": request_id})
        return {"statusCode": 500, "body": "internal error"}


if __name__ == "__main__":
    results = run_once(top_n=5)
    with open("scraped_summaries.jsonl", "a", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
