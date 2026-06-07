# -*- coding: utf-8 -*-
"""Backfill 카카오페이손해보험 (KR1098) quarterly 정기경영공시 gaps.

Missing cells (3): FY2024_Q2, FY2025_Q2, FY2025_Q3.

The disclosure page is a React/SPA that renders ONE table with rows per
period. Each row exposes a direct <a href="https://static.kakaoinsure.com/...
.pdf|.zip"> 다운로드 link. We render the page, enumerate every row, map its
Korean period label -> (year, quarter), then download the 3 target cells.

Period-label -> quarter mapping (Korean 손보 disclosure cadence):
  "YYYY년 1분기"   -> Q1
  "YYYY년 상반기"  -> Q2   (반기 = 2/4분기)
  "YYYY년 3분기"   -> Q3
  "YYYY년 결산"/"4분기" -> Q4

When both a plain and a "(정정)" row exist for the same period we prefer the
정정 (KICS포함/최종) variant — it carries the K-ICS 도해 the parser needs.
This matches the already-collected FY2024_Q3 (12월 정정, KICS포함, 5.6MB).

Save to canonical plain stem (NO _amended):
  data/disclosure/FY{YYYY}_Q{N}/raw/KR1098_카카오페이손해보험.pdf
On failure: screenshot + HTML to artifacts/disclosure_research/_tmp/kakaopay/.
"""
from __future__ import annotations

import io
import re
import sys
import zipfile
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path("data/disclosure").resolve()
PAGE = "https://kakaopayinscorp.co.kr/disclosure/management"
STAGE = Path("artifacts/disclosure_research/_tmp/kakaopay").resolve()
STAGE.mkdir(parents=True, exist_ok=True)
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
STEM = "KR1098_카카오페이손해보험"

# Target cells to backfill.
WANT = [("FY2024_Q2"), ("FY2025_Q2"), ("FY2025_Q3")]


def label_to_period(label: str) -> str | None:
    """Map a Korean disclosure-row label to FY{YYYY}_Q{N}, or None if N/A."""
    m = re.search(r"(20\d{2})\s*년", label)
    if not m:
        return None
    year = int(m.group(1))
    if "1분기" in label:
        q = 1
    elif "상반기" in label or "2분기" in label or "2_4분기" in label or "2/4" in label:
        q = 2
    elif "3분기" in label:
        q = 3
    elif "결산" in label or "4분기" in label:
        q = 4
    else:
        return None
    # exclude pure 감사보고서 rows (not 경영공시)
    if "경영공시" not in label:
        return None
    return f"FY{year}_Q{q}"


def is_correction(label: str) -> bool:
    return ("정정" in label) or ("최종" in label and "정정" in label)


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
    """From a 경영공시 ZIP, return the 본문 PDF (drop 감사보고서/재무제표)."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile:
        return None, "bad zip"
    SUPPL = ("감사", "audit", "재무제표", "별첨", "reporting", "직인")
    BODY_HINT = ("경영공시", "disclosure", "공시")
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
            -zf.getinfo(c[0].filename).file_size,
        )

    candidates.sort(key=rank)
    info, nm = candidates[0]
    return zf.read(info.filename), nm


def main() -> int:
    results = []
    rows_dump = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            accept_downloads=True, ignore_https_errors=True, locale="ko-KR",
            user_agent=UA,
        )
        page = ctx.new_page()
        loaded = False
        for attempt in range(4):
            try:
                page.goto(PAGE, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_selector("table tbody tr", timeout=30000)
                loaded = True
                break
            except Exception as e:
                print(f"  goto attempt {attempt+1} failed: {str(e)[:70]} — retrying")
                page.wait_for_timeout(2500)
        if not loaded:
            page.screenshot(path=str(STAGE / "_load_fail.png"), full_page=True)
            (STAGE / "_load_fail.html").write_text(page.content(), encoding="utf-8")
            print("FATAL: could not load page; dump saved")
            browser.close()
            return 1
        page.wait_for_timeout(2500)

        rows = page.evaluate(r"""()=>{
            const out=[];
            document.querySelectorAll('table tbody tr').forEach(r=>{
                const cells=Array.from(r.querySelectorAll('td,th')).map(c=>c.innerText.trim());
                const a=r.querySelector('a[href]');
                out.push({cells, href: a? a.getAttribute('href'):null});
            });
            return out;
        }""")

        # Build period -> chosen href. Among rows for the same period, prefer
        # the 정정/KICS variant (later filing). Keep first-seen as fallback.
        period_pick: dict[str, dict] = {}
        for r in rows:
            cells = r["cells"]
            href = r["href"]
            # label is the cell containing 경영공시 text
            label = next((c for c in cells if "공시" in c or "분기" in c or "결산" in c or "상반기" in c), "")
            rows_dump.append({"label": label, "href": href})
            period = label_to_period(label)
            if not period or not href:
                continue
            corr = is_correction(label)
            kics = "kics" in href.lower() or "KICS" in href
            score = (1 if corr else 0) + (1 if kics else 0)
            prev = period_pick.get(period)
            if prev is None or score > prev["score"]:
                period_pick[period] = {"href": href, "label": label, "score": score}

        print("== period labels exposed by site ==")
        for rd in rows_dump:
            print(f"  {rd['label']!r}")
        print("\n== resolved period -> chosen download ==")
        for per in sorted(period_pick):
            print(f"  {per}: {period_pick[per]['label']!r}")

        for period in WANT:
            pick = period_pick.get(period)
            if not pick:
                print(f"\n[{period}] NO matching row on site")
                results.append((period, "missing", "no row matched on site"))
                continue
            href = pick["href"]
            url = href if href.startswith("http") else "https://kakaopayinscorp.co.kr" + href
            print(f"\n[{period}] downloading: {pick['label']!r}")
            print(f"           url: {url}")
            try:
                resp = ctx.request.get(url, timeout=90000)
                if resp.status != 200:
                    print(f"  HTTP {resp.status}")
                    results.append((period, "blocked", f"http {resp.status}"))
                    continue
                raw = resp.body()
            except Exception as e:
                print(f"  download failed: {str(e)[:80]}")
                results.append((period, "blocked", "dl err"))
                continue

            if raw[:2] == b"PK":
                data, picked = extract_disclosure_pdf(raw)
                if data is None:
                    print(f"  zip extract failed: {picked}")
                    results.append((period, "blocked", f"zip: {picked}"))
                    continue
                print(f"  picked from zip: {picked}")
            else:
                data = raw

            ok, why = verify_pdf(data)
            if not ok:
                print(f"  verify failed: {why}")
                (STAGE / f"{period}_badbody.bin").write_bytes(data[:4096])
                results.append((period, "blocked", why))
                continue

            outdir = ROOT / period / "raw"
            outdir.mkdir(parents=True, exist_ok=True)
            dest = outdir / f"{STEM}.pdf"
            dest.write_bytes(data)
            print(f"  OK -> {period}/raw/{dest.name} ({why})")
            results.append((period, "collected", why))

        ctx.close()
        browser.close()

    print("\n== SUMMARY ==")
    for period, status, why in results:
        print(f"  {period}: {status.upper()}  {why}")
    ok = sum(1 for _, s, _ in results if s == "collected")
    print(f"  {ok}/{len(results)} collected")
    return 0 if ok == len(WANT) else 2


if __name__ == "__main__":
    sys.exit(main())
