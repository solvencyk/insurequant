#!/usr/bin/env python3
"""손해율 가정 비교 단위(구분 x 상품구분 x 포트폴리오 한 줄) 선택기 점검 (2026-10-19 신설, designer).

compare.html 손해율 카드(넓은 화면 Chart.js · 좁은 화면 SVG · 현재가치 표 · 업계 중앙값 · 주소 g=)와 IFRS17.html 8절(select#lrGrp, panel_loss_ratio.json)이
그린 값을 마스터(data/loss_ratio/master_loss_ratio.json)의 금액으로 직접 재계산한 기대값과 대조한다. 정본 docs/loss_ratio_comparable_unit_20261019.md.
  단위 손해율 = Σ예상보험금 / Σ위험보험료 x 100 (그 단위의 잎 행, 두 금액이 모두 있는 칸만, 위험보험료 합 0 이하면 없음). 원수사 단위 = 구분 x 상품구분 x 포트폴리오,
  재보사 단위 = 세그먼트 묶음 x Non-Par x 포트폴리오. 위험보험료는 마스터 값 그대로 억원(백만원 표기 공시사도 ×1.0).
  A. 데이터: panel_compare.json 의 loss_curve.u·up·med_u 와 loss_pv.vu·medu 를 마스터에서 전수 재계산한 값과 비교(전 단위 x 전 회사 x 전 분기).
  B. compare: 전 단위 x 업권 전 회사(4곳씩 묶음) 최신 결산의 선·현재가치 숫자·업계 중앙값·흐림 칸·n/a 사유를 1280 / 375 / 다크에서 화면과 대조.
     처음 화면(업권별 기본 단위), 주소 g= 여러 경우, 빈 칸 정책(합계·다른 구분으로 대체하지 않음), 변액사망 문구, 재보 단위, 선택기 접근성(라벨·optgroup·키보드), 구판 JSON 폴백, 콘솔 오류.
  C. IFRS17 8절: 전 회사 x 전 공시시점 x 단위 선택지의 값·흐림 칸·현재가치 숫자·기본 선택·끈끈한 선택, 구판 패널 폴백, 375 / 다크.
  D. 흐린 칸 선 색의 대비(배경 대비)를 실측해 인쇄한다.
  모든 브라우저 요청은 가로채 collector·분석 호출이 0건임을 단정한다.
Playwright·망이 없으면 SKIP(exit 0) — SKIP 은 통과가 아니라 안 돌렸다는 뜻이다.
실행: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/check_loss_unit.py [--only data|compare|ifrs17|regress] [--shots DIR]
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
import json
import math
import re
import socket
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parents[1]
SLOTS = [f"{n}년" for n in range(1, 11)] + ["11~15년", "16~20년", "21~25년", "26~30년", "30년 이후", "1~10년"]
NSTD = 15
PV = "현재가치"
FADE_EOK = 100            # 화면 상수 FADE_BELOW_EOK 와 같아야 한다
FADE_MIN_CR = 2.2         # 화면 상수 FADE_MIN_CR 와 같아야 한다(흐린 선 색의 배경 대비 하한)
GROUPS = ["Non-Par", "Direct-Par", "Indirect-Par"]
RE_PAIRS = {("생명", "건강"), ("생명", "사망"), ("장기손해", "질병"), ("장기손해", "상해")}
BG = {"light": "#ffffff", "dark": "#151615"}
VIEWS = [("1280", 1280, 900, "light"), ("375", 375, 812, "light"), ("1280-dark", 1280, 900, "dark")]

BAD: list = []
STATS: dict = defaultdict(float)
SEEN_ALT: dict = defaultdict(set)     # (화면, 단위) -> 변액사망 문구를 본 alt_co 회사 코드
SEEN_PLAIN: dict = defaultdict(set)   # (화면, 단위) -> 단순 사유를 본 alt_co 밖 회사 코드


def round_hu(x, dec=1):
    """패널 빌더와 같은 반올림: 정확한 이진 값 기준 half-up(파이썬 round() 는 x.x5 에서 짝수 쪽이라 0.1 어긋난다)."""
    return float(Decimal(x).quantize(Decimal(1).scaleb(-dec), rounding=ROUND_HALF_UP))


def median_hu(xs, dec=1):
    """패널 빌더와 같은 중앙값 반올림: 회사별로 이미 반올림한 값을 소수(Decimal)로 읽어 중앙값을 내고 half-up(89.3 과 89.4 의 평균 89.35 는 89.4)."""
    d = sorted(Decimal(repr(float(x))) for x in xs)
    n = len(d)
    m = d[n // 2] if n % 2 else (d[n // 2 - 1] + d[n // 2]) / 2
    return float(m.quantize(Decimal(1).scaleb(-dec), rounding=ROUND_HALF_UP))


def bad(where, msg):
    BAD.append(f"{where}: {msg}")


def jl(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


# ------------------------------------------------------------------ 마스터에서 직접 재계산
def re_group(seg, pf):
    if seg.startswith("생명"):
        return "생명"
    if seg.startswith("장기손해"):
        return "장기손해"
    if seg == "":
        return "생명" if pf in ("건강", "사망") else ("장기손해" if pf in ("질병", "상해") else None)
    return None


def unit_of_row(sector, r):
    """마스터 잎 행 -> 단위 식별 튜플. 원수사 (업권, 구분, 상품구분, 포트폴리오), 재보사 (재보, 세그먼트 묶음, 구분, 포트폴리오)."""
    g, p, f, seg = r["구분"], r["상품구분"] or "", r["포트폴리오"], r.get("세그먼트") or ""
    if sector != "재보":
        return (sector, g, p, f)
    sg = re_group(seg, f)
    if g != "Non-Par" or p not in ("", "무배당") or sg is None or (sg, f) not in RE_PAIRS:
        return None
    return (sector, sg, g, f)


def unit_key_tuple(u):
    if u["sector"] == "재보":
        return ("재보", u["seg"], u["gubun"], u["portfolio"])
    return (u["sector"], u["gubun"], u["product"], u["portfolio"])


class Expect:
    def __init__(self):
        self.panel = jl("data/compare/panel_compare.json")
        self.C = self.panel["loss_curve"]
        self.co = {c["code"]: c for c in self.panel["companies"]}
        self.short = {c["short"]: c["code"] for c in self.panel["companies"]}
        self.sector = {c: ("재보" if d["type"] == "재보·보증" else d["type"]) for c, d in self.co.items()}
        self.units = self.C["units"]
        self.by_key = {u["key"]: u for u in self.units}
        self.tuple_to_key = {unit_key_tuple(u): u["key"] for u in self.units}
        self.qlist = self.panel["meta"]["quarters"]
        pvm = next(m for m in self.panel["metrics"] if m["id"] == "loss_pv")
        self.pvm = pvm
        last_i = max(i for a in pvm["v"].values() for i, x in enumerate(a) if x is not None)
        self.asof_q = self.qlist[last_i]
        self.asof_i = last_i
        rows = jl("data/loss_ratio/master_loss_ratio.json")
        # acc[(key, code, q, slot)] = [Σ위험보험료, Σ예상보험금]  (두 금액이 모두 있는 잎 행)
        self.acc = defaultdict(lambda: [0.0, 0.0])
        self.tot_rp = defaultdict(float)     # (code, q, seg, slot) 합계 행 위험보험료 (항등식 검산)
        self.leaf_rp = defaultdict(float)    # (code, q, seg, slot) 잎 행 위험보험료 합
        self.units_seen = defaultdict(set)
        for r in rows:
            code, q, slot = r["원보험사코드"], r["공시분기"], r["경과차년"]
            if code not in self.sector:
                continue
            seg = r.get("세그먼트") or ""
            if r["구분"] == "합계" and r["포트폴리오"] == "합계":
                if r["위험보험료"] is not None:
                    self.tot_rp[(code, q, seg, slot)] += r["위험보험료"]
                continue
            if r["구분"] not in GROUPS or r["포트폴리오"] in ("합계", ""):
                continue
            if r["위험보험료"] is not None and slot in SLOTS:
                self.leaf_rp[(code, q, seg, slot)] += r["위험보험료"]
            u = unit_of_row(self.sector[code], r)
            key = self.tuple_to_key.get(u) if u else None
            if key is None:
                continue
            rp, ec = r["위험보험료"], r["예상보험금"]
            if rp is None or ec is None:
                continue
            a = self.acc[(key, code, q, slot)]
            a[0] += rp
            a[1] += ec

    def row(self, key, code, q):
        """(손해율 16칸, 위험보험료 16칸) 또는 None."""
        v, p, any_ = [], [], False
        for s in SLOTS:
            a = self.acc.get((key, code, q, s))
            if a and a[0] > 0:
                v.append(round_hu(a[1] / a[0] * 100.0))
                x = round(a[0], 2)
                p.append(int(x) if x == int(x) else x)
                any_ = True
            else:
                v.append(None)
                p.append(None)
        return (v, p) if any_ else None

    def pv(self, key, code, q):
        a = self.acc.get((key, code, q, PV))
        return round_hu(a[1] / a[0] * 100.0) if a and a[0] > 0 else None

    def latest(self, key, code):
        """화면이 그리는 행: asof 이하에서 가장 늦은 분기(없으면 None) -> (q, 손해율, 위험보험료)."""
        for q in sorted([q for q in self.qlist if q <= self.asof_q], reverse=True):
            r = self.row(key, code, q)
            if r:
                return q, r[0], r[1]
        return None

    def pool(self, sec):
        if sec == "재보":
            return [c for c, d in self.co.items() if d["type"] == "재보·보증" and d["sector"] == "재보험"]
        return [c for c, d in self.co.items() if d["type"] == sec]

    def median_row(self, key, q):
        sec = self.by_key[key]["sector"]
        out = []
        for k in range(NSTD):
            xs = []
            for c in self.pool(sec):
                r = self.row(key, c, q)
                if r and r[0][k] is not None:
                    xs.append(r[0][k])
            out.append(median_hu(xs) if len(xs) >= 5 else None)
        return out

    def median_latest(self, key):
        for q in sorted([q for q in self.qlist if q <= self.asof_q], reverse=True):
            m = self.median_row(key, q)
            if any(x is not None for x in m):
                return q, m
        return None

    def pv_median_latest(self, key):
        sec = self.by_key[key]["sector"]
        for q in sorted([q for q in self.qlist if q <= self.asof_q], reverse=True):
            xs = [self.pv(key, c, q) for c in self.pool(sec)]
            xs = [x for x in xs if x is not None]
            if len(xs) >= 5:
                return q, median_hu(xs)
        return None

    def pv_latest(self, key, code):
        for q in sorted([q for q in self.qlist if q <= self.asof_q], reverse=True):
            v = self.pv(key, code, q)
            if v is not None:
                return q, v
        return None

    def sector_companies(self, sec):
        return [c for c in self.co if self.sector[c] == sec]

    def default_unit(self, code, asof_i=None):
        sec = self.sector[code]
        d = self.C["default_unit"].get(sec)
        if d:
            return d
        for u in self.units:
            if u["sector"] == sec and self.latest(u["key"], code):
                return u["key"]
        for u in self.units:
            if u["sector"] == sec:
                return u["key"]
        return None


def plot_y(row, co_row=None):
    """lossChart: 1~10년 한 구간 공시(row[15])는 앞 10칸을 그 값으로."""
    pts = list(row[:NSTD])
    if row[NSTD] is not None:
        for i in range(10):
            pts[i] = row[NSTD]
    return pts


def plot_fd(row, up):
    """흐림 칸: 점마다 (그 칸이 쓰는 위험보험료 < FADE_EOK) 이고 점 값이 있을 때."""
    pts = plot_y(row)
    out = []
    for i in range(NSTD):
        ri = NSTD if (row[NSTD] is not None and i < 10) else i
        rv = up[ri]
        out.append(bool(rv is not None and rv < FADE_EOK and pts[i] is not None))
    return out


def close(a, b, tol=0.06):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= tol


def contrast(h1, h2):
    def lum(h):
        h = h.lstrip("#")
        c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        c = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    a, b = lum(h1), lum(h2)
    if a < b:
        a, b = b, a
    return (a + 0.05) / (b + 0.05)


def rgb_hex(s):
    m = re.match(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", s)
    if m:
        return "#%02x%02x%02x" % tuple(int(x) for x in m.groups())
    return s


# ------------------------------------------------------------------ A. 데이터 전수 재계산
def check_data(E):
    n = 0
    C = E.C
    pvm = E.pvm
    for u in E.units:
        k = u["key"]
        cos = E.sector_companies(u["sector"])
        for code in cos:
            got = C["u"][k].get(code, {})
            gup = C["up"][k].get(code, {})
            for q in E.qlist:
                exp = E.row(k, code, q)
                g, gp = got.get(q), gup.get(q)
                n += 1
                if exp is None:
                    if g is not None:
                        bad("data", f"{k} {E.co[code]['short']} {q}: 기대에 없는 행")
                    continue
                if g is None:
                    bad("data", f"{k} {E.co[code]['short']} {q}: 행 없음")
                    continue
                if not all(close(a, b, 0.051) for a, b in zip(g, exp[0])):
                    bad("data", f"{k} {E.co[code]['short']} {q}: 손해율 {g} != {exp[0]}")
                if not all(close(a, b, 0.0051) for a, b in zip(gp, exp[1])):
                    bad("data", f"{k} {E.co[code]['short']} {q}: 위험보험료 {gp} != {exp[1]}")
            for q in got:
                if q not in E.qlist:
                    bad("data", f"{k} {E.co[code]['short']}: 알 수 없는 분기 {q}")
            # 현재가치
            arr = pvm["vu"][k].get(code)
            for i, q in enumerate(E.qlist):
                e = E.pv(k, code, q)
                gv = arr[i] if arr else None
                n += 1
                if not close(gv, e, 0.051):
                    bad("data", f"{k} {E.co[code]['short']} {q}: 현재가치 {gv} != {e}")
        # 단위 목록의 회사 수·업권 밖 회사가 없는지
        have = {c for c in C["u"][k]}
        if not have <= set(cos):
            bad("data", f"{k}: 업권 밖 회사 {have - set(cos)}")
        exp_n = len([c for c in cos if E.latest(k, c)])
        if exp_n < 1:
            bad("data", f"{k}: 공시 회사 0")
    # 중앙값
    for sec, d in C["med_u"].items():
        for k, byq in d.items():
            for q, row in byq.items():
                n += 1
                e = E.median_row(k, q)
                if not all(close(a, b, 0.051) for a, b in zip(row, e)):
                    bad("data", f"중앙값 {k} {q}: {row} != {e}")
    for u in E.units:
        k = u["key"]
        has_any = any(any(x is not None for x in E.median_row(k, q)) for q in E.qlist)
        if has_any != (k in C["med_u"].get(u["sector"], {})):
            bad("data", f"중앙값 존재 여부 {k}: 기대 {has_any}")
    # 단위 배수 항등식: 잎 위험보험료 합 ≈ 합계 행 위험보험료 (백만원 표기 공시사 포함, 100배 어긋남을 잡는다)
    cnt = defaultdict(int)
    worst = 0.0
    for (code, q, seg, slot), tv in E.tot_rp.items():
        if slot != "1년" or tv <= 0:
            continue
        lv = E.leaf_rp.get((code, q, seg, slot))
        if not lv:
            continue
        ratio = lv / tv
        worst = max(worst, abs(ratio - 1))
        cnt["ok" if 0.9 <= ratio <= 1.1 else "off"] += 1
        if ratio < 0.5 or ratio > 2:
            bad("data", f"단위 배수 항등식 {E.co[code]['short']} {q} {seg!r}: 잎 합/합계 행 = {ratio:.3f}")
    print(f"[data] 단위 x 회사 x 분기 {n}칸 대조, 항등식(잎 합 / 합계 행, 1년 칸) {dict(cnt)} 최대 편차 {worst:.3f}")
    # 흐린 기준 칸 수
    nf = nt = 0
    for k, byc in C["up"].items():
        for c, byq in byc.items():
            for q, arr in byq.items():
                for x in arr[:NSTD]:
                    if x is not None:
                        nt += 1
                        nf += x < FADE_EOK
    print(f"[data] up 값이 있는 칸 {nt}, {FADE_EOK}억원 미만 {nf}")
    if C["unit_rule"].get("fade_below_eok") != FADE_EOK:
        bad("data", f"unit_rule.fade_below_eok {C['unit_rule'].get('fade_below_eok')} != 화면 상수 {FADE_EOK}")


# ------------------------------------------------------------------ 브라우저 도구
CMP_READ = """() => {
  const anc = document.getElementById('c-loss_pv'); const card = anc ? anc.parentElement : null;
  if (!card) return {card: false};
  const cv = card.querySelector('canvas'); const ch = cv && window.Chart ? Chart.getChart(cv) : null;
  const svg = card.querySelector('.lcs svg');
  const sel = card.querySelector('#sel-g');
  const bgc = getComputedStyle(document.documentElement).getPropertyValue('--bg').trim();
  const o = {card: true, bg: bgc,
    sel: sel ? {value: sel.value, labelFor: [...sel.labels].map(l => l.textContent.trim()), groups: [...sel.querySelectorAll('optgroup')].map(g => ({label: g.label, opts: [...g.querySelectorAll('option')].map(x => ({v: x.value, t: x.textContent, on: x.selected}))})),
      flat: [...sel.querySelectorAll(':scope > option')].map(x => x.value), w: sel.getBoundingClientRect().width, cardW: card.getBoundingClientRect().width} : null,
    na: [...card.querySelectorAll('.na-list li')].map(li => li.innerText.trim()),
    help: (card.querySelector('.iq-help-pop') || {}).textContent || '',
    visibleText: (() => { const c = card.cloneNode(true); c.querySelectorAll('.iq-help-pop').forEach(e => e.remove()); return c.textContent; })(),
    defText: (card.querySelector('.def') || {}).textContent || '',
    aria: cv ? cv.getAttribute('aria-label') : (svg ? svg.getAttribute('aria-label') : null),
    sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth, url: location.search,
    empty: (card.querySelector('.empty') || {}).textContent || null,
    attrs: [...card.querySelectorAll('[title],[aria-label],option,optgroup')].map(e => (e.getAttribute('title') || '') + '|' + (e.getAttribute('aria-label') || '') + '|' + (e.getAttribute('label') || '') + '|' + (e.tagName === 'OPTION' ? e.textContent : '')).join('~'),
    ds: ch ? ch.data.datasets.map(d => {
      const fdIdx = d.fd ? d.fd.map((f, i) => f ? i : -1).filter(i => i >= 0) : [];
      const r = {label: d.label, y: d.data.map(p => p.y), fd: d.fd || null, rp: d.rp || null, base: d.borderColor, dash: d.borderDash || []};
      if (fdIdx.length && typeof d.pointBackgroundColor === 'function') {
        r.pbg = d.data.map((p, i) => d.pointBackgroundColor({dataIndex: i}));
        r.pbc = d.data.map((p, i) => d.pointBorderColor({dataIndex: i}));
        r.segDash = d.data.slice(0, -1).map((p, i) => d.segment.borderDash({p0DataIndex: i, p1DataIndex: i + 1}));
        r.segCol = d.data.slice(0, -1).map((p, i) => d.segment.borderColor({p0DataIndex: i, p1DataIndex: i + 1}));
      }
      return r; }) : null};
  if (svg) {
    o.vb = (svg.getAttribute('viewBox') || '').split(' ').map(Number);
    o.paths = [...svg.querySelectorAll('path')].map(p => ({d: p.getAttribute('d'), stroke: p.getAttribute('stroke'), dash: p.getAttribute('stroke-dasharray')}));
    o.texts = [...svg.querySelectorAll('text')].map(t => ({t: t.textContent, y: parseFloat(t.getAttribute('y'))}));
    o.table = [...card.querySelectorAll('.lcm tbody tr')].map(tr => [...tr.cells].map(c => c.innerText.trim()));
  }
  return o;
}"""

BLOCK_HOSTS = ("script.google.com", "script.googleusercontent.com", "google-analytics.com", "googletagmanager.com", "analytics.google.com")


class Net:
    """가로챈 요청 기록: 수집기(script.google*)로 가려던 요청은 0건이어야 하고, 분석 요청은 전부 막는다."""
    collector = []
    analytics = []


def route_block(route):
    u = route.request.url
    if any(h in u for h in BLOCK_HOSTS):
        (Net.collector if "script.google" in u else Net.analytics).append(u)
        return route.abort()
    return route.continue_()


def decode_svg(o):
    """모바일 SVG: 눈금 글자로 y 를 값으로, x 를 열 번호로 되돌려 경로마다 구간 목록 [(i0, v0, i1, v1, dash)]을 만든다(중앙값 경로 제외)."""
    cal = []
    for t in o["texts"]:
        m = re.fullmatch(r"(△?)(\d+)%", t["t"])
        if m:
            cal.append((t["y"] + 3, -float(m.group(2)) if m.group(1) else float(m.group(2))))
    if len(cal) < 2:
        return None
    (y1, v1), (y2, v2) = cal[0], cal[-1]
    k = (v2 - v1) / (y2 - y1)
    W = o["vb"][2]
    pw = W - 12

    def X(x):
        return 4 + pw * x / 33.0
    xs = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 13, 18, 23, 28, 33]
    px = [X(x) for x in xs]

    def idx(x):
        return min(range(NSTD), key=lambda i: abs(px[i] - x))
    segs = []
    for p in o["paths"]:
        if p["stroke"] == "var(--muted)":
            continue
        toks = re.findall(r"([ML])([\d.\-]+) ([\d.\-]+)", p["d"])
        prev = None
        for c, x, y in toks:
            pt = (idx(float(x)), v1 + (float(y) - y1) * k)
            if c == "L" and prev is not None:
                segs.append((prev[0], prev[1], pt[0], pt[1], bool(p["dash"]), p["stroke"]))
            prev = pt
    return segs


def new_ctx(br, w, h, scheme):
    ctx = br.new_context(viewport={"width": w, "height": h}, color_scheme=scheme)
    ctx.add_init_script("try{localStorage.setItem('iq_notice_seen','2026-3Q')}catch(e){}")
    ctx.route("**/*", route_block)
    return ctx


def attach_errs(pg, errs):
    pg.on("pageerror", lambda x: errs.append(str(x)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)


def open_cmp(pg, base, query, tries=3):
    for _ in range(tries):
        pg.goto(f"{base}/compare.html?iq_internal=1&{query}", wait_until="commit", timeout=60000)
        try:
            pg.wait_for_function("() => window.Chart && document.getElementById('c-loss_pv')", timeout=40000)
            pg.wait_for_timeout(500)
            return True
        except Exception:  # noqa: BLE001
            pass
    return False


def go(pg, query):
    """같은 페이지 안에서 주소만 바꿔 다시 그린다(popstate)."""
    pg.evaluate("(q) => { history.pushState(null, '', location.pathname + '?iq_internal=1&' + q); window.dispatchEvent(new PopStateEvent('popstate')); }", query)
    pg.wait_for_timeout(120)


def url_g(search):
    from urllib.parse import parse_qs
    v = parse_qs(search.lstrip("?")).get("g")
    return v[0] if v else None


# ------------------------------------------------------------------ B. compare
def verify_cmp_state(E, o, names, key, vn, scheme, wide, tag, fade_seen):
    """한 화면 상태(회사 묶음 x 단위)를 마스터 기대값과 대조한다."""
    where = f"compare {vn} {key} {names}"
    u = E.by_key[key]
    codes = [E.short[nm] for nm in names]
    if not o.get("card"):
        bad(where, "손해율 카드 없음")
        return
    if o["sel"] is None:
        bad(where, "선택기 없음")
        return
    if o["sel"]["value"] != key:
        bad(where, f"선택기 값 {o['sel']['value']} != {key}")
    if o["sw"] > o["cw"] + 1:
        bad(where, f"가로 넘침 {o['sw']}>{o['cw']}")
    if re.search(r"KR\d{4}", o["visibleText"] + (o["aria"] or "") + o["url"] + o["attrs"]):
        bad(where, "회사코드 노출")
    if not (f"{u['label']} 단위의" in o["defText"]):
        bad(where, f"정의 줄이 단위를 말하지 않음 {o['defText']!r}")
    if "100억원" in o["visibleText"] or "구분은 공시 각주" in o["visibleText"]:
        bad(where, "설명 문장이 화면에 노출")
    if "100억원" not in o["help"] or "구분은 공시 각주" not in o["help"]:
        bad(where, "? 팝오버에 단위 설명·100억원 규칙 없음")
    if re.search(r"(?<![A-Za-z0-9가-힣])-\d", o["visibleText"]):
        bad(where, "음수가 하이픈 표기")
    exp_lines, exp_na = [], []
    for nm, code in zip(names, codes):
        lat = E.latest(key, code) if E.sector[code] == u["sector"] else None
        if lat is None:
            exp_na.append(nm)
        else:
            exp_lines.append((nm, code, lat))
    if wide:
        ds = o["ds"] or []
        med = [d for d in ds if "업계 중앙값" in d["label"]]
        got = [d for d in ds if "업계 중앙값" not in d["label"]]
        if len(got) != len(exp_lines):
            bad(where, f"선 {len(got)}개 != 기대 {len(exp_lines)}개 {[d['label'] for d in got]}")
        for d, (nm, code, (q, row, up)) in zip(got, exp_lines):
            if not d["label"].startswith(nm):
                bad(where, f"선 이름 {d['label']} != {nm}")
                continue
            if not all(close(a, b) for a, b in zip(d["y"], plot_y(row))):
                bad(where, f"{nm} 값 {d['y']} != {plot_y(row)}")
            pvq = E.pv_latest(key, code)
            want_lab = nm + (f" · 현재가치 {pvq[1]:.1f}%" if pvq else "")
            if not d["label"].startswith(want_lab):
                bad(where, f"{nm} 현재가치 라벨 {d['label']!r} != {want_lab!r}")
            efd = plot_fd(row, up)
            if d["fd"] != efd:
                bad(where, f"{nm} 흐림 칸 {d['fd']} != {efd}")
            elif any(efd):
                fade_seen["wide"] += 1
                bgc = BG[scheme]
                for i in range(NSTD):
                    if efd[i]:
                        if d["pbg"][i].lower() != bgc:
                            bad(where, f"{nm} 흐린 칸 {i} 표식이 속 빈 원이 아님 {d['pbg'][i]}")
                    elif d["pbg"][i] != d["base"]:
                        bad(where, f"{nm} 선명한 칸 {i} 표식이 속이 참 {d['pbg'][i]}")
                for i in range(NSTD - 1):
                    f2 = efd[i] or efd[i + 1]
                    if f2 and d["segDash"][i] != [2, 4]:
                        bad(where, f"{nm} 흐린 구간 {i} 점선 아님 {d['segDash'][i]}")
                    if (not f2) and d["segDash"][i] not in (None, [], d["dash"]):
                        bad(where, f"{nm} 선명한 구간 {i} 점선 {d['segDash'][i]}")
                    if f2:
                        fc = rgb_hex(d["segCol"][i])
                        cr = contrast(fc, bgc)
                        STATS[f"faded_cr_{scheme}_min"] = min(STATS.get(f"faded_cr_{scheme}_min") or 99, cr)
                        bcr = contrast(rgb_hex(d["base"]), bgc)
                        STATS[f"base_cr_{scheme}_min"] = min(STATS.get(f"base_cr_{scheme}_min") or 99, bcr)
                        STATS[f"faded_n_{scheme}"] += 1
                        if bcr >= FADE_MIN_CR and cr < FADE_MIN_CR - 0.01:
                            bad(where, f"{nm} 흐린 색 대비 {cr:.2f} < {FADE_MIN_CR}")
                        if bcr < FADE_MIN_CR and fc != rgb_hex(d["base"]):
                            bad(where, f"{nm} 원래 색이 이미 옅은데 색을 더 뺌")
                        if fc == rgb_hex(d["base"]):
                            STATS[f"faded_same_color_{scheme}"] += 1
            # 위험보험료 툴팁 값
            if d["rp"] and any(a != b and not (a is None or b is None) and abs(a - b) > 0.0051 for a, b in zip(d["rp"], [up[NSTD] if (row[NSTD] is not None and i < 10) else up[i] for i in range(NSTD)])):
                bad(where, f"{nm} 위험보험료 {d['rp']}")
        em = E.median_latest(key) if exp_lines else None   # 회사가 하나도 안 그려지면 차트 자체가 없다
        if em is None:
            if med:
                bad(where, "기대에 없는 중앙값 선")
        else:
            if not med:
                bad(where, "중앙값 선 없음")
            else:
                if not all(close(a, b, 0.051) for a, b in zip(med[0]["y"], em[1])):
                    bad(where, f"중앙값 {med[0]['y']} != {em[1]}")
                if not med[0]["label"].startswith(u["sector"] + " 업계 중앙값") or not med[0]["label"].endswith(" · " + u["label"]):
                    bad(where, f"중앙값 이름 {med[0]['label']!r}")
        if exp_lines and (u["label"] not in (o["aria"] or "")):
            bad(where, f"aria 에 단위 없음 {o['aria']!r}")
    else:
        segs = (decode_svg(o) if "texts" in o else []) or []
        # 기대 구간: 그려지는 회사(최대 4) 순서대로
        exp_segs = []
        for nm, code, (q, row, up) in exp_lines[:4]:
            pts = plot_y(row)
            fd = plot_fd(row, up)
            for i in range(NSTD - 1):
                if pts[i] is not None and pts[i + 1] is not None:
                    exp_segs.append((i, pts[i], i + 1, pts[i + 1], bool(fd[i] or fd[i + 1])))
        if len(segs) != len(exp_segs):
            bad(where, f"SVG 구간 {len(segs)}개 != 기대 {len(exp_segs)}개")
        else:
            for s, e in zip(segs, exp_segs):
                if (s[0], s[2]) != (e[0], e[2]) or abs(s[1] - e[1]) > 0.45 or abs(s[3] - e[3]) > 0.45:
                    bad(where, f"SVG 구간 {s[:4]} != {e[:4]}")
                    break
                if s[4] != e[4]:
                    bad(where, f"SVG 흐림 구간 {s[:4]} dash={s[4]} 기대 {e[4]}")
                    break
            if any(e[4] for e in exp_segs):
                fade_seen["narrow"] += 1
        # 현재가치 표 (선이 하나도 없으면 표 자체가 없다)
        rows_t = {r[0]: r[1] for r in o.get("table", [])}
        for nm, code in (zip(names, codes) if exp_lines else []):
            pvq = E.pv_latest(key, code) if E.sector[code] == u["sector"] else None
            cell = next((v for k, v in rows_t.items() if k.startswith(nm)), None)
            want = f"{pvq[1]:.1f}%" if pvq else "—"
            if cell != want:
                bad(where, f"{nm} 표 현재가치 {cell!r} != {want!r}")
        em = E.median_latest(key) if exp_lines else None
        mp = E.pv_median_latest(key)
        mrow = next((v for k, v in rows_t.items() if k.startswith(u["sector"] + " 중앙값")), None)
        if em and mp:
            if mrow != f"{mp[1]:.1f}%":
                bad(where, f"중앙값 표 {mrow!r} != {mp[1]:.1f}%")
            if not next((k for k in rows_t if k.startswith(u["sector"] + " 중앙값 · " + u["label"])), None):
                bad(where, f"중앙값 표 이름 {list(rows_t)}")
        elif em is None and mrow is not None:
            bad(where, "기대에 없는 중앙값 표 줄")
    # n/a 줄
    if len(o["na"]) < len(exp_na) or not all(any(nm in x and "n/a" in x for x in o["na"]) for nm in exp_na):
        bad(where, f"n/a 줄 {o['na']} 기대 회사 {exp_na}")
    for nm in exp_na:
        line = next((x for x in o["na"] if nm in x), "")
        code = E.short[nm]
        if E.sector[code] == u["sector"]:
            if u["alt_n"] and "이 단위 값 없음" in line and not ("변액사망" in line and "Indirect-Par" in line):
                bad(where, f"변액사망 사유 문구 {line!r}")
            # 회사별 사유: 같은 이름을 다른 구분으로 공시한 회사(패널 alt_co)만 그 문구, 나머지는 다른 회사·구분 이야기 없이 단순 사유
            alt_list = E.C.get("alt_co", {}).get(key)
            if alt_list is not None:
                has_alt = "Indirect-Par" in line or "공시한 회사" in line or re.search(r"\d+곳", line)
                if code in alt_list:
                    SEEN_ALT[(vn, key)].add(code)
                    if not ("이 단위 값 없음" in line and "변액사망" in line and "Indirect-Par" in line and "공시하여" in line):
                        bad(where, f"alt_co 회사 {nm} 문구 {line!r}")
                    if re.search(r"\d+곳|공시한 회사", line):
                        bad(where, f"alt_co 회사 {nm} 문구에 다른 회사 수 {line!r}")
                else:
                    # 단위 수준 사유("이 단위 미공시")이거나 회사 수준 사유(마스터 na)이고, 어느 쪽이든 다른 회사·다른 구분 이야기가 없다
                    if "이 단위 미공시" in line:
                        SEEN_PLAIN[(vn, key)].add(code)
                    if has_alt or ("미공시" not in line and "없음" not in line and "미산출" not in line):
                        bad(where, f"alt_co 밖 회사 {nm} 사유 {line!r}")
            if not ("이 단위 값 없음" in line or "미공시" in line or "없음" in line or "미산출" in line):
                bad(where, f"n/a 사유 {line!r}")
        else:
            if "단위입니다" not in line:
                bad(where, f"다른 업권 사유 {line!r}")
    if exp_na and not exp_lines and not o["empty"]:
        bad(where, "모두 빈 칸인데 안내 문구 없음")
    # 합계·다른 구분으로 바꿔 그리지 않았는지: 빈 칸 회사 이름이 데이터셋·SVG 표 선에 없다
    if wide:
        for nm in exp_na:
            if any(d["label"].startswith(nm) for d in (o["ds"] or [])):
                bad(where, f"{nm}: 단위가 없는데 선이 그려짐(대체 금지)")


def compare_sweep(E, pg, base, vn, scheme, wide, fade_seen):
    n = 0
    for u in E.units:
        key = u["key"]
        cos = sorted(E.sector_companies(u["sector"]), key=lambda c: E.co[c]["short"])
        # 단위를 공시한 회사와 안 한 회사가 같은 묶음에 섞이도록 번갈아 채운다
        have = [c for c in cos if E.latest(key, c)]
        lack = [c for c in cos if c not in have]
        order = []
        while have or lack:
            for lst in (have, lack):
                if lst:
                    order.append(lst.pop(0))
        groups = [order[i:i + 4] for i in range(0, len(order), 4)]
        for grp in groups:
            names = [E.co[c]["short"] for c in grp]
            go(pg, "c=" + ",".join(names) + "&g=" + key)
            o = pg.evaluate(CMP_READ)
            verify_cmp_state(E, o, names, key, vn, scheme, wide, "", fade_seen)
            n += 1
    # 단위마다 alt_co 의 회사 전부가 별칭 문구를, 그 밖 회사는 단순 사유를 한 번 이상 봤는지(점검이 무력하지 않다는 증거)
    for u in E.units:
        key = u["key"]
        alt = set(E.C.get("alt_co", {}).get(key, []))
        if SEEN_ALT[(vn, key)] != alt:
            bad(f"compare {vn} {key}", f"alt_co 문구를 본 회사 {sorted(SEEN_ALT[(vn, key)])} != alt_co {sorted(alt)}")
        if key == "life_dp_va_death":
            STATS[f"altwording_{vn}"] = len(SEEN_ALT[(vn, key)])
            STATS[f"plainreason_{vn}"] = len(SEEN_PLAIN[(vn, key)])
            if len(alt) != 8 or not SEEN_PLAIN[(vn, key)]:
                bad(f"compare {vn} {key}", f"변액사망 alt_co {len(alt)}곳, 단순 사유 회사 {len(SEEN_PLAIN[(vn, key)])}곳")
    return n


def check_defaults(E, pg, vn):
    """주소에 g 없음: 첫 회사 업권의 기본 단위가 눌려 있고 주소에 g 가 없다."""
    n = 0
    for code, d in E.co.items():
        nm = d["short"]
        go(pg, "c=" + nm)
        o = pg.evaluate(CMP_READ)
        n += 1
        if not o.get("card"):
            bad(f"defaults {vn}", f"{nm}: 손해율 카드 없음")
            continue
        if o["sel"] is None:
            # 손해율 가정이 전혀 없는 회사는 선택기 대신 빈 안내
            if E.latest(E.default_unit(code), code) if E.default_unit(code) else False:
                bad(f"defaults {vn}", f"{nm}: 선택기 없음")
            continue
        want = E.default_unit(code)
        if o["sel"]["value"] != want:
            bad(f"defaults {vn}", f"{nm}({E.sector[code]}): 기본 {o['sel']['value']} != {want}")
        if url_g(o["url"]) is not None:
            bad(f"defaults {vn}", f"{nm}: 주소에 g 가 있음 {o['url']}")
        if want:
            lab = E.by_key[want]["label"]
            if lab not in o["defText"]:
                bad(f"defaults {vn}", f"{nm}: 정의 줄 {o['defText']!r}")
    return n


def check_urls(E, pg, base):
    """주소 g= 여러 경우: 옛 링크·구분 이름(인코딩)·단위 키·없는 값·다른 업권 단위."""
    from urllib.parse import quote
    n = 0
    life, nl = "삼성생명", "삼성화재"
    cases = [
        # (query, 기대 선택값 or ('grp', 값), 설명)
        (f"c={life}", "life_np_mb_health", "g 없음 = 생보 기본 단위"),
        (f"c={nl}", "nl_np_mb_injury", "g 없음 = 손보 기본 단위"),
        (f"c={life}&g=Non-Par", "Non-Par", "옛 링크 g=Non-Par(구분)"),
        (f"c={life}&g={quote('합계')}", "합계", "옛 링크 g=합계(인코딩)"),
        (f"c={life}&g=합계", "합계", "옛 링크 g=합계"),
        (f"c=한화생명&g=Direct-Par", "Direct-Par", "옛 링크 g=Direct-Par"),
        (f"c=한화생명&g=Indirect-Par", "Indirect-Par", "옛 링크 g=Indirect-Par"),
        (f"c={life}&g=life_np_mb_death", "life_np_mb_death", "단위 키"),
        (f"c={life}&g=%6Cife_np_mb_death", "life_np_mb_death", "단위 키 인코딩"),
        (f"c={life}&g=zzz_없는값", "life_np_mb_health", "없는 단위 -> 기본 단위"),
        (f"c={life}&g=nl_np_mb_injury", "nl_np_mb_injury", "다른 업권 단위(주소로만 가능)"),
        (f"c=스위스리&g=re_ltnl_np_injury", "re_ltnl_np_injury", "재보 단위"),
        (f"c=스위스리&g=life_np_mb_health", "life_np_mb_health", "재보 회사에 생보 단위 주소"),
    ]
    for q, want, desc in cases:
        go(pg, q)
        o = pg.evaluate(CMP_READ)
        n += 1
        if not o.get("card") or o["sel"] is None:
            bad("url", f"{q}: 카드·선택기 없음")
            continue
        if o["sel"]["value"] != want:
            bad("url", f"{desc} [{q}]: 선택값 {o['sel']['value']} != {want}")
    # 구분 이름은 옛 동작 그대로: Non-Par 구분은 대체(합계) 규칙이 걸린다 — 데이터 비교는 옛 점검(check_loss_group)이 가진 BASE 와 같은 코드 경로라 값만 본다
    # 주소 쓰기: 선택 -> 주소
    return n


def check_ui(E, br, base):
    """선택기 접근성·키보드·주소 쓰기·끈끈한 선택·구판 폴백. 넓은 화면 한 번."""
    n = 0
    errs = []
    ctx = new_ctx(br, 1280, 900, "light")
    pg = ctx.new_page()
    attach_errs(pg, errs)
    if not open_cmp(pg, base, "c=삼성생명,한화생명"):
        bad("ui", "로드 실패")
        ctx.close()
        return 0
    o = pg.evaluate(CMP_READ)
    sel = o["sel"]
    n += 1
    if len(sel["labelFor"]) != 1 or not sel["labelFor"][0].startswith("비교 단위"):
        bad("ui", f"선택기 라벨 {sel['labelFor']}")
    labels = [g["label"] for g in sel["groups"]]
    if labels != ["구분", "생보"]:
        bad("ui", f"optgroup 머리글 {labels}")
    gopts = [x["t"] for x in sel["groups"][0]["opts"]]
    if gopts != ["합계", "Non-Par", "Direct-Par", "Indirect-Par"]:
        bad("ui", f"구분 그룹 {gopts}")
    uopts = [x["t"] for x in sel["groups"][1]["opts"]]
    want_u = [u["label"] for u in E.units if u["sector"] == "생보"]
    if uopts != want_u:
        bad("ui", f"생보 단위 그룹 {uopts} != {want_u}")
    if sel["w"] > sel["cardW"] + 1:
        bad("ui", f"선택기 폭 {sel['w']} > 카드 {sel['cardW']}")
    # 키보드: 포커스 -> ArrowDown 으로 값이 바뀌고 주소에 g 가 써진다
    pg.evaluate("() => document.getElementById('sel-g').focus()")
    pg.keyboard.press("ArrowDown")
    pg.wait_for_timeout(300)
    o2 = pg.evaluate(CMP_READ)
    n += 1
    if o2["sel"]["value"] == sel["value"] or url_g(o2["url"]) != o2["sel"]["value"]:
        bad("ui", f"키보드 선택 {sel['value']} -> {o2['sel']['value']} 주소 {o2['url']}")
    foc = pg.evaluate("() => document.activeElement && document.activeElement.id")
    if foc != "sel-g":
        bad("ui", f"다시 그린 뒤 포커스 유실 {foc!r}")
    # 끈끈한 선택: 회사를 바꿔도 고른 단위 유지, 주소에 단위 키
    pg.select_option("#sel-g", "life_np_mb_death")
    pg.wait_for_timeout(300)
    o3 = pg.evaluate(CMP_READ)
    if url_g(o3["url"]) != "life_np_mb_death":
        bad("ui", f"선택 후 주소 {o3['url']}")
    go(pg, "c=교보생명,삼성생명&g=life_np_mb_death")
    pg.click("#chips li:first-child button")   # 첫 회사 제거
    pg.wait_for_timeout(300)
    o4 = pg.evaluate(CMP_READ)
    n += 1
    if o4["sel"]["value"] != "life_np_mb_death":
        bad("ui", f"회사를 바꾼 뒤 선택 {o4['sel']['value']}")
    # 구분 하나 고르면 주소에 구분 이름(옛 링크와 같은 모양)
    pg.select_option("#sel-g", "Direct-Par")
    pg.wait_for_timeout(300)
    o5 = pg.evaluate(CMP_READ)
    if url_g(o5["url"]) != "Direct-Par" or o5["sel"]["value"] != "Direct-Par":
        bad("ui", f"구분 선택 후 {o5['url']}")
    if errs:
        bad("ui", f"콘솔 오류 {errs[:3]}")
    ctx.close()
    # 구판 JSON(단위 키 없음): 선택기에 단위 그룹이 없고, 처음 화면은 예전처럼 구분 Non-Par, 단위 주소는 무시, 오류 없음
    for kind in ("compare-old-json",):
        errs = []
        ctx = new_ctx(br, 1280, 900, "light")
        pg = ctx.new_page()
        attach_errs(pg, errs)

        def strip(route):
            r = route.fetch()
            d = json.loads(r.text())
            C = d["loss_curve"]
            for k in ("units", "default_unit", "u", "up", "med_u", "unit_note", "unit_rule"):
                C.pop(k, None)
            for m in d["metrics"]:
                m.pop("vu", None)
                m.pop("medu", None)
            route.fulfill(body=json.dumps(d, ensure_ascii=False), content_type="application/json; charset=utf-8")
        ctx.route("**/panel_compare.json*", strip)
        if not open_cmp(pg, base, "c=삼성생명&g=life_np_mb_health"):
            bad(kind, "로드 실패")
            ctx.close()
            continue
        o = pg.evaluate(CMP_READ)
        n += 1
        s0 = o["sel"]
        if s0 is None:
            bad(kind, "구분 선택기 없음")
        else:
            if [g["label"] for g in s0["groups"]] != ["구분"]:
                bad(kind, f"구판인데 단위 그룹 {[g['label'] for g in s0['groups']]}")
            if s0["value"] != "Non-Par":
                bad(kind, f"구판 처음 화면 {s0['value']} != Non-Par")
        if "처음 화면은 Non-Par" not in o["help"]:
            bad(kind, "구판 ? 팝오버에 Non-Par 안내 없음")
        if o["ds"] is None or not any(d["label"].startswith("삼성생명") for d in o["ds"]):
            bad(kind, "구판 선 없음")
        if errs:
            bad(kind, f"콘솔 오류 {errs[:3]}")
        ctx.close()
    return n


def check_compare(E, br, base, only=None):
    n = 0
    fade_seen = defaultdict(int)
    for vn, w, h, scheme in VIEWS:
        errs = []
        ctx = new_ctx(br, w, h, scheme)
        pg = ctx.new_page()
        attach_errs(pg, errs)
        if not open_cmp(pg, base, "c=삼성생명"):
            print("SKIP: compare 로드 실패", vn)
            ctx.close()
            continue
        print(f"progress: compare {vn}", flush=True)
        wide = w >= 641
        n += compare_sweep(E, pg, base, vn, scheme, wide, fade_seen)
        if vn == "1280":
            n += check_defaults(E, pg, vn)
            n += check_urls(E, pg, base)
        elif vn == "375":
            # 좁은 화면 기본·주소 표본
            for nm in ("삼성생명", "삼성화재", "스위스리", "처브라이프"):
                go(pg, "c=" + nm)
                o = pg.evaluate(CMP_READ)
                n += 1
                if o["sel"] is None or o["sel"]["value"] != E.default_unit(E.short[nm]):
                    bad("defaults 375", f"{nm}: {o['sel'] and o['sel']['value']}")
                if o["sel"] and o["sel"]["w"] > o["sel"]["cardW"] + 1:
                    bad("defaults 375", f"{nm}: 선택기 폭 {o['sel']['w']} > {o['sel']['cardW']}")
        if errs:
            bad(f"compare {vn}", f"콘솔 오류 {errs[:3]}")
        ctx.close()
    print(f"[compare] 상태 {n}개 점검, 흐린 칸이 있는 상태: 넓은 화면 선 {fade_seen['wide']}개 · 좁은 화면 {fade_seen['narrow']}개")
    if fade_seen["wide"] == 0 or fade_seen["narrow"] == 0:
        bad("compare", "흐린 칸을 한 번도 못 봄(점검 무력)")
    n += check_ui(E, br, base)
    return n


# ------------------------------------------------------------------ C. IFRS17
IFRS_READ = """() => { const ch = Chart.getChart('canvasLr'); const g = document.getElementById('lrGrp');
  const rank = {'1~10년': -1}; ['1년','2년','3년','4년','5년','6년','7년','8년','9년','10년','11~15년','16~20년','21~25년','26~30년','30년 이후','현재가치'].forEach((y, i) => rank[y] = i);
  return {q: document.getElementById('lrQ').value, seg: document.getElementById('lrSeg').value, hidden: document.getElementById('lrGrpWrap').hidden,
   labelFor: [...g.labels].map(l => l.textContent.trim()),
   groups: [...g.querySelectorAll('optgroup')].map(x => ({label: x.label, opts: [...x.querySelectorAll('option')].map(o => ({v: o.value, t: o.textContent}))})),
   flat: [...g.options].map(o => o.value), val: g.value,
   ds: ch ? ch.data.datasets.map(d => ({label: d.label, y: d.data.map(p => p.y), fd: d.fd || null, rp: d.rp || null, base: d.borderColor,
     pbg: (d.fd && d.fd.some(Boolean) && typeof d.pointBackgroundColor === 'function') ? d.data.map((p, i) => d.pointBackgroundColor({dataIndex: i})) : null,
     segDash: (d.fd && d.fd.some(Boolean) && d.segment) ? d.data.slice(0, -1).map((p, i) => d.segment.borderDash({p0DataIndex: i, p1DataIndex: i + 1})) : null,
     segCol: (d.fd && d.fd.some(Boolean) && d.segment) ? d.data.slice(0, -1).map((p, i) => d.segment.borderColor({p0DataIndex: i, p1DataIndex: i + 1})) : null,
   })) : null,
   pv: document.getElementById('lrPv').innerText, title: ch ? ch.options.plugins.title.text : null, aria: document.getElementById('canvasLr').getAttribute('aria-label'),
   helpUnit: (document.getElementById('lrHelpUnit') || {}).textContent || '', helpDef: (document.getElementById('lrHelpDef') || {}).textContent || '',
   vis: (() => { const c = document.getElementById('sec-lr').cloneNode(true); c.querySelectorAll('.iq-help-pop').forEach(e => e.remove()); return c.innerText; })(),
   bg: getComputedStyle(document.documentElement).getPropertyValue('--bg').trim(),
   sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth, selW: g.getBoundingClientRect().width,
   table: document.querySelectorAll('#lrTable tbody tr').length, tableHead: [...document.querySelectorAll('#lrTable thead th')].map(t => t.textContent)}; }"""


def ifrs_expected_units(E, code, q):
    sec = E.sector.get(code)
    out = []
    for u in E.units:
        if u["sector"] == sec and E.row(u["key"], code, q):
            out.append(u["key"])
    return out


def ifrs_order(row_vals):
    """IFRS17 차트 칸 순서: 1~10년(있으면) 먼저, 그다음 1년 ... 30년 이후. 현재가치 제외."""
    order = ["1~10년"] + SLOTS[:NSTD]
    return order


def ifrs_seq(E, key, code, q):
    """(값 목록, 위험보험료 목록) in 차트 칸 순서, 값 있는 칸만."""
    vals, rps = [], []
    for s in ["1~10년"] + SLOTS[:NSTD]:
        a = E.acc.get((key, code, q, s))
        if a and a[0] > 0:
            vals.append(a[1] / a[0] * 100.0)
            rps.append(a[0])
    return vals, rps


def load_ifrs(br, base, w, h, scheme, errs, route=None):
    ctx = new_ctx(br, w, h, scheme)
    if route:
        for pat, fn in route:
            ctx.route(pat, fn)
    pg = ctx.new_page()
    attach_errs(pg, errs)
    for _ in range(2):
        pg.goto(f"{base}/IFRS17.html?iq_internal=1", wait_until="commit", timeout=60000)
        try:
            pg.wait_for_function("() => window.Chart && document.getElementById('company').options.length > 5", timeout=45000)
            pg.wait_for_timeout(700)
            return ctx, pg
        except Exception:  # noqa: BLE001
            pass
    return ctx, None


def pick_company(pg, code):
    pg.evaluate("""(code) => { const s = document.getElementById('company'); const o = [...s.options].find(x => x.value === code); if (!o) return false; s.value = code; s.dispatchEvent(new Event('change')); return true; }""", code)
    try:
        pg.wait_for_function("() => document.getElementById('canvasLr') && window.Chart && Chart.getChart('canvasLr')", timeout=20000)
    except Exception:  # noqa: BLE001
        return False
    pg.wait_for_timeout(250)
    return True


def set_val(pg, sid, v):
    pg.evaluate("""([sid, v]) => { const s = document.getElementById(sid); s.value = v; s.dispatchEvent(new Event('change')); }""", [sid, v])
    pg.wait_for_timeout(150)


def check_ifrs_company(E, pg, code, vn, scheme, full, stats):
    """한 회사: 공시시점마다 선택지·기본값·단위별 값."""
    n = 0
    sec = E.sector[code]
    nm = E.co[code]["short"]
    pan = JSON_LR["companies"].get(code)
    if not pan:
        return 0
    qs_all = sorted(pan["q"], reverse=True)
    o0 = pg.evaluate(IFRS_READ)
    if o0["q"] != qs_all[0]:
        bad(f"ifrs17 {vn} {nm}", f"처음 공시시점 {o0['q']} != {qs_all[0]}")
    for qv in (qs_all if full else qs_all[:1]):
        set_val(pg, "lrQ", qv)
        o = pg.evaluate(IFRS_READ)
        where = f"ifrs17 {vn} {nm} {qv}"
        n += 1
        exp_units = ifrs_expected_units(E, code, qv)
        got_units = [x["v"] for g in o["groups"] for x in g["opts"] if g["label"] != "구분"]
        if got_units != exp_units:
            bad(where, f"단위 선택지 {got_units} != {exp_units}")
        if exp_units:
            if len(o["labelFor"]) != 1 or not o["labelFor"][0].startswith("비교 단위"):
                bad(where, f"라벨 {o['labelFor']}")
            labs = [g["label"] for g in o["groups"]]
            if labs[-1] != sec or (len(labs) == 2 and labs[0] != "구분"):
                bad(where, f"optgroup 머리글 {labs} 업권 {sec}")
            for g in o["groups"]:
                if g["label"] != "구분":
                    want_l = [E.by_key[k]["label"] for k in exp_units]
                    if [x["t"] for x in g["opts"]] != want_l:
                        bad(where, f"단위 이름 {[x['t'] for x in g['opts']]} != {want_l}")
        else:
            if any(g["label"] != "구분" for g in o["groups"]):
                bad(where, f"단위가 없는데 단위 그룹 {o['groups']}")
        if re.search(r"KR\d{4}", o["vis"] + (o["aria"] or "") + (o["title"] or "")):
            bad(where, "회사코드 노출")
        if o["sw"] > o["cw"] + 1:
            bad(where, f"가로 넘침 {o['sw']}>{o['cw']}")
        if "100억원" in o["vis"]:
            bad(where, "설명 문장이 화면에 노출")
        if exp_units and ("100억원" not in o["helpUnit"] or "구분은 공시 각주" not in o["helpUnit"]):
            bad(where, "? 팝오버에 단위 설명·100억원 규칙 없음")
        # 기본 선택(아직 아무것도 고르지 않은 시점 = 공시시점을 막 바꾼 상태. 끈끈한 선택은 아래에서 따로)
        grp_opts = [x["v"] for g in o["groups"] if g["label"] == "구분" for x in g["opts"]] or [v for v in o["flat"] if v not in exp_units]
        dflt_unit = E.C["default_unit"].get(sec)
        if dflt_unit and dflt_unit in exp_units:
            want_def = dflt_unit
        else:
            want_def = "Non-Par" if "Non-Par" in grp_opts else ("합계" if "합계" in grp_opts else grp_opts[0])
        # 공시시점을 바꾸기 전 끈끈한 값이 남아 있을 수 있어, 기본값 점검은 첫 시점·직접 고른 적 없는 회사에서만 한다
        if qv == qs_all[0] and o["val"] != want_def:
            bad(where, f"기본 선택 {o['val']} != {want_def}")
        # 단위마다 값·흐림·현재가치
        for key in exp_units:
            set_val(pg, "lrGrp", key)
            o2 = pg.evaluate(IFRS_READ)
            n += 1
            wk = f"{where} {key}"
            u = E.by_key[key]
            exp_vals, exp_rps = ifrs_seq(E, key, code, qv)
            d_cur = [d for d in o2["ds"] if d["label"].startswith(qv + " 공시")]
            if not d_cur:
                bad(wk, "현 시점 선 없음")
                continue
            d = d_cur[0]
            got_idx = [i for i, v in enumerate(d["y"]) if v is not None]
            got_vals = [d["y"][i] for i in got_idx]
            if len(got_vals) != len(exp_vals) or not all(abs(a - b) <= 0.06 for a, b in zip(got_vals, exp_vals)):
                bad(wk, f"현 시점 값 {[round(x, 2) for x in got_vals]} != {[round(x, 2) for x in exp_vals]}")
            else:
                stats["max_err"] = max(stats["max_err"], max([abs(a - b) for a, b in zip(got_vals, exp_vals)] or [0]))
            if not d["label"].endswith(u["label"]):
                bad(wk, f"범례 {d['label']!r}")
            if o2["title"] is None or u["label"] not in o2["title"]:
                bad(wk, f"제목 {o2['title']!r}")
            efd = [bool(r < FADE_EOK) for r in exp_rps]
            gfd = [bool(d["fd"][i]) for i in got_idx] if d["fd"] else []
            if gfd != efd:
                bad(wk, f"흐림 칸 {gfd} != {efd}")
            elif any(efd):
                stats["fade_lines"] += 1
                bgc = BG[scheme]
                if d["pbg"] is None:
                    bad(wk, "흐린 칸이 있는데 표식 함수 없음")
                else:
                    for j, i in enumerate(got_idx):
                        if efd[j] and d["pbg"][i].lower() != bgc:
                            bad(wk, f"흐린 칸 표식이 속 빈 원이 아님 {d['pbg'][i]}")
                    for i in range(len(d["y"]) - 1):
                        f1 = bool(d["fd"][i]) or bool(d["fd"][i + 1])
                        if f1 and d["segDash"][i] != [2, 4]:
                            bad(wk, f"흐린 구간 {i} 점선 아님 {d['segDash'][i]}")
                        if f1:
                            fc = rgb_hex(d["segCol"][i])
                            if fc.startswith("#"):
                                cr = contrast(fc, bgc)
                                stats[f"faded_cr_{scheme}_min"] = min(stats.get(f"faded_cr_{scheme}_min") or 99, cr)
                                stats[f"faded_n_{scheme}"] += 1
            # 현재가치 숫자
            a_pv = E.acc.get((key, code, qv, PV))
            pv = (math.floor(a_pv[1] / a_pv[0] * 1000.0 + 0.5) / 10.0) if a_pv and a_pv[0] > 0 else None   # 화면은 반올림 전 값을 절반 올림으로 한 번 반올림
            want_pv = f"현재가치 기준 {u['label']} " + (f"{pv:.1f}%" if pv is not None else "-")
            if not o2["pv"].startswith(want_pv):
                bad(wk, f"현재가치 {o2['pv']!r} != {want_pv!r}")
            if pv is not None and E.pv(key, code, qv) is not None and abs(E.pv(key, code, qv) - pv) > 0.101:
                bad(wk, f"현재가치 {pv} 와 비교 패널 값 {E.pv(key, code, qv)} 가 0.1 넘게 다름")
            elif pv is not None and E.pv(key, code, qv) != pv:
                stats["pv_tie_diff"] += 1
            # 직전 연도 점선
            y_, qn = qv.split(".")
            pq = f"{int(y_) - 1}.{qn}"
            d_prev = [x for x in o2["ds"] if x["label"].startswith(pq + " 공시")]
            pvals, prps = ifrs_seq(E, key, code, pq)
            if pvals:
                if not d_prev:
                    bad(wk, "직전 연도 점선 없음")
                else:
                    gv = [v for v in d_prev[0]["y"] if v is not None]
                    if len(gv) != len(pvals) or not all(abs(a - b) <= 0.06 for a, b in zip(gv, pvals)):
                        bad(wk, f"직전 값 {[round(x, 2) for x in gv]} != {[round(x, 2) for x in pvals]}")
                    if d_prev[0]["fd"] is not None:
                        pg_idx = [i for i, v in enumerate(d_prev[0]["y"]) if v is not None]
                        pfd = [bool(d_prev[0]["fd"][i]) for i in pg_idx]
                        if pfd != [bool(r < FADE_EOK) for r in prps]:
                            bad(wk, f"직전 흐림 칸 {pfd}")
            elif d_prev:
                bad(wk, "기대에 없는 직전 점선")
            if o2["table"] < 1:
                bad(wk, "표가 비었음")
        # 끈끈한 선택: 단위를 고른 뒤 같은 시점을 다시 그려도(회사 안) 유지, 선택지에 없으면 기본으로
    return n


def check_ifrs17(E, br, base):
    n = 0
    stats = defaultdict(float)
    codes = [c for c in JSON_LR["companies"] if c in E.co]
    errs = []
    ctx, pg = load_ifrs(br, base, 1280, 900, "light", errs)
    if pg is None:
        print("SKIP: IFRS17 로드 실패")
        return 0
    print("progress: ifrs17 1280 전 회사", flush=True)
    for code in codes:
        if not pick_company(pg, code):
            bad("ifrs17", f"{E.co[code]['short']}: 회사 선택 실패")
            continue
        n += check_ifrs_company(E, pg, code, "1280", "light", True, stats)
    if errs:
        bad("ifrs17 1280", f"콘솔 오류 {errs[:3]}")
    # 끈끈한 선택·기본값·키보드
    n += check_ifrs_sticky(E, pg)
    ctx.close()
    # 좁은 화면·다크: 표본 회사 + 오류·넘침
    sample = ["처브라이프", "삼성생명", "삼성화재", "스위스리", "코리안리", "교보라이프플래닛", "카카오페이손보"]
    for vn, w, h, scheme in VIEWS[1:]:
        errs = []
        ctx, pg = load_ifrs(br, base, w, h, scheme, errs)
        if pg is None:
            print("SKIP: IFRS17 로드 실패", vn)
            continue
        print(f"progress: ifrs17 {vn}", flush=True)
        for nm in sample:
            code = E.short.get(nm)
            if code and code in JSON_LR["companies"] and pick_company(pg, code):
                n += check_ifrs_company(E, pg, code, vn, scheme, False, stats)
        if errs:
            bad(f"ifrs17 {vn}", f"콘솔 오류 {errs[:3]}")
        ctx.close()
    # 구판 패널(5번째 원소·rp_note 없음) 폴백, 비교 패널 없음 폴백
    for kind in ("old-panel", "no-catalog"):
        errs = []

        def strip_panel(route):
            r = route.fetch()
            d = json.loads(r.text())
            d["meta"].pop("rp_note", None)
            for c in d["companies"].values():
                for qd in c["q"].values():
                    for rows in qd["s"].values():
                        for i, row in enumerate(rows):
                            if len(row) > 4:
                                rows[i] = row[:4]
            route.fulfill(body=json.dumps(d, ensure_ascii=False), content_type="application/json; charset=utf-8")

        def no_catalog(route):
            route.fulfill(status=404, body="not found")
        rt = [("**/panel_loss_ratio.json*", strip_panel)] if kind == "old-panel" else [("**/panel_compare.json*", no_catalog)]
        ctx, pg = load_ifrs(br, base, 1280, 900, "light", errs, rt)
        if pg is None:
            print("SKIP: IFRS17 구판 로드 실패", kind)
            continue
        for nm in ("삼성생명", "스위스리", "한화생명"):
            code = E.short[nm]
            if not pick_company(pg, code):
                bad(f"ifrs17 {kind}", f"{nm} 선택 실패")
                continue
            o = pg.evaluate(IFRS_READ)
            n += 1
            if any(g["label"] != "구분" for g in o["groups"]) or [v for v in o["flat"] if v not in ("합계", "Non-Par", "Direct-Par", "Indirect-Par")]:
                bad(f"ifrs17 {kind} {nm}", f"단위 선택지가 숨지 않음 {o['flat']}")
            if o["val"] != "Non-Par":
                bad(f"ifrs17 {kind} {nm}", f"구판 기본 {o['val']} != Non-Par")
            if o["helpUnit"]:
                bad(f"ifrs17 {kind} {nm}", "구판인데 단위 설명이 팝오버에 있음")
            if len(o["labelFor"]) != 1 or not o["labelFor"][0].startswith("비교 단위"):
                bad(f"ifrs17 {kind} {nm}", f"라벨 {o['labelFor']}")
            d = [x for x in o["ds"] if x["label"].startswith("2025.4Q 공시")]
            if not d or d[0]["fd"] and any(d[0]["fd"]):
                bad(f"ifrs17 {kind} {nm}", "구판인데 흐림 칸이 있거나 선이 없음")
        if errs:
            bad(f"ifrs17 {kind}", f"콘솔 오류 {errs[:3]}")
        ctx.close()
    print(f"[ifrs17] 점검 {n}건, 흐린 선 {int(stats['fade_lines'])}개, 현재 칸 값 최대 오차 {stats['max_err']:.4f}%p, 현재가치 0.1 어긋난 칸(절반 올림 대 파이썬 반올림) {int(stats['pv_tie_diff'])}")
    for k in ("light", "dark"):
        if stats.get(f"faded_n_{k}"):
            print(f"[ifrs17] 흐린 구간 대비 {k}: 최소 {stats[f'faded_cr_{k}_min']:.2f}:1 ({int(stats[f'faded_n_{k}'])}구간)")
    if stats["fade_lines"] == 0:
        bad("ifrs17", "흐린 칸을 한 번도 못 봄(점검 무력)")
    for k in ("faded_cr_light_min", "faded_cr_dark_min", "faded_n_light", "faded_n_dark"):
        if stats.get(k):
            STATS["ifrs_" + k] = stats[k]
    return n


def check_ifrs_sticky(E, pg):
    n = 0
    code = E.short["삼성생명"]
    pick_company(pg, code)
    o = pg.evaluate(IFRS_READ)
    if o["val"] != "life_np_mb_health":
        bad("ifrs17 sticky", f"삼성생명 기본 {o['val']}")
    set_val(pg, "lrGrp", "life_ip_mb_death")
    set_val(pg, "lrQ", "2024.4Q")
    o = pg.evaluate(IFRS_READ)
    n += 1
    if o["val"] != "life_ip_mb_death":
        bad("ifrs17 sticky", f"공시시점을 바꾼 뒤 선택이 풀림 {o['val']}")
    set_val(pg, "lrGrp", "Direct-Par")
    set_val(pg, "lrQ", "2025.4Q")
    o = pg.evaluate(IFRS_READ)
    n += 1
    if o["val"] != "Direct-Par":
        bad("ifrs17 sticky", f"구분 선택이 풀림 {o['val']}")
    # 다른 회사로 가면 기본으로
    pick_company(pg, E.short["삼성화재"])
    o = pg.evaluate(IFRS_READ)
    n += 1
    if o["val"] != "nl_np_mb_injury":
        bad("ifrs17 sticky", f"회사를 바꾼 뒤 기본 {o['val']}")
    # 선택기 라벨·키보드
    pg.evaluate("() => document.getElementById('lrGrp').focus()")
    before = pg.evaluate("() => document.getElementById('lrGrp').value")
    pg.keyboard.press("ArrowDown")
    pg.wait_for_timeout(300)
    after = pg.evaluate("() => document.getElementById('lrGrp').value")
    if after == before:   # 마지막 선택지였으면 위로
        pg.keyboard.press("ArrowUp")
        pg.wait_for_timeout(300)
        after = pg.evaluate("() => document.getElementById('lrGrp').value")
    n += 1
    if before == after:
        bad("ifrs17 sticky", "키보드로 선택이 안 바뀜")
    ch_title = pg.evaluate("() => Chart.getChart('canvasLr').options.plugins.title.text")
    lab = pg.evaluate("() => { const s = document.getElementById('lrGrp'); return s.options[s.selectedIndex].textContent; }")
    if lab != "합계" and lab not in ch_title:
        bad("ifrs17 sticky", f"제목이 선택을 따르지 않음 {ch_title!r} / {lab!r}")
    # 단위 없는 회사(손해율 단위 목록 밖 업권)에서 선택기 숨김/구분만: IBK연금보험은 패널에 없다면 건너뜀
    return n


# ------------------------------------------------------------------ E. 구분 수준 선택은 이미 배포된 동작 그대로
BASE_REV = "ca717655"   # 비교 단위 선택기를 넣기 직전 커밋(손해율 구분 선택기·기본 Non-Par 가 라이브인 상태)


def git_show(path, rev=BASE_REV):
    return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=str(ROOT), capture_output=True, check=True).stdout.decode("utf-8")


REG_CMP_READ = """() => {
  const anc = document.getElementById('c-loss_pv'); const card = anc ? anc.parentElement : null;
  if (!card) return {card: false};
  const cv = card.querySelector('canvas'); const ch = cv && window.Chart ? Chart.getChart(cv) : null;
  const svg = card.querySelector('.lcs svg');
  const sg = card.querySelector('#sel-g');
  return {card: true, selVal: sg ? sg.value : null, ds: ch ? ch.data.datasets.map(d => ({label: d.label, y: d.data.map(p => p.y)})) : null,
    paths: svg ? [...svg.querySelectorAll('path')].map(p => [p.getAttribute('d'), p.getAttribute('stroke'), p.getAttribute('stroke-dasharray')]) : null,
    table: svg ? [...card.querySelectorAll('.lcm tbody tr')].map(tr => [...tr.cells].map(c => c.innerText.trim())) : null,
    na: [...card.querySelectorAll('.na-list li')].map(li => li.innerText.trim()),
    aria: cv ? cv.getAttribute('aria-label') : (svg ? svg.getAttribute('aria-label') : null),
    def: (card.querySelector('.def') || {}).textContent || '', empty: (card.querySelector('.empty') || {}).textContent || null,
    foot: [...card.querySelectorAll('.clipnote')].map(e => e.textContent)}; }"""


def check_regress_compare(E, br, base):
    n = 0
    head_html = git_show("compare.html")
    sets = [("스위스리",), ("한화생명",), ("삼성화재",), ("카카오페이손보",), ("삼성생명", "교보라이프플래닛", "ABL생명"),
            ("카카오페이손보", "삼성화재"), ("뮌헨", "스코리"), ("IBK연금보험",)]

    def drop_np(d, code):
        d["loss_curve"]["g"]["Non-Par"].pop(code, None)
        for m in d["metrics"]:
            if m["id"] == "loss_pv":
                m["vg"]["Non-Par"].pop(code, None)

    def drop_np_total(d, code):
        drop_np(d, code)
        d["loss_curve"]["v"].pop(code, None)
    synth = {"no-NonPar": drop_np, "no-NonPar-no-total": drop_np_total}
    for vn, w, h, scheme in VIEWS[:2]:
        print(f"progress: regress-compare {vn}", flush=True)
        for kind in ["live"] + list(synth):
            sets_k = sets if kind == "live" else [x for x in sets if len(x) == 1]
            pages = {}
            ctxs = []
            for use_head in (False, True):
                errs = []
                ctx = new_ctx(br, w, h, scheme)
                if use_head:
                    ctx.route("**/compare.html*", lambda route, request=None: route.fulfill(body=head_html, content_type="text/html; charset=utf-8"))
                if kind != "live":
                    def make_mod(kind=kind):
                        def mod(route, request=None):
                            r = route.fetch()
                            d = json.loads(r.text())
                            synth[kind](d, mod.code)
                            route.fulfill(body=json.dumps(d, ensure_ascii=False), content_type="application/json; charset=utf-8")
                        mod.code = None
                        return mod
                    mod = make_mod()
                    ctx.route("**/panel_compare.json*", mod)
                    pages[use_head] = (ctx, ctx.new_page(), errs, mod)
                else:
                    pages[use_head] = (ctx, ctx.new_page(), errs, None)
                attach_errs(pages[use_head][1], errs)
                ctxs.append(ctx)
            for names in sets_k:
                for g in ("합계", "Non-Par", "Direct-Par", "Indirect-Par"):
                    outs = []
                    for use_head in (False, True):
                        ctx, pg, errs, mod = pages[use_head]
                        query = "c=" + ",".join(names) + "&g=" + g
                        if mod is not None and mod.code != E.short[names[0]]:
                            mod.code = E.short[names[0]]
                            ok = open_cmp(pg, base, query)   # JSON 을 다시 받아야 하므로 새로 연다
                        elif not pg.url.startswith("http"):
                            ok = open_cmp(pg, base, query)
                        else:
                            go(pg, query)
                            ok = True
                        outs.append(pg.evaluate(REG_CMP_READ) if ok else None)
                    n += 1
                    where = f"regress-compare {vn} {kind} {names} {g}"
                    if outs[0] is None or outs[1] is None:
                        bad(where, "로드 실패")
                        continue
                    new_o, old_o = outs
                    # 새 화면이 그 구분을 실제로 눌러 보인 상태만 비교한다(고른 회사 누구도 공시하지 않은 구분, 구분이 아예 없는 회사는 주소의 g 가 '없는 값'이라 새 기본(비교 단위)으로 간다 — 의도된 변경).
                    # 구분 Non-Par 는 고른 회사가 아무도 Non-Par 를 공시하지 않아도 예전처럼 합계가 눌려 보인다.
                    sv = new_o.get("selVal")
                    honored = sv == g or (g == "Non-Par" and sv == "합계" and sv in ("합계",))
                    if not honored or (sv is not None and "_" in sv):
                        STATS["regress_skipped"] += 1
                        continue
                    STATS["regress_compared"] += 1
                    for k in ("ds", "paths", "table", "na", "aria", "def", "empty", "foot"):
                        if new_o.get(k) != old_o.get(k):
                            bad(where, f"{k} 가 배포본과 다름 new={str(new_o.get(k))[:200]} old={str(old_o.get(k))[:200]}")
            for use_head in (False, True):
                if pages[use_head][2]:
                    bad(f"regress-compare {vn} {kind}", f"콘솔 오류 {pages[use_head][2][:2]}")
            for c in ctxs:
                c.close()
    return n


REG_IFRS_READ = """() => { const ch = Chart.getChart('canvasLr'); const g = document.getElementById('lrGrp');
  return {opts: [...g.options].map(o => o.value), val: g.value, hidden: document.getElementById('lrGrpWrap').hidden,
    ds: ch ? ch.data.datasets.map(d => ({label: d.label, y: d.data.map(p => p.y)})) : null, title: ch ? ch.options.plugins.title.text : null,
    aria: document.getElementById('canvasLr').getAttribute('aria-label'), pv: document.getElementById('lrPv').innerText,
    table: document.getElementById('lrTable').innerText, q: document.getElementById('lrQ').value, seg: document.getElementById('lrSeg').value}; }"""


def check_regress_ifrs(E, br, base):
    n = 0
    head_html = git_show("IFRS17.html")
    names = ["삼성생명", "한화생명", "삼성화재", "카카오페이손보", "스위스리", "코리안리", "뮌헨"]
    pages = {}
    ctxs = []
    for use_head in (False, True):
        errs = []
        ctx = new_ctx(br, 1280, 900, "light")
        if use_head:
            ctx.route("**/IFRS17.html*", lambda route: route.fulfill(body=head_html, content_type="text/html; charset=utf-8"))
        pg = ctx.new_page()
        attach_errs(pg, errs)
        pg.goto(f"{base}/IFRS17.html?iq_internal=1", wait_until="commit", timeout=60000)
        pg.wait_for_function("() => window.Chart && document.getElementById('company').options.length > 5", timeout=45000)
        pg.wait_for_timeout(700)
        pages[use_head] = (pg, errs)
        ctxs.append(ctx)
    print("progress: regress-ifrs17", flush=True)
    for nm in names:
        code = E.short[nm]
        for use_head in (False, True):
            pick_company(pages[use_head][0], code)
        qs = pages[False][0].evaluate("() => [...document.getElementById('lrQ').options].map(o => o.value)")
        for qv in qs:
            for use_head in (False, True):
                set_val(pages[use_head][0], "lrQ", qv)
            old_o = pages[True][0].evaluate(REG_IFRS_READ)
            grp_vals = list(old_o["opts"])
            for gv in grp_vals:
                outs = []
                for use_head in (False, True):
                    set_val(pages[use_head][0], "lrGrp", gv)
                    outs.append(pages[use_head][0].evaluate(REG_IFRS_READ))
                n += 1
                new_o, old_o2 = outs
                for k in ("ds", "title", "aria", "pv", "table", "q", "seg", "val"):
                    if new_o[k] != old_o2[k]:
                        bad(f"regress-ifrs17 {nm} {qv} {gv}", f"{k} 가 배포본과 다름 new={str(new_o[k])[:160]} old={str(old_o2[k])[:160]}")
                new_flat = [v for v in new_o["opts"] if v in grp_vals]
                if new_flat != grp_vals:
                    bad(f"regress-ifrs17 {nm} {qv}", f"구분 선택지 {new_o['opts']} 에 배포본 {grp_vals} 가 그대로 없음")
    for (pg, errs) in pages.values():
        if errs:
            bad("regress-ifrs17", f"콘솔 오류 {errs[:2]}")
    for c in ctxs:
        c.close()
    return n


# ------------------------------------------------------------------ main
JSON_LR = None


def main():
    global JSON_LR
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None

    def on(k):
        return only is None or only == k
    E = Expect()
    JSON_LR = jl("data/loss_ratio/panel_loss_ratio.json")
    print(f"단위 {len(E.units)}개, 기준 분기 {E.asof_q}, 회사 {len(E.co)}곳(패널 손해율 {len(JSON_LR['companies'])}곳)")
    if on("data"):
        check_data(E)
    if only == "data":
        return finish()
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:  # noqa: BLE001
        print("SKIP: playwright 없음 (브라우저 점검은 안 돌렸다)", e)
        return finish()
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    base = f"http://127.0.0.1:{port}"
    n = 0
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(channel="msedge", headless=True)
            if on("compare"):
                n += check_compare(E, br, base)
            if on("ifrs17"):
                n += check_ifrs17(E, br, base)
            if on("regress"):
                n += check_regress_compare(E, br, base)
                n += check_regress_ifrs(E, br, base)
            br.close()
    finally:
        srv.terminate()
    if Net.collector:
        bad("net", f"수집기로 가려던 요청 {len(Net.collector)}건 {Net.collector[:2]}")
    print(f"[net] 가로챈 분석 요청 {len(Net.analytics)}건(전부 차단), 수집기 요청 {len(Net.collector)}건")
    print(f"브라우저 점검 {n}건")
    return finish()


def finish():
    for k in sorted(STATS):
        if k.startswith("faded_cr") or k.startswith("base_cr"):
            print(f"[대비] {k} = {STATS[k]:.2f}")
        elif k.startswith("regress_"):
            print(f"[회귀] {k} = {int(STATS[k])}")
        elif k.startswith("altwording_") or k.startswith("plainreason_"):
            print(f"[변액사망 사유] {k} = {int(STATS[k])}")
        elif k.startswith("faded_n") or k.startswith("faded_same"):
            print(f"[흐린 구간] {k} = {int(STATS[k])}")
    print(f"violations {len(BAD)}")
    by = defaultdict(list)
    for b in BAD:
        by[b.split(":")[0].split(" ")[0]].append(b)
    for k, lst in by.items():
        print(f"  [{k}] {len(lst)}건")
        for b in lst[:12]:
            print("   -", b[:420])
    return 1 if BAD else 0


if __name__ == "__main__":
    sys.exit(main())
