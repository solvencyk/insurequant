#!/usr/bin/env python3
"""Test 동양생명 downloadFile endpoint: seed cookies from a headless browser
session, then POST /api/fileUp/downloadFile with a known fileIndvcsId and inspect
the response (status, content-type, content-disposition, first bytes)."""
import json
import sys
import time

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

sys.stdout.reconfigure(encoding="utf-8")

EN = "https://www.myangel.co.kr/Company/En/Ir/CoIrMat"
DL = "https://www.myangel.co.kr/api/fileUp/downloadFile"


def driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.page_load_strategy = "eager"
    return webdriver.Chrome(options=opts)


d = driver()
d.set_page_load_timeout(40)
ua = d.execute_script("return navigator.userAgent")
try:
    try:
        d.get(EN)
    except Exception:
        pass
    time.sleep(6)
    cookies = d.get_cookies()
finally:
    d.quit()

s = requests.Session()
for c in cookies:
    s.cookies.set(c["name"], c["value"], domain=c.get("domain"))
hdr = {
    "User-Agent": ua,
    "Content-Type": "application/json;charset=UTF-8",
    "Referer": EN,
    "Origin": "https://www.myangel.co.kr",
    "Accept": "*/*",
}


def body(file_indvcs_id):
    return {"header": {"svcType": "PC", "sndTime": time.strftime("%Y%m%d%H%M%S"),
                       "befoScrnId": "", "userTmunIdnfVal": "", "tempSndData1": "",
                       "tempSndData2": "", "csPk": "", "bizRstCod": "", "bizRstMsg": "",
                       "ipAddr": ""},
            "payload": {"fileIndvcsId": file_indvcs_id}}


for label, fid in (("PDF FY2026.1Q EN", "CPY720260427001848842001"),
                   ("XLS FY2026.1Q EN", "ONT420260427001848843001")):
    try:
        r = s.post(DL, data=json.dumps(body(fid)), headers=hdr, timeout=60, verify=False)
        ct = r.headers.get("Content-Type", "")
        cd = r.headers.get("Content-Disposition", "")
        head = r.content[:8]
        print(f"{label}: status={r.status_code} len={len(r.content)} ct={ct!r}")
        print(f"   content-disposition={cd!r}")
        print(f"   first bytes={head!r}")
    except Exception as e:
        print(f"{label}: ERR {e}")
