#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""경영공시 PL 공란 백필 병합 (2026-10-08, parser/ifrs17 단일 병합자).

owner 2026-10-08: "정기경영공시를 내는 회사라면 BS 전부 공란인 건 말이 안 된다 ... 전사 전기간 채워라."
census = data/_derived/bspl_blank_census_20261008.json 의 pl_empty 29칸 (회사,분기).
추출 = data/_derived/pl_from_disclosure_parts/<KR>.json (6 그룹 병렬 추출, 마스터 미반영).

방식은 2026-09-20 `merge_pl_backfill_disclosure_20260920.py` 와 같다 (그 docstring 참조):
- 루트 `PL_breakdown.json` 에만 쓴다. `build_root_masters.py` 는 부르지 않는다(main() 통짜 금지).
  `data/dart/viz/pl_breakdown_master.json`(빌더 산출, PL 골든이 고정)은 안 건드린다 --
  `build_pl()` 의 `_additive_merge` 가 루트 행을 다음 리빌드에서 보존한다.
- **값이 None 인 기존 행 채움 + 행 자체가 없는 칸은 새 행 추가**. 값이 있는 칸은 절대 안 건드린다.
- `값_당분기` 는 같은 소스(이번 병합 집합) 안에서만 만든다: Q1 = 누계, 직전분기가 이번 집합에
  있으면 차분, 아니면 None(소스 혼합 금지). 4Q 는 집합 안이어도 None.
- 사이드카 `PL_breakdown_provenance.json` 에 DISCLOSURE 계보를 append/patch 한다. `as_of_date` 는 안 싣는다.
- 기존 행은 허가 집합 밖 1칸이라도 바뀌면 abort.

제외(칸 단위, 사유 기록): KR0004 2025.3Q -- 원문 기간이 신설법인 제1기 2025-06-16~09-30 이라
1/1 기준 연누계가 아니다. YTD 계열에 넣으면 값_당분기가 2Q 누계와 섞여 틀리다.

보류(staging): 항목 17·20·21 은 마스터에 싣지 않는다. validate_data_contract §3d
`CONCEPT_MIXED_DISCLOSURE_INTO_DART`(CONCEPT_REGISTRY['pl_disclosure_vs_dart'].reference_only_items)
가 경영공시 계보 셀의 17/20/21 을 RED 로 막는다 -- 허용은 §2-1 5항목(1,16,22,23,24)뿐이다.
KR0004(전체 별도 포괄손익계산서, 원 단위)·KR0099(요약표, 보정 통과) 값은 근거와 함께
`data/_derived/pl_disclosure_reference_only_staged_20261008.json` 에 두고, validation/owner 가
"전체 재무제표 계보" 허용을 결정하면 그때 싣는다. 라벨 위장(source_id 바꿔 달기)으로 우회하지 않는다.

사이드카 계보: 한 블록에 DART/OWNER_GOLD 와 DISCLOSURE 버킷이 섞이면 block `source_id` 는 비-DISCLOSURE
쪽을 유지한다(validate_master_tables 의 fail-closed — 한 다리라도 값이 있으면 엄격 검산).

실행:
    $py scripts/merge_pl_backfill_disclosure_20261008.py            # dry-run
    $py scripts/merge_pl_backfill_disclosure_20261008.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)

MASTER = ROOT / "PL_breakdown.json"
SIDECAR = ROOT / "PL_breakdown_provenance.json"
PARTS = ROOT / "data" / "_derived" / "pl_from_disclosure_parts"
OUT_MANIFEST = ROOT / "data" / "_derived" / "pl_from_disclosure_merge_20261008.json"

MASTER_ITEM_NAME = {1: "보험손익", 16: "기타사업비용", 17: "투자손익", 20: "영업이익",
                    21: "영업외손익", 22: "세전이익", 23: "법인세", 24: "당기순이익"}

# 칸 단위 제외 -- (회사, 분기) 전체 또는 (회사, 분기, 항목)
EXCLUDE_CQ = {
    ("KR0004", "2025.3Q"): "원문 기간이 신설법인 제1(당)3분기 2025-06-16~09-30(예별 신설법인 제1기 개시)이라 "
                          "1/1 기준 연누계가 아니다 -- YTD 계열에 넣으면 2Q 누계와 섞인다. 비교 단절 구간이라 비움.",
}
# 4Q 당분기는 소스 혼합(억원 요약 vs 원 단위)이라 만들지 않는다
NO_DANGI_Q4 = True
# 경영공시 계보로 싣지 못하는 항목(validate_data_contract §3d) -- 보류 파일로만 남긴다
REFERENCE_ONLY_ITEMS = (17, 20, 21)
STAGED_OUT = ROOT / "data" / "_derived" / "pl_disclosure_reference_only_staged_20261008.json"


def _qkey(q):
    return (int(q[:4]), int(q[5]))


def _prev_q(q):
    y, n = _qkey(q)
    return None if n == 1 else f"{y}.{n - 1}Q"


def fail(msg):
    print("ABORT:", msg)
    sys.exit(2)


def load_parts():
    """세 가지 파트 스키마를 {(code,item,quarter): spec} 으로 정규화한다."""
    cells = {}
    for f in sorted(PARTS.glob("KR*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        code = f.stem
        c = d["cells"]
        if isinstance(c, list):
            for ce in c:
                q = ce["공시분기"]
                for it, v in ce["items"].items():
                    cells[(code, int(it), q)] = {
                        "값": float(v["값"]), "pdf": ce.get("source_file"), "page": ce.get("page"),
                        "scale": ce.get("scale"), "file": f.name}
        else:
            for k, v in c.items():
                cc, it, q = k.split("|")
                cells[(cc, int(it), q)] = {
                    "값": float(v["값"]), "pdf": v.get("pdf"), "page": v.get("page"),
                    "scale": v.get("축척"), "file": f.name}
    return cells


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    side = json.loads(SIDECAR.read_text(encoding="utf-8"))
    before_stat = MASTER.stat()
    n_before = len(rows)
    by_key = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in rows}
    if len(by_key) != len(rows):
        fail("마스터에 (코드,항목,분기) 중복 행이 있다")
    meta = {}
    for r in rows:
        meta.setdefault(r["원보험사코드"], {k: r[k] for k in ("원수사명", "티커", "생손보여부")})

    parts = load_parts()
    excluded = {k: EXCLUDE_CQ[(k[0], k[2])] for k in parts if (k[0], k[2]) in EXCLUDE_CQ}
    cand_all = {k: v for k, v in parts.items() if k not in excluded}
    staged = {k: v for k, v in cand_all.items() if k[1] in REFERENCE_ONLY_ITEMS}
    cand = {k: v for k, v in cand_all.items() if k not in staged}
    unknown =sorted({k[0] for k in cand if k[0] not in meta})
    if unknown:
        fail(f"마스터에 없는 회사코드 {unknown}")
    bad_item = sorted({k[1] for k in cand if k[1] not in MASTER_ITEM_NAME})
    if bad_item:
        fail(f"알 수 없는 항목번호 {bad_item}")

    # 충돌 검사 -- 값 있는 기존 칸은 건드리지 않는다
    clash = [k for k in cand if (k in by_key and by_key[k].get("값") is not None)]
    if clash:
        fail(f"값 있는 기존 칸과 충돌 {len(clash)}건: {clash[:5]}")
    for k in cand:
        r = by_key.get(k)
        if r is not None and r.get("항목명") != MASTER_ITEM_NAME[k[1]]:
            fail(f"항목명 불일치 {k}: {r.get('항목명')!r}")

    # 항등식 (보고용 + 허용오차 초과면 abort)
    by_cq = defaultdict(dict)
    for (c, i, q), v in cand_all.items():     # 항등식은 보류 항목까지 포함해 전체로 검산한다
        by_cq[(c, q)][i] = v["값"]
    ident_report = []
    for (c, q), g in sorted(by_cq.items()):
        # 억원 해상도 칸은 값이 100 의 배수 -- 반올림 2.5억 허용, 원 단위 칸은 0.01
        yok = all(abs(v / 100 - round(v / 100)) < 1e-6 for v in g.values())
        tol = 250.0 if yok else 0.01
        for name, ok in (
            ("24=22-23", (24 in g and 22 in g and 23 in g, lambda: g[22] - g[23] - g[24])),
            ("20=1+17", (20 in g and 1 in g and 17 in g, lambda: g[1] + g[17] - g[20])),
            ("22=20+21", (22 in g and 20 in g and 21 in g, lambda: g[20] + g[21] - g[22])),
        ):
            if ok[0]:
                resid = ok[1]()
                ident_report.append((c, q, name, round(resid, 6), tol))
                if abs(resid) > tol:
                    fail(f"항등식 {name} 잔차 {resid} > {tol}: {c} {q}")

    # 값_당분기 (같은 소스 안에서만)
    in_set = defaultdict(dict)
    for (c, i, q), v in cand.items():
        in_set[(c, i)][q] = v["값"]
    dangi = {}
    stat = {"q1": 0, "diff": 0, "none": 0}
    for (c, i, q), v in cand.items():
        p = _prev_q(q)
        if q.endswith("4Q") and NO_DANGI_Q4:
            dangi[(c, i, q)] = None
            stat["none"] += 1
        elif p is None:
            dangi[(c, i, q)] = v["값"]
            stat["q1"] += 1
        elif in_set[(c, i)].get(p) is not None:
            dangi[(c, i, q)] = round(v["값"] - in_set[(c, i)][p], 6)
            stat["diff"] += 1
        else:
            dangi[(c, i, q)] = None
            stat["none"] += 1

    snapshot = {k: json.dumps(v, ensure_ascii=False, sort_keys=True) for k, v in by_key.items()}
    authorized_existing = {k for k in cand if k in by_key}
    filled_existing, appended = [], []

    # 사이드카 사전 검사
    side_idx = {(x["company_code"], x["quarter"], x["item_block"]): x for x in side["cells"]}
    pairs = sorted({(k[0], k[2]) for k in cand}, key=lambda x: (x[0], _qkey(x[1])))
    items_by_pair = defaultdict(list)
    for k in cand:
        items_by_pair[(k[0], k[2])].append(k[1])
    pdf_by_pair = {}
    for k, v in cand.items():
        pdf_by_pair.setdefault((k[0], k[2]), v["pdf"])
    for (c, q), pdf in pdf_by_pair.items():
        if not pdf or not (ROOT / pdf).exists():
            fail(f"source pdf 디스크 부재: {pdf}")

    print("=" * 78)
    print(f"파트 셀 {len(parts)} · 제외 {len(excluded)} · 보류 {len(staged)} · 병합 후보 {len(cand)} "
          f"((회사,분기) {len(pairs)})")
    print(f"  기존 null 행 채움 {len(authorized_existing)} · 신규 행 {len(cand) - len(authorized_existing)}")
    print(f"  값_당분기: Q1직접 {stat['q1']} · 동일소스차분 {stat['diff']} · None {stat['none']}")
    print(f"  항등식 점검 {len(ident_report)}건 전부 허용오차 이내")
    print(f"  보류(17/20/21 -- §3d reference_only) {len(staged)}셀 -> {STAGED_OUT.name}")
    for k, why in excluded.items():
        print(f"  제외 {k}: {why[:60]}...")
    print("=" * 78)
    if not args.apply:
        print("dry-run -- 아무것도 쓰지 않았다.")
        return

    now = MASTER.stat()
    if (now.st_mtime_ns, now.st_size) != (before_stat.st_mtime_ns, before_stat.st_size):
        fail("읽은 뒤 PL_breakdown.json 이 바뀌었다 -- 동시 세션 의심")

    new_rows = []
    for k in sorted(cand, key=lambda x: (x[0], _qkey(x[2]), x[1])):
        c, i, q = k
        r = by_key.get(k)
        if r is not None:
            r["값"] = cand[k]["값"]
            r["값_당분기"] = dangi[k]
            filled_existing.append(k)
        else:
            m = meta[c]
            new_rows.append({
                "원보험사코드": c, "원수사명": m["원수사명"], "티커": m["티커"],
                "생손보여부": m["생손보여부"], "항목번호": i, "항목명": MASTER_ITEM_NAME[i],
                "공시분기": q, "값": cand[k]["값"], "값_당분기": dangi[k]})
            appended.append(k)

    changed = [k for k, s in snapshot.items()
               if json.dumps(by_key[k], ensure_ascii=False, sort_keys=True) != s]
    if set(changed) - authorized_existing:
        fail(f"허가 밖 기존 행이 바뀌었다: {sorted(set(changed) - authorized_existing)[:10]}")
    if set(changed) != authorized_existing:
        fail(f"허가된 칸 중 안 바뀐 게 있다: {sorted(authorized_existing - set(changed))[:10]}")
    out = rows + new_rows
    if len(out) != n_before + len(appended):
        fail("결과 행수 불일치")
    if len({(r["원보험사코드"], r["항목번호"], r["공시분기"]) for r in out}) != len(out):
        fail("결과에 키 중복이 생겼다")

    # 사이드카 append / patch (income_statement 블록 -- 이번 항목은 전부 1,16,17,20,21,22,23,24)
    n_new_side = n_patch_side = 0
    for (c, q) in pairs:
        items = sorted(items_by_pair[(c, q)])
        pdf = pdf_by_pair[(c, q)]
        key = (c, q, "income_statement")
        cell = side_idx.get(key)
        bucket = {"file": pdf, "how": "disclosure_summary_pl", "items": items}
        if cell is None:
            side["cells"].append({
                "company_code": c, "quarter": q, "item_block": "income_statement",
                "source_id": "DISCLOSURE", "source_file": pdf, "source_files": [bucket],
                "resolution": "disclosure_summary_pl", "published_items": len(items),
                "schema_items": 24})
            n_new_side += 1
            continue
        for b in cell.get("source_files") or []:
            if set(b["items"]) & set(items):
                fail(f"사이드카 버킷 항목 중복 {key}: {b}")
        cell.setdefault("source_files", []).append(bucket)
        cell["published_items"] = cell.get("published_items", 0) + len(items)
        # 혼합 블록은 비-DISCLOSURE 버킷이 앞선다 -> block source_id 가 DISCLOSURE 로 뒤집히지 않는다
        # (그러면 §3d 가 DART 항목까지 경영공시 계보로 읽고, 2e 의 fail-closed 가 풀린다)
        cell["source_files"].sort(key=lambda b: (
            1 if str(b["file"]).startswith("data/disclosure/") else 0,
            -len(b["items"]), 0 if str(b["file"]).startswith("data/dart/") else 1, str(b["file"])))
        top = cell["source_files"][0]
        cell["source_file"] = top["file"]
        cell["resolution"] = top["how"]
        f = str(top["file"])
        cell["source_id"] = ("DART" if f.startswith("data/dart/") else
                             "DISCLOSURE" if f.startswith("data/disclosure/") else "OWNER_GOLD")
        cell.pop("unresolved_reason", None)
        n_patch_side += 1
    side["merge_note_20261008"] = (
        "경영공시 PL 공란 백필(owner 2026-10-08) -- 12사 29(회사,분기) 중 KR0004 2025.3Q 제외 28칸 "
        "DISCLOSURE append/patch. as_of_date 는 싣지 않았다. "
        "재현: scripts/merge_pl_backfill_disclosure_20261008.py --apply")

    MASTER.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    SIDECAR.write_text(json.dumps(side, ensure_ascii=False, indent=1), encoding="utf-8")
    STAGED_OUT.write_text(json.dumps({
        "_note": ("경영공시 계보로 마스터에 싣지 못하는 항목(17 투자손익 · 20 영업이익 · 21 영업외손익) -- "
                  "validate_data_contract §3d CONCEPT_MIXED_DISCLOSURE_INTO_DART 때문에 보류. "
                  "KR0004=전체 별도 포괄손익계산서(원 단위, 항등식 닫힘) · KR0099=요약표(보정 11분기 통과). "
                  "validation/owner 가 '전체 재무제표 계보' 를 허용하면 이 값을 그대로 싣는다."),
        "cells": {f"{c}|{i}|{q}": {"값": v["값"], "pdf": v["pdf"], "page": v["page"], "scale": v["scale"],
                                  "part_file": v["file"]}
                  for (c, i, q), v in sorted(staged.items(), key=lambda x: (x[0][0], _qkey(x[0][2]), x[0][1]))},
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    OUT_MANIFEST.write_text(json.dumps({
        "filled_existing": [list(k) for k in filled_existing],
        "appended": [list(k) for k in appended],
        "excluded": {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in excluded.items()},
        "dangi_stat": stat,
        "sidecar_new": n_new_side, "sidecar_patched": n_patch_side,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {MASTER} ({len(out)} rows, +{len(new_rows)}, 채움 {len(filled_existing)})")
    print(f"wrote {SIDECAR} (신규 {n_new_side}, 패치 {n_patch_side})")


if __name__ == "__main__":
    main()
