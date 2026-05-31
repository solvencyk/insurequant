#!/usr/bin/env python3
"""Probe 미래에셋생명 IR materials page DOM to discover download mechanics."""
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

sys.stdout.reconfigure(encoding="utf-8")
URL = "https://life.miraeasset.com/micro/company/PC-HO-060401-000000.do"

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--window-size=1400,3000")
d = webdriver.Chrome(options=opts)
try:
    d.get(URL)
    time.sleep(8)
    print("TITLE:", d.title)
    # year selector(s)
    for sel in d.find_elements(By.TAG_NAME, "select"):
        opts_txt = [o.text for o in sel.find_elements(By.TAG_NAME, "option")]
        print("SELECT id=", sel.get_attribute("id"), "name=", sel.get_attribute("name"), "opts=", opts_txt[:20])
    # tabs / section labels
    print("\n--- elements containing 실적발표 / Fact / 녹취 ---")
    for xp in ["실적발표", "Fact Sheet", "녹취"]:
        els = d.find_elements(By.XPATH, f"//*[contains(normalize-space(text()),'{xp}')]")
        print(f"[{xp}] count={len(els)}")
        for e in els[:6]:
            print("   tag=", e.tag_name, "| text=", repr(e.text[:60]), "| class=", e.get_attribute("class"))
    # download anchors / buttons
    print("\n--- download-ish anchors/buttons ---")
    cand = d.find_elements(By.XPATH, "//a | //button")
    shown = 0
    for e in cand:
        t = (e.text or "").strip()
        href = e.get_attribute("href") or ""
        onclick = e.get_attribute("onclick") or ""
        cls = e.get_attribute("class") or ""
        if any(k in (t + href + onclick + cls).lower() for k in
               ["download", "다운", "filedown", ".pdf", ".xls", "factsheet", "fnfile"]):
            print(f"  tag={e.tag_name} text={t[:30]!r} href={href[:90]!r} onclick={onclick[:90]!r} class={cls[:40]!r}")
            shown += 1
        if shown > 40:
            break
    # list rows
    print("\n--- list item rows (ul/li or table tr) snapshot ---")
    for li in d.find_elements(By.XPATH, "//li[contains(.,'실적') or contains(.,'Fact')]")[:10]:
        print("  LI:", repr(li.text[:80]))
finally:
    d.quit()
