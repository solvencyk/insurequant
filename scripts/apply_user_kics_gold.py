# -*- coding: utf-8 -*-
"""Apply data/_gold/user_kics_cells.json to kics_disclosure.json (UPSERT).

Owner hand-transcribed OCR/image-only insurers (미래에셋/AIA/동양/악사 …) in the
review xlsx; build_user_kics_gold.py captured those cells. This re-applies them
AFTER every fill/build so they survive rebuilds. Derived 27/28 are left to
recalc_kics_derived. Generalises apply_kr0010_gold.py to all gold companies.

Run order: fill_period → fill_market_* → apply_user_kics_gold →
           apply_kr0010_gold → recalc_kics_derived → validate.
Usage: PYTHONIOENCODING=utf-8 python scripts/apply_user_kics_gold.py
"""
from __future__ import annotations
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
JSON_PATH = REPO / "kics_disclosure.json"
GOLD = REPO / "data" / "_gold" / "user_kics_cells.json"


def main() -> int:
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    blob = json.loads(GOLD.read_text(encoding="utf-8"))
    meta, names, cells = blob["_meta"], blob["_names"], blob["cells"]
    keys = list(rows[0].keys())
    kcode, kname, ktick, kkind, kitem, kiname, kq, kval = keys[:8]

    # canonical item names from any existing row (fallback to gold-captured name)
    name_by_item = {}
    for r in rows:
        name_by_item.setdefault(str(r[kitem]), r[kiname])

    idx = {(r[kcode], r[kq], str(r[kitem])): r for r in rows}
    n_set = n_post = n_add = 0
    for code, quarters in cells.items():
        for q, items in quarters.items():
            for it, cell in items.items():
                key = (code, q, it)
                row = idx.get(key)
                if row is None:
                    nm = names.get(code, {}).get(it) or name_by_item.get(it, "")
                    m = meta.get(code, {})
                    row = {kcode: code, kname: m.get("원수사명", ""),
                           ktick: m.get("티커", "X"), kkind: m.get("생손보여부", ""),
                           kitem: int(it), kiname: nm, kq: q, kval: None}
                    rows.append(row)
                    idx[key] = row
                    n_add += 1
                if "값" in cell and str(row.get(kval)) != str(cell["값"]):
                    row[kval] = cell["값"]
                    n_set += 1
                if "값_적용후" in cell and str(row.get("값_적용후", "")) != str(cell["값_적용후"]):
                    row["값_적용후"] = cell["값_적용후"]
                    n_post += 1

    JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"user gold applied: {n_set} 값 set, {n_post} 값_적용후 set, {n_add} rows added "
          f"({len(rows)} rows). companies={sorted(cells)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
