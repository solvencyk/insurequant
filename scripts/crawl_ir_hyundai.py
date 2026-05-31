# -*- coding: utf-8 -*-
"""현대해상 (KR0009) IR 실적발표자료 downloader.

hi.co.kr IR is a JS SPA: 실적발표자료 list is rendered via goMenu('101641');
each row (div.ir_item) has a div.ir_title + div.ir_detail with
doBizFileDownload('/data/..') buttons (발표자료 PDF, Factsheet xlsx).

Direct GET of /data/.. 404s (download goes through a REST endpoint with a
token), so we use the proven headless-click method: enable headless download,
click each button, wait for the file to land in a staging dir, then move it
into data/ir/FY{YYYY}_Q{N}/KR0009_현대해상/ with a friendly name.

Quarter mapping (현대해상 FY = calendar year): 'YYYY.NQ 경영실적' -> Q N;
'YYYY 경영실적 및 ...' (annual) -> Q4.
"""
import json
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
STAGE = Path("artifacts/ir_research/_tmp/hi_dl").resolve()
STAGE.mkdir(parents=True, exist_ok=True)
WANT_FY = list(range(2023, 2027))
PATH_RE = re.compile(r"doBizFileDownload\('([^']+)'\)")
# labels we want, mapped to a friendly file-name token
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
    WebDriverWait(d, 25).until(
        lambda x: x.execute_script("return typeof goMenu === 'function';")
    )
    d.execute_script("goMenu('101641');")
    WebDriverWait(d, 25).until(EC.presence_of_element_located((By.ID, "rstbzYear")))
    WebDriverWait(d, 25).until(
        lambda x: len(x.find_elements(By.CSS_SELECTOR, "div.ir_item")) > 0
    )


def wait_download(before, timeout=60):
    for _ in range(timeout):
        time.sleep(1)
        if any(f.name.endswith(".crdownload") for f in STAGE.glob("*")):
            continue
        new = [f for f in STAGE.glob("*")
               if f.name not in before and not f.name.endswith(".crdownload")]
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
    manifest = []
    seen_q = set()
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
        d.execute_cdp_cmd("Page.setDownloadBehavior",
                          {"behavior": "allow", "downloadPath": str(STAGE)})

        for yr in ["2026", "2025", "2024", "2023"]:
            try:
                Select(d.find_element(By.ID, "rstbzYear")).select_by_value(yr)
            except Exception as e:
                print(f"  year {yr} select failed: {e}")
                continue
            time.sleep(4)
            n_items = len(d.find_elements(By.CSS_SELECTOR, "div.ir_item"))
            print(f"== year {yr}: {n_items} items ==")
            for idx in range(n_items):
                # re-fetch items each iteration (DOM stable but safe)
                items = d.find_elements(By.CSS_SELECTOR, "div.ir_item")
                if idx >= len(items):
                    break
                item = items[idx]
                try:
                    title = item.find_element(By.CSS_SELECTOR, "div.ir_title").text.strip()
                except Exception:
                    continue
                q = title_to_quarter(title)
                if not q or q[0] not in WANT_FY or q in seen_q:
                    continue
                fy, qn = q
                outdir = ROOT / f"FY{fy}_Q{qn}" / KR_DIR
                outdir.mkdir(parents=True, exist_ok=True)
                print(f"  [{title}] -> FY{fy}_Q{qn}")
                grabbed = False
                for label, token in WANT_LABELS.items():
                    btns = item.find_elements(
                        By.XPATH,
                        f".//a[.//span[normalize-space(text())='{label}']]")
                    if not btns:
                        continue
                    path = PATH_RE.search(btns[0].get_attribute("onclick") or "")
                    ext = (path.group(1).split(".")[-1].lower() if path else "bin")
                    before = {f.name for f in STAGE.glob("*")}
                    d.execute_script("arguments[0].scrollIntoView({block:'center'});", btns[0])
                    time.sleep(0.4)
                    d.execute_script("arguments[0].click();", btns[0])
                    got = wait_download(before)
                    if not got:
                        print(f"      {label}: TIMEOUT")
                        continue
                    dest = outdir / f"hyundai_FY{fy}_Q{qn}_{token}.{ext}"
                    if dest.exists():
                        dest.unlink()
                    got.replace(dest)
                    sz = dest.stat().st_size
                    print(f"      {label}: {dest.name} ({sz} bytes)")
                    manifest.append({
                        "fy": fy, "q": qn, "title": title, "label": label,
                        "file": str(dest), "bytes": sz,
                    })
                    grabbed = True
                if grabbed:
                    seen_q.add(q)
    finally:
        d.quit()
    Path("data/ir/_hyundai_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    got = sorted({(m["fy"], m["q"]) for m in manifest})
    print("\n== Hyundai manifest ==")
    for m in manifest:
        print(f"  FY{m['fy']}_Q{m['q']}  {m['label']:>10}  {Path(m['file']).name}  ({m['bytes']} B)")
    want = [(fy, qn) for fy in WANT_FY for qn in (1, 2, 3, 4)
            if not (fy == 2026 and qn > 1)]
    missing = [q for q in want if q not in got]
    print(f"\ngot: {got}")
    print(f"missing: {missing}")


if __name__ == "__main__":
    main()
