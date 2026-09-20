#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Adjudicate the PRINTED_DASH item23 (법인세) cells of the disclosure-PL backfill staging.

Default is null.  A dash is promoted to 0 only with evidence.  Three independent axes:
  A  self-closure  : the same table prints 세전이익 and 당기순이익 and they are EQUAL,
                     i.e. E6 closes with 법인세 = 0 and this is the table's only dash.
  B  DART 4Q       : the same company's DART-sourced item23 in PL_breakdown.json (annual,
                     a different source entirely) is 0 for the surrounding year(s).
  C  loss-maker    : the quarter's 당기순이익 < 0 — a 결손 company owing no current tax.
Prints the full per-cell table.  Read-only."""
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

stg = json.loads((ROOT / "data/_derived/pl_backfill_disclosure_20260918.json")
                 .read_text(encoding="utf-8"))
BF = set(stg["backfill_item_numbers"])
rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))

# DART master item23 / item24 per (code, quarter) — all of these companies are 4Q-only in DART
m23, m24 = {}, {}
for r in rows:
    try:
        it = int(r.get("항목번호"))
    except (TypeError, ValueError):
        continue
    if it == 23:
        m23[(r["원보험사코드"], r["공시분기"])] = r.get("값")
    elif it == 24:
        m24[(r["원보험사코드"], r["공시분기"])] = r.get("값")

dash_by_co = defaultdict(list)
out = []
for c in stg["cells"]:
    code, q = c.get("원보험사코드"), c.get("공시분기")
    for k, it in (c.get("items") or {}).items():
        n = int(k)
        if it.get("dash_state") != "PRINTED_DASH" or n not in BF:
            continue
        dash_by_co[code].append(q)
        items = c["items"]
        pre = (items.get("22") or {}).get("값_억원")
        net = (items.get("24") or {}).get("값_억원")
        # B: the company's DART 4Q 법인세 for the years around this quarter
        yr = int(q[:4])
        dart = {f"{y}.4Q": m23.get((code, f"{y}.4Q")) for y in (yr - 1, yr, yr + 1)}
        dart_known = {k2: v for k2, v in dart.items() if v is not None}
        out.append({
            "code": code, "name": c.get("원보험사명"), "quarter": q, "item": n,
            "backfill_excluded": c.get("backfill_excluded"),
            "raw_value": it.get("raw_value"),
            "세전_억": pre, "순이익_억": net,
            "A_self_closure": (pre is not None and net is not None and abs(pre - net) < 1e-9),
            "A_diff_억": (None if pre is None or net is None else round(pre - net, 4)),
            "B_dart_4Q_tax_백만원": dart_known,
            "C_lossmaker": (net is not None and net < 0),
            "existing_promotion": it.get("dash_promotion"),
        })

print(f"PRINTED_DASH cells in the 5 merge items = {len(out)}")
print("  by item:", dict(Counter(o['item'] for o in out)))
print("  backfill_excluded:", dict(Counter(str(o['backfill_excluded']) for o in out)))
print("\nconsecutive-dash runs per company:",
      {k: len(v) for k, v in sorted(dash_by_co.items())})

print("\n| 회사 | 분기 | 항목 | 세전(억) | 순이익(억) | A 자기폐쇄 | B DART 4Q 법인세(백만원) | C 결손 | 판정 |")
print("|---|---|---|---|---|---|---|---|---|")
verdicts = Counter()
for o in sorted(out, key=lambda x: (x["code"], x["quarter"])):
    axes = sum([o["A_self_closure"], bool(o["B_dart_4Q_tax_백만원"]) and
                all(abs(v) < 1e-9 for v in o["B_dart_4Q_tax_백만원"].values()), o["C_lossmaker"]])
    if o["backfill_excluded"]:
        verdict = "범위밖(KR0004 보류)"
    elif o["A_self_closure"] and axes >= 2:
        verdict = "0 승격"
    elif o["A_self_closure"]:
        verdict = "0 승격(A단독)"
    else:
        verdict = "null 유지"
    verdicts[verdict] += 1
    b = ", ".join(f"{k2}={v:g}" for k2, v in sorted(o["B_dart_4Q_tax_백만원"].items())) or "—"
    print(f"| {o['code']} {o['name']} | {o['quarter']} | #{o['item']} 법인세 | "
          f"{o['세전_억']:g} | {o['순이익_억']:g} | "
          f"{'PASS(세전=순이익)' if o['A_self_closure'] else 'FAIL'} | {b} | "
          f"{'예' if o['C_lossmaker'] else '아니오'} | {verdict} |")
print("\nverdicts:", dict(verdicts))

dst = ROOT / "data/_derived/_probe_20260920_dash_adjudication.json"
dst.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"wrote {dst.relative_to(ROOT)}")
