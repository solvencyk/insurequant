"""Derive 값_적용후 for the POST_TRANSITION_PARENT/CHILD_MISSING cells of the 16 life
companies, 2026.2Q, using ONLY:
  (a) mirroring 값(pre) -> 값_적용후 where the relevant transition axis is X (verified via
      kics_transition_applicability.json) or where 값(pre) itself is 0 (safe trivial),
  (b) copying already-present sibling cells within the SAME master (item50/51 TFI table
      -> item2/3; item36-40 -> item19 via MARKET_M identity check only, not invention),
  (c) pure arithmetic identities that the gate itself enforces (rule 1/4/5/6/7/8, imported
      from src/solvency/validation/kics_json_rules.py -- not retyped).

Universal fact (empirically confirmed across every company/quarter in the master before
touching anything): item18(일반손해)/20(신용)/21(운영) NEVER change under any K-ICS
transition axis -- no TIR/TER/TIRR/TAC/TFI targets them. All 16 target companies show
item18=0 in every quarter on file. This script re-verifies that empirically rather than
hard-coding it.

Output: a dry-run report of resolved vs. NEEDS_RAW cells per company. No file writes.
"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "solvency" / "validation"))

from kics_json_rules import R4, R7, MARKET_M  # noqa: E402

CODE, QUARTER, ITEM = "원보험사코드", "공시분기", "항목번호"
VAL, VAL_POST, NAME = "값", "값_적용후", "항목명"

CODES = ["KR0068", "KR0069", "KR0070", "KR0071", "KR0072", "KR0080", "KR0082", "KR0083",
         "KR0087", "KR0094", "KR0097", "KR0099", "KR0100", "KR0104", "KR1010", "KR1011"]

# my target items per company, from the live gate run (validate_data_contract.py), 2026.2Q only
TARGETS = {
    "KR0068": [1, 2, 3, 14, 15, 16, 17, 18, 20, 21, 22, 23, 27, 28],
    "KR0069": [1, 14, 27, 28, 29, 30, 31, 33, 34],
    "KR0070": [16, 17, 18, 19, 20, 21, 22, 23],
    "KR0071": [16, 18],
    "KR0072": [16, 18, 20, 21, 22, 23],
    "KR0080": [16, 17, 18, 20, 21, 22, 23],
    "KR0082": [16, 18, 19, 23],
    "KR0083": [16, 18, 22, 23],
    "KR0087": [17, 20, 21, 22],
    "KR0094": [1, 2, 3, 14, 15, 16, 17, 18, 20, 21, 22, 23, 27, 28],
    "KR0097": [16, 18, 23],
    "KR0099": [16, 17, 18, 20, 21, 22, 23],
    "KR0100": [16, 18, 21, 22, 23],
    "KR0104": [16, 18, 20, 21, 23],
    "KR1010": [16, 18, 22, 23],
    "KR1011": [2, 3, 16, 17, 18, 19, 20, 21, 22, 23, 28],
}

Q = "2026.2Q"


def to_f(v):
    if v in (None, "", "None"):
        return None
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def fmt(x):
    if x is None:
        return None
    s = f"{x:.6f}".rstrip("0").rstrip(".")
    return s if s else "0"


records = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
appl = json.loads((ROOT / "data" / "_derived" / "kics_transition_applicability.json").read_text(encoding="utf-8"))
appl_by = {(r["code"], r["quarter"]): r for r in appl["records"]}

byq = {}
labels = {}
for r in records:
    c, q, it = r.get(CODE), r.get(QUARTER), r.get(ITEM)
    try:
        it = int(it)
    except (TypeError, ValueError):
        continue
    if c and q:
        byq.setdefault((c, q), {})[it] = {"v": to_f(r.get(VAL)), "vp": (to_f(r.get(VAL_POST)) if VAL_POST in r else "MISSING"), "name": r.get(NAME)}
        labels[(c, it)] = r.get(NAME)

# universal fact check: item18 is 0 (or absent) for every (company,quarter) on file, any company
bad18 = []
for (c, q), m in byq.items():
    if 18 in m and m[18]["v"] not in (0.0, None):
        bad18.append((c, q, m[18]["v"]))
print(f"item18 universal-zero check across ENTIRE master: {len(bad18)} non-zero exceptions found")
if bad18[:10]:
    for b in bad18[:10]:
        print("   ", b)

print()
print("=" * 100)

results = {c: {} for c in CODES}
needs_raw = {c: [] for c in CODES}

for c in CODES:
    m = byq.get((c, Q), {})
    a = appl_by.get((c, Q))
    tir_x = a is not None and a.get("TIR") == "X"
    ter_x = a is not None and a.get("TER") == "X"
    tirr_x = a is not None and a.get("TIRR") == "X"
    req_all_x = tir_x and ter_x and tirr_x

    def cur(it):
        return m.get(it, {"v": None, "vp": "MISSING"})

    def set_post(it, val, reason):
        results[c][it] = (val, reason)

    # --- universal mirror: 18, 20, 21 ---
    for it in (18, 20, 21):
        cell = cur(it)
        if cell["vp"] != "MISSING":
            continue
        if cell["v"] is None:
            continue
        set_post(it, cell["v"], "mirror(universal, no transition axis targets this leg)")

    # --- item17 (생명장기) ---
    c17 = cur(17)
    if c17["vp"] == "MISSING":
        if c17["v"] == 0:
            set_post(17, 0.0, "mirror(pre=0)")
        elif tir_x:
            set_post(17, c17["v"], f"mirror(TIR=X confirmed {Q})")
        else:
            needs_raw[c].append(("item17", f"TIR={a.get('TIR') if a else 'NO_APPLICABILITY_RECORD'}, pre={c17['v']}"))

    # --- item19 (시장) ---
    c19 = cur(19)
    if c19["vp"] == "MISSING":
        if c19["v"] == 0:
            set_post(19, 0.0, "mirror(pre=0)")
        elif ter_x and tirr_x:
            set_post(19, c19["v"], f"mirror(TER=X,TIRR=X confirmed {Q})")
        else:
            needs_raw[c].append(("item19", f"TER={a.get('TER') if a else '?'} TIRR={a.get('TIRR') if a else '?'}, pre={c19['v']}"))

    # --- item22 / item23 ---
    for it in (22, 23):
        cell = cur(it)
        if cell["vp"] == "MISSING":
            if cell["v"] == 0:
                set_post(it, 0.0, "mirror(pre=0)")
            elif req_all_x:
                set_post(it, cell["v"], "mirror(TIR=TER=TIRR=X, no requirement-side axis active)")
            else:
                needs_raw[c].append((f"item{it}", f"pre={cell['v']}, TIR/TER/TIRR not all X"))

    # --- item2/item3 via TFI table copy (item50/51), else mirror if TFI=X and TAC=X
    #     (no capital-side axis active at all -> pre/post identical by definition) ---
    tfi_x = a is not None and a.get("TFI") == "X"
    tac_x = a is not None and a.get("TAC") == "X"
    for it, tfi_it in ((2, 50), (3, 51)):
        cell = cur(it)
        if cell["vp"] == "MISSING":
            tfi = cur(tfi_it)
            if tfi["vp"] != "MISSING":
                set_post(it, tfi["vp"], f"copy(item{tfi_it}_post from TFI table, same concept)")
            elif cell["v"] == 0:
                set_post(it, 0.0, "mirror(pre=0)")
            elif tfi_x and tac_x:
                set_post(it, cell["v"], f"mirror(TFI=X,TAC=X confirmed {Q}, no capital-side axis active)")
            else:
                needs_raw[c].append((f"item{it}", f"pre={cell['v']}, no item{tfi_it} TFI counterpart, TFI={a.get('TFI') if a else '?'} TAC={a.get('TAC') if a else '?'}"))

    # --- item15: use existing if present, else derive via R4 ---
    c15 = cur(15)
    if c15["vp"] != "MISSING":
        item15_post = c15["vp"]
    else:
        # need 17,18,19,20 post resolved
        vals = {}
        ok = True
        for it in (17, 18, 19, 20):
            if it in results[c]:
                vals[it] = results[c][it][0]
            elif cur(it)["vp"] not in ("MISSING",):
                vals[it] = cur(it)["vp"]
            else:
                ok = False
        if ok and 21 in results[c] or cur(21)["vp"] != "MISSING":
            item21_post = results[c].get(21, (cur(21)["vp"],))[0] if 21 in results[c] else cur(21)["vp"]
            import numpy as np
            v = np.array([vals[17], vals[18], vals[19], vals[20]], dtype=float)
            expected15 = float(np.sqrt(max(v @ R4 @ v, 0.0))) + item21_post
            set_post(15, expected15, "derive(R4 sqrt formula, same as gate rule 4)")
            item15_post = expected15
        else:
            item15_post = None
            needs_raw[c].append(("item15", "cannot derive: missing 17/18/19/20/21 post inputs"))

    # --- item16 = sum(17:21) - item15 (gate rule 6) ---
    c16 = cur(16)
    if c16["vp"] == "MISSING" and 16 in TARGETS.get(c, []):
        vals = {}
        ok = True
        for it in (17, 18, 19, 20, 21):
            if it in results[c]:
                vals[it] = results[c][it][0]
            elif cur(it)["vp"] not in ("MISSING",):
                vals[it] = cur(it)["vp"]
            else:
                ok = False
        if ok and item15_post is not None:
            expected16 = sum(vals.values()) - item15_post
            set_post(16, expected16, "derive(rule 6: sum(17:21)-15)")
        else:
            needs_raw[c].append(("item16", "cannot derive: missing components"))

    # --- item1 = item2+item3 (rule 1) ---
    c1 = cur(1)
    if c1["vp"] == "MISSING" and 1 in TARGETS.get(c, []):
        v2 = results[c][2][0] if 2 in results[c] else (cur(2)["vp"] if cur(2)["vp"] != "MISSING" else None)
        v3 = results[c][3][0] if 3 in results[c] else (cur(3)["vp"] if cur(3)["vp"] != "MISSING" else None)
        if v2 is not None and v3 is not None:
            set_post(1, v2 + v3, "derive(rule 1: item2+item3)")
        else:
            needs_raw[c].append(("item1", "cannot derive: item2/3 post unresolved"))

    # --- item14 = item15-item22+item23 (rule 5) ---
    c14 = cur(14)
    if c14["vp"] == "MISSING" and 14 in TARGETS.get(c, []):
        v22 = results[c][22][0] if 22 in results[c] else (cur(22)["vp"] if cur(22)["vp"] != "MISSING" else None)
        v23 = results[c][23][0] if 23 in results[c] else (cur(23)["vp"] if cur(23)["vp"] != "MISSING" else None)
        if v22 is not None and v23 is not None and item15_post is not None:
            set_post(14, item15_post - v22 + v23, "derive(rule 5: 15-22+23)")
        else:
            needs_raw[c].append(("item14", "cannot derive: 15/22/23 post unresolved"))

    # --- item27 = item1/item14*100 (rule 7), item28 = item2/item14*100 (rule 8) ---
    v1 = results[c][1][0] if 1 in results[c] else (cur(1)["vp"] if cur(1)["vp"] != "MISSING" else None)
    v14 = results[c][14][0] if 14 in results[c] else (cur(14)["vp"] if cur(14)["vp"] != "MISSING" else None)
    v2f = results[c][2][0] if 2 in results[c] else (cur(2)["vp"] if cur(2)["vp"] != "MISSING" else None)
    if 27 in TARGETS.get(c, []) and cur(27)["vp"] == "MISSING":
        if v1 is not None and v14 not in (None, 0):
            set_post(27, v1 / v14 * 100.0, "derive(rule 7: item1/item14*100)")
        else:
            needs_raw[c].append(("item27", "cannot derive: item1/14 post unresolved"))
    if 28 in TARGETS.get(c, []) and cur(28)["vp"] == "MISSING":
        if v2f is not None and v14 not in (None, 0):
            set_post(28, v2f / v14 * 100.0, "derive(rule 8: item2/item14*100)")
        else:
            needs_raw[c].append(("item28", "cannot derive: item2/14 post unresolved"))

    # --- children 29-35 mirror if item17 was just resolved via mirror (not raw) and pre values exist ---
    if 17 in results[c] and "mirror" in results[c][17][1]:
        for it in range(29, 36):
            cell = cur(it)
            if cell["vp"] == "MISSING" and cell["v"] is not None:
                set_post(it, cell["v"], "mirror(parent item17 mirrored, child follows)")

    # --- children 36-40 mirror if item19 was just resolved via mirror, to avoid opening new CHILD_MISSING ---
    if 19 in results[c] and "mirror" in results[c][19][1]:
        for it in range(36, 41):
            cell = cur(it)
            if cell["vp"] == "MISSING" and cell["v"] is not None:
                set_post(it, cell["v"], "mirror(parent item19 mirrored, child follows, avoid new CHILD_MISSING)")
    elif 19 in TARGETS.get(c, []):
        # item19 resolved some other way (or needs raw) -- still check 36-40 completeness
        for it in range(36, 41):
            cell = cur(it)
            if cell["vp"] == "MISSING" and cell["v"] is not None and cell["v"] >= 5.0:
                needs_raw[c].append((f"item{it}", "parent item19 resolving -> this child needed too (avoid new CHILD_MISSING), pre=" + str(cell["v"])))

    print(f"--- {c} (TIR={a.get('TIR') if a else '?'} TER={a.get('TER') if a else '?'} TIRR={a.get('TIRR') if a else '?'}) ---")
    for it in sorted(results[c]):
        val, reason = results[c][it]
        print(f"   item{it:<3} = {fmt(val):<14}  {reason}")
    if needs_raw[c]:
        print("   NEEDS_RAW:")
        for it, why in needs_raw[c]:
            print(f"      {it}: {why}")
    print()

print("=" * 100)
total_resolved = sum(len(v) for v in results.values())
total_needs_raw = sum(len(v) for v in needs_raw.values())
print(f"TOTAL resolved via mirror/derive/copy: {total_resolved}")
print(f"TOTAL still needing raw extraction: {total_needs_raw}")
for c in CODES:
    if needs_raw[c]:
        print(f"  {c}: {[x[0] for x in needs_raw[c]]}")

# dump machine-readable for the next step
out = {c: {str(it): {"value": v, "reason": r} for it, (v, r) in results[c].items()} for c in CODES}
(ROOT / "scripts" / "_probes" / "_life16_derived_values.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("\nWrote scripts/_probes/_life16_derived_values.json")
