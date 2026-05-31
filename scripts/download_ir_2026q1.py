#!/usr/bin/env python3
"""Download FY2026.1Q IR materials for 13 sources covering multiple K-ICS entities.

Reuses the per-insurer config pattern from download_disclosure_2026q1_nonlife.py.
Group sources (KB금융 / 신한금융 / 농협금융) cover multiple K-ICS entities; the
KR field below uses the parent insurer's code but the manifest records all
covered entities.

Output: data/ir/FY2026_Q1/<KR>_<name>/<filename>
Manifest: data/ir/FY2026_Q1/_manifest.json
"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

ROOT = Path(__file__).resolve().parents[1]
OUT_BASE = ROOT / "data" / "ir" / "FY2026_Q1"
OUT_BASE.mkdir(parents=True, exist_ok=True)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

# fmt: off
SOURCES = {
    "KR0001": {  # 메리츠금융그룹 factsheet (mobile site)
        "name": "메리츠화재해상보험", "group": "메리츠금융",
        "covers": ["KR0001"],
        "mode": "click_dl",
        "url": "https://m.meritzgroup.com/mo/ko/ir/ir1.do",
        "xpath": '//*[@id="firstInfo"]/ul/li[3]/a',
    },
    "KR0003": {  # 롯데손보
        "name": "롯데손해보험", "covers": ["KR0003"],
        "mode": "click_dl",
        "url": "https://www.lotteins.co.kr/web/C/D/H/cdh_ir_board04_list_6.jsp",
        "xpath": '//*[@id="tab-2"]/div/table/tbody/tr[1]/td[2]/a',
    },
    "KR0008": {  # 삼성화재 IR factsheet xlsx
        "name": "삼성화재해상보험", "covers": ["KR0008"],
        "mode": "click_dl",
        "url": "https://www.samsungfire.com/vh/page/VH.HPMK0201.do",
        "xpath": '//*[@id="baseMain"]/div[2]/section[1]/div[2]/ul/li[1]/div/div[2]/div/button[3]',
        "wait_ms": 3000,
    },
    "KR0009": {  # 현대해상 IR
        "name": "현대해상", "covers": ["KR0009"],
        "mode": "click_dl",
        "url": "https://www.hi.co.kr/serviceAction.do?view=bin/KC/IR/HHKCIR090M",
        "xpath": '//*[@id="rstbzList"]/div[1]/div[2]/div[2]/a[2]/span',
        "wait_ms": 3000,
    },
    "KR0010": {  # KB금융그룹 factbook (KB손보 + KB라이프 합산)
        "name": "KB금융그룹", "group": "KB금융지주",
        "covers": ["KR0010", "KR0099"],
        "mode": "direct_href",
        "url": "https://www.kbfg.com/kor/ir/report/factbook/list.jsp",
        "xpath": '//*[@id="list_form"]/div/div[1]/div[2]/ul[2]/li[1]/div[3]/div/a[2]',
    },
    "KR0011_factsheet": {  # DB손보 factsheet (xlsx)
        "name": "DB손해보험_factsheet", "covers": ["KR0011", "KR0082"],
        "mode": "direct_href",
        "url": "https://www.idbins.com/pc/bizxpress/cmy/inv/ir/FWCOMV1705_260514(1).shtm?tp=T&tx=&ct=2",
        "xpath": '//*[@id="content"]/div/div/div[1]/div[2]/dl/dd/ul/li[1]/a',
    },
    "KR0051": {  # 신한금융그룹 factbook (신한EZ + 신한라이프 합산)
        "name": "신한금융그룹", "group": "신한금융지주",
        "covers": ["KR0051", "KR0094"],
        "mode": "direct_href",
        "url": "https://shinhangroup.com/kr/ir/finance/factBook",
        "xpath": '//*[@id="listBody"]/li[1]/div[3]/div/span/a',
        "wait_ms": 3000,
    },
    "KR1000": {  # 코리안리 (2-step with known detail URL)
        "name": "코리안리재보험", "covers": ["KR1000"],
        "mode": "two_step_direct_url",
        "url1": "https://koreanre.co.kr/sub.asp?maincode=503&sub_sequence=551&sub_sub_sequence=552&exec=list&strBoardID=kui_552",
        "url2": "https://koreanre.co.kr/sub.asp?maincode=503&sub_sequence=551&sub_sub_sequence=552&mskin=&exec=view&strBoardID=kui_552&intPage=1&intCategory=0&strSearchCategory=|s_name|s_subject|&strSearchWord=&intSeq=1539",
        "xpath": '//*[@id="pageCont"]/div/table/tbody/tr/td/div[3]/table/tbody/tr[2]/td[2]/table/tbody/tr/td/a',
        "step2_mode": "direct_href",
    },
    "KR0032": {  # 농협금융지주 (NH농협손보 + 농협생명 합산)
        "name": "농협금융지주", "group": "농협금융지주",
        "covers": ["KR0032", "KR0104"],
        "mode": "click_dl",
        "url": "https://nhfngroup.com/user/indexSub.do?codyMenuSeq=1219941109&siteId=nhfngroup",
        "xpath": '//*[@id="siteFunction_menu_3_11_5_1713486737124102"]/div/div[1]/ul/li/a[2]/span',
    },
    "KR0068": {  # 한화생명
        "name": "한화생명", "covers": ["KR0068"],
        "mode": "click_dl",
        "url": "https://company.hanwhalife.com/ko/investment/investor/earnings-release",
        "xpath": '//*[@id="company-contents"]/div/div[2]/div[2]/div[2]/ul/li[2]/ul/li[2]/button[2]/span',
        "wait_ms": 3000,
    },
    "KR0069": {  # 삼성생명
        "name": "삼성생명", "covers": ["KR0069"],
        "mode": "click_dl",
        "url": "https://www.samsunglife.com/individual/display/invest/PDK-IRIVI015220M",
        "xpath": '//*[@id="samsungLifeWideMain"]/section/div[2]/div[2]/div/table/tbody/tr[1]/td[4]/button',
        "wait_ms": 3000,
    },
    "KR0079": {  # 미래에셋생명 — <a onclick="fileDownload('2026 Q1 FactSheet_Kr.xlsx', ...)">
        "name": "미래에셋생명", "covers": ["KR0079"],
        "mode": "click_dl",
        "url": "https://life.miraeasset.com/micro/company/PC-HO-060401-000000.do",
        "xpath": '//*[@id="mainCont"]/div[3]/div/ul[3]/li/a',
    },
    "KR0087": {  # 동양생명
        "name": "동양생명", "covers": ["KR0087"],
        "mode": "click_dl",
        "url": "https://www.myangel.co.kr/Company/Ir/CoIrData",
        "xpath": '//*[@id="mainContent"]/div[2]/div/div/div[2]/div[1]/div/button[2]',
        "wait_ms": 3000,
    },
}
# fmt: on


def _xpath(loc):
    return f"xpath={loc}"


def _detect_ext(body: bytes, src: str) -> str:
    """Pick file extension from magic bytes (more reliable than URL)."""
    if body[:4] == b"%PDF": return "pdf"
    if body[:4] == b"PK\x03\x04":
        # could be xlsx/zip/pptx — peek for xlsx/zip
        if b"xl/workbook.xml" in body[:8192]: return "xlsx"
        if b"ppt/presentation.xml" in body[:8192]: return "pptx"
        return "zip"
    if body[:4] == b"\xd0\xcf\x11\xe0":
        # OLE compound: hwp/xls/doc/ppt — IR context defaults to xls
        head = body[:4096]
        if b"HWP Document" in head or b"\\fHwp" in head: return "hwp"
        if b"PowerPoint" in head: return "ppt"
        if b"WordDocument" in head: return "doc"
        return "xls"
    # fallback to URL extension
    path = urlparse(src).path.lower()
    for ext in ("pdf", "xlsx", "xls", "hwp", "hwpx", "zip", "pptx"):
        if path.endswith("." + ext):
            return ext
    return "bin"


def _resolve_href(page, xpath: str, referer: str) -> tuple[bytes, str]:
    el = page.locator(_xpath(xpath)).first
    href = el.get_attribute("href") or ""
    onclick = el.get_attribute("onclick") or ""
    if not href:
        a = page.locator(_xpath(xpath + "/ancestor::a[1]")).first
        href = a.get_attribute("href") or ""
    if not href or href.startswith("javascript:") or href == "#":
        raise RuntimeError(f"no resolvable href on xpath={xpath} (onclick={onclick!r})")
    abs_url = urljoin(page.url, href)
    resp = page.request.get(abs_url, headers={"Referer": referer})
    if not resp.ok:
        raise RuntimeError(f"GET {abs_url} -> {resp.status}")
    return resp.body(), abs_url


def _extract_onclick_url(page, xpath: str, regex: str = r"['\"](/[^'\"]+\.(?:pdf|xlsx?|hwp|hwpx|zip|pptx?))['\"]") -> tuple[bytes, str]:
    """Extract file path from onclick attribute and fetch via page.request.

    For sites where the trigger element has onclick="doBizFileDownload('/data/...xlsx')"
    but `expect_download` doesn't fire (e.g. element inside hidden tab).
    """
    el = page.locator(_xpath(xpath)).first
    onclick = el.get_attribute("onclick") or ""
    m = re.search(regex, onclick)
    if not m:
        raise RuntimeError(f"no file path in onclick={onclick!r}")
    path = m.group(1)
    abs_url = urljoin(page.url, path)
    resp = page.request.get(abs_url, headers={"Referer": page.url})
    if not resp.ok:
        raise RuntimeError(f"GET {abs_url} -> {resp.status}")
    return resp.body(), abs_url


def _click_with_download(page, xpath: str) -> tuple[bytes, str, str]:
    """Returns (body, src_url, suggested_filename)."""
    with page.expect_download(timeout=25_000) as dl_info:
        page.locator(_xpath(xpath)).first.click()
    dl = dl_info.value
    path = dl.path()
    if not path or not Path(path).exists():
        raise RuntimeError(f"download path missing for {xpath}")
    return Path(path).read_bytes(), (dl.url or ""), (dl.suggested_filename or "")


def _save(out_dir: Path, fname_stem: str, body: bytes, ext: str, suggested: str = "") -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    # prefer suggested filename when provided, else stem.ext
    if suggested and len(suggested) <= 180:
        safe = re.sub(r'[\\/:*?"<>|]+', "_", suggested)
        target = out_dir / safe
    else:
        target = out_dir / f"{fname_stem}.{ext}"
    target.write_bytes(body)
    return target


def _run_one(p, key: str, cfg: dict) -> dict:
    name = cfg["name"]
    mode = cfg["mode"]
    started = time.time()
    print(f"[{key}] {name} mode={mode}", flush=True)
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(user_agent=UA, accept_downloads=True, ignore_https_errors=True)
    page = context.new_page()
    page.set_default_timeout(25_000)
    result = {"key": key, "name": name, "mode": mode, "covers": cfg.get("covers"), "started_at": started}
    try:
        wait_ms = cfg.get("wait_ms", 1500)
        wait_sel = cfg.get("wait_selector")
        wait_idle = cfg.get("wait_networkidle", False)

        def _common_wait():
            if wait_idle:
                try: page.wait_for_load_state("networkidle", timeout=15_000)
                except Exception: pass
            if wait_sel:
                try: page.wait_for_selector(wait_sel, timeout=15_000)
                except Exception: pass
            page.wait_for_timeout(wait_ms)

        suggested = ""
        if mode == "direct_href":
            page.goto(cfg["url"], wait_until="domcontentloaded")
            _common_wait()
            body, src = _resolve_href(page, cfg["xpath"], cfg["url"])
        elif mode == "onclick_url":
            page.goto(cfg["url"], wait_until="domcontentloaded")
            _common_wait()
            body, src = _extract_onclick_url(page, cfg["xpath"])
        elif mode == "click_dl":
            page.goto(cfg["url"], wait_until="domcontentloaded")
            _common_wait()
            body, src, suggested = _click_with_download(page, cfg["xpath"])
        elif mode == "two_step_direct_url":
            page.goto(cfg["url1"], wait_until="domcontentloaded")
            page.wait_for_timeout(800)
            page.goto(cfg["url2"], wait_until="domcontentloaded")
            _common_wait()
            sm = cfg.get("step2_mode", "direct_href")
            if sm == "direct_href":
                body, src = _resolve_href(page, cfg["xpath"], cfg["url2"])
            else:
                body, src, suggested = _click_with_download(page, cfg["xpath"])
        else:
            raise RuntimeError(f"unknown mode {mode!r}")

        ext = _detect_ext(body, src)
        out_dir = OUT_BASE / f"{key}_{name}"
        saved = _save(out_dir, f"{key}_{name}", body, ext, suggested)
        result["status"] = "ok"
        result["path"] = str(saved.relative_to(ROOT)).replace("\\", "/")
        result["src_url"] = src
        result["bytes"] = len(body)
        result["ext"] = ext
        result["suggested_filename"] = suggested
        print(f"  OK -> {saved.name} ({len(body):,} bytes, .{ext})", flush=True)
    except Exception as exc:
        result["status"] = "fail"
        result["error"] = f"{type(exc).__name__}: {exc}"
        try:
            shot = OUT_BASE / f"_failures/{key}_failure.png"
            shot.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(shot), full_page=True)
            result["screenshot"] = str(shot.relative_to(ROOT)).replace("\\", "/")
        except Exception: pass
        try:
            html = OUT_BASE / f"_failures/{key}_failure.html"
            html.write_text(page.content(), encoding="utf-8")
            result["html_dump"] = str(html.relative_to(ROOT)).replace("\\", "/")
        except Exception: pass
        print(f"  FAIL {result['error']}", flush=True)
    finally:
        result["elapsed_s"] = round(time.time() - started, 2)
        browser.close()
    return result


def main() -> int:
    only = set(sys.argv[1:]) if len(sys.argv) > 1 else None
    targets = {k: v for k, v in SOURCES.items() if not only or k in only}
    import urllib3; urllib3.disable_warnings()

    results = []
    with sync_playwright() as p:
        for k, cfg in targets.items():
            results.append(_run_one(p, k, cfg))

    manifest = {
        "_meta": {
            "period": "FY2026_Q1",
            "stamp_utc": datetime.now(timezone.utc).isoformat(),
            "source_count": len(results),
            "ok_count": sum(1 for r in results if r["status"] == "ok"),
            "fail_count": sum(1 for r in results if r["status"] == "fail"),
        },
        "results": results,
    }
    manifest_path = OUT_BASE / "_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[summary] ok={manifest['_meta']['ok_count']}/{len(results)} -> {manifest_path}")
    return 0 if manifest["_meta"]["fail_count"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
