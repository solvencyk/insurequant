#!/usr/bin/env python3
"""Download FY2026.2Q 생명보험협회 일괄 경영공시 (bulk zip).

Clone of download_disclosure_2026q1_life.py with the quarter bumped to 2Q.

  URL: https://pub.insure.or.kr/mngtDis/mngtDis/list.do

Selector note (probed 2026-08-31, structure differs from the 1Q script's comment):
the list table's last row (tr[23]) is not a company row -- it is the 전체파일
bulk row, and each quarter's bulk zip hangs off an anchor whose onclick is
``fn_quarterfileDown('<q>')``. The quarter cells are created only once that
quarter is posted (on 2026-08-31 only ``('1')`` existed), so a fixed ``td[N]``
index would silently drift. Anchor on the onclick argument instead.

Output: data/disclosure/FY2026_Q2/life_bulk/<original_filename>.zip
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "disclosure" / "FY2026_Q2" / "life_bulk"
META_DIR = ROOT / "data" / "disclosure" / "_meta" / "FY2026_Q2"
OUT_DIR.mkdir(parents=True, exist_ok=True)
META_DIR.mkdir(parents=True, exist_ok=True)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

LIST_URL = "https://pub.insure.or.kr/mngtDis/mngtDis/list.do"

PERIODS = {
    "FY2026_Q2": {
        # 전체파일 row -> 2분기 bulk zip
        "selector": "#scroll_cont table a[onclick*=\"fn_quarterfileDown('2')\"]",
        "fallback_text": "2분기",
    },
}


def main() -> int:
    target = "FY2026_Q2"
    cfg = PERIODS[target]
    print(f"[life-bulk] period={target} url={LIST_URL}", flush=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent=UA, accept_downloads=True, ignore_https_errors=True)
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        page.goto(LIST_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        link = page.locator(cfg["selector"]).first
        if link.count() == 0:
            link = page.locator("#scroll_cont table a", has_text=cfg["fallback_text"]).first
        if link.count() == 0:
            print(
                f"  NOT_POSTED  2분기 bulk link absent on {LIST_URL} "
                "(전체파일 row has no 2분기 anchor yet)",
                flush=True,
            )
            manifest = {
                "_meta": {"period": target, "source": LIST_URL,
                          "stamp_utc": datetime.now(timezone.utc).isoformat()},
                "result": {"status": "not_posted"},
            }
            (META_DIR / "life_bulk_manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            browser.close()
            return 1

        try:
            with page.expect_download(timeout=180_000) as dl_info:
                link.click()
            dl = dl_info.value
            suggested = dl.suggested_filename or "life_bulk.zip"
            target_path = OUT_DIR / re.sub(r'[\\/:*?"<>|]+', "_", suggested)
            dl.save_as(str(target_path))
            size = target_path.stat().st_size
            head = target_path.read_bytes()[:4]
            sig = "ZIP" if head == b"PK\x03\x04" else "PDF" if head == b"%PDF" else head.hex()
            print(f"  OK -> {target_path.name} ({size:,} bytes, {sig})", flush=True)
            manifest = {
                "_meta": {
                    "period": target,
                    "source": LIST_URL,
                    "stamp_utc": datetime.now(timezone.utc).isoformat(),
                },
                "result": {
                    "status": "ok",
                    "suggested_filename": suggested,
                    "path": str(target_path.relative_to(ROOT)).replace("\\", "/"),
                    "src_url": dl.url or "",
                    "bytes": size,
                    "magic": sig,
                },
            }
        except Exception as exc:
            print(f"  FAIL {type(exc).__name__}: {exc}", flush=True)
            shot = META_DIR / "life_bulk_failure.png"
            try: page.screenshot(path=str(shot), full_page=True)
            except Exception: pass
            html = META_DIR / "life_bulk_failure.html"
            try: html.write_text(page.content(), encoding="utf-8")
            except Exception: pass
            manifest = {
                "_meta": {"period": target, "stamp_utc": datetime.now(timezone.utc).isoformat()},
                "result": {"status": "fail", "error": f"{type(exc).__name__}: {exc}"},
            }
            (META_DIR / "life_bulk_manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            browser.close()
            return 2
        browser.close()

    mp = META_DIR / "life_bulk_manifest.json"
    mp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[summary] wrote {mp}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
