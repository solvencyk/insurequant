#!/usr/bin/env python3
"""Download FY2026.2Q 경영공시 PDFs from individual 생명보험사 sites.

The standard 생보 path is the 생명보험협회 일괄 zip (download_disclosure_2026q2_life.py),
but that portal had not posted 2분기 as of 2026-08-31 while three insurers had already
put the file on their own site. This grabs those, so the round is not blocked on the
portal. Targets come from the discovery census
(`data/disclosure/_meta/FY2026_Q2/life_own_site_census.json`, verdict == posted).

Each site needs its own click path -- they are unrelated stacks:
  KR0074 라이나      Nuxt SPA, row 'FY2026 2Q 경영공시' + 'PDF 다운로드' control
  KR0075 BNP카디프   attachment anchor, text carries the .pdf filename
  KR0095 메트라이프   fnc_file('<id>', '<filename>', '<vo>') onclick

Output: data/disclosure/FY2026_Q2/raw/<KR>_<회사명>.pdf  (+ _meta manifest)
Run `scripts/_probes/verify_q2_disclosure_content.py` afterwards -- a differing hash is
NOT evidence of collection (re-rendered 1Q / 2025 결산 / DART 사업보고서 all differed before).
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "disclosure" / "FY2026_Q2" / "raw"
META_DIR = ROOT / "data" / "disclosure" / "_meta" / "FY2026_Q2"
CENSUS = META_DIR / "life_own_site_census.json"
OUT_DIR.mkdir(parents=True, exist_ok=True)
META_DIR.mkdir(parents=True, exist_ok=True)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")

# One XPath per company -- these are three unrelated stacks and a generic selector
# silently picks the wrong quarter. Probed against the live DOM 2026-08-31:
#   라이나  the control is a <button>PDF 다운로드</button>, one per row, so it has to be
#           anchored on the row title that precedes it (an //a search finds nothing).
#   BNP     the row title IS the anchor (<a class="filedown">FY2026 Q2 정기 경영공시</a>).
#   메트라이프 the anchor text carries the .pdf filename.
TARGETS = {
    "KR0074": {
        "name": "라이나생명보험",
        "url": "https://www.lina.co.kr/disclosure/management-public-announcement/regular-announcement",
        "xpath": ("//*[contains(normalize-space(.), 'FY2026 2Q 경영공시')]"
                  "/following::button[contains(., 'PDF 다운로드')][1]"),
    },
    "KR0075": {
        "name": "비엔피파리바카디프생명보험",
        "url": "https://www.cardif.co.kr/disclosure/papam001.do",
        "xpath": "//a[contains(@class,'filedown')][contains(., 'FY2026 Q2 정기 경영공시')]",
    },
    "KR0095": {
        "name": "메트라이프생명보험",
        "url": "https://brand.metlife.co.kr/pn/fxtrmMnnt/retrieveFxtrmMnntMain.do",
        "xpath": "//a[contains(., '2026년 2분기') and contains(., '.pdf')]",
    },
    "KR0076": {
        # 구 DGB생명. Grid layout: 연도(row) x 분기(column) table whose cells all read
        # '공시자료' with no row label, so neither the link text nor a row index can pick
        # the quarter. The href carries the filename, which does.
        "name": "아이엠라이프생명보험",
        "url": "https://www.imlifeins.co.kr/BA/BA_F010.do",
        "xpath": "//a[contains(@href, '2026년 2분기 경영공시자료')]",
    },
    "KR0079": {
        # 정기공시 = PC-HO-082000-000000.do. The neighbouring PC-HO-081900-000000.do is the
        # 공시정보관리규정 policy text with no listing -- an easy wrong-page mistake.
        # The row label reads 'FY 2026년 2/4 분기' and the anchor's own href carries the
        # target filename, so anchor on the href rather than the row position.
        "name": "미래에셋생명",
        "url": "https://life.miraeasset.com/micro/disclosure/management/PC-HO-082000-000000.do",
        "xpath": "//a[contains(@href, '2026년 2분기 경영공시')]",
    },
}


def posted_from_census() -> set[str]:
    if not CENSUS.exists():
        return set()
    d = json.loads(CENSUS.read_text(encoding="utf-8"))
    res = d.get("results", d if isinstance(d, list) else [])
    return {r.get("kr") for r in res if r.get("verdict") == "posted"}


def grab(page, cfg) -> tuple[str, bytes] | None:
    """Click the Q2 control and return (suggested_name, bytes)."""
    loc = page.locator(f"xpath={cfg['xpath']}")
    if loc.count() == 0:
        return None
    with page.expect_download(timeout=120_000) as dl:
        loc.first.click()
    d = dl.value
    tmp = OUT_DIR / f"_tmp_{d.suggested_filename or 'file.pdf'}"
    d.save_as(str(tmp))
    data = tmp.read_bytes()
    tmp.unlink(missing_ok=True)
    return (d.suggested_filename or "file.pdf", data)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", nargs="*", help="restrict to these KR codes")
    args = ap.parse_args()

    posted = posted_from_census()
    todo = [k for k in TARGETS if (not args.only or k in args.only)]
    if posted:
        skipped = [k for k in todo if k not in posted]
        for k in skipped:
            print(f"  SKIP {k} — census 가 posted 로 보지 않음(수집 대상 아님)", flush=True)
        todo = [k for k in todo if k in posted]

    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent=UA, accept_downloads=True,
                                  ignore_https_errors=True)
        for kr in todo:
            cfg = TARGETS[kr]
            page = ctx.new_page()
            page.set_default_timeout(45_000)
            try:
                page.goto(cfg["url"], wait_until="domcontentloaded")
                page.wait_for_timeout(4000)
                got = grab(page, cfg)
                if not got:
                    print(f"  FAIL {kr} {cfg['name']}: 클릭 경로를 못 찾음", flush=True)
                    results[kr] = {"status": "fail", "error": "no_download_control"}
                    page.close()
                    continue
                suggested, data = got
                head = data[:4]
                sig = "PDF" if head == b"%PDF" else "ZIP" if head == b"PK\x03\x04" else head.hex()
                if sig != "PDF":
                    print(f"  FAIL {kr}: PDF 가 아님 ({sig})", flush=True)
                    results[kr] = {"status": "fail", "error": f"not_pdf:{sig}"}
                    page.close()
                    continue
                target = OUT_DIR / f"{kr}_{cfg['name']}.pdf"
                target.write_bytes(data)
                print(f"  OK {kr} {cfg['name']} -> {target.name} "
                      f"({len(data):,} bytes) [{suggested}]", flush=True)
                results[kr] = {"status": "ok", "path": str(target.relative_to(ROOT)).replace("\\", "/"),
                               "bytes": len(data), "suggested_filename": suggested}
            except Exception as exc:  # noqa: BLE001
                print(f"  FAIL {kr}: {type(exc).__name__}: {exc}", flush=True)
                results[kr] = {"status": "fail", "error": f"{type(exc).__name__}: {exc}"[:200]}
            finally:
                page.close()
        browser.close()

    mp = META_DIR / "life_own_site_download_manifest.json"
    mp.write_text(json.dumps(
        {"_meta": {"period": "FY2026_Q2", "source": "individual 생보 sites",
                   "stamp_utc": datetime.now(timezone.utc).isoformat()},
         "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for v in results.values() if v.get("status") == "ok")
    print(f"[summary] ok={ok}/{len(results)} -> {mp}")
    return 0 if ok == len(results) and results else 1


if __name__ == "__main__":
    raise SystemExit(main())
