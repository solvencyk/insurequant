# -*- coding: utf-8 -*-
"""스테이징 재생성 감사: (a) 8항목 값이 베이스라인과 불변인지, (b) REJECT/NOT_TESTABLE 셀별
내역, (c) PRINTED_DASH 전건 판정표.

실행:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260918f_staging_audit.py <baseline.json>
"""
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NEW = os.path.join(ROOT, "data", "_derived", "pl_backfill_disclosure_20260918.json")


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    base = load(sys.argv[1])
    new = load(NEW)
    bmap = {(c["원보험사코드"], c["공시분기"]): c for c in base["cells"]}
    nmap = {(c["원보험사코드"], c["공시분기"]): c for c in new["cells"]}

    print("=== (a) 8항목 값 불변 대조 (베이스라인 vs 재생성) ===")
    diffs, dash_flips, n_cmp = [], [], 0
    for k, bc in bmap.items():
        nc = nmap.get(k)
        if nc is None:
            diffs.append((k, "*", "cell missing in new"))
            continue
        for it, brec in bc.get("items", {}).items():
            nrec = nc.get("items", {}).get(it)
            if nrec is None:
                diffs.append((k, it, "item missing in new"))
                continue
            n_cmp += 1
            bv, nv = brec["값_억원"], nrec["값_억원"]
            if brec.get("dash_zero"):
                dash_flips.append((k, it, brec.get("raw_value"), nrec.get("dash_state"),
                                   nrec["dash_promotion"]["promoted"], nv))
                continue
            if bv != nv:
                diffs.append((k, it, f"{bv} -> {nv}"))
        for it in nc.get("items", {}):
            if it not in bc.get("items", {}):
                diffs.append((k, it, "new item appeared"))
    print(f"비대시 항목 대조 {n_cmp}건, 값 차이 {len(diffs)}건")
    for d in diffs[:40]:
        print("  DIFF", d)
    print(f"베이스라인 dash_zero=True 였던 항목 {len(dash_flips)}건 (아래 판정표 참조)")

    print()
    print("=== (b) REJECT_SELF_CLOSURE 셀 ===")
    for c in new["cells"]:
        if c.get("acceptance") != "REJECT_SELF_CLOSURE":
            continue
        print(f"\n{c['원보험사코드']} {c['원보험사명']} {c['공시분기']}  page={c.get('page')}")
        for name, r in sorted(c["equations"].items()):
            if r["status"] != "FAIL":
                continue
            print(f"   {name} FAIL  {r['equation']}")
            print(f"      lhs={r['lhs_억원']}  rhs={r['rhs_억원']}  diff={r['diff_억원']}억")
        vals = {k: v["값_억원"] for k, v in c["items"].items()}
        comps = {k: v["값_억원"] for k, v in c["components"].items()}
        print("      items:", vals)
        print("      comps:", comps)

    print()
    print("=== (c) EQ_NOT_TESTABLE 셀 ===")
    for c in new["cells"]:
        if c.get("acceptance") != "EQ_NOT_TESTABLE":
            continue
        s = c["equation_summary"]
        nt = {k: c["equations"][k]["missing_terms"] for k in s["not_testable_list"]}
        print(f"{c['원보험사코드']} {c['공시분기']}  pass={s['pass']} nt={s['not_testable_list']}")
        for k, m in nt.items():
            print(f"      {k}: missing {m}")

    print()
    print("=== (d) PRINTED_DASH 판정표 (items) ===")
    rows = []
    for c in new["cells"]:
        for it, rec in sorted(c["items"].items(), key=lambda kv: int(kv[0])):
            if rec.get("dash_state") != "PRINTED_DASH":
                continue
            rows.append((c["원보험사코드"], c["원보험사명"], c["공시분기"], it, rec["항목명"],
                         rec["dash_promotion"]["promoted"], rec["값_억원"],
                         rec["dash_promotion"].get("evidence") or rec["dash_promotion"].get("reason")))
    print(f"총 {len(rows)}건")
    for r in rows:
        ev = r[7]
        ev = ev.split(" PASS")[0] + " PASS" if ev and " PASS" in ev else ev
        print(f"{r[0]} {r[1][:8]:<8} {r[2]} #{r[3]:<2} {r[4]:<12} "
              f"{'0으로 승격' if r[5] else 'null 유지':<10} {ev}")

    print()
    print("=== (e) PRINTED_DASH (components) ===")
    for c in new["cells"]:
        for ck, rec in c["components"].items():
            if rec.get("dash_state") != "PRINTED_DASH":
                continue
            ev = rec["dash_promotion"].get("evidence") or rec["dash_promotion"].get("reason")
            ev = ev.split(" PASS")[0] + " PASS" if ev and " PASS" in ev else ev
            print(f"{c['원보험사코드']} {c['공시분기']} {ck:<14} "
                  f"{'0으로 승격' if rec['dash_promotion']['promoted'] else 'null 유지':<10} {ev}")

    print()
    print("=== (f) 병합 후보 집계 ===")
    by_item, by_co = {}, {}
    for c in new["cells"]:
        for it, rec in c["items"].items():
            if rec.get("merge_candidate"):
                by_item[it] = by_item.get(it, 0) + 1
                by_co[c["원보험사코드"]] = by_co.get(c["원보험사코드"], 0) + 1
    print("항목별:", {k: by_item[k] for k in sorted(by_item, key=int)})
    print("회사별:", dict(sorted(by_co.items())))
    print("총:", new["n_merge_candidate_values"], " provenance entries:", len(new["provenance_entries"]))


if __name__ == "__main__":
    main()
