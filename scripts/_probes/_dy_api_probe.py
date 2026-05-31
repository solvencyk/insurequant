#!/usr/bin/env python3
"""동양생명: capture the real selectListIrData POST body + the file-download
request triggered by clicking an XLS button. Uses CDP Network domain to read
request postData and all request URLs."""
import json
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

sys.stdout.reconfigure(encoding="utf-8")

URL = "https://www.myangel.co.kr/Company/En/Ir/CoIrMat"


def driver(dl_dir=None):
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,4000")
    opts.page_load_strategy = "eager"
    opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    if dl_dir:
        opts.add_experimental_option("prefs", {
            "download.default_directory": dl_dir,
            "download.prompt_for_download": False,
        })
    return webdriver.Chrome(options=opts)


d = driver()
d.set_page_load_timeout(40)
try:
    try:
        d.get(URL)
    except Exception as e:
        print("get warn", e)
    time.sleep(7)
    print("URL:", d.current_url)

    # dump performance log: find selectListIrData request + its postData via CDP
    logs = d.get_log("performance")
    req_ids = {}
    for entry in logs:
        msg = json.loads(entry["message"])["message"]
        if msg["method"] == "Network.requestWillBeSent":
            p = msg["params"]
            u = p.get("request", {}).get("url", "")
            if "selectListIrData" in u or "irData" in u:
                req_ids[p["requestId"]] = p["request"]
    print("\n== selectListIrData requests ==")
    for rid, req in req_ids.items():
        print("  method:", req.get("method"), "url:", req.get("url"))
        print("  postData:", req.get("postData"))

    # Use CDP to get response body of the API
    print("\n== try CDP response bodies ==")
    for rid in req_ids:
        try:
            body = d.execute_cdp_cmd("Network.getResponseBody", {"requestId": rid})
            txt = body.get("body", "")
            print(f"  [{rid}] {txt[:2500]}")
        except Exception as e:
            print(f"  [{rid}] body err: {e}")

    # Click first XLS button and capture resulting requests
    print("\n== click first XLS, capture download request ==")
    btns = d.find_elements(By.XPATH, "//button[normalize-space(text())='XLS']")
    print("XLS buttons:", len(btns))
    if btns:
        d.execute_script("arguments[0].scrollIntoView({block:'center'});", btns[0])
        d.execute_script("arguments[0].click();", btns[0])
        time.sleep(4)
        logs2 = d.get_log("performance")
        for entry in logs2:
            msg = json.loads(entry["message"])["message"]
            if msg["method"] == "Network.requestWillBeSent":
                p = msg["params"]
                u = p.get("request", {}).get("url", "")
                if any(k in u for k in ["file", "File", "down", "Down", "atch", "Atch", "irData", "blob"]):
                    print("  REQ", p["request"].get("method"), u[:160])
                    pd = p["request"].get("postData")
                    if pd:
                        print("       postData:", pd[:300])
finally:
    d.quit()
