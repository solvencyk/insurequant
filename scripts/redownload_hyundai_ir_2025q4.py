# -*- coding: utf-8 -*-
"""One-off: re-download 현대해상 (KR0009) FY2025_Q4 Factsheet.

The original crawl produced a Factsheet xlsx with a bogus magic
(4372323403000000) that Excel can't open. Re-fetch from hi.co.kr and
overwrite the broken file in canonical layout
data/ir/FY2025_Q4/raw/KR0009_현대해상/.

Reuses the proven goMenu('101641') + doBizFileDownload click pattern.
"""
import re
import sys
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

sys.stdout.reconfigure(encoding="utf-8")

ENTRY = "https://www.hi.co.kr/serviceAction.do?view=bin/KC/00/HHKC00000M"
KR_DIR = "KR0009_현대해상"
ROOT = Path("data/ir").resolve()
STAGE = Path("artifacts/ir_research/_tmp/hi_dl_2025q4").resolve()
STAGE.mkdir(parents=True, exist_ok=True)

TARGET_FY = 2025
TARGET_Q = 4

PATH_RE = re.compile(r"doBizFileDownload\('([^']+)'\)")
WANT_LABELS = {"Factsheet": "Factsheet", "발표자료": "presentation"}


def title_to_quarter(title: str):
    t = title.strip()
    m = re.search(r"(20\d{2})\.\s*([1-4])Q\s*경영실적", t)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r"(20\d{2})\.\s*([1-4])분기", t)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r"(20\d{2})\s*상반기", t)
    if m:
        return int(m.group(1)), 2
    m = re.search(r"(20\d{2})\s*경영실적\s*및", t)
    if m:
        return int(m.group(1)), 4
    return None


def goto_list(d):
    d.get(ENTRY)
    WebDriverWait(d, 25).until(lambda x: x.execute_script("return typeof goMenu === 'function';"))
    d.execute_script("goMenu('101641');")
    WebDriverWait(d, 25).until(EC.presence_of_element_located((By.ID, "rstbzYear")))
    WebDriverWait(d, 25).until(lambda x: len(x.find_elements(By.CSS_SELECTOR, "div.ir_item")) > 0)


def wait_download(before, timeout=90):
    for _ in range(timeout):
        time.sleep(1)
        if any(f.name.endswith(".crdownload") for f in STAGE.glob("*")):
            continue
        new = [f for f in STAGE.glob("*") if f.name not in before and not f.name.endswith(".crdownload")]
        if new:
            return max(new, key=lambda p: p.stat().st_mtime)
    return None


def main():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,6000")
    opts.add_argument("--lang=ko-KR")
    opts.add_experimental_option("prefs", {
        "download.default_directory": str(STAGE),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "plugins.always_open_pdf_externally": True,
    })
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
    d = webdriver.Chrome(options=opts)
    outdir = ROOT / f"FY{TARGET_FY}_Q{TARGET_Q}" / "raw" / KR_DIR
    outdir.mkdir(parents=True, exist_ok=True)
    print(f"target: FY{TARGET_FY}_Q{TARGET_Q} -> {outdir}")

    try:
        for attempt in range(3):
            try:
                goto_list(d)
                break
            except Exception as e:
                print(f"  goto_list attempt {attempt+1} failed: {e}")
                time.sleep(3)
        else:
            raise SystemExit("could not load 실적발표자료 list")
        d.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(STAGE)})

        # 2025년 annual = FY2025_Q4 ("2025 경영실적 및 ..." title)
        Select(d.find_element(By.ID, "rstbzYear")).select_by_value("2025")
        time.sleep(4)
        items = d.find_elements(By.CSS_SELECTOR, "div.ir_item")
        print(f"== year 2025: {len(items)} items ==")

        for item in items:
            try:
                title = item.find_element(By.CSS_SELECTOR, "div.ir_title").text.strip()
            except Exception:
                continue
            q = title_to_quarter(title)
            if not q or q != (TARGET_FY, TARGET_Q):
                continue
            print(f"  [{title}] matches target")

            for label, token in WANT_LABELS.items():
                btns = item.find_elements(
                    By.XPATH, f".//a[.//span[normalize-space(text())='{label}']]"
                )
                if not btns:
                    print(f"    {label}: no button found")
                    continue
                onclick = btns[0].get_attribute("onclick") or ""
                pm = PATH_RE.search(onclick)
                ext = (pm.group(1).split(".")[-1].lower() if pm else "bin")
                before = {f.name for f in STAGE.glob("*")}
                d.execute_script("arguments[0].scrollIntoView({block:'center'});", btns[0])
                time.sleep(0.5)
                d.execute_script("arguments[0].click();", btns[0])
                got = wait_download(before)
                if not got:
                    print(f"    {label}: TIMEOUT")
                    continue
                # check magic
                head = got.read_bytes()[:8]
                if ext == "xlsx" and not head.startswith(b"PK\x03\x04"):
                    print(f"    {label}: BAD MAGIC {head.hex()[:16]} - leaving in stage for inspection")
                    continue
                if ext == "pdf" and not head.startswith(b"%PDF"):
                    print(f"    {label}: BAD MAGIC {head.hex()[:16]} - leaving in stage for inspection")
                    continue
                dest = outdir / f"hyundai_FY{TARGET_FY}_Q{TARGET_Q}_{token}.{ext}"
                if dest.exists():
                    backup = dest.with_suffix(dest.suffix + ".bad")
                    if backup.exists():
                        backup.unlink()
                    dest.replace(backup)
                    print(f"    backed up old to {backup.name}")
                got.replace(dest)
                sz = dest.stat().st_size
                print(f"    {label}: {dest.name} ({sz} bytes, magic={head.hex()[:16]})")
            break
        else:
            print("  no matching item found for FY2025_Q4")
    finally:
        d.quit()


if __name__ == "__main__":
    main()
