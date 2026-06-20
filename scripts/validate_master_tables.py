#!/usr/bin/env python3
"""Validate master tables: data/dart/viz/pl_breakdown_master.json + CSM_waterfall.json.

Implements V8 consumer code:
  - CSM_WATERFALL_CLOSING_IDENTITY : 기초+신계약+이자+가정+상각 = 기말  (CSM_waterfall, 억원)
  - PL_BRIDGE_DART_INTERNAL        : 8-eq P&L bridge                  (pl_breakdown_master, 백만원)
  - CSM_CROSSCHECK_WATERFALL_VS_PL : pl.원수CSM상각(+) + wf.CSM상각(-)*100 ≈ 0

Both masters long-format. PL master is **백만원**, CSM waterfall is **억원**:
cross-check aligns by ×100 (억→백만). Item names space-normalized.
Tolerance per equation: max(0.1%·|expected|, floor). floor = 2억 (waterfall) / 200백만 (PL).
An equation is SKIPPED if its LHS or any RHS term is missing (None) — 0.0 is a valid value.

Runs `build_root_masters.py` first (idempotent) so root masters reflect the latest
diag/viz source — parser fixes to the source aren't visible in root masters until rebuilt.
Pass --no-build to skip the rebuild and validate the existing root masters as-is.
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")

PL_PATH = "data/dart/viz/pl_breakdown_master.json"
WF_PATH = "CSM_waterfall.json"


def norm(s: str) -> str:
    return (s or "").replace(" ", "")


def load_long(path: str) -> dict:
    d = json.loads((ROOT / path).read_text(encoding="utf-8"))
    idx: dict = defaultdict(dict)
    for r in d:
        idx[(r["원수사명"], r["공시분기"])][norm(r["항목명"])] = r["값"]
    return idx


# ---- PL bridge equations: (label, LHS_key, [(RHS_key, sign), ...]) ----
# 보험손익은 dual-form(별도 처리): 회사마다 보험손익 = ΣLOB(bare) 또는 ΣLOB+기타영업수익-기타사업비용(adj).
# 손보(DB/현대/흥국/메리츠 등)는 기타영업수익·기타사업비용이 보험손익 라인 밖(별도 영업비용)이라 bare.
# 삼성화재 등은 adj. 둘 중 하나 닫히면 PASS.
PL_EQS = [
    ("생명장기원수손익 = 원수CSM상각+원수RA+원수예실차+기타원수",
     "생명장기원수손익",
     [("원수CSM상각", 1), ("원수위험조정변동", 1), ("원수예실차", 1), ("기타생명장기원수손익", 1)]),
    ("생명장기재보험손익 = 재보험CSM상각+재보험RA+재보험예실차+기타재보험",
     "생명장기재보험손익",
     [("재보험CSM상각", 1), ("재보험위험조정변동", 1), ("재보험예실차", 1), ("기타생명장기재보험손익", 1)]),
    ("생명장기손익 = 원수손익+재보험손익",
     "생명장기손익",
     [("생명장기원수손익", 1), ("생명장기재보험손익", 1)]),
    ("투자손익 = 투자이익+보험금융손익",
     "투자손익",
     [("투자이익", 1), ("보험금융손익", 1)]),
    ("영업이익 = 보험손익+투자손익",
     "영업이익",
     [("보험손익", 1), ("투자손익", 1)]),
    ("세전이익 = 영업이익+영업외손익",
     "세전이익",
     [("영업이익", 1), ("영업외손익", 1)]),
    ("당기순이익 = 세전-법인세",
     "당기순이익",
     [("세전이익", 1), ("법인세", -1)]),
]

# 등식별 abs floor (백만원). 영업이익은 0근처 회사(KDB 등) 과민 방지로 완화.
EQ_FLOOR = {"영업이익 = 보험손익+투자손익": 600.0}
DEFAULT_FLOOR = 200.0

QS = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q",
      "2024.3Q", "2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q"]


def load_qoq_cfg():
    return yaml.safe_load((ROOT / "config" / "qoq_thresholds.yaml").read_text(encoding="utf-8"))


def qoq_threshold(cfg, yaml_key, domain="ifrs17"):
    items = (cfg.get("items", {}).get(domain, {}) or {})
    if yaml_key and yaml_key in items and "threshold" in items[yaml_key]:
        return items[yaml_key]["threshold"]
    dd = (cfg.get("defaults", {}).get(domain, {}) or {})
    return dd.get("threshold") or cfg["defaults"]["global"]["threshold"]


def prev_quarter(q):
    i = QS.index(q) if q in QS else -1
    return QS[i - 1] if i > 0 else None


def net_quarterly(idx, co, item, q):
    """YTD 누적값 → net 분기 증분. 같은 FY 내 cur-prev, FY 1Q는 cur 자체."""
    y, qq = q.split(".")
    qn = int(qq[0])
    cur = idx.get((co, q), {}).get(item)
    if cur is None:
        return None
    if qn == 1:
        return cur
    pv = idx.get((co, f"{y}.{qn - 1}Q"), {}).get(item)
    return None if pv is None else cur - pv


def qoq_scan(idx, items, floor, cfg):
    """items: [(항목명, yaml_key, cumulative)]. 2024+ 분기만 평가. YELLOW(anomaly).
    - cumulative(flow: 신계약/이자/상각/손익) → **YoY**: 같은 분기 전년 YTD 대비.
      net-quarterly QoQ는 분기 계절성(1Q net vs 4Q net)으로 노이즈가 커 부적합.
      YoY는 같은 누적 시점 비교라 계절성이 상쇄돼 추세 이상만 잡힘.
    - non-cumulative(stock: 기말 CSM) → QoQ: 잔액이라 직전 분기 대비 안정적."""
    rows = []
    eval_q = [q for q in QS if not q.startswith("2023.")]
    for (co, q) in idx:
        if q not in eval_q:
            continue
        for item, yk, cum in items:
            thr = qoq_threshold(cfg, yk)
            if cum:  # flow → YoY
                y, qq = q.split(".")
                ref = f"{int(y) - 1}.{qq}"
                basis = "yoy"
            else:    # stock → QoQ
                ref = prev_quarter(q)
                basis = "qoq"
            if ref is None:
                continue
            a, b = idx.get((co, q), {}).get(item), idx.get((co, ref), {}).get(item)
            if a is None or b is None or abs(b) < floor:
                continue
            delta = (a - b) / abs(b)
            if abs(delta) > thr:
                rows.append((co, q, item, delta, thr, a, b, basis))
    return rows


def coverage_holes(idx, key_items, active_min=7):
    """데이터 누락(hole) census. SKIP으로 숨기지 말고 명시.
    active 회사(핵심항목 보유 분기 >= active_min)의 빈 분기 = hole.
    그 미만(외국계·소형 = 애초에 미공시)은 structural로 분리(검증 제외).
    2023 분기는 사이트 비노출(사용자 결정)이라 known으로 분리 — real hole은 2024+."""
    cos = sorted({co for (co, _) in idx})
    real, known, struct = [], [], []
    for co in cos:
        present = [q for q in QS if any(idx.get((co, q), {}).get(k) is not None for k in key_items)]
        if not present:
            continue
        if len(present) < active_min:
            struct.append((co, len(present)))
            continue
        for q in QS:
            m = idx.get((co, q), {})
            vals = [m.get(k) for k in key_items]
            if all(v is None for v in vals):
                kind = "통째"
            elif any(v is None for v in vals):
                kind = "부분"
            else:
                continue
            (known if q.startswith("2023.") else real).append((co, q, kind))
    return real, known, struct


def rebuild_root_masters() -> None:
    """Run build_root_masters.py so root masters reflect the latest diag/viz source.
    parser가 소스(csm_waterfall_master_diag / pl_breakdown_master)를 고쳐도 이 빌드를
    안 돌리면 루트 CSM_waterfall.json / PL_breakdown.json(검증 대상)에 반영 안 됨.
    idempotent라 항상 선행 호출 (끄려면 --no-build)."""
    script = ROOT / "scripts" / "build_root_masters.py"
    print("[build] build_root_masters.py 실행 (루트 마스터 최신화) ...")
    r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(f"[build] ⚠️ 빌드 실패 (rc={r.returncode}) — 기존 마스터로 검증 진행.")
        if r.stderr:
            print("[build] " + r.stderr.strip().splitlines()[-1][:160])
    else:
        for ln in [l for l in (r.stdout or "").splitlines() if l.strip()][-2:]:
            print(f"[build] {ln[:120]}")
    print()


SENS_PATH = "data/dart/viz/sensitivity_heatmap.json"


def sensitivity_unit_sanity():
    """Owner 2026-06-14 claim 2: CSM 민감도 단위 미정규화(원/만원/억원 혼재) sanity.
    회사별 max|csm_delta| vs 또래 median 규모비. 정규화 후엔 동일단위(억원) 가정이므로 또래 대비
    거대 outlier = 미정규화 시그니처(현대해상=원 단위라 삼성화재의 ~640배였던 케이스의 회귀가드).
      RED   : ratio>1000x or <1/1000x (clean 단위오류 — gate 차단)
      YELLOW: ratio>100x or <1/100x  (의심 — 보고만, 또래보다 100배+ 작은 미정규화 ÷ 누락 등)."""
    sp = ROOT / SENS_PATH
    sens_red, sens_yellow = [], []
    if not sp.exists():
        return sens_red, sens_yellow
    sdoc = json.loads(sp.read_text(encoding="utf-8"))
    scales = []
    for c in sdoc.get("companies", []) or []:
        ds = [abs(s["csm_delta"]) for s in (c.get("scenarios") or [])
              if isinstance(s.get("csm_delta"), (int, float))]
        if ds:
            scales.append((c.get("company"), max(ds), c.get("unit"), c.get("unit_detected")))
    if len(scales) < 5:
        return sens_red, sens_yellow
    vals = sorted(v for _, v, _, _ in scales)
    med = vals[len(vals) // 2] or 1.0
    for name, mx, unit, ud in scales:
        ratio = mx / med
        if ratio > 1000 or ratio < 1e-3:
            sens_red.append((name, mx, ratio, unit, ud))
        elif ratio > 100 or ratio < 1e-2:
            sens_yellow.append((name, mx, ratio, unit, ud))
    return sens_red, sens_yellow


def sensitivity_direction_sanity():
    """User 2026-06-14 rule-of-thumb: CSM이 증가하는 시나리오면 당기손익도 증가해야 한다(반대도 동일).
    100% 법칙은 아니나(onerous-block에선 실제 역행 가능) 의심 신호 → sign(csm_delta)≠sign(pl_impact)이면
    YELLOW flag. 파싱오류(손익/자본 컬럼 오선택·부호) 또는 실효과(흥국생명 해지율=source-faithful 역행)를
    한 망으로 triage. 0근방 노이즈는 floor로 제외. 게이트 비차단(보고만)."""
    sp = ROOT / SENS_PATH
    flags = []
    if not sp.exists():
        return flags
    sdoc = json.loads(sp.read_text(encoding="utf-8"))
    for c in sdoc.get("companies", []) or []:
        name = c.get("company")
        for s in (c.get("scenarios") or []):
            cd, pl = s.get("csm_delta"), s.get("pl_impact")
            if not (isinstance(cd, (int, float)) and isinstance(pl, (int, float))):
                continue
            if abs(cd) >= 1.0 and abs(pl) >= 1.0 and (cd > 0) != (pl > 0):
                ratio = abs(cd) / abs(pl) if pl else float("inf")
                flags.append((name, s.get("risk"), s.get("shock"), cd, pl, ratio))
    return flags


def main() -> int:
    if "--no-build" not in sys.argv:
        rebuild_root_masters()
    pl = load_long(PL_PATH)
    wf = load_long(WF_PATH)

    # ===== 1. CLOSING_IDENTITY (CSM_waterfall, 억원) =====
    need = ["기초CSM", "신계약CSM", "이자부리", "가정및경험조정", "CSM상각", "기말CSM"]
    ci_pass = ci_skip = 0
    ci_fail = []
    for (co, q), m in sorted(wf.items()):
        if any(m.get(k) is None for k in need):
            ci_skip += 1
            continue
        lhs = sum(m[k] for k in need[:-1])
        rhs = m["기말CSM"]
        diff = lhs - rhs
        if abs(diff) > max(0.001 * abs(rhs), 2.0):
            ci_fail.append((co, q, round(rhs, 1), round(diff, 1)))
        else:
            ci_pass += 1

    print("=" * 78)
    print(f"1. CLOSING_IDENTITY (CSM_waterfall, 억원)  pass={ci_pass} fail={len(ci_fail)} skip={ci_skip}")
    print("=" * 78)
    for co, q, rhs, diff in ci_fail:
        print(f"  FAIL {co:14s} {q}  기말={rhs:>11.1f}  diff={diff:>+10.1f}  ({diff/rhs*100:+.1f}%)")

    # ===== 0. COVERAGE (데이터 누락 hole — SKIP으로 숨기지 않음) =====
    wf_holes, wf_known, wf_struct = coverage_holes(wf, ["기초CSM", "신계약CSM", "이자부리", "가정및경험조정", "CSM상각", "기말CSM"])
    pl_holes, pl_known, pl_struct = coverage_holes(pl, ["보험손익", "생명장기손익", "당기순이익"])
    print("=" * 78)
    print(f"0. COVERAGE real hole(2024+)  CSM={len(wf_holes)} PL={len(pl_holes)}  | "
          f"2023 known(비노출)={len(wf_known)+len(pl_known)} | struct(미공시)제외={len(wf_struct)+len(pl_struct)}")
    print("=" * 78)
    for co, q, kind in wf_holes:
        print(f"  HOLE-CSM {co:14s} {q} ({kind})")
    for co, q, kind in pl_holes:
        print(f"  HOLE-PL  {co:14s} {q} ({kind})")
    print()

    # ===== 1b. CSM_PLAUSIBILITY (절댓값 sanity — closing identity가 못 잡는 것) =====
    # closing identity는 내부 산술 합산만 봐서 (a)분기 복붙 (b)기말 QoQ 폭락 같은
    # 절댓값 이상을 통과시킴. 별도 plausibility 체크로 보강.
    wf_co: dict = defaultdict(dict)
    for (co, q), m in wf.items():
        wf_co[co][q] = m
    dup_rows = []     # (co, [분기...]) — 같은 회사 내 기말 CSM 동일 (복붙 의심)
    spike_rows = []   # (co, q_prev, q, prev, cur, dq) — 기말 QoQ |Δ|>50%
    for co, qmap in sorted(wf_co.items()):
        # 복붙: 같은 회사 내 서로 다른 분기의 기말 CSM이 소수점까지 동일.
        # CSM 잔액은 매분기 변하므로 동일 = 분기 데이터 복붙(2025를 2024로 채움 등) 강력 의심.
        end_sigs: dict = defaultdict(list)
        for q, m in qmap.items():
            e = m.get("기말CSM")
            if e is not None:
                end_sigs[round(e, 1)].append(q)
        for v, qq in end_sigs.items():
            if len(qq) > 1:
                dup_rows.append((co, sorted(qq)))
        for i in range(1, len(QS)):
            p = qmap.get(QS[i - 1], {}).get("기말CSM")
            c = qmap.get(QS[i], {}).get("기말CSM")
            if p is not None and c is not None and abs(p) > 1e-6 and abs((c - p) / p) > 0.50:
                spike_rows.append((co, QS[i - 1], QS[i], p, c, (c - p) / p))

    # 연속성: FY[t] 각 분기 기초 CSM = FY[t-1].4Q 기말 (YTD 연초값 고정 방식).
    # 작년 기말 = 올해 기시. 2023은 2022 데이터 없어 SKIP.
    FY_Q = {
        "2024": ["2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q"],
        "2025": ["2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q"],
        "2026": ["2026.1Q"],
    }
    PREV_CLOSE = {"2024": "2023.4Q", "2025": "2024.4Q", "2026": "2025.4Q"}
    # 연속성(continuity) break = 무조건 RED. 원천 "소급재작성"으로 보이는 케이스라도 raw 대조로
    # 확정되기 전에는 면제하지 않는다 (owner 2026-06-16: self-closing identity는 opening을 검증 못 함 —
    # 2026.1Q 5사 기시 misparse를 '재작성'으로 오판한 사건. 기시≠직전기말이면 그냥 RED). 메모리: continuity-break-is-red.
    # owner는 면제(self-closing) 대신 **데이터 정정** 방식 채택(2026-06-20): 재작성/misparse 과거 cell은 후속 분기
    # 공시의 '전기(비교)' 테이블에서 재작성값을 추출해 마스터를 통일 → cont 자연 해소(parser 발주). 면제셋 미사용.
    cont_rows = []   # (co, q, 기초, 전년말기말, 전년말분기)
    for co, qmap in sorted(wf_co.items()):
        for fy, qq in FY_Q.items():
            pc = qmap.get(PREV_CLOSE[fy], {}).get("기말CSM")
            if pc is None:
                continue
            for q in qq:
                o = qmap.get(q, {}).get("기초CSM")
                if o is None:
                    continue
                if abs(o - pc) > max(0.005 * abs(pc), 2.0):
                    cont_rows.append((co, q, o, pc, PREV_CLOSE[fy]))

    # FY내 기초 일관성: YTD 컨벤션상 같은 FY 모든 분기의 기초 CSM은 동일(=전년말)해야 함.
    # 사용자 적발(2026-06-10): 롯데 2023.2Q 기초가 3Q/4Q와 다름 — FY경계 연속성만 보고
    # FY내 동일성을 안 봐서 미스. 2023도 검사 가능(전년 기말 없이 FY내 상호비교라).
    # Documented exceptions (parser 판별 2026-06-11, inbox user_xlsx_audit_followup 답변):
    # 전부 legit_restatement — 원천 공시가 FY 중 정정/소급재작성(교보는 3Q24 공식 소급재작성 주석).
    # 데이터 수정 대상 아님 → EXC 표시만, 게이트 제외. (CONT/연속성에는 적용 안 함 — owner 2026-06-16:
    # continuity break는 무조건 RED. WFY[FY내 동일성]만 이 면제 유지.)
    WFY_EXCEPTIONS = {
        ("교보생명보험", "2023"), ("교보생명보험", "2024"), ("KB라이프생명", "2024"),
        ("한화생명", "2023"), ("현대해상", "2023"), ("케이디비생명보험", "2023"),
        ("메리츠화재해상보험", "2023"), ("에이비엘생명보험", "2023"), ("농협생명보험", "2023"),
    }
    wfy_rows = []   # (co, fy, {q: 기초})
    wfy_exc = []
    for co, qmap in sorted(wf_co.items()):
        for fy in ("2023", "2024", "2025", "2026"):
            opens = [(q, qmap[q].get("기초CSM")) for q in QS
                     if q.startswith(fy + ".") and q in qmap and qmap[q].get("기초CSM") is not None]
            if len(opens) < 2:
                continue
            vals = [v for _, v in opens]
            if max(vals) - min(vals) > max(0.005 * abs(max(vals)), 2.0):
                rec = (co, fy, {q: round(v, 1) for q, v in opens})
                (wfy_exc if (co, fy) in WFY_EXCEPTIONS else wfy_rows).append(rec)

    # 불가능한 0: CSM상각 == 정확히 0 (경제적으로 불가능 — 보유계약 있으면 상각 발생).
    # 사용자 룰 지시(2026-06-10): 미래에셋 2025.2Q+ 상각 0 적발. None은 coverage가 잡지만
    # 0.0은 "present"로 통과하던 맹점.
    # parser AMORT_ZERO 스펙(2026-06-10): 상각 0인데 기초/기말이 양수면 RED.
    # 기초=기말=0(미보유) 정상사는 가드로 제외. None 0값은 coverage/ZLEG 담당.
    zamort_rows = []  # (co, q)
    for (co, q), m in sorted(wf.items()):
        a = m.get("CSM상각")
        o, c = m.get("기초CSM"), m.get("기말CSM")
        endpoints_pos = (o is not None and o > 0) or (c is not None and c > 0)
        if a is not None and a == 0 and endpoints_pos:
            zamort_rows.append((co, q))

    print()
    print("=" * 78)
    print(f"1b. CSM_PLAUSIBILITY  복붙(dup)={len(dup_rows)} 기말QoQ폭변(spike)={len(spike_rows)} "
          f"연속성위반(cont)={len(cont_rows)} FY내기초불일치(wfy)={len(wfy_rows)} 상각0(zamort)={len(zamort_rows)}")
    print("=" * 78)
    for co, qq in dup_rows:
        print(f"  DUP   {co:14s} 기말 CSM 동일(복붙 의심): {qq}")
    for co, qp, q, p, c, dq in spike_rows:
        print(f"  SPIKE {co:14s} {qp}->{q}: 기말 {p:.0f} -> {c:.0f} ({dq*100:+.0f}%)")
    for co, q, o, pc, pcq in cont_rows:
        print(f"  CONT  {co:14s} {q} 기초={o:.0f} ≠ {pcq} 기말={pc:.0f}  (Δ{o-pc:+.0f})")
    for co, fy, opens in wfy_rows:
        print(f"  WFY   {co:14s} FY{fy} 기초 불일치: {opens}")
    for co, fy, opens in wfy_exc:
        print(f"  WFYEX {co:14s} FY{fy} (documented: legit restatement) {opens}")
    for co, q in zamort_rows:
        print(f"  ZAMRT {co:14s} {q} CSM상각=0 (불가능 — 추출오류)")

    # ===== 2. PL_BRIDGE (pl_breakdown_master, 백만원) =====
    pb_pass = pb_skip = 0
    pb_fail = []
    eq_fail_count = defaultdict(int)
    for (co, q), m in sorted(pl.items()):
        # --- 보험손익 dual-form (bare ΣLOB / adj +기타영업수익-기타사업비용) ---
        bo = m.get("보험손익")
        lob = [m.get("생명장기손익"), m.get("자동차손익"), m.get("일반손익")]
        if bo is None or any(x is None for x in lob):
            pb_skip += 1
        else:
            bare = sum(lob)
            cands = [bare]
            oi, oe = m.get("기타영업수익"), m.get("기타사업비용")
            if oi is not None and oe is not None:
                cands.append(bare + oi - oe)
            diff = min((c - bo for c in cands), key=abs)
            if abs(diff) > max(0.001 * abs(bo), DEFAULT_FLOOR):
                pb_fail.append((co, q, "보험손익(dual)", round(bo, 1), round(diff, 1)))
                eq_fail_count["보험손익(dual)"] += 1
            else:
                pb_pass += 1
        # --- 나머지 등식 ---
        for label, lhs_key, terms in PL_EQS:
            lhs = m.get(lhs_key)
            if lhs is None or any(m.get(k) is None for k, _ in terms):
                pb_skip += 1
                continue
            rhs = sum(sign * m[k] for k, sign in terms)
            diff = rhs - lhs
            if abs(diff) > max(0.001 * abs(lhs), EQ_FLOOR.get(label, DEFAULT_FLOOR)):
                pb_fail.append((co, q, label, round(lhs, 1), round(diff, 1)))
                eq_fail_count[label] += 1
            else:
                pb_pass += 1

    # ===== 2b. PL_ZERO_LEGS (생명장기 sub-item 0/None 무더기 = 추출실패) =====
    # 사용자 적발(2026-06-10): 현대해상 등 생명장기 sub-item이 xlsx에서 전부 0으로 보임.
    # JSON 확인 결과 정확히-0이 아니라 **None**(추출 누락)이고 xlsx가 None→0 렌더링.
    # 기존 coverage는 헤드라인 3개(보험손익/생명장기손익/당기순이익)만 봐서 sub-item hole 사각.
    # 룰: 보험손익이 있는 active 행에서 sub-item 10종 중 (None 또는 정확히 0.0)이 ≥4 → flag.
    # (0.0도 함께 — 0=0+0+0 자명통과 맹점. 2023 분기는 사이트 비노출이라 제외.)
    PL_LEG_ITEMS = ["생명장기원수손익", "원수CSM상각", "원수위험조정변동", "원수예실차",
                    "기타생명장기원수손익", "생명장기재보험손익", "재보험CSM상각",
                    "재보험위험조정변동", "재보험예실차", "기타생명장기재보험손익"]
    # 불가능-0 leg (owner 확정 2026-06-11): 장기보험 영위사면 아래 4종은 0원일 수 없다.
    # 0.0이면 추출오류 — None(coverage가 잡음)과 별개로 명시 RED.
    IMPOSSIBLE_ZERO_LEGS = ["생명장기원수손익", "기타생명장기원수손익",
                            "생명장기재보험손익", "기타생명장기재보험손익"]
    zerolegs_rows = []   # (co, q, item)
    for (co, q), m in sorted(pl.items()):
        if q.startswith("2023."):
            continue
        for k in IMPOSSIBLE_ZERO_LEGS:
            if m.get(k) == 0:
                zerolegs_rows.append((co, q, k))

    # Legit-absent (parser 판별 2026-06-11): None이 추출실패가 아니라 원천 비공시인 케이스.
    # "ALL" = 생명장기 분해 자체 미공시(감사보고서-only 소형사/보증보험). 항목 set = 해당 항목만 분리 미공시.
    # 단 (co, q) 튜플은 *특정 분기만* 예외(진짜 미공시 confirmed) — 회사 전체 면죄 금지.
    ZLEG_LEGIT = {
        # 현대해상은 legit_absent 오판이었음(owner 답지로 2026.1Q 분리손익 실재 확인) → 회사 면제 제거.
        "에이비엘생명보험": {"생명장기재보험손익", "재보험CSM상각", "재보험위험조정변동", "기타생명장기재보험손익"},
        "서울보증보험": "ALL",          # 보증보험 — 생명장기 leg 자체 없음
        "AIG손해보험": "ALL",           # 감사보고서-only, 분해 미공시
        "교보라이프플래닛생명보험": "ALL",  # 디지털 최소공시 (TODO_parser L51 legit)
        "신한이지손해보험": "ALL",        # CSM 제외사(단위오류), PL 분해도 미공시
    }
    # 분기 단위 legit (진짜 미공시 confirmed). 현대 2024.1Q~2025.2Q: OLD form 주석에 보험서비스비용·재보험수익
    # LOB 미분리(parser 표단위 raw확인 2026-06-14: LOB-헤더 표=수지현황 netted·보험수익+재보험서비스비용·금융손익
    # 3종뿐 → 비용 leg 부재로 도출불가). 2025.3Q+는 NEW form(분석공시)부터 분리공시 → 추출됨(예외 불요).
    ZLEG_LEGIT_CQ = {("현대해상", q) for q in
                     ("2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q", "2025.1Q", "2025.2Q")}
    zleg_rows = []  # (co, q, n_zero, n_none, 생명장기손익)
    zleg_exc = 0
    for (co, q), m in sorted(pl.items()):
        if q.startswith("2023."):
            continue
        if m.get("보험손익") is None:
            continue
        legit = ZLEG_LEGIT.get(co)
        if legit == "ALL" or (co, q) in ZLEG_LEGIT_CQ:
            zleg_exc += 1
            continue
        items = [k for k in PL_LEG_ITEMS if not (legit and k in legit)]
        vals = [m.get(k) for k in items]
        n_none = sum(1 for v in vals if v is None)
        n_zero = sum(1 for v in vals if v is not None and v == 0)
        if n_none + n_zero >= 4:
            zleg_rows.append((co, q, n_zero, n_none, m.get("생명장기손익")))

    print()
    print("=" * 78)
    print(f"2. PL_BRIDGE (pl_breakdown_master, 백만원)  pass={pb_pass} fail={len(pb_fail)} skip={pb_skip}  "
          f"| 2b. ZERO_LEGS flag={len(zleg_rows)} | 2c. IMPOSSIBLE-0 leg={len(zerolegs_rows)}")
    print("=" * 78)
    print("  -- fail count by equation --")
    for label, n in sorted(eq_fail_count.items(), key=lambda x: -x[1]):
        print(f"    {n:>3d}  {label}")
    print("  -- fail detail (first 35) --")
    for co, q, label, lhs, diff in pb_fail[:35]:
        print(f"  FAIL {co:14s} {q}  [{label.split('=')[0].strip()}]  lhs={lhs:.1f} diff={diff:+.1f}")
    print("  -- zero-legs (생명장기 sub-item 0/None 무더기, 2024+, first 40) --")
    for co, q, zs, nnone, lt in zleg_rows[:40]:
        lt_s = f"{lt:.0f}" if lt is not None else "None"
        print(f"  ZLEG {co:14s} {q}  zero={zs} none={nnone}  생명장기손익={lt_s}")
    print("  -- IMPOSSIBLE-0: 생명장기 분해손익 0원 불가 (owner 확정) --")
    for co, q, item in zerolegs_rows[:40]:
        print(f"  ZERO0 {co:14s} {q}  {item}=0 (불가능 — 추출오류)")

    # ===== 3. CSM_CROSSCHECK (pl.원수CSM상각 + wf.CSM상각*100 ≈ 0, 백만원) =====
    # 4Q-only: pl 원수CSM상각/wf CSM상각 모두 YTD 누적이라 1~3Q는 분기배분 차이로 틀어짐.
    # 연말(4Q=연간 누계)에서만 동일 기준 → 4Q만 비교, 1~3Q SKIP.
    # cross-table(서로 다른 DART 표: PL 보험수익 구성 vs CSM 변동표)이라 표간 반올림/집계 차이로
    # 수% 편차는 구조적 → 3단계 tol: OK ≤ max(5%,300mn) / MINOR ≤ 10%(경고,pass) / FAIL > 10%.
    cc_pass = cc_minor = cc_skip = 0
    cc_fail = []
    cc_minor_rows = []
    common = sorted(set(pl) & set(wf))
    for (co, q) in common:
        if not q.endswith(".4Q"):
            cc_skip += 1
            continue
        # wf '발행한 보험계약' CSM상각 = 원수(direct) + 수재(assumed reinsurance). For a
        # reinsurer (코리안리) the PL splits these into 원수CSM상각(4) + 수재CSM상각(4-1):
        # both are issued contracts, so the PL side must add 수재 to match the rollforward.
        # (출재/retro = 9-1 출재CSM상각, a HELD reinsurance asset — excluded, not added.)
        p_dir = pl[(co, q)].get("원수CSM상각")       # 백만원, 보험수익 기여 → 양수
        p_assumed = pl[(co, q)].get("수재CSM상각")   # 재보험사만 존재 (수재 발행계약)
        p = None if p_dir is None else p_dir + (p_assumed or 0.0)
        w = wf[(co, q)].get("CSM상각")               # 억원, CSM 감소 → 음수
        if p is None or w is None:
            cc_skip += 1
            continue
        w_mn = w * 100.0                              # 억 → 백만
        s = p + w_mn
        abs_s = abs(s)
        rel = abs_s / abs(p) if p else 0.0
        if abs_s <= max(0.05 * abs(p), 300.0):
            cc_pass += 1
        elif rel <= 0.10:
            cc_minor += 1
            cc_minor_rows.append((co, q, round(p, 1), round(w_mn, 1), round(s, 1), rel))
        else:
            cc_fail.append((co, q, round(p, 1), round(w_mn, 1), round(s, 1), rel))

    print()
    print("=" * 78)
    print(f"3. CSM_CROSSCHECK (pl.원수CSM상각 + wf.CSM상각 ≈ 0, 4Q-only 백만원)  "
          f"common={len(common)} pass={cc_pass} minor={cc_minor} fail={len(cc_fail)} skip={cc_skip}")
    print("   tol: OK≤max(5%,300mn) / MINOR≤10%(경고) / FAIL>10%")
    print("=" * 78)
    for co, q, p, w, s, rel in cc_fail[:35]:
        print(f"  FAIL  {co:14s} {q}  pl={p:>+12.1f}  wf={w:>+12.1f}  sum={s:>+10.1f}  ({rel*100:+.1f}%)")
    for co, q, p, w, s, rel in cc_minor_rows[:35]:
        print(f"  MINOR {co:14s} {q}  pl={p:>+12.1f}  wf={w:>+12.1f}  sum={s:>+10.1f}  ({rel*100:+.1f}%)")

    # ===== 4. QOQ_DELTA_WARN (시계열 anomaly, YELLOW — 다운스트림 차단 안 함) =====
    # 누적항목(신계약/이자/상각, PL 손익)은 net-quarterly 증분 비교, 시점값(기말 CSM)은 raw QoQ.
    # 2024+ 분기만 평가. threshold는 config/qoq_thresholds.yaml.
    qcfg = load_qoq_cfg()
    # spec(qoq_thresholds.yaml items.ifrs17) 대상 = CSM 항목만. PL 손익(보험손익/투자손익/당기순이익)은
    # 시장·금리 민감으로 본질적 고변동 + spec 미등록이라 anomaly 룰 부적합 → 제외.
    CSM_QOQ = [("신계약CSM", "new_business_csm", True), ("이자부리", "csm_interest_accretion", True),
               ("CSM상각", "csm_amortization", True), ("기말CSM", "csm_closing", False)]
    qoq_rows = qoq_scan(wf, CSM_QOQ, 50.0, qcfg)  # floor 50억 (작은 분모 폭발 제거)
    qoq_rows.sort(key=lambda r: -abs(r[3]))
    print()
    print("=" * 78)
    print(f"4. QOQ_DELTA_WARN (시계열 급변, YELLOW)  flagged={len(qoq_rows)} (2024+, net-quarterly)")
    print("=" * 78)
    for co, q, item, delta, thr, a, b, basis in qoq_rows[:30]:
        print(f"  YEL {co:14s} {q} {item:10s} ΔQoQ={delta*100:>+8.1f}% (>{thr*100:.0f}%, {basis}) {b:.0f}→{a:.0f}")
    if len(qoq_rows) > 30:
        print(f"  ... +{len(qoq_rows)-30} more")
    qout = ROOT / "data" / "_derived" / "qoq_warn.json"
    qout.parent.mkdir(parents=True, exist_ok=True)
    qout.write_text(json.dumps(
        [{"company": c, "quarter": q, "item": it, "delta_pct": round(d * 100, 1),
          "threshold_pct": round(t * 100, 0), "cur": round(a, 1), "ref": round(b, 1),
          "basis": bs, "sign_flip": (a < 0) != (b < 0)} for c, q, it, d, t, a, b, bs in qoq_rows],
        ensure_ascii=False, indent=2), encoding="utf-8")

    sens_red, sens_yellow = sensitivity_unit_sanity()
    sens_dir = sensitivity_direction_sanity()
    print()
    print("=" * 78)
    print(f"5. SENSITIVITY_UNIT_SANITY (csm_delta 또래-median 규모비, 억원)  "
          f"RED={len(sens_red)} YELLOW={len(sens_yellow)}")
    print("   RED: ratio>1000x or <1/1000x (단위 미정규화) / YELLOW: >100x or <1/100x")
    print("=" * 78)
    for name, mx, ratio, unit, ud in sens_red:
        print(f"  RED  {str(name):18s} max|Δ|={mx:>12.2f} ×med={ratio:>8.3g}  unit={unit}/det={ud}")
    for name, mx, ratio, unit, ud in sens_yellow:
        print(f"  YEL  {str(name):18s} max|Δ|={mx:>12.2f} ×med={ratio:>8.3g}  unit={unit}/det={ud}")

    print()
    print("=" * 78)
    print(f"5b. SENSITIVITY_DIRECTION_SANITY (CSM↔손익 부호 역행 = 파싱오류/onerous 의심, YELLOW)  flag={len(sens_dir)}")
    print("    rule(user): CSM↑면 손익도↑ 통상 — sign 불일치 시 flag. |CSM|·|손익|≥1억 floor.")
    print("=" * 78)
    for name, risk, shock, cd, pl, ratio in sens_dir:
        print(f"  SDIR {str(name):16s} {str(risk):14s} {str(shock):20s} CSM={cd:>+10.1f} 손익={pl:>+9.1f} (|CSM|/|손익|={ratio:.0f}x)")

    print()
    print("#" * 78)
    print(f"SUMMARY  coverage_hole:{len(wf_holes)}CSM/{len(pl_holes)}PL | "
          f"closing:{ci_pass}P/{len(ci_fail)}F/{ci_skip}S | "
          f"plausibility:{len(dup_rows)}dup/{len(spike_rows)}spike/{len(cont_rows)}cont/"
          f"{len(wfy_rows)}wfy/{len(zamort_rows)}zamort | "
          f"pl_bridge:{pb_pass}P/{len(pb_fail)}F/{pb_skip}S | zero_legs:{len(zleg_rows)} | "
          f"impossible0:{len(zerolegs_rows)} | "
          f"crosscheck:{cc_pass}P/{cc_minor}M/{len(cc_fail)}F/{cc_skip}S | "
          f"qoq_warn:{len(qoq_rows)}Y | sens:{len(sens_red)}R/{len(sens_yellow)}Y/{len(sens_dir)}dir")
    print("#" * 78)
    # QOQ/sens_yellow는 YELLOW(anomaly)라 exit code에 반영 안 함. wfy/zamort/zleg/impossible0/sens_red은 데이터 오류라 반영.
    return 0 if not (ci_fail or pb_fail or cc_fail or dup_rows or spike_rows or cont_rows
                     or wf_holes or pl_holes or wfy_rows or zamort_rows or zleg_rows
                     or zerolegs_rows or sens_red) else 2


if __name__ == "__main__":
    raise SystemExit(main())
