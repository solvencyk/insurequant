import json
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
d = json.load(open("data/_derived/asset_quality_diagnostics.json", encoding="utf-8"))
for r in d:
    print(json.dumps(r, ensure_ascii=False, indent=2))
