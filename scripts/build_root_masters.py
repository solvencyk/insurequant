#!/usr/bin/env python3
"""Assemble the neat ROOT master tables with both 연누계(YTD) and 당분기(quarterly) columns.

Sources (YTD, long-format):
  - data/dart/viz/pl_breakdown_master.json   (PL breakdown, 백만원)
  - CSM_waterfall.json                        (CSM 6-step waterfall, 억원)

Outputs (overwrite, root):
  - PL_breakdown.json
  - CSM_waterfall.json   (in place; 값_당분기 always recomputed from 값 → idempotent)

당분기 = quarterly standalone, derived from YTD by 유량/저량 (flow/stock):
  - 유량(flow)  : 당분기 = YTD(Qn) − YTD(Qn-1) within the same FY; Q1 당분기 = Q1 YTD.
    (all PL items; CSM 신계약/이자/가정경험조정/상각)
  - 저량(stock) : point-in-time balance — CSM 기초/기말 (항목 1, 6).
      · 기말 당분기 = 기말 YTD (unchanged).
      · 기초 당분기 = 직전분기 기말 YTD (Q1 → 기초 YTD).
  This makes the 당분기 waterfall close: 기초+Σflow=기말 (≡ sequential quarter).
  NOTE: a few 4Q(annual) filings restate the opening CSM, so the 4Q 당분기 기초 (=Q3 기말)
  can differ from the annual-report 기초 — a source quirk, surfaced not hidden.
"""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PL_SRC = ROOT / "data" / "dart" / "viz" / "pl_breakdown_master.json"
PL_OUT = ROOT / "PL_breakdown.json"
# CSM source = the build_csm_waterfall_master.py output (item4=residual → closing closes by
# construction; 35 companies, all coded).  Supersedes the old history-chain root file.
CSM_SRC = ROOT / "data" / "dart" / "viz" / "csm_waterfall_master_diag.json"
CSM_OUT = ROOT / "CSM_waterfall.json"
# Owner manual corrections (xlsx review, 2026-06-10) — survive diag rebuilds. Upserts 값
# by (code, item, quarter) and drops excluded companies BEFORE 당분기 recompute.
CSM_OVR = ROOT / "data" / "dart" / "viz" / "csm_manual_overrides.json"
CSM_ABS_CAP = 5e5    # 억: real insurer CSM max (삼성생명) ≈ 3e5; >5e5 = unit error (AIG 2025.4Q ~1000×)

CSM_OPEN, CSM_CLOSE = 1, 6          # 저량 (stock) 항목번호: 기초 CSM / 기말 CSM
# Canonical 항목명 (the diag labels item4 "가정 및 경험 조정 등"; consumers/validation expect
# "가정 및 경험 조정" — normalize so the closing-identity 항목명 match holds).
CSM_ITEM_NM = {1: "기초 CSM", 2: "신계약 CSM", 3: "이자 부리",
               4: "가정 및 경험 조정", 5: "CSM 상각", 6: "기말 CSM"}


def _qkey(q):                        # "2023.2Q" -> (2023, 2)
    return (int(q[:4]), int(q[5]))


def _prev_q(q):                      # within same FY; None at Q1
    y, n = _qkey(q)
    return None if n == 1 else f"{y}.{n - 1}Q"


def _flow_dangi(ytd_by_q, q):
    """유량 당분기 = YTD(q) − YTD(prev); Q1 = YTD.  None if a needed YTD is missing."""
    cur = ytd_by_q.get(q)
    if cur is None:
        return None
    p = _prev_q(q)
    if p is None:
        return cur
    prev = ytd_by_q.get(p)
    return None if prev is None else round(cur - prev, 6)


_PL_COMP = (4, 5, 6, 7, 8, 13, 14, 15)   # 보험손익(1) components excluding 16


def _zero_other_expense(rows):
    """item16(기타사업비) -> 0 where 보험손익(1) already closes WITHOUT it (item16 is
    below-the-line opex there, not a 보험손익 component — owner/validation 20260616T1210Z;
    IFRS17.html:470 waterfall subtracts -16). General, raw-independent closure test:
    |item1 - Σ(4,5,6,7,8,13,14,15)| <= max(100, 1%·|item1|). Naturally keeps cells that only
    close WITH -16 (KEEP) and excludes partial mis-extracts (DB손해 2023.2Q resid 6869 > tol)."""
    by_cq = defaultdict(dict)
    for r in rows:
        by_cq[(r["원보험사코드"], r["공시분기"])][r["항목번호"]] = r
    n = 0
    for items in by_cq.values():
        r1, r16 = items.get(1), items.get(16)
        if r1 is None or r16 is None:
            continue
        i1, i16 = r1.get("값"), r16.get("값")
        if i1 is None or not i16:
            continue
        comp = sum(((items.get(k) or {}).get("값") or 0) for k in _PL_COMP)
        # tol tuned to catch genuine closures (흥국화재 resid ≤278, KB/KDB exact) while
        # excluding partial mis-extracts (DB손해 2023.2Q resid 6869 = separate PL-bridge issue).
        if abs(i1 - comp) <= max(300, abs(i1) * 0.001):
            r16["값"] = 0.0
            n += 1
    print(f"  pl 기타사업비(item16)->0: {n} cells (보험손익 closes without -16)")
    return rows


def build_pl():
    rows = json.loads(PL_SRC.read_text(encoding="utf-8"))
    rows = _zero_other_expense(rows)
    # YTD by (code, item) -> {quarter: 값}
    ytd = defaultdict(dict)
    for r in rows:
        ytd[(r["원보험사코드"], r["항목번호"])][r["공시분기"]] = r["값"]
    out = []
    for r in rows:
        key = (r["원보험사코드"], r["항목번호"])
        v = r.get("값")
        dangi = _flow_dangi(ytd[key], r["공시분기"]) if v is not None else None
        nr = {k: r[k] for k in r if k != "값_당분기"}
        nr["값"] = v                 # 연누계(YTD)
        nr["값_당분기"] = dangi       # 당분기(quarterly) — all PL items are flows
        out.append(nr)
    PL_OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(out)


def _apply_csm_overrides(rows):
    """Owner manual corrections: exclude companies + upsert 값. Returns new row list."""
    if not CSM_OVR.exists():
        return rows
    ovr = json.loads(CSM_OVR.read_text(encoding="utf-8"))
    excl = set(ovr.get("exclude_companies", {}))
    rows = [r for r in rows if r["원보험사코드"] not in excl]
    idx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in rows}
    meta = {}
    for r in rows:
        meta.setdefault(r["원보험사코드"],
                        {k: r[k] for k in ("원수사명", "티커", "생손보여부")})
    n_set = n_add = 0
    for s in ovr.get("set", []):
        key = (s["원보험사코드"], s["항목번호"], s["공시분기"])
        if key in idx:
            idx[key]["값"] = s["값"]; n_set += 1
        elif s["원보험사코드"] in meta:
            rows.append({"원보험사코드": s["원보험사코드"], **meta[s["원보험사코드"]],
                         "항목번호": s["항목번호"],
                         "항목명": CSM_ITEM_NM.get(s["항목번호"], ""),
                         "공시분기": s["공시분기"], "값": s["값"]})
            n_add += 1
    print(f"  csm overrides: {n_set} set, {n_add} added, {len(excl)} companies excluded")
    return rows


def build_csm():
    rows = json.loads(CSM_SRC.read_text(encoding="utf-8"))
    rows = _apply_csm_overrides(rows)
    # Unit-error guard: drop a (company, quarter) whose ANY stage exceeds the absolute cap
    # (e.g. AIG손해 2025.4Q is ~1000× — a filing-unit misread).  Null its stages, don't ship.
    bad_cq = set()
    by_cq = defaultdict(list)
    for r in rows:
        by_cq[(r["원보험사코드"], r["공시분기"])].append(r.get("값"))
    for cq, vs in by_cq.items():
        if any(isinstance(x, (int, float)) and abs(x) > CSM_ABS_CAP for x in vs):
            bad_cq.add(cq)
    ytd = defaultdict(dict)           # (code, item) -> {q: 값}
    for r in rows:
        if (r["원보험사코드"], r["공시분기"]) in bad_cq:
            continue
        ytd[(r["원보험사코드"], r["항목번호"])][r["공시분기"]] = r["값"]
    out = []
    for r in rows:
        code, item, q = r["원보험사코드"], r["항목번호"], r["공시분기"]
        v = None if (code, q) in bad_cq else r.get("값")
        if v is None:
            dangi = None
        elif item == CSM_CLOSE:                       # 저량: 기말 = point-in-time
            dangi = v
        elif item == CSM_OPEN:                        # 저량: 기초 = 직전분기 기말 (Q1 → 기초)
            p = _prev_q(q)
            dangi = v if p is None else ytd[(code, CSM_CLOSE)].get(p)
        else:                                         # 유량: 신계약/이자/조정/상각
            dangi = _flow_dangi(ytd[(code, item)], q)
        nr = {k: r[k] for k in r if k != "값_당분기"}
        nr["항목명"] = CSM_ITEM_NM.get(item, r.get("항목명"))   # canonical name (drop "등")
        nr["값"] = v
        nr["값_당분기"] = (round(dangi, 6) if isinstance(dangi, (int, float)) else dangi)
        out.append(nr)
    CSM_OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(out), len(bad_cq)


def main():
    np = build_pl()
    nc, nbad = build_csm()
    print(f"wrote {PL_OUT}  ({np} rows, 값 + 값_당분기)")
    print(f"wrote {CSM_OUT}  ({nc} rows, 값 + 값_당분기; {nbad} unit-error c-q nulled)")


if __name__ == "__main__":
    main()
