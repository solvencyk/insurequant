#!/usr/bin/env python3
"""Probe: harvest 미래에셋생명 fileDownload args per year + render 동양생명 IR list."""
import re
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

sys.stdout.reconfigure(encoding="utf-8")


def driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,3000")
    return webdriver.Chrome(options=opts)


def probe_mirae():
    url = "https://life.miraeasset.com/micro/company/PC-HO-060401-000000.do"
    d = driver()
    try:
        d.get(url)
        time.sleep(6)
        sel_el = d.find_element(By.TAG_NAME, "select")
        years = [o.get_attribute("value") or o.text.strip()
                 for o in sel_el.find_elements(By.TAG_NAME, "option")]
        years = [y for y in years if y.isdigit()]
        print("MIRAE years:", years)
        for y in years:
            try:
                Select(sel_el).select_by_value(y)
            except Exception:
                # select by visible text
                Select(sel_el).select_by_visible_text(y)
            time.sleep(3)
            # re-fetch select element (DOM may rebuild)
            try:
                sel_el = d.find_element(By.TAG_NAME, "select")
            except Exception:
                pass
            src = d.page_source
            calls = re.findall(r"fileDownload\('([^']+)','([^']+)'\)", src)
            titles = re.findall(r'box-list-tit">([^<]+)<', src)
            print(f"\n--- MIRAE year {y}: {len(calls)} fileDownload, titles={titles[:12]}")
            for org, lst in calls:
                print(f"    {org!r} | {lst!r}")
    finally:
        d.quit()


def probe_dy():
    for url in [
        "https://www.myangel.co.kr/paging/WE_AC_WECIRM050505L?sic=2",
        "https://www.myangel.co.kr/paging/WE_AC_WECIRM050505L",
    ]:
        d = driver()
        try:
            d.get(url)
            time.sleep(6)
            print(f"\n===== DY :: {url} -> {d.current_url} =====")
            print("TITLE:", d.title)
            src = d.page_source
            for kw in ["fileDown", "download", "Fact", "실적", "fn_", "javascript:", ".xls", ".pdf"]:
                idxs = [m.start() for m in re.finditer(re.escape(kw), src)][:2]
                for i in idxs:
                    print(f"  [{kw}] ...{src[max(0,i-120):i+160]}...".replace("\n", " "))
            # anchors / onclicks
            els = d.find_elements(By.XPATH, "//a[@onclick] | //a[@href] | //button[@onclick] | //td")
            print("-- candidate rows --")
            n = 0
            for e in els:
                txt = (e.text or "").strip().replace("\n", " ")
                oc = e.get_attribute("onclick") or ""
                href = e.get_attribute("href") or ""
                if any(k in (txt + oc + href) for k in
                       ["다운", "Down", "Fact", "실적", "20", "fn_", ".xls", ".pdf", "file"]):
                    if txt or oc:
                        print(f"   txt={txt[:55]!r} oc={oc[:110]!r} href={href[:90]!r}")
                        n += 1
                if n > 60:
                    break
        finally:
            d.quit()


if __name__ == "__main__":
    probe_mirae()
    probe_dy()
