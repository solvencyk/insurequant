"""Read-only census: find every (code, quarter) bucket where kics_disclosure.json's
item14 (지급여력기준금액) 값_적용후 is a non-integer value that matches
item1_후 / item27_후 * 100 to 2 decimals -- the back-solve signature flagged in
inbox/parser/20260921T1400Z (SS B, "40-bucket census").

No writes. Output: data/_derived/_probe_20260921_item14_backsolve_census.json
"""
import json
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MASTER = REPO / "kics_disclosure.json"

KEY_CODE = "원보험사코드"
KEY_NAME = "원수사명"
KEY_ITEM = "항목번호"
KEY_Q = "공시분기"
KEY_VAL = "값"
KEY_POST = "값_적용후"


def to_float(x):
    if x is None:
        return None
    try:
        return float(str(x).replace(",", ""))
    except ValueError:
        return None


def is_integerish(x: float) -> bool:
    return abs(x - round(x)) < 1e-9


def main():
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    buckets: dict[tuple[str, str], dict[int, dict]] = defaultdict(dict)
    names: dict[str, str] = {}
    for r in rows:
        buckets[(r[KEY_CODE], r[KEY_Q])][r[KEY_ITEM]] = r
        names[r[KEY_CODE]] = r.get(KEY_NAME)

    hits = []
    for (code, quarter), items in buckets.items():
        row14 = items.get(14)
        row1 = items.get(1)
        row27 = items.get(27)
        if row14 is None or row1 is None or row27 is None:
            continue
        post14 = to_float(row14.get(KEY_POST))
        post1 = to_float(row1.get(KEY_POST))
        post27 = to_float(row27.get(KEY_POST))
        if post14 is None or post1 is None or post27 is None:
            continue
        if post27 == 0:
            continue
        if is_integerish(post14):
            continue
        expected = post1 / post27 * 100.0
        if round(expected, 2) == round(post14, 2):
            row15 = items.get(15)
            row22 = items.get(22)
            row23 = items.get(23)
            hits.append(
                {
                    "code": code,
                    "name": names.get(code),
                    "quarter": quarter,
                    "item1_post": row1.get(KEY_POST),
                    "item14_post_master": row14.get(KEY_POST),
                    "item14_post_expected_from_ratio": round(expected, 4),
                    "item27_post": row27.get(KEY_POST),
                    "item14_pre": row14.get(KEY_VAL),
                    "item1_pre": row1.get(KEY_VAL),
                    "item27_pre": row27.get(KEY_VAL),
                    "item15_post": row15.get(KEY_POST) if row15 else None,
                    "item22_post": row22.get(KEY_POST) if row22 else None,
                    "item23_post": row23.get(KEY_POST) if row23 else None,
                    "delta_from_2eok_tolerance": round(abs(expected - post14), 4),
                }
            )

    hits.sort(key=lambda h: (h["code"], h["quarter"]))

    by_company = defaultdict(int)
    for h in hits:
        by_company[h["code"]] += 1

    print(f"total buckets: {len(hits)}")
    for code, n in sorted(by_company.items(), key=lambda kv: -kv[1]):
        print(f"  {code} {names.get(code)}: {n}")

    out_path = REPO / "data" / "_derived" / "_probe_20260921_item14_backsolve_census.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(hits, f, ensure_ascii=False, indent=2)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    main()
