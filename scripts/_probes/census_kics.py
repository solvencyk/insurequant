# -*- coding: utf-8 -*-
"""Census probe for kics_disclosure.json (read-only): row count, set of
(원보험사코드, 공시분기, 항목번호) combos, and a hash of every field EXCEPT 값_적용후 (so
before/after comparisons can prove nothing but 값_적용후 moved). Writes a snapshot file so two
runs can be diffed. Not part of the pipeline -- one-off verification for inbox ticket
20260821T1030Z.
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
TARGET = REPO / "kics_disclosure.json"


def main() -> int:
    out_path = sys.argv[1] if len(sys.argv) > 1 else None
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    combos = set()
    non_after_hash = hashlib.sha256()
    after_values = {}
    for r in data:
        c, q, it = r["원보험사코드"], r["공시분기"], int(r["항목번호"])
        key = (c, q, it)
        if key in combos:
            print(f"DUPLICATE combo: {key}")
        combos.add(key)
        frozen = {k: v for k, v in sorted(r.items()) if k != "값_적용후"}
        non_after_hash.update(json.dumps(frozen, ensure_ascii=False, sort_keys=True).encode("utf-8"))
        after_values[key] = r.get("값_적용후")

    print(f"rows={len(data)} combos={len(combos)} non_after_sha256={non_after_hash.hexdigest()}")

    if out_path:
        snap = {
            "rows": len(data),
            "combos": sorted(f"{c}|{q}|{it}" for c, q, it in combos),
            "non_after_sha256": non_after_hash.hexdigest(),
            "after_values": {f"{c}|{q}|{it}": v for (c, q, it), v in after_values.items()},
        }
        Path(out_path).write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
