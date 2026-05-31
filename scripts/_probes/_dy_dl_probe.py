#!/usr/bin/env python3
"""동양생명: (1) fetch KR list via API from inside page (full JSON to learn XLS
file fields), (2) click a PDF and an XLS button and capture the file-download
request URL + method + postData."""
import json
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

sys.stdout.reconfigure(encoding="utf-8")

URL = "https://www.myangel.co.kr/Company/Ir/CoIrMat"  # try KR app route via nav
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
try:
    try:
        d.get(EN)
    except Exception as e:
        print("get warn", e)
    time.sleep(7)
    print("URL:", d.current_url)

    # 1) fetch KR list (lang KR) and dump first item fully + any XLS in mFileLst
    js = r"""
    var done = arguments[arguments.length-1];
    var body = {"header":{"svcType":"PC","sndTime":"20260530000000","befoScrnId":"","userTmunIdnfVal":"","tempSndData1":"","tempSndData2":"","csPk":"","bizRstCod":"","bizRstMsg":"","ipAddr":""},
      "payload":{"inqIrRefrSecd":"2","exsCnt":3,"inqUseLanTypCod":"KR","pageNo":1,"pageSize":30}};
    fetch('/api/irData/selectListIrData',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),credentials:'include'})
      .then(r=>r.text()).then(t=>done(t)).catch(e=>done('ERR '+e));
    """
    res = d.execute_async_script(js)
    try:
        obj = json.loads(res)
        items = obj.get("payload", {}).get("irDataList", [])
        print(f"\n== KR list: {obj.get('payload',{}).get('totCnt')} total, {len(items)} returned ==")
        for it in items:
            files = it.get("mFileLst", [])
            fdesc = [(f.get("savViewImgNm"), f.get("fileFextNam"), f.get("fileGrpId"), f.get("fileIndvcsId"), f.get("fileSize")) for f in files]
            print(f"  {it.get('dataTitl')!r} ymd={it.get('pbanoYmd')} irRefrPk={it.get('irRefrPk')} "
                  f"fileGrpId={it.get('fileGrpId')} irDataFileIndvcsId={it.get('irDataFileIndvcsId')}")
            for fn, ext, fg, fi, sz in fdesc:
                print(f"        FILE {fn!r} ext={ext} grp={fg} indv={fi} size={sz}")
    except Exception as e:
        print("parse err", e, res[:500])

    # 2) click a PDF then XLS button, capture download request
    for label in ("PDF", "XLS"):
        d.get_log("performance")  # clear
        btns = d.find_elements(By.XPATH, f"//button[normalize-space(text())='{label}']")
        print(f"\n== {label} buttons: {len(btns)} ==")
        if not btns:
            continue
        try:
            d.execute_script("arguments[0].scrollIntoView({block:'center'});", btns[0])
            d.execute_script("arguments[0].click();", btns[0])
        except Exception as e:
            print("click err", e)
        time.sleep(4)
        logs = d.get_log("performance")
        for entry in logs:
            msg = json.loads(entry["message"])["message"]
            if msg["method"] == "Network.requestWillBeSent":
                p = msg["params"]
                u = p.get("request", {}).get("url", "")
                if any(k in u for k in ["file", "File", "down", "Down", "atch", "Atch", "blob", "irData"]):
                    print("  REQ", p["request"].get("method"), u[:170])
                    pd = p["request"].get("postData")
                    if pd:
                        print("       postData:", pd[:400])
finally:
    d.quit()
