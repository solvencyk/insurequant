# -*- coding: utf-8 -*-
"""Backfill 신한이지손해보험 (KR0051) 정기경영공시 분기 PDFs from the company site.

The 신한EZ 경영공시 page (PUB10000T01.html) renders a paginated board under the
정기공시 tab panel ``#tabFPanel1``. Each row (``li.bbs-row``) carries a title
(``.bbs-subject`` e.g. "2023년 1분기 경영공시") and a download button
(``button[data-action=download]``) that fires a JS download event — no href.

Missing cells to backfill (4):
  FY2023_Q1  = "2023년 1분기 경영공시"   (page 2, #77)
  FY2023_Q2  = "2023년 상반기 경영공시"  (page 2, #78)
  FY2023_Q3  = "2023년 3분기 경영공시"   (page 2, #79)
  FY2024_Q1  = "2024년 1분기 경영공시"   (page 1, #81)

This script reads the board page-by-page, matches each target by its title
text, clicks the row's 다운로드 button (Playwright expect_download), verifies the
PDF, and saves to data/disclosure/FY{YYYY}_Q{N}/raw/KR0051_신한이지손해보험.pdf.
"""
from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
DISC = ROOT / "data" / "disclosure"
URL = "https://www.shinhanez.co.kr/static/pub/PUB10000T01.html"
STAGE = ROOT / "artifacts" / "disclosure_research" / "_tmp" / "shinhanez"
STAGE.mkdir(parents=True, exist_ok=True)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

STEM = "KR0051_신한이지손해보험"

# period -> exact board title text (신한EZ 분기 표기: 상반기 = 2분기)
TARGETS = {
    "FY2023_Q1": "2023년 1분기 경영공시",
    "FY2023_Q2": "2023년 상반기 경영공시",
    "FY2023_Q3": "2023년 3분기 경영공시",
    "FY2024_Q1": "2024년 1분기 경영공시",
}


def verify_pdf(b: bytes) -> tuple[bool, str]:
    if not b.startswith(b"%PDF"):
        return False, f"bad magic {b[:8].hex()}"
    if b"%%EOF" not in b[-16384:] and b"%%EOF" not in b:
        return False, "missing %%EOF"
    return True, f"ok {len(b)}B"


def _decode_zipname(raw: str) -> str:
    try:
        return raw.encode("cp437").decode("euc-kr")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return raw


def extract_disclosure_pdf(zip_bytes: bytes) -> tuple[bytes | None, str]:
    """If a target download is a ZIP, return the 경영공시 본문 PDF (drop 감사/재무제표)."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile:
        return None, "bad zip"
    SUPPL = ("감사", "audit", "재무제표", "별첨", "reporting", "지급여력")
    BODY_HINT = ("경영공시", "disclosure", "현황", "공시")
    candidates = []
    for info in zf.infolist():
        nm = _decode_zipname(info.filename)
        low = nm.lower()
        if not low.endswith(".pdf"):
            continue
        if any(s in low for s in SUPPL):
            continue
        candidates.append((info, nm))
    if not candidates:
        return None, "no 경영공시 본문 in zip (all supplements)"

    def rank(c):
        nm, low = c[1], c[1].lower()
        return (
            0 if any(h in low for h in BODY_HINT) else 1,
            0 if nm.strip().startswith("[") else 1,
            -zf.getinfo(c[0].filename).file_size,
        )
    candidates.sort(key=rank)
    info, nm = candidates[0]
    return zf.read(info.filename), nm


def read_board_titles(page) -> list[str]:
    return page.evaluate(r"""()=>{
        const panel=document.querySelector('#tabFPanel1');
        if(!panel) return [];
        return Array.from(panel.querySelectorAll('li.bbs-row[data-eid=row]'))
            .map(li=>(li.querySelector('.bbs-subject')||{}).innerText?.trim()||'');
    }""")


def goto_page(page, n: int) -> bool:
    """Click pager page number n inside #tabFPanel1; returns True if clicked."""
    try:
        link = page.locator('#tabFPanel1 #paging ul li a', has_text=str(n)).first
        if link.count() == 0:
            # exact-text match fallback
            link = page.locator('#tabFPanel1 #paging').get_by_role("link", name=str(n), exact=True).first
        link.click(timeout=5000)
        page.wait_for_timeout(2500)
        return True
    except Exception as e:
        print(f"  WARN goto page {n} failed: {str(e)[:80]}")
        return False


def download_by_title(page, title: str) -> tuple[bytes | None, str]:
    """Click the 다운로드 button in the row whose .bbs-subject == title."""
    row = page.locator(
        '#tabFPanel1 li.bbs-row[data-eid=row]'
    ).filter(has=page.locator(f'.bbs-subject:text-is("{title}")')).first
    if row.count() == 0:
        return None, "row not found"
    btn = row.locator('button[data-action=download], button.download').first
    if btn.count() == 0:
        btn = row.locator('button').first
    try:
        with page.expect_download(timeout=25000) as dl_info:
            btn.click()
        dl = dl_info.value
        path = dl.path()
        if not path or not Path(path).exists():
            return None, "download path missing"
        return Path(path).read_bytes(), (dl.suggested_filename or dl.url or "")
    except Exception as e:
        return None, f"click/download err: {str(e)[:100]}"


def save_pdf(period: str, data: bytes) -> Path:
    outdir = DISC / period / "raw"
    outdir.mkdir(parents=True, exist_ok=True)
    dest = outdir / f"{STEM}.pdf"
    dest.write_bytes(data)
    return dest


def main() -> int:
    results = {}  # period -> (status, detail)
    exposed_labels: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            accept_downloads=True, ignore_https_errors=True, locale="ko-KR",
            user_agent=UA,
        )
        page = ctx.new_page()
        page.set_default_timeout(20000)
        page.goto(URL, wait_until="domcontentloaded", timeout=45000)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        page.wait_for_selector('#tabFPanel1 li.bbs-row', timeout=20000)
        page.wait_for_timeout(1500)

        # Collect the full set of exposed period labels across all pages.
        seen_pages = set()
        for pnum in range(1, 7):  # pager shows up to 5; loop a little past to be safe
            if pnum > 1:
                if not goto_page(page, pnum):
                    break
            titles = read_board_titles(page)
            if not titles or tuple(titles) in seen_pages:
                break
            seen_pages.add(tuple(titles))
            exposed_labels.extend(titles)
            print(f"[page {pnum}] {len(titles)} rows: {titles}")

            # Try to satisfy any pending targets visible on this page.
            for period, want in TARGETS.items():
                if period in results:
                    continue
                if want not in titles:
                    continue
                raw, detail = download_by_title(page, want)
                if raw is None:
                    results[period] = ("FAIL", detail)
                    print(f"  [{period}] download FAIL: {detail}")
                    continue
                if raw[:2] == b"PK":
                    data, picked = extract_disclosure_pdf(raw)
                    if data is None:
                        results[period] = ("FAIL", f"zip extract: {picked}")
                        print(f"  [{period}] zip extract FAIL: {picked}")
                        continue
                    print(f"    picked from zip: {picked}")
                else:
                    data = raw
                ok, why = verify_pdf(data)
                if not ok:
                    results[period] = ("FAIL", f"verify: {why}")
                    # dump the bad bytes for inspection
                    (STAGE / f"{period}_bad.bin").write_bytes(data[:4096])
                    print(f"  [{period}] verify FAIL: {why}")
                    continue
                dest = save_pdf(period, data)
                results[period] = ("OK", f"{dest.relative_to(ROOT)} ({why})")
                print(f"  [{period}] OK -> {dest.relative_to(ROOT)} ({why})")

            if all(per in results for per in TARGETS):
                break

        # Anything still missing: dump diagnostics.
        missing = [per for per in TARGETS if per not in results]
        if missing:
            try:
                page.screenshot(path=str(STAGE / "fail.png"), full_page=True)
                (STAGE / "fail.html").write_text(page.content(), encoding="utf-8")
            except Exception:
                pass
            for per in missing:
                results[per] = ("FAIL", f"target title '{TARGETS[per]}' not reached on any page")

        ctx.close()
        browser.close()

    # dedupe exposed labels preserving order
    seen = set()
    uniq_labels = [x for x in exposed_labels if not (x in seen or seen.add(x))]

    print("\n== EXPOSED PERIOD LABELS (정기공시 board) ==")
    for lbl in uniq_labels:
        print(f"  - {lbl}")

    print("\n== SUMMARY ==")
    n_ok = sum(1 for s, _ in results.values() if s == "OK")
    for period in TARGETS:
        s, d = results.get(period, ("FAIL", "not attempted"))
        print(f"  {period}: {s}  {d}")
    print(f"  {n_ok}/{len(TARGETS)} ok")
    return 0 if n_ok == len(TARGETS) else 2


if __name__ == "__main__":
    raise SystemExit(main())
