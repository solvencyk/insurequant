"""a1: per-candidate detail for the apply ticket (READ-ONLY). Joins block_verdicts (ticket_category == 채택 후보) with conflict_blocks.json."""
import csv, io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
D = "data/_derived/kics_latest_prior_precedence_dryrun_20261012/"
rows = list(csv.DictReader(open(D + "block_verdicts.csv", encoding="utf-8-sig")))
cand = [r for r in rows if r["ticket_category"] == "채택 후보"]
cb = {(b["code"], b["quarter"]): b for b in json.load(open(D + "conflict_blocks.json", encoding="utf-8"))}
for r in cand:
    b = cb[(r["code"], r["quarter"])]
    plan = json.load(open(D + "plans/" + r["id"] + ".json", encoding="utf-8"))
    print("=" * 110)
    print(r["id"], r["company"], "| applier", b["applier"], "| even", b["even"], "| tier", b.get("tier"), "| status", b["status"])
    print("  flags:", b["flags"])
    print("  diffs:", [(d["item"], d["master"], d["latest"]) for d in b["diffs"]])
    print("  own_dev:", b["own_dev"])
    print("  l1_vs_l2:", b["l1_vs_l2"])
    print("  q statuses: own", b["own_status"], "q1", b["q1_status"], "q2", b["q2_status"], "| latest", b["latest_label"])
    print("  latest_src:", b["latest_src"], "| own_src:", b["own_src"])
    print("  post_mirrored:", b.get("post_mirrored_items"), "post_indep:", b.get("post_independent_items"))
    print("  plan edits:", [(e["item"], e["field"], e["old"], e["new"]) for e in plan["edits"]])
    print("  plan inserts:", len(plan["inserts"]))
