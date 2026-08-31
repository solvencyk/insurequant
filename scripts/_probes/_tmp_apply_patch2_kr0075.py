# -*- coding: utf-8 -*-
"""Apply data/_derived/_patch2_2026q2_KR0075.json onto a scratch copy of
kics_disclosure.json (UPSERT by 원보험사코드+공시분기+항목번호). Never touches
the live root file.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
PATCH = REPO / "data" / "_derived" / "_patch2_2026q2_KR0075.json"


def _fmt(x) -> str:
    x = float(x)
    s = f"{x:.2f}"
    if s.endswith("0"):
        s = s.rstrip("0").rstrip(".")
    return s or "0"


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: apply_patch2_kr0075.py <src_json> <dst_json>")
        return 1
    src_path = Path(sys.argv[1])
    dst_path = Path(sys.argv[2])

    data = json.loads(src_path.read_text(encoding="utf-8"))
    patch = json.loads(PATCH.read_text(encoding="utf-8"))
    code = patch["company_code"]
    quarter = patch["quarter"]

    bucket = {r["항목번호"]: r for r in data
              if r.get("원보험사코드") == code and r.get("공시분기") == quarter}
    if not bucket:
        print(f"ABORT: no existing rows for {code} {quarter}")
        return 1
    template = next(iter(bucket.values()))

    changes = []
    for cell in patch["cells"]:
        n = cell["항목번호"]
        val_str = _fmt(cell["값"]) if cell.get("값") is not None else None
        valpost_str = _fmt(cell["값_적용후"]) if cell.get("값_적용후") is not None else None
        row = bucket.get(n)
        if row is None:
            row = {
                "원보험사코드": template["원보험사코드"],
                "원수사명": template["원수사명"],
                "티커": template["티커"],
                "생손보여부": template["생손보여부"],
                "항목번호": n,
                "항목명": cell["항목명"],
                "공시분기": quarter,
            }
            data.append(row)
            bucket[n] = row
            changes.append(f"ADD item{n}")
        else:
            changes.append(
                f"FIX item{n} 값 {row.get('값')!r}->{val_str!r} "
                f"값_적용후 {row.get('값_적용후')!r}->{valpost_str!r}"
            )
        row["항목명"] = cell["항목명"]
        if val_str is not None:
            row["값"] = val_str
        if valpost_str is not None:
            row["값_적용후"] = valpost_str

    dst_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {dst_path} ({len(data)} rows)")
    for c in changes:
        print(" ", c)
    return 0


if __name__ == "__main__":
    sys.exit(main())
