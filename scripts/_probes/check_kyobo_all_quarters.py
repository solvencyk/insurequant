import glob
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")

from scripts.fetch_dart_fs import _parse  # noqa: E402

files = sorted(glob.glob("data/dart/_fs_api_cache/00112882_*_OFS.json"))
for f in files:
    m = re.search(r"00112882_(\d{4})_(\d{5})_OFS", f)
    year, reprt = m.group(1), m.group(2)
    annual = reprt == "11011"
    d = json.loads(Path(f).read_text(encoding="utf-8"))
    t1 = _parse(d, annual)
    if t1 is None or 25 not in t1:
        print(f"{f}: no item25")
        continue
    parts = [t1.get(n) for n in (26, 27, 28, 29, 30, 32)]
    line = f"{f}: item25={t1.get(25)}  item28={t1.get(28)}  item32={t1.get(32)}"
    if all(p is not None for p in parts):
        resid = t1[25] - sum(parts)
        line += f"  resid={resid:.6f}"
    print(line)
    for p in (t1.get("_oci32_src") or []):
        print("     prov:", p)
