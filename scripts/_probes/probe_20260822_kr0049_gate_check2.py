# -*- coding: utf-8 -*-
"""Read-only: inspect report_latest.json for KR0049 2024.3Q findings (correct field names)."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPORT = REPO / "artifacts" / "kics_validation" / "report_latest.json"


def main() -> int:
    data = json.loads(REPORT.read_text(encoding="utf-8"))
    findings = data["findings"]
    hits = [f for f in findings if f.get("원보험사코드") == "KR0049" and f.get("공시분기") == "2024.3Q"]
    print(f"total findings for KR0049 2024.3Q: {len(hits)}")
    for f in hits:
        print(f"  rule={f.get('rule'):32s} status={f.get('status'):6s} exp={f.get('expected')!r:>10} act={f.get('actual')!r:>10} detail={f.get('detail','')[:150]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
