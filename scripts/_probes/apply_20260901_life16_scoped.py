"""Scoped applier for the POST_TRANSITION_PARENT/CHILD_MISSING fix, 16 life companies,
2026.2Q. Unlike the generic apply_2026q2_patches.py (which applies EVERY cell in a
company's patch file, including other sessions' unrelated staged work), this only
touches the exact (company, item) whitelist this session resolved -- everything else
in those patch files is left untouched for whoever owns it.

UPSERT semantics: only sets 값_적용후 (never 값, never touches other fields). Refuses to
overwrite a cell that already has a non-null 값_적용후 in the live master (merge, not
clobber). Backs up the master before writing. Reports scope-audit (rows/combos unchanged
outside the whitelist) before AND after.
"""
import io
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "kics_disclosure.json"

CODE, QUARTER, ITEM = "원보험사코드", "공시분기", "항목번호"
VAL, VAL_POST, NAME = "값", "값_적용후", "항목명"
Q = "2026.2Q"

WHITELIST = {
    "KR0068": [1, 2, 3, 14, 15, 16, 17, 18, 20, 21, 22, 23, 27, 28, 29, 30, 31, 32, 33, 34, 35],
    "KR0069": [1, 14, 27, 28],
    "KR0070": [16, 17, 18, 19, 20, 21, 22, 23],
    "KR0071": [16, 18],
    "KR0072": [16, 18, 20, 21, 22, 23],
    "KR0080": [16, 17, 18, 20, 21, 22, 23, 29, 30, 31, 32, 33, 34, 35],
    "KR0082": [16, 18, 19, 23, 36],
    "KR0083": [16, 18, 22, 23],
    "KR0087": [17, 20, 21, 22, 35],
    "KR0094": [1, 2, 3, 14, 15, 16, 17, 18, 20, 21, 22, 23, 27, 28],
    "KR0097": [16, 18, 23],
    "KR0099": [16, 17, 18, 20, 21, 22, 23],
    "KR0100": [16, 18, 21, 22, 23],
    "KR0104": [16, 18, 20, 21, 23],
    "KR1010": [16, 18, 22, 23],
    "KR1011": [2, 3, 16, 17, 18, 19, 20, 21, 22, 23, 28, 36],
}

dry_run = "--dry-run" in sys.argv

final = json.loads((ROOT / "scripts" / "_probes" / "_life16_final_values.json").read_text(encoding="utf-8"))

rows = json.loads(MASTER.read_text(encoding="utf-8"))
rows = rows if isinstance(rows, list) else rows.get("records", rows)


def key_of(r):
    return (r.get(CODE), r.get(QUARTER), r.get(ITEM))


idx = {}
for r in rows:
    c, q, it = r.get(CODE), r.get(QUARTER), r.get(ITEM)
    try:
        it_i = int(it)
    except (TypeError, ValueError):
        it_i = it
    idx[(c, q, it_i)] = r

before_snapshot = {key_of(r): (r.get(VAL), r.get(VAL_POST)) for r in rows}
before_n = len(rows)
before_combos = {key_of(r) for r in rows}

stats = {"updated": 0, "skipped_already_set": 0, "missing_row": []}
touched_keys = set()

for c, items in WHITELIST.items():
    for it in items:
        val = final[c][str(it)]["value"]
        key = (c, Q, it)
        touched_keys.add(key)
        row = idx.get(key)
        if row is None:
            stats["missing_row"].append(key)
            continue
        existing = row.get(VAL_POST)
        existing_num = None
        if existing not in (None, "", "None"):
            try:
                existing_num = float(str(existing).replace(",", ""))
            except ValueError:
                existing_num = None
        if existing_num is not None:
            stats["skipped_already_set"] += 1
            print(f"  SKIP {c} item{it}: 값_적용후 already set ({existing!r}) -- merge policy, not overwriting")
            continue
        # format to match sibling precision convention: integer if it lands on one, else 4dp trimmed
        r_val = round(val, 6)
        if abs(r_val - round(r_val)) < 1e-6:
            fmt_val = str(int(round(r_val)))
        else:
            fmt_val = f"{r_val:.4f}".rstrip("0").rstrip(".")
        if not dry_run:
            row[VAL_POST] = fmt_val
        stats["updated"] += 1

print(f"\n{'DRY-RUN ' if dry_run else ''}updated={stats['updated']} skipped_already_set={stats['skipped_already_set']} missing_row={stats['missing_row']}")

# scope audit: nothing outside the whitelist keys changed
after_combos = {key_of(r) for r in rows}
drift_removed = before_combos - after_combos
drift_added = after_combos - before_combos
outside_value_changes = []
for r in rows:
    k = key_of(r)
    if k in touched_keys:
        continue
    was = before_snapshot.get(k)
    now = (r.get(VAL), r.get(VAL_POST))
    if was is not None and was != now:
        outside_value_changes.append(k)

print(f"combos removed: {len(drift_removed)}  combos added: {len(drift_added)} {sorted(drift_added)[:5]}")
print(f"value changes OUTSIDE whitelist: {len(outside_value_changes)} {outside_value_changes[:10]}")
print(f"row count: {before_n} -> {len(rows)}")

if drift_removed or outside_value_changes or len(rows) != before_n:
    print("\nABORT: out-of-scope change detected, not writing.")
    sys.exit(2)

if dry_run:
    print("\n(dry-run) not written.")
    sys.exit(0)

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = MASTER.with_suffix(f".json.bak_{stamp}_posttrans_life16")
shutil.copy2(MASTER, backup)
MASTER.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"\nwrote {MASTER} (backup: {backup.name})")
