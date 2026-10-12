#!/usr/bin/env python3
"""K-ICS.html Forward Outlook 노트 · 차트 · 도넛 툴팁 헤드리스 검사 (2026-10-12, designer; 검증 감사 티켓 20261012T2236Z).

**왜 있나.** `kics_forward_capital.json` 은 가용자본(기본자본) <= 0 인 해의 비율을 0.0 으로 자르고 `capacity_exhausted` /
`basic_capacity_exhausted` 를 true 로 둔다. 예전 화면은 자르지 않은 기준선에서 잘린 2030 값을 빼 예별 「+41.8%p」·롯데 「+5.4%p」
같은 거짓 개선을 인쇄했다. 이 스크립트는 실제 페이지를 47사 전부로 돌려 다음을 단정한다(JSON 은 읽기만 한다).

  1. 노트의 「2030 변화」 = 마지막 해 자본/SCR 비율 - 기준선 자본/SCR 비율(JSON 의 금액으로 직접 계산), 또는 그 해가 잘렸으면 「—」.
  2. 잘린 해는 차트 시리즈가 null(점 없음), 안 잘린 해는 JSON 값 그대로. 잘린 해가 하나라도 있으면 안내 한 줄이 있고 없으면 없다.
  3. 노트·y축 눈금 어디에도 ASCII 마이너스(숫자 앞 `-`)가 없다 — 음수는 △. 잘린 지표에 `+NN.N%p` 가 없다.
  4. 잘린 해의 툴팁에는 「자본잠식」, `0.00%` 는 없다.
  5. 375px 에서 도넛 툴팁 박스가 캔버스 안에 들어간다(오른쪽 잘림 0), 「보완자본형이면 X%」는 표시값과 다를 때만 있다.
  6. 콘솔 오류 0, 가로 넘침 0.

Playwright(msedge) 와 망(jsdelivr: chart.js)이 없으면 SKIP(exit 0) — 안 돌렸다 != 통과했다.
실행(저장소 루트): C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/check_kics_forward_note.py [--mobile] [--dark] [--company 예별]
종료코드: 0 = 통과 또는 SKIP · 1 = 위반.
"""
from __future__ import annotations

import argparse
import json
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
OUT = ROOT / "artifacts" / "designer" / "kics_forward_note"


def jl(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def fmt_tri(v, dp):
    from decimal import Decimal, ROUND_HALF_UP  # JS toFixed = 정확한 이진값 기준 반올림, 동률이면 큰 쪽(83.25 -> 83.3; 파이썬 f-string 은 83.2)
    t = str(Decimal(abs(v)).quantize(Decimal(1).scaleb(-dp), rounding=ROUND_HALF_UP))
    return ("△" if v < 0 and float(t) != 0 else "") + t + "%"


def expected(row):
    """JSON 의 금액(자본/SCR)에서 직접 계산한 기대값. 반환: dict."""
    pr = row["projections"]
    base = row.get("baseline") or row.get("baseline_2025_4Q") or {}
    ex_r = [p.get("capacity_exhausted") is True for p in pr]
    ex_b = [p.get("basic_capacity_exhausted") is True for p in pr]
    last = pr[-1]
    cap_base = base.get("capital_eok"); bas_base = base.get("basic_capital_eok"); scr_base = base.get("scr_post_eok")
    out = {"ex_r": ex_r, "ex_b": ex_b, "chg_r": None, "chg_b": None}
    if not ex_r[-1] and cap_base is not None and scr_base:
        out["chg_r"] = last["capital_eok"] / last["scr_eok"] * 100 - cap_base / scr_base * 100
    if not ex_b[-1] and bas_base is not None and scr_base:
        out["chg_b"] = last["basic_capital_eok"] / last["scr_eok"] * 100 - bas_base / scr_base * 100
    return out


PICK = """() => {
  const fc = Chart.getChart('forward-chart');
  const q = (id) => document.getElementById(id);
  return {
    note: q('forward-note').innerText, wrap: q('forward-chart-wrap').style.display, ph: q('forward-placeholder').innerText,
    clip: !!q('forward-clip-note'),
    ratio: fc ? fc.data.datasets[0].data : null, basic: fc ? fc.data.datasets[1]._originalBasic : null,
    ticks: fc ? [fc.scales.y.ticks.map(t => fc.scales.y.options.ticks.callback(t.value)), fc.scales.y1.ticks.map(t => fc.scales.y1.options.ticks.callback(t.value))] : null,
    scrollW: document.documentElement.scrollWidth, clientW: document.documentElement.clientWidth };
}"""

FW_TIPS = """() => {
  const fc = Chart.getChart('forward-chart'); if (!fc) return null;
  const out = [];
  const n = fc.data.labels.length;
  for (let i = 0; i < n; i++) {
    const act = [0, 1, 2].filter(d => fc.getDatasetMeta(d).data[i] && !fc.getDatasetMeta(d).data[i].skip && fc.data.datasets[d].data[i] != null).map(d => ({datasetIndex: d, index: i}));
    if (!act.length) { out.push(null); continue; }
    const px = fc.scales.x.getPixelForValue(i);
    fc.tooltip.setActiveElements(act, {x: px, y: 40}); fc.update('none');
    out.push((fc.tooltip.body || []).map(b => b.lines.concat(b.after || [])).flat());
  }
  fc.tooltip.setActiveElements([], {x: 0, y: 0}); fc.update('none');
  return out;
}"""

DONUT_GEOM = """(id) => { const c = Chart.getChart(id); if (!c) return null; const arc = c.getDatasetMeta(0).data[0];
  return {x: arc.x, y: arc.y, r: arc.outerRadius * 0.86, cw: c.width}; }"""
DONUT_READ = """(id) => { const t = Chart.getChart(id).tooltip; return {op: t.opacity, w: t.width, x: t.x, lines: (t.body || []).map(b => b.lines.concat(b.after || [])).flat()}; }"""


def donut_tooltips(pg):
    """실제 마우스 호버(프로그램으로 setActiveElements 하면 툴팁 폭이 계산되지 않는다). 링 위 여러 각도를 훑어 나온 박스를 모은다."""
    import math
    res = {}
    for cid in ("donut-tier1", "donut-tier2"):
        g = pg.evaluate(DONUT_GEOM, cid)
        if not g:
            res[cid] = None; continue
        pg.locator("#" + cid).scroll_into_view_if_needed(); pg.wait_for_timeout(200)
        box = pg.locator("#" + cid).bounding_box()
        recs = []
        for deg in (12, 90, 200, 300, 350):
            px = box["x"] + g["x"] + g["r"] * math.sin(math.radians(deg))
            py = box["y"] + g["y"] - g["r"] * math.cos(math.radians(deg))
            pg.mouse.move(px, py); pg.wait_for_timeout(260)
            rd = pg.evaluate(DONUT_READ, cid)
            if rd["op"] and rd["lines"]:
                rd["cw"] = g["cw"]; recs.append(rd)
        pg.mouse.move(2, 2); pg.wait_for_timeout(100)
        res[cid] = recs
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--company", default="", help="회사명 일부(여러 개는 쉼표). 비우면 전 회사")
    ap.add_argument("--mobile", action="store_true", help="375px 도 돌린다(도넛 툴팁 폭 검사는 모바일에서만 의미)")
    ap.add_argument("--dark", action="store_true")
    ap.add_argument("--page", default="K-ICS.html", help="검사할 HTML(회귀 확인용으로 옛 판을 넘길 때)")
    ap.add_argument("--shots", default="", help="이 회사(쉼표)는 전망·도넛 패널 스크린샷을 artifacts/designer/kics_forward_note 에 저장")
    a = ap.parse_args()
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:  # noqa: BLE001
        print("SKIP: playwright 없음", e); return 0
    fw = {r["insurer_name"]: r for r in jl("kics_forward_capital.json")}
    t1 = {r["company"]: r for r in jl("kics_tier1_utilization.json")["results"]}
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=str(ROOT),
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.3).close(); break
        except OSError:
            time.sleep(0.2)
    bad, checked, shots = [], 0, [x for x in a.shots.split(",") if x]
    want = [x for x in a.company.split(",") if x]
    views = [("desktop", 1280, 900, "light")] + ([("mobile", 375, 812, "light")] if a.mobile else []) + ([("dark", 1280, 900, "dark")] if a.dark else [])
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(channel="msedge", headless=True)
            for vn, w, h, scheme in views:
                ctx = br.new_context(viewport={"width": w, "height": h}, color_scheme=scheme)
                pg = ctx.new_page(); errs = []
                # 망 흔들림(외부 CDN·폰트·분석 스크립트의 ERR_CONNECTION_RESET)은 우리 코드 오류가 아니다 — 외부 호스트 요청 실패는 경고로만 센다.
                pg.on("console", lambda m, e=errs: e.append(m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
                pg.on("requestfailed", lambda r: (errs.append("로컬 요청 실패 " + r.url) if r.url.startswith("http://127.0.0.1") else print("  (경고) 외부 요청 실패", r.url[:80], r.failure)))
                pg.on("response", lambda r: errs.append(f"HTTP {r.status} {r.url}") if r.status >= 400 and r.url.startswith("http://127.0.0.1") else None)
                pg.on("pageerror", lambda x, e=errs: e.append(str(x)))
                pg.set_default_timeout(60000)
                pg.goto(f"http://127.0.0.1:{port}/{a.page}?iq_internal=1", wait_until="domcontentloaded")
                try:
                    pg.wait_for_function("() => window.Chart && document.getElementById('company').options.length > 5", timeout=60000, polling=300)
                except Exception:  # noqa: BLE001
                    print("SKIP: chart.js(망) 또는 회사 목록을 못 불러옴", errs[:2]); return 0
                pg.wait_for_timeout(1500)
                names = pg.evaluate("() => Array.from(document.getElementById('company').options).map(o => o.value).filter(Boolean)")
                for name in names:
                    if want and not any(x in name for x in want):
                        continue
                    pg.evaluate("(n) => { const s = document.getElementById('company'); s.value = n; s.dispatchEvent(new Event('change')); }", name)
                    pg.wait_for_timeout(250)
                    row = fw.get(name) or next((r for k, r in fw.items() if k and (k in name or name in k)), None)
                    info = pg.evaluate(PICK)
                    prob = []
                    note = info["note"]
                    if row is None or row.get("status") != "ok":
                        if info["wrap"] != "none":
                            prob.append("전망 대상 아님인데 차트가 보임")
                    else:
                        ex = expected(row)
                        pr = row["projections"]
                        if info["wrap"] != "block": prob.append(f"차트 영역 숨김 {info['wrap']}")
                        # 2. 시리즈
                        for key, flags, field in (("ratio", ex["ex_r"], "ratio_pct"), ("basic", ex["ex_b"], "basic_ratio_pct")):
                            got = info[key]
                            for i, p in enumerate(pr):
                                want_v = None if flags[i] else p[field]
                                if (got[i] is None) != (want_v is None) or (want_v is not None and abs(got[i] - want_v) > 1e-9):
                                    prob.append(f"{key}[{p['year']}]={got[i]} != {want_v}")
                        any_ex = any(ex["ex_r"]) or any(ex["ex_b"])
                        if info["clip"] != any_ex: prob.append(f"안내 줄 clip={info['clip']} 기대 {any_ex}")
                        # 1. 노트의 2030 변화
                        m = re.search(r"2030 변화: 지급여력 (\S+), 기본자본 (\S+)", note)
                        if not m:
                            prob.append("노트에서 2030 변화를 못 찾음: " + note[:80])
                        else:
                            for lab, got, want_chg in (("지급여력", m.group(1), ex["chg_r"]), ("기본자본", m.group(2), ex["chg_b"])):
                                if want_chg is None:
                                    if got.rstrip(" |") != "—": prob.append(f"{lab} 변화 {got!r} != '—'")
                                else:
                                    mm = re.fullmatch(r"([+△])(\d+\.\d)%p", got.rstrip(" |"))
                                    if not mm: prob.append(f"{lab} 변화 형식 {got!r}"); continue
                                    val = float(mm.group(2)) * (-1 if mm.group(1) == "△" else 1)
                                    # JSON 금액은 소수 1자리로 반올림돼 있어(소형사는 비율에 0.5%p 까지 영향) 허용오차를 금액 반올림만큼 넓힌다
                                    tol = 0.06 + 100 * 0.1 / pr[-1]["scr_eok"]
                                    if abs(val - want_chg) > tol: prob.append(f"{lab} 변화 {val} != 자본/SCR 기준 {want_chg:.2f}")
                        # 기준선 표기
                        base = row.get("baseline") or row.get("baseline_2025_4Q") or {}
                        for lab, v in (("지급여력", base.get("ratio_post_pct")), ("기본자본", base.get("basic_ratio_post_pct"))):
                            if v is not None and f"{lab} {fmt_tri(v, 1)}" not in note: prob.append(f"기준선 {lab} {fmt_tri(v, 1)} 표기 없음")
                        # 4. 툴팁
                        tips = pg.evaluate(FW_TIPS)
                        for i, p in enumerate(pr):
                            lines = tips[i] if tips else None
                            if lines is None:
                                prob.append(f"{p['year']} 툴팁 없음"); continue
                            joined = " | ".join(lines)
                            if ex["ex_r"][i] and "지급여력비율: 자본잠식" not in joined: prob.append(f"{p['year']} 툴팁 지급여력 자본잠식 없음: {joined}")
                            if ex["ex_b"][i] and "기본자본비율: 자본잠식" not in joined: prob.append(f"{p['year']} 툴팁 기본자본 자본잠식 없음: {joined}")
                            if (ex["ex_r"][i] or ex["ex_b"][i]) and "0.00%" in joined: prob.append(f"{p['year']} 툴팁 0.00% 인쇄: {joined}")
                            if re.search(r"(?<![\w.])-\d", joined): prob.append(f"{p['year']} 툴팁 ASCII 마이너스: {joined}")
                    # 3. 부호
                    if re.search(r"(?<![\w.])-\d", note): prob.append("노트에 ASCII 마이너스: " + note)
                    if info["ticks"] and any(re.match(r"-\d", t) for ax in info["ticks"] for t in ax): prob.append(f"y축 눈금 ASCII 마이너스 {info['ticks']}")
                    if row is not None and row.get("status") == "ok":
                        ex = expected(row)
                        for lab, flags in (("지급여력", ex["ex_r"]), ("기본자본", ex["ex_b"])):
                            if flags[-1] and re.search(rf"{lab} \+\d", note.split("2030 변화:")[1] if "2030 변화:" in note else ""): prob.append(f"잘린 {lab}에 + 변화 인쇄")
                    # 5. 도넛 툴팁 폭
                    if w < 480:
                        dt = donut_tooltips(pg)
                        for cid, arr in dt.items():
                            if not arr and arr is not None: prob.append(f"{cid} 호버 툴팁이 안 뜸")
                            for rec in arr or []:
                                if rec["w"] is None or rec["w"] != rec["w"]: prob.append(f"{cid} 툴팁 폭 NaN"); continue
                                if rec["x"] + rec["w"] > rec["cw"] + 0.5 or rec["x"] < -0.5:
                                    prob.append(f"{cid} 툴팁 x={rec['x']:.0f} w={rec['w']:.0f} > 캔버스 {rec['cw']:.0f}: {rec['lines']}")
                    # 보완자본형이면 X% 는 표시값과 다를 때만
                    r1 = t1.get(name)
                    if r1 and r1.get("tier1_pct_if_unconfirmed_tier2") is not None:
                        same = f"{r1['tier1_pct_if_unconfirmed_tier2']:.1f}" == f"{r1['utilization_pct']:.1f}"
                        has = "보완자본형이면" in pg.evaluate("() => document.getElementById('help-capsec-t1').innerText")
                        if has == same: prob.append(f"보완자본형이면 줄 has={has} same={same}")
                    # 6. 오류·넘침
                    if info["scrollW"] > info["clientW"] + 1: prob.append(f"가로 넘침 {info['scrollW']}>{info['clientW']}")
                    if errs: prob.append(f"콘솔 오류 {errs[:2]}"); errs.clear()
                    checked += 1
                    if any(x in name for x in shots):
                        OUT.mkdir(parents=True, exist_ok=True)
                        for sec, nm in (("donut-section-panel", "donut"), ("sec-forward", "fw")):
                            pg.locator("#" + sec).scroll_into_view_if_needed(); pg.wait_for_timeout(400)
                            pg.locator("#" + sec).screenshot(path=str(OUT / f"{name}_{vn}_{nm}.png"))
                        pg.locator("#forward-chart").scroll_into_view_if_needed()
                        box = pg.locator("#forward-chart").bounding_box()
                        pg.mouse.move(box["x"] + box["width"] * 0.9, box["y"] + box["height"] * 0.5); pg.wait_for_timeout(600)
                        pg.screenshot(path=str(OUT / f"{name}_{vn}_fwtip.png"))
                        print(f"[{vn}] {name}: {note.replace(chr(10), ' / ')}")
                    if prob:
                        bad.append((vn, name, prob))
                ctx.close()
            br.close()
    finally:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(srv.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"checked {checked} (view x company), violations {len(bad)}")
    for b in bad:
        print("  ", b[0], b[1])
        for p in b[2]:
            print("      -", p)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
