"""probe_report_shape.py (parser-kics, ticket 20261012T1030Z) -- READ ONLY.
Shows the structure of a gate report JSON (artifacts/kics_validation/report_*.json): top-level keys, one finding, status counts.
usage: probe_report_shape.py REPORT.json
"""
import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
rep = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print("top-level keys:", list(rep))
f = rep["findings"]
print("n findings:", len(f))
print("finding[0] keys:", list(f[0]))
print("finding[0]:", json.dumps(f[0], ensure_ascii=False)[:600])
print("status counts:", Counter(x.get("status") or x.get("상태") for x in f))
print("source:", rep.get("source"), "| generated_at:", rep.get("generated_at"))
