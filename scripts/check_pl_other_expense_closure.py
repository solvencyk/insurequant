#!/usr/bin/env python3
"""PL 기타사업비용(item16) closure check — is item16 part of 보험손익(item1) or spurious?

Schema (IFRS17.html waterfall): item1(보험손익) = 4+5+6+7+8+13+14 + (15 − 16).
i.e. 기타사업비용(item16) is subtracted as part of 보험손익. For SOME companies the
EXTRACTED item1 already equals the component sum WITHOUT subtracting item16 — there
item16 is NOT part of 보험손익 (it lives below it as a separate operating expense),
so the waterfall's −16 over-subtracts and the chart breaks (owner report 2026-06-16:
KB손해 보험손익 0.63조 only without −16; item16=0.39조 wrongly subtracted).

Rule (owner): where 보험손익 = Σcomponents closes WITHOUT −16, item16 should be 0.

Classifies every (company, quarter) in pl_breakdown_master.json:
  ZERO   = closes without −16 (|item1 − Σcomp| ≤ tol) AND item16 materially != 0
  KEEP   = closes WITH −16 (item16 is a real 보험손익 component)
  NEITHER= closes neither way (separate PL-bridge issue, not this rule)
tol = max(100, 1% of |item1|) 백만원. Read-only. Exit 2 if any ZERO cell found.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "data" / "dart" / "viz" / "pl_breakdown_master.json"
COMP = ("4", "5", "6", "7", "8", "13", "14", "15")  # 보험손익 leaf comps (8=재보험 agg; excl 9-12)


def _num(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    m = json.loads(MASTER.read_text(encoding="utf-8"))
    rows = m if isinstance(m, list) else m.get("rows", m.get("data", []))
    g: dict = {}
    name: dict = {}
    for r in rows:
        code, it, q = r.get("원보험사코드"), r.get("항목번호"), r.get("공시분기")
        if code is None or it is None or q is None:
            continue
        g.setdefault((code, q), {})[str(it)] = r.get("값")
        name[code] = r.get("원수사명")

    zero, keep, neither = [], [], []
    for (code, q), items in sorted(g.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        i1 = _num(items.get("1"))
        if i1 is None or _num(items.get("4")) is None:
            continue
        present = [_num(items.get(k)) for k in COMP if _num(items.get(k)) is not None]
        if len(present) < 3:
            continue
        S = sum(present)
        i16 = _num(items.get("16")) or 0.0
        resid_wo = i1 - S
        resid_w = i1 - (S - i16)
        tol = max(100.0, 0.01 * abs(i1))
        closes_wo, closes_w = abs(resid_wo) <= tol, abs(resid_w) <= tol
        if closes_wo and abs(i16) > tol:
            zero.append((code, name.get(code), q, i16, resid_wo))
        elif closes_w and not closes_wo:
            keep.append((code, name.get(code), q))
        elif not closes_wo and not closes_w:
            neither.append((code, name.get(code), q, i1, S, i16, resid_wo, resid_w))

    print(f"PL 기타사업비(item16) closure: ZERO={len(zero)} KEEP={len(keep)} NEITHER={len(neither)}")
    print("\nZERO candidates (보험손익 closes WITHOUT −16 → item16 should be 0):")
    for code, nm, q, i16, rwo in zero:
        clean = "exact" if abs(rwo) < 1 else f"resid={rwo:.0f}"
        print(f"  {code} {nm} {q}  item16={i16:.0f} ({clean})")
    print("\nNEITHER (separate PL-bridge issue, not this rule):")
    for code, nm, q, i1, S, i16, rwo, rw in neither:
        print(f"  {code} {nm} {q}  i1={i1:.0f} Σcomp={S:.0f} item16={i16:.0f} resid_wo={rwo:.0f} resid_w={rw:.0f}")
    return 2 if zero else 0


if __name__ == "__main__":
    raise SystemExit(main())
