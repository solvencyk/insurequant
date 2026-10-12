"""a8: print selected rows of the newly written tier JSONs (read-only) for eyeball review.

Run (repo root):
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_utilization_apply_20261012/a8_show_rows.py KR1010 KR1102 KR0068
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[3]


def main() -> int:
    codes = sys.argv[1:] or ["KR1010", "KR1102", "KR0068"]
    for name in ("kics_tier1_utilization.json", "kics_tier2_utilization.json"):
        doc = json.loads((REPO / name).read_text(encoding="utf-8"))
        print(f"== {name} definition: {json.dumps(doc.get('definition'), ensure_ascii=False, indent=1)}")
        for r in doc["results"]:
            if r["code"] in codes:
                print(json.dumps(r, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
