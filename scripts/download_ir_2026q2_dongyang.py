#!/usr/bin/env python3
"""Download FY2026 H1 (상반기) IR materials for 동양생명 (KR0087).

동양생명 posted its H1 2026 earnings release ahead of the rest of the
industry (2026-07-27, vs. the usual mid-August cadence) — see
TODO_downloader.md 2026.2Q scouting note. Rest of the 13-source IR catalog
is not ready yet, so this is a single-source fetch rather than a full
download_ir_2026q2.py pass.

Output: data/ir/FY2026_Q2/raw/KR0087_동양생명/<filename>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "ir" / "FY2026_Q2" / "raw" / "KR0087_동양생명"

URL = "https://www.myangel.co.kr/Company/Ir/CoIrData"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

# Row is identified by its title + date text (robust to new rows being
# prepended above it, unlike a fixed nth-of-type index).
ROW_XPATH = (
    '//div[contains(@class,"board-item")]'
    '[.//*[contains(text(),"상반기실적발표자료")] and .//*[contains(text(),"2026.07.27")]]'
)


def _detect_ext(body: bytes, src: str) -> str:
    if body[:4] == b"%PDF":
        return "pdf"
    if body[:4] == b"PK\x03\x04":
        if b"xl/workbook.xml" in body[:8192]:
            return "xlsx"
        return "zip"
    path = urlparse(src).path.lower()
    for ext in ("pdf", "xlsx", "xls"):
        if path.endswith("." + ext):
            return ext
    return "bin"


def _fetch_one(page, row_xpath: str, button_class: str, label: str) -> tuple[bytes, str, str]:
    btn = page.locator(f"xpath={row_xpath}").locator(f"button.{button_class}").first
    with page.expect_download(timeout=25_000) as dl_info:
        btn.click()
    dl = dl_info.value
    path = dl.path()
    if not path or not Path(path).exists():
        raise RuntimeError(f"{label}: download path missing")
    return Path(path).read_bytes(), (dl.url or ""), (dl.suggested_filename or "")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    saved = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=UA, accept_downloads=True, ignore_https_errors=True)
        page = context.new_page()
        page.set_default_timeout(25_000)
        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        row_count = page.locator(f"xpath={ROW_XPATH}").count()
        if row_count == 0:
            print("FAIL: no board-item row matched FY2026 상반기 + 2026.07.27", flush=True)
            browser.close()
            return 2

        for cls, label in (("ico-pdf", "PDF"), ("ico-xls", "XLS")):
            try:
                body, src, suggested = _fetch_one(page, ROW_XPATH, cls, label)
                ext = _detect_ext(body, src)
                if suggested and len(suggested) <= 180:
                    fname = re.sub(r'[\\/:*?"<>|]+', "_", suggested)
                else:
                    fname = f"KR0087_동양생명_FY2026_Q2.{ext}"
                target = OUT_DIR / fname
                target.write_bytes(body)
                print(f"OK [{label}] -> {target.relative_to(ROOT)} ({len(body):,} bytes, src={src})", flush=True)
                saved.append(str(target))
            except Exception as exc:
                print(f"FAIL [{label}]: {type(exc).__name__}: {exc}", flush=True)

        browser.close()

    return 0 if saved else 2


if __name__ == "__main__":
    raise SystemExit(main())
