# -*- coding: utf-8 -*-
"""KR0074 2023.4Q income_statement 블록의 계보 셀 1개만 갱신한다.

이 블록은 published_items=0 이라 `source_id=DART · source_file=null ·
unresolved_reason=NO_PUBLISHED_VALUE_IN_BLOCK` 로 박혀 있었다. 2026-09-22 에 20칸을
`_GOLD_CELL_OVERRIDE` 로 채웠으므로 계보가 같은 회사 2024.4Q·2025.4Q 와 동일하게
`OWNER_GOLD / scripts/build_pl_breakdown.py / gold_cell_override` 가 돼야 한다.
(안 고치면 validate_data_contract 가 MISSING_PROVENANCE + SOURCE_ID_LINEAGE_MISMATCH 로
정확히 RED 를 낸다 — 실제로 냈다.)

`scripts/emit_pl_provenance.py` 통째 재발행은 쓰지 않는다: 지금 라이브 사이드카는 그 뒤에
DISCLOSURE 계보(경영공시 PL 백필)가 더해진 상태인데, 이 스크립트를 다시 돌리면 그 155셀이
다시 null 로 되돌아간다(--dry-run 으로 실측). 그래서 셀 한 개만 손본다.

가드: 대상 셀 1개만 · 다른 셀의 바이트가 그대로인지 대조 · published_items 를 실제 마스터
값 개수로 다시 센다.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from scripts.build_pl_breakdown import _GOLD_CELL_OVERRIDE  # noqa: E402

PROV = ROOT / "PL_breakdown_provenance.json"
MASTER = ROOT / "PL_breakdown.json"
CODE, QUARTER, BLOCK = "KR0074", "2023.4Q", "income_statement"
IS_ITEMS = {1, 2, 3, 7, 8, 12, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24}
DRY = "--dry-run" in sys.argv


def main():
    prov = json.loads(PROV.read_text(encoding="utf-8"))
    master = json.loads(MASTER.read_text(encoding="utf-8"))
    ov = _GOLD_CELL_OVERRIDE[(CODE, QUARTER)]

    published = sorted(
        int(r["항목번호"]) for r in master
        if r.get("원보험사코드") == CODE and r.get("공시분기") == QUARTER
        and r.get("값") is not None and int(r["항목번호"]) in IS_ITEMS)
    items = sorted(i for i in ov if i in IS_ITEMS)
    print(f"마스터 income_statement 실값 {len(published)}칸 {published}")
    print(f"override 가 설명하는 칸   {len(items)}칸 {items}")
    if set(items) - set(published):
        sys.exit(f"REFUSE: override 에 있는데 마스터에 값이 없다 {set(items) - set(published)}")

    before = json.dumps(prov, ensure_ascii=False, sort_keys=True)
    hit = 0
    for c in prov["cells"]:
        if (c.get("company_code"), c.get("quarter"), c.get("item_block")) != (CODE, QUARTER, BLOCK):
            continue
        hit += 1
        c.pop("unresolved_reason", None)
        c["source_id"] = "OWNER_GOLD"
        c["source_file"] = "scripts/build_pl_breakdown.py"
        c["source_files"] = [{"file": "scripts/build_pl_breakdown.py",
                              "how": "gold_cell_override", "items": items}]
        c["resolution"] = "gold_cell_override"
        c["published_items"] = len(published)
        c["schema_items"] = 24
        print("갱신:", json.dumps(c, ensure_ascii=False))
    if hit != 1:
        sys.exit(f"REFUSE: 대상 셀이 {hit}개 (1개여야 한다)")

    # 다른 셀은 한 글자도 안 바뀌었는지 대조
    a = json.loads(before)
    n_diff = 0
    for x, y in zip(a["cells"], prov["cells"]):
        same_key = (x.get("company_code"), x.get("quarter"), x.get("item_block"))
        if same_key == (CODE, QUARTER, BLOCK):
            continue
        if json.dumps(x, ensure_ascii=False, sort_keys=True) != json.dumps(y, ensure_ascii=False, sort_keys=True):
            n_diff += 1
    if n_diff:
        sys.exit(f"REFUSE: 다른 셀 {n_diff}개가 바뀌었다")
    print(f"다른 셀 {len(prov['cells']) - 1}개 불변 확인")

    if DRY:
        print("(dry-run: 파일 안 씀)")
        return
    PROV.write_text(json.dumps(prov, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote", PROV.name)


main()
