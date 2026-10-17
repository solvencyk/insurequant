#!/usr/bin/env python3
"""손해율 가정 구분(Non-Par / Direct-Par / Indirect-Par) 선택기 점검 (2026-10-18, designer).

compare.html 손해율 카드와 IFRS17.html 8절이 그린 값을 마스터(data/loss_ratio/master_loss_ratio.json)의 금액으로 직접 재계산한 기대값과 대조한다.
  구분 손해율 = Σ예상보험금 / Σ위험보험료 x 100 (그 구분의 모든 포트폴리오 잎 행, 두 금액이 모두 있는 칸만, 위험보험료 합 0 이하면 없음).
  - compare: 회사 조합 x 구분 4종 x (1280 / 375 / 다크). 넓은 화면은 Chart.js 데이터셋, 좁은 화면은 SVG 경로를 눈금으로 되돌려 읽는다.
    현재가치 숫자(범례 / 표), 업계 중앙값, 값 없는 회사의 n/a 사유 줄, 콘솔 오류, 가로 넘침.
  - 합계를 고른 화면은 git HEAD 의 옛 HTML(같은 JSON 위에서 돌린 것)과 데이터셋이 글자 그대로 같아야 한다.
  - IFRS17: 회사 x 구분 선택지 x (1280 / 375 / 다크). 선택지 = 합계 + 값이 있는 구분(둘 미만이면 숨김), 현 시점 선과 직전 연도 점선.
Playwright·망이 없으면 SKIP(exit 0) — SKIP 은 통과가 아니라 안 돌렸다는 뜻이다.
실행: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/check_loss_group.py [--shots DIR]
"""
from __future__ import annotations

import json
import re
import socket
import subprocess
import sys
import time
import statistics
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parents[1]
SLOTS = [f"{n}년" for n in range(1, 11)] + ["11~15년", "16~20년", "21~25년", "26~30년", "30년 이후", "1~10년"]
NSTD = 15
GROUPS = ["Non-Par", "Direct-Par", "Indirect-Par"]
OPTS_ALL = ["합계"] + GROUPS


def jl(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def git_show(path):
    return subprocess.run(["git", "show", f"HEAD:{path}"], cwd=str(ROOT), capture_output=True, check=True).stdout.decode("utf-8")


# ------------------------------------------------------------------ 마스터에서 직접 재계산한 기대값
def build_expected():
    rows = jl("data/loss_ratio/master_loss_ratio.json")
    cmp_acc = defaultdict(lambda: [0.0, 0.0])      # (g, code, q, slot)  — 세그먼트를 가로질러
    seg_acc = defaultdict(lambda: [0.0, 0.0, 0])   # (g, code, q, seg, slot)
    tot = {}                                       # (code, q, seg, slot) 합계 행 손해율
    segs = defaultdict(set)
    for r in rows:
        g, p, code, q, slot = r["구분"], r["포트폴리오"], r["원보험사코드"], r["공시분기"], r["경과차년"]
        seg = r.get("세그먼트") or ""
        segs[(code, q)].add(seg)
        if g == "합계" and p == "합계":
            if r["손해율"] is not None:
                tot[(code, q, seg, slot)] = float(r["손해율"])
            continue
        if g not in GROUPS or p in ("합계", ""):
            continue
        rp, ec = r["위험보험료"], r["예상보험금"]
        if rp is None or ec is None:
            continue
        for acc, key in ((cmp_acc, (g, code, q, slot)), (seg_acc, (g, code, q, seg, slot))):
            a = acc[key]
            a[0] += rp
            a[1] += ec
            if len(a) > 2:
                a[2] += 1
    cur = {}
    for (g, code, q, slot), (rp, ec) in cmp_acc.items():
        if rp > 0:
            cur[(g, code, q, slot)] = round(ec / rp * 100.0, 1)
    sg = {}
    for (g, code, q, seg, slot), (rp, ec, n) in seg_acc.items():
        if rp > 0:
            sg[(g, code, q, seg, slot)] = round(ec / rp * 100, 2)
    return cur, sg, tot, segs


def exp_row(cur, g, code, asof_q, qs):
    """compare 의 행 조회: asof 이하에서 가장 늦은 분기의 16칸 (없으면 None)."""
    for q in sorted([x for x in qs if x <= asof_q], reverse=True):
        row = [cur.get((g, code, q, s)) for s in SLOTS]
        if any(v is not None for v in row):
            return q, row
    return None, None


def plot_y(row):
    """lossChart: 1~10년 한 구간 공시(row[15])는 앞 10칸을 그 값으로."""
    pts = list(row[:NSTD])
    if row[NSTD] is not None:
        for i in range(10):
            pts[i] = row[NSTD]
    return pts


def close(a, b, tol=0.06):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= tol


# ------------------------------------------------------------------ 브라우저 읽기
CMP_READ = """() => {
  const anc = document.getElementById('c-loss_pv'); const card = anc ? anc.parentElement : null;
  if (!card) return {card: false};
  const cv = card.querySelector('canvas'); const ch = cv && window.Chart ? Chart.getChart(cv) : null;
  const svg = card.querySelector('.lcs svg');
  const o = {card: true,
    opts: [...card.querySelectorAll('.gsel .seg-btn')].map(b => b.dataset.g + (b.classList.contains('active') ? '*' : '') + (b.getAttribute('aria-pressed') === 'true' ? '+' : '')),
    na: [...card.querySelectorAll('.na-list li')].map(li => li.innerText.trim()),
    help: (card.querySelector('.iq-help-pop') || {}).textContent || '',
    visibleText: (() => { const c = card.cloneNode(true); c.querySelectorAll('.iq-help-pop').forEach(e => e.remove()); return c.textContent; })(),
    aria: cv ? cv.getAttribute('aria-label') : (svg ? svg.getAttribute('aria-label') : null),
    sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth,
    url: location.search,
    ds: ch ? ch.data.datasets.map(d => ({label: d.label, y: d.data.map(p => p.y)})) : null,
    cardW: card.getBoundingClientRect().width,
    gselW: (card.querySelector('.gsel') || {scrollWidth: 0}).scrollWidth, gselCW: (card.querySelector('.gsel') || {clientWidth: 0}).clientWidth};
  if (svg) {
    o.paths = [...svg.querySelectorAll('path')].map(p => ({d: p.getAttribute('d'), stroke: p.getAttribute('stroke'), dash: p.getAttribute('stroke-dasharray')}));
    o.texts = [...svg.querySelectorAll('text')].map(t => ({t: t.textContent, y: parseFloat(t.getAttribute('y'))}));
    o.table = [...card.querySelectorAll('.lcm tbody tr')].map(tr => [...tr.cells].map(c => c.innerText.trim()));
  }
  return o;
}"""


def svg_series(o):
    """모바일 SVG: 눈금 글자(y = Y(v) - 3)로 y 좌표를 값으로 되돌려, 경로마다 점 값 목록을 만든다."""
    cal = []
    for t in o["texts"]:
        m = re.fullmatch(r"(△?)(\d+)%", t["t"])
        if m:
            cal.append((t["y"] + 3, -float(m.group(2)) if m.group(1) else float(m.group(2))))
    if len(cal) < 2:
        return None
    (y1, v1), (y2, v2) = cal[0], cal[-1]
    k = (v2 - v1) / (y2 - y1)
    out = []
    for p in o["paths"]:
        pts = [float(m.group(1)) for m in re.finditer(r"[ML][\d.\-]+ ([\d.\-]+)", p["d"])]
        out.append({"stroke": p["stroke"], "dash": p["dash"], "v": [v1 + (y - y1) * k for y in pts]})
    return out


def nonnull(xs):
    return [x for x in xs if x is not None]


def main():
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:  # noqa: BLE001
        print("SKIP: playwright 없음", e)
        return 0
    shots = None
    if "--shots" in sys.argv:
        shots = Path(sys.argv[sys.argv.index("--shots") + 1]); shots.mkdir(parents=True, exist_ok=True)
    cur, sg, tot, segs = build_expected()
    panel = jl("data/compare/panel_compare.json")
    co = {c["short"]: c for c in panel["companies"]}
    qs_by_g = defaultdict(set)
    for (g, code, q, slot) in cur:
        qs_by_g[(g, code)].add(q)
    quarters = sorted({q for (_, _, q, _) in cur})
    pvm = next(m for m in panel["metrics"] if m["id"] == "loss_pv")
    # 현재가치 기대값: 마스터 합산 (구분, 회사, 분기)
    pv_acc = defaultdict(lambda: [0.0, 0.0])
    for r in jl("data/loss_ratio/master_loss_ratio.json"):
        if r["경과차년"] == "현재가치" and r["구분"] in GROUPS and r["포트폴리오"] not in ("합계", "") and r["위험보험료"] is not None and r["예상보험금"] is not None:
            a = pv_acc[(r["구분"], r["원보험사코드"], r["공시분기"])]
            a[0] += r["위험보험료"]; a[1] += r["예상보험금"]
    pv = {k: round(v[1] / v[0] * 100, 1) for k, v in pv_acc.items() if v[0] > 0}
    # 지표 최신 공시 분기 = 39사 합계 현재가치가 있는 가장 늦은 분기
    qlist = panel["meta"]["quarters"]
    last_i = max(i for c, a in pvm["v"].items() for i, x in enumerate(a) if x is not None)
    asof_q = qlist[last_i]

    def exp_pv(g, code):
        for q in sorted([q for (gg, cc, q) in pv if gg == g and cc == code and q <= asof_q], reverse=True):
            return q, pv[(g, code, q)]
        return None, None

    # 점검 회사 조합 (이름은 화면 표시명)
    sets = [
        ("스위스리",),
        ("한화생명",),                                   # 구분 3종
        ("삼성화재",),                                   # 구분 2종
        ("카카오페이손보",),                             # 구분 1종(선택기 없음)
        ("삼성생명", "교보라이프플래닛", "ABL생명"),     # 구분 커버리지가 다른 조합
        ("한화생명", "삼성생명", "교보생명", "신한라이프", "동양생명"),   # 5곳 > 4 상한 아님(최대 4) -> 4곳으로 잘림 확인
    ]
    views = [("1280", 1280, 900, "light"), ("375", 375, 812, "light"), ("1280-dark", 1280, 900, "dark")]
    head_cmp = git_show("compare.html")
    head_ifrs = git_show("IFRS17.html")
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    bad, n = [], 0
    base = f"http://127.0.0.1:{port}"
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(channel="msedge", headless=True)

            def newpage(w, h, scheme, errs):
                ctx = br.new_context(viewport={"width": w, "height": h}, color_scheme=scheme)
                ctx.add_init_script("try{localStorage.setItem('iq_notice_seen','2026-3Q')}catch(e){}")
                pg = ctx.new_page()
                pg.on("pageerror", lambda x: errs.append(str(x)))
                pg.on("console", lambda m: errs.append(m.text) if m.type == "error" and "Failed to load resource" not in m.text and "/g/collect" not in m.text else None)   # 분석 수집 CSP 메시지는 이 점검 대상이 아니다
                return ctx, pg

            # ---------------------------------------------------------- compare.html
            for vn, w, h, scheme in views:
                for names in sets:
                    errs = []
                    ctx, pg = newpage(w, h, scheme, errs)
                    names = names[:4]
                    url = f"{base}/compare.html?iq_internal=1&c=" + ",".join(names)
                    loaded = False
                    for attempt in range(3):
                        pg.goto(url, wait_until="commit", timeout=60000)
                        try:
                            pg.wait_for_function("() => window.Chart && document.getElementById('c-loss_pv')", timeout=40000)
                            loaded = True
                            break
                        except Exception:  # noqa: BLE001
                            pass
                    if not loaded:
                        print("SKIP: compare 로드 실패", vn, names, errs[:3]); ctx.close(); continue
                    pg.wait_for_timeout(600)
                    codes = [co[nm]["code"] for nm in names]
                    typ = co[names[0]]["type"]
                    base_o = pg.evaluate(CMP_READ)
                    avail = [g for g in GROUPS if any(exp_row(cur, g, c, asof_q, qs_by_g[(g, c)])[0] for c in codes)]
                    want_opts = (["합계"] + avail) if len(avail) >= 2 else []
                    got_opts = [x.rstrip("*+") for x in base_o["opts"]]
                    prob = []
                    if got_opts != want_opts:
                        prob.append(f"선택지 {got_opts} != {want_opts}")
                    if base_o["opts"] and not base_o["opts"][0].endswith("*+"):
                        prob.append(f"기본 선택이 합계가 아님 {base_o['opts']}")
                    for opt in (want_opts or ["합계"]):
                        if want_opts:
                            pg.locator(f'.gsel .seg-btn[data-g="{opt}"]').click()
                            pg.wait_for_timeout(500)
                        o = pg.evaluate(CMP_READ)
                        n += 1
                        p2 = []
                        if want_opts and not o["opts"][want_opts.index(opt)].endswith("*+"):
                            p2.append(f"선택 표시 {o['opts']}")
                        if (opt == "합계" and "g=" in o["url"]) or (opt != "합계" and f"g={opt}" not in o["url"]):
                            p2.append(f"주소 g= {o['url']}")
                        if o["sw"] > o["cw"] + 1:
                            p2.append(f"가로 넘침 {o['sw']}>{o['cw']}")
                        if o["gselW"] > o["gselCW"] + 1:
                            p2.append(f"선택기 줄 넘침 {o['gselW']}>{o['gselCW']}")
                        if want_opts and ("세 유형의 비중" not in o["help"]):
                            p2.append("? 팝오버에 구성 설명 없음")
                        if "세 유형의 비중" in o["visibleText"]:
                            p2.append("구성 설명 문장이 화면에 노출")
                        if re.search(r"KR\d{4}", o["visibleText"] + o["aria"] + o["url"]):
                            p2.append("회사코드 노출")
                        # --- 기대값
                        g = opt
                        exp_lines, exp_na = [], []
                        for nm, code in zip(names, codes):
                            if g == "합계":
                                exp_lines.append((nm, code, "TOTAL"))
                                continue
                            qrow, row = exp_row(cur, g, code, asof_q, qs_by_g[(g, code)])
                            if row is None:
                                exp_na.append(nm)
                            else:
                                exp_lines.append((nm, code, plot_y(row), exp_pv(g, code), qrow))
                        if g != "합계":
                            wide = o["ds"] is not None
                            lines_exp = [e for e in exp_lines]
                            if wide:
                                got = [d for d in o["ds"] if not d["label"].startswith(typ + " 업계 중앙값")]
                                med = [d for d in o["ds"] if d["label"].startswith(typ + " 업계 중앙값")]
                                if len(got) != len(lines_exp):
                                    p2.append(f"선 {len(got)}개 != 기대 {len(lines_exp)}개")
                                for d, e in zip(got, lines_exp):
                                    if not d["label"].startswith(e[0]):
                                        p2.append(f"선 이름 {d['label']} != {e[0]}"); continue
                                    if not all(close(a, b) for a, b in zip(d["y"], e[2])):
                                        p2.append(f"{e[0]} 값 {d['y']} != {e[2]}")
                                    pvq, pvv = e[3]
                                    want_lab = e[0] + (f" · 현재가치 {pvv:.1f}%" if pvv is not None else "")
                                    if not d["label"].startswith(want_lab):
                                        p2.append(f"{e[0]} 현재가치 라벨 {d['label']!r} != {want_lab!r}")
                            else:
                                ser = svg_series(o) or []
                                lines_s = [x for x in ser if x["stroke"] != "var(--muted)"]
                                if len(lines_s) != min(len(lines_exp), 4):
                                    p2.append(f"SVG 선 {len(lines_s)}개 != 기대 {min(len(lines_exp), 4)}개")
                                for sv, e in zip(lines_s, lines_exp):
                                    want = nonnull(e[2])
                                    gotv = sv["v"]
                                    if len(gotv) != len(want) or not all(abs(a - b) <= 0.35 for a, b in zip(gotv, want)):
                                        p2.append(f"{e[0]} SVG 값 {[round(x, 1) for x in gotv]} != {want}")
                                rows_t = {r[0]: r[1] for r in o.get("table", [])}
                                for e in lines_exp:
                                    pvv = e[3][1]
                                    cell = next((v for k, v in rows_t.items() if k.startswith(e[0])), None)
                                    want = f"{pvv:.1f}%" if pvv is not None else "—"
                                    if cell != want:
                                        p2.append(f"{e[0]} 표 현재가치 {cell!r} != {want!r}")
                            for nm in exp_na:
                                if not any(nm in x and "이 구분 값 없음" in x for x in o["na"]):
                                    p2.append(f"{nm} n/a 사유 줄 없음 {o['na']}")
                            if len(o["na"]) != len(exp_na) + (0):
                                p2.append(f"n/a 줄 수 {o['na']} != {exp_na}")
                            # 중앙값 (재보 제외)
                            if typ != "재보·보증":
                                pool = [c for c in panel["companies"] if c["type"] == typ]
                                # 분기별 중앙값: asof 이하에서 값 있는 가장 늦은 분기
                                best = None
                                for q in sorted({q for (gg, cc, q, sl) in cur if gg == g and q <= asof_q}, reverse=True):
                                    xs = []
                                    for k in range(NSTD):
                                        v = [cur.get((g, c["code"], q, SLOTS[k])) for c in pool]
                                        v = [x for x in v if x is not None]
                                        xs.append(sorted(v) if len(v) >= 5 else None)
                                    if any(x is not None for x in xs):
                                        best = (q, [round(statistics.median(x), 1) if x else None for x in xs]); break
                                if wide:
                                    if best and not med:
                                        p2.append("중앙값 선 없음")
                                    elif not best and med:
                                        p2.append("기대에 없는 중앙값 선")
                                    elif best and not all(close(a, b) for a, b in zip(med[0]["y"], best[1])):
                                        p2.append(f"중앙값 {med[0]['y']} != {best[1]}")
                                    elif best and not med[0]["label"].endswith(" · " + g):
                                        p2.append(f"중앙값 이름 {med[0]['label']}")
                        else:
                            # 합계: HEAD 의 옛 화면과 글자 그대로 같아야 한다
                            ctx2, pg2 = newpage(w, h, scheme, [])
                            pg2.route("**/compare.html*", lambda route: route.fulfill(body=head_cmp, content_type="text/html; charset=utf-8"))
                            ok2 = False
                            for _try in range(3):
                                pg2.goto(f"{base}/compare.html?iq_internal=1&c=" + ",".join(names), wait_until="commit", timeout=60000)
                                try:
                                    pg2.wait_for_function("() => window.Chart && document.getElementById('c-loss_pv')", timeout=40000)
                                    ok2 = True
                                    break
                                except Exception:  # noqa: BLE001
                                    pass
                            if not ok2:
                                p2.append(f"HEAD 화면 로드 실패 {vn} {names} url={pg2.url}")
                                ctx2.close()
                                if p2:
                                    prob.append((opt, p2))
                                continue
                            pg2.wait_for_timeout(600)
                            h_o = pg2.evaluate(CMP_READ)
                            ctx2.close()
                            if h_o["ds"] != o["ds"]:
                                p2.append(f"합계 데이터셋이 HEAD 와 다름 new={o['ds']} head={h_o['ds']}")
                            if o.get("paths") != h_o.get("paths") or o.get("table") != h_o.get("table"):
                                p2.append("합계 SVG/표가 HEAD 와 다름")
                            if o["na"] != h_o["na"]:
                                p2.append(f"합계 n/a 줄이 HEAD 와 다름 {o['na']} vs {h_o['na']}")
                            if o["aria"] != h_o["aria"]:
                                p2.append(f"합계 aria 가 HEAD 와 다름 {o['aria']!r} vs {h_o['aria']!r}")
                        if errs:
                            p2.append(f"콘솔 {errs[:2]}")
                            errs.clear()
                        if shots and names in (("스위스리",), ("삼성생명", "교보라이프플래닛", "ABL생명")):
                            pg.locator("#c-loss_pv").locator("xpath=..").screenshot(path=str(shots / f"cmp_{vn}_{'+'.join(names)}_{opt}.png"))
                        if p2:
                            prob.append((opt, p2))
                    ctx.close()
                    if prob:
                        bad.append(("compare", vn, names, prob))

            # ---------------------------------------------------------- compare: 구판 JSON(g 없음) · 주소 g= · 키보드
            head_json = git_show("data/compare/panel_compare.json")
            for vn, w, h, scheme in views[:2]:
                errs = []
                ctx, pg = newpage(w, h, scheme, errs)
                pg.route("**/data/compare/panel_compare.json", lambda route: route.fulfill(body=head_json, content_type="application/json; charset=utf-8"))
                pg.goto(f"{base}/compare.html?iq_internal=1&g=Direct-Par&c=한화생명,삼성생명", wait_until="commit", timeout=60000)
                pg.wait_for_function("() => window.Chart && document.getElementById('c-loss_pv')", timeout=60000)
                pg.wait_for_timeout(600)
                o = pg.evaluate(CMP_READ)
                n += 1
                p2 = []
                if o["opts"]:
                    p2.append(f"구판 JSON 인데 선택기가 있음 {o['opts']}")
                if "g=" in o["url"]:
                    p2.append(f"구판 JSON 인데 주소에 g= {o['url']}")
                if not (o["ds"] or o.get("paths")):
                    p2.append("구판 JSON 에서 곡선이 안 그려짐")
                if errs:
                    p2.append(f"콘솔 {errs[:2]}")
                ctx.close()
                if p2:
                    bad.append(("compare-oldjson", vn, "한화생명,삼성생명", [("-", p2)]))
            for vn, w, h, scheme in views[:2]:
                for url_q, want in (("g=Direct-Par&c=한화생명", "Direct-Par"), ("g=Direct-Par&c=삼성화재", "합계"), ("g=엉터리&c=한화생명", "합계"),
                                    ("g=Non-Par&c=스위스리", "Non-Par")):
                    errs = []
                    ctx, pg = newpage(w, h, scheme, errs)
                    for attempt in range(2):   # CDN 지연으로 가끔 늦게 뜨므로 한 번 더
                        pg.goto(f"{base}/compare.html?iq_internal=1&{url_q}", wait_until="commit", timeout=60000)
                        try:
                            pg.wait_for_function("() => window.Chart && document.getElementById('c-loss_pv')", timeout=45000)
                            break
                        except Exception:  # noqa: BLE001
                            if attempt == 1:
                                raise
                    pg.wait_for_timeout(600)
                    o = pg.evaluate(CMP_READ)
                    n += 1
                    sel_g = next((x.rstrip("*+") for x in o["opts"] if x.endswith("*+")), "합계")
                    p2 = []
                    if sel_g != want and not (want == "합계" and not o["opts"]):
                        p2.append(f"주소 {url_q} 의 선택 {sel_g} != {want}")
                    if want == "합계" and "g=" in o["url"]:
                        p2.append(f"되돌렸는데 주소에 g= {o['url']}")
                    if errs:
                        p2.append(f"콘솔 {errs[:2]}")
                    if vn == "1280" and url_q.startswith("g=Non-Par"):
                        # 키보드: 포커스 -> Enter -> 다시 그려도 포커스·선택 유지
                        pg.locator('.gsel .seg-btn[data-g="합계"]').focus()
                        pg.keyboard.press("Tab")
                        pg.keyboard.press("Enter")
                        pg.wait_for_timeout(300)
                        k = pg.evaluate("() => { const a = document.activeElement; return {g: a && a.dataset ? a.dataset.g : null, on: a && a.classList.contains('active'), live: document.getElementById('live').textContent}; }")
                        if k["g"] != "Non-Par" or not k["on"]:
                            p2.append(f"키보드 Enter 뒤 포커스/선택 {k}")
                    ctx.close()
                    if p2:
                        bad.append(("compare-url", vn, url_q, [("-", p2)]))

            # ---------------------------------------------------------- IFRS17.html
            ifrs_cos = ["스위스리", "한화생명", "삼성화재", "카카오페이손보", "코리안리", "뮌헨", "제네럴", "퍼시픽"]
            for vn, w, h, scheme in views:
                for nm in ifrs_cos:
                    errs = []
                    ctx, pg = newpage(w, h, scheme, errs)
                    loaded = False
                    for attempt in range(2):
                        pg.goto(f"{base}/IFRS17.html?iq_internal=1", wait_until="commit", timeout=60000)
                        try:
                            pg.wait_for_function("() => window.Chart && document.getElementById('company').options.length > 5", timeout=45000)
                            loaded = True
                            break
                        except Exception:  # noqa: BLE001
                            pass
                    if not loaded:
                        print("SKIP: IFRS17 로드 실패", vn, nm, errs[:3], pg.evaluate("() => [!!window.Chart, document.readyState, document.getElementById('company') ? document.getElementById('company').options.length : -1]"))
                        ctx.close()
                        continue
                    pg.wait_for_timeout(800)
                    sel = pg.evaluate("""(nm) => { const s = document.getElementById('company'); const o = [...s.options].find(x => x.textContent.includes(nm));
                        if (!o) return null; s.value = o.value; s.dispatchEvent(new Event('change')); return o.value; }""", nm)
                    if sel is None:
                        bad.append(("ifrs17", vn, nm, [("-", ["회사 옵션 없음"])])); ctx.close(); continue
                    code = sel
                    pg.wait_for_function("() => document.getElementById('canvasLr') && window.Chart && Chart.getChart('canvasLr')", timeout=30000)
                    pg.wait_for_timeout(500)
                    READ = """() => { const ch = Chart.getChart('canvasLr');
                      return { q: document.getElementById('lrQ').value, seg: document.getElementById('lrSeg').value,
                        grpHidden: document.getElementById('lrGrpWrap').hidden, grpOpts: [...document.querySelectorAll('#lrGrp option')].map(o => o.value), grp: document.getElementById('lrGrp').value,
                        ds: ch.data.datasets.map(d => ({label: d.label, y: d.data.map(p => p.y)})), title: ch.options.plugins.title.text,
                        aria: document.getElementById('canvasLr').getAttribute('aria-label'), pv: document.getElementById('lrPv').innerText,
                        cols: [...document.querySelectorAll('#lrTable thead th')].map(t => t.textContent).slice(1),
                        open: document.querySelectorAll('#lrTable [aria-expanded=true]').length, trs: document.querySelectorAll('#lrTable tbody tr:not([hidden])').length,
                        help: document.getElementById('help-lr').textContent, vis: document.getElementById('sec-lr').innerText,
                        sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }; }"""
                    st = pg.evaluate(READ)
                    q0, seg0 = st["q"], st["seg"]
                    prob = []
                    # 기대 선택지
                    def groups_of(q_, seg_):
                        out = []
                        for g in GROUPS:
                            if any(k[0] == g and k[1] == code and k[2] == q_ and k[3] == seg_ for k in sg):
                                out.append(g)
                        return out
                    has_tot = any(k[0] == code and k[1] == q0 and k[2] == seg0 for k in tot)
                    ga = groups_of(q0, seg0)
                    want_opts = (["합계"] + ga if len(ga) >= 2 else ["합계"]) if has_tot else (ga if ga else ["합계"])
                    if st["grpOpts"] != want_opts or st["grpHidden"] != (len(want_opts) < 2):
                        prob.append(("-", [f"선택지 {st['grpOpts']} hidden={st['grpHidden']} != {want_opts}"]))
                    # 합계 행이 없는 사업구분(재보사 생명·장기손해)은 빈 차트를 피해 첫 구분이 기본값
                    want_def = ga[0] if (not has_tot and ga) else "합계"
                    if st["grp"] != want_def:
                        prob.append(("-", [f"기본값 {st['grp']} != {want_def}"]))
                    for opt in st["grpOpts"]:
                        if not st["grpHidden"]:
                            pg.evaluate("""(v) => { const s = document.getElementById('lrGrp'); s.value = v; s.dispatchEvent(new Event('change')); }""", opt)
                            pg.wait_for_timeout(300)
                        o = pg.evaluate(READ)
                        n += 1
                        p2 = []
                        cols = [c for c in o["cols"] if c != "현재가치"]
                        # 현 시점
                        if opt == "합계":
                            want = [tot.get((code, q0, seg0, c)) for c in cols]
                            want = [None if v is None else round(v, 2) for v in want]
                        else:
                            want = [sg.get((opt, code, q0, seg0, c)) for c in cols]
                        d_cur = [d for d in o["ds"] if d["label"].startswith(q0 + " 공시")]
                        if not d_cur:
                            if any(v is not None for v in want):
                                p2.append("현 시점 선 없음")
                        else:
                            got = nonnull(d_cur[0]["y"])
                            if len(got) != len(nonnull(want)) or not all(close(a, b, 0.011) for a, b in zip(got, nonnull(want))):
                                p2.append(f"현 시점 값 {got} != {nonnull(want)}")
                            if not d_cur[0]["label"].endswith(opt):
                                p2.append(f"범례 {d_cur[0]['label']}")
                        # 직전 연도 점선
                        y, qn = q0.split(".")
                        pq = f"{int(y) - 1}.{qn}"
                        d_prev = [d for d in o["ds"] if d["label"].startswith(pq + " 공시")]
                        if opt == "합계":
                            pw = {k[3]: v for k, v in tot.items() if k[0] == code and k[1] == pq and k[2] == seg0 and k[3] != "현재가치"}
                        else:
                            pw = {k[4]: v for k, v in sg.items() if k[0] == opt and k[1] == code and k[2] == pq and k[3] == seg0 and k[4] != "현재가치"}
                        if d_prev:
                            gotp = nonnull(d_prev[0]["y"]); wantp = nonnull([round(v, 2) for v in pw.values()])
                            if sorted(gotp) != sorted(wantp):
                                p2.append(f"직전 점선 값 {gotp} != {wantp}")
                        elif pw and any(v is not None for k, v in pw.items() if k != "현재가치"):
                            p2.append("직전 점선이 있어야 하는데 없음")
                        # 현재가치 숫자
                        pvv = tot.get((code, q0, seg0, "현재가치")) if opt == "합계" else sg.get((opt, code, q0, seg0, "현재가치"))
                        pvs = "-" if pvv is None else f"{pvv:.1f}"
                        if f"현재가치 기준 {'' if opt == '합계' else opt + ' '}{pvs}%".replace("-%", "-%") not in o["pv"].replace("\n", " ") and not (pvv is None and "현재가치 기준" in o["pv"]):
                            p2.append(f"현재가치 줄 {o['pv']!r} (기대 {pvs})")
                        if opt != "합계" and opt not in o["title"]:
                            p2.append(f"제목에 구분 없음 {o['title']}")
                        if opt != "합계" and opt not in o["aria"]:
                            p2.append(f"aria 에 구분 없음")
                        if "세 유형의 비중" not in o["help"] or "세 유형의 비중" in o["vis"].replace(o["help"], ""):
                            p2.append("구성 설명이 ? 팝오버 안에만 있어야 함")
                        if o["sw"] > o["cw"] + 1:
                            p2.append(f"가로 넘침 {o['sw']}>{o['cw']}")
                        if re.search(r"KR\d{4}", o["vis"] + o["aria"]):
                            p2.append("회사코드 노출")
                        if errs:
                            p2.append(f"콘솔 {errs[:2]}")
                            errs.clear()
                        if opt == "합계":
                            ctx2, pg2 = newpage(w, h, scheme, [])
                            pg2.route("**/IFRS17.html*", lambda route: route.fulfill(body=head_ifrs, content_type="text/html; charset=utf-8"))
                            pg2.goto(f"{base}/IFRS17.html?iq_internal=1", wait_until="commit", timeout=60000)
                            pg2.wait_for_function("() => window.Chart && document.getElementById('company').options.length > 5", timeout=60000)
                            pg2.wait_for_timeout(800)
                            pg2.evaluate("""(v) => { const s = document.getElementById('company'); s.value = v; s.dispatchEvent(new Event('change')); }""", code)
                            pg2.wait_for_function("() => document.getElementById('canvasLr') && Chart.getChart('canvasLr')", timeout=30000)
                            pg2.wait_for_timeout(500)
                            hd = pg2.evaluate("""() => { const ch = Chart.getChart('canvasLr'); return {ds: ch.data.datasets.map(d => ({label: d.label, y: d.data.map(p => p.y)})), title: ch.options.plugins.title.text, aria: document.getElementById('canvasLr').getAttribute('aria-label'), pv: document.getElementById('lrPv').innerText}; }""")
                            ctx2.close()
                            if hd["ds"] != o["ds"]:
                                p2.append(f"합계 데이터셋이 HEAD 와 다름 {o['ds']} vs {hd['ds']}")
                            for k in ("title", "aria", "pv"):
                                if hd[k] != o[k]:
                                    p2.append(f"합계 {k} 가 HEAD 와 다름 {o[k]!r} vs {hd[k]!r}")
                        if shots and nm in ("스위스리", "한화생명"):
                            pg.locator("#sec-lr").screenshot(path=str(shots / f"ifrs_{vn}_{nm}_{opt}.png"))
                        if p2:
                            prob.append((opt, p2))
                    # 펼친 행 유지: 모두 펼치기 -> 구분 바꾸기 -> 그대로
                    if not st["grpHidden"] and len(st["grpOpts"]) >= 2:
                        pg.evaluate("""() => document.querySelector('#lrBar [data-act=open]').click()""")
                        a = pg.evaluate(READ)
                        pg.evaluate("""(v) => { const s = document.getElementById('lrGrp'); s.value = v; s.dispatchEvent(new Event('change')); }""", st["grpOpts"][1])
                        pg.wait_for_timeout(300)
                        b = pg.evaluate(READ)
                        if a["open"] != b["open"] or a["trs"] != b["trs"]:
                            prob.append(("펼침", [f"구분을 바꾸자 펼친 행이 변함 {a['open']}/{a['trs']} -> {b['open']}/{b['trs']}"]))
                    ctx.close()
                    if prob:
                        bad.append(("ifrs17", vn, nm, prob))
            br.close()
    finally:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(srv.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"checked {n} (view x company x 구분), violations {len(bad)}")
    for page, vn, who, prob in bad:
        print("  ", page, vn, who)
        for opt, ps in prob:
            for p in ps:
                print(f"      - [{opt}] {p}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
