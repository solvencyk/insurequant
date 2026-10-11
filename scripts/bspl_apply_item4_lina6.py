#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 7 (parser/ifrs17, orchestrator follow-up): load PL item 4 (원수 CSM상각 slot) for Lina Life KR0074 six quarters whose CSM waterfall was
just backfilled (28b9e23): 2023.3Q, 2024.1Q, 2024.2Q, 2024.3Q, 2025.1Q, 2025.2Q.  2023.1Q / 2023.2Q are held for an owner decision and are NOT loaded.

Value = the 합계 of '제공한 서비스 반영 인식한 보험계약마진' of the 재무제표 주석 attached to the 경영공시 PDF (spec re-read from the source pages, see
data/_derived/bspl_apply_20261011/item4_reinsurers_lina6/spec_lina6.json), 천원 -> 백만원, positive, YTD.  Same style as scripts/bspl_apply_item4_reinsurers.py:
cell-level, old-value guard (cell + contract_notes sidecar block must be ABSENT, the bucket's income_statement block must exist, no leg items 3..12 in the bucket),
backup, one sidecar contract_notes block per cell (source_id=DISCLOSURE by path lineage; how = resolution = fs_note_csm_amort, page + printed + unit),
verification that ONLY additions happened (every pre-existing row/block byte-identical).

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_item4_lina6.py [--apply]

값_당분기 of a new row = `build_root_masters._flow_dangi` (Q1 = YTD; otherwise YTD - previous quarter's item-4 YTD if it exists AFTER this load, else None).
Existing rows are never touched -- also not the 값_당분기 of KR0074 2025.3Q / 4Q rows that become derivable (they are only printed).
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
WORK = ROOT / "data/_derived/bspl_apply_20261011/item4_reinsurers_lina6"
SPEC = WORK / "spec_lina6.json"
BACKUP = ROOT / "data/_derived/bspl_apply_backup_20261011/item4_reinsurers_lina6"
COMPANY = "KR0074"
QUARTERS = {"2023.3Q", "2024.1Q", "2024.2Q", "2024.3Q", "2025.1Q", "2025.2Q"}
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
    if {s["quarter"] for s in cells} != QUARTERS or len(cells) != len(QUARTERS):
        raise SystemExit(f"ABORT: spec quarters {sorted(s['quarter'] for s in cells)} != expected {sorted(QUARTERS)}")
    for s in cells:
        if s["group"] != "lina6" or s["company"] != COMPANY or s["item"] != ITEM_NO:
            raise SystemExit(f"ABORT: spec cell outside scope {s['group']} {s['company']} {s['quarter']} item {s['item']}")
    rows, raw_m = L.load_json_exact(MASTER, 1, "\r\n")
    side, raw_s = L.load_json_exact(SIDECAR, 1, "\r\n")
    by = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r for r in rows}
    blocks = {(b["company_code"], b["quarter"], b["item_block"]): b for b in side["cells"]}
    meta = next(r for r in rows if r["원보험사코드"] == COMPANY)

    # ---- old-value guard
    for s in cells:
        q = s["quarter"]
        if (COMPANY, "4", q) in by:
            raise SystemExit(f"ABORT: {COMPANY} {q} item 4 already in master = {by[(COMPANY, '4', q)]['값']}")
        if (COMPANY, q, "contract_notes") in blocks:
            raise SystemExit(f"ABORT: {COMPANY} {q} already has a contract_notes sidecar block")
        if (COMPANY, q, "income_statement") not in blocks:
            raise SystemExit(f"ABORT: {COMPANY} {q} has no income_statement block (bucket must already exist in the master)")
        clash = [k for k in by if k[0] == COMPANY and k[2] == q and k[1] in ("3", "4", "5", "6", "7", "8", "9", "10", "11", "12")]
        if clash:
            raise SystemExit(f"ABORT: {COMPANY} {q} already carries leg items {clash}")
    held = [q for q in ("2023.1Q", "2023.2Q") if (COMPANY, "4", q) in by]
    if held:
        raise SystemExit(f"ABORT: held quarters {held} unexpectedly carry item 4")

    # ---- values + derived 값_당분기 (builder rule on the post-load YTD map; existing rows untouched)
    ytd = {q: r.get("값") for (c, it, q), r in by.items() if c == COMPANY and it == "4"}
    for s in cells:
        ytd[s["quarter"]] = s["value"]

    def dangi(q):
        cur = ytd.get(q)
        if cur is None:
            return None
        p = prev_q(q)
        if p is None:
            return cur
        pv = ytd.get(p)
        return None if pv is None else round(cur - pv, 6)

    added = []
    for s in cells:
        added.append({"원보험사코드": COMPANY, "원수사명": meta["원수사명"], "티커": meta["티커"], "생손보여부": meta["생손보여부"],
                      "항목번호": ITEM_NO, "항목명": ITEM_NAME, "공시분기": s["quarter"], "값": s["value"], "값_당분기": dangi(s["quarter"])})
    print(f"NEW item-4 rows ({len(added)}):")
    for a, s in zip(added, cells):
        print(f"  [lina6] {a['원보험사코드']} {a['공시분기']} 값 {a['값']:>12,.3f} 백만원 값_당분기 {a['값_당분기']}  (printed {s['printed']} {s['printed_unit']}, p{s['pages']}, wf {s['wf_item5_eok']} 억)")
    new_q = {s["quarter"] for s in cells}
    print("existing KR0074 item-4 rows whose 값_당분기 is None but derivable after this load (printed only, NOT changed):")
    for (c, it, q), r in sorted(by.items(), key=lambda kv: (kv[0][2][:4], kv[0][2][5])):
        if c == COMPANY and it == "4" and r.get("값_당분기") is None and q not in new_q and dangi(q) is not None:
            print(f"    {q} 값 {r['값']} -> derivable {dangi(q)}")
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
        new_cells.append({
            "company_code": COMPANY, "quarter": s["quarter"], "item_block": "contract_notes",
            "source_id": "DISCLOSURE", "source_file": s["source_file"],
            "published_items": 1, "schema_items": 8,
            "source_files": [{"file": s["source_file"], "how": HOW, "items": [ITEM_NO], "page": s["pages"][0],
                              "printed": s["printed"], "unit": s["printed_unit"]}],
            "resolution": HOW,
        })
    stamp = time.strftime("%Y-%m-%d %H:%M")
    side["merge_note_20261011_item4_lina6"] = (
        f"round-7 PL 항목 4(원수 CSM상각) 라이나생명 KR0074 6칸 적재(오케스트레이터 후속 발주, {stamp}): 2023.3Q(FY2024_Q3 전기 열 = 소급재작성 기준) · 2024.1Q · 2024.2Q · 2024.3Q · 2025.1Q · 2025.2Q. "
        f"값 = 경영공시 PDF 에 첨부된 재무제표 주석 '당(반)분기 및 전(반)분기 중 보험계약부채(자산)의 측정요소별 변동내역(단위:천원)' 의 '제공한 서비스 반영 인식한 보험계약마진' 합계(CSM 3열 합), "
        f"천원 -> 백만원, 양수, 누계. 라이나 2023.1Q·2Q 는 소급재작성 전 기준만 인쇄돼 owner 결정 대기라 안 채웠다. 계보 표식은 라운드 6 과 같다 "
        f"(source_id=DISCLOSURE = 경로 계보, how=resolution={HOW}, 쪽·인쇄값 동반). 근거·재현 data/_derived/bspl_apply_20261011/item4_reinsurers_lina6/spec_lina6.json · scripts/bspl_apply_item4_lina6.py")

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
    want = {(COMPANY, "4", s["quarter"]) for s in cells}
    if bad or new_keys != want or len(chk) != len(rows) + len(added) or len(ci) != len(chk):
        raise SystemExit(f"VERIFY FAILED changed={bad[:5]} new_keys_diff={sorted(new_keys ^ want)[:5]} rows {len(chk)}")
    cs = json.loads(SIDECAR.read_bytes().decode("utf-8"))
    cb = {(b["company_code"], b["quarter"], b["item_block"]): b for b in cs["cells"]}
    bad_b = [k for k, v in snap_blocks.items() if json.dumps(cb.get(k), ensure_ascii=False, sort_keys=True) != v]
    if bad_b or len(cs["cells"]) != len(side["cells"]):
        raise SystemExit(f"VERIFY FAILED sidecar blocks changed {bad_b[:5]}")
    print(f"APPLIED: +{len(added)} item-4 rows (rows {len(rows)} -> {len(chk)}); all other {len(snap)} rows identical; "
          f"sidecar +{len(new_cells)} contract_notes blocks (cells {len(cs['cells']) - len(new_cells)} -> {len(cs['cells'])}), existing {len(snap_blocks)} blocks identical")
    manifest = {"applied_at": stamp, "hash_before": h_before,
                "hash_after": {"PL_breakdown.json": sha(MASTER), "PL_breakdown_provenance.json": sha(SIDECAR)},
                "added": [{"key": f"{COMPANY}|4|{s['quarter']}", "value": a["값"], "값_당분기": a["값_당분기"]} for a, s in zip(added, cells)]}
    (WORK / "load_manifest_lina6.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
