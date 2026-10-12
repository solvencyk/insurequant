"""a0c: first differing lines between kics_tier1_utilization.json on disk and json.dumps(indent=2) of it (read-only)."""
from __future__ import annotations

import difflib
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[3]


def main() -> int:
    for rel in ("kics_tier1_utilization.json", "kics_tier2_utilization.json"):
        raw = (REPO / rel).read_text(encoding="utf-8")
        new = json.dumps(json.loads(raw), ensure_ascii=False, indent=2) + "\n"
        d = list(difflib.unified_diff(raw.splitlines(), new.splitlines(), lineterm="", n=1))
        print(f"== {rel}: {len(d)} diff lines; first 30:")
        print("\n".join(d[:30]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
