"""Step 1: dump master items needed for capital-utilization re-definition (2026.2Q, read-only).

Writes s1_master_dump.json (code -> item -> {pre, post, raw fields}) and prints field names.
Run (repo root):
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_utilization_definition_20261012/s1_master_dump.py
"""
from __future__ import annotations

import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
Q = sys.argv[1] if len(sys.argv) > 1 else "2026.2Q"
ITEMS = (1, 2, 3, 4, 5, 6, 12, 13, 14, 15, 22, 23, 27, 28, 47, 48, 49, 50, 51, 52, 53, 54)


def main() -> int:
    rows = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
    keys = Counter()
    out: dict[str, dict] = {}
    for r in rows:
        if r.get("공시분기") != Q:
            continue
        keys.update(r.keys())
        it = r.get("항목번호")
        if it not in ITEMS:
            continue
        e = out.setdefault(r["원보험사코드"], {"name": r.get("원수사명"), "items": {}})
        e["items"][str(it)] = {k: v for k, v in r.items() if k not in ("원보험사코드", "원수사명", "공시분기", "항목번호")}
    print("field counts:", dict(keys))
    print("companies:", len(out))
    (HERE / f"s1_master_dump_{Q.replace('.', '')}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    # show one sample company
    for code in ("KR0001", "KR0082", "KR1102"):
        if code in out:
            print(code, out[code]["name"])
            for it in ("3", "6", "13", "14", "47", "48", "49", "51", "53", "54"):
                print("  ", it, out[code]["items"].get(it))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
