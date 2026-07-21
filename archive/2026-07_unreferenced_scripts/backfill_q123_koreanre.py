# -*- coding: utf-8 -*-
"""Backfill 코리안리재보험 (KR1000) 분기 정기경영공시 — FY2024/FY2025 Q1-Q3.

Korean Re publishes ALL periodic 경영공시 as plain PDF links in ONE table on
  https://www.koreanre.co.kr/ir/ir_03_1.asp
The table is one <tr> per year; each row has cells for 1/4분기, 2/4분기,
3/4분기, 회계연도(=Q4). Every cell's <a href> points straight at the PDF, e.g.
  /USER_DATA/koreanre/content/editor/pdf/gyungyoung/2024_1.pdf
No year selector / pagination — all years (2012..2026) are in the same table.

This script enumerates the table, maps (year, quarter) -> href via the URL's
trailing `<year>_<q>` token (quarter token 1/2/3 = Q1/Q2/Q3; 4 or '4Q' = Q4),
then downloads the 6 missing cells and verifies them.

Save layout (matches the FY2023-2025 files alongside which these slot in):
  data/disclosure/FY{YYYY}_Q{N}/raw/KR1000_코리안리.pdf
"""
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
PAGE = "https://www.koreanre.co.kr/ir/ir_03_1.asp"
DISC = ROOT / "data" / "disclosure"
TMP = ROOT / "artifacts" / "disclosure_research" / "_tmp" / "koreanre"
TMP.mkdir(parents=True, exist_ok=True)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# The 6 gap cells to fill.
WANT = [(2024, 1), (2024, 2), (2024, 3), (2025, 1), (2025, 2), (2025, 3)]

# Map the trailing "<year>_<qtoken>" in the gyungyoung PDF path to (year, quarter).
# qtoken examples seen on the page: 2024_1, 2025_2, 2024_4Q, 2023_4Q.
PDF_TOKEN = re.compile(r"/(\d{4})_(\d)(?:Q)?\.pdf$", re.IGNORECASE)


def verify_pdf(b: bytes) -> tuple[bool, str]:
    if not b.startswith(b"%PDF"):
        return False, f"bad magic {b[:8].hex()}"
    if b"%%EOF" not in b[-16384:] and b"%%EOF" not in b:
        return False, "missing %%EOF"
    return True, f"ok {len(b)}B"


def main() -> int:
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            accept_downloads=True, ignore_https_errors=True, locale="ko-KR",
            user_agent=UA,
        )
        page = ctx.new_page()
        page.set_default_timeout(30000)
        page.goto(PAGE, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)

        # Collect every <a href> on the page; the periodic PDFs live under the
        # gyungyoung folder but earlier years use other folders — match by the
        # "<year>_<q>.pdf" token regardless of folder.
        hrefs = page.eval_on_selector_all(
            "a[href]", "els => els.map(e => e.getAttribute('href'))"
        )

        # (year, quarter) -> absolute url
        cell_url = {}
        all_labels = {}  # year -> sorted list of quarters present
        for h in hrefs:
            if not h:
                continue
            m = PDF_TOKEN.search(h)
            if not m:
                continue
            year = int(m.group(1))
            qtoken = int(m.group(2))
            if qtoken not in (1, 2, 3, 4):
                continue
            abs_url = urljoin(page.url, h)
            cell_url.setdefault((year, qtoken), abs_url)
            all_labels.setdefault(year, set()).add(qtoken)

        print("== Korean Re periodic disclosure table (year -> quarters present) ==")
        for year in sorted(all_labels, reverse=True):
            qs = sorted(all_labels[year])
            print(f"  {year}: {['Q'+str(q) for q in qs]}")
        print()

        for year, q in WANT:
            period = f"FY{year}_Q{q}"
            url = cell_url.get((year, q))
            if not url:
                print(f"  [{period}] no link on page")
                results.append((period, False, "no link", None))
                continue
            try:
                resp = ctx.request.get(url, headers={"Referer": PAGE}, timeout=60000)
                if resp.status != 200:
                    print(f"  [{period}] HTTP {resp.status} {url}")
                    results.append((period, False, f"http {resp.status}", url))
                    continue
                body = resp.body()
            except Exception as e:
                print(f"  [{period}] download err: {str(e)[:80]}")
                results.append((period, False, "dl err", url))
                continue

            ok, why = verify_pdf(body)
            if not ok:
                # Save the bad payload for diagnosis.
                bad = TMP / f"{period}_bad.bin"
                bad.write_bytes(body[:65536])
                print(f"  [{period}] verify failed: {why} (src={url})")
                results.append((period, False, why, url))
                continue

            outdir = DISC / period / "raw"
            outdir.mkdir(parents=True, exist_ok=True)
            dest = outdir / "KR1000_코리안리.pdf"
            dest.write_bytes(body)
            print(f"  [{period}] -> {dest.relative_to(ROOT)} ({why}) src={urlparse(url).path}")
            results.append((period, True, why, url))

        ctx.close()
        browser.close()

    print("\n== SUMMARY ==")
    for period, ok, why, _ in results:
        print(f"  {period}: {'OK' if ok else 'FAIL'}  {why}")
    n_ok = sum(1 for _, ok, *_ in results if ok)
    print(f"  {n_ok}/{len(results)} ok")
    return 0 if n_ok == len(WANT) else 2


if __name__ == "__main__":
    sys.exit(main())
