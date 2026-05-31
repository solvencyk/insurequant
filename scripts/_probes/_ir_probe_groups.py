# -*- coding: utf-8 -*-
"""Probe the four financial-group IR pages with headless Selenium and dump
the rendered structure: download links/buttons, file URLs, and any list of
quarterly publications. Read-only — downloads nothing. Output is printed so we
can design the per-group crawler.

Run: python scripts/_ir_probe_groups.py [group]
  group in {kb, kb_factbook, shinhan, hana_databook, hana_present, nh}
"""
import sys
import time
import json

sys.stdout.reconfigure(encoding="utf-8")

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

PAGES = {
    "kb": "https://www.kbfg.com/kor/ir/mgt-performance/list.jsp",
    "kb_factbook": "https://www.kbfg.com/kor/ir/report/factbook/list.jsp",
    "shinhan_fb": "http://www.shinhangroup.com/kr/invest/finance/factBook.jsp",
    "shinhan_ir": "https://shinhangroup.com/kr/ir/overview",
    "hana_databook": "https://www.hanafn.com/ir/financial/databookDetail.do",
    "hana_present": "https://www.hanafn.com/ir/info/presentationsList.do",
    "hana_factsheet": "https://www.hanafn.com/ir/info/factSheet.do",
    "nh": "https://www.nhfngroup.com/user/indexSub.do?codyMenuSeq=1219938669&siteId=nhfngroup",
}


def make_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,2600")
    opts.add_argument("--ignore-certificate-errors")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
    return webdriver.Chrome(options=opts)


def probe(key, url):
    print(f"\n{'='*70}\n{key}  {url}\n{'='*70}")
    d = make_driver()
    try:
        d.get(url)
        time.sleep(8)
        print("TITLE:", d.title)
        print("CUR URL:", d.current_url)
        # iframes
        frames = d.find_elements(By.TAG_NAME, "iframe")
        print(f"iframes: {len(frames)}")
        for fr in frames[:6]:
            print("  iframe src:", fr.get_attribute("src"))
        # anchors with file-ish hrefs or download
        anchors = d.find_elements(By.TAG_NAME, "a")
        hits = []
        for a in anchors:
            href = (a.get_attribute("href") or "")
            txt = (a.text or "").strip()
            onclick = (a.get_attribute("onclick") or "")
            low = (href + " " + onclick).lower()
            if any(x in low for x in (".pdf", ".xls", ".xlsx", "download", "filedown", "down.do", "fileid", "atch")):
                hits.append((txt[:40], href[:160], onclick[:160]))
        print(f"file-ish anchors: {len(hits)}")
        for t, h, o in hits[:40]:
            print(f"  A txt={t!r}\n     href={h}\n     onclick={o}")
        # buttons
        btns = d.find_elements(By.XPATH, "//button|//*[@role='button']|//span[contains(@class,'down')]|//a[contains(@class,'down')]")
        print(f"button-ish: {len(btns)}")
        seen = set()
        for b in btns[:50]:
            t = (b.text or "").strip()
            oc = (b.get_attribute("onclick") or "")
            cl = (b.get_attribute("class") or "")
            key2 = (t, oc[:80], cl[:40])
            if t and key2 not in seen and ("다운" in t or "down" in cl.lower() or "down" in oc.lower() or "엑셀" in t or "excel" in t.lower()):
                seen.add(key2)
                print(f"  BTN txt={t!r} class={cl[:40]!r} onclick={oc[:120]!r}")
        # list rows that look like quarterly publications
        body = d.find_element(By.TAG_NAME, "body").text
        lines = [l.strip() for l in body.splitlines() if l.strip()]
        rel = [l for l in lines if any(y in l for y in ("2023", "2024", "2025", "2026"))
               and any(k in l for k in ("분기", "경영실적", "Fact", "Databook", "실적", "Q", "데이터", "공시"))]
        print(f"date-ish lines ({len(rel)}):")
        for l in rel[:30]:
            print("   ", l[:90])
    except Exception as e:
        print("ERROR:", repr(e))
    finally:
        d.quit()


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which == "all":
        for k, u in PAGES.items():
            probe(k, u)
    else:
        probe(which, PAGES[which])
