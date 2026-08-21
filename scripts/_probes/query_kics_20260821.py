"""Query kics_disclosure.json for specific (code, quarter, item) cells — read-only inspection.
Usage: python query_kics_20260821.py <code> <quarter> [item1,item2,...]
If items omitted, dumps all items for that (code, quarter).
"""
import sys
import io
import json
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]

KEY_CODE = "원보험사코드"
KEY_NAME = "원보험사명"
KEY_QUARTER = "공시분기"
KEY_ITEM = "항목번호"
KEY_ITEM_NAME = "항목명"
KEY_VALUE = "값"
KEY_VALUE_POST = "값_적용후"


def main():
    code = sys.argv[1]
    quarter = sys.argv[2]
    items = None
    if len(sys.argv) > 3:
        items = set(int(x) for x in sys.argv[3].split(","))
    data = json.load(open(ROOT / "kics_disclosure.json", encoding="utf-8"))
    rows = [r for r in data if r.get(KEY_CODE) == code and r.get(KEY_QUARTER) == quarter]
    rows.sort(key=lambda r: (r.get(KEY_ITEM) if isinstance(r.get(KEY_ITEM), (int, float)) else 999))
    print(f"=== {code} {quarter}  ({len(rows)} rows) ===")
    for r in rows:
        it = r.get(KEY_ITEM)
        if items is not None and it not in items:
            continue
        keys = sorted(r.keys())
        extra = {k: r[k] for k in keys if k not in (KEY_CODE, KEY_NAME, KEY_QUARTER, KEY_ITEM, KEY_ITEM_NAME, KEY_VALUE, KEY_VALUE_POST)}
        print(f"item{it:>3}  {str(r.get(KEY_ITEM_NAME))[:30]:30s}  값={r.get(KEY_VALUE)!r:>14}  값_적용후={r.get(KEY_VALUE_POST)!r:>14}  other_keys={extra}")


if __name__ == "__main__":
    main()
