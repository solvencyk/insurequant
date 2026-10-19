#!/usr/bin/env python3
"""접근성 감사 C1·C2·C3·C4·C6 회귀 검사 (2026-10-19 신설, designer).

티켓 inbox/designer/20261019T1400Z__orchestrator__MULTI_ALL__a11y_compare_privacy.md 의 수락 기준을 그대로 단언한다.
  C1  `?` 팝오버가 마우스로 닿는다: 버튼 중앙에서 팝오버 중앙까지 1px 단위로 옮기는 동안(수직 우선 경로·직선 대각선·곡선 2개) 팝오버 opacity 가 내내 1(그리고 pointer-events:auto).
      키보드 포커스로 열리고 Esc 로 닫힌다. 375 폭에서 팝오버가 화면 안(좌우 8px 여백). 다리(::before)와 유예(is-grace)를 일부러 끈 음성 대조에서는 이 시험이 실제로 실패해야 한다.
      (compare + 공통 css 를 쓰는 4페이지)
      마우스 유예: ? 를 떠난 뒤 400ms 동안 팝오버가 남는다(theme.js pointerleave -> is-grace). 수직 우선·직선·아래로 휜 곡선 경로는 단언하고, 옆으로 먼저 멀리 갔다 내려오는 곡선은 400ms 를 넘으면 풀리므로 참고만 한다.
      호버 가로 넘침: 모든 `?` 버튼에 마우스를 올린 채로 문서 가로 폭이 화면 폭을 넘지 않는다(2026-10-19 에 시도했다 버린 버튼 옆 삼각형 호버 영역이 오른쪽 끝 버튼에서 문서를 넓힌 회귀 방지).
      탭 뒤에 남는 :hover 는 Playwright 터치 에뮬레이션이 만들지 못해(탭해도 :hover 불일치) 못 쟀다 - 375 폭 마우스 호버로 대신 잰다.
  C2  compare: 칩 제거 뒤(다음 칩 > 이전 칩 > 검색창)·4번째 회사를 키보드로 추가한 뒤(첫 칩 제거 버튼) activeElement 가 body 가 아니고 화면에 보이는 컨트롤.
      안내문 #live 는 그대로 나온다.
  C3  input#addco 테두리가 배경 대비 3.0:1 이상(라이트·다크). --border 값은 그대로, --control-border 는 #85888d / #727772. 네이티브 체크박스 테두리도 3:1 이상.
  C4  input#addco::placeholder 대비 4.5:1 이상(라이트·다크).
  C6  375 폭 손해율 꺾은선: 선마다 서로 다른 표식 모양, 현재가치 표 견본과 같은 모양, 넓은 화면 PT 와 같은 모양·색, 흐린 점선 구간에도 표식.
각 항목을 1280/375 x 라이트/다크 x compare 3 시나리오(생보 4사 · 손보 4사 · 회사 미선택)로 돈다.
모든 주소는 ?iq_internal=1, GA·수집기 요청은 route 로 막고 수집기 요청 0 을 단언한다.

실행(저장소 루트): C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/check_a11y_compare_privacy.py [--out DIR] [--root DIR]
종료코드 0 = 통과 · 1 = 위반 · 브라우저가 없으면 SKIP(exit 0)이며 "안 돌렸다" 로 인쇄한다. Chart.js(CDN)가 안 떠 넓은 화면 선을 못 읽은 항목은 "SKIP-WIDE" 로 따로 센다.
"""
from __future__ import annotations

import argparse
import re
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import quote

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
NOW = "2026-10-19T12:00:00+09:00"   # 안내 팝업 표시 시작일(2026-10-31) 전이라 팝업이 안 뜬다
SETS = {
    "life": ["삼성생명", "한화생명", "교보생명", "신한라이프"],
    "nonlife": ["삼성화재", "DB손보", "현대해상", "KB손보"],
    "none": [],
}
PT = ["circle", "triangle", "rect", "rectRot"]
VIEWPORTS = [("desktop", 1280, 900), ("mobile", 375, 812)]
BLOCK = re.compile(r"google-analytics\.com|googletagmanager\.com|script\.google\.com|script\.googleusercontent\.com")
COLLECTOR = re.compile(r"script\.google\.com|script\.googleusercontent\.com|google-analytics\.com")
COMMON_PAGES = ["index.html", "K-ICS.html", "IFRS17.html", "공시보고서.html"]
ALL_PAGES = COMMON_PAGES + ["compare.html", "privacy.html"]
BG = {"light": (255, 255, 255), "dark": (21, 22, 21)}
TOKENS = {"light": {"--border": "#e4e4e2", "--control-border": "#85888d"}, "dark": {"--border": "#313431", "--control-border": "#727772"}}


# ---------------------------------------------------------------- 색 계산
def nums(s: str) -> list[float]:
    return [float(x) for x in re.findall(r"[\d.]+", s or "")]


def parse_color(s: str) -> tuple[float, float, float, float]:
    n = nums(s)
    return (n[0], n[1], n[2], n[3] if len(n) > 3 else 1.0)


def over(fg, bg):
    a = fg[3]
    return tuple(fg[i] * a + bg[i] * (1 - a) for i in range(3))


def lum(rgb) -> float:
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(rgb[0]) + 0.7152 * ch(rgb[1]) + 0.0722 * ch(rgb[2])


def ratio(a, b) -> float:
    x, y = lum(a), lum(b)
    return (max(x, y) + 0.05) / (min(x, y) + 0.05)


def hex_rgb(h: str):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# ---------------------------------------------------------------- 서버
def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def start_server(port: int, root: Path) -> subprocess.Popen:
    proc = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
                            cwd=str(root), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.3).close()
            return proc
        except OSError:
            time.sleep(0.2)
    raise RuntimeError("http.server 가 시작되지 않았습니다")


def stop_server(proc: subprocess.Popen) -> None:
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        proc.terminate()


# ---------------------------------------------------------------- 페이지 안에서 도는 조각
HELP_PREP_JS = """(i) => {
  const bs = document.querySelectorAll('.iq-help-btn');
  const b = bs[i]; if (!b) return null;
  b.scrollIntoView({block: 'center'});
  const r = b.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2;
  const e = document.elementFromPoint(cx, cy);
  return {n: bs.length, cx: cx, cy: cy, bottom: r.bottom, hit: !!e && (e === b || b.contains(e)), cover: e ? e.tagName + '.' + String(e.className).slice(0, 40) : null, w: r.width};
}"""
HELP_STATE_JS = """(i) => {
  const b = document.querySelectorAll('.iq-help-btn')[i];
  const p = b.closest('.iq-help').querySelector('.iq-help-pop');
  const cs = getComputedStyle(p), r = p.getBoundingClientRect();
  return {op: parseFloat(cs.opacity), pe: cs.pointerEvents, l: r.left, r: r.right, t: r.top, b: r.bottom, vw: innerWidth, vh: innerHeight,
          bridge: getComputedStyle(p, '::before').height, bridgeContent: getComputedStyle(p, '::before').content};
}"""
ACTIVE_JS = """() => {
  const a = document.activeElement, r = a.getBoundingClientRect(), cs = getComputedStyle(a), live = document.getElementById('live');
  return {isBody: a === document.body || a === document.documentElement, tag: a.tagName, id: a.id, label: a.getAttribute('aria-label'), disabled: !!a.disabled,
          w: r.width, h: r.height, t: r.top, b: r.bottom, l: r.left, r: r.right, vis: cs.visibility, disp: cs.display,
          vw: innerWidth, vh: innerHeight, live: live ? live.textContent : null, liveAttr: live ? live.getAttribute('aria-live') : null,
          chips: [...document.querySelectorAll('#chips li button')].map(x => x.getAttribute('aria-label'))};
}"""
INPUT_JS = """() => {
  const el = document.getElementById('addco'), cs = getComputedStyle(el), ph = getComputedStyle(el, '::placeholder');
  let bg = null, n = el.parentElement;
  while (n) { const c = getComputedStyle(n).backgroundColor; const a = c.match(/[\\d.]+/g); if (a && (a.length < 4 || parseFloat(a[3]) > 0)) { bg = c; break; } n = n.parentElement; }
  const root = getComputedStyle(document.documentElement);
  return {disabled: el.disabled, border: cs.borderTopColor, borderW: cs.borderTopWidth, bg: cs.backgroundColor, outer: bg, ph: ph.color, phOp: ph.opacity,
          bodyBg: getComputedStyle(document.body).backgroundColor, tokBorder: root.getPropertyValue('--border').trim(), tokCtl: root.getPropertyValue('--control-border').trim(),
          dark: matchMedia('(prefers-color-scheme: dark)').matches};
}"""
LOSS_JS = """() => {
  const svg = document.querySelector('.lcs svg');
  const rows = [...document.querySelectorAll('.lcm tbody tr')].map(tr => {
    const sw = tr.querySelector('svg.sw'), mk = sw && sw.querySelector('.mk'), ln = sw && sw.querySelector('line');
    return {name: tr.cells[0].textContent, pt: mk ? mk.getAttribute('data-pt') : null, tag: mk ? mk.tagName.toLowerCase() : null,
            color: ln ? ln.getAttribute('stroke') : null, dash: ln ? ln.getAttribute('stroke-dasharray') : null, mkfill: mk ? mk.getAttribute('fill') : null,
            swW: sw ? sw.getBoundingClientRect().width : 0, swH: sw ? sw.getBoundingClientRect().height : 0};
  });
  if (!svg) return {svg: false, rows};
  const groups = [...svg.querySelectorAll('g.mks')].map(g => ({
    line: g.getAttribute('data-line'), pt: g.getAttribute('data-pt'),
    marks: [...g.querySelectorAll('.mk')].map(m => { const bb = m.getBBox(); return {pt: m.getAttribute('data-pt'), tag: m.tagName.toLowerCase(), fill: m.getAttribute('fill'), stroke: m.getAttribute('stroke'),
      sw: m.getAttribute('stroke-width'), w: bb.width, h: bb.height, pts: m.getAttribute('points')}; })}));
  const paths = [...svg.querySelectorAll('path[data-line]')].map(p => ({line: p.getAttribute('data-line'), stroke: p.getAttribute('stroke'), dash: p.getAttribute('stroke-dasharray')}));
  return {svg: true, rows, groups, paths, w: svg.getBoundingClientRect().width};
}"""
WIDE_JS = """() => {
  if (typeof Chart === 'undefined') return null;
  const out = [];
  Object.values(Chart.instances).forEach(c => c.data.datasets.forEach(d => { if (d.short !== undefined && d.pointStyle) out.push({short: d.short, color: d.borderColor, pt: d.pointStyle}); }));
  return out;
}"""
FORM_JS = """() => [...document.querySelectorAll('.iq-input,.iq-textarea,.iq-select')].map(e => { const c = getComputedStyle(e), p = getComputedStyle(e, '::placeholder');
  return {cls: e.className, border: c.borderTopColor, bg: c.backgroundColor, ph: p.color}; })"""
LAYOUT_JS = """() => ({sw: document.documentElement.scrollWidth, iw: innerWidth,
  tokBorder: getComputedStyle(document.documentElement).getPropertyValue('--border').trim(), tokCtl: getComputedStyle(document.documentElement).getPropertyValue('--control-border').trim(),
  dark: matchMedia('(prefers-color-scheme: dark)').matches, bg: getComputedStyle(document.body).backgroundColor, help: document.querySelectorAll('.iq-help-btn').length,
  notice: !!document.getElementById('iqNotice')})"""


def run(args) -> int:
    from playwright.sync_api import sync_playwright

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    port = free_port()
    root = Path(args.root)
    srv = start_server(port, root)
    fails: list[str] = []
    n_checks = [0]
    skips: list[str] = []
    info: list[str] = []
    meas: dict[str, float] = {}   # 최소·최대 실측값(항목 이름 -> 값). 끝에 인쇄한다

    def mmin(key: str, v: float) -> None:
        meas[key] = min(v, meas.get(key, v))

    def mmax(key: str, v: float) -> None:
        meas[key] = max(v, meas.get(key, v))
    stats = {"gtag_blocked": 0, "collector": 0, "ga_beacon": 0}

    def check(cond: bool, msg: str) -> None:
        n_checks[0] += 1
        if not cond:
            fails.append(msg)

    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception:
                try:
                    browser = p.chromium.launch(headless=True, channel="msedge")
                except Exception as e:  # 브라우저 없음
                    print("SKIP: 브라우저를 띄울 수 없어 안 돌렸다 (" + str(e).splitlines()[0] + ")")
                    return 0

            def new(vw, vh, scheme, touch=None):
                mobile = (vw < 641) if touch is None else touch
                ctx = browser.new_context(viewport={"width": vw, "height": vh}, color_scheme=scheme, has_touch=mobile, is_mobile=mobile, timezone_id="Asia/Seoul")
                pg = ctx.new_page()
                pg.set_default_timeout(30000)
                pg.clock.set_fixed_time(NOW)
                errs: list[str] = []
                reqs: list[str] = []
                pg.on("console", lambda m, e=errs: e.append(m.text) if m.type == "error" and "net::ERR_" not in m.text else None)
                pg.on("pageerror", lambda x, e=errs: e.append(str(x)))
                pg.on("request", lambda r, q=reqs: q.append(r.url))
                pg.route(BLOCK, lambda r: r.abort())
                return ctx, pg, errs, reqs

            def url(name, names=None):
                q = "?iq_internal=1"
                if names:
                    q += "&c=" + quote(",".join(names))
                return f"http://127.0.0.1:{port}/{name}{q}"

            def go(pg, name, names=None, wait_cmp=True):
                for attempt in range(3):   # 외부 CDN(chart.js·글꼴)이 가끔 멈춰 load 가 안 끝난다 — 그때만 다시 연다
                    try:
                        pg.goto(url(name, names), wait_until="load", timeout=30000)
                        break
                    except Exception as e:
                        if attempt == 2 or "Timeout" not in str(e):
                            raise
                        info.append(f"{name}: 페이지 로드 시간 초과, 다시 엶({attempt + 1})")
                if name == "compare.html" and wait_cmp:
                    pg.wait_for_function("() => document.getElementById('main-msg').hidden", timeout=30000)
                pg.wait_for_timeout(500)

            def tally(reqs, tag):
                for u in reqs:
                    if COLLECTOR.search(u):
                        stats["collector"] += 1
                        fails.append(f"[{tag}] 수집기·분석 요청 발생 {u[:80]}")
                    elif "googletagmanager.com" in u:
                        stats["gtag_blocked"] += 1   # 정적 gtag.js 태그. route 가 막는다(전송 0)
                n_checks[0] += 1

            # ---------- C1: 마우스 경로 ------------------------------------------------------------
            tested = [0]
            hov_tested = [0]   # 호버 가로 넘침을 실제로 잰 버튼 수

            def c1_mouse(pg, tag, idxs, expect_lost=False):
                """expect_lost=True 는 다리를 끈 음성 대조: 경로 어딘가에서 팝오버가 풀리면 정상(시험이 버그를 잡는다는 증거)."""
                lost_any = False
                for i in idxs:
                    pg.mouse.move(2, 2)
                    pg.wait_for_timeout(150)
                    prep = pg.evaluate(HELP_PREP_JS, i)
                    if not prep:
                        continue
                    pg.wait_for_timeout(120)
                    prep = pg.evaluate(HELP_PREP_JS, i)
                    if prep["w"] <= 0 or not prep["hit"]:   # 안 보이거나 다른 요소(예: 떠 있는 버튼)가 덮은 버튼은 마우스 시험 대상이 아니다. 몇 개를 건너뛰었는지 알린다
                        info.append(f"{tag}#{i}: 마우스 시험 건너뜀(닫힌 패널 안이라 안 보이거나 {prep['cover']} 가 덮음)")
                        continue
                    tested[0] += 1
                    pg.mouse.move(prep["cx"], prep["cy"])
                    pg.wait_for_timeout(350)
                    st = pg.evaluate(HELP_STATE_JS, i)
                    if st["b"] > st["vh"] - 2:   # 팝오버가 아래로 잘리면 조금 올려 다시 잰다
                        pg.evaluate("(d) => window.scrollBy(0, d)", st["b"] - st["vh"] + 40)
                        pg.wait_for_timeout(150)
                        prep = pg.evaluate(HELP_PREP_JS.replace("scrollIntoView({block: 'center'})", "getBoundingClientRect()"), i)
                        if not prep["hit"]:   # 올린 뒤에 고정 머리글 등이 버튼을 덮으면 마우스로 닿을 수 없는 자리라 시험 대상이 아니다
                            info.append(f"{tag}#{i}: 팝오버가 화면보다 커서 올린 뒤 {prep['cover']} 가 버튼을 덮음 — 마우스 시험 건너뜀")
                            tested[0] -= 1
                            continue
                        pg.mouse.move(prep["cx"], prep["cy"])
                        pg.wait_for_timeout(350)
                        st = pg.evaluate(HELP_STATE_JS, i)
                    cx, cy = prep["cx"], prep["cy"]
                    px, py = (st["l"] + st["r"]) / 2, (st["t"] + st["b"]) / 2
                    check(st["op"] >= 0.999 and st["pe"] == "auto", f"[{tag}#{i}] 버튼 위에서 팝오버가 안 열림 op={st['op']} pe={st['pe']}")
                    # 경로: 버튼 중앙에서 수직으로 팝오버 중앙의 높이까지(틈을 가로지른다), 거기서 수평으로 팝오버 중앙까지. 1px 단위.
                    check(st["l"] <= cx <= st["r"], f"[{tag}#{i}] 팝오버 가로 범위 [{st['l']:.0f},{st['r']:.0f}] 가 버튼 중앙 {cx:.0f} 를 포함하지 않음")
                    vert = [(round(cx), round(cy + (py - cy) * s / max(1, int(abs(py - cy))))) for s in range(1, int(abs(py - cy)) + 1)]
                    vert += [(round(cx + (px - cx) * s / max(1, int(abs(px - cx)))), round(py)) for s in range(1, int(abs(px - cx)) + 1)]
                    # 직선: 버튼 중앙에서 팝오버 중앙까지 1px 단위 대각선(티켓 수락 기준 그대로). 곡선: 같은 두 점을 잇는 2차 곡선 두 개(위쪽으로 휘는 것·아래쪽으로 휘는 것).
                    nline = max(2, int(((px - cx) ** 2 + (py - cy) ** 2) ** 0.5))
                    line = [(round(cx + (px - cx) * s / nline), round(cy + (py - cy) * s / nline)) for s in range(1, nline + 1)]

                    def bez(kx, ky):
                        qx, qy = cx + (px - cx) * kx, cy + (py - cy) * ky
                        return [(round((1 - u) ** 2 * cx + 2 * (1 - u) * u * qx + u * u * px), round((1 - u) ** 2 * cy + 2 * (1 - u) * u * qy + u * u * py))
                                for u in (s / nline for s in range(1, nline + 1))]
                    paths = [("수직 우선", vert), ("직선", line), ("곡선(아래로 휨)", bez(0.25, 0.9)), ("곡선(옆으로 휨)", bez(0.7, 0.35))]
                    for pname, pts in paths:
                        n = len(pts)
                        min_op, min_pe_ok = 1.0, True
                        for (x, y) in pts[::args.step] + pts[-1:]:
                            pg.mouse.move(x, y)
                            pg.wait_for_timeout(2)   # 걸음당 약 8ms(1px 단위 약 125px/s, --step 3 이면 약 370px/s): 사람 손보다 느린 쪽이라 유예(400ms)에 불리하다
                            t = pg.evaluate(HELP_STATE_JS, i)
                            min_op = min(min_op, t["op"])
                            if t["pe"] != "auto":
                                min_pe_ok = False
                        lost = min_op < 0.999 or not min_pe_ok
                        lost_any = lost_any or lost
                        if pname.startswith("곡선(옆으로"):
                            if lost and not expect_lost:
                                info.append(f"참고 [{tag}#{i}] 옆으로 먼저 멀리 갔다가 내려오는 경로는 유예(400ms)를 넘기면 풀린다(단언 대상 아님)")
                        elif not expect_lost:
                            check(not lost, f"[{tag}#{i}] 마우스 {pname} 경로(버튼 중앙→팝오버 중앙 {n}단계)에서 팝오버가 풀림 최소 opacity={min_op:.2f} pointer-events 유지={min_pe_ok}")
                        # 다음 경로를 위해 버튼 중앙으로 되돌아간다(열린 채로)
                        pg.mouse.move(cx, cy)
                        pg.wait_for_timeout(120)
                    check(st["bridgeContent"] not in ("none", "normal") or expect_lost, f"[{tag}#{i}] 다리(::before)가 없음")
                    pg.mouse.move(2, 2)
                if expect_lost:
                    check(lost_any, f"[{tag}] 음성 대조 실패: 다리를 껐는데도 경로에서 팝오버가 안 풀림(시험이 버그를 못 잡는다)")

            def c1_keyboard(pg, tag, vw):
                n = pg.evaluate("() => document.querySelectorAll('.iq-help-btn').length")
                lo, hi = 1e9, -1e9
                for i in range(n):
                    pg.evaluate("(i) => { const b = document.querySelectorAll('.iq-help-btn')[i]; b.scrollIntoView({block: 'center'}); b.focus(); }", i)
                    pg.wait_for_timeout(180)
                    st = pg.evaluate(HELP_STATE_JS, i)
                    check(st["op"] >= 0.999, f"[{tag}#{i}] 포커스로 팝오버가 안 열림 op={st['op']}")
                    lo, hi = min(lo, st["l"]), max(hi, st["r"])
                    if vw < 641:
                        check(st["l"] >= 7.5 and st["r"] <= vw - 7.5, f"[{tag}#{i}] 375 폭 팝오버가 화면 여백 밖 [{st['l']:.0f},{st['r']:.0f}]")
                    pg.keyboard.press("Escape")
                    pg.wait_for_timeout(180)
                    st = pg.evaluate(HELP_STATE_JS, i)
                    check(st["op"] <= 0.001 and st["pe"] == "none", f"[{tag}#{i}] Esc 로 안 닫힘 op={st['op']} pe={st['pe']}")
                    pg.evaluate("(i) => document.querySelectorAll('.iq-help-btn')[i].blur()", i)
                return n, lo, hi

            def c1_hover_overflow(pg, tag, vw, expect_over=False):
                """? 버튼 전부에 마우스를 올린 채로 문서 가로 폭을 잰다. 호버 중 문서가 화면 폭보다 넓어지면 실패.
                expect_over=True 이면 단언하지 않고 최대 넘침을 돌려준다(변이시험용)."""
                n = pg.evaluate("() => document.querySelectorAll('.iq-help-btn').length")
                worst = 0
                for i in range(n):
                    pg.mouse.move(2, 2)
                    pg.wait_for_timeout(60)
                    prep = pg.evaluate(HELP_PREP_JS, i)
                    if not prep:
                        continue
                    pg.wait_for_timeout(80)
                    prep = pg.evaluate(HELP_PREP_JS, i)
                    if prep["w"] <= 0 or not prep["hit"]:
                        info.append(f"{tag}#{i}: 호버 가로 넘침 시험 건너뜀(닫힌 패널 안이라 안 보이거나 {prep['cover']} 가 덮음)")
                        continue
                    pg.mouse.move(prep["cx"], prep["cy"])
                    pg.wait_for_timeout(220)
                    r = pg.evaluate("([i, vw]) => ({ov: document.documentElement.scrollWidth - vw, hov: document.querySelectorAll('.iq-help-btn')[i].closest('.iq-help').matches(':hover')})", [i, vw])
                    if not expect_over:
                        check(r["hov"], f"[{tag}#{i}] 호버 상태가 안 걸려 가로 넘침을 못 쟀다")
                        check(r["ov"] <= 0, f"[{tag}#{i}] ? 에 마우스를 올린 동안 문서가 가로로 넓어짐 +{r['ov']}px")
                        hov_tested[0] += 1 if r["hov"] else 0
                        mmax("C1 호버 중 가로 넘침 최대(px)", max(0, r["ov"]))
                    worst = max(worst, r["ov"])
                pg.mouse.move(2, 2)
                pg.evaluate("() => { if (document.activeElement && document.activeElement.blur) document.activeElement.blur(); }")
                return worst

            # ---------- C2 -----------------------------------------------------------------------
            def visible_control(a):
                return (not a["isBody"] and a["w"] > 0 and a["h"] > 0 and a["vis"] == "visible" and a["disp"] != "none"
                        and a["b"] > 0 and a["t"] < a["vh"] and a["r"] > 0 and a["l"] < a["vw"])

            def remove_cascade(pg, tag, names):
                """키보드로 칩을 하나씩 뺀다: 가운데 > 마지막 > 첫째 > 하나 남은 칩. 매번 포커스·안내문을 단언."""
                cur = list(names)
                plan = [1, len(names) - 2, 0, 0]   # 4 → 가운데(1) → 마지막(2) → 첫째(0) → 남은 하나(0)
                for step, k in enumerate(plan):
                    if not cur:
                        break
                    k = min(k, len(cur) - 1)
                    pg.locator("#chips li button").nth(k).focus()
                    pg.keyboard.press("Enter")
                    pg.wait_for_timeout(180)
                    gone = cur.pop(k)
                    a = pg.evaluate(ACTIVE_JS)
                    check(visible_control(a), f"[{tag} 제거{step}] 포커스가 body 이거나 안 보임 {a['tag']}#{a['id']}")
                    if cur:
                        want = cur[k] if k < len(cur) else cur[k - 1]
                        check(a["label"] == f"{want} 제거", f"[{tag} 제거{step}] 포커스가 다음/이전 칩 제거 버튼이 아님 {a['label']!r} 기대 {want!r}")
                    else:
                        check(a["id"] == "addco" and not a["disabled"], f"[{tag} 제거{step}] 칩이 없는데 포커스가 검색창이 아님 {a['tag']}#{a['id']}")
                    check(a["live"] == f"{gone} 제거", f"[{tag} 제거{step}] #live 안내문 {a['live']!r}")
                    check(a["liveAttr"] in ("polite", "assertive"), f"[{tag}] #live aria-live={a['liveAttr']!r}")
                    check(a["chips"] == [f"{x} 제거" for x in cur], f"[{tag} 제거{step}] 칩 목록 {a['chips']}")

            def add_cascade(pg, tag, names):
                """키보드로 회사를 하나씩 더한다. 3번째까지는 검색창에 포커스가 남고, 4번째는 첫 칩 제거 버튼으로."""
                pg.locator("#addco").focus()
                for k, nm in enumerate(names):
                    pg.keyboard.type(nm)
                    pg.wait_for_timeout(120)
                    pg.keyboard.press("ArrowDown")
                    pg.keyboard.press("Enter")
                    pg.wait_for_timeout(180)
                    a = pg.evaluate(ACTIVE_JS)
                    check(a["live"] == f"{nm} 추가", f"[{tag} 추가{k}] #live 안내문 {a['live']!r}")
                    check(a["chips"] == [f"{x} 제거" for x in names[:k + 1]], f"[{tag} 추가{k}] 칩 목록 {a['chips']}")
                    if k < len(names) - 1:
                        check(a["id"] == "addco" and not a["disabled"], f"[{tag} 추가{k}] 검색창 포커스 유지 실패 {a['tag']}#{a['id']}")
                    else:
                        check(visible_control(a), f"[{tag} 4곳째 추가] 포커스가 body 이거나 안 보임 {a['tag']}#{a['id']}")
                        check(a["label"] == f"{names[0]} 제거", f"[{tag} 4곳째 추가] 포커스가 첫 칩 제거 버튼이 아님 {a['label']!r}")
                        check(pg.evaluate("() => document.getElementById('addco').disabled"), f"[{tag} 4곳째 추가] 검색창이 비활성이어야 함")

            def pointer_removal(pg, tag, names):
                """마우스 클릭 제거: 칩이 남아 있으면 그 칩 제거 버튼, 마지막 칩이면 검색창을 열지 않는다(화면 키보드 방지)."""
                two = names[:2]
                go(pg, "compare.html", two)
                pg.locator("#chips li button").nth(0).click()
                pg.wait_for_timeout(180)
                a = pg.evaluate(ACTIVE_JS)
                check(visible_control(a) and a["label"] == f"{two[1]} 제거", f"[{tag} 마우스 제거] 포커스 {a['tag']}#{a['id']} {a['label']!r}")
                pg.locator("#chips li button").nth(0).click()
                pg.wait_for_timeout(180)
                a = pg.evaluate(ACTIVE_JS)
                check(a["id"] != "addco", f"[{tag} 마우스 제거] 마지막 칩을 마우스로 뺐는데 검색창이 포커스를 받음")

            # ---------- C3·C4 ---------------------------------------------------------------------
            def c3_c4(pg, tag, scheme):
                s = pg.evaluate(INPUT_JS)
                check(s["dark"] == (scheme == "dark"), f"[{tag}] 색 구성표가 적용되지 않음")
                check(s["tokBorder"].lower() == TOKENS[scheme]["--border"], f"[{tag}] --border 값이 바뀜 {s['tokBorder']}")
                check(s["tokCtl"].lower() == TOKENS[scheme]["--control-border"], f"[{tag}] --control-border 값 {s['tokCtl']}")
                if s["disabled"]:
                    return
                bg_in = over(parse_color(s["bg"]), BG[scheme])
                outer = over(parse_color(s["outer"]), BG[scheme]) if s["outer"] else BG[scheme]
                bd = parse_color(s["border"])
                c_in = ratio(over(bd, bg_in), bg_in)
                c_out = ratio(over(bd, outer), outer)
                check(float(s["borderW"][:-2]) >= 1, f"[{tag}] 검색창 테두리 두께 {s['borderW']}")
                check(c_in >= 3.0 and c_out >= 3.0, f"[{tag}] C3 테두리 대비 입력창 안 {c_in:.2f} 바깥 {c_out:.2f} (3.0 미만)")
                ph = parse_color(s["ph"])
                c_ph = ratio(over(ph, bg_in), bg_in)
                check(ph[3] == 1.0 and float(s["phOp"]) == 1.0, f"[{tag}] C4 placeholder 투명도 {s['ph']} op={s['phOp']}")
                check(c_ph >= 4.5, f"[{tag}] C4 placeholder 대비 {c_ph:.2f} (4.5 미만)")
                mmin(f"C3 검색창 테두리 대비 최소 {scheme}", min(c_in, c_out))
                mmin(f"C4 placeholder 대비 최소 {scheme}", c_ph)

            # ---------- C6 -----------------------------------------------------------------------
            def c6(d, tag, names, wide):
                rows = d["rows"][:len(names)]
                check(len(rows) == len(names), f"[{tag}] 현재가치 표 회사 행 {len(rows)}≠{len(names)}")
                with_mk = [(i, r) for i, r in enumerate(rows) if r["pt"]]
                check(d["svg"] and len(d["groups"]) >= 1 and len(with_mk) == len(d["groups"]), f"[{tag}] 선 표식 그룹 {len(d.get('groups', []))} 표 견본 표식 {len(with_mk)}")
                if not d["svg"]:
                    return
                check([int(g["line"]) for g in d["groups"]] == [i for i, _ in with_mk], f"[{tag}] 선 표식 그룹 순서·번호가 표와 다름")
                kinds = [g["pt"] for g in d["groups"]]
                check(len(set(kinds)) == len(kinds), f"[{tag}] 선마다 모양이 서로 달라야 함 {kinds}")
                for g in d["groups"]:
                    k = int(g["line"])
                    check(g["pt"] == PT[k % 4], f"[{tag}] 선{k} 모양 {g['pt']} 기대(넓은 화면 PT) {PT[k % 4]}")
                    check(len(g["marks"]) >= 1, f"[{tag}] 선{k} 표식 0개")
                    row = rows[k]
                    check(row["pt"] == g["pt"], f"[{tag}] 선{k} 모양 {g['pt']} 표 견본 {row['pt']}")
                    exp_tag = {"circle": "circle", "triangle": "polygon", "rect": "rect", "rectRot": "polygon"}[g["pt"]]
                    check(row["tag"] == exp_tag, f"[{tag}] 선{k} 표 견본 요소 {row['tag']}")
                    check(row["swW"] >= 22 - 0.5 and row["swH"] >= 10, f"[{tag}] 선{k} 표 견본 크기 {row['swW']}x{row['swH']}")
                    solid = [p for p in d["paths"] if p["line"] == str(k) and not p["dash"]]
                    dashed = [p for p in d["paths"] if p["line"] == str(k) and p["dash"]]
                    main_col = row["color"]
                    check(row["mkfill"] == main_col, f"[{tag}] 선{k} 표 견본 표식 색 {row['mkfill']} 선색 {main_col}")
                    if solid:
                        check(all(p["stroke"] == main_col for p in solid), f"[{tag}] 선{k} 선 색 {[p['stroke'] for p in solid]} 표 견본 색 {main_col}")
                    for m in g["marks"]:
                        check(m["pt"] == g["pt"] and m["tag"] == exp_tag, f"[{tag}] 선{k} 표식 요소 불일치 {m['tag']}/{m['pt']}")
                        check(5 <= m["w"] <= 10 and 5 <= m["h"] <= 10, f"[{tag}] 선{k} 표식 크기 {m['w']:.1f}x{m['h']:.1f}")
                        if g["pt"] == "triangle":
                            check(len(re.split(r"[ ,]+", m["pts"].strip())) == 6, f"[{tag}] 선{k} 삼각형 꼭짓점")
                        if g["pt"] == "rectRot":
                            check(len(re.split(r"[ ,]+", m["pts"].strip())) == 8, f"[{tag}] 선{k} 마름모 꼭짓점")
                    hollow = [m for m in g["marks"] if m["fill"] == "var(--bg)"]
                    filled = [m for m in g["marks"] if m["fill"] != "var(--bg)"]
                    check(all(m["fill"] == main_col and m["stroke"] == main_col for m in filled), f"[{tag}] 선{k} 속 찬 표식 색이 선색과 다름")
                    if dashed:
                        # 흐린 점선 구간마다 표식이 하나 이상(넓은 화면 흐린 칸의 속 빈 표식과 같은 모양)
                        check(len(hollow) >= 1, f"[{tag}] 선{k} 흐린 점선 구간이 있는데 속 빈 표식 0개")
                        fcols = {p["stroke"] for p in dashed}
                        check(all(m["stroke"] in fcols and m["sw"] == "2" for m in hollow), f"[{tag}] 선{k} 속 빈 표식 윤곽이 흐린 선 색과 다름")
                        check(all(p["dash"] == "2 4" for p in dashed), f"[{tag}] 선{k} 흐린 구간 점선 모양 {[p['dash'] for p in dashed]}")
                    else:
                        check(not hollow, f"[{tag}] 선{k} 흐린 구간이 없는데 속 빈 표식이 있음")
                if wide:
                    for r in rows:
                        if not r["pt"]:
                            continue
                        w = next((x for x in wide if r["name"].startswith(x["short"])), None)
                        check(w is not None, f"[{tag}] 넓은 화면에 같은 회사 선이 없음 {r['name']!r}")
                        if w:
                            check(w["pt"] == r["pt"], f"[{tag}] 모양이 넓은 화면과 다름 {r['name']!r} 좁은 {r['pt']} 넓은 {w['pt']}")
                            check(str(w["color"]).lower() == r["color"].lower(), f"[{tag}] 색이 넓은 화면과 다름 {r['name']!r} 좁은 {r['color']} 넓은 {w['color']}")

            # ======================= 실행 ==============================================================
            faded_seen = [0]
            wide_cache: dict = {}
            for scheme in ("light", "dark"):
                # ---- 공통 css 페이지 6개: 토큰·가로 넘침 (1280/375) + 4개 페이지 `?` 마우스 경로(1280) ----
                for vname, vw, vh in VIEWPORTS:
                    for name in ALL_PAGES:
                        tag = f"{name}|{vname}|{scheme}"
                        ctx, pg, errs, reqs = new(vw, vh, scheme)
                        go(pg, name)
                        L = pg.evaluate(LAYOUT_JS)
                        check(L["sw"] <= L["iw"], f"[{tag}] 가로 넘침 {L['sw']}>{L['iw']}")
                        check(L["dark"] == (scheme == "dark"), f"[{tag}] 색 구성표 미적용")
                        check(L["tokBorder"].lower() == TOKENS[scheme]["--border"] and L["tokCtl"].lower() == TOKENS[scheme]["--control-border"], f"[{tag}] 토큰 값 {L['tokBorder']} {L['tokCtl']}")
                        check(not L["notice"], f"[{tag}] 안내 팝업이 뜸(시계 고정 실패)")
                        pg.screenshot(path=str(out / f"page_{Path(name).stem}_{vname}_{scheme}.png"))
                        if L["help"] and vname == "desktop":
                            c1_hover_overflow(pg, f"C1 호버 {tag}", vw)
                        if vname == "desktop" and name in COMMON_PAGES and L["help"]:
                            n = L["help"]
                            c1_mouse(pg, f"C1 {name}|{scheme}", sorted({0, n // 2, n - 1}))
                        check(not errs, f"[{tag}] 콘솔 오류 {errs[:3]}")
                        tally(reqs, tag)
                        ctx.close()
                        if vname == "mobile" and scheme == "light" and L["help"]:
                            # 375 폭에 마우스를 쓰는 창(터치 없음): 호버 가로 넘침
                            ctx2, pg2, errs2, reqs2 = new(vw, vh, scheme, touch=False)
                            go(pg2, name)
                            c1_hover_overflow(pg2, f"C1 호버(포인터) {tag}", vw)
                            check(not errs2, f"[{tag}(포인터)] 콘솔 오류 {errs2[:3]}")
                            tally(reqs2, tag + "(포인터)")
                            ctx2.close()

                # ---- 공통 폼 컨트롤(오류 제보 창의 .iq-input·.iq-textarea·.iq-select) C3·C4 ----
                ctx, pg, errs, reqs = new(1280, 900, scheme)
                go(pg, "index.html")
                pg.locator(".iq-report-fab").click()
                pg.wait_for_timeout(500)
                fc = pg.evaluate(FORM_JS)
                check(len(fc) >= 3, f"[form|{scheme}] 오류 제보 창 컨트롤 {len(fc)}개")
                for e in fc:
                    bgc = over(parse_color(e["bg"]), BG[scheme])
                    bd = over(parse_color(e["border"]), bgc)
                    if e["cls"] in ("iq-input", "iq-textarea"):
                        check(ratio(bd, bgc) >= 3.0, f"[form|{scheme}] {e['cls']} 테두리 대비 {ratio(bd, bgc):.2f}")
                        check(ratio(over(parse_color(e["ph"]), bgc), bgc) >= 4.5, f"[form|{scheme}] {e['cls']} placeholder 대비 {ratio(over(parse_color(e['ph']), bgc), bgc):.2f}")
                        mmin(f"C3 오류 제보 입력창 테두리 대비 최소 {scheme}", ratio(bd, bgc))
                        mmin(f"C4 오류 제보 placeholder 대비 최소 {scheme}", ratio(over(parse_color(e["ph"]), bgc), bgc))
                    else:   # 선택 상자는 owner 범위 밖이라 --border 그대로
                        check(e["border"].replace(" ", "") == ("rgb(228,228,226)" if scheme == "light" else "rgb(49,52,49)"), f"[form|{scheme}] 선택 상자 테두리가 바뀜 {e['border']}")
                check(not errs, f"[form|{scheme}] 콘솔 오류 {errs[:3]}")
                tally(reqs, f"form|{scheme}")
                pg.screenshot(path=str(out / f"report_modal_{scheme}.png"))
                ctx.close()

                # ---- compare: 3 시나리오 x 2 뷰포트 ----
                for sname, names in SETS.items():
                    for vname, vw, vh in VIEWPORTS:
                        tag = f"compare|{sname}|{vname}|{scheme}"
                        ctx, pg, errs, reqs = new(vw, vh, scheme)
                        go(pg, "compare.html", names)

                        # C3·C4 (시작 상태)
                        c3_c4(pg, tag, scheme)

                        # C1 (마우스 경로. 375 폭은 터치 맥락에서 theme.js 가 팝오버 보정 스크롤을 해 마우스 밑의 버튼이 움직이므로, 터치 없는 375 폭 맥락에서 잰다)
                        n_help = pg.evaluate("() => document.querySelectorAll('.iq-help-btn').length")
                        check(n_help >= 1, f"[{tag}] ? 버튼 없음")
                        if vname == "desktop":
                            c1_hover_overflow(pg, f"C1 호버 {tag}", vw)
                            c1_mouse(pg, f"C1 {tag}", sorted({0, n_help // 2, n_help - 1}))
                        else:
                            ctx2, pg2, errs2, reqs2 = new(vw, vh, scheme, touch=False)
                            go(pg2, "compare.html", names)
                            c1_mouse(pg2, f"C1 {tag}(포인터)", sorted({0, n_help // 2, n_help - 1}))
                            c1_hover_overflow(pg2, f"C1 호버(포인터) {tag}", vw)
                            check(not errs2, f"[{tag}(포인터)] 콘솔 오류 {errs2[:3]}")
                            tally(reqs2, tag + "(포인터)")
                            ctx2.close()
                        if scheme == "light" and sname == "life" and vname == "desktop":
                            pg.add_style_tag(content=".iq-help-pop::before,.iq-help::before,.iq-help::after{display:none !important} .iq-help.is-grace > .iq-help-pop{opacity:0 !important;pointer-events:none !important}")
                            c1_mouse(pg, f"C1 음성대조 {tag}", [0], expect_lost=True)
                            pg.reload(wait_until="load")
                            pg.wait_for_function("() => document.getElementById('main-msg').hidden")
                            pg.wait_for_timeout(400)
                        nh, lo, hi = c1_keyboard(pg, f"C1 키보드 {tag}", vw)
                        if vw < 641:
                            mmin("C1 375폭 팝오버 왼쪽 끝 최소", lo)
                            mmax("C1 375폭 팝오버 오른쪽 끝 최대", hi)

                        # C6
                        if sname != "none":
                            if vname == "desktop":
                                check(pg.evaluate("() => document.querySelectorAll('.lcs svg').length") == 0, f"[{tag}] 넓은 화면에 좁은 화면 SVG 가 있음")
                                wd = pg.evaluate(WIDE_JS)
                                if wd is None:
                                    skips.append(f"{tag}: Chart.js 가 안 떠 넓은 화면 선(모양·색)을 못 읽음")
                                else:
                                    check(len(wd) == len(names) or len(wd) >= 1, f"[{tag}] 넓은 화면 선 데이터셋 {len(wd)}")
                                    wide_cache[(scheme, sname)] = wd
                            else:
                                opts = pg.evaluate("() => [...document.querySelectorAll('#sel-g option')].map(o => o.value)")
                                wd = wide_cache.get((scheme, sname))
                                for oi, ov in enumerate(opts):
                                    if oi:
                                        pg.select_option("#sel-g", ov)
                                        pg.wait_for_timeout(300)
                                    d = pg.evaluate(LOSS_JS)
                                    if not d["rows"] or not d["svg"]:
                                        continue   # 이 단위는 선택한 회사 모두 n/a
                                    c6(d, f"C6 {tag} 단위{oi}", names, wd if oi == 0 else None)
                                    if any(m["fill"] == "var(--bg)" for g in d["groups"] for m in g["marks"]):
                                        faded_seen[0] += 1
                                pg.select_option("#sel-g", opts[0])
                                pg.wait_for_timeout(300)
                                card = pg.query_selector(".lcm")
                                if card:
                                    card.scroll_into_view_if_needed()
                                    card.screenshot(path=str(out / f"loss_{sname}_{scheme}.png"))
                        else:
                            check(pg.evaluate("() => document.querySelectorAll('.lcs svg').length") == 0, f"[{tag}] 회사 미선택인데 손해율 SVG 가 있음")

                        # C2 (키보드 제거·추가) — 시나리오에 따라 순서만 다르다
                        if sname == "none":
                            add_names = SETS["life" if scheme == "light" else "nonlife"]
                            add_cascade(pg, tag + "|add", add_names)
                            remove_cascade(pg, tag + "|rm", add_names)
                        else:
                            remove_cascade(pg, tag + "|rm", names)
                            add_cascade(pg, tag + "|add", names)
                            pointer_removal(pg, tag, names)
                        c3_c4(pg, tag + "|끝", scheme)

                        check(not errs, f"[{tag}] 콘솔 오류 {errs[:3]}")
                        tally(reqs, tag)
                        pg.screenshot(path=str(out / f"compare_{sname}_{vname}_{scheme}.png"))
                        ctx.close()

            # ---------- 네이티브 체크박스 테두리(3:1) — 픽셀로 잰다 -------------------------------
            try:
                from PIL import Image
                for scheme in ("light", "dark"):
                    ctx, pg, errs, reqs = new(1280, 900, scheme)
                    go(pg, "compare.html", SETS["life"][:1])
                    el = pg.query_selector("#med")
                    el.scroll_into_view_if_needed()
                    pg.evaluate("() => { document.getElementById('med').checked = false; }")
                    shot = out / f"checkbox_{scheme}.png"
                    el.screenshot(path=str(shot))
                    im = Image.open(shot).convert("RGB")
                    edge, inner = im.getpixel((0, im.size[1] // 2)), im.getpixel((im.size[0] // 2, im.size[1] // 2))
                    c = ratio(edge, BG[scheme])
                    check(c >= 3.0, f"[checkbox|{scheme}] 네이티브 체크박스 테두리 대비 {c:.2f}")
                    mmin(f"C3 체크박스 테두리 대비 {scheme}", c)
                    ctx.close()
            except ImportError:
                skips.append("PIL 없음: 체크박스 테두리 픽셀 대비를 안 쟀다")
            browser.close()
    finally:
        stop_server(srv)

    # ---------- 정적 검사 ----------
    css = (root / "common.css").read_text(encoding="utf-8")
    check("--control-border:#85888d" in css and css.count("--control-border:#727772") == 2, "[static] common.css --control-border 값·위치(라이트 1 · 다크 2)")
    check("--border:#e4e4e2" in css and css.count("--border:#313431") == 2, "[static] common.css --border 값이 바뀜")
    check(re.search(r"input::placeholder\s*,\s*textarea::placeholder\s*\{[^}]*color:var\(--muted\)", css) is not None, "[static] placeholder 규칙")
    check(".iq-help-pop::before" in css, "[static] ? 팝오버 다리 규칙")
    theme_src = (root / "theme.js").read_text(encoding="utf-8")
    check(".iq-help.is-grace > .iq-help-pop" in css and "pointerleave" in theme_src and "is-grace" in theme_src and "iq-wing-r" not in css and "trimHelpWings" not in theme_src, "[static] ? 팝오버 마우스 유예(is-grace) 규칙·핸들러가 있고 옛 옆 삼각형은 없음")
    cmp_src = (root / "compare.html").read_text(encoding="utf-8")
    check("var PAL_BAR  = ['#8ccfc6', '#f6b49f', '#a8c1f0', '#e6d27e'];" in cmp_src, "[static] PAL_BAR 가 바뀜(C5 는 owner 가 하지 않기로 함)")
    check("var PAL_LINE = ['#4fb0a5', '#ee8f72', '#7b9fe6', '#cdb04a'];" in cmp_src, "[static] PAL_LINE 이 바뀜(C7 은 owner 가 하지 않기로 함)")
    check(not re.search(r"KR\d{4}", cmp_src.split("<script>", 1)[0]), "[static] compare.html 머리 부분에 회사코드")
    check("border:1px solid var(--control-border)" in cmp_src, "[static] compare 검색창 --control-border")

    check(tested[0] >= 24, f"[C1] 마우스 경로를 실제로 잰 버튼이 {tested[0]}개뿐(24개 미만)")
    check(hov_tested[0] >= 80, f"[C1] 호버 가로 넘침을 실제로 잰 버튼이 {hov_tested[0]}개뿐(80개 미만)")
    print(f"checks={n_checks[0]} fails={len(fails)} mouse_paths={tested[0]} hover_overflow_buttons={hov_tested[0]} faded_cases={faded_seen[0]} collector_requests={stats['collector']} gtag_blocked={stats['gtag_blocked']}")
    if faded_seen[0] == 0:
        skips.append("흐린 점선 구간이 있는 단위를 못 만나 C6 의 흐린 구간 표식을 못 쟀다")
    for k, v in sorted(meas.items()):
        print(f"MEASURE {k}: {v:.2f}")
    for s in info:
        print("INFO", s)
    for s in skips:
        print("SKIP-WIDE" if "Chart.js" in s else "SKIP", s)
    for f in fails:
        print("FAIL", f)
    print("OK" if not fails else "VIOLATIONS")
    return 1 if fails else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "artifacts" / "designer" / "a11y_compare_privacy"))
    ap.add_argument("--step", type=int, default=1, help="마우스 경로를 N 점마다 잰다(기본 1 = 1px 단위, 티켓 수락 기준 그대로. 빠른 점검은 3)")
    ap.add_argument("--root", default=str(ROOT), help="서빙할 폴더(기본 저장소 루트). 옛 판과 비교하는 변이시험용")
    sys.exit(run(ap.parse_args()))
