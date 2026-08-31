import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
d = json.load(open(ROOT / "management_indicators.json", encoding="utf-8"))
codes = sys.argv[1].split(",") if len(sys.argv) > 1 else None
for r in d:
    if codes and r["원보험사코드"] not in codes:
        continue
    print(r["원보험사코드"], r["공시분기"], r["항목번호"], r["항목명"], r["섹션"], r["값"])
