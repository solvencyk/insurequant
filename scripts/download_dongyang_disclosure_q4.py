# -*- coding: utf-8 -*-
"""동양생명 (KR0087) 경영공시 결산(Q4) backfill — FY2023_Q4 + FY2024_Q4.

생명보험협회 통합공시 (pub.insure.or.kr/mngtDis). The list page lays out one
row per insurer, columns = [회사명, 1분기, 2분기, 3분기, 결산]. 동양생명 is
row 10 (tr[10]); the 결산 download link is td[5]/a. Year picked via
?search_stdYear=YYYY.

We already have 동양생명 Q1-Q3 for 2023/2024 and full 2025 + 2026.1Q; only
the two 결산(Q4) PDFs (FY2023_Q4, FY2024_Q4) are missing. Fetch just those.

Output (canonical): data/disclosure/FY{YYYY}_Q4/raw/KR0087_동양생명.pdf
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path("data/disclosure").resolve()
KR_NAME = "KR0087_동양생명"
ROW_XPATH = '//*[@id="scroll_cont"]/table/tbody/tr[10]/td[5]/a'  # 결산 column
STAGE = Path("artifacts/disclosure_research/_tmp/dongyang_q4").resolve()
STAGE.mkdir(parents=True, exist_ok=True)

TARGETS = [("2023", "FY2023_Q4"), ("2024", "FY2024_Q4")]


def verify_pdf(b: bytes) -> tuple[bool, str]:
    if not b.startswith(b"%PDF"):
        return False, f"bad magic {b[:8].hex()}"
    if b"%%EOF" not in b[-16384:] and b"%%EOF" not in b:
        return False, "missing %%EOF"
    return True, f"ok size={len(b)}"


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
        for yr, period in TARGETS:
            url = f"https://pub.insure.or.kr/mngtDis/mngtDis/list.do?search_stdYear={yr}"
            page.goto(url, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(1500)

            # sanity: confirm row 10 is 동양생명
            label = page.evaluate("""() => {
                const r = document.querySelector('#scroll_cont table tbody tr:nth-child(10)');
                return r ? r.querySelector('td')?.innerText.trim() : null;
            }""")
            if label != "동양생명":
                print(f"  [{period}] row10 != 동양생명 (got {label!r}) — aborting this period")
                results.append((period, False, f"row mismatch: {label}"))
                continue

            try:
                with page.expect_download(timeout=60000) as dl_info:
                    page.locator(f"xpath={ROW_XPATH}").click()
                dl = dl_info.value
                tmp = STAGE / f"{period}.pdf"
                dl.save_as(str(tmp))
            except Exception as e:
                print(f"  [{period}] download failed: {e}")
                results.append((period, False, f"download err: {e}"))
                continue

            data = tmp.read_bytes()
            ok, why = verify_pdf(data)
            if not ok:
                print(f"  [{period}] verify failed: {why}")
                results.append((period, False, why))
                continue

            outdir = ROOT / period / "raw"
            outdir.mkdir(parents=True, exist_ok=True)
            dest = outdir / f"{KR_NAME}.pdf"
            dest.write_bytes(data)
            print(f"  [{period}] OK -> {dest} ({why})")
            results.append((period, True, why))

        ctx.close()
        browser.close()

    print("\n== SUMMARY ==")
    ok = sum(1 for _, s, _ in results if s)
    for period, s, why in results:
        print(f"  {period}: {'OK' if s else 'FAIL'}  {why}")
    print(f"  {ok}/{len(results)} ok")
    return 0 if ok == len(results) else 2


if __name__ == "__main__":
    sys.exit(main())
