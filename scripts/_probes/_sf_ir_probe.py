#!/usr/bin/env python3
"""Probe 삼성화재 IR result page (+ capture file/api URLs) to find factsheet/PDF."""
import json, sys, time, re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
sys.stdout.reconfigure(encoding="utf-8")

URLS = [
    "https://www.samsungfire.com/sfmi/ui/m/etcsv/market/ir/MO_IR_result_report.html",
    "https://www.samsungfire.com/vh/page/VH.HPMK0201.do",
]
opts = Options()
opts.add_argument("--headless=new"); opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage"); opts.add_argument("--window-size=1400,2400")
opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})
d = webdriver.Chrome(options=opts)
try:
    for u in URLS:
        try:
            d.get(u); time.sleep(6)
        except Exception as e:
            print("GET fail", u, e); continue
        print(f"\n==== {u}  (rendered {len(d.page_source)}) ====")
        # network file/api urls
        urls=set()
        for entry in d.get_log("performance"):
            try: m=json.loads(entry["message"])["message"]
            except: continue
            if m.get("method") in ("Network.requestWillBeSent","Network.responseReceived"):
                p=m.get("params",{}); url=(p.get("request") or {}).get("url") or (p.get("response") or {}).get("url")
                if url and any(k in url.lower() for k in ('.xlsx','.pdf','.xls','file','down','/api','list','board','ir')):
                    if 'samsungfire' in url or '.xlsx' in url or '.pdf' in url: urls.add(url)
        print("-- net file/api urls --")
        for x in sorted(urls)[:25]: print("  ",x[:150])
        # anchors/buttons
        print("-- download-ish elements --")
        for e in d.find_elements(By.XPATH,"//a[@href]|//*[@onclick]|//button")[:200]:
            try:
                href=e.get_attribute("href") or ""; onc=e.get_attribute("onclick") or ""; txt=(e.text or "").strip()[:35]
                blob=(href+onc+txt).lower()
                if any(k in blob for k in ('xlsx','.pdf','down','fact','다운','분기','실적','release','연간')):
                    print(f"   txt={txt!r} href={href[:80]!r} onclick={onc[:80]!r}")
            except: continue
finally:
    d.quit()
