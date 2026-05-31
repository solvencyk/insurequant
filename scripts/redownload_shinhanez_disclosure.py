# -*- coding: utf-8 -*-
"""Re-download 신한이지손해보험 (KR0051) 정기경영공시 PDFs.

Integrity check found 6 truncated PDFs across FY2024_Q2..FY2026_Q1 — all
have valid %PDF-1.5 header but the cross-reference table is cut off
mid-xref (no %%EOF). Re-fetch from shinhanez.co.kr static publication
page and verify each landed file with %%EOF in the tail before
overwriting.

Strategy: open the publication page in Playwright, find every PDF link
row, label by '경영공시 YYYY년 N분기' / 'YYYY년 연간' text. For each
target period click the row, capture the download, verify magic+EOF,
move to canonical raw/.
"""
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path("data/disclosure").resolve()
KR = "KR0051"
NAME = "신한이지손해보험"
URL = "https://www.shinhanez.co.kr/static/pub/PUB10000T01.html"
STAGE = Path("artifacts/disclosure_research/_tmp/shinhanez_dl").resolve()
STAGE.mkdir(parents=True, exist_ok=True)

# (period_key, search-keywords-in-row-text) — pick first row whose text contains all keywords
# Korean disclosure naming: '경영공시 YYYY년 N분기' (quarterly), 'YYYY년 연간경영공시' (annual = Q4)
TARGETS = [
    ("FY2024_Q2", ["2024", "2분기"]),
    ("FY2024_Q3", ["2024", "3분기"]),
    ("FY2025_Q1", ["2025", "1분기"]),
    ("FY2025_Q2", ["2025", "2분기"]),
    ("FY2025_Q3", ["2025", "3분기"]),
    ("FY2026_Q1", ["2026", "1분기"]),
]


def verify_pdf(path: Path) -> tuple[bool, str]:
    b = path.read_bytes()
    if not b.startswith(b"%PDF"):
        return False, f"bad magic {b[:8].hex()}"
    tail = b[-128:]
    if b"%%EOF" not in tail:
        return False, "missing %%EOF"
    return True, f"ok size={len(b)}"


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            accept_downloads=True,
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
            locale="ko-KR",
        )
        page = ctx.new_page()
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2000)

        # Find every clickable row in the publication list
        # Try several common containers
        rows = page.query_selector_all('li, tr, div.list-item, div[role="row"]')
        print(f"candidate rows: {len(rows)}")

        # Build (text, element) list filtered to those that mention '경영공시' or '분기'
        candidates = []
        for r in rows:
            try:
                txt = (r.inner_text() or "").strip()
            except Exception:
                continue
            if not txt:
                continue
            if ("경영공시" in txt) or ("분기" in txt and ("2024" in txt or "2025" in txt or "2026" in txt)):
                if len(txt) > 200:
                    continue  # too generic container
                candidates.append((txt, r))

        print(f"matching rows: {len(candidates)}")
        for t, _ in candidates[:30]:
            t1 = t.replace("\n", " | ")[:100]
            print(f"  {t1}")

        results = []
        for period, kws in TARGETS:
            picked = None
            for txt, r in candidates:
                if all(kw in txt for kw in kws) and "경영공시" in txt:
                    picked = (txt, r)
                    break
            if not picked:
                # fallback: just kws
                for txt, r in candidates:
                    if all(kw in txt for kw in kws):
                        picked = (txt, r)
                        break
            if not picked:
                print(f"  [{period}] no matching row")
                results.append((period, False, "no row"))
                continue

            txt, row = picked
            print(f"  [{period}] picked: {txt[:80]}")

            # the row often has a 다운로드 link/button inside; find <a> or .btn first
            target = None
            for sel in ['a[href]', 'button', '.btn-download', 'a']:
                els = row.query_selector_all(sel)
                if els:
                    target = els[-1]  # last anchor usually = download button
                    break
            if target is None:
                target = row

            try:
                with page.expect_download(timeout=60000) as dl_info:
                    target.scroll_into_view_if_needed()
                    target.click()
                dl = dl_info.value
                tmp = STAGE / f"{period}.pdf"
                dl.save_as(str(tmp))
            except Exception as e:
                print(f"  [{period}] download failed: {e}")
                results.append((period, False, f"download err: {e}"))
                continue

            ok, why = verify_pdf(tmp)
            if not ok:
                print(f"  [{period}] verify failed: {why}")
                results.append((period, False, why))
                continue

            outdir = ROOT / period / "raw"
            outdir.mkdir(parents=True, exist_ok=True)
            dest = outdir / f"{KR}_{NAME}.pdf"
            if dest.exists():
                backup = dest.with_suffix(".pdf.bad")
                if backup.exists():
                    backup.unlink()
                dest.replace(backup)
            tmp.replace(dest)
            print(f"  [{period}] OK -> {dest} ({why})")
            results.append((period, True, why))

        ctx.close()
        browser.close()

    print("\n== SUMMARY ==")
    ok_count = sum(1 for _, ok, _ in results if ok)
    for period, ok, why in results:
        flag = "OK" if ok else "FAIL"
        print(f"  {period}  {flag}  {why}")
    print(f"  total: {ok_count}/{len(results)} ok")
    return 0 if ok_count == len(results) else 2


if __name__ == "__main__":
    sys.exit(main())
