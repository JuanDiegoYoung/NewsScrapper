
import time, hashlib
import requests
import feedparser
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --------------------
# 1) SCRAPING VÍA RSS
# --------------------
RSS_FEEDS = [
    "https://www.reuters.com/finance/markets/rss",   # Reuters Markets (RSS oficial)
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",  # CNBC Top News (RSS)
]

def fetch_rss(url, timeout=20):
    """Descarga y parsea un feed RSS, devuelve lista de dicts normalizados."""
    d = feedparser.parse(url)
    out = []
    for e in d.entries:
        link = e.get("link") or e.get("id") or ""
        title = (e.get("title") or "").strip()
        summary = (e.get("summary") or e.get("description") or "").strip()
        published = None
        for k in ("published", "updated", "pubDate"):
            if e.get(k):
                published = e.get(k)
                break
        uid = hashlib.sha1((link + title).encode()).hexdigest()
        out.append({
            "uid": uid, "title": title, "summary": summary,
            "link": link, "published": published, "_source": url
        })
    return out

# --------------------------------
# 2) SCRAPING VÍA HTML (BeautifulSoup)
# --------------------------------
HTML_TARGETS = [
    # (url, css_selector_de_items, css_selector_de_título_relativo, css_selector_de_link_relativo)
    ("https://www.reuters.com/markets/", "article", "h3, h2, a[aria-label]", "a"),
    ("https://www.marketwatch.com/latest-news", "div.article__content", "h3, h2, a", "a"),
]

def fetch_html_list(url, item_sel, title_sel, link_sel, timeout=20):
    """Descarga HTML y extrae lista de (título, link) usando selectores CSS simples."""
    r = requests.get(url, timeout=timeout, headers={"User-Agent":"Mozilla/5.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    items = []
    for it in soup.select(item_sel):
        title_el = it.select_one(title_sel)
        link_el = it.select_one(link_sel)
        title = None
        href = None
        if title_el:
            # texto del título (limpiando espacios)
            title = " ".join(title_el.get_text(strip=True).split())
        if link_el and link_el.get("href"):
            href = urljoin(url, link_el["href"])
        if title and href:
            uid = hashlib.sha1((href + title).encode()).hexdigest()
            items.append({"uid": uid, "title": title, "link": href, "_source": url})
    return items

# --------------------
# MAIN DEMO
# --------------------
if __name__ == "__main__":
    print("=== RSS ===")
    rss_all = []
    for feed in RSS_FEEDS:
        try:
            batch = fetch_rss(feed)
            rss_all.extend(batch)
            print(f"[OK] {feed} → {len(batch)} items")
        except Exception as e:
            print(f"[FAIL] {feed}: {e}")
        time.sleep(0.5)

    for it in rss_all[:8]:
        print(f"- {it['title']}\n  {it['link']}\n")

    print("\n=== HTML ===")
    html_all = []
    for url, item_sel, title_sel, link_sel in HTML_TARGETS:
        try:
            batch = fetch_html_list(url, item_sel, title_sel, link_sel)
            html_all.extend(batch)
            print(f"[OK] {url} → {len(batch)} items")
        except Exception as e:
            print(f"[FAIL] {url}: {e}")
        time.sleep(0.5)

    for it in html_all[:8]:
        print(f"- {it['title']}\n  {it['link']}\n")