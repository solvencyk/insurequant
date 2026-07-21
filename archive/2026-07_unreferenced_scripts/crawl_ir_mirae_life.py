#!/usr/bin/env python3
"""미래에셋생명 (KR0079) IR 자료실 크롤러.

Renders life.miraeasset.com IR 자료실 microsite, iterates the year <select>
(2023..2026), and for each row triggers the page's own fileDownload(org,lst) JS
handler (COMUTIL.fileDown -> server stream) with CDP download enabled. Files are
saved to a temp dir, then organized into
  data/ir/FY{YYYY}_Q{N}/KR0079_미래에셋생명/<orgFileName>
per the row title (연간->Q4, 3분기/Q3->Q3, 2분기/Q2->Q2, 1분기/Q1->Q1).
Life insurer => FY == calendar year.

Targets FY2023.1Q ~ FY2026.1Q. Prefers Excel Fact Sheet but also grabs the
Results PDF deck for each quarter.
"""
import re
import shutil
import sys
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
URL = "https://life.miraeasset.com/micro/company/PC-HO-060401-000000.do"
KR_DIR = "KR0079_미래에셋생명"
TMP = ROOT / "data" / "ir" / "_tmp_mirae"
YEARS = ["2023", "2024", "2025", "2026"]


def quarter_from_title(title: str):
    """Return 'Q1'..'Q4' from an IR row title, or None."""
    t = title
    if "연간" in t or re.search(r"\bFY\d{4}\b(?!\s*Q)", t) and "Q" not in t.split("FY")[-1][:8]:
        # '연간' or 'FY2018 연간' -> Q4. Handle bare 'FYxxxx Results' (annual) too.
        if "연간" in t:
            return "Q4"
    m = re.search(r"Q\s*([1-4])", t)
    if m:
        return f"Q{m.group(1)}"
    m = re.search(r"([1-4])\s*분기", t)
    if m:
        return f"Q{m.group(1)}"
    if "연간" in t:
        return "Q4"
    return None


def year_from_title(title: str):
    m = re.search(r"FY?\s*(\d{4})", title)
    if m:
        return m.group(1)
    m = re.search(r"\b(20\d{2})\b", title)
    return m.group(1) if m else None


def is_target(kind: str, year: str, q: str) -> bool:
    """FY2023.1Q..FY2026.1Q window; we want Fact Sheet (xlsx) + Results (pdf)."""
    if not year or not q:
        return False
    y = int(year)
    if y < 2023 or y > 2026:
        return False
    if y == 2026 and q != "Q1":
        return False
    return kind in ("fact", "results")


def classify(title: str):
    if "Fact" in title or "FactSheet" in title:
        return "fact"
    if "녹취" in title:
        return "audio"
    if "감사보고서" in title or "지속가능" in title:
        return "other"
    if "실적발표" in title or "Results" in title:
        return "results"
    return "other"


def main():
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True, exist_ok=True)

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,3000")
    opts.add_experimental_option("prefs", {
        "download.default_directory": str(TMP),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    })
    d = webdriver.Chrome(options=opts)
    log = []
    try:
        d.get(URL)
        time.sleep(6)
        d.execute_cdp_cmd("Page.setDownloadBehavior",
                          {"behavior": "allow", "downloadPath": str(TMP)})
        sel_el = d.find_element(By.TAG_NAME, "select")
        for y in YEARS:
            try:
                Select(sel_el).select_by_value(y)
            except Exception:
                Select(sel_el).select_by_visible_text(y)
            time.sleep(3)
            try:
                sel_el = d.find_element(By.TAG_NAME, "select")
            except Exception:
                pass
            # collect (title, org, lst) from anchors with fileDownload onclick
            anchors = d.find_elements(By.XPATH, "//a[contains(@onclick,'fileDownload')]")
            rows = []
            for a in anchors:
                oc = a.get_attribute("onclick") or ""
                m = re.search(r"fileDownload\('([^']+)','([^']+)'\)", oc)
                if not m:
                    continue
                # title from sibling span.box-list-tit
                try:
                    title = a.find_element(By.CSS_SELECTOR, "span.box-list-tit").text.strip()
                except Exception:
                    title = (a.text or "").strip()
                rows.append((title, m.group(1), m.group(2)))
            print(f"[year {y}] {len(rows)} download rows")
            for title, org, lst in rows:
                kind = classify(title)
                yr = year_from_title(title) or y
                q = quarter_from_title(title)
                if not is_target(kind, yr, q):
                    continue
                before = {p.name for p in TMP.glob("*") if not p.name.endswith(".crdownload")}
                # trigger the page's own handler with these exact args
                d.execute_script(
                    "fileDownload(arguments[0], arguments[1]);", org, lst)
                got = None
                for _ in range(50):
                    time.sleep(1)
                    if any(f.name.endswith(".crdownload") for f in TMP.glob("*")):
                        continue
                    new = [f for f in TMP.glob("*")
                           if f.name not in before and not f.name.endswith(".crdownload")]
                    if new:
                        got = max(new, key=lambda p: p.stat().st_mtime)
                        break
                if not got:
                    log.append(f"FAIL  FY{yr} {q} {kind} :: {org} (timeout)")
                    print(f"   FAIL {title} -> timeout")
                    continue
                # organize
                dest_dir = ROOT / "data" / "ir" / f"FY{yr}_{q}" / KR_DIR
                dest_dir.mkdir(parents=True, exist_ok=True)
                # use the human org filename; fall back to downloaded name
                target_name = org if got.suffix and org.lower().endswith(got.suffix.lower()) else got.name
                dest = dest_dir / target_name
                shutil.move(str(got), str(dest))
                sz = dest.stat().st_size
                log.append(f"OK    FY{yr} {q} {kind:7s} {sz:>10,d}  {dest.relative_to(ROOT)}")
                print(f"   OK [{kind}] FY{yr} {q}  {sz:,} bytes  {target_name}")
    finally:
        d.quit()
        if TMP.exists():
            try:
                TMP.rmdir()
            except OSError:
                pass

    print("\n===== MIRAE DOWNLOAD LOG =====")
    print("\n".join(log))


if __name__ == "__main__":
    main()
