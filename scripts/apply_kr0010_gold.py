"""Apply owner-verified KB손해(KR0010) cells to kics_disclosure.json (UPSERT).

KR0010 is an image-only (OCR) filer — the MD-based fill_period pipeline produces
inaccurate cells (and would overwrite on any re-fill, incl. the 2026.1Q new rows).
Owner hand-verified the values in the review xlsx; they are persisted in
data/_gold/kr0010_user_cells.json and re-applied here AFTER every fill_period /
build so they survive rebuilds. Derived 27/28 are left to recalc_kics_derived.

Run order: fill_period_to_disclosure → apply_kr0010_gold → recalc_kics_derived.
Usage: PYTHONIOENCODING=utf-8 python scripts/apply_kr0010_gold.py
"""
from __future__ import annotations
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
JSON_PATH = REPO / "kics_disclosure.json"
GOLD = REPO / "data" / "_gold" / "kr0010_user_cells.json"
CODE = "KR0010"
ITEM_NAMES = {  # canonical names for new-row creation (item_no -> 항목명)
    1: "지급여력금액", 2: "기본자본", 3: "보완자본", 4: "지급여력금액으로 불인정하는 항목",
    5: "보완자본으로 재분류하는 항목", 6: "기타기본자본조정", 7: "조정준비금", 8: "기타조정",
    9: "신종자본증권", 10: "후순위채무", 11: "해약환급금준비금", 12: "기타포괄손익누계액",
    13: "이익잉여금", 14: "지급여력기준금액", 15: "보험위험액", 16: "생명·장기손해보험위험액",
    17: "일반손해보험위험액", 18: "시장위험액", 19: "신용위험액", 20: "운영위험액",
    21: "법인세조정", 22: "기타", 23: "기본자본요구자본", 24: "보완자본요구자본",
    25: "분산효과", 26: "기타요구자본", 27: "지급여력비율", 28: "기본자본비율",
    29: "사망위험", 30: "장수위험", 31: "장해·질병위험", 32: "장기재물·기타위험",
    33: "해지위험", 34: "사업비위험", 35: "대재해위험",
    36: "시장위험액 中 금리위험액", 37: "주식위험액", 38: "부동산위험액", 39: "외환위험액",
    40: "자산집중위험액", 41: "3-1-0. 금리위험 순자산가치(충격전)",
    42: "3-1-1. 금리위험 순자산가치(평균회귀)", 43: "3-1-2. 금리위험 순자산가치(금리상승)",
    44: "3-1-3. 금리위험 순자산가치(금리하락)", 45: "3-1-4. 금리위험 순자산가치(금리평탄)",
    46: "3-1-5. 금리위험 순자산가치(금리경사)",
}


def main():
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    gold = json.loads(GOLD.read_text(encoding="utf-8"))
    # prefix (원수사명/티커/생손보) + canonical item names from any existing KR0010 row
    meta = next((r for r in rows if r["원보험사코드"] == CODE), None)
    keys = list(rows[0].keys())
    kcode, kname, ktick, kkind, kitem, kiname, kq, kval = keys[:8]
    name_by_item = {}
    for r in rows:
        if r["원보험사코드"] == CODE:
            name_by_item[r[kitem]] = r[kiname]

    idx = {(r["원보험사코드"], r["공시분기"], r[kitem]): r for r in rows}
    n_set = n_add = 0
    for q, cells in gold.items():
        for it_s, v in cells.items():
            it = int(it_s)
            key = (CODE, q, it)
            if key in idx:
                if str(idx[key][kval]) != str(v):
                    idx[key][kval] = v
                    n_set += 1
            else:
                nm = name_by_item.get(it) or ITEM_NAMES.get(it, "")
                row = {kcode: CODE, kname: meta[kname], ktick: meta[ktick],
                       kkind: meta[kkind], kitem: it, kiname: nm, kq: q, kval: v}
                rows.append(row)
                n_add += 1
    JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"KR0010 gold applied: {n_set} set, {n_add} added ({len(rows)} rows). "
          f"quarters={sorted(gold)}")


if __name__ == "__main__":
    main()
