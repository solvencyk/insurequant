# -*- coding: utf-8 -*-
"""DB손해보험 (KR0011) IR materials downloader.

Renders the DB IR 리포트 list (JS pagination) with Selenium headless Chrome,
enumerates every row across all pages, opens each relevant detail .shtm page,
and downloads the attached files (prefer Excel FACT SHEET) into
data/ir/FY{YYYY}_Q{N}/KR0011_DB손해보험/<filename>.

Quarter mapping (DB FY = calendar year): 결산/경영실적 -> Q4, 상반기/2Q -> Q2,
3Q -> Q3, 1Q -> Q1.
"""
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, unquote

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

sys.stdout.reconfigure(encoding="utf-8")

LIST_URL = "https://www.idbins.com/pc/bizxpress/contentTemplet/cmy/inv/ir/list.jsp"
KR_DIR = "KR0011_DB손해보험"
ROOT = Path("data/ir").resolve()

# FY range we want: FY2023 Q1 .. FY2026 Q1
WANT_FY = list(range(2023, 2027))


def title_to_quarter(title: str):
    """Map a DB IR row title to (FY, Q) or None. DB FY == calendar year."""
    t = title.strip()
    # explicit "YYYY.NQ" pattern (Fact sheet / IR Report)
    m = re.search(r"(20\d{2})\.\s*([1-4])Q", t)
    if m:
        return int(m.group(1)), int(m.group(2))
    # "YYYY 경영실적 및 ..." -> that year's Q4 (annual results)
    m = re.search(r"(20\d{2})\s*경영실적", t)
    if m:
        return int(m.group(1)), 4
    # "YYYY.NQ 경영실적" handled by first pattern; "결산"
    m = re.search(r"(20\d{2}).*결산", t)
    if m:
        return int(m.group(1)), 4
    return None


def is_target(title: str) -> bool:
    """Only Fact sheet / 경영실적(annual) rows carry the per-quarter financials."""
    if "Fact sheet" in title or "FactSheet" in title:
        return True
    if "경영실적" in title:  # annual results deck
        return True
    return False


def collect_rows(d):
    """Return list of dicts {title, href} for the current page table."""
    out = []
    for a in d.find_elements(By.XPATH, "//table//tr//a"):
        t = (a.text or "").strip()
        h = a.get_attribute("href") or ""
        if t and h and "FWCOMV1705" in h:
            out.append({"title": t, "href": h})
    return out


def enumerate_all_rows(d):
    """Walk every list page via the pager until we've covered all WANT_FY years."""
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
        print(f"  page {page}: {len(rows)} rows; last={titles[-1] if titles else '-'}")
        # stop once we see a row older than FY2023 1Q on this page
        oldest_reached = any(
            (q := title_to_quarter(t)) and q[0] < min(WANT_FY) for t in titles
        )
        # find pager "next" — DB uses 더보기 / numbered paging
        nxt = d.find_elements(
            By.XPATH,
            "//a[contains(@class,'next') or contains(normalize-space(.),'더보기') "
            "or contains(normalize-space(.),'다음')]",
        )
        if oldest_reached or not nxt or page > 25:
            break
        try:
            d.execute_script("arguments[0].click();", nxt[0])
            time.sleep(3)
        except Exception:
            break
    return list(seen.values())


def detail_files(d, href):
    """Open a detail .shtm page; return list of (filename, file_url)."""
    d.get(href)
    time.sleep(3)
    files = []
    for a in d.find_elements(By.XPATH, "//a"):
        h = a.get_attribute("href") or ""
        if re.search(r"\.(xlsx|xls|pdf|pptx?|zip)(\?|$)", h, re.I) and "__etc" in h:
            name = unquote(h.split("/")[-1].split("?")[0])
            files.append((name, h))
    return files


def pick_files(files):
    """Prefer Korean Excel FactSheet; fall back to any Excel, then PDF/others."""
    if not files:
        return []
    kor_xlsx = [f for f in files if f[0].lower().endswith((".xlsx", ".xls")) and "kor" in f[0].lower()]
    any_xlsx = [f for f in files if f[0].lower().endswith((".xlsx", ".xls"))]
    pdfs = [f for f in files if f[0].lower().endswith(".pdf")]
    if kor_xlsx:
        return kor_xlsx
    if any_xlsx:
        return any_xlsx
    return pdfs or files


def main():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,4000")
    opts.add_argument("--lang=ko-KR")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
    d = webdriver.Chrome(options=opts)
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Referer": LIST_URL,
    })
    manifest = []
    try:
        print("== enumerate DB IR rows ==")
        rows = enumerate_all_rows(d)
        print(f"total rows discovered: {len(rows)}")
        targets = []
        for r in rows:
            q = title_to_quarter(r["title"])
            if q and q[0] in WANT_FY and is_target(r["title"]):
                targets.append((q, r))
        # dedupe by (fy,q): prefer "Fact sheet" over annual deck if both exist
        by_q = {}
        for q, r in targets:
            cur = by_q.get(q)
            if cur is None:
                by_q[q] = r
            else:
                # prefer Fact sheet
                if "Fact" in r["title"] and "Fact" not in cur["title"]:
                    by_q[q] = r
        print(f"target quarters: {sorted(by_q)}")
        for q in sorted(by_q):
            r = by_q[q]
            fy, qn = q
            outdir = ROOT / f"FY{fy}_Q{qn}" / KR_DIR
            outdir.mkdir(parents=True, exist_ok=True)
            files = detail_files(d, r["href"])
            chosen = pick_files(files)
            print(f"  [FY{fy}_Q{qn}] {r['title']!r} -> {[c[0] for c in chosen]}")
            for name, url in chosen:
                dest = outdir / name
                try:
                    resp = sess.get(url, timeout=60)
                    resp.raise_for_status()
                    dest.write_bytes(resp.content)
                    print(f"      saved {dest} ({len(resp.content)} bytes)")
                    manifest.append({
                        "fy": fy, "q": qn, "title": r["title"],
                        "file": str(dest), "bytes": len(resp.content), "url": url,
                    })
                except Exception as e:
                    print(f"      FAIL {name}: {e}")
    finally:
        d.quit()
    (ROOT / "series").mkdir(parents=True, exist_ok=True)
    Path("data/ir/_db_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    got = sorted({(m["fy"], m["q"]) for m in manifest})
    print("\n== DB manifest ==")
    for m in manifest:
        print(f"  FY{m['fy']}_Q{m['q']}  {Path(m['file']).name}  ({m['bytes']} B)")
    want = [(fy, qn) for fy in WANT_FY for qn in (1, 2, 3, 4)
            if not (fy == 2026 and qn > 1)]
    missing = [q for q in want if q not in got]
    print(f"\ngot: {got}")
    print(f"missing: {missing}")


if __name__ == "__main__":
    main()
