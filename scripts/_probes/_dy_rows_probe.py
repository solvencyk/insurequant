#!/usr/bin/env python3
"""동양생명: map each list row -> (title, has PDF btn, has XLS btn) and find the
pagination control / how many rows render. Print row container HTML skeleton."""
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
    opts.add_argument("--window-size=1400,6000")
    opts.page_load_strategy = "eager"
    return webdriver.Chrome(options=opts)


d = driver()
d.set_page_load_timeout(40)
try:
    try:
        d.get(EN)
    except Exception:
        pass
    time.sleep(7)
    # Use JS to walk rows: each PDF/XLS button's nearest row title
    info = d.execute_script(r"""
    function rowTitle(btn){
      var el = btn;
      for(var i=0;i<8 && el;i++){
        el = el.parentElement;
        if(!el) break;
        // find a title-ish text within this container
        var t = el.querySelector('strong, .tit, .title, h3, h4, .subject, a');
        if(t && t.textContent.trim().length>4 && /FY|Earnings|Factsheet|Presentation/i.test(t.textContent)){
          return t.textContent.trim();
        }
      }
      // fallback: scan container text
      el = btn.closest('li, tr, .item, .list-item, div');
      return el ? el.textContent.trim().slice(0,80) : '';
    }
    var out = [];
    document.querySelectorAll('button').forEach(function(b){
      var lbl=b.textContent.trim();
      if(lbl==='PDF'||lbl==='XLS'){
        out.push({label:lbl, title:rowTitle(b)});
      }
    });
    // pagination
    var pag = [];
    document.querySelectorAll('.pagination a, .paging a, [class*=page] a, .pagination button').forEach(function(a){
      pag.push(a.textContent.trim());
    });
    return {rows: out, totalButtons: document.querySelectorAll('button').length, pagination: pag, bodyLen: document.body.innerText.length};
    """)
    print("totalButtons:", info["totalButtons"], "| pagination:", info["pagination"])
    print(f"{len(info['rows'])} PDF/XLS buttons:")
    for r in info["rows"]:
        print(f"   {r['label']:3s}  {r['title'][:70]!r}")
finally:
    d.quit()
