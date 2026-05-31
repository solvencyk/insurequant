#!/usr/bin/env python3
"""Probe IRGO (irgo.co.kr) for a company's downloadable IR documents (factsheet/실적 PDF).
If IRGO exposes uniform per-company IR file downloads, it's a scalable source."""
import json, sys, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
sys.stdout.reconfigure(encoding="utf-8")

# 삼성화재 000810, 메리츠금융 138040 — try a couple
URLS = [
    "https://m.irgo.co.kr/IR-COMP/000810/-IR-PAGE",
    "https://irgo.co.kr/IR-COMP/000810",
    "https://www.irgo.co.kr/company/000810",
]
opts = Options()
opts.add_argument("--headless=new"); opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage"); opts.add_argument("--window-size=1300,2400")
opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})
d = webdriver.Chrome(options=opts)
try:
    for u in URLS:
        try:
            d.get(u); time.sleep(6)
        except Exception as e:
            print("GET fail", u, e); continue
        print(f"\n==== {u}  rendered={len(d.page_source)} title={d.title!r} ====")
        urls = set()
        for entry in d.get_log("performance"):
            try: m = json.loads(entry["message"])["message"]
            except: continue
            if m.get("method") in ("Network.requestWillBeSent", "Network.responseReceived"):
                p = m.get("params", {}); url = (p.get("request") or {}).get("url") or (p.get("response") or {}).get("url")
                if url and any(k in url.lower() for k in ('.pdf', '.xlsx', '.xls', 'file', 'down', '/api', 'ir', 'doc', 'attach')):
                    if 'irgo' in url or '.pdf' in url or '.xlsx' in url: urls.add(url)
        print("-- net file/api urls --")
        for x in sorted(urls)[:30]: print("  ", x[:150])
        print("-- download-ish elements --")
        seen = 0
        for e in d.find_elements(By.XPATH, "//a[@href]|//*[@onclick]|//button"):
            try:
                href = e.get_attribute("href") or ""; onc = e.get_attribute("onclick") or ""; txt = (e.text or "").strip()[:40]
                blob = (href + onc + txt).lower()
                if any(k in blob for k in ('.pdf', 'xlsx', 'down', '다운', '실적', 'fact', '자료', 'ir')):
                    print(f"   txt={txt!r} href={href[:90]!r} onclick={onc[:60]!r}"); seen += 1
                    if seen > 25: break
            except: continue
        if len(d.page_source) > 5000:
            break  # got a real render
finally:
    d.quit()
