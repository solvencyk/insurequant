# -*- coding: utf-8 -*-
"""Render Hana FN databook + presentations pages and map each download link to
its row's quarter label by walking list items. Read-only; prints JSON."""
import sys, time, json
sys.stdout.reconfigure(encoding="utf-8")
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

URLS = {
    "databook": "https://www.hanafn.com/ir/financial/databookDetail.do",
    "present": "https://www.hanafn.com/ir/info/presentationsList.do",
    "factsheet": "https://www.hanafn.com/ir/info/factSheet.do",
}

def make_driver():
    o = Options()
    o.add_argument("--headless=new"); o.add_argument("--no-sandbox")
    o.add_argument("--disable-dev-shm-usage"); o.add_argument("--window-size=1400,3000")
    o.add_argument("--ignore-certificate-errors")
    o.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
    return webdriver.Chrome(options=o)

def dump(key):
    d = make_driver()
    out = []
    try:
        d.get(URLS[key]); time.sleep(7)
        # try clicking any year filters/tabs to expand all years (best-effort)
        # collect list items
        for li in d.find_elements(By.CSS_SELECTOR, "li, tr, div"):
            txt = (li.text or "").strip()
            if not txt:
                continue
            if not any(y in txt for y in ("2023","2024","2025","2026")):
                continue
            links = []
            for a in li.find_elements(By.TAG_NAME, "a"):
                oc = a.get_attribute("onclick") or ""
                hr = a.get_attribute("href") or ""
                at = (a.text or "").strip()
                if "crossDownload" in oc or "crossDownload" in hr or "download" in (oc+hr).lower():
                    links.append({"t": at, "onclick": oc[:200], "href": hr[:200]})
            if links and len(txt) < 200:
                out.append({"row": txt[:120], "links": links})
    except Exception as e:
        out = [{"ERROR": repr(e)}]
    finally:
        d.quit()
    # dedup
    seen=set(); uniq=[]
    for r in out:
        k=json.dumps(r,ensure_ascii=False)
        if k not in seen:
            seen.add(k); uniq.append(r)
    print(json.dumps({"key":key,"rows":uniq}, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    dump(sys.argv[1] if len(sys.argv)>1 else "databook")
