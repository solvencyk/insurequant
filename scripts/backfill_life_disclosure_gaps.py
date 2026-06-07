# -*- coding: utf-8 -*-
"""Backfill missing 생보 정기경영공시 cells from 생명보험협회 통합공시.

pub.insure.or.kr/mngtDis list page: one row per life insurer, columns =
[회사명, 1분기, 2분기, 3분기, 결산]. Year via ?search_stdYear=YYYY.
Quarter → column: Q1=td[2], Q2=td[3], Q3=td[4], Q4(결산)=td[5].

Rows are matched by company-name text (not hardcoded index). Filename stem is
reused from the same insurer's existing files so naming stays consistent.

Output (canonical): data/disclosure/FY{YYYY}_Q{N}/raw/<stem>.pdf
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path("data/disclosure").resolve()
STAGE = Path("artifacts/disclosure_research/_tmp/life_gaps").resolve()
STAGE.mkdir(parents=True, exist_ok=True)

QCOL = {1: 2, 2: 3, 3: 4, 4: 5}  # quarter → td index (Q4=결산)

# (kr, site company-name to match, year, quarter, period_dir)
GAPS = [
    # IBK연금보험 (KR1011) — FY2023 Q1-Q4, FY2024 Q1-Q4, FY2025 Q1-Q3
    ("KR1011", "IBK연금보험", 2023, 1, "FY2023_Q1"),
    ("KR1011", "IBK연금보험", 2023, 2, "FY2023_Q2"),
    ("KR1011", "IBK연금보험", 2023, 3, "FY2023_Q3"),
    ("KR1011", "IBK연금보험", 2023, 4, "FY2023_Q4"),
    ("KR1011", "IBK연금보험", 2024, 1, "FY2024_Q1"),
    ("KR1011", "IBK연금보험", 2024, 2, "FY2024_Q2"),
    ("KR1011", "IBK연금보험", 2024, 3, "FY2024_Q3"),
    ("KR1011", "IBK연금보험", 2024, 4, "FY2024_Q4"),
    ("KR1011", "IBK연금보험", 2025, 1, "FY2025_Q1"),
    ("KR1011", "IBK연금보험", 2025, 2, "FY2025_Q2"),
    ("KR1011", "IBK연금보험", 2025, 3, "FY2025_Q3"),
    # AIA생명 (KR0080) — FY2023_Q4, FY2024_Q4 결산
    ("KR0080", "AIA생명", 2023, 4, "FY2023_Q4"),
    ("KR0080", "AIA생명", 2024, 4, "FY2024_Q4"),
]


def existing_stem(kr: str) -> str:
    for p in sorted(ROOT.glob("FY*_Q*")):
        raw = p / "raw"
        if not raw.exists():
            continue
        for f in raw.iterdir():
            if f.is_file() and f.name.startswith(kr + "_"):
                return f.stem.replace("_amended", "")
    return f"{kr}_생보"  # fallback


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
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
        )
        page = ctx.new_page()
        # cache page per year
        loaded_year = None
        for kr, cname, year, q, period in GAPS:
            if loaded_year != year:
                page.goto(f"https://pub.insure.or.kr/mngtDis/mngtDis/list.do?search_stdYear={year}",
                          wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(1200)
                loaded_year = year

            # find row index whose first cell == cname
            ridx = page.evaluate("""(cname)=>{
                const trs=document.querySelectorAll('#scroll_cont table tbody tr');
                for(let i=0;i<trs.length;i++){
                    const t=trs[i].querySelector('td')?.innerText.trim();
                    if(t===cname) return i+1;
                }
                return -1;
            }""", cname)
            if ridx < 0:
                print(f"  [{period}] {kr} {cname}: row not found")
                results.append((period, kr, False, "row not found"))
                continue

            td = QCOL[q]
            xp = f'//*[@id="scroll_cont"]/table/tbody/tr[{ridx}]/td[{td}]/a'
            try:
                with page.expect_download(timeout=60000) as dl:
                    page.locator(f"xpath={xp}").click()
                tmp = STAGE / f"{kr}_{period}.pdf"
                dl.value.save_as(str(tmp))
            except Exception as e:
                print(f"  [{period}] {kr} {cname}: download failed {e}")
                results.append((period, kr, False, f"dl err: {e}"))
                continue

            data = tmp.read_bytes()
            ok, why = verify_pdf(data)
            if not ok:
                print(f"  [{period}] {kr} {cname}: verify failed {why}")
                results.append((period, kr, False, why))
                continue

            outdir = ROOT / period / "raw"
            outdir.mkdir(parents=True, exist_ok=True)
            dest = outdir / f"{existing_stem(kr)}.pdf"
            dest.write_bytes(data)
            print(f"  [{period}] {kr} {cname} (tr{ridx}/td{td}) -> {dest.name} ({why})")
            results.append((period, kr, True, why))

        ctx.close()
        browser.close()

    ok = sum(1 for *_, s, _ in [(r[0], r[1], r[2], r[3]) for r in results] if s)
    print("\n== SUMMARY ==")
    for period, kr, s, why in results:
        print(f"  {period} {kr}: {'OK' if s else 'FAIL'}  {why}")
    n_ok = sum(1 for _, _, s, _ in results if s)
    print(f"  {n_ok}/{len(results)} ok")
    return 0 if n_ok == len(results) else 2


if __name__ == "__main__":
    sys.exit(main())
