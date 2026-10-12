"""a0b: does json.dumps(indent=2, ensure_ascii=False) + '\\n' reproduce the four tier JSONs byte-for-byte? (read-only)

The writer in scripts/apply_disclosure_utilization.py uses that format; if the files on disk were last written in
another format, the first apply run would show a whole-file diff that has nothing to do with the values.

Run (repo root):
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_utilization_apply_20261012/a0b_roundtrip_check.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[3]
FILES = ["kics_tier1_utilization.json", "kics_tier2_utilization.json",
         "output/tier1_utilization/tier1_utilization_20262Q.json",
         "output/tier2_utilization/tier2_utilization_20262Q.json"]


def main() -> int:
    for rel in FILES:
        raw = (REPO / rel).read_bytes()
        doc = json.loads(raw.decode("utf-8"))
        for indent in (2, 1):
            for tail in ("\n", ""):
                if (json.dumps(doc, ensure_ascii=False, indent=indent) + tail).encode("utf-8") == raw:
                    print(f"{rel}: roundtrip OK with indent={indent} tail={tail!r} crlf={b'\\r\\n' in raw}")
                    break
            else:
                continue
            break
        else:
            print(f"{rel}: NO simple roundtrip (crlf={b'\\r\\n' in raw}, bom={raw[:3] == b'\\xef\\xbb\\xbf'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
