"""Apply data/_derived/_patch_2026q2_KR1000.json onto a SCRATCH copy of
kics_disclosure.json (never the live root file), reusing apply_2026q2_patches.apply_patch.
"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import apply_2026q2_patches as ap  # noqa: E402

SCRATCH_DIR = Path(
    r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant"
    r"\a2eaf685-d24e-438d-8f71-52ff9b5cfb3b\scratchpad"
)
SRC = SCRATCH_DIR / "kr1000_after.json"
PATCH = ROOT / "data" / "_derived" / "_patch_2026q2_KR1000.json"

rows = json.loads(SRC.read_text(encoding="utf-8"))
before_n = len(rows)
patch = json.loads(PATCH.read_text(encoding="utf-8"))

rows2, stats = ap.apply_patch(rows, patch, dry=False)
print(f"{patch['company_code']} {patch['quarter']}: +{stats['added']} 신규 · "
      f"{stats['updated']} 갱신 · {stats['skipped']} 변화없음"
      + (f" · 오류 {len(stats['errors'])}" if stats["errors"] else ""))
for e in stats["errors"]:
    print(f"    ERROR {e}")

if stats["errors"]:
    print("errors present -- not writing")
    raise SystemExit(2)

print(f"rows {before_n} -> {len(rows2)}")
SRC.write_text(json.dumps(rows2, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"wrote {SRC}")
