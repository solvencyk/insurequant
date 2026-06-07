# -*- coding: utf-8 -*-
"""Backfill 손보 연간(결산) 정기경영공시 from 손해보험협회 통합공시 (kpub.knia.or.kr).

The kpub 정기경영공시 page renders ONE table:
  rows  = 손보사 (th scope="row")
  cols  = 연도 (left→right: 2025, 2024, 2023, 2022, 2021) — ANNUAL/결산 only,
          NOT quarterly. Each cell = <a href="/file/download/<id>.do">다운로드</a>.

So this site only carries the annual 결산 disclosure (= our FY{YYYY}_Q4). The
quarterly (Q1-Q3) 손보 공시 lives on each insurer's own site, not here.

This script maps company-name → KR code, column-index → year, and downloads
the requested (KR, year) 결산 PDFs into canonical
  data/disclosure/FY{YYYY}_Q4/raw/<stem>.pdf
"""
import io
import sys
import zipfile
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path("data/disclosure").resolve()
PAGE = "https://kpub.knia.or.kr/managementDisc/regularly/regularlyDisclosure.do"
BASE = "https://kpub.knia.or.kr"
STAGE = Path("artifacts/disclosure_research/_tmp/kpub").resolve()
STAGE.mkdir(parents=True, exist_ok=True)

# kpub row label → KR code
NAME_TO_KR = {
    "메리츠화재": "KR0001", "한화손보": "KR0002", "롯데손보": "KR0003",
    "흥국화재": "KR0005", "삼성화재": "KR0008", "현대해상": "KR0009",
    "KB손보": "KR0010", "DB손보": "KR0011", "서울보증": "KR0150",
    "코리안리": "KR1000", "AXA손보": "KR0049", "하나손보": "KR0050",
    "AIG손보": "KR0029", "신한EZ손해보험": "KR0051",
    "카카오페이손해보험": "KR1098", "농협손보": "KR0032",
}

# Column index → year (left→right per kpub layout). Updated dynamically from
# the header if possible; this is the documented default.
DEFAULT_COL_YEARS = [2025, 2024, 2023, 2022, 2021]

# 손보 결산(Q4) gaps to fill: (KR, year)
WANT = [
    ("KR0010", 2023),  # KB손보 FY2023_Q4
    ("KR0032", 2024),  # 농협손보 FY2024_Q4
    ("KR0029", 2023),  # AIG손보 FY2023_Q4
    ("KR0029", 2024),  # AIG손보 FY2024_Q4
    ("KR0049", 2023),  # AXA손보 FY2023_Q4
    ("KR0051", 2023),  # 신한EZ FY2023_Q4
    ("KR0051", 2024),  # 신한EZ FY2024_Q4
    ("KR0150", 2024),  # 서울보증 FY2024_Q4
]


def existing_stem(kr: str) -> str:
    for p in sorted(ROOT.glob("FY*_Q*")):
        raw = p / "raw"
        if not raw.exists():
            continue
        for f in raw.iterdir():
            if f.is_file() and f.name.startswith(kr + "_"):
                return f.stem.replace("_amended", "")
    return None


def verify_pdf(b: bytes) -> tuple[bool, str]:
    if not b.startswith(b"%PDF"):
        return False, f"bad magic {b[:8].hex()}"
    if b"%%EOF" not in b[-16384:] and b"%%EOF" not in b:
        return False, "missing %%EOF"
    return True, f"ok {len(b)}B"


def _decode_zipname(raw: str) -> str:
    """ZIP stores Korean names as cp437-mojibake when the UTF-8 flag is off."""
    try:
        return raw.encode("cp437").decode("euc-kr")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return raw


def extract_disclosure_pdf(zip_bytes: bytes) -> tuple[bytes | None, str]:
    """From the kpub 결산공시 ZIP, return the 경영공시 본문 PDF bytes.

    The ZIP bundles 감사보고서(별도/연결) + 재무제표 감사보고서 + the actual
    결산경영공시 본문. Per project rule (감사보고서/재무제표 무시) we keep ONLY
    the 경영공시 본문 — filename contains '경영공시' and excludes 감사/재무제표.
    """
    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile:
        return None, "bad zip"
    # Supplements to drop (감사보고서 / 재무제표 / 별첨 / K-ICS reporting / 지급여력 감사)
    SUPPL = ("감사", "audit", "재무제표", "별첨", "reporting", "지급여력")
    BODY_HINT = ("경영공시", "disclosure", "현황", "공시")  # 본문 hints
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
    # prefer body-hint names, then '[' prefix convention, then largest file
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
                page.goto(PAGE, wait_until="commit", timeout=45000)
                page.wait_for_selector('a[href*="file/download"]', timeout=30000)
                loaded = True
                break
            except Exception as e:
                print(f"  goto attempt {attempt+1} failed: {str(e)[:60]} — retrying")
                page.wait_for_timeout(2000)
        if not loaded:
            print("FATAL: could not load kpub page after retries")
            browser.close()
            return 1
        page.wait_for_timeout(1500)

        # Build mapping: KR -> {year -> download-href}. Read the table whose
        # rows have th[scope=row]=회사명 and cells with file/download links.
        table = page.evaluate(r"""()=>{
            const tbls=document.querySelectorAll('table');
            let target=null;
            tbls.forEach(t=>{ if(t.querySelector('a[href*="file/download"]')) target=t; });
            if(!target) return null;
            // header year cells (may include a leading 회사명 col)
            const headCells=Array.from(target.querySelectorAll('thead th, thead td')).map(c=>c.innerText.trim());
            const rows=Array.from(target.querySelectorAll('tbody tr')).map(r=>{
                const name=(r.querySelector('th[scope=row], th, td')||{}).innerText?.trim();
                const dls=Array.from(r.querySelectorAll('a[href*="file/download"]')).map(a=>a.getAttribute('href'));
                return {name, dls};
            });
            return {headCells, rows};
        }""")
        if not table:
            print("FATAL: download table not found")
            browser.close()
            return 1

        # Determine column→year. Header may be like ['회사명','2025','2024',...]
        years_from_head = [int(h[:4]) for h in table["headCells"] if h[:4].isdigit()]
        col_years = years_from_head if len(years_from_head) >= 3 else DEFAULT_COL_YEARS
        print(f"column years: {col_years}")

        # KR -> {year: href}
        kr_year_href = {}
        for row in table["rows"]:
            nm = (row["name"] or "").strip()
            kr = NAME_TO_KR.get(nm)
            if not kr:
                continue
            mp = {}
            for i, href in enumerate(row["dls"]):
                if i < len(col_years):
                    mp[col_years[i]] = href
            kr_year_href[kr] = mp
            print(f"  {kr} {nm}: years={sorted(mp.keys())}")

        # Download each wanted cell
        for kr, year in WANT:
            href = kr_year_href.get(kr, {}).get(year)
            if not href:
                print(f"  [{kr} {year}] no download link")
                results.append((kr, year, False, "no link"))
                continue
            url = href if href.startswith("http") else BASE + href
            period = f"FY{year}_Q4"
            try:
                # Direct GET with the page's session cookies (file/download link)
                resp = ctx.request.get(url, timeout=60000)
                if resp.status != 200:
                    print(f"  [{kr} {year}] HTTP {resp.status}")
                    results.append((kr, year, False, f"http {resp.status}"))
                    continue
                raw = resp.body()
            except Exception as e:
                print(f"  [{kr} {year}] download failed: {str(e)[:60]}")
                results.append((kr, year, False, "dl err"))
                continue

            # kpub delivers a ZIP bundling 경영공시 본문 + 감사보고서 — keep only 본문
            if raw[:2] == b"PK":
                data, picked = extract_disclosure_pdf(raw)
                if data is None:
                    print(f"  [{kr} {year}] zip extract failed: {picked}")
                    results.append((kr, year, False, picked))
                    continue
                print(f"    picked from zip: {picked}")
            else:
                data = raw

            ok, why = verify_pdf(data)
            if not ok:
                print(f"  [{kr} {year}] verify failed: {why}")
                results.append((kr, year, False, why))
                continue

            stem = existing_stem(kr) or f"{kr}_손보"
            outdir = ROOT / period / "raw"
            outdir.mkdir(parents=True, exist_ok=True)
            dest = outdir / f"{stem}.pdf"
            dest.write_bytes(data)
            print(f"  [{kr} {year}] -> {period}/{dest.name} ({why})")
            results.append((kr, year, True, why))

        ctx.close()
        browser.close()

    print("\n== SUMMARY ==")
    n_ok = sum(1 for *_, s, _ in [(r[0], r[1], r[2], r[3]) for r in results] if s)
    for kr, year, s, why in results:
        print(f"  {kr} {year}: {'OK' if s else 'FAIL'}  {why}")
    print(f"  {sum(1 for _,_,s,_ in results if s)}/{len(results)} ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
