# -*- coding: utf-8 -*-
"""Inspect the Hanwha Life 실적발표자료 list DOM in detail: dump full body text,
and every element carrying a click handler / data attr that could trigger a
file download. Hanwha Life IR is a Next.js SPA."""
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

sys.stdout.reconfigure(encoding="utf-8")

URL = "https://company.hanwhalife.com/ko/investment/investor/earnings-release"

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--window-size=1400,5000")
opts.add_argument("--lang=ko-KR")
d = webdriver.Chrome(options=opts)
try:
    d.get(URL)
    time.sleep(9)
    print("FINAL:", d.current_url)
    body = d.find_element(By.TAG_NAME, "body").text
    print("===== BODY TEXT =====")
    print(body[:4000])
    print("===== /BODY =====")
    # any element with download / data-file / button-ish role
    print("\n===== clickable / download candidates =====")
    els = d.find_elements(
        By.XPATH,
        "//*[@onclick or @data-file or @data-url or @download or "
        "contains(@class,'down') or contains(@class,'btn') or "
        "contains(@class,'excel') or contains(@class,'file')]",
    )
    seen = set()
    for e in els[:120]:
        try:
            tag = e.tag_name
            cls = e.get_attribute("class") or ""
            txt = (e.text or "").strip().replace("\n", " ")[:50]
            href = e.get_attribute("href") or ""
            oc = e.get_attribute("onclick") or ""
            dl = e.get_attribute("download") or ""
            df = e.get_attribute("data-file") or e.get_attribute("data-url") or ""
        except Exception:
            continue
        key = (tag, cls, txt, href, oc, df)
        if key in seen:
            continue
        seen.add(key)
        if any(k in (cls + " " + txt + " " + href + " " + oc + " " + dl + " " + df).lower()
               for k in ["down", "excel", "엑셀", "xls", "pdf", "file", "btn", "다운"]):
            print(f"  {tag} cls={cls[:30]!r} txt={txt!r} href={href[:55]} oc={oc[:45]} df={df[:45]} dl={dl[:30]}")
    # dropdown / select for year filter?
    print("\n===== selects =====")
    for s in d.find_elements(By.TAG_NAME, "select"):
        print("  SELECT", repr((s.text or "").replace("\n", " ")[:120]))
    print("\n===== buttons text dump =====")
    for b in d.find_elements(By.TAG_NAME, "button"):
        t = (b.text or "").strip().replace("\n", " ")
        if t:
            print("  BTN", repr(t[:60]))
finally:
    d.quit()
