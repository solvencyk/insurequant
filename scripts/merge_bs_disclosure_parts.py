#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""17BS 경영공시 백필 통합 스크립트 (2026-09-11, inbox/parser/20260911T0109Z).

`data/_derived/bs_from_disclosure_parts/*.json`(회사별 파트 파일 -- 엔진 산출 + 서브에이전트
검증/이미지 보충 파일)을 하나로 합쳐 `data/_derived/bs_from_disclosure.json`(계보 사이드카)에
쓰고, `data/dart/viz/bs_manual_overrides.json`에 **셀 단위 UPSERT**한다(마스터 통째
read-modify-write 금지 원칙 -- 이 스크립트는 오버라이드 파일만 건드리고 마스터는 안 건드린다,
반영은 build_ifrs17_bs.py 를 나중에 별도로 돌려야 한다).

우선순위(같은 셀 키가 여러 파일에 있으면): `<KR>_agent_vision.json`(사람 비전판독+4Q교차확인)
> `<KR>_agent_note.json`(사람 원문 재확인) > `<KR>.json`(엔진 자동추출, 기본).

Run:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/merge_bs_disclosure_parts.py [--dry-run]
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")

PARTS_DIR = ROOT / "data" / "_derived" / "bs_from_disclosure_parts"
SIDECAR = ROOT / "data" / "_derived" / "bs_from_disclosure.json"
OVERRIDES = ROOT / "data" / "dart" / "viz" / "bs_manual_overrides.json"

ITEM_LABELS = {
    1: "자산총계", 2: "부채총계", 3: "자본총계", 4: "기타포괄손익 누계액",
    5: "해약환급금준비금 적립액", 6: "비상위험준비금 적립액", 7: "대손준비금 적립액",
    8: "보증준비금 적립액", 10: "현금및현금성자산", 11: "당기손익-공정가치측정금융자산",
    12: "기타포괄손익-공정가치측정금융자산", 13: "상각후원가측정금융자산",
    14: "재보험계약자산", 15: "유형자산", 20: "보험계약부채", 21: "재보험계약부채",
    22: "투자계약부채", 23: "차입부채", 24: "기타부채", 30: "자본금", 31: "이익잉여금",
}


def main() -> int:
    dry_run = "--dry-run" in sys.argv

    all_cells: dict[str, dict] = {}
    all_skips: dict[str, dict] = {}
    sources_by_key: dict[str, str] = {}

    # 우선순위 낮은 것부터 덮어써서 높은 것이 마지막에 이긴다.
    files = sorted(PARTS_DIR.glob("*.json"))
    engine_files = [f for f in files if "_agent_" not in f.stem]
    note_files = [f for f in files if f.stem.endswith("_agent_note")]
    vision_files = [f for f in files if f.stem.endswith("_agent_vision")]
    other_agent_files = [f for f in files if "_agent_" in f.stem
                          and f not in note_files and f not in vision_files]

    for group in (engine_files, other_agent_files, note_files, vision_files):
        for f in group:
            d = json.loads(f.read_text(encoding="utf-8"))
            for k, v in (d.get("cells") or {}).items():
                all_cells[k] = v
                sources_by_key[k] = f.name
                all_skips.pop(k, None)
            for k, v in (d.get("skips") or {}).items():
                if k in all_cells:
                    continue
                all_skips[k] = v

    print(f"parts files: {len(files)} (engine={len(engine_files)} note={len(note_files)} "
          f"vision={len(vision_files)} other={len(other_agent_files)})")
    print(f"total cells: {len(all_cells)}  total skips(non-cell keys): {len(all_skips)}")

    # 항목별 채택 집계
    by_item = Counter(k.split("|")[1] for k in all_cells)
    print("cells by item:", dict(sorted(by_item.items(), key=lambda x: int(x[0]))))
    by_co = Counter(k.split("|")[0] for k in all_cells)
    print("cells by company:", dict(sorted(by_co.items())))

    # skip_reason 없는 칸(스키마 위반) 감사
    missing_reason = [k for k, v in all_skips.items() if not v.get("skip_reason")]
    if missing_reason:
        print(f"WARNING: {len(missing_reason)} skip entries missing skip_reason: "
              f"{missing_reason[:10]}")

    if dry_run:
        print("(--dry-run: 사이드카/오버라이드 파일 안 씀)")
        return 0

    SIDECAR.write_text(json.dumps({
        "_readme": [
            "IFRS17_BS.json 경영공시 백필 계보 사이드카 (inbox/parser/20260911T0109Z).",
            "각 칸의 pdf 경로/페이지/sha256/축척/방법/근거를 보존한다.",
            "반영은 별도로 data/dart/viz/bs_manual_overrides.json 에 셀 단위 UPSERT 된다.",
            "이 파일은 scripts/merge_bs_disclosure_parts.py 가 생성한다 -- 손으로 고치지 말 것.",
        ],
        "cells": all_cells,
        "skips": all_skips,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {SIDECAR}: {len(all_cells)} cells, {len(all_skips)} skips")

    ov = json.loads(OVERRIDES.read_text(encoding="utf-8")) if OVERRIDES.exists() else \
        {"_readme": [], "cells": {}}
    ov.setdefault("cells", {})
    ov.setdefault("_readme", [])
    replaced = added = 0
    for k, cell in all_cells.items():
        entry = {"값": cell["값"], "근거": cell.get("근거", "")}
        if k in ov["cells"]:
            replaced += 1
        else:
            added += 1
        ov["cells"][k] = entry
    ov["_readme"].append(
        f"[2026-09-11] 17BS 경영공시 백필(inbox/parser/20260911T0109Z) -- {added}칸 신규 + "
        f"{replaced}칸 교체, scripts/merge_bs_disclosure_parts.py 로 셀단위 UPSERT. 계보(PDF "
        f"경로·페이지·sha256·축척·방법)는 data/_derived/bs_from_disclosure.json 사이드카에.")
    OVERRIDES.write_text(json.dumps(ov, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OVERRIDES}: {added} new + {replaced} replaced (total cells now "
          f"{len(ov['cells'])})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
