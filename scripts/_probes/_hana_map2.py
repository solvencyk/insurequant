# -*- coding: utf-8 -*-
"""Hana FN databook/presentations/factsheet: click each year tab, read the
quarter rows and their download links via JS. Prints JSON {year: [{label, url}]}.
Read-only."""
import sys, time, json
sys.stdout.reconfigure(encoding="utf-8")
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

URLS = {
    "databook": "https://www.hanafn.com/ir/financial/databookDetail.do",
    "present": "https://www.hanafn.com/ir/info/presentationsList.do",
    "factsheet": "https://www.hanafn.com/ir/info/factSheet.do",
}

JS = r"""
const out = {};
// find anchors whose onclick has downloadFile(...crossDownload...)
const anchors = Array.from(document.querySelectorAll('a'));
const dls = anchors.filter(a => /crossDownload/.test(a.getAttribute('onclick')||'') || /crossDownload/.test(a.getAttribute('href')||''));
function urlOf(a){
  const oc=a.getAttribute('onclick')||''; let m=oc.match(/downloadFile\(['"]([^'"]+)['"]/); if(m) return m[1];
  const hr=a.getAttribute('href')||''; if(/crossDownload/.test(hr)) return hr; return '';
}
// For each dl anchor, walk up to a row container and grab nearby text (label)
const rows=[];
for(const a of dls){
  let node=a, label='';
  for(let i=0;i<6 && node;i++){
    node=node.parentElement;
    if(!node) break;
    const t=(node.innerText||'').trim();
    if(t && t.length<160 && /(분기|반기|Q|Databook|연간|상반기|하반기|발표|실적|Factsheet|Fact)/i.test(t)){ label=t.replace(/\n/g,' | '); break; }
  }
  rows.push({label: label, url: urlOf(a), self: (a.innerText||'').trim()});
}
return JSON.stringify(rows);
"""

def make_driver():
    o = Options()
    o.add_argument("--headless=new"); o.add_argument("--no-sandbox")
    o.add_argument("--disable-dev-shm-usage"); o.add_argument("--window-size=1400,3000")
    o.add_argument("--ignore-certificate-errors")
    o.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
    return webdriver.Chrome(options=o)

def run(key):
    d = make_driver()
    try:
        d.get(URLS[key]); time.sleep(7)
        # click year tabs 2023-2026 if present to load their content
        for yr in ("2026","2025","2024","2023"):
            try:
                els = d.find_elements("xpath", f"//a[normalize-space(text())='{yr}'] | //button[normalize-space(text())='{yr}'] | //li[normalize-space(text())='{yr}']")
                for e in els[:1]:
                    d.execute_script("arguments[0].click();", e); time.sleep(3)
                    res = d.execute_script(JS)
                    print(f"### YEAR TAB {yr}")
                    print(res)
            except Exception as ex:
                print(f"### YEAR {yr} ERR {ex!r}")
        # also a default dump
        print("### DEFAULT")
        print(d.execute_script(JS))
    except Exception as e:
        print("ERROR", repr(e))
    finally:
        d.quit()

if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv)>1 else "databook")
