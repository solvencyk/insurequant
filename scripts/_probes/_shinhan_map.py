# -*- coding: utf-8 -*-
"""Shinhan FG IR: render overview/finance pages, enumerate the quarterly earnings
list and map each row to its PDF/XLS downloadAttach links. Read-only; prints JSON."""
import sys, time, json
sys.stdout.reconfigure(encoding="utf-8")
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

URLS = {
    "overview": "https://shinhangroup.com/kr/ir/overview",
    "earnings": "https://shinhangroup.com/kr/ir/earnings",
    "finance": "https://shinhangroup.com/kr/ir/finance",
    "library": "https://shinhangroup.com/kr/ir/library",
    "fb": "http://www.shinhangroup.com/kr/invest/finance/factBook.jsp",
}

JS = r"""
const anchors = Array.from(document.querySelectorAll('a'));
const dls = anchors.filter(a => /downloadAttach/.test(a.getAttribute('href')||''));
const rows=[];
for(const a of dls){
  let node=a, label='';
  for(let i=0;i<7 && node;i++){
    node=node.parentElement; if(!node) break;
    const t=(node.innerText||'').trim();
    if(t && t.length<200 && /(분기|반기|실적|연간|발표|Q|Fact|Book)/i.test(t)){ label=t.replace(/\s+/g,' '); break; }
  }
  rows.push({label, href:a.getAttribute('href'), self:(a.innerText||'').trim()});
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
        d.get(URLS[key]); time.sleep(8)
        print("CURURL", d.current_url, "| TITLE", d.title)
        # try to expand any "more"/list pagination by scrolling
        for _ in range(4):
            d.execute_script("window.scrollTo(0, document.body.scrollHeight);"); time.sleep(1.5)
        body=d.find_element("tag name","body").text
        rel=[l.strip() for l in body.splitlines() if l.strip() and any(y in l for y in ("2023","2024","2025","2026")) and any(k in l for k in ("분기","실적","연간","Fact","Book","발표"))]
        print("DATE LINES:", json.dumps(rel[:40], ensure_ascii=False))
        print("DLROWS:", d.execute_script(JS))
    except Exception as e:
        print("ERROR", repr(e))
    finally:
        d.quit()

if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv)>1 else "earnings")
