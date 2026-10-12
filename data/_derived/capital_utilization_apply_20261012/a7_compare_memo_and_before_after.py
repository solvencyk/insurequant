"""a7: (1) 47-company diff of the newly written kics_tier{1,2}_utilization.json against the Opus memo
(recompute_47.csv + memo §3.2 final tier1 table), (2) before/after table vs the committed HEAD version (read-only).

Memo §3.2 tier1 finals are typed here from the memo text (the CSV column t1_pct_binding is the upper bound that
treats every non-legacy security as basic-capital type; the memo table then zeroes the supplementary-type ones).
For the four undetermined companies the expected value is the upper bound (ticket: 보수적 상한 + type_unconfirmed),
except 흥국생명 whose type is now confirmed basic-capital (same number, 81.4).

Run (repo root):
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_utilization_apply_20261012/a7_compare_memo_and_before_after.py
Outputs (same folder): a7_memo_diff.txt · b1_before_after_47.csv (utf-8-sig)
"""
from __future__ import annotations

import csv
import io
import json
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
MEMO = REPO / "data" / "_derived" / "capital_utilization_definition_20261012" / "recompute_47.csv"

# memo §3.2 "새 정의로 2026.2Q tier1" table (final values; undetermined -> upper bound)
T1_MEMO = {"KR0068": 0.0, "KR0072": 0.0, "KR0050": 0.0, "KR0032": 0.0, "KR0005": 62.4, "KR0073": 70.1,
           "KR0002": 53.1, "KR0011": 151.6, "KR0097": 238.2, "KR0001": 18.9, "KR0003": 14.3, "KR0099": 12.2,
           "KR0076": 221.7, "KR1000": 205.1, "KR0104": 72.7, "KR0083": 42.1, "KR0071": 81.4, "KR0008": 0.5}
# memo §3.2 leg values quoted in the text: code -> (legacy 15% leg, basic-new 10% leg)
T1_LEGS = {"KR0073": (70.1, 56.8), "KR0002": (43.8, 53.1), "KR1000": (94.0, 205.1), "KR0104": (48.5, 72.7),
           "KR0083": (17.3, 42.1), "KR0071": (11.7, 81.4), "KR0005": (62.4, None), "KR0011": (0.0, 151.6),
           "KR0097": (0.0, 238.2)}
UNDETERMINED = {"KR1000", "KR0104", "KR0083", "KR0071"}


def fnum(v):
    if v in (None, ""):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def eq(a, b, tol=0.051):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= tol


def head_json(rel):
    raw = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=REPO, capture_output=True, check=True).stdout
    return json.loads(raw.decode("utf-8"))


def main() -> int:
    t1 = {r["code"]: r for r in json.loads((REPO / "kics_tier1_utilization.json").read_text(encoding="utf-8"))["results"]}
    t2 = {r["code"]: r for r in json.loads((REPO / "kics_tier2_utilization.json").read_text(encoding="utf-8"))["results"]}
    with MEMO.open(encoding="utf-8-sig", newline="") as fh:
        memo = {r["code"]: r for r in csv.DictReader(fh)}
    out = [f"memo rows={len(memo)} · new tier1 rows={len(t1)} · new tier2 rows={len(t2)}"]
    diffs = []
    for code in sorted(set(memo) | set(t1) | set(t2)):
        m, a, b = memo.get(code, {}), t1.get(code, {}), t2.get(code, {})
        checks = [
            ("t2 rule", m.get("t2_rule"), b.get("rule"), m.get("t2_rule") == b.get("rule")),
            ("t2 numerator", fnum(m.get("t2_num_reg")), b.get("numerator_eok"), eq(fnum(m.get("t2_num_reg")), b.get("numerator_eok"), 0.011)),
            ("t2 pct", fnum(m.get("t2_pct_reg")), b.get("utilization_pct"), eq(fnum(m.get("t2_pct_reg")), b.get("utilization_pct"))),
            ("t2 numerator_tfi_off", fnum(m.get("t2_num_tfi_off")), b.get("numerator_tfi_off_eok"),
             eq(fnum(m.get("t2_num_tfi_off")), b.get("numerator_tfi_off_eok"), 0.011)),
            ("t2 pct_tfi_off", fnum(m.get("t2_pct_tfi_off")), b.get("utilization_pct_tfi_off"),
             eq(fnum(m.get("t2_pct_tfi_off")), b.get("utilization_pct_tfi_off"))),
            ("t2 limit", fnum(m.get("tier2_limit_scr50")), b.get("tier2_limit_eok"), eq(fnum(m.get("tier2_limit_scr50")), b.get("tier2_limit_eok"), 0.011)),
            ("item47 scope", m.get("gate_item47_scope"), b.get("item47_scope"), m.get("gate_item47_scope") == b.get("item47_scope")),
            ("t1 pct (memo §3.2 final)", T1_MEMO.get(code, 0.0), a.get("utilization_pct"), eq(T1_MEMO.get(code, 0.0), a.get("utilization_pct"))),
        ]
        if code in T1_LEGS:
            lg, nw = T1_LEGS[code]
            checks.append(("t1 legacy leg", lg, a.get("tier1_legacy_pct"), eq(lg, a.get("tier1_legacy_pct"))))
            if nw is not None:
                checks.append(("t1 basic-new leg", nw, a.get("tier1_basic_new_pct"), eq(nw, a.get("tier1_basic_new_pct"))))
        if code in UNDETERMINED:
            upper = fnum(m.get("t1_pct_binding"))
            checks.append(("t1 = memo CSV upper bound (t1_pct_binding)", upper, a.get("utilization_pct"), eq(upper, a.get("utilization_pct"))))
        bad = [c for c in checks if not c[3]]
        name = (m.get("name") or a.get("company") or b.get("company") or "")[:10]
        out.append(f"{code} {name:10s} {'OK ' if not bad else 'DIFF'} | T2 {b.get('rule')} {b.get('utilization_pct')} "
                   f"(memo {m.get('t2_rule')} {m.get('t2_pct_reg')}) | T1 {a.get('utilization_pct')} "
                   f"(memo {T1_MEMO.get(code, 0.0)}) leg={a.get('binding_leg')} unconfirmed={a.get('type_unconfirmed')}")
        for c in bad:
            out.append(f"     DIFF {c[0]}: memo={c[1]!r} new={c[2]!r}")
            diffs.append((code, c[0], c[1], c[2]))
    out.append("")
    out.append(f"SUMMARY: companies={len(set(memo) | set(t1) | set(t2))} · differing checks={len(diffs)} · "
               f"companies with a difference={len({d[0] for d in diffs})}")
    (HERE / "a7_memo_diff.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))

    # ---- before/after vs HEAD ----
    h1 = {r["code"]: r for r in head_json("kics_tier1_utilization.json")["results"]}
    h2 = {r["code"]: r for r in head_json("kics_tier2_utilization.json")["results"]}
    rows = []
    for code in sorted(set(t1) | set(t2)):
        for tier, new, old in (("tier1", t1.get(code, {}), h1.get(code, {})), ("tier2", t2.get(code, {}), h2.get(code, {}))):
            num_key = "tier1_hybrid_recognized_eok" if tier == "tier1" else "numerator_eok"
            lim_key = "tier1_hybrid_limit_eok" if tier == "tier1" else "tier2_limit_eok"
            rows.append({
                "code": code, "company": new.get("company") or old.get("company"), "tier": tier,
                "pct_before": old.get("utilization_pct"), "pct_after": new.get("utilization_pct"),
                "changed": "Y" if old.get("utilization_pct") != new.get("utilization_pct") else "",
                "numerator_before": old.get(num_key), "numerator_after": new.get(num_key),
                "limit_before": old.get(lim_key), "limit_after": new.get(lim_key),
                "rule_or_binding_leg": new.get("rule") if tier == "tier2" else new.get("binding_leg"),
                "type_unconfirmed": new.get("type_unconfirmed") if tier == "tier1" else "",
                "reason": new.get("reason") if tier == "tier2" else "",
                "numerator_source_or_type_note": new.get("numerator_source") if tier == "tier2" else new.get("type_note"),
            })
    with (HERE / "b1_before_after_47.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    n1 = sum(1 for r in rows if r["tier"] == "tier1" and r["changed"])
    n2 = sum(1 for r in rows if r["tier"] == "tier2" and r["changed"])
    print(f"\nbefore/after: tier1 pct changed {n1} · tier2 pct changed {n2} -> b1_before_after_47.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
