# -*- coding: utf-8 -*-
"""Backfill AIG손해보험 (KR0029) quarterly 정기경영공시 (Q1-Q3, FY2023-FY2025).

AIG publishes its 정기경영공시 on its own site:
  list page: https://m.aig.co.kr/wo/dpwom012.html?menuId=MS709  (12 pages, curPage=N)

Each disclosure entry on the list is a title anchor `goView(<pancId>)` immediately
followed by a "파일다운로드" anchor whose href is a DIRECT download:
  /downLoadFiles.do?fileId=<id>&fileSeq=1
So no detail-page navigation is needed — we read the download href straight off
the list, pairing it with the preceding title text.

AIG's publication cadence (confirmed from the list) for each fiscal year:
  - "<YYYY>년 1분기 경영공시"      -> FY<YYYY>_Q1   (true quarterly)
  - "<YYYY>년 상반기 경영공시"     -> FY<YYYY>_Q2   (반기/H1 — AIG has NO separate "2분기")
  - "<YYYY>년 3분기 경영공시"      -> FY<YYYY>_Q3   (true quarterly)
  - "<YYYY>년 결산 경영공시"       -> FY<YYYY>_Q4   (already collected)

So the 9 missing cells (FY2023/24/25 x Q1/Q2/Q3) are all available; Q2 is satisfied
by the 반기(상반기) disclosure (AIG's structural substitute for a Q2 filing).

Output: data/disclosure/FY{YYYY}_Q{N}/raw/KR0029_AIG손해보험.pdf
Failures: screenshot + HTML dump to artifacts/disclosure_research/_tmp/aig/
"""
from __future__ import annotations

import io
import json
import re
import sys
import zipfile
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
DISC = ROOT / "data" / "disclosure"
TMP = ROOT / "artifacts" / "disclosure_research" / "_tmp" / "aig"
TMP.mkdir(parents=True, exist_ok=True)

KR = "KR0029"
STEM = "KR0029_AIG손해보험"  # match existing naming exactly
BASE = "https://m.aig.co.kr"
LIST_URL = "https://m.aig.co.kr/wo/dpwom012.html?menuId=MS709"
N_PAGES = 12  # "전체 12페이지" as of 2026-06

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

# (year, quarter) -> regex matching the AIG list title for that cell.
# Q2 maps to 상반기(반기) — AIG's structural substitute for a 2분기 filing.
TARGETS = {
    (2023, 1): "1분기", (2023, 2): "상반기", (2023, 3): "3분기",
    (2024, 1): "1분기", (2024, 2): "상반기", (2024, 3): "3분기",
    (2025, 1): "1분기", (2025, 2): "상반기", (2025, 3): "3분기",
}


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
    """If the download is a ZIP, return the 경영공시 본문 PDF (drop 감사/재무제표/별첨)."""
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


def parse_entries(page):
    """Return list of {title, year, label, href} for one list page.

    Pairs each title anchor `goView(id)` with the next sibling 파일다운로드 anchor.
    """
    raw = page.evaluate(r"""()=>{
        const anchors = Array.from(document.querySelectorAll('a'));
        const items = [];
        for (let i = 0; i < anchors.length; i++) {
            const oc = anchors[i].getAttribute('onclick') || '';
            if (/goView\(\d+\)/.test(oc)) {
                const title = (anchors[i].innerText || '').trim();
                // find the next anchor whose href hits downLoadFiles.do
                let href = null;
                for (let j = i + 1; j < Math.min(i + 4, anchors.length); j++) {
                    const h = anchors[j].getAttribute('href') || '';
                    if (h.includes('downLoadFiles.do')) { href = h; break; }
                }
                items.push({title, href, panc: (oc.match(/goView\((\d+)\)/)||[])[1]});
            }
        }
        return items;
    }""")
    out = []
    for it in raw:
        title = it["title"]
        m = re.search(r"(\d{4})\s*년", title)
        year = int(m.group(1)) if m else None
        # period label keywords
        label = None
        if "1분기" in title:
            label = "1분기"
        elif "상반기" in title or "반기" in title:
            label = "상반기"
        elif "3분기" in title:
            label = "3분기"
        elif "결산" in title:
            label = "결산"
        out.append({"title": title, "year": year, "label": label,
                    "href": it["href"], "panc": it.get("panc")})
    return out


def main() -> int:
    import urllib3
    urllib3.disable_warnings()

    # year/label -> chosen entry. Skip supplement titles (감사보고서, 결산공고,
    # 외부검증보고서) — we want the plain "경영공시" body for each period.
    found: dict[tuple[int, str], dict] = {}
    all_titles: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent=UA, ignore_https_errors=True,
                                  locale="ko-KR", accept_downloads=True)
        page = ctx.new_page()
        page.set_default_timeout(30000)

        for pg in range(1, N_PAGES + 1):
            url = f"{LIST_URL}&curPage={pg}"
            try:
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_timeout(2000)
            except Exception as e:
                print(f"  page {pg} goto failed: {str(e)[:80]}")
                continue
            entries = parse_entries(page)
            for e in entries:
                all_titles.append(e["title"])
                y, lab = e["year"], e["label"]
                if y is None or lab is None or lab == "결산":
                    continue
                # exclude supplement variants that slipped into the label bucket
                t = e["title"]
                if any(s in t for s in ("감사보고서", "결산공고", "외부검증",
                                        "K-ICS", "공고")):
                    continue
                key = (y, lab)
                # keep the first (newest) plain 경영공시 match for that period
                if key not in found and e["href"]:
                    found[key] = e
            print(f"  page {pg}: {len(entries)} entries")

        # Download the 9 target cells
        results = []
        for (year, q), label in TARGETS.items():
            entry = found.get((year, label))
            period = f"FY{year}_Q{q}"
            cell = f"{period}"
            if not entry:
                results.append((cell, "missing", f"no list entry for {year} {label}"))
                print(f"  [{cell}] NO ENTRY ({year} {label})")
                continue
            href = entry["href"]
            dl_url = href if href.startswith("http") else urljoin(BASE, href)
            try:
                resp = ctx.request.get(dl_url, headers={"Referer": LIST_URL}, timeout=60000)
                if resp.status != 200:
                    results.append((cell, "blocked", f"http {resp.status}"))
                    print(f"  [{cell}] HTTP {resp.status}")
                    continue
                raw = resp.body()
            except Exception as e:
                results.append((cell, "blocked", f"dl err {str(e)[:60]}"))
                print(f"  [{cell}] download error {str(e)[:60]}")
                continue

            if raw[:2] == b"PK":
                data, picked = extract_disclosure_pdf(raw)
                if data is None:
                    results.append((cell, "blocked", f"zip: {picked}"))
                    print(f"  [{cell}] zip extract failed: {picked}")
                    continue
                print(f"    picked from zip: {picked}")
            else:
                data = raw

            ok, why = verify_pdf(data)
            if not ok:
                results.append((cell, "blocked", f"verify: {why}"))
                print(f"  [{cell}] verify failed: {why}")
                # dump the bad payload head for diagnosis
                (TMP / f"{cell}_badhead.bin").write_bytes(data[:2048])
                continue

            outdir = DISC / period / "raw"
            outdir.mkdir(parents=True, exist_ok=True)
            dest = outdir / f"{STEM}.pdf"
            dest.write_bytes(data)
            kb = len(data) // 1024
            results.append((cell, "collected", f"{kb} KB | {entry['title']}"))
            print(f"  [{cell}] -> {dest.name} ({kb} KB) [{entry['title']}]")

        ctx.close()
        browser.close()

    # Persist the period inventory the site exposes (cadence evidence)
    inventory = sorted({t for t in all_titles if re.search(r"\d{4}\s*년", t)})
    (TMP / "aig_period_inventory.json").write_text(
        json.dumps({"found_keys": [f"{y}/{l}" for (y, l) in sorted(found.keys())],
                    "all_titles": inventory},
                   ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n== SUMMARY ==")
    for cell, status, why in sorted(results):
        print(f"  {cell}: {status}  {why}")
    print(f"\n== AIG exposed periods ({len(inventory)}) ==")
    for t in inventory:
        print(f"  {t}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
