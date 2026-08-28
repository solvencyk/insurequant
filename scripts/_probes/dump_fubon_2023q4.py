import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")

from scripts.fetch_dart_fs import _parse  # noqa: E402

d = json.loads(Path("data/dart/_fs_api_cache/00459844_2023_11011_OFS.json").read_text(encoding="utf-8"))
t1 = _parse(d, annual=True)
for n in (25, 26, 27, 28, 29, 30, 31, 32):
    print(f"item{n}: {t1.get(n)}")
print("_oci32_src:")
for p in (t1.get("_oci32_src") or []):
    print("  ", p)
