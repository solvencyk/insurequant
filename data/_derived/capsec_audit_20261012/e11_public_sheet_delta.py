# -*- coding: utf-8 -*-
"""e11: the downloadable capsec sheets between the previous audited pin (OLD, default 6fd00720) and the new pin: structure (columns, row counts, item names per sheet) and value-level delta.
Expectation after the call-date correction: identical structure; changed cells only in rows of 메리츠 / 아이엠라이프 / KB라이프 of 보완자본소진율 (numerator, utilization, deducted legacy
subordinated, notes); 기본자본소진율 / 자본비율전망 / 자본성증권발행현황 unchanged.   Output e11_public_sheet_delta_<newrev>.txt"""
import os
import sys
from collections import Counter

HERE = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/capsec_audit_20261012/"
sys.path.insert(0, HERE)
import audit_io  # noqa: E402

OLD = os.environ.get("AUDIT_OLD", "6fd00720")
NEW = audit_io.resolved_rev()
L = ["old pin %s -> new pin %s ; manifest build_id old %s new %s" % (OLD, NEW, audit_io.load_json("public_exports/manifest.json", OLD).get("build_id"),
                                                                    audit_io.load_json("public_exports/manifest.json", NEW).get("build_id"))]
for sheet in ("기본자본소진율", "보완자본소진율", "자본비율전망", "자본성증권발행현황"):
    o = audit_io.load_json("public_exports/%s.json" % sheet, OLD)
    n = audit_io.load_json("public_exports/%s.json" % sheet, NEW)
    cols_o, cols_n = list(o[0].keys()), list(n[0].keys())
    items_key = "항목명" if "항목명" in o[0] else "구분"
    items_o, items_n = Counter(r[items_key] for r in o), Counter(r[items_key] for r in n)
    L.append("== %s: rows %d -> %d ; columns equal %s ; item-name multiset equal %s" % (sheet, len(o), len(n), cols_o == cols_n, items_o == items_n))
    # cell-level delta: align rows by (company, quarter, item) occurrence order
    def key(r, i):
        return (r.get("원수사명") or r.get("회사명"), r.get("공시분기"), r.get(items_key), r.get("발행일"), r.get("액면가_억"))
    mo = {}
    for r in o:
        mo.setdefault(key(r, 0), []).append(r)
    mn = {}
    for r in n:
        mn.setdefault(key(r, 0), []).append(r)
    changed = []
    for k in sorted(set(mo) | set(mn), key=str):
        a, b = mo.get(k, []), mn.get(k, [])
        if len(a) != len(b):
            changed.append((k, "row count %d -> %d" % (len(a), len(b))))
            continue
        for x, y in zip(a, b):
            diff = [c for c in cols_n if x.get(c) != y.get(c)]
            if diff:
                changed.append((k, "; ".join("%s: %s -> %s" % (c, str(x.get(c))[:36], str(y.get(c))[:36]) for c in diff if c != "비고") + ("; 비고 changed" if "비고" in diff else "")))
    comps = sorted({str(k[0]) for k, _ in changed})
    L.append("   changed cells/rows: %d ; companies touched: %s" % (len(changed), comps))
    for k, d in changed:
        L.append("      %s | %s | %s" % (k[0], k[2], d))
open(HERE + "e11_public_sheet_delta_%s.txt" % NEW, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\n".join(L))
