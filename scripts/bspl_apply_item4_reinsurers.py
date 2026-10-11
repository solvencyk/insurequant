#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 6 (parser/ifrs17, orchestrator course-correction + scope addition): load PL item 4 (원수 CSM상각 slot) for

  group reinsurer17 -- the pure reinsurers KR1101~KR1107 = the total 수재 CSM amortization of the audit-report note
                       ('서비스를 제공한(당기손익으로 인식한) 보험계약마진'), 17 year-end buckets;
  group lina3       -- Lina Life KR0074 2025.3Q / 2026.1Q / 2026.2Q = the 재무제표 주석 '제공한 서비스 반영 인식한 보험계약마진' (합계, 유배당 + 유배당 외),
                       the same figure the CSM lane loaded into CSM_waterfall item 5.

Cell-level, old-value guard (the cell must be ABSENT and the bucket must have no contract_notes sidecar block), backup, one sidecar contract_notes block
per bucket.  KR1000 (Korean Re) and every other KR0074 PL item are not touched.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_item4_reinsurers.py [--apply]

Values are YTD in 백만원, POSITIVE (same convention as KR1000 item 4; CSM_waterfall item 5 is negative 억원).
값_당분기 of a new row = the builder rule `build_root_masters._flow_dangi` (Q1 = YTD; otherwise YTD - previous quarter's YTD if that exists, else None) except that a
4Q row stays None (the lineage convention of these 4Q rows).  An existing row's 값_당분기 is never touched (the existing KR0074 2025.4Q item 4 keeps None).
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import bspl_granularity_load_bs as L  # noqa: E402

MASTER = ROOT / "PL_breakdown.json"
SIDECAR = ROOT / "PL_breakdown_provenance.json"
WORK = ROOT / "data/_derived/bspl_apply_20261011/item4_reinsurers"
SPEC = WORK / "spec_item4.json"
BACKUP = ROOT / "data/_derived/bspl_apply_backup_20261011/item4_reinsurers"
PURE_REINSURERS = {"KR1101", "KR1102", "KR1103", "KR1104", "KR1105", "KR1106", "KR1107"}
LINA = ("KR0074", {"2025.3Q", "2026.1Q", "2026.2Q"})
ITEM_NO, ITEM_NAME = 4, "원수 CSM상각"
HOW = "fs_note_csm_amort"


def prev_q(q):
    y, n = int(q[:4]), int(q[5])
    return None if n == 1 else f"{y}.{n - 1}Q"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    apply = "--apply" in sys.argv
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    if spec.get("failures"):
        raise SystemExit(f"ABORT: spec has failures {spec['failures']}")
    cells = spec["cells"]
    for s in cells:
        ok_r = s["group"] == "reinsurer17" and s["company"] in PURE_REINSURERS and s["quarter"][5:] == "4Q"
        ok_l = s["group"] == "lina3" and s["company"] == LINA[0] and s["quarter"] in LINA[1]
        if not (ok_r or ok_l) or s["item"] != ITEM_NO:
            raise SystemExit(f"ABORT: spec cell outside scope {s['group']} {s['company']} {s['quarter']} item {s['item']}")
    rows, raw_m = L.load_json_exact(MASTER, 1, "\r\n")
    side, raw_s = L.load_json_exact(SIDECAR, 1, "\r\n")
    by = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r for r in rows}
    blocks = {(b["company_code"], b["quarter"], b["item_block"]): b for b in side["cells"]}
    meta = {}
    for r in rows:
        meta.setdefault(r["원보험사코드"], r)

    # ---- old-value guard
    for s in cells:
        c, q = s["company"], s["quarter"]
        if (c, "4", q) in by:
            raise SystemExit(f"ABORT: {c} {q} item 4 already in master = {by[(c, '4', q)]['값']}")
        if s["group"] == "reinsurer17":
            other = [k for k in by if k[0] == c and k[1] in ("4", "4-1")]
            if other:
                raise SystemExit(f"ABORT: {c} already carries item 4/4-1 rows {other[:3]} -- not a pure blank company")
        if (c, q, "contract_notes") in blocks:
            raise SystemExit(f"ABORT: {c} {q} already has a contract_notes sidecar block")
        if (c, q, "income_statement") not in blocks:
            raise SystemExit(f"ABORT: {c} {q} has no income_statement block (bucket must already exist in the master)")
        if s["group"] == "lina3":      # nothing else of the bucket's contract_notes items may exist (we add item 4 only)
            clash = [k for k in by if k[0] == c and k[2] == q and k[1] in ("3", "4", "5", "6", "7", "8", "9", "10", "11", "12")]
            if clash:
                raise SystemExit(f"ABORT: {c} {q} already carries leg items {clash}")
    if len({(s["company"], s["quarter"]) for s in cells}) != len(cells):
        raise SystemExit("ABORT: duplicate (company, quarter) in spec")

    # ---- values + derived 값_당분기 (builder rule; 4Q rows None; existing rows untouched)
    ytd = {}
    for (c, it, q), r in by.items():
        if it == "4":
            ytd.setdefault(c, {})[q] = r.get("값")
    for s in cells:
        ytd.setdefault(s["company"], {})[s["quarter"]] = s["value"]

    def dangi(c, q):
        cur = ytd[c].get(q)
        if cur is None or q.endswith("4Q"):
            return None
        p = prev_q(q)
        if p is None:
            return cur
        pv = ytd[c].get(p)
        return None if pv is None else round(cur - pv, 6)

    added = []
    for s in cells:
        m = meta[s["company"]]
        added.append({"원보험사코드": s["company"], "원수사명": m["원수사명"], "티커": m["티커"], "생손보여부": m["생손보여부"],
                      "항목번호": ITEM_NO, "항목명": ITEM_NAME, "공시분기": s["quarter"], "값": s["value"],
                      "값_당분기": dangi(s["company"], s["quarter"])})
    print(f"NEW item-4 rows ({len(added)}):")
    for a, s in zip(added, cells):
        print(f"  [{s['group']}] {a['원보험사코드']} {a['공시분기']} 값 {a['값']:>14,.6f} 백만원 값_당분기 {a['값_당분기']}  "
              f"(printed {s['printed']} {s['printed_unit']}, p{s['pages']}, wf {s['wf_item5_eok']} 억)")
    if not apply:
        print("dry-run")
        return

    BACKUP.mkdir(parents=True, exist_ok=True)
    shutil.copy2(MASTER, BACKUP / MASTER.name)
    shutil.copy2(SIDECAR, BACKUP / SIDECAR.name)
    h_before = {"PL_breakdown.json": sha(MASTER), "PL_breakdown_provenance.json": sha(SIDECAR)}
    snap = {k: json.dumps(v, ensure_ascii=False, sort_keys=True) for k, v in by.items()}
    snap_blocks = {k: json.dumps(v, ensure_ascii=False, sort_keys=True) for k, v in blocks.items()}

    new_cells = []
    for s in cells:
        entry = {"file": s["source_file"], "how": HOW, "items": [ITEM_NO], "page": s["pages"][0], "printed": s["printed"], "unit": s["printed_unit"]}
        if len(s["pages"]) > 1:
            entry["pages"] = s["pages"]
        new_cells.append({
            "company_code": s["company"], "quarter": s["quarter"], "item_block": "contract_notes",
            "source_id": "DISCLOSURE", "source_file": s["source_file"],
            "published_items": 1, "schema_items": 8,
            "source_files": [entry],
            "resolution": HOW,
        })
    stamp = time.strftime("%Y-%m-%d %H:%M")
    side["merge_note_20261011_item4_reinsurers"] = (
        f"round-6 PL 항목 4(원수 CSM상각 슬롯) 적재(오케스트레이터 보정·범위 추가, {stamp}): (A) 순수 재보사 17칸 = KR1101 2023/2024/2025.4Q · KR1102 3 · KR1103 3 · KR1104 2023.4Q · "
        f"KR1105 2023/2024.4Q · KR1106 3 · KR1107 2024/2025.4Q 의 감사보고서 주석(수재 일반모형 보험계약마진 열, 행 '서비스를 제공한(당기손익으로 인식한) 보험계약마진' 합계); "
        f"(B) 라이나생명 KR0074 2025.3Q · 2026.1Q · 2026.2Q 3칸 = 경영공시 PDF 에 첨부된 재무제표 주석 '제공한 서비스 반영 인식한 보험계약마진' 합계(유배당 + 유배당 외, 천원). "
        f"값 = 인쇄값(원/천원 -> 백만원, 양수, 누계), CSM_waterfall 항목 5(억원, 음수)와 |값|/100 이 0.00002억 이내로 일치. "
        f"계보: 경영공시 §2-1 요약 PL 이 아니라 재무제표·감사보고서 주석이다 -- 그러나 source_file 경로가 data/disclosure/ 라 게이트의 경로 계보 판정은 DISCLOSURE 로 귀착한다"
        f"(source_id=DISCLOSURE 만이 CHECK 2 를 통과한다). 그래서 validate_data_contract §3d(CONCEPT_MIXED_DISCLOSURE_INTO_DART, 허용항목 1·16·22·23·24)가 이 20개 contract_notes 블록의 "
        f"항목 4 를 막는다 -- how=resolution={HOW} 로 구분 표기했고 게이트 예외(또는 새 계보 id)는 validation 몫이다. "
        f"근거·재현 data/_derived/bspl_apply_20261011/item4_reinsurers/spec_item4.json · scripts/bspl_apply_item4_reinsurers.py")

    for p, raw in ((MASTER, raw_m), (SIDECAR, raw_s)):
        if p.read_bytes() != raw:
            raise SystemExit(f"ABORT: {p.name} changed since read -- nothing written")
    side["cells"] = side["cells"] + new_cells
    L.safe_write(SIDECAR, L.dumps(side, 1, "\r\n"))
    L.safe_write(MASTER, L.dumps(rows + added, 1, "\r\n"))

    chk = json.loads(MASTER.read_bytes().decode("utf-8"))
    ci = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r for r in chk}
    bad = [k for k, v in snap.items() if json.dumps(ci.get(k), ensure_ascii=False, sort_keys=True) != v]
    new_keys = set(ci) - set(snap)
    want = {(s["company"], "4", s["quarter"]) for s in cells}
    if bad or new_keys != want or len(chk) != len(rows) + len(added) or len(ci) != len(chk):
        raise SystemExit(f"VERIFY FAILED changed={bad[:5]} new_keys_diff={sorted(new_keys ^ want)[:5]} rows {len(chk)}")
    cs = json.loads(SIDECAR.read_bytes().decode("utf-8"))
    cb = {(b["company_code"], b["quarter"], b["item_block"]): b for b in cs["cells"]}
    bad_b = [k for k, v in snap_blocks.items() if json.dumps(cb.get(k), ensure_ascii=False, sort_keys=True) != v]
    if bad_b or len(cs["cells"]) != len(side["cells"]):
        raise SystemExit(f"VERIFY FAILED sidecar blocks changed {bad_b[:5]}")
    n17 = sum(1 for s in cells if s["group"] == "reinsurer17")
    n3 = sum(1 for s in cells if s["group"] == "lina3")
    print(f"APPLIED: +{len(added)} item-4 rows = reinsurer17 {n17} + lina3 {n3} (rows {len(rows)} -> {len(chk)}); all other {len(snap)} rows identical; "
          f"sidecar +{len(new_cells)} contract_notes blocks (cells {len(cs['cells']) - len(new_cells)} -> {len(cs['cells'])}), existing {len(snap_blocks)} blocks identical")
    manifest = {"applied_at": stamp, "hash_before": h_before,
                "hash_after": {"PL_breakdown.json": sha(MASTER), "PL_breakdown_provenance.json": sha(SIDECAR)},
                "added": [{"group": s["group"], "key": f"{s['company']}|4|{s['quarter']}", "value": a["값"], "값_당분기": a["값_당분기"]} for a, s in zip(added, cells)]}
    (WORK / "load_manifest_item4.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
