#!/usr/bin/env python3
"""Download FY2026.1Q 생명보험협회 일괄 경영공시 (bulk zip).

User-provided 2026-05-30:
  URL: https://pub.insure.or.kr/mngtDis/mngtDis/list.do
  XPath (2026.1Q row): //*[@id="scroll_cont"]/table/tbody/tr[23]/td[2]/a

The portal aggregates all life-insurer 정기경영공시 PDFs in one zip per quarter.
Output: data/disclosure/FY2026_Q1/life_bulk/<original_filename>.zip
"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "disclosure" / "FY2026_Q1" / "life_bulk"
META_DIR = ROOT / "data" / "disclosure" / "_meta" / "FY2026_Q1"
OUT_DIR.mkdir(parents=True, exist_ok=True)
META_DIR.mkdir(parents=True, exist_ok=True)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

# Per-quarter row index on the list table (tr[N]). 2026.1Q = tr[23] per user.
# As new quarters get added the older indices shift -- recompute by date column if needed.
PERIODS = {
    "FY2026_Q1": {
        "xpath": '//*[@id="scroll_cont"]/table/tbody/tr[23]/td[2]/a',
    },
}


def main() -> int:
    target = "FY2026_Q1"
    cfg = PERIODS[target]
    print(f"[life-bulk] period={target} url=https://pub.insure.or.kr/mngtDis/mngtDis/list.do", flush=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent=UA, accept_downloads=True, ignore_https_errors=True)
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        page.goto("https://pub.insure.or.kr/mngtDis/mngtDis/list.do", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        try:
            with page.expect_download(timeout=120_000) as dl_info:
                page.locator(f"xpath={cfg['xpath']}").first.click()
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
                    "source": "https://pub.insure.or.kr/mngtDis/mngtDis/list.do",
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
            browser.close()
            return 2
        browser.close()

    mp = META_DIR / "life_bulk_manifest.json"
    mp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[summary] wrote {mp}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
