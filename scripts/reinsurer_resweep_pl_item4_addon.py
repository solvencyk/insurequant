#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-12 add-on to the reinsurer PL/BS re-sweep ticket (coordinator message): PL item 4 (원수 CSM상각 slot) for the three year-end buckets whose CSM_waterfall item 5
was just loaded by the CSM lane (57b7d78): RGA KR1105 2025.4Q, Hannover KR1104 2025.4Q, Pacific KR1107 2023.4Q.  Same method as the 2026-10-11 round 6
(scripts/bspl_apply_item4_reinsurers.py): cell-level ADD, guard (cell and contract_notes block must be absent), backup, one contract_notes sidecar block per bucket with
how = resolution = fs_note_csm_amort, page and printed value.  Values are YTD 백만원, positive; waterfall item 5 is negative 억원 (|값|/100 must match).

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/reinsurer_resweep_pl_item4_addon.py [--apply]

Each printed value was re-read from the source page (rendered image + text layer where readable) and the column sum was re-added:
  KR1105 2025.4Q  FY2025_Q4 raw PDF p136 (printed -59-), note 12 1) 당기말 (단위 천원), row '서비스의 이전을 반영하기 위해 당기손익으로 인식한 보험계약마진 금액':
                  (27,475,433) + (12,256,528) = 합계 (39,731,961) 천원
  KR1104 2025.4Q  FY2025_Q4 raw PDF p123 (printed -59-), (4) 1) 당기 (단위 원), row '보험계약마진의 상각':
                  (259,215,758) + (1,163,501,407) + (1,613,545,992) = 소계·합계 (3,036,263,157) 원
  KR1107 2023.4Q  FY2024_Q4 raw_aux audit PDF p51 (2023 열), row '보험계약마진 상각':
                  (2,703,823,148) + (9,078,072,981) = 합계 (11,781,896,129) 원
"""
from __future__ import annotations

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
WF = ROOT / "CSM_waterfall.json"
BACKUP = ROOT / "data/_derived/reinsurer_resweep_backup_20261012/item4_addon"
HOW = "fs_note_csm_amort"
CELLS = [
    {"company": "KR1104", "quarter": "2025.4Q", "value": 3036.263157, "printed": "(3,036,263,157)", "unit": "원", "page": 123,
     "file": "data/disclosure/FY2025_Q4/raw/KR1104_하노버재보험.pdf"},
    {"company": "KR1105", "quarter": "2025.4Q", "value": 39731.961, "printed": "(39,731,961)", "unit": "천원", "page": 136,
     "file": "data/disclosure/FY2025_Q4/raw/KR1105_알지에이리인슈어런스.pdf"},
    {"company": "KR1107", "quarter": "2023.4Q", "value": 11781.896129, "printed": "(11,781,896,129)", "unit": "원", "page": 51,
     "file": "data/disclosure/FY2024_Q4/raw_aux/KR1107_퍼시픽라이프리__audit.pdf"},
]


def main():
    apply = "--apply" in sys.argv
    rows, raw_m = L.load_json_exact(MASTER, 1, "\r\n")
    side, raw_s = L.load_json_exact(SIDECAR, 1, "\r\n")
    wf = json.loads(WF.read_text(encoding="utf-8"))
    wfv = {(r["원보험사코드"], r["공시분기"]): r["값"] for r in wf if r["항목번호"] == 5}
    by = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r for r in rows}
    blocks = {(b["company_code"], b["quarter"], b["item_block"]): b for b in side["cells"]}
    meta = {}
    for r in rows:
        meta.setdefault(r["원보험사코드"], r)
    for c in CELLS:
        k = (c["company"], c["quarter"])
        w = wfv.get(k)
        if w is None or abs(abs(w) - c["value"] / 100.0) > 0.00002:
            raise SystemExit(f"ABORT: waterfall item 5 {k} = {w} does not match |{c['value']}|/100")
        if (c["company"], "4", c["quarter"]) in by or (c["company"], "4-1", c["quarter"]) in by:
            raise SystemExit(f"ABORT: {k} already has item 4/4-1")
        if (c["company"], c["quarter"], "contract_notes") in blocks:
            raise SystemExit(f"ABORT: {k} already has a contract_notes block")
        if (c["company"], c["quarter"], "income_statement") not in blocks:
            raise SystemExit(f"ABORT: {k} has no income_statement block")
        print(f"  {k}: value {c['value']:,.6f} 백만원 (printed {c['printed']} {c['unit']}, p{c['page']}) wf item5 {w} 억 -> |wf|*100 = {abs(w) * 100:.6f}")
    if not apply:
        print("dry-run")
        return
    BACKUP.mkdir(parents=True, exist_ok=True)
    for p in (MASTER, SIDECAR):
        if (BACKUP / p.name).exists():
            raise SystemExit("ABORT: add-on backup exists already")
        shutil.copy2(p, BACKUP / p.name)
    snap = {k: json.dumps(v, ensure_ascii=False, sort_keys=True) for k, v in by.items()}
    snap_blocks = {k: json.dumps(v, ensure_ascii=False, sort_keys=True) for k, v in blocks.items()}
    added, new_blocks = [], []
    for c in CELLS:
        m = meta[c["company"]]
        added.append({"원보험사코드": c["company"], "원수사명": m["원수사명"], "티커": m["티커"], "생손보여부": m["생손보여부"], "항목번호": 4, "항목명": "원수 CSM상각",
                      "공시분기": c["quarter"], "값": c["value"], "값_당분기": None})     # 4Q row: None (lineage convention)
        new_blocks.append({"company_code": c["company"], "quarter": c["quarter"], "item_block": "contract_notes", "source_id": "DISCLOSURE", "source_file": c["file"],
                           "published_items": 1, "schema_items": 8,
                           "source_files": [{"file": c["file"], "how": HOW, "items": [4], "page": c["page"], "printed": c["printed"], "unit": c["unit"]}],
                           "resolution": HOW})
    side["merge_note_20261012_item4_addon"] = (
        f"round-8 add-on(조정자 지시, {time.strftime('%Y-%m-%d %H:%M')}): PL 항목 4(원수 CSM상각 슬롯) 3칸 = KR1105 2025.4Q(FY2025_Q4 p136 주석 12 합계 (39,731,961)천원) · "
        f"KR1104 2025.4Q(p123 (4) 1) 당기 (3,036,263,157)원) · KR1107 2023.4Q(FY2024 감사보고서 p51 (11,781,896,129)원). CSM 레인 57b7d78 이 올린 워터폴 항목 5 와 |값|/100 일치. "
        f"계보 표식은 2026-10-11 라운드 6 과 같다(how=resolution={HOW}). 재현 scripts/reinsurer_resweep_pl_item4_addon.py")
    side["cells"] = side["cells"] + new_blocks
    for p, raw in ((MASTER, raw_m), (SIDECAR, raw_s)):
        if p.read_bytes() != raw:
            raise SystemExit(f"ABORT: {p.name} changed since read -- nothing written")
    L.safe_write(SIDECAR, L.dumps(side, 1, "\r\n"))
    L.safe_write(MASTER, L.dumps(rows + added, 1, "\r\n"))
    chk = json.loads(MASTER.read_bytes().decode("utf-8"))
    ci = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r for r in chk}
    bad = [k for k, v in snap.items() if json.dumps(ci.get(k), ensure_ascii=False, sort_keys=True) != v]
    cs = json.loads(SIDECAR.read_bytes().decode("utf-8"))
    cb = {(b["company_code"], b["quarter"], b["item_block"]): b for b in cs["cells"]}
    bad_b = [k for k, v in snap_blocks.items() if json.dumps(cb.get(k), ensure_ascii=False, sort_keys=True) != v]
    if bad or bad_b or len(chk) != len(rows) + 3 or len(cs["cells"]) != len(blocks) + 3:
        raise SystemExit(f"VERIFY FAILED rows {bad[:3]} blocks {bad_b[:3]}")
    print(f"APPLIED: +3 item-4 rows (rows {len(rows)} -> {len(chk)}), all {len(snap)} pre-existing rows identical; sidecar +3 contract_notes blocks, existing {len(snap_blocks)} blocks identical")


if __name__ == "__main__":
    main()
