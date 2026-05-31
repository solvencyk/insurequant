# -*- coding: utf-8 -*-
"""Crawl quarterly IR materials for 롯데손해보험 (Lotte) and 코리안리 (Korean Re).

Recipe (proven on 삼성생명 / 메리츠): JS SPA list pages -> Selenium headless
Chrome render -> harvest per-row download links (Excel / PDF) -> download each
file (urllib + CERT_NONE since both hosts have cert/redirect quirks).

- Lotte: list at /web/C/D/H/cdh_ir_board04_list_6.jsp (실적발표자료, Excel factsheets).
  Pagination via JS go_page(n) which resubmits POST form 'myform' to /CChannelSvl.
  We click the paginator and re-scrape each rendered page for /upload/...xls hrefs.
- Korean Re: IR자료실 list pages (asp). Reinsurer -> capture whatever earnings /
  경영실적 / 경영통일공시 material exists; no 신계약 CSM 배수 expected.

Files saved to data/ir/decks/<slug>/ (raw archive). Organization into
data/ir/FY*/<KR>_<회사>/ is done by the caller after inspection.

Run: python scripts/crawl_ir_lotte_koreanre.py [lotte|koreanre|both]
"""
from __future__ import annotations
import os
import re
import ssl
import sys
import time
import urllib.request
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def fetch_bytes(url, referer=None):
    headers = {"User-Agent": UA, "Accept": "*/*"}
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=CTX, timeout=120) as r:
        return r.read()


def save(slug, filename, data):
    d = os.path.join(ROOT, "data", "ir", "decks", slug)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, filename)
    with open(p, "wb") as f:
        f.write(data)
    return p, len(data)


def make_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--ignore-certificate-errors")
    opts.add_argument("--window-size=1400,2000")
    opts.add_argument(f"user-agent={UA}")
    drv = webdriver.Chrome(options=opts)
    drv.set_page_load_timeout(60)
    return drv


# ---------------------------------------------------------------- Lotte ----
def crawl_lotte():
    from selenium.webdriver.common.by import By
    base = "https://www.lotteins.co.kr"
    list_url = base + "/web/C/D/H/cdh_ir_board04_list_6.jsp"
    drv = make_driver()
    seen = {}  # url -> title
    try:
        drv.get(list_url)
        time.sleep(2)
        # iterate pages 1..6 by calling go_page(n) in-page
        max_page = 6
        for pg in range(1, max_page + 1):
            if pg > 1:
                try:
                    drv.execute_script(f"go_page({pg});")
                    time.sleep(2)
                except Exception as e:
                    print(f"[lotte] go_page({pg}) failed: {e}")
                    break
            html = drv.page_source
            rows = re.findall(r'(/upload/[^"\'\s)]+?\.(?:xls|xlsx|pdf))', html)
            # titles: grab anchor text near the link if possible
            titles = re.findall(r'20\d\d[^<>]{0,14}(?:분기|반기|factsheet|Factsheet)', html)
            for u in rows:
                seen.setdefault(u, "")
            print(f"[lotte] page {pg}: {len(rows)} file links, titles={titles[:10]}")
    finally:
        drv.quit()

    log = []
    for u in sorted(seen):
        fn = os.path.basename(u)
        try:
            data = fetch_bytes(base + u, referer=list_url)
        except Exception as e:
            log.append(f"[lotte] DL FAIL {fn}: {e}")
            continue
        p, n = save("lotte_nonlife", fn, data)
        log.append(f"[lotte] OK {fn}  {n} bytes")
    print("\n".join(log))
    return seen


# ------------------------------------------------------------ Korean Re ----
def crawl_koreanre():
    base = "https://www.koreanre.co.kr"
    # IR자료실 candidate list pages (asp). ir_03_5 = IR자료실 landing.
    list_urls = [
        base + "/ir/ir_03_5.asp",
        base + "/ir/ir_03_1.asp",
        base + "/ir/ir_03_2.asp",
        base + "/ir/ir_03_3.asp",
        base + "/ir/ir_03_4.asp",
    ]
    drv = make_driver()
    seen = {}
    try:
        for lu in list_urls:
            try:
                drv.get(lu)
                time.sleep(2)
            except Exception as e:
                print(f"[koreanre] load fail {lu}: {e}")
                continue
            html = drv.page_source
            files = re.findall(r'([^"\'\s(]+?\.(?:pdf|xls|xlsx|ppt|pptx|zip))', html)
            for f in files:
                if "javascript" in f.lower():
                    continue
                seen.setdefault(f, lu)
            print(f"[koreanre] {lu}: {len(files)} file refs")
    finally:
        drv.quit()
    for f in sorted(seen):
        print("[koreanre] FOUND:", f)
    return seen


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    if which in ("lotte", "both"):
        crawl_lotte()
    if which in ("koreanre", "both"):
        crawl_koreanre()
