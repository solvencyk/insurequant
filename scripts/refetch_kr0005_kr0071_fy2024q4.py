# -*- coding: utf-8 -*-
"""One-off refetch for inbox/downloader/20260821T1625Z.

The FY2024_Q4 raw files for 흥국화재 (KR0005) and 흥국생명 (KR0071) turned out
to be DART 사업보고서, not the K-ICS 정기경영공시 (0 hits on "경과조치", body is
plain prose, page footers say dart.fss.or.kr). This script re-fetches the real
정기경영공시 결산 PDFs from the industry-association portals:

  - KR0005 (손보, kpub.knia.or.kr 통합공시 결산 column, same route as
    scripts/backfill_nonlife_disclosure_kpub.py)
  - KR0071 (생보, pub.insure.or.kr mngtDis 결산(Q4) column, same route as
    scripts/backfill_life_disclosure_gaps.py)

Downloads go to a STAGING dir first. Nothing under data/disclosure/ is touched
until the staged file is verified (PDF magic + "경과조치" keyword hit count +
지급여력비율 세부 table presence). Only then is the old raw file archived to
data/_archive/<stamp>/... and the new one written to the canonical path.
"""
import io
import sys
import zipfile
from pathlib import Path

import fitz
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path("data/disclosure").resolve()
STAGE = Path("artifacts/disclosure_research/_tmp/refetch_20260821").resolve()
STAGE.mkdir(parents=True, exist_ok=True)
ARCHIVE_STAMP = "20260821T044328Z"
ARCHIVE_ROOT = Path(f"data/_archive/{ARCHIVE_STAMP}").resolve()

PERIOD = "FY2024_Q4"


def verify_pdf(b: bytes) -> tuple[bool, str]:
    if not b.startswith(b"%PDF"):
        return False, f"bad magic {b[:8].hex()}"
    if b"%%EOF" not in b[-16384:] and b"%%EOF" not in b:
        return False, "missing %%EOF"
    return True, f"ok {len(b)}B"


def verify_kics_content(pdf_path: Path) -> tuple[bool, str]:
    """Prove the file is the K-ICS 정기경영공시, not a lookalike doc."""
    doc = fitz.open(str(pdf_path))
    n = doc.page_count
    hit_pages_transition = []
    hit_pages_scr_table = []
    scr_markers = ("지급여력기준금액", "지급여력금액", "지급여력비율")
    for i in range(n):
        txt = doc[i].get_text()
        if "경과조치" in txt:
            hit_pages_transition.append(i + 1)
        if any(m in txt for m in scr_markers):
            hit_pages_scr_table.append(i + 1)
    doc.close()
    msg = (
        f"pages={n} | \"경과조치\" hit on {len(hit_pages_transition)}p "
        f"{hit_pages_transition[:15]} | 지급여력 marker hit on "
        f"{len(hit_pages_scr_table)}p {hit_pages_scr_table[:15]}"
    )
    ok = bool(hit_pages_transition) and bool(hit_pages_scr_table)
    return ok, msg


def _decode_zipname(raw: str) -> str:
    try:
        return raw.encode("cp437").decode("euc-kr")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return raw


def extract_disclosure_pdf(zip_bytes: bytes) -> tuple[bytes | None, str]:
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


def fetch_kr0005_kpub(ctx) -> tuple[bytes | None, str]:
    """흥국화재 결산 2024 from kpub.knia.or.kr."""
    page = ctx.new_page()
    PAGE_URL = "https://kpub.knia.or.kr/managementDisc/regularly/regularlyDisclosure.do"
    loaded = False
    for attempt in range(4):
        try:
            page.goto(PAGE_URL, wait_until="commit", timeout=45000)
            page.wait_for_selector('a[href*="file/download"]', timeout=30000)
            loaded = True
            break
        except Exception as e:
            print(f"  [KR0005] goto attempt {attempt+1} failed: {str(e)[:80]}")
            page.wait_for_timeout(2000)
    if not loaded:
        return None, "could not load kpub page"
    page.wait_for_timeout(1500)

    table = page.evaluate(r"""()=>{
        const tbls=document.querySelectorAll('table');
        let target=null;
        tbls.forEach(t=>{ if(t.querySelector('a[href*="file/download"]')) target=t; });
        if(!target) return null;
        const headCells=Array.from(target.querySelectorAll('thead th, thead td')).map(c=>c.innerText.trim());
        const rows=Array.from(target.querySelectorAll('tbody tr')).map(r=>{
            const name=(r.querySelector('th[scope=row], th, td')||{}).innerText?.trim();
            const dls=Array.from(r.querySelectorAll('a[href*="file/download"]')).map(a=>a.getAttribute('href'));
            return {name, dls};
        });
        return {headCells, rows};
    }""")
    if not table:
        return None, "download table not found"

    years_from_head = [int(h[:4]) for h in table["headCells"] if h[:4].isdigit()]
    col_years = years_from_head if len(years_from_head) >= 3 else [2025, 2024, 2023, 2022, 2021]
    print(f"  [KR0005] column years: {col_years}")

    href = None
    for row in table["rows"]:
        nm = (row["name"] or "").strip()
        if nm != "흥국화재":
            continue
        for i, h in enumerate(row["dls"]):
            if i < len(col_years) and col_years[i] == 2024:
                href = h
                break
    if not href:
        return None, "no 2024 link for 흥국화재 row"

    BASE = "https://kpub.knia.or.kr"
    url = href if href.startswith("http") else BASE + href
    resp = ctx.request.get(url, timeout=60000)
    if resp.status != 200:
        return None, f"http {resp.status}"
    raw = resp.body()
    if raw[:2] == b"PK":
        data, picked = extract_disclosure_pdf(raw)
        if data is None:
            return None, f"zip extract failed: {picked}"
        print(f"  [KR0005] picked from zip: {picked}")
        return data, "ok"
    return raw, "ok"


def fetch_kr0071_pub(ctx) -> tuple[bytes | None, str]:
    """흥국생명 결산(Q4) 2024 from pub.insure.or.kr."""
    page = ctx.new_page()
    page.goto(
        "https://pub.insure.or.kr/mngtDis/mngtDis/list.do?search_stdYear=2024",
        wait_until="networkidle", timeout=60000,
    )
    page.wait_for_timeout(1200)

    ridx = page.evaluate("""(cname)=>{
        const trs=document.querySelectorAll('#scroll_cont table tbody tr');
        for(let i=0;i<trs.length;i++){
            const t=trs[i].querySelector('td')?.innerText.trim();
            if(t===cname) return i+1;
        }
        return -1;
    }""", "흥국생명")
    if ridx < 0:
        return None, "row not found for 흥국생명"

    td = 5  # 결산 column
    xp = f'//*[@id="scroll_cont"]/table/tbody/tr[{ridx}]/td[{td}]/a'
    tmp = STAGE / "KR0071_raw_dl.pdf"
    try:
        with page.expect_download(timeout=60000) as dl:
            page.locator(f"xpath={xp}").click()
        dl.value.save_as(str(tmp))
    except Exception as e:
        return None, f"download failed: {e}"
    return tmp.read_bytes(), "ok"


def main() -> int:
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            accept_downloads=True, ignore_https_errors=True, locale="ko-KR",
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
        )

        print("== KR0005 흥국화재 (kpub.knia.or.kr) ==")
        data, why = fetch_kr0005_kpub(ctx)
        if data is None:
            print(f"  FAIL: {why}")
            results["KR0005"] = (False, why, None)
        else:
            ok, why2 = verify_pdf(data)
            if not ok:
                print(f"  FAIL verify: {why2}")
                results["KR0005"] = (False, why2, None)
            else:
                stage_path = STAGE / "KR0005_흥국화재.pdf"
                stage_path.write_bytes(data)
                print(f"  staged: {stage_path} ({why2})")
                results["KR0005"] = (True, why2, stage_path)

        print("\n== KR0071 흥국생명 (pub.insure.or.kr) ==")
        data, why = fetch_kr0071_pub(ctx)
        if data is None:
            print(f"  FAIL: {why}")
            results["KR0071"] = (False, why, None)
        else:
            ok, why2 = verify_pdf(data)
            if not ok:
                print(f"  FAIL verify: {why2}")
                results["KR0071"] = (False, why2, None)
            else:
                stage_path = STAGE / "KR0071_흥국생명보험.pdf"
                stage_path.write_bytes(data)
                print(f"  staged: {stage_path} ({why2})")
                results["KR0071"] = (True, why2, stage_path)

        ctx.close()
        browser.close()

    print("\n== CONTENT VERIFICATION (경과조치 + 지급여력 marker) ==")
    for kr, (ok, why, path) in results.items():
        if not ok:
            print(f"  {kr}: SKIP (fetch failed: {why})")
            continue
        kics_ok, msg = verify_kics_content(path)
        print(f"  {kr}: {'PASS' if kics_ok else 'FAIL'} — {msg}")
        results[kr] = (kics_ok, msg, path)

    print("\n== SUMMARY ==")
    for kr, (ok, why, path) in results.items():
        print(f"  {kr}: {'VERIFIED' if ok else 'NOT VERIFIED'} — {why}")

    return 0 if all(v[0] for v in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
