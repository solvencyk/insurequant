"""Measure item4 - sum(items 5..11) residual distribution (pre and post columns).

Diagnostic only, read-only against kics_disclosure.json. Writes a JSON report
to the path given as argv[1] (or stdout if omitted).
"""
from __future__ import annotations
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
JSON_PATH = REPO / "kics_disclosure.json"

KEY_CODE = "원보험사코드"
KEY_NAME = "원수사명"
KEY_ITEM = "항목번호"
KEY_INAME = "항목명"
KEY_Q = "공시분기"
KEY_VAL = "값"
KEY_POST = "값_적용후"


def _to_float(raw):
    if raw is None:
        return None
    s = str(raw).strip().replace(",", "")
    if s in ("", "-"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def main():
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    buckets = defaultdict(dict)
    for r in rows:
        it = r.get(KEY_ITEM)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        buckets[(r.get(KEY_CODE), r.get(KEY_Q))][it] = r

    def sweep(field, *, require_complete):
        """require_complete=True: strict (all of 5..11 present).
        require_complete=False: mirrors rule 2 / _sum_optional (missing=0)."""
        compared = 0
        exact0 = 0
        hist = defaultdict(int)
        cells = []
        for (code, q), items in buckets.items():
            r4 = items.get(4)
            if r4 is None:
                continue
            i4 = _to_float(r4.get(field))
            if i4 is None:
                continue
            comps = {}
            complete = True
            for n in range(5, 12):
                rn = items.get(n)
                v = _to_float(rn.get(field)) if rn is not None else None
                if v is None:
                    complete = False
                    continue
                comps[n] = v
            if require_complete and not complete:
                continue
            total = sum(comps.values())
            resid = i4 - total
            compared += 1
            rr = round(resid, 6)
            # bucket residual to nearest integer for histogram (already 억원-scale)
            hist[round(resid)] += 1
            if abs(resid) < 1e-6:
                exact0 += 1
            cells.append({
                "code": code, "quarter": q, "item4": i4, "sum_children": total,
                "residual": rr, "children_complete": complete,
            })
        return compared, exact0, dict(sorted(hist.items())), cells

    report = {}
    for label, field in (("pre", KEY_VAL), ("post", KEY_POST)):
        for mode, require_complete in (("strict", True), ("rule2_semantics", False)):
            compared, exact0, hist, cells = sweep(field, require_complete=require_complete)
            key = f"{label}_{mode}"
            report[key] = {
                "compared": compared,
                "exact_zero": exact0,
                "pct_exact_zero": round(100.0 * exact0 / compared, 1) if compared else None,
                "histogram": hist,
            }
            if mode == "rule2_semantics":
                report[label + "_cells"] = cells

    out = sys.argv[1] if len(sys.argv) > 1 else None
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if out:
        Path(out).write_text(text, encoding="utf-8")
        print(f"wrote {out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
