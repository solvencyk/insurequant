#!/usr/bin/env python3
"""Download FY2026.2Q 정기경영공시 PDFs for 17 non-life insurers.

Copied from download_disclosure_2026q1_nonlife.py (2026-05-30 template) and
updated for the 2026.2Q period (2026-08-27). Per-insurer config drives one of
four download patterns:

  direct_href : XPath resolves to an <a> (or <a><img>) — read href, GET pdf.
  click_dl    : XPath resolves to a button/span/div that triggers a JS
                download — Playwright click + capture the download event.
  two_step    : Navigate URL1, click XPath1 to reach detail page, then
                resolve XPath2 (which is either direct_href or click_dl).

Most XPaths select "the first/latest row" (tr[1] etc.) and auto-adapt to a
new quarter without changes. 5 insurers hard-code the period label in the
XPath itself and were bumped 1분기->2분기 for this run: KR0002, KR0003,
KR0004_MG, KR0009, KR0032.

CAUTION (2026-08-27): manual site checks before this run (생보 22사 일괄,
한화손보, 삼성화재, KB손해보험) all showed 2026.2Q not yet posted (KB손보's own
historical listing shows -2/4분기 경영통일공시 registers 8/29~31 every year
since 2015). For "auto-latest" XPaths (KR0010, KR1000 in particular — fixed
tr[N] row index, not text-anchored), a "success" may just re-resolve to the
still-current 1Q row. Caller MUST hash-compare each output against the
existing FY2026_Q1 file for the same KR code and treat an identical hash as
an honest not-yet-posted gap, not a real 2Q collection.

Output: data/disclosure/FY2026_Q2/pdf/KR####_<name>.pdf
Manifest: data/disclosure/_meta/FY2026_Q2/manifest.json
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
OUT_DIR = ROOT / "data" / "disclosure" / "FY2026_Q2" / "pdf"
META_DIR = ROOT / "data" / "disclosure" / "_meta" / "FY2026_Q2"
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
    "KR0002": {  # 한화손보 — direct PDF href in HTML (2Q label bumped)
        "name": "한화손해보험", "mode": "direct_href",
        "url": "https://www.hwgeneralins.com/notice/ir/biz01.do",
        "xpath": '//a[contains(@title, "fy2026 2/4분기") or contains(@href, "FY2026-2_4.pdf") or contains(@title,"2026 상반기") or contains(@href,"FY2026-2H.pdf")]',
    },
    "KR0003": {  # 롯데손보 — 2-step: click 2026.2Q row → detail page → 2Q.zip JS dl
        "name": "롯데손해보험", "mode": "two_step",
        "url": "https://www.lotteins.co.kr/web/C/D/H/cdh_ir_board03_list.jsp",
        "step1_xpath": '//a[@title="2026년 2분기 경영공시"]',
        "step2_xpath": '//a[contains(@href, "downLoadFile")]',
        "step2_mode": "click_dl",
    },
    "KR0004_MG": {  # 예별손해보험 (구 MG손해보험) — id bumped quarter1->quarter2
        "name": "예별손해보험", "mode": "click_dl",
        "url": "https://yebyeol.co.kr/PB021010DM.scp?menuId=MN0802001",
        "xpath": '//*[@id="quarter2_2026"]',
    },
    "KR0005": {  # 흥국화재
        "name": "흥국화재", "mode": "click_dl",
        "url": "https://www.heungkukfire.co.kr/FRW/announce/manageRegular.do",
        "xpath": '//*[@id="tab01_01"]/dt/button/span',
    },
    "KR0008": {  # 삼성화재 — TEXT-ANCHORED, not cell-indexed (2026-08-31)
        # The old '.../tbody/tr[1]/td[1]/div/div/button' was positional. This site puts
        # BOTH quarters' buttons in the same row ('FY 26 1분기 PDF 다운로드' 와
        # 'FY 26 2분기 PDF 다운로드'), so td[1] is the 1분기 button and it kept returning a
        # zip holding only 1분기 files ([삼성화재] 2026년 1분기 경영공시_최종.pdf 등) even
        # after 2Q was posted. Same failure mode as the 하나손보/악사 entries. Anchor on
        # the button's own label instead.
        # Every button on the page has the SAME label ('PDF 다운로드') -- the quarter lives
        # in the sibling cell text, and the real discriminator is the onclick filename
        # (FY26_20260529.zip = 1분기, FY26_20260831.zip = 2분기). So anchor on the cell
        # that names the quarter and take the button inside it.
        "name": "삼성화재해상보험", "mode": "click_dl",
        "url": "https://www.samsungfire.com/v2/html/publication/02/J_020_010_001.html",
        "xpath": '//td[contains(., "2분기")]//button[contains(@class, "ico-pdf")]',
    },
    "KR0009": {  # 현대해상 — JS goMenu('100911') → 2026.2Q → li[3]=경영공시 최종 (li[1,2]=재무제표, skip)
        # 2026-08-31: 이 회사는 2분기를 "2026년 상반기 경영공시" 로 올린다("2분기" 아님).
        # 목록 실측: 2026년 상반기 / 2026년 1분기 / 2025년 결산 / 2025년 3분기 / 2025년 상반기.
        # 즉 짝수분기는 상반기·결산 표기라 "N분기" 단일 매칭이면 2Q·4Q 를 매번 놓친다.
        "name": "현대해상", "mode": "two_step",
        "url": "https://www.hi.co.kr/serviceAction.do",
        "js_eval_first": 'goMenu("100911")',
        "step1_xpath": ('//a[contains(text(), "2026년 상반기 경영공시")'
                        ' or contains(text(), "2026년 2분기 경영공시")]'),
        # 2026-08-31: li[3] 고정 인덱스는 틀렸다. 실측 첨부 목록은
        #   li[1] [현대해상]2026년 상반기 경영공시(최종).pdf   <- 이게 정답
        #   li[2] [현대해상]반기검토보고서(2026.08.14).pdf
        #   li[3] [현대해상]반기연결검토보고서(2026.08.14).pdf
        # li[3] 을 집었더니 129페이지짜리 삼일회계법인 반기연결검토보고서를 받아왔고
        # "지급여력" 이 한 번도 안 나오는 문서였다. 인덱스 대신 파일명으로 잡는다.
        # contains(text(), ...) 는 첫 텍스트 노드만 본다 — 이 앵커는 파일명과 크기가
        # 다른 노드로 쪼개져 있어 매칭에 실패했다. contains(., ...) 는 서브트리 전체 텍스트를 본다.
        "step2_xpath": '//*[@id="fileList"]//a[contains(., "경영공시")]',
        "step2_mode": "click_dl",
    },
    "KR0010": {  # KB손보 — fixed row index; site listing showed no 2026 2Q row yet as of 2026-08-27
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
        # This site does NOT use a uniform quarter label: 1Q is '2026년 1/4분기' but the
        # half-year filing is posted as **'2026년 상반기'** (verified 2026-08-31 against the
        # discovery census). The old '2026년 2/4분기 PDF다운로드' title never matched and the
        # download failed outright -- a loud failure, unlike the silent wrong-quarter
        # selectors fixed elsewhere in this file. Accept either spelling.
        "name": "NH농협손해보험", "mode": "click_dl",
        "url": "https://www.nhfire.co.kr/announce/managementAnnounce/retrievePeriodicManagementAnnounce.nhfire",
        "xpath": '//a[contains(@title, "상반기 PDF다운로드") or contains(@title, "2/4분기 PDF다운로드")]',
    },
    "KR0049": {  # 악사 — TEXT/HREF-ANCHORED, not row-indexed (2026-08-31)
        # Same defect the 하나손보 entry below already documents: the old
        # '.../tbody/tr[1]/td[2]/a' assumed "first row == newest quarter".
        # It is not — this table lists 1/4분기 above 2/4분기, so tr[1] returned
        # .../2026/05/29/1Q2026_Disclosure_AXA.pdf even after 2Q was posted, and it
        # came back byte-identical to FY2026_Q1 while the manifest said ok.
        # Caught by verify_q2_disclosure_content.py (REJECT: 내용이 2026 1분기).
        # Anchor on the quarter in the file name so the selector cannot drift.
        "name": "악사손해보험", "mode": "direct_href",
        "url": "https://www.axa.co.kr/cms/AsianPlatformInternet/html/axacms/common/intro/disclosure/regular/index.html",
        "xpath": '//a[contains(@href, "2Q2026_Disclosure")]',
    },
    "KR0050": {  # 하나손보 — TEXT-ANCHORED, not row-indexed (2026-08-29)
        # The old '//*[@id="targetRegularList"]/tr[1]/td[1]/a[1]' assumed
        # "first row == newest quarter". It is not: this site lists FY2026
        # 1/4분기 ABOVE 2/4분기, so tr[1] returned the 1Q file even after 2Q
        # was posted -- a byte-identical copy of FY2026_Q1, reported ok.
        # Anchor on the label so the selector cannot drift to another quarter.
        "name": "하나손해보험", "mode": "direct_href",
        "url": "https://m.hanainsure.co.kr/w/disclosure/manage/regularMngDisclosure",
        "xpath": '//a[contains(normalize-space(.), "FY2026 2/4분기 경영공시")]',
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
    "KR1000": {  # 코리안리 — HREF-ANCHORED, not row-indexed (2026-08-31)
        # The old '.../tbody/tr[2]/td[2]/a' was a fixed row index and returned the 1분기
        # file (.../gyungyoung/2026_1.pdf) after 2Q was posted -- byte-identical to
        # FY2026_Q1, reported ok. Caught by verify_q2_disclosure_content.py.
        # The quarter is in the filename, so anchor there.
        "name": "코리안리재보험", "mode": "direct_href",
        "url": "https://www.koreanre.co.kr/ir/ir_03_1.asp",
        "xpath": '//a[contains(@href, "gyungyoung/2026_2.pdf")]',
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
            "period": "FY2026_Q2",
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
