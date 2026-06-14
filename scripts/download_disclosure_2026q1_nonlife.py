#!/usr/bin/env python3
"""Download FY2026.1Q 정기경영공시 PDFs for 16 non-life insurers.

User-provided URLs + XPaths (2026-05-30). Per-insurer config drives one of
four download patterns:

  direct_href : XPath resolves to an <a> (or <a><img>) — read href, GET pdf.
  click_dl    : XPath resolves to a button/span/div that triggers a JS
                download — Playwright click + capture the download event.
  two_step    : Navigate URL1, click XPath1 to reach detail page, then
                resolve XPath2 (which is either direct_href or click_dl).

Output: data/disclosure/FY2026_Q1/pdf/KR####_<name>.pdf
Manifest: data/disclosure/_meta/FY2026_Q1/manifest.json
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "disclosure" / "FY2026_Q1" / "pdf"
META_DIR = ROOT / "data" / "disclosure" / "_meta" / "FY2026_Q1"
OUT_DIR.mkdir(parents=True, exist_ok=True)
META_DIR.mkdir(parents=True, exist_ok=True)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

# fmt: off
INSURERS = {
    "KR0001": {  # 메리츠화재 — AngularJS, wait for ng-scope render
        "name": "메리츠화재해상보험", "mode": "click_dl",
        "url": "https://www.meritzfire.com/disclosure/managerial-announcement/periodic.do#!/",
        "xpath": '(//a[contains(@class,"btn_file") and contains(@class,"i_pdf") and @download])[1]',
        "wait_selector": 'a.btn_file.i_pdf',
        "wait_ms": 5000,
    },
    "KR0002": {  # 한화손보 — direct PDF href in HTML
        "name": "한화손해보험", "mode": "direct_href",
        "url": "https://www.hwgeneralins.com/notice/ir/biz01.do",
        "xpath": '//a[contains(@title, "fy2026 1/4분기") or contains(@href, "FY2026-1_4.pdf")]',
    },
    "KR0003": {  # 롯데손보 — 2-step: click 2026.1Q row → detail page → 1Q.zip JS dl
        "name": "롯데손해보험", "mode": "two_step",
        "url": "https://www.lotteins.co.kr/web/C/D/H/cdh_ir_board03_list.jsp",
        "step1_xpath": '//a[@title="2026년 1분기 경영공시"]',
        "step2_xpath": '//a[contains(@href, "downLoadFile")]',
        "step2_mode": "click_dl",
    },
    "KR0004_MG": {  # 예별손해보험 (구 MG손해보험) — 사명 yebyeol.co.kr 확인
        "name": "예별손해보험", "mode": "click_dl",
        "url": "https://yebyeol.co.kr/PB021010DM.scp?menuId=MN0802001",
        "xpath": '//*[@id="quarter1_2026"]',
    },
    "KR0005": {  # 흥국화재
        "name": "흥국화재", "mode": "click_dl",
        "url": "https://www.heungkukfire.co.kr/FRW/announce/manageRegular.do",
        "xpath": '//*[@id="tab01_01"]/dt/button/span',
    },
    "KR0008": {  # 삼성화재
        "name": "삼성화재해상보험", "mode": "click_dl",
        "url": "https://www.samsungfire.com/v2/html/publication/02/J_020_010_001.html",
        "xpath": '//*[@id="baseMain"]/div[2]/section[2]/div/div/table/tbody/tr[1]/td[1]/div/div/button',
    },
    "KR0009": {  # 현대해상 — JS goMenu('100911') → 2026.1Q → li[3]=경영공시 최종 (li[1,2]=재무제표, skip)
        "name": "현대해상", "mode": "two_step",
        "url": "https://www.hi.co.kr/serviceAction.do",
        "js_eval_first": 'goMenu("100911")',
        "step1_xpath": '//a[contains(text(), "2026년 1분기 경영공시")]',
        "step2_xpath": '//*[@id="fileList"]/li[3]/a',
        "step2_mode": "click_dl",
    },
    "KR0010": {  # KB손보
        "name": "KB손해보험", "mode": "direct_href",
        "url": "https://www.kbinsure.co.kr/CG801010001.ec",
        "xpath": '//*[@id="contents"]/div[3]/table/tbody/tr[3]/td[3]/a',
    },
    "KR0011": {  # DB손보 (2-step, second URL known)
        "name": "DB손해보험", "mode": "two_step_direct_url",
        "url1": "https://www.idbins.com/pc/bizxpress/contentTemplet/pb/mp/rg/list.jsp",
        "url2": "https://www.idbins.com/pc/bizxpress/contentTemplet/pb/mp/rg/view.jsp?i=4c3187cc8627450a93bc&tp=T&tx=&ct=1",
        "xpath": '//*[@id="content"]/div[2]/div/div/div[1]/div[2]/dl/dd/ul/li[1]/a',
        "step2_mode": "direct_href",
    },
    "KR0029": {  # AIG (2-step, second URL known)
        "name": "AIG손해보험", "mode": "two_step_direct_url",
        "url1": "https://m.aig.co.kr/wo/dpwom012.html?menuId=MS709",
        "url2": "https://m.aig.co.kr/wo/dpwom021.html?menuId=MS709&pancId=15467&searchWord=&curPage=1",
        "xpath": '//*[@id="aigContent"]/div[1]/div[1]/span/a/em',
        "step2_mode": "click_dl",
    },
    "KR0032": {  # NH농협 — onclick="fnFileDownload(...)"
        "name": "NH농협손해보험", "mode": "click_dl",
        "url": "https://www.nhfire.co.kr/announce/managementAnnounce/retrievePeriodicManagementAnnounce.nhfire",
        "xpath": '//a[@title="2026년 1/4분기 PDF다운로드"]',
    },
    "KR0049": {  # 악사
        "name": "악사손해보험", "mode": "direct_href",
        "url": "https://www.axa.co.kr/cms/AsianPlatformInternet/html/axacms/common/intro/disclosure/regular/index.html",
        "xpath": '//*[@id="content"]/div[2]/div[2]/div[1]/table/tbody/tr[1]/td[2]/a',
    },
    "KR0050": {  # 하나손보
        "name": "하나손해보험", "mode": "direct_href",
        "url": "https://m.hanainsure.co.kr/w/disclosure/manage/regularMngDisclosure",
        "xpath": '//*[@id="targetRegularList"]/tr[1]/td[1]/a[1]',
    },
    "KR0051": {  # 신한EZ
        "name": "신한이지손해보험", "mode": "click_dl",
        "url": "https://www.shinhanez.co.kr/static/pub/PUB10000T01.html",
        "xpath": '//*[@id="tabFPanel1"]/div/div/div[1]/ul[2]/li[1]/div[3]',
    },
    "KR0150": {  # 서울보증 — SPA, requires networkidle wait
        "name": "서울보증보험", "mode": "click_dl",
        "url": "https://www.sgic.co.kr/biz/ccg/index.html?p=CCGIRI010101F01",
        "xpath": '//*[@id="test1"]',
        "wait_networkidle": True,
        "wait_ms": 5000,
    },
    "KR1000": {  # 코리안리
        "name": "코리안리재보험", "mode": "direct_href",
        "url": "https://www.koreanre.co.kr/ir/ir_03_1.asp",
        "xpath": '//*[@id="pageCont"]/div/div[3]/table/tbody/tr[2]/td[2]/a',
    },
    "KR1098": {  # 카카오페이
        "name": "카카오페이손해보험", "mode": "direct_href",
        "url": "https://kakaopayinscorp.co.kr/disclosure/management",
        "xpath": '//*[@id="mainContent"]/div/div/div[2]/div[2]/table/tbody/tr[1]/td[3]/div/a',
    },
}
# fmt: on


def _xpath(loc):
    """Playwright xpath= prefix helper."""
    return f"xpath={loc}"


def _save(kr: str, name: str, content: bytes, ext: str = "pdf") -> Path:
    safe_name = name.replace("/", "_")
    target = OUT_DIR / f"{kr}_{safe_name}.{ext}"
    target.write_bytes(content)
    return target


def _http_get_pdf(url: str, referer: str) -> bytes:
    headers = {
        "User-Agent": UA,
        "Referer": referer,
        "Accept": "application/pdf,*/*",
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    }
    r = requests.get(url, headers=headers, timeout=60, verify=False, allow_redirects=True)
    r.raise_for_status()
    return r.content


def _resolve_href(page, xpath: str, referer: str) -> tuple[bytes, str]:
    """Find <a> at xpath, get href, fetch PDF via requests using page cookies."""
    el = page.locator(_xpath(xpath)).first
    href = el.get_attribute("href") or ""
    onclick = el.get_attribute("onclick") or ""
    if not href and not onclick:
        # try ancestor <a>
        a = page.locator(_xpath(xpath + "/ancestor::a[1]")).first
        href = a.get_attribute("href") or ""
    if not href:
        raise RuntimeError(f"no href on xpath={xpath} (onclick={onclick!r})")
    abs_url = urljoin(page.url, href)
    # Use Playwright's request context so cookies follow.
    resp = page.request.get(abs_url, headers={"Referer": referer})
    if not resp.ok:
        raise RuntimeError(f"GET {abs_url} -> {resp.status}")
    body = resp.body()
    return body, abs_url


def _click_with_download(page, xpath: str) -> tuple[bytes, str]:
    """Click element at xpath, expect a download event."""
    with page.expect_download(timeout=20_000) as dl_info:
        page.locator(_xpath(xpath)).first.click()
    dl = dl_info.value
    path = dl.path()
    if not path or not Path(path).exists():
        raise RuntimeError(f"download path missing for {xpath}")
    return Path(path).read_bytes(), dl.url or ""


def _try_xpaths(page, xpaths: list[str]) -> str | None:
    for x in xpaths:
        try:
            if page.locator(_xpath(x)).first.is_visible(timeout=2000):
                return x
        except Exception:
            continue
    return None


def _run_one(p, kr: str, cfg: dict) -> dict:
    name = cfg["name"]
    mode = cfg["mode"]
    started = time.time()
    print(f"[{kr}] {name} mode={mode}", flush=True)
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(user_agent=UA, accept_downloads=True, ignore_https_errors=True)
    page = context.new_page()
    page.set_default_timeout(20_000)
    result = {"kr": kr, "name": name, "mode": mode, "started_at": started}
    try:
        wait_ms = cfg.get("wait_ms", 1500)
        wait_sel = cfg.get("wait_selector")
        wait_idle = cfg.get("wait_networkidle", False)

        def _common_wait():
            if wait_idle:
                try:
                    page.wait_for_load_state("networkidle", timeout=15_000)
                except Exception:
                    pass
            if wait_sel:
                try:
                    page.wait_for_selector(wait_sel, timeout=15_000)
                except Exception:
                    pass
            page.wait_for_timeout(wait_ms)

        if mode == "direct_href":
            page.goto(cfg["url"], wait_until="domcontentloaded")
            _common_wait()
            body, src = _resolve_href(page, cfg["xpath"], cfg["url"])
        elif mode == "click_dl":
            page.goto(cfg["url"], wait_until="domcontentloaded")
            _common_wait()
            xpaths = [cfg["xpath"]] + (cfg.get("fallback_xpaths") or [])
            picked = _try_xpaths(page, xpaths)
            if not picked:
                raise RuntimeError(f"no visible element found among {xpaths}")
            body, src = _click_with_download(page, picked)
        elif mode == "two_step":
            page.goto(cfg["url"], wait_until="domcontentloaded")
            _common_wait()
            # Optional JS evaluation to navigate within SPA before clicking step1
            if cfg.get("js_eval_first"):
                try:
                    page.evaluate(cfg["js_eval_first"])
                    page.wait_for_timeout(2500)
                except Exception as e:
                    print(f'  WARN js_eval_first failed: {e}', flush=True)
            # click step1 — may navigate, submit form, or rerender in-page
            try:
                with page.expect_navigation(wait_until="domcontentloaded", timeout=8_000):
                    page.locator(_xpath(cfg["step1_xpath"])).first.click()
            except PWTimeout:
                # JS may rerender without nav event — already clicked, fall through
                pass
            page.wait_for_timeout(2500)
            sm = cfg.get("step2_mode", "direct_href")
            if sm == "direct_href":
                body, src = _resolve_href(page, cfg["step2_xpath"], cfg["url"])
            else:
                body, src = _click_with_download(page, cfg["step2_xpath"])
        elif mode == "two_step_direct_url":
            page.goto(cfg["url1"], wait_until="domcontentloaded")
            page.wait_for_timeout(800)
            page.goto(cfg["url2"], wait_until="domcontentloaded")
            page.wait_for_timeout(1500)
            sm = cfg.get("step2_mode", "direct_href")
            if sm == "direct_href":
                body, src = _resolve_href(page, cfg["xpath"], cfg["url2"])
            else:
                body, src = _click_with_download(page, cfg["xpath"])
        else:
            raise RuntimeError(f"unknown mode {mode!r}")
        # Verify PDF signature
        if not body[:4] in (b"%PDF",):
            # may be wrapped or HTML; flag but still save
            head = body[:64]
            result["pdf_signature"] = False
            print(f"  WARN: not a PDF magic ({head!r})", flush=True)
        else:
            result["pdf_signature"] = True
        # Determine extension from src URL + magic bytes (URL often hidden by JS)
        ext = "pdf"
        path = urlparse(src).path.lower()
        if path.endswith(".hwp"): ext = "hwp"
        elif path.endswith(".hwpx"): ext = "hwpx"
        elif path.endswith(".zip"): ext = "zip"
        # Magic-byte override (more reliable than URL)
        if body[:4] == b"%PDF": ext = "pdf"
        elif body[:4] == b"PK\x03\x04": ext = "zip"  # may include hwpx (OOXML-style)
        elif body[:4] == b"\xd0\xcf\x11\xe0": ext = "hwp"  # CFB
        saved = _save(kr, name, body, ext=ext)
        result["status"] = "ok"
        result["path"] = str(saved.relative_to(ROOT)).replace("\\", "/")
        result["src_url"] = src
        result["bytes"] = len(body)
        print(f"  OK -> {saved.name} ({len(body):,} bytes)", flush=True)
    except Exception as exc:
        result["status"] = "fail"
        result["error"] = f"{type(exc).__name__}: {exc}"
        # screenshot for diagnosis
        try:
            shot = META_DIR / f"{kr}_failure.png"
            page.screenshot(path=str(shot), full_page=True)
            result["screenshot"] = str(shot.relative_to(ROOT)).replace("\\", "/")
        except Exception:
            pass
        # also save page HTML
        try:
            html = META_DIR / f"{kr}_failure.html"
            html.write_text(page.content(), encoding="utf-8")
            result["html_dump"] = str(html.relative_to(ROOT)).replace("\\", "/")
        except Exception:
            pass
        print(f"  FAIL {result['error']}", flush=True)
    finally:
        result["elapsed_s"] = round(time.time() - started, 2)
        browser.close()
    return result


def main() -> int:
    only = set(sys.argv[1:]) if len(sys.argv) > 1 else None
    targets = {k: v for k, v in INSURERS.items() if not only or k in only}

    # disable noisy urllib3 warnings (we use verify=False on some sites)
    import urllib3
    urllib3.disable_warnings()

    results = []
    with sync_playwright() as p:
        for kr, cfg in targets.items():
            results.append(_run_one(p, kr, cfg))

    manifest = {
        "_meta": {
            "period": "FY2026_Q1",
            "stamp_utc": datetime.now(timezone.utc).isoformat(),
            "insurer_count": len(results),
            "ok_count": sum(1 for r in results if r["status"] == "ok"),
            "fail_count": sum(1 for r in results if r["status"] == "fail"),
        },
        "results": results,
    }
    manifest_path = META_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[summary] ok={manifest['_meta']['ok_count']}/{len(results)} -> {manifest_path}")
    return 0 if manifest["_meta"]["fail_count"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
