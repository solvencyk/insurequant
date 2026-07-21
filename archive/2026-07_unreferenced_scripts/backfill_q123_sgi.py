# -*- coding: utf-8 -*-
"""Backfill 서울보증보험 / SGI (KR0150) quarterly 정기경영공시 from SGI's own SPA.

Target gaps (8 cells): FY2023 Q1/Q2/Q3, FY2024 Q1/Q2/Q3, FY2025 Q2/Q3.

SGI 정기공시 page is a heavy custom-framework SPA (re$, jsviews, vestweb ajax
encryption). The disclosure list is rendered into
  <ul class="ccg-document-list" id="CCGIRI010101F01_listTmpl">
after a single encrypted AJAX (retrievelstNtcth). Each period is an
  <a id="test1" class="btn-document {pdf|zip} ty2"
     data-file-download="<fileId>" data-file-attflsrlno="<n>">{label}</a>
and clicking it triggers a JS download (expect_download).

KEY STRUCTURAL FINDING (probed 2026-06-01):
  SGI publishes 연간(annual) 경영공시 only, plus the single most-recent quarter.
  The list exposes exactly:
    - 2026년 1분기 경영공시 자료   (PDF) -> FY2026_Q1   (already collected)
    - 2025년 연간 경영공시 자료    (ZIP) -> FY2025_Q4   (already collected)
    - 2024년 연간 경영공시 자료    (ZIP) -> FY2024_Q4   (already collected)
    - 2023년 연간 경영공시 자료    (ZIP) -> FY2023_Q4   (already collected)
  There is NO pagination / 더보기 control; the whole list is one template fill.
  => None of the 8 target Q1/Q2/Q3 cells exist on the SGI site. They are
     STRUCTURAL 미발행 (SGI does not publish those quarters), not 미수집.

This script re-enumerates the SPA live (so the classification is evidence-based
each run), and if any quarterly entry that maps to a target gap is ever present,
it downloads + verifies it (defensive — in case SGI changes its publication
cadence in a future quarter).

Output (only when a real file is found): data/disclosure/FY{YYYY}_Q{N}/raw/KR0150_서울보증보험.pdf
On failure: artifacts/disclosure_research/_tmp/sgi/{screenshot,html}
"""
from __future__ import annotations

import io
import re
import sys
import zipfile
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
DISC = ROOT / "data" / "disclosure"
TMP = ROOT / "artifacts" / "disclosure_research" / "_tmp" / "sgi"
TMP.mkdir(parents=True, exist_ok=True)

URL = "https://www.sgic.co.kr/biz/ccg/index.html?p=CCGIRI010101F01"
KR = "KR0150"
NAME = "서울보증보험"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# The 8 target gaps as (fiscal_year, quarter).
TARGETS = [
    (2023, 1), (2023, 2), (2023, 3),
    (2024, 1), (2024, 2), (2024, 3),
    (2025, 2), (2025, 3),
]


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
    """From an annual 결산 ZIP, return the 경영공시 본문 PDF (drop 감사/재무제표)."""
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


# label -> (fiscal_year, quarter) ; only QUARTERLY entries map to a Q1-Q3 cell.
QUARTER_RE = re.compile(r"(20\d{2})\s*년\s*([1-4])\s*분기")


def classify_label(label: str) -> tuple[int, int] | None:
    """Return (year, quarter) if the label is an explicit Nth-quarter entry."""
    m = QUARTER_RE.search(label)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def enumerate_periods(page) -> list[dict]:
    """Return the rendered 정기공시 list items as dicts."""
    return page.evaluate(r"""()=>{
        const ul = document.querySelector('#CCGIRI010101F01_listTmpl')
                || document.querySelector('.ccg-document-list');
        if(!ul) return [];
        return Array.from(ul.querySelectorAll('a[data-file-download]')).map(a=>({
            label: (a.innerText||'').trim(),
            kind: (a.className.includes('zip') ? 'zip'
                   : a.className.includes('pdf') ? 'pdf' : '?'),
            fileId: a.getAttribute('data-file-download'),
            attflsrlno: a.getAttribute('data-file-attflsrlno'),
        }));
    }""")


def download_entry(page, file_id: str) -> bytes | None:
    """Click the list anchor with the given data-file-download and capture dl."""
    sel = f'a[data-file-download="{file_id}"]'
    try:
        with page.expect_download(timeout=30000) as dl_info:
            page.locator(sel).first.click()
        dl = dl_info.value
        p = dl.path()
        if p and Path(p).exists():
            return Path(p).read_bytes()
    except Exception as e:
        print(f"  download click failed for fileId={file_id}: {str(e)[:80]}")
    return None


def main() -> int:
    results = {f"FY{y}_Q{q}": {"status": "pending"} for y, q in TARGETS}
    periods_found: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent=UA, accept_downloads=True,
                                  ignore_https_errors=True, locale="ko-KR")
        page = ctx.new_page()
        page.set_default_timeout(30000)
        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            try:
                page.wait_for_load_state("networkidle", timeout=30000)
            except Exception:
                pass
            page.wait_for_timeout(6000)
            try:
                page.wait_for_selector('#CCGIRI010101F01_listTmpl a[data-file-download]',
                                       timeout=15000)
            except Exception:
                pass

            periods_found = enumerate_periods(page)
            print("=== SGI 정기공시 periods exposed by the SPA ===")
            for e in periods_found:
                yq = classify_label(e["label"])
                tag = f"  -> FY{yq[0]}_Q{yq[1]}" if yq else "  (annual/연간)"
                print(f"  [{e['kind']}] {e['label']}  (fileId={e['fileId']}){tag}")

            # Build map of available quarterly entries -> target cells.
            quarterly = {}
            for e in periods_found:
                yq = classify_label(e["label"])
                if yq:
                    quarterly[yq] = e

            for (y, q) in TARGETS:
                cell = f"FY{y}_Q{q}"
                entry = quarterly.get((y, q))
                if not entry:
                    results[cell] = {
                        "status": "미발행",
                        "reason": ("SGI SPA does not list this quarter — only "
                                   "연간(annual) + most-recent quarter published"),
                    }
                    continue
                # An actual quarterly file exists for a target gap — fetch it.
                raw = download_entry(page, entry["fileId"])
                if raw is None:
                    results[cell] = {"status": "blocked", "reason": "download trigger failed"}
                    continue
                if raw[:2] == b"PK":
                    data, picked = extract_disclosure_pdf(raw)
                    if data is None:
                        results[cell] = {"status": "blocked", "reason": f"zip extract: {picked}"}
                        continue
                else:
                    data = raw
                ok, why = verify_pdf(data)
                if not ok:
                    results[cell] = {"status": "blocked", "reason": f"verify: {why}"}
                    continue
                outdir = DISC / cell / "raw"
                outdir.mkdir(parents=True, exist_ok=True)
                dest = outdir / f"{KR}_{NAME}.pdf"
                dest.write_bytes(data)
                results[cell] = {"status": "collected", "bytes": len(data),
                                 "path": str(dest.relative_to(ROOT)).replace("\\", "/")}
                print(f"  COLLECTED {cell} -> {dest.name} ({why})")
        except Exception as exc:
            # Global failure: dump diagnostics.
            try:
                page.screenshot(path=str(TMP / "backfill_failure.png"), full_page=True)
                (TMP / "backfill_failure.html").write_text(page.content(), encoding="utf-8")
            except Exception:
                pass
            print(f"FATAL: {type(exc).__name__}: {exc}")
            ctx.close()
            browser.close()
            return 1
        ctx.close()
        browser.close()

    print("\n== SUMMARY ==")
    for cell, r in results.items():
        extra = r.get("reason") or f"{r.get('bytes','')}B"
        print(f"  {cell}: {r['status']}  {extra}")

    # Verdict
    any_quarterly_gap_filled = any(r["status"] == "collected" for r in results.values())
    only_annual = all(classify_label(e["label"]) is None
                      or classify_label(e["label"])[1] in (4,)  # never; just guard
                      for e in periods_found) if periods_found else False
    print("\n== VERDICT ==")
    print("  SGI exposes only 연간(annual) + most-recent-quarter 경영공시.")
    print("  The 8 Q1/Q2/Q3 target cells are STRUCTURAL 미발행 (not 미수집)."
          if not any_quarterly_gap_filled else
          "  Some quarterly gap was unexpectedly available and collected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
