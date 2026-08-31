# -*- coding: utf-8 -*-
import io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("artifacts/kics_validation/report_latest.json", "r", encoding="utf-8") as f:
    r = json.load(f)

keys_to_check = [
    "parent_present_child_incomplete", "parent_present_child_incomplete_after",
    "post_transition_parent_census", "after_parent_missing_child_present",
    "transition_identities_after", "transition_mmult_after", "transition_irr_after",
    "parent_present_child_source_absent_pinned", "coverage_census",
]

def contains_kr0074(obj):
    s = json.dumps(obj, ensure_ascii=False)
    return "KR0074" in s

for k in keys_to_check:
    v = r.get(k)
    if v is None:
        print(f"{k}: KEY ABSENT")
        continue
    if isinstance(v, list):
        hits = [x for x in v if contains_kr0074(x)]
        print(f"{k}: list len={len(v)}, KR0074 hits={len(hits)}")
        for h in hits:
            if isinstance(h, dict) and h.get("공시분기") == "2026.2Q" or (isinstance(h,dict) and h.get("quarter")=="2026.2Q"):
                print("   ", json.dumps(h, ensure_ascii=False)[:500])
    elif isinstance(v, dict):
        s = json.dumps(v, ensure_ascii=False)
        print(f"{k}: dict, contains KR0074 2026.2Q substring: {'KR0074' in s and '2026.2Q' in s}")
        # try common substructures
        for subk in ("missing_rows","findings","rows","items"):
            sv = v.get(subk)
            if isinstance(sv, list):
                hits = [x for x in sv if contains_kr0074(x)]
                if hits:
                    print(f"    .{subk}: {len(hits)} KR0074 hits")
                    for h in hits[:5]:
                        print("      ", json.dumps(h, ensure_ascii=False)[:400])
