import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")

from scripts.fetch_dart_fs import _parse, ACCT_OCI  # noqa: E402

print("ACCT_OCI[26] =", ACCT_OCI[26])

d = json.loads(Path("data/dart/_fs_api_cache/00104069_2026_11012_OFS.json").read_text(encoding="utf-8"))
t1 = _parse(d, annual=False)
print("fresh t1 item26 =", t1.get(26))
print("fresh t1 item25 =", t1.get(25))
print("fresh t1 item27-30 =", [t1.get(n) for n in (27, 28, 29, 30)])
print("fresh t1 item32 =", t1.get(32))
print("fresh t1 _oci32_src =", t1.get("_oci32_src"))
