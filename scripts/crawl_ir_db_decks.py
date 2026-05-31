# -*- coding: utf-8 -*-
"""DB손해보험 (KR0011) IR deck (PDF) downloader — companion to crawl_ir_db.py.

The DB FactSheet (already downloaded) carries the raw CSM waterfall + 월납 premium,
but the *disclosed* 신계약 CSM 배수 headline lives in the IR Report / 경영실적 deck.
This grabs the Korean deck PDF per quarter into the same
data/ir/FY{YYYY}_Q{N}/KR0011_DB손해보험/ dir.

Detail .shtm pages expose direct __etc/*.pdf links downloadable via requests.
"""
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import unquote

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

sys.stdout.reconfigure(encoding="utf-8")

LIST_URL = "https://www.idbins.com/pc/bizxpress/contentTemplet/cmy/inv/ir/list.jsp"
KR_DIR = "KR0011_DB손해보험"
ROOT = Path("data/ir").resolve()
WANT_FY = list(range(2023, 2027))


def title_to_quarter(title: str):
    t = title.strip()
    m = re.search(r"(20\d{2})\.\s*([1-4])Q", t)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r"(20\d{2})\s*경영실적", t)
    if m:
        return int(m.group(1)), 4
    return None


def is_deck(title: str) -> bool:
    """Rows carrying the disclosed 배수: quarterly IR Report + annual 경영실적 deck."""
    return ("IR Report" in title) or ("경영실적" in title)


def collect_rows(d):
    out = []
    for a in d.find_elements(By.XPATH, "//table//tr//a"):
        t = (a.text or "").strip()
        h = a.get_attribute("href") or ""
        if t and h and "FWCOMV1705" in h:
            out.append({"title": t, "href": h})
    return out


def enumerate_rows(d):
    d.get(LIST_URL)
    time.sleep(8)
    seen = {}
    page = 0
    while True:
        page += 1
        rows = collect_rows(d)
        for r in rows:
            seen.setdefault(r["href"], r)
        titles = [r["title"] for r in rows]
        oldest = any((q := title_to_quarter(t)) and q[0] < min(WANT_FY) for t in titles)
        nxt = d.find_elements(
            By.XPATH,
            "//a[contains(@class,'next') or contains(normalize-space(.),'더보기') "
            "or contains(normalize-space(.),'다음')]")
        if oldest or not nxt or page > 25:
            break
        try:
            d.execute_script("arguments[0].click();", nxt[0])
            time.sleep(3)
        except Exception:
            break
    return list(seen.values())


def detail_pdfs(d, href):
    d.get(href)
    time.sleep(3)
    out = []
    for a in d.find_elements(By.XPATH, "//a"):
        h = a.get_attribute("href") or ""
        if h.lower().endswith(".pdf") and "__etc" in h:
            out.append((unquote(h.split("/")[-1]), h))
    return out


def pick_kor_pdf(pdfs):
    if not pdfs:
        return None
    eng_tokens = ("eng", "english", "insurance", "financial results", "business strategy")
    kor = [p for p in pdfs if not any(tok in p[0].lower() for tok in eng_tokens)]
    return (kor or pdfs)[0]


def main():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,4000")
    opts.add_argument("--lang=ko-KR")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
    d = webdriver.Chrome(options=opts)
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Referer": LIST_URL,
    })
    manifest = []
    try:
        rows = enumerate_rows(d)
        # one deck per quarter; prefer quarterly "IR Report" over annual deck for Q1-Q3,
        # use annual 경영실적 for Q4
        by_q = {}
        for r in rows:
            q = title_to_quarter(r["title"])
            if not q or q[0] not in WANT_FY or not is_deck(r["title"]):
                continue
            cur = by_q.get(q)
            if cur is None:
                by_q[q] = r
            else:
                # prefer "IR Report" for non-Q4; for Q4 prefer annual 경영실적 deck
                fy, qn = q
                if qn == 4:
                    if "경영실적" in r["title"] and "IR Report" not in r["title"]:
                        by_q[q] = r
                else:
                    if "IR Report" in r["title"]:
                        by_q[q] = r
        print(f"deck target quarters: {sorted(by_q)}")
        for q in sorted(by_q):
            r = by_q[q]
            fy, qn = q
            outdir = ROOT / f"FY{fy}_Q{qn}" / KR_DIR
            outdir.mkdir(parents=True, exist_ok=True)
            pdfs = detail_pdfs(d, r["href"])
            chosen = pick_kor_pdf(pdfs)
            if not chosen:
                print(f"  [FY{fy}_Q{qn}] {r['title']!r} -> NO PDF ({[p[0] for p in pdfs]})")
                continue
            name, url = chosen
            dest = outdir / name
            try:
                resp = sess.get(url, timeout=60)
                resp.raise_for_status()
                dest.write_bytes(resp.content)
                print(f"  [FY{fy}_Q{qn}] {r['title']!r} -> {name} ({len(resp.content)} B)")
                manifest.append({"fy": fy, "q": qn, "title": r["title"],
                                 "file": str(dest), "bytes": len(resp.content), "url": url})
            except Exception as e:
                print(f"  [FY{fy}_Q{qn}] FAIL {name}: {e}")
    finally:
        d.quit()
    Path("data/ir/_db_decks_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    got = sorted({(m["fy"], m["q"]) for m in manifest})
    print(f"\ndeck got: {got}")


if __name__ == "__main__":
    main()
