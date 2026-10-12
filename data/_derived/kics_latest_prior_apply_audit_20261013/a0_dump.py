import csv, io, sys
base = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_apply_20261012/"
out = open("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_apply_audit_20261013/a0_dump.txt", "w", encoding="utf-8")
for fn in ("held_blocks.csv",):
    rows = list(csv.DictReader(open(base + fn, encoding="utf-8-sig")))
    out.write(f"== {fn} {len(rows)}\n")
    for r in rows:
        out.write(" | ".join(f"{k}={v}" for k, v in r.items() if k not in ("hold_reason",)) + "\n")
        out.write("   REASON: " + r["hold_reason"] + "\n")
