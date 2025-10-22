# scrape_and_summarize.py — RSS → HTML → OpenAI (local y Lambda)
import os, time, hashlib, json, requests, feedparser
from dateutil import parser as dateparser
from bs4 import BeautifulSoup

OPENAI_URL = "https://api.openai.com/v1/responses"
API_KEY = os.environ.get("OPENAI_API_KEY") or ""

RSS_FEEDS = [
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "https://www.reuters.com/finance/markets/rss"
]

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

def fetch_article_text(url, timeout=25):
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent":"Mozilla/5.0"})
        r.raise_for_status()
    except Exception:
        return ""
    try:
        soup = BeautifulSoup(r.text, "html.parser")
        for sel in ["article", "main", "div#main-content", "div.article__content", "div#content"]:
            node = soup.select_one(sel)
            if node:
                txt = " ".join(node.get_text(" ", strip=True).split())
                if len(txt) >= 200:
                    return txt[:8000]
        txt = " ".join(soup.get_text(" ", strip=True).split())
        return txt[:8000]
    except Exception:
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
    r = requests.post(OPENAI_URL, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=payload, timeout=40)
    try:
        r.raise_for_status()
        j = r.json()
        text = robust_openai_extract(j)
        return text if text.strip() else f"(respuesta cruda)\n{j}"
    except requests.HTTPError as e:
        return f"ERROR HTTP {e.response.status_code}: {e.response.text[:400]}"
    except Exception as e:
        return f"ERROR: {e}"

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
    all_entries = []
    for feed in RSS_FEEDS:
        try:
            all_entries.extend(fetch_rss(feed))
        except Exception:
            pass
        time.sleep(0.2)
    all_entries = dedupe(all_entries)
    all_entries.sort(key=lambda x: x.get("published") or "", reverse=True)
    top = all_entries[:top_n]
    results = []
    for e in top:
        body = fetch_article_text(e["link"]) or e["summary"]
        summary = summarize_with_openai(e["title"], e["link"], body)
        results.append({"title": e["title"], "link": e["link"], "published": e.get("published"), "summary": summary})
        time.sleep(0.3)
    return results

def lambda_handler(event, context):
    results = run_once(top_n=5)
    outpath = "/tmp/scraped_summaries.jsonl"
    with open(outpath, "a", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return {"statusCode": 200, "body": results}

if __name__ == "__main__":
    results = run_once(top_n=5)
    with open("scraped_summaries.jsonl", "a", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

