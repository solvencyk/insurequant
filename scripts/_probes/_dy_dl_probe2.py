#!/usr/bin/env python3
"""동양생명: reliably click first XLS + first PDF button (single JS pass), capture
ALL network requests after each click to learn the file-download endpoint + params.
Also try a detail API to find the XLS factsheet file ids."""
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
d.set_script_timeout(30)


def dump_requests_after(tag):
    time.sleep(4)
    logs = d.get_log("performance")
    print(f"-- requests after {tag} --")
    seen = set()
    for entry in logs:
        msg = json.loads(entry["message"])["message"]
        if msg["method"] == "Network.requestWillBeSent":
            p = msg["params"]
            req = p.get("request", {})
            u = req.get("url", "")
            if u.startswith("data:") or u.endswith((".js", ".css", ".png", ".woff", ".woff2", ".svg")):
                continue
            if u in seen:
                continue
            seen.add(u)
            if any(k in u for k in ["api/", "file", "File", "down", "Down", "atch", "Atch", "blob", "irData"]):
                print("   ", req.get("method"), u[:170])
                pd = req.get("postData")
                if pd:
                    print("        postData:", pd[:400])


try:
    try:
        d.get(EN)
    except Exception as e:
        print("get warn", e)
    time.sleep(7)
    print("URL:", d.current_url)

    # click first XLS via JS, then first PDF; capture network each time
    for label in ("XLS", "PDF"):
        d.get_log("performance")  # clear
        clicked = d.execute_script(
            """
            var lbl = arguments[0];
            var btns = Array.from(document.querySelectorAll('button')).filter(b=>b.textContent.trim()===lbl);
            if(!btns.length) return 'no '+lbl+' buttons (total buttons='+document.querySelectorAll('button').length+')';
            btns[0].scrollIntoView({block:'center'});
            btns[0].click();
            return 'clicked '+lbl+' (n='+btns.length+')';
            """, label)
        print(clicked)
        dump_requests_after(label)

    # Also: fetch detail for the first FY2026 1Q item to see if XLS factsheet present
    print("\n== detail API guesses for FY2026 1Q (irRefrPk 20260427100000265 EN) ==")
    for ep in ("/api/irData/selectIrData", "/api/irData/selectIrDataDtl", "/api/irData/detailIrData"):
        js = """
        var done = arguments[arguments.length-1]; var ep = arguments[0];
        var body={"header":{"svcType":"PC","sndTime":"20260530000000","ipAddr":""},
          "payload":{"irRefrPk":"20260427100000265","inqIrRefrSecd":"2","inqUseLanTypCod":"EN"}};
        fetch(ep,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),credentials:'include'})
          .then(r=>r.text()).then(t=>done(ep+' => '+t.slice(0,1200))).catch(e=>done(ep+' ERR '+e));
        """
        try:
            print(d.execute_async_script(js, ep))
        except Exception as e:
            print(ep, "err", e)
finally:
    d.quit()
