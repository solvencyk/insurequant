#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-12 reinsurer PL/BS blank re-sweep (inbox/parser/20261012T0110Z), PL part: load the 감독회계 총괄 요약 포괄손익계산서 lines that the reinsurer
경영공시 prints but the master leaves blank: item 17 투자손익, 20 영업이익, 21 영업외손익 (+ one item 16 cell), KR1101..KR1108.  Cell level, ADD ONLY, old-value guard
(the key must be absent), backup, sidecar lineage with its own `how`.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/reinsurer_resweep_pl_apply.py [--apply]

Plan = data/_derived/reinsurer_resweep_20261012/fill_plan.json (built by s31_decide.py + s33_plan.py from the PDF text layer; every cell was parsed by two backends or
closed by the printed identities).  Values are YTD in 백만원 (printed 억원 x 100); sign as printed.  값_당분기 = rule of the builder (Q1 = YTD; Q2/Q3 = YTD - previous
quarter if present; Q4 row = None like every sibling Q4 row of this lineage).  Existing rows are never touched.
Sidecar: block (company, quarter, income_statement) gets one more source_files entry with how=disclosure_summary_pl_reinsurer (items, page, printed, unit, column).
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import bspl_granularity_load_bs as L  # noqa: E402

MASTER = ROOT / "PL_breakdown.json"
SIDECAR = ROOT / "PL_breakdown_provenance.json"
D = ROOT / "data/_derived/reinsurer_resweep_20261012"
PLAN = D / "fill_plan.json"
BACKUP = ROOT / "data/_derived/reinsurer_resweep_backup_20261012"
NAMES = {"16": "기타사업비용", "17": "투자손익", "20": "영업이익", "21": "영업외손익"}
HOW = "disclosure_summary_pl_reinsurer"


def prev_q(q):
    y, n = int(q[:4]), int(q[5])
    return None if n == 1 else f"{y}.{n - 1}Q"


def rel(path: str) -> str:
    p = Path(path)
    try:
        return p.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.replace("\\", "/")


def main():
    apply = "--apply" in sys.argv
    plan = json.loads(PLAN.read_text(encoding="utf-8"))["plan"]
    rows, raw_m = L.load_json_exact(MASTER, 1, "\r\n")
    side, raw_s = L.load_json_exact(SIDECAR, 1, "\r\n")
    by = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r for r in rows}
    for p in plan:
        if (p["co"], p["item"], p["q"]) in by:
            raise SystemExit(f"ABORT: {p['co']} {p['q']} item {p['item']} already in master")
    ytd = defaultdict(dict)      # (co, item) -> q -> value
    for (c, it, q), r in by.items():
        if r.get("값") is not None:
            ytd[(c, it)][q] = r["값"]
    for p in plan:
        ytd[(p["co"], p["item"])][p["q"]] = p["val"]

    def dangi(c, it, q):
        cur = ytd[(c, it)].get(q)
        if cur is None or q.endswith("4Q"):
            return None
        pq = prev_q(q)
        if pq is None:
            return cur
        pv = ytd[(c, it)].get(pq)
        return None if pv is None else round(cur - pv, 6)

    meta = {}
    for r in rows:
        meta.setdefault(r["원보험사코드"], r)
    print(f"plan cells {len(plan)}: " + ", ".join(f"item {k}: {v}" for k, v in sorted(defaultdict(int, {i: sum(1 for p in plan if p['item'] == i) for i in NAMES}).items())))
    added = []
    for p in sorted(plan, key=lambda p: (p["co"], p["q"], int(p["item"]))):
        m = meta[p["co"]]
        added.append({"원보험사코드": p["co"], "원수사명": m["원수사명"], "티커": m["티커"], "생손보여부": m["생손보여부"], "항목번호": int(p["item"]),
                      "항목명": NAMES[p["item"]], "공시분기": p["q"], "값": p["val"], "값_당분기": dangi(p["co"], p["item"], p["q"])})
    # sidecar: group per (company, quarter, file, kind)
    blocks = {(b["company_code"], b["quarter"], b["item_block"]): b for b in side["cells"]}
    groups = defaultdict(list)
    for p in plan:
        groups[(p["co"], p["q"], rel(p["file"]), p["kind"], p["page"], p["unit"])].append(p)
    per_bucket_new = defaultdict(int)
    entries = []
    for (co, q, f, kind, page, unit), ps in sorted(groups.items()):
        b = blocks.get((co, q, "income_statement"))
        if b is None:
            raise SystemExit(f"ABORT: no income_statement sidecar block for {co} {q}")
        if b.get("source_id") != "DISCLOSURE" or b.get("resolution") != "disclosure_summary_pl":
            raise SystemExit(f"ABORT: unexpected block {co} {q}: {b.get('source_id')} {b.get('resolution')}")
        items = sorted(int(x["item"]) for x in ps)
        ent = {"file": f, "how": HOW, "items": items, "page": page, "printed": {x["item"]: x["raw"] for x in sorted(ps, key=lambda x: int(x["item"]))},
               "unit": unit, "column": "current" if kind == "own" else "prior_year_column_of_later_filing"}
        if kind == "later":
            ent["later_filing_quarter"] = f"{int(q[:4]) + 1}.{q[5]}Q"
        entries.append((b, ent))
        per_bucket_new[(co, q)] += len(items)
    for p in added[:6]:
        print("  e.g.", p["원보험사코드"], p["공시분기"], p["항목번호"], p["값"], p["값_당분기"])
    print(f"NEW rows {len(added)} in {len(per_bucket_new)} buckets; sidecar entries {len(entries)}")
    if not apply:
        print("dry-run")
        return

    BACKUP.mkdir(parents=True, exist_ok=True)
    for src in (MASTER, SIDECAR):
        if (BACKUP / src.name).exists():
            raise SystemExit(f"ABORT: backup {BACKUP / src.name} already exists (a previous apply?) -- refuse to overwrite")
        shutil.copy2(src, BACKUP / src.name)
    snap = {k: json.dumps(v, ensure_ascii=False, sort_keys=True) for k, v in by.items()}
    for b, ent in entries:
        b["source_files"].append(ent)
    for (co, q), n in per_bucket_new.items():
        blocks[(co, q, "income_statement")]["published_items"] += n
    stamp = time.strftime("%Y-%m-%d %H:%M")
    side["merge_note_20261012_reinsurer_resweep"] = (
        f"round-8 재보사 PL 공란 재스윕(inbox/parser/20261012T0110Z, {stamp}): KR1101~KR1108 감독회계 총괄 요약 포괄손익계산서(2-1/3-2)의 투자손익(17)·영업이익(20)·영업외손익(21) "
        f"{sum(1 for p in plan if p['item'] != '16')}칸 + 기타사업비용(16) {sum(1 for p in plan if p['item'] == '16')}칸 신규 적재 -- 해당 블록 source_files 에 how={HOW} 항목을 추가하고 published_items 를 늘렸다 "
        f"(item 17/20/21 은 DART 정의와 다를 수 있어 CONCEPT_REGISTRY pl_disclosure_vs_dart 의 reference_only 이나, 재보사 8곳은 DART 사업보고서가 없어 한 회사 시계열 안에서 개념이 섞이지 않는다). "
        f"근거·재현 data/_derived/reinsurer_resweep_20261012/ (s30_final_parse.py → s31_decide.py → s33_plan.py) · scripts/reinsurer_resweep_pl_apply.py")
    for p, raw in ((MASTER, raw_m), (SIDECAR, raw_s)):
        if p.read_bytes() != raw:
            raise SystemExit(f"ABORT: {p.name} changed since read -- nothing written")
    L.safe_write(SIDECAR, L.dumps(side, 1, "\r\n"))
    L.safe_write(MASTER, L.dumps(rows + added, 1, "\r\n"))

    chk = json.loads(MASTER.read_bytes().decode("utf-8"))
    ci = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r for r in chk}
    bad = [k for k, v in snap.items() if json.dumps(ci.get(k), ensure_ascii=False, sort_keys=True) != v]
    if bad or len(chk) != len(rows) + len(added) or len(ci) != len(chk):
        raise SystemExit(f"VERIFY FAILED changed={bad[:5]} rows {len(chk)}")
    print(f"APPLIED: +{len(added)} rows (rows {len(rows)} -> {len(chk)}); all {len(snap)} pre-existing rows byte-identical; sidecar +{len(entries)} entries")


if __name__ == "__main__":
    main()
