#!/usr/bin/env python3
"""경영공시 PL 백필 병합 선행조건 ②③④ 의 재현 프로브 (2026-09-20, validation 12차).

**읽기전용.** 마스터·사이드카·게이트 산출을 한 바이트도 쓰지 않는다. 임시 병합 사이드카만
scratchpad 가 아닌 `artifacts/` 아래에 만들고 끝나면 지운다.

세 가지를 잰다.

1. **계보 census** — 디스크의 모든 provenance 사이드카에서 `source_id` 선언 ↔ `source_file`
   경로 계보가 맞는지. `_SOURCE_LINEAGE` 등재 전/후를 같이 찍어, 계보 검사를
   `_CAPITAL_SECURITIES_MASTERS` guard 밖으로 뺄 때 무엇이 red-out 되는지 보여준다.
2. **소스인식 기대그리드** — 스테이징 `pl_backfill_disclosure_20260918.json` 의 병합후보
   775칸을 가상 병합한 인덱스에 `coverage_holes` 를 종전규격/소스인식 두 방식으로 돌린다.
3. **두 게이트 일치** — 같은 census 를 `validate_master_tables._check_coverage` 와
   `validate_data_contract.check_census` §1c 가 **같은 숫자**로 내는지. 이 둘이 갈리는 것이
   2026-09-20 배선 도중 실제로 발견된 결함이다(§1c 가 resolver 없이 부르고 있었다).

실행:
    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe \
        scripts/_probes/_probe_20260920_pl_merge_precondition.py
"""
from __future__ import annotations

import io
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import validate_data_contract as G  # noqa: E402
import validate_master_tables as V  # noqa: E402

PL_KEYS = ["보험손익", "생명장기손익", "당기순이익"]
STAGING = ROOT / "data/_derived/pl_backfill_disclosure_20260918.json"

# 2026-09-20 등재 **이전**의 목록. 등재 효과를 보여주기 위한 대조군이라 여기 리터럴로 둔다.
LINEAGE_BEFORE = (
    ("data/bonds/capital_securities_", "DART"),
    ("data/bonds/disclosure/", "DART"),
    ("data/dart/", "DART"),
    ("data/bonds/normalized/", "FSC_BONDS"),
    ("data/bonds/raw/", "FSC_BONDS"),
    ("kics_disclosure.json", "DISCLOSURE"),
)


def lineage(sf, table):
    p = str(sf or "").replace("\\", "/").lstrip("./")
    for prefix, sid in table:
        if p.startswith(prefix):
            return sid
    return None


def verdict(cells, table):
    c = Counter()
    for x in cells:
        got = lineage(x.get("source_file"), table)
        declared = x.get("source_id")
        c["UNREGISTERED" if got is None
          else ("MATCH" if got == declared else f"MISMATCH({declared}!={got})")] += 1
    return dict(c)


def section_1():
    print("=" * 78)
    print("1. 계보 census — `SOURCE_ID_LINEAGE_MISMATCH` 를 capsec guard 밖으로 뺄 때의 영향")
    print("=" * 78)
    for master, rel in sorted(G.Env.MASTER_FILES.items()):
        side = ROOT / ((rel[:-5] if rel.endswith(".json") else rel) + "_provenance.json")
        if not side.exists():
            print(f"  {master:22s} 사이드카 없음 (MISSING_PROVENANCE_SIDECAR 대상)")
            continue
        cells = json.loads(side.read_text(encoding="utf-8")).get("cells") or []
        print(f"  {master:22s} n={len(cells):5d}  등재전={verdict(cells, LINEAGE_BEFORE)}"
              f"  등재후={verdict(cells, G._SOURCE_LINEAGE)}")
    print()


def merged_world():
    """(가상 병합 인덱스, 가상 병합 사이드카 경로). 사이드카는 호출자가 지운다."""
    stg = json.loads(STAGING.read_text(encoding="utf-8"))
    rows = json.loads((ROOT / V.PL_PATH).read_text(encoding="utf-8"))
    code2name = {r["원보험사코드"]: r["원수사명"] for r in rows if r.get("원보험사코드")}
    merged = {k: dict(v) for k, v in V.load_long(V.PL_PATH).items()}
    n_added = 0
    for cell in stg["cells"]:
        if cell.get("backfill_excluded"):
            continue
        name = code2name.get(cell["원보험사코드"], cell["원보험사명"])
        for it in (cell.get("items") or {}).values():
            if it.get("merge_candidate") and it.get("값") is not None:
                merged.setdefault((name, cell["공시분기"]), {})[V.norm(it["항목명"])] = it["값"]
                n_added += 1
    side = json.loads((ROOT / V.PL_PROVENANCE_PATH).read_text(encoding="utf-8"))
    tmp = ROOT / "artifacts" / "_probe_20260920_merged_provenance.json"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps({**side, "cells": list(side["cells"]) + list(stg["provenance_entries"])},
                              ensure_ascii=False), encoding="utf-8")
    return merged, tmp, n_added


def section_2_3(merged, tmp, n_added):
    print("=" * 78)
    print(f"2. 소스인식 기대그리드 (스테이징 병합후보 {n_added}값 가상 병합)")
    print("=" * 78)
    live = V.load_long(V.PL_PATH)
    live_src, merged_src = V.pl_cell_source_ids(), V.pl_cell_source_ids(sidecar_path=str(tmp))
    print(f"  계보 census  live={dict(Counter(live_src.values()))}  "
          f"merged={dict(Counter(merged_src.values()))}")
    out = {}
    for tag, idx, src in (("LIVE", live, live_src), ("MERGED", merged, merged_src)):
        off = V.coverage_holes(idx, PL_KEYS, na_registry=V.LOB_LEG_NA)
        on = V.coverage_holes(idx, PL_KEYS, na_registry=V.LOB_LEG_NA,
                              key_items_for=V.pl_key_items_for(src, PL_KEYS))
        print(f"  {tag:7s} 종전규격 real={len(off[0]):3d} known={len(off[1]):3d} struct={len(off[2]):2d}"
              f"   |   소스인식 real={len(on[0]):3d} known={len(on[1]):3d} struct={len(on[2]):2d}")
        out[tag] = (off[0], on[0], idx, src)
    print("  LIVE 두 규격 동일? ", sorted(out['LIVE'][0]) == sorted(out['LIVE'][1]),
          " (= 오늘 골든 SUMMARY 가 안 움직이는 근거)")
    print("  MERGED 소스인식 real hole:")
    for x in sorted(out["MERGED"][1]):
        mark = "기존" if x in set(out["LIVE"][0]) else "**병합으로 드러남**"
        print(f"     {x}  {mark}")
    print()
    print("=" * 78)
    print("3. 두 게이트 일치 (validate_master_tables ↔ validate_data_contract §1c)")
    print("=" * 78)
    for tag in ("LIVE", "MERGED"):
        _off, on, idx, src = out[tag]
        res = G.run_gate(G.Env(inject={"pl": idx, "pl_source_ids": src}))
        dc = sorted({(f.company, f.quarter) for f in res.red
                     if f.rule == "MASTER_HOLE" and f.master == "PL_breakdown"})
        vmt = sorted((c, q) for c, q, _ in on)
        print(f"  {tag:7s} master_tables real={len(vmt):3d}  data_contract MASTER_HOLE={len(dc):3d}"
              f"  일치={vmt == dc}")
        if vmt != dc:
            print("     master_tables:", vmt)
            print("     data_contract:", dc)
    print()


def main():
    section_1()
    merged, tmp, n_added = merged_world()
    try:
        section_2_3(merged, tmp, n_added)
    finally:
        tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
