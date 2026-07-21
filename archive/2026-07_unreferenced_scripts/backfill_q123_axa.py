# -*- coding: utf-8 -*-
"""Backfill missing AXA (KR0049) quarterly 정기경영공시 PDFs from AXA's own site.

AXA regular-disclosure page renders a table with ONE row per disclosure period.
We enumerate every row, read its period label (year + quarter), and map
(year, quarter) -> download <a href>. Then for each missing target cell we GET
the PDF via the page request context (cookies follow), verify, and save to the
canonical disclosure layout.

Missing cells (4): FY2023 Q1, FY2023 Q3, FY2025 Q1, FY2025 Q3.

Output: data/disclosure/FY{YYYY}_Q{N}/raw/KR0049_악사손해보험.pdf
Failure dumps: artifacts/disclosure_research/_tmp/axa/
"""
from __future__ import annotations

import io
import re
import sys
import zipfile
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
DISC = ROOT / "data" / "disclosure"
TMP = ROOT / "artifacts" / "disclosure_research" / "_tmp" / "axa"
TMP.mkdir(parents=True, exist_ok=True)

PAGE = ("https://www.axa.co.kr/cms/AsianPlatformInternet/html/axacms/common/"
        "intro/disclosure/regular/index.html")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# Target (year, quarter) cells to backfill.
WANT = [(2023, 1), (2023, 3), (2025, 1), (2025, 3)]


# ---- verify helpers (mirrors backfill_nonlife_disclosure_kpub.py) ----
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
    """From a bundled ZIP, return the 경영공시 본문 PDF (drop 감사/재무제표/별첨)."""
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
        nm = c[1]
        low = nm.lower()
        return (
            0 if any(h in low for h in BODY_HINT) else 1,
            0 if nm.strip().startswith("[") else 1,
            -zf.getinfo(c[0].filename).file_size,
        )

    candidates.sort(key=rank)
    info, nm = candidates[0]
    return zf.read(info.filename), nm


def parse_period(label: str) -> tuple[int, int] | None:
    """Extract (year, quarter) from a period label string.

    Handles e.g. '2023년 1분기', '2023.1Q', '2023년 1/4분기', '2023 1Q', etc.
    """
    if not label:
        return None
    s = label.strip()
    # year: first 20YY
    ym = re.search(r"(20\d{2})", s)
    if not ym:
        return None
    year = int(ym.group(1))
    # quarter: '1분기' / '1/4분기' / '1Q' / 'Q1' / '제1분기'
    qm = re.search(r"([1-4])\s*/\s*4\s*분기", s)
    if not qm:
        qm = re.search(r"제?\s*([1-4])\s*분기", s)
    if not qm:
        qm = re.search(r"([1-4])\s*[Qq]", s)
    if not qm:
        qm = re.search(r"[Qq]\s*([1-4])", s)
    if not qm:
        return None
    return year, int(qm.group(1))


def main() -> int:
    results: dict[tuple[int, int], dict] = {}
    all_labels: list[str] = []
    period_map: dict[tuple[int, int], str] = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent=UA, accept_downloads=True,
            ignore_https_errors=True, locale="ko-KR",
        )
        page = ctx.new_page()
        page.set_default_timeout(30_000)

        loaded = False
        for attempt in range(4):
            try:
                page.goto(PAGE, wait_until="domcontentloaded", timeout=45_000)
                page.wait_for_timeout(2500)
                loaded = True
                break
            except Exception as e:
                print(f"  goto attempt {attempt+1} failed: {str(e)[:80]} — retrying")
                page.wait_for_timeout(2000)
        if not loaded:
            print("FATAL: could not load AXA page")
            (TMP / "load_fail.html").write_text(page.content(), encoding="utf-8")
            page.screenshot(path=str(TMP / "load_fail.png"), full_page=True)
            browser.close()
            return 1

        # Enumerate table rows. Each FY row has one year label (th/first cell)
        # plus per-quarter <td> cells (1/4분기, 2/4분기, 3/4분기, 전체), each
        # holding its own download <a>. Capture every cell's (label, href) so
        # we can map (year, quarter) precisely instead of taking only the first
        # link per row.
        rows = page.evaluate(r"""()=>{
            const out=[];
            const tables=document.querySelectorAll('table');
            tables.forEach(t=>{
                t.querySelectorAll('tbody tr').forEach(tr=>{
                    const rowText = tr.innerText.replace(/\s+/g,' ').trim();
                    const cells=[];
                    tr.querySelectorAll('th, td').forEach(c=>{
                        const a=c.querySelector('a[href]');
                        cells.push({
                            text: c.innerText.replace(/\s+/g,' ').trim(),
                            href: a ? a.getAttribute('href') : null,
                            title: a ? (a.getAttribute('title')||a.innerText.trim()) : '',
                        });
                    });
                    out.push({rowText, cells});
                });
            });
            return out;
        }""")

        for r in rows:
            row_text = (r.get("rowText") or "").strip()
            if not row_text:
                continue
            all_labels.append(row_text)
            # Year comes from the row text (single 20YY per FY row).
            ym = re.search(r"(20\d{2})", row_text)
            if not ym:
                continue
            year = int(ym.group(1))
            cells = r.get("cells") or []
            # Find which quarter each link-bearing cell corresponds to. Prefer
            # the cell's own label/title; fall back to positional order of the
            # link-bearing cells (1st link=Q1, 2nd=Q2, 3rd=Q3, 4th=전체/Q4).
            link_cells = [c for c in cells if c.get("href")]
            link_idx = 0
            for c in link_cells:
                ctext = f"{c.get('text','')} {c.get('title','')}"
                qm = re.search(r"([1-4])\s*/\s*[34]\s*분기", ctext)
                if not qm:
                    qm = re.search(r"제?\s*([1-4])\s*분기", ctext)
                if qm:
                    q = int(qm.group(1))
                elif "전체" in ctext or "결산" in ctext:
                    q = 4
                else:
                    # positional fallback within link cells
                    q = link_idx + 1 if link_idx < 3 else 4
                link_idx += 1
                key = (year, q)
                if key not in period_map:
                    period_map[key] = c["href"]

        print("== AXA table period labels ==")
        for lab in all_labels:
            print(f"  {lab}")
        print("== parsed (year,quarter)->href ==")
        for yq in sorted(period_map):
            print(f"  {yq}: {period_map[yq]}")

        # Download each target cell.
        for (year, q) in WANT:
            key = (year, q)
            href = period_map.get(key)
            if not href:
                results[key] = {"status": "미발행",
                                "evidence": "not present in AXA table rows"}
                print(f"  [{year} Q{q}] 미발행 — no matching row")
                continue
            url = urljoin(page.url, href)
            try:
                resp = ctx.request.get(url, headers={"Referer": PAGE}, timeout=60_000)
                if not resp.ok:
                    results[key] = {"status": "blocked",
                                    "error": f"HTTP {resp.status} {url}"}
                    print(f"  [{year} Q{q}] blocked HTTP {resp.status}")
                    continue
                raw = resp.body()
            except Exception as e:
                results[key] = {"status": "blocked", "error": str(e)[:120]}
                print(f"  [{year} Q{q}] blocked {str(e)[:80]}")
                continue

            picked = None
            if raw[:2] == b"PK":
                data, picked = extract_disclosure_pdf(raw)
                if data is None:
                    results[key] = {"status": "blocked",
                                    "error": f"zip extract: {picked}"}
                    print(f"  [{year} Q{q}] blocked zip extract: {picked}")
                    continue
            else:
                data = raw

            ok, why = verify_pdf(data)
            if not ok:
                # dump for inspection
                (TMP / f"{year}_Q{q}_badbody.bin").write_bytes(raw[:4096])
                results[key] = {"status": "blocked", "error": f"verify: {why}"}
                print(f"  [{year} Q{q}] blocked verify: {why}")
                continue

            outdir = DISC / f"FY{year}_Q{q}" / "raw"
            outdir.mkdir(parents=True, exist_ok=True)
            dest = outdir / "KR0049_악사손해보험.pdf"
            dest.write_bytes(data)
            results[key] = {"status": "collected", "bytes": len(data),
                            "path": str(dest.relative_to(ROOT)).replace("\\", "/"),
                            "src": url, "zip_pick": picked}
            kb = len(data) / 1024
            extra = f" (from zip: {picked})" if picked else ""
            print(f"  [{year} Q{q}] collected -> {dest.name} ({kb:.0f} KB){extra}")

        ctx.close()
        browser.close()

    print("\n== SUMMARY ==")
    for (year, q) in WANT:
        r = results.get((year, q), {"status": "?"})
        st = r["status"]
        if st == "collected":
            print(f"  FY{year}_Q{q}: collected ({r['bytes']/1024:.0f} KB)")
        elif st == "미발행":
            print(f"  FY{year}_Q{q}: 미발행 ({r.get('evidence')})")
        else:
            print(f"  FY{year}_Q{q}: blocked ({r.get('error')})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
