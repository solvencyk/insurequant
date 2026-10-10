#!/usr/bin/env python3
"""공유 스크린샷 회귀 검사 (2026-10-11 신설, designer).

**왜 있나.** 2026-10-08 공통 공유 메뉴(8c997cb)가 `scrollHeight <= 6000` 일 때만 전체를 찍고 그보다 길면
"지금 보이는 화면"만 찍도록 막아 두었다. K-ICS·IFRS17·모바일은 거의 다 6000px 을 넘으니 사실상 늘 현재 화면만
찍혔고, 어느 게이트도 이미지를 만들어 보지 않아 두 번째 날 owner 가 눈으로 잡았다.
이 스크립트는 **실제로 헤드리스 브라우저에서 이미지를 만들어** 다음을 단정한다.

  1. 전체 페이지 이미지의 높이(CSS px)가 뷰포트 높이보다 크다(= 현재 화면만 찍히는 회귀가 아니다).
  2. 이미지 한 변이 캔버스 한도(IQTheme.share.limits.maxDim) 이하이고 비어 있지 않다(캔버스 한도에 먹혀 빈 이미지 아님).
  3. 섹션 이미지: 3~4곳을 만들고, 각 섹션 높이 ≈ 이미지 본문 높이이며 제목(페이지 · 섹션 · 회사)·출처 문구가 들어간다.
  4. 모든 `[data-share-section]` 에 버튼이 붙고 aria-label 이 있다. 버튼 타깃은 44px 이상.
  5. 콘솔 오류 0.

html2canvas 는 페이지가 SRI 로 CDN(jsdelivr)에서 불러온다. 망이 막혀 못 불러오면 SKIP(exit 0)로 끝내고 그 사실을 인쇄한다 —
"안 돌렸다 != 통과했다".

실행(저장소 루트에서):
    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/check_share_screenshot.py
    ... --out artifacts/designer/share_shots --company 삼성생명 --dark
종료코드: 0 = 통과 또는 SKIP · 1 = 회귀.
"""
from __future__ import annotations

import argparse
import base64
import re
import socket
import subprocess
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]

# (페이지, 회사 쿼리, 기대하는 섹션 수 — 이 수가 줄면 섹션이 빠진 것)
PAGES = [
    ("K-ICS.html", "", 4),                                   # 회사는 헤더 드롭다운에서 고른다(아래 SELECT_LABEL)
    ("IFRS17.html", "company=삼성생명", 9),
    ("compare.html", "c=삼성생명,한화생명,교보생명", 1),   # 지표 카드 수는 데이터에 따라 달라 하한만 본다
]
SELECT_LABEL = {"K-ICS.html": "삼성생명"}
VIEWPORTS = [("desktop", 1280, 900), ("mobile", 375, 812)]


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def start_server(port: int) -> subprocess.Popen:
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.3).close()
            return proc
        except OSError:
            time.sleep(0.2)
    raise RuntimeError("http.server 가 시작되지 않았습니다")


def stop_server(proc: subprocess.Popen) -> None:
    # Windows: venv python.exe 는 자식을 하나 더 띄운다 -> 트리째 종료
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        proc.terminate()


RENDER_JS = """
async (arg) => {
  const T = window.IQTheme.share;
  const ok = await new Promise(res => T.load(() => res(true), () => res(false)));
  if (!ok) return { error: 'html2canvas load failed' };
  let target;
  if (arg.kind === 'page') target = T.root();
  else target = document.querySelectorAll('[data-share-section]')[arg.index];
  if (!target) return { error: 'no target' };
  target.scrollIntoView({block: 'center'});    // 사용자는 스크롤한 채로 누른다 — 스크롤 위치에 영향받지 않는지도 본다
  const r = await T.render(target, arg.kind === 'page' ? { tag: 'full' } : T.secOpts(target));
  return { url: r.canvas.toDataURL('image/png'), meta: r.meta,
           bodyH: Math.ceil(Math.max(target.getBoundingClientRect().height, target.scrollHeight)),
           vh: window.innerHeight, vw: window.innerWidth };
}
"""


# 캔버스 한도: 아주 긴 합성 요소를 만들어 scale 이 내려가고(14,000px) 하한을 넘으면 위쪽만 담기는지(40,000px) 본다.
LIMIT_JS = """
async (h) => {
  const T = window.IQTheme.share;
  const ok = await new Promise(res => T.load(() => res(true), () => res(false)));
  if (!ok) return { error: 'html2canvas load failed' };
  const d = document.createElement('div');
  d.id = 'iqSynth';
  d.style.cssText = 'position:relative;width:100%;height:' + h + 'px;background:linear-gradient(#ffffff,#99aadd);font:16px sans-serif;margin:0';
  d.innerHTML = '<p style="margin:0;padding:8px">synthetic top</p>';
  document.body.appendChild(d);
  const r = await T.render(d, { tag: 'limit', settle: 100 });
  d.remove();
  const cv = r.canvas, probe = document.createElement('canvas'); probe.width = 4; probe.height = 64;
  const pc = probe.getContext('2d'); pc.drawImage(cv, 0, 0, 4, 64);
  const px = pc.getImageData(0, 0, 4, 64).data; let amin = 255, bmin = 255, bmax = 0;
  for (let i = 0; i < px.length; i += 4) { amin = Math.min(amin, px[i + 3]); bmin = Math.min(bmin, px[i + 2]); bmax = Math.max(bmax, px[i + 2]); }
  return { meta: r.meta, alphaMin: amin, spread: bmax - bmin, url: cv.toDataURL('image/png').length };
}
"""

PLAN_JS = """
() => {
  const P = window.IQTheme.share.plan, M = window.IQTheme.share.limits;
  return { m: M, cases: [
    ['short', P(375, 3000, 120, 2, true)], ['mid', P(375, 9000, 120, 2, true)],
    ['long', P(375, 14000, 120, 2, true)], ['huge', P(375, 40000, 120, 2, true)],
    ['wide-desktop', P(1062, 12000, 120, 2, false)]] };
}
"""


def run(args) -> int:
    from playwright.sync_api import sync_playwright

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    port = free_port()
    srv = start_server(port)
    fails: list[str] = []
    notes: list[str] = []
    skipped = False
    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception:
                browser = p.chromium.launch(headless=True, channel="msedge")
            for vname, vw, vh in VIEWPORTS:
                for page_name, company, want_secs in PAGES:
                    theme = "dark" if args.dark else "light"
                    ctx = browser.new_context(
                        viewport={"width": vw, "height": vh}, device_scale_factor=2 if vname == "mobile" else 1,
                        has_touch=(vname == "mobile"), is_mobile=(vname == "mobile"),
                        color_scheme=theme,
                    )
                    page = ctx.new_page()
                    # 분석 비콘은 테스트에서 내보내지 않는다(gtag 는 로컬 서빙이어도 실제로 나간다)
                    page.route(re.compile(r"google-analytics\.com|googletagmanager\.com"), lambda r: r.abort())
                    errors: list[str] = []
                    failed: list[str] = []
                    page.on("console", lambda m, e=errors: e.append(m.text) if m.type == "error" else None)
                    page.on("pageerror", lambda x, e=errors: e.append(str(x)))
                    page.on("requestfailed", lambda r, e=failed: e.append(r.url + " " + str(r.failure)))
                    url = f"http://127.0.0.1:{port}/{page_name}?iq_internal=1"
                    if company:
                        url += "&" + company
                    tag = f"{Path(page_name).stem}_{vname}_{theme}"
                    page.goto(url, wait_until="load", timeout=60000)
                    if page_name in SELECT_LABEL:
                        page.select_option("#company", label=SELECT_LABEL[page_name])
                    if page_name == "compare.html":
                        page.wait_for_selector("#grid .card", timeout=20000)
                    elif page_name == "IFRS17.html":
                        page.wait_for_selector("#sec-ps", state="attached", timeout=30000)
                    else:
                        page.wait_for_selector("#chart", state="attached", timeout=20000)
                    page.wait_for_timeout(2500)   # 차트 첫 렌더·입장 애니메이션
                    # 버튼 마운트(관찰자 디바운스) 대기
                    page.wait_for_selector(".iq-sec-share", state="attached", timeout=10000)
                    n_secs = page.locator("[data-share-section]").count()
                    n_btn = page.locator("[data-share-section] > .iq-sec-share").count()
                    if n_secs < want_secs:
                        fails.append(f"{tag}: 섹션 {n_secs}개 < 기대 {want_secs}")
                    if n_btn != n_secs:
                        fails.append(f"{tag}: 버튼 {n_btn}개 != 섹션 {n_secs}개")
                    lab = page.evaluate("[...document.querySelectorAll('.iq-sec-share')].every(b => b.getAttribute('aria-label') === '이 섹션 스크린샷 공유')")
                    if not lab:
                        fails.append(f"{tag}: 버튼 aria-label 불일치")
                    boxes = page.evaluate("[...document.querySelectorAll('.iq-sec-share')].map(b => { const r = b.getBoundingClientRect(); return [r.width, r.height]; })")
                    if any(w < 44 or h < 44 for w, h in boxes):
                        fails.append(f"{tag}: 버튼 타깃 44px 미만")
                    # 제목과 버튼 겹침: 제목(h2/h3) 오른쪽 끝이 버튼 왼쪽보다 작거나 padding 이 있어야 한다
                    over = page.evaluate("""[...document.querySelectorAll('[data-share-section]')].filter(s => { const h = s.querySelector(':scope > h2, :scope > h3'); return h && parseFloat(getComputedStyle(h).paddingRight) < 40; }).length""")
                    if over:
                        fails.append(f"{tag}: 제목 오른쪽 여백 부족 섹션 {over}곳")

                    # 전체 페이지
                    res = page.evaluate(RENDER_JS, {"kind": "page"})
                    if res.get("error") == "html2canvas load failed":
                        skipped = True
                        ctx.close()
                        break
                    if res.get("error") or not res.get("url"):
                        fails.append(f"{tag}: 전체 이미지 생성 실패 {res}")
                    else:
                        m = res["meta"]
                        fn = out / f"{tag}_FULL.png"
                        fn.write_bytes(base64.b64decode(res["url"].split(",", 1)[1]))
                        notes.append(f"{tag} FULL  {m['pxW']}x{m['pxH']}px  css {m['cssW']}x{m['cssH']}  scale {m['scale']:.2f}  body {m['fullBodyH']}  truncated={m['truncated']}")
                        if not m["cssH"] > res["vh"]:
                            fails.append(f"{tag}: 전체 이미지 높이 {m['cssH']} <= 뷰포트 {res['vh']} (현재 화면만 찍히는 회귀)")
                        if m["pxH"] > 16384 or m["pxW"] > 16384 or m["pxH"] < 100:
                            fails.append(f"{tag}: 이미지 크기 비정상 {m['pxW']}x{m['pxH']}")
                        # 전체 본문 높이 = 문서 안 모든 섹션 합 이상이어야 한다(섹션이 잘렸는지)
                        if not m["truncated"] and m["fullBodyH"] < res["vh"]:
                            fails.append(f"{tag}: 본문 높이 {m['fullBodyH']} < 뷰포트")
                        if m["truncated"]:
                            notes.append(f"  ! {tag}: 너무 길어 위쪽만 담음(truncated) — 이어 붙이기 후속 필요")

                    # 섹션 3~4곳
                    idxs = sorted({0, max(0, n_secs // 3), max(0, (2 * n_secs) // 3), n_secs - 1})
                    for i in idxs:
                        r2 = page.evaluate(RENDER_JS, {"kind": "section", "index": i})
                        if r2.get("error") or not r2.get("url"):
                            fails.append(f"{tag} sec{i}: 생성 실패 {r2}")
                            continue
                        m = r2["meta"]
                        fn = out / f"{tag}_sec{i}.png"
                        fn.write_bytes(base64.b64decode(r2["url"].split(",", 1)[1]))
                        notes.append(f"{tag} sec{i}  {m['pxW']}x{m['pxH']}px  scale {m['scale']:.2f}  head='{m['head']}'")
                        if m["fullBodyH"] < 40:
                            fails.append(f"{tag} sec{i}: 섹션 높이 {m['fullBodyH']}")
                        if "·" not in m["head"] and page_name != "compare.html":
                            fails.append(f"{tag} sec{i}: 제목에 페이지·섹션이 없음 '{m['head']}'")
                        joined = " ".join(m["lines"])
                        if "InsureQuant" not in joined or "자료" not in joined:
                            fails.append(f"{tag} sec{i}: 출처 문구 없음 {joined[:80]}")
                    # 실제 클릭 경로: 헤더 공유 메뉴 -> 다운로드(PNG), 섹션 버튼 -> 다운로드(PNG)
                    if page_name != "compare.html" or vname == "desktop":
                        from PIL import Image
                        page.evaluate("window.scrollTo(0, 500)")
                        page.click("#iqShareBtn")
                        with page.expect_download(timeout=120000) as dl:
                            page.get_by_role("menuitem", name="페이지 전체 스크린샷").click()
                        fp = out / f"{tag}_click_full.png"
                        dl.value.save_as(str(fp))
                        im = Image.open(fp)
                        dpr = 2 if vname == "mobile" else 1
                        if im.height <= vh * dpr:
                            fails.append(f"{tag}: 메뉴 클릭 이미지 높이 {im.height}px <= 뷰포트 {vh * dpr}px")
                        notes.append(f"{tag} CLICK-FULL {im.width}x{im.height}px")
                        page.wait_for_timeout(300)
                        with page.expect_download(timeout=120000) as dl2:
                            page.locator(".iq-sec-share").nth(min(1, n_secs - 1)).click()
                        fp2 = out / f"{tag}_click_sec.png"
                        dl2.value.save_as(str(fp2))
                        im2 = Image.open(fp2)
                        if im2.height >= im.height:
                            fails.append(f"{tag}: 섹션 클릭 이미지가 전체보다 크거나 같음")
                        notes.append(f"{tag} CLICK-SEC  {im2.width}x{im2.height}px")
                    # 콘솔 오류
                    # 네트워크 일시 오류(로컬 서버 밖 요청 실패)는 페이지 JS 오류가 아니다 — 알리기만 한다
                    ext = [u for u in failed if not u.startswith("http://127.0.0.1") and "google" not in u]
                    if ext:
                        notes.append(f"  (참고) {tag}: 외부 요청 실패 {ext[:2]}")
                    bad = [e for e in errors if "favicon" not in e.lower() and not e.startswith("Failed to load resource: net::ERR_")]
                    loc = [u for u in failed if u.startswith("http://127.0.0.1")]
                    if loc:
                        bad.append("로컬 요청 실패 " + loc[0])
                    if bad:
                        fails.append(f"{tag}: 콘솔 오류 {bad[:2]}")
                    if vname == "mobile" and page_name == "K-ICS.html":
                        plan = page.evaluate(PLAN_JS)
                        mx = plan["m"]["maxDim"]
                        for name, pl in plan["cases"]:
                            notes.append(f"PLAN {name}: scale {pl['scale']:.2f} cropH {pl['cropH']} truncated {pl['truncated']} cssH {pl['cssH']}")
                            if pl["cssH"] * pl["scale"] > mx + 1:
                                fails.append(f"plan {name}: 이미지 높이 {pl['cssH'] * pl['scale']:.0f}px 가 한도 {mx} 초과")
                        for h in (14000, 40000):
                            lr = page.evaluate(LIMIT_JS, h)
                            if lr.get("error"):
                                fails.append(f"한도 시험 {h}: {lr}")
                                continue
                            lm = lr["meta"]
                            notes.append(f"LIMIT {h}px  -> {lm['pxW']}x{lm['pxH']}px scale {lm['scale']:.2f} truncated={lm['truncated']} alphaMin={lr['alphaMin']} spread={lr['spread']}")
                            if lm["pxH"] > mx or lm["pxH"] < 100:
                                fails.append(f"한도 시험 {h}: 높이 {lm['pxH']}px 가 한도({mx}) 밖")
                            if lr["alphaMin"] < 255 or lr["spread"] < 8:
                                fails.append(f"한도 시험 {h}: 이미지가 비었음(alphaMin {lr['alphaMin']}, spread {lr['spread']})")
                            if h == 14000 and lm["truncated"]:
                                fails.append("한도 시험 14000: 위쪽만 담기면 안 되는 길이")
                            if h == 40000 and not lm["truncated"]:
                                fails.append("한도 시험 40000: 하한을 넘는데 truncated 표시가 없음")
                    ctx.close()
            browser.close()
    except Exception as e:  # noqa: BLE001
        msg = str(e)
        fails.append(f"예외: {type(e).__name__}: {msg[:300]}")
    finally:
        stop_server(srv)
    for n in notes:
        print(n)
    if skipped:
        print("SKIP: html2canvas(CDN) 를 불러오지 못했습니다 — 이 망에서는 검사하지 못했습니다(통과 아님)")
        return 0
    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("OK: 전체 이미지 > 뷰포트, 한도 이내, 섹션 버튼·출처·제목 확인")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "artifacts" / "designer" / "share_shots"))
    ap.add_argument("--dark", action="store_true")
    return run(ap.parse_args())


if __name__ == "__main__":
    sys.exit(main())
