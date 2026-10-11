# -*- coding: utf-8 -*-
"""Step 97: registry candidates for the 6 new PL_CSM_AMORT_VS_WATERFALL REDs of the extension (nothing in data/_gold is touched)
+ the PL item 4 amounts (백만원, YTD) that the PL lane would need if it fills them instead (lineage rule 3d decides whether it may)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
W = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
TICKET = "inbox/parser/20261011T1700Z__orchestrator__MULTI_2023.1Q-2026.2Q__csm_backfill_annual_filers_from_disclosure.md (확장: owner 전 분기 결정)"

wf = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
amort = {r["공시분기"]: r["값"] for r in wf if r["원보험사코드"] == "KR0074" and r["항목번호"] == 5}
side = {c["quarter"]: c for c in json.loads((ROOT / "CSM_waterfall_provenance.json").read_text(encoding="utf-8"))["cells"] if c["company_code"] == "KR0074"}
qs = ["2023.3Q", "2024.1Q", "2024.2Q", "2024.3Q", "2025.1Q", "2025.2Q"]
entries, pl_amounts = {}, {}
for q in qs:
    a = round(abs(amort[q]), 2)
    entries[f"라이나생명보험|{q}"] = {
        "wf_amort_eok": a, "status": "UNADJUDICATED", "suggested_cause": "DISCLOSURE_LINEAGE_PL_ITEM4_NOT_LOADABLE",
        "note": (f"비상장 연 1회 DART 공시사(분기 DART 보고서 없음). 워터폴 상각은 정기경영공시 PDF {side[q]['source_file']} 의 검토 주석 "
                 f"'제공한 서비스 반영 인식한 보험계약마진'(CSM 3열 합) = {a}억이다. PL_breakdown 에는 이 분기 버킷이 있으나(경영공시 §2-1 계보 항목 1·16·22·23·24) 항목 4 는 비었다. "
                 f"validate_data_contract 3d 가 경영공시 계보 항목을 그 5개로 제한해 이 계보로 채울 수 없다(2025.3Q 이후는 PL 레인이 항목 4 를 채워 CONCEPT_MIXED_DISCLOSURE_INTO_DART 로 바뀌었다)."),
        "routed": TICKET}
    pl_amounts[q] = {"원수CSM상각_백만원_YTD": round(abs(amort[q]) * 100, 3), "참고": "PL 항목 4 의 부호 관례 = 워터폴 상각의 절댓값 × 100(백만원)"}
out = {"_what": "라이나 CSM 워터폴 확장 6분기 적재로 새로 생긴 PL_CSM_AMORT_VS_WATERFALL RED 6건의 건별 등재 후보. 등재는 owner 만 한다(제안일 뿐, data/_gold 는 안 건드렸다).",
       "_which_ledger": "data/_gold/pl_csm_amort_missing_ledger.json", "n_entries": len(entries), "entries": entries,
       "_if_pl_lane_fills_item4_instead": pl_amounts}
(W / "proposed_registry_entries_ext.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
print(json.dumps({q: v["wf_amort_eok"] for q, v in entries.items()}, ensure_ascii=False))
print(json.dumps(pl_amounts, ensure_ascii=False))
