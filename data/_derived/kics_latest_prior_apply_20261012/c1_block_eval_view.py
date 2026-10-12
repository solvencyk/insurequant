"""c1: show what the dry-run gate evaluation recorded for the 17 surviving candidate blocks (READ-ONLY)."""
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
D = "data/_derived/kics_latest_prior_precedence_dryrun_20261012/"
SURV = ["KR0003_2023.4Q", "KR0003_2025.1Q", "KR0004_2023.1Q", "KR0004_2024.1Q", "KR0009_2023.1Q", "KR0009_2023.2Q",
        "KR0032_2024.3Q", "KR0049_2025.1Q", "KR0049_2026.1Q", "KR0050_2025.3Q", "KR0069_2024.2Q", "KR0070_2024.3Q",
        "KR0071_2024.4Q", "KR0072_2025.2Q", "KR0080_2026.1Q", "KR0095_2024.4Q", "KR0099_2024.3Q"]
ev = {}
for ln in open(D + "block_eval.jsonl", encoding="utf-8"):
    r = json.loads(ln)
    ev[r["id"]] = r
for b in SURV:
    r = ev[b]
    print("=" * 100)
    print(b, "edits", r["n_cell_edits"], "derived", r["n_derived"], "| base RED in bucket:", sorted(r["base_bucket_red"]), "-> cand:", sorted(r["cand_bucket_red"]))
    for d in r["derived"]:
        print("   derived:", d["item"], d["field"], d["old"], "->", d["new"])
    for c in r["bucket_changes"]:
        print("   bucket :", c)
    for c in r["neighbour_changes"]:
        print("   nearby :", c)
    for c in r["other_changes"]:
        print("   other  :", c)
    print("   new_extra_red:", r["new_extra_red"], "| new_registry_red:", r["new_registry_red"], "| gone_registry_red:", r["gone_registry_red"])
    print("   status", r["base_status"], "->", r["cand_status"])
