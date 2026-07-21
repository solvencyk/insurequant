#!/usr/bin/env python3
"""동양생명 (KR0087) IR 자료실 크롤러.

myangel.co.kr IR Materials is a React SPA backed by JSON APIs:
  POST /api/irData/selectListIrData  (inqIrRefrSecd=2 => 실적발표자료)
  POST /api/fileUp/downloadFile      {payload:{fileIndvcsId}}

Each list item exposes TWO downloadable files:
  - Earnings Presentation PDF  -> fileIndvcsId = mFileLst[0].fileIndvcsId
  - Factsheet (XLS)            -> fileIndvcsId = item.irDataFileIndvcsId

Direct requests POST returns 401 (anti-bot/raon session), so we run the exact
fetch from INSIDE the rendered page (same origin/session/headers as the SPA),
read the blob as base64, and save it in Python.

Files -> data/ir/FY{YYYY}_Q{N}/KR0087_동양생명/<savViewImgNm>
Quarter map: 1분기/1Q->Q1, 상반기/1H->Q2, 3분기/3Q->Q3, annual('FY... 실적발표자료')->Q4.
Life insurer => FY == calendar year. Target FY2023.1Q ~ FY2026.1Q.
We fetch the KR list (Korean decks) and grab both PDF + XLS per quarter.
"""
import base64
import json
import re
import sys
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
KR_DIR = "KR0087_동양생명"
EN = "https://www.myangel.co.kr/Company/En/Ir/CoIrMat"
KR_PAGE = "https://www.myangel.co.kr/Company/Ir/CoIrMat"


def driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,3000")
    opts.page_load_strategy = "eager"
    return webdriver.Chrome(options=opts)


def quarter_from_title(t: str):
    if re.search(r"1\s*분기|\b1Q\b", t):
        return "Q1"
    if re.search(r"상반기|\b1H\b|2\s*분기|\b2Q\b", t):
        return "Q2"
    if re.search(r"3\s*분기|\b3Q\b", t):
        return "Q3"
    # 4분기 explicit (rare) else annual = Q4
    if re.search(r"4\s*분기|\b4Q\b", t):
        return "Q4"
    return "Q4"  # 'FY2024 실적발표자료' (annual)


def year_from_title(t: str):
    m = re.search(r"FY?\s*(\d{4})", t)
    return m.group(1) if m else None


def in_window(y, q):
    if not y:
        return False
    y = int(y)
    if y < 2023 or y > 2026:
        return False
    if y == 2026 and q != "Q1":
        return False
    return True


FETCH_LIST_JS = r"""
var done = arguments[arguments.length-1];
var lang = arguments[0];
var body = {"header":{"svcType":"PC","sndTime":"20260530000000","befoScrnId":"",
  "userTmunIdnfVal":"","tempSndData1":"","tempSndData2":"","csPk":"","bizRstCod":"",
  "bizRstMsg":"","ipAddr":""},
  "payload":{"inqIrRefrSecd":"2","exsCnt":3,"inqUseLanTypCod":lang,"pageNo":1,"pageSize":100}};
fetch('/api/irData/selectListIrData',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify(body),credentials:'include'})
  .then(r=>r.text()).then(t=>done(t)).catch(e=>done('ERR '+e));
"""

# download a file by fileIndvcsId, return base64 (or 'ERR ...')
FETCH_FILE_JS = r"""
var done = arguments[arguments.length-1];
var fid = arguments[0];
var body = {"header":{"svcType":"PC","sndTime":"20260530000000","befoScrnId":"",
  "userTmunIdnfVal":"","tempSndData1":"","tempSndData2":"","csPk":"","bizRstCod":"",
  "bizRstMsg":"","ipAddr":""},"payload":{"fileIndvcsId":fid}};
fetch('/api/fileUp/downloadFile',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify(body),credentials:'include'})
  .then(function(r){ return r.arrayBuffer().then(function(buf){
      return {ct:r.headers.get('Content-Type')||'', status:r.status, buf:buf};
  });})
  .then(function(o){
      var bytes = new Uint8Array(o.buf); var bin='';
      for(var i=0;i<bytes.length;i++){ bin += String.fromCharCode(bytes[i]); }
      done(JSON.stringify({status:o.status, ct:o.ct, b64: btoa(bin), len: bytes.length}));
  }).catch(e=>done('ERR '+e));
"""


def main():
    d = driver()
    d.set_page_load_timeout(40)
    d.set_script_timeout(120)
    log = []
    try:
        try:
            d.get(EN)
        except Exception:
            pass
        time.sleep(7)
        # fetch KR list (Korean decks). EN list has same structure if needed.
        raw = d.execute_async_script(FETCH_LIST_JS, "KR")
        obj = json.loads(raw)
        items = obj.get("payload", {}).get("irDataList", [])
        print(f"KR list: {obj.get('payload',{}).get('totCnt')} total, {len(items)} fetched")

        for it in items:
            title = it.get("dataTitl", "")
            y = year_from_title(title)
            q = quarter_from_title(title)
            if not in_window(y, q):
                continue
            files = it.get("mFileLst") or []
            pdf_id = files[0].get("fileIndvcsId") if files else None
            pdf_name = files[0].get("savViewImgNm") if files else None
            xls_id = it.get("irDataFileIndvcsId")
            dest_dir = ROOT / "data" / "ir" / f"FY{y}_{q}" / "raw" / KR_DIR
            dest_dir.mkdir(parents=True, exist_ok=True)

            for kind, fid, default_name in (
                ("pdf", pdf_id, pdf_name),
                ("xls", xls_id, None),
            ):
                if not fid:
                    log.append(f"MISS  FY{y} {q} {kind}: no id ({title})")
                    continue
                try:
                    res = d.execute_async_script(FETCH_FILE_JS, fid)
                except Exception as e:
                    log.append(f"FAIL  FY{y} {q} {kind}: js err {e}")
                    continue
                if isinstance(res, str) and res.startswith("ERR"):
                    log.append(f"FAIL  FY{y} {q} {kind}: {res[:80]}")
                    continue
                meta = json.loads(res)
                if meta.get("status") != 200:
                    log.append(f"FAIL  FY{y} {q} {kind}: http {meta.get('status')}")
                    continue
                data = base64.b64decode(meta["b64"])
                ct = meta.get("ct", "")
                # reject JSON error bodies
                if data[:1] == b"{" and "json" in ct.lower():
                    log.append(f"FAIL  FY{y} {q} {kind}: json body (auth?)")
                    continue
                # filename
                if kind == "pdf":
                    name = default_name or f"{title}_{kind}.pdf"
                else:
                    # xls: derive from pdf name pattern
                    base = (default_name or pdf_name or title).rsplit(".", 1)[0]
                    base = re.sub(r"Presentation.*$", "", base).strip(" _-")
                    ext = ".xlsx" if data[:2] == b"PK" else (".xls" if data[:2] == b"\xd0\xcf" else ".bin")
                    name = f"{base} Factsheet{ext}".strip()
                name = re.sub(r'[\\/:*?"<>|]', "_", name)
                dest = dest_dir / name
                dest.write_bytes(data)
                log.append(f"OK    FY{y} {q} {kind:3s} {len(data):>10,d}  {dest.relative_to(ROOT)}")
                print(f"   OK FY{y} {q} {kind} {len(data):,}b  {name}")
    finally:
        d.quit()
    print("\n===== DONGYANG DOWNLOAD LOG =====")
    print("\n".join(log))


if __name__ == "__main__":
    main()
