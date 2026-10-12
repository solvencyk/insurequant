"""probe_public_export_drift.py (parser-kics, ticket 20261012T1030Z) -- READ ONLY.
Lists every PUBLIC_EXPORT_* finding of scripts/validate_live_artifacts.py::check_public_exports (default out_dir, nothing written)
so we can see whether a K-ICS public export (기본자본소진율 / 보완자본소진율 / 자본비율전망 ...) drifted because of the kics_disclosure.json change.
"""
import io
import sys
from pathlib import Path

REPO = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
sys.path.insert(0, str(REPO / "scripts"))
import validate_live_artifacts as L  # noqa: E402

fd = L.Findings()
L.check_public_exports(fd)
print("PUBLIC_EXPORT findings:", len(fd.rows))
for r in fd.rows:
    print(f"- {r['artifact']} | {r['rule']} | {r['key']} | {r['detail'][:260]}")
