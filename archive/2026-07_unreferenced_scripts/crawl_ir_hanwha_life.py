# -*- coding: utf-8 -*-
"""한화생명 (KR0068) IR 실적발표자료: download ALL quarterly materials
(발표자료 deck + 팩트시트) for FY2023 1분기 ~ FY2026 1분기 via Selenium headless
Chrome into a staging dir. Each list row (li.list-col.btn-wrap) carries a title
(e.g. 'FY2026 1분기', 'FY2025 2025년도') and two buttons 발표자료 / 팩트시트.
Buttons have no href/onclick; JS handlers trigger the download on click.

Pagination: page 1 = FY2026 1Q .. FY2023 결산 (10 rows); page 2 = FY2023 3Q/2Q/1Q.
"""
import json
import re
import sys
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

sys.stdout.reconfigure(encoding="utf-8")
URL = "https://company.hanwhalife.com/ko/investment/investor/earnings-release"
STAGE = Path("data/ir/decks/hanwha_life").resolve()
STAGE.mkdir(parents=True, exist_ok=True)


def title_to_quarter(title: str):
    """'FY2026 1분기' -> 'FY2026_Q1'; 'FY2025 2025년도' -> 'FY2025_Q4'."""
    m = re.search(r"FY(\d{4})", title)
    if not m:
        return None
    fy = m.group(1)
    if "1분기" in title:
        q = "Q1"
    elif "2분기" in title or "상반기" in title:
        q = "Q2"
    elif "3분기" in title:
        q = "Q3"
    elif "년도" in title or "결산" in title or "연간" in title:
        q = "Q4"
    else:
        return None
    return f"FY{fy}_{q}"


def find_rows(d):
    """Return list of (title, row_el, [buttons]) for current page.

    Each data row is `ul.list-outer > li` and contains the title text
    (e.g. 'FY2026 1분기 발표자료 팩트시트') plus two <button>s whose label is
    carried by an inner <span> (so match on button.text)."""
    out = []
    rows = d.find_elements(By.CSS_SELECTOR, "ul.list-outer > li")
    for r in rows:
        txt = (r.text or "").strip().replace("\n", " ")
        if "FY" not in txt:  # skip header row '제목 첨부'
            continue
        m = re.search(r"FY\d{4}\s*\S+", txt)
        title = m.group(0).strip() if m else txt
        btns = r.find_elements(By.TAG_NAME, "button")
        out.append((title, r, btns))
    return out


_IGNORE_EXT = (".crdownload", ".tmp", ".htm", ".html", ".json")


def wait_download(before, timeout=60):
    for _ in range(timeout):
        time.sleep(1)
        if any(f.name.endswith(".crdownload") for f in STAGE.glob("*")):
            continue
        new = [f for f in STAGE.glob("*")
               if f.name not in before
               and not any(f.name.lower().endswith(e) for e in _IGNORE_EXT)]
        if new:
            return max(new, key=lambda p: p.stat().st_mtime)
    return None


def click_and_grab(d, btn, kind, quarter):
    before = {f.name for f in STAGE.glob("*")}
    d.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
    time.sleep(0.5)
    d.execute_script("arguments[0].click();", btn)
    got = wait_download(before)
    if got:
        # prefix with quarter+kind so we can sort later and avoid name clashes
        newname = f"{quarter}_{kind}_{got.name}"
        target = STAGE / newname
        if target.exists():
            target.unlink()
        # file handle may linger briefly; retry the rename
        for attempt in range(10):
            try:
                got.rename(target)
                break
            except PermissionError:
                time.sleep(1)
        else:
            print(f"    {kind}: rename locked, leaving {got.name}")
            return {"quarter": quarter, "kind": kind, "file": got.name,
                    "bytes": got.stat().st_size}
        print(f"    {kind}: {newname} ({target.stat().st_size} bytes)")
        return {"quarter": quarter, "kind": kind, "file": newname,
                "bytes": target.stat().st_size}
    print(f"    {kind}: TIMEOUT")
    return None


def main():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,5000")
    opts.add_argument("--lang=ko-KR")
    opts.add_experimental_option("prefs", {
        "download.default_directory": str(STAGE),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "plugins.always_open_pdf_externally": True,
    })
    d = webdriver.Chrome(options=opts)
    manifest = []
    grabbed = set()  # (quarter, kind)
    try:
        d.get(URL)
        time.sleep(9)
        d.execute_cdp_cmd("Page.setDownloadBehavior",
                          {"behavior": "allow", "downloadPath": str(STAGE)})
        for pg in range(2):  # page 1 + page 2 cover all target quarters
            rows = find_rows(d)
            print(f"== page {pg+1}: {[r[0] for r in rows]}")
            n = len(rows)
            for idx in range(n):
                rows = find_rows(d)  # re-fetch (DOM may re-render)
                if idx >= len(rows):
                    break
                title, _, btns = rows[idx]
                q = title_to_quarter(title)
                if not q:
                    print(f"  SKIP unmatched title: {title!r}")
                    continue
                print(f"  [{title}] -> {q}  ({len(btns)} btns)")
                # button order: 발표자료 (deck), 팩트시트 (factsheet)
                for btn in btns:
                    label = (btn.text or "").strip()
                    if "팩트" in label:
                        kind = "factsheet"
                    elif "발표" in label:
                        kind = "deck"
                    else:
                        continue
                    if (q, kind) in grabbed:
                        continue
                    rows2 = find_rows(d)
                    if idx >= len(rows2):
                        break
                    btns2 = rows2[idx][2]
                    tgt = None
                    for b2 in btns2:
                        lab2 = (b2.text or "").strip()
                        if kind == "factsheet" and "팩트" in lab2:
                            tgt = b2
                        elif kind == "deck" and "발표" in lab2:
                            tgt = b2
                    if tgt is None:
                        continue
                    rec = click_and_grab(d, tgt, kind, q)
                    if rec:
                        manifest.append(rec)
                        grabbed.add((q, kind))
            # next page
            if pg == 0:
                nxts = d.find_elements(
                    By.XPATH,
                    "//button[normalize-space(text())='2']")
                if nxts:
                    d.execute_script("arguments[0].click();", nxts[0])
                    time.sleep(5)
                else:
                    print("  (no page-2 button found)")
    finally:
        d.quit()
    (STAGE / "_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n== manifest ==")
    for r in manifest:
        print(f"  {r['quarter']:>11}  {r['kind']:>9}  {r['file']}  ({r['bytes']} B)")
    quarters = sorted({r["quarter"] for r in manifest})
    print(f"\ngrabbed quarters (any file): {quarters}")


if __name__ == "__main__":
    main()
