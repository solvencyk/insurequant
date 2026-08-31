import io, json, shutil, sys
from datetime import datetime
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(".").resolve()
MASTER = ROOT / "kics_disclosure.json"
dry = "--dry-run" in sys.argv

patch = json.loads((ROOT / "data/_derived/_patch_2026q2_KR0069.json").read_text(encoding="utf-8"))
whitelist_items = {29, 30, 31, 33, 34}
cells = {c["항목번호"]: c for c in patch["cells"] if c["항목번호"] in whitelist_items}

rows = json.loads(MASTER.read_text(encoding="utf-8"))
idx = {(r.get("원보험사코드"), r.get("공시분기"), int(r.get("항목번호"))): r for r in rows}
before_n = len(rows)
before_snap = {k: (r.get("값"), r.get("값_적용후")) for k, r in idx.items()}

updated = 0
for it, c in cells.items():
    key = ("KR0069", "2026.2Q", it)
    row = idx.get(key)
    assert row is not None, key
    existing = row.get("값_적용후")
    if existing not in (None, "", "None"):
        print(f"SKIP item{it}: already set ({existing!r})")
        continue
    if not dry:
        row["값_적용후"] = c["값_적용후"]
    updated += 1
    print(f"SET item{it} 값_적용후={c['값_적용후']!r}")

# scope audit
outside = []
for k, r in idx.items():
    if k[0] == "KR0069" and k[1] == "2026.2Q" and k[2] in whitelist_items:
        continue
    was = before_snap.get(k)
    now = (r.get("값"), r.get("값_적용후"))
    if was != now:
        outside.append(k)
print(f"updated={updated} outside-scope changes={len(outside)} {outside[:5]} rows={before_n}->{len(rows)}")
if outside or len(rows) != before_n:
    print("ABORT")
    sys.exit(2)
if dry:
    print("(dry-run) not written")
    sys.exit(0)
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy2(MASTER, MASTER.with_suffix(f".json.bak_{stamp}_kr0069children"))
MASTER.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"wrote {MASTER}")
