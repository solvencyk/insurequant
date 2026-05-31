#!/usr/bin/env python3
"""Capture the EXACT request headers the SPA sends to /api/fileUp/downloadFile
on a real button click (to find the auth header my raw fetch omits)."""
import json
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

sys.stdout.reconfigure(encoding="utf-8")

EN = "https://www.myangel.co.kr/Company/En/Ir/CoIrMat"


def driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,5000")
    opts.page_load_strategy = "eager"
    opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    return webdriver.Chrome(options=opts)


d = driver()
d.set_page_load_timeout(40)
try:
    try:
        d.get(EN)
    except Exception:
        pass
    time.sleep(7)
    d.get_log("performance")  # clear
    d.execute_script("""
      var b = Array.from(document.querySelectorAll('button')).filter(x=>x.textContent.trim()==='PDF')[0];
      b.scrollIntoView({block:'center'}); b.click();
    """)
    time.sleep(4)
    logs = d.get_log("performance")
    for entry in logs:
        msg = json.loads(entry["message"])["message"]
        if msg["method"] == "Network.requestWillBeSent":
            p = msg["params"]
            u = p.get("request", {}).get("url", "")
            if "downloadFile" in u:
                req = p["request"]
                print("URL:", u)
                print("METHOD:", req.get("method"))
                print("HEADERS:")
                for k, v in (req.get("headers") or {}).items():
                    print(f"   {k}: {str(v)[:120]}")
                print("POSTDATA:", req.get("postData"))
finally:
    d.quit()
