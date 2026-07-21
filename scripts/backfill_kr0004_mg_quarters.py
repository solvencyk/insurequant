# -*- coding: utf-8 -*-
"""Backfill 예별손해보험(구 MG손해보험, KR0004) historical 정기경영공시.

The 예별 site (yebyeol.co.kr) keeps the FULL historical archive of 정기경영공시
on one page — each quarter is an <a id="quarter{N}_{YYYY}" href="javascript:fn_download(ID)">.
These older filings were lodged under the 구사명 "MG손해보험" (2025 사명변경 동일 법인).

Naming on site → our period:
  quarter1 = 1분기  → FY{Y}_Q1
  quarter2 = 상반기 → FY{Y}_Q2   (반기보고서)
  quarter3 = 3분기  → FY{Y}_Q3
  quarter4 = 결산   → FY{Y}_Q4   (연간; may be a ZIP bundling 감사/재무제표)

Parser bounce inbox/downloader/20260616T0055Z requested 2023.1Q~2025.3Q (11분기).
Saves to data/disclosure/FY{YYYY}_Q{N}/raw/KR0004_예별손해보험.pdf (parser globs KR0004_*).
Already on disk: FY2025_Q4, FY2026_Q1 — NOT touched.
"""
import io
import sys
import zipfile
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

URL = "https://yebyeol.co.kr/PB021010DM.scp?menuId=MN0802001"
ROOT = Path("data/disclosure").resolve()
STEM = "KR0004_예별손해보험"

# (period, element-id) — 11 quarters requested by parser
TARGETS = [
    ("FY2023_Q1", "quarter1_2023"), ("FY2023_Q2", "quarter2_2023"),
    ("FY2023_Q3", "quarter3_2023"), ("FY2023_Q4", "quarter4_2023"),
    ("FY2024_Q1", "quarter1_2024"), ("FY2024_Q2", "quarter2_2024"),
    ("FY2024_Q3", "quarter3_2024"), ("FY2024_Q4", "quarter4_2024"),
    ("FY2025_Q1", "quarter1_2025"), ("FY2025_Q2", "quarter2_2025"),
    ("FY2025_Q3", "quarter3_2025"),
]


def verify_pdf(b: bytes) -> tuple[bool, str]:
    if not b.startswith(b"%PDF"):
        return False, f"bad magic {b[:8].hex()}"
    if b"%%EOF" not in b[-32768:]:
        return False, "missing %%EOF"
    return True, f"ok {len(b)//1024}KB"


def _decode_zipname(raw: str) -> str:
    try:
        return raw.encode("cp437").decode("euc-kr")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return raw


def extract_disclosure_pdf(zip_bytes: bytes) -> tuple[bytes | None, str]:
    """From a 결산공시 ZIP keep only the 경영공시 본문 PDF (drop 감사/재무제표)."""
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


def main() -> int:
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            accept_downloads=True, ignore_https_errors=True, locale="ko-KR",
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
        )
        page = ctx.new_page()
        loaded = False
        for attempt in range(4):
            try:
                page.goto(URL, wait_until="networkidle", timeout=60000)
                page.wait_for_selector('a[id^="quarter"]', timeout=30000)
                loaded = True
                break
            except Exception as e:
                print(f"  goto attempt {attempt+1} failed: {str(e)[:60]} — retry")
                page.wait_for_timeout(2000)
        if not loaded:
            print("FATAL: could not load yebyeol page")
            browser.close()
            return 1
        page.wait_for_timeout(1500)

        for period, elem_id in TARGETS:
            try:
                with page.expect_download(timeout=45000) as dl_info:
                    page.eval_on_selector(f'#{elem_id}', "el => el.click()")
                dl = dl_info.value
                tmp = Path(dl.path())
                raw = tmp.read_bytes()
            except Exception as e:
                print(f"  [{period} {elem_id}] download failed: {str(e)[:70]}")
                results.append((period, elem_id, False, "dl err"))
                continue

            if raw[:2] == b"PK":
                data, picked = extract_disclosure_pdf(raw)
                if data is None:
                    print(f"  [{period}] zip extract failed: {picked}")
                    results.append((period, elem_id, False, picked))
                    continue
                print(f"    [{period}] picked from zip: {picked}")
            else:
                data = raw

            ok, why = verify_pdf(data)
            if not ok:
                print(f"  [{period}] verify failed: {why}")
                results.append((period, elem_id, False, why))
                continue

            outdir = ROOT / period / "raw"
            outdir.mkdir(parents=True, exist_ok=True)
            dest = outdir / f"{STEM}.pdf"
            dest.write_bytes(data)
            print(f"  [{period}] -> {dest.relative_to(ROOT.parent.parent)} ({why})")
            results.append((period, elem_id, True, why))

        ctx.close()
        browser.close()

    print("\n== SUMMARY ==")
    for period, elem_id, s, why in results:
        print(f"  {period} ({elem_id}): {'OK' if s else 'FAIL'}  {why}")
    print(f"  {sum(1 for *_, s, _ in results if s)}/{len(results)} ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
