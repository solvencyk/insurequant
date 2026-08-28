import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")

from scripts.fetch_dart_fs import _parse  # noqa: E402

CASES = [
    ("koreanre_2024.3Q", "data/dart/_fs_api_cache/00113191_2024_11014_OFS.json", False),
    ("fubon_2024.3Q", "data/dart/_fs_api_cache/00459844_2024_11014_OFS.json", False),
]

for label, path, annual in CASES:
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    t1 = _parse(d, annual)
    print(f"\n=== {label} ===")
    if t1 is None:
        print("  _parse returned None")
        continue
    for n in (25, 26, 27, 28, 29, 30, 31, 32):
        print(f"  item{n}: {t1.get(n)}")
    prov = t1.get("_oci32_src")
    print(f"  _oci32_src ({len(prov) if prov is not None else 0} rows):")
    for p in (prov or []):
        print(f"     {p}")
    # identity check: 25 == 26+27+28+29+30+32 (only if all present)
    parts = [t1.get(n) for n in (26, 27, 28, 29, 30, 32)]
    if t1.get(25) is not None and all(p is not None for p in parts):
        resid = t1[25] - sum(parts)
        print(f"  25 - sum(26..30,32) = {resid:.6f}  (25={t1[25]})")
