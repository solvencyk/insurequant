#!/usr/bin/env python3
"""삼성화재해상보험 (KR0008) IR factsheet (xlsx) collector → disclosure layout.

Two stages:
 1) DOWNLOAD: drive the Samsung Fire IR SPA (VH.HPMK0201.do) with headless
    Selenium Chrome, iterate the quarter list (ul > li), click each li's
    "Factsheet" button (verified by button text), CDP download into a staging
    dir. (If the staging dir already has all quarters' xlsx, this is skipped.)
 2) ORGANIZE: copy each staged factsheet xlsx into
    data/ir/FY{YYYY}_Q{N}/KR0008_삼성화재해상보험/<original name>.

Samsung Fire factsheets are clean xlsx (no PDF parsing needed). The factsheet
filename encodes the quarter, e.g. "(KOR) 23.1Q 삼성화재.xlsx",
"(KOR) SFMI 26.1Q_f.xlsx", "(KOR) 삼성화재 25.4Q.xlsx".

RUN SOLO. One Chrome instance, one click at a time.
"""
import re
import shutil
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
URL = "https://www.samsungfire.com/vh/page/VH.HPMK0201.do"
STAGE = (ROOT / "data/ir/decks/samsung_fire").resolve()
STAGE.mkdir(parents=True, exist_ok=True)
COMPANY_DIR = "KR0008_삼성화재해상보험"

# all quarters we want, FY2023_Q1 .. FY2026_Q1
WANT_QUARTERS = [
    "FY2023_Q1", "FY2023_Q2", "FY2023_Q3", "FY2023_Q4",
    "FY2024_Q1", "FY2024_Q2", "FY2024_Q3", "FY2024_Q4",
    "FY2025_Q1", "FY2025_Q2", "FY2025_Q3", "FY2025_Q4",
    "FY2026_Q1",
]


def fname_to_quarter(name: str) -> str | None:
    """Map a factsheet filename like '(KOR) 23.1Q 삼성화재.xlsx' or
    '(KOR) SFMI 26.1Q_f.xlsx' or '(KOR) SFMI_24.4Q.xlsx' -> 'FY2024_Q4'."""
    # e.g. '23.1Q', 'SFMI_24.4Q', 'SFMI 26.1Q_f', '삼성화재 25.4Q'
    m = re.search(r"(\d{2})[._ ](\d)Q", name)
    if not m:
        return None
    yy, q = m.group(1), m.group(2)
    return f"FY20{yy}_Q{q}"


# ---------------------------------------------------------------------------
# Stage 1: download (only if staging is incomplete)
# ---------------------------------------------------------------------------
def staged_xlsx() -> dict[str, Path]:
    """quarter -> staged xlsx path (factsheets only)."""
    out: dict[str, Path] = {}
    for f in STAGE.glob("*.xlsx"):
        q = fname_to_quarter(f.name)
        if q:
            out[q] = f
    return out


def download_via_selenium() -> None:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,3000")
    opts.add_argument("--lang=ko-KR")
    opts.add_experimental_option("prefs", {
        "download.default_directory": str(STAGE),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "plugins.always_open_pdf_externally": True,
    })
    d = webdriver.Chrome(options=opts)
    try:
        d.get(URL)
        time.sleep(8)
        d.execute_cdp_cmd("Page.setDownloadBehavior",
                          {"behavior": "allow", "downloadPath": str(STAGE)})
        # The IR list: ul > li per quarter; each li has a button group whose
        # Factsheet button text contains 'Factsheet' / '팩트시트' / '팩트북'.
        lis = d.find_elements(
            By.XPATH,
            "//*[@id='baseMain']/div[2]/section[1]/div[2]/ul/li")
        print(f"{len(lis)} quarter rows on page")
        for i in range(len(lis)):
            lis = d.find_elements(
                By.XPATH,
                "//*[@id='baseMain']/div[2]/section[1]/div[2]/ul/li")
            if i >= len(lis):
                break
            li = lis[i]
            label = li.text.strip().split("\n")[0]
            btns = li.find_elements(By.TAG_NAME, "button")
            target = None
            for b in btns:
                t = (b.text or "").strip()
                if any(k in t for k in ("Factsheet", "팩트시트", "팩트북")):
                    target = b
                    break
            print(f"  li[{i+1}] '{label}' buttons={[b.text for b in btns]}")
            if target is None:
                continue
            before = {f.name for f in STAGE.glob("*")}
            d.execute_script("arguments[0].scrollIntoView({block:'center'});", target)
            time.sleep(0.4)
            d.execute_script("arguments[0].click();", target)
            for _ in range(30):
                time.sleep(1)
                if any(f.name.endswith(".crdownload") for f in STAGE.glob("*")):
                    continue
                new = [f for f in STAGE.glob("*")
                       if f.name not in before and not f.name.endswith(".crdownload")]
                if new:
                    print(f"    got {new[0].name}")
                    break
    finally:
        d.quit()


# ---------------------------------------------------------------------------
# Stage 2: organize into disclosure layout
# ---------------------------------------------------------------------------
def organize(staged: dict[str, Path]) -> list[tuple[str, Path]]:
    saved = []
    for q, src in sorted(staged.items()):
        dst_dir = ROOT / "data/ir" / q / COMPANY_DIR
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / src.name
        shutil.copy2(src, dst)
        saved.append((q, dst))
    return saved


def main():
    staged = staged_xlsx()
    missing = [q for q in WANT_QUARTERS if q not in staged]
    if missing:
        print(f"staging missing {missing}; running Selenium download...")
        download_via_selenium()
        staged = staged_xlsx()
        missing = [q for q in WANT_QUARTERS if q not in staged]
    else:
        print("all wanted quarters already staged; skipping download")

    saved = organize(staged)
    print("\n== organized factsheets ==")
    for q, dst in saved:
        print(f"  {q}  {dst}  ({dst.stat().st_size} B)")
    if missing:
        print(f"\nSTILL MISSING: {missing}")
    else:
        print("\nAll FY2023_Q1..FY2026_Q1 present.")


if __name__ == "__main__":
    main()
