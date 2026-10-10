# -*- coding: utf-8 -*-
"""Candidate entries for the owner's PL<->waterfall ledgers (READ ONLY; the ledgers are owner-held, nothing is written there).

For every reinsurer (company, quarter) whose waterfall 상각 (abs) is >= CSM_AMORT_MIN_EOK (10억) the data-contract gate
cross-checks it against PL_breakdown 원수CSM상각. Reinsurers have no such PL cell (PL item 4 may not be filled from the
disclosure lineage, gate section 3d), so each of those cells is a RED unless the owner lists it. This writes the candidate
entries in the schema of data/_gold/pl_amort_coverage_baseline.json (PL bucket absent) and
data/_gold/pl_csm_amort_missing_ledger.json (PL bucket present, item 4 empty) to
  data/_derived/reinsurer_ifrs17_csm_20261011/proposed_registry_entries.json

Run:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20261011_reinsurer_csm_registry_proposal.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "data" / "_derived" / "reinsurer_ifrs17_csm_20261011"
sys.stdout.reconfigure(encoding="utf-8")
MIN_EOK = 10.0


def main() -> int:
    rows = json.loads((STAGE / "rows_waterfall.json").read_text(encoding="utf-8"))
    rep = json.loads((STAGE / "build_report.json").read_text(encoding="utf-8"))
    prov = {(p["code"], p["quarter"]): p for p in rep["wf_provenance"]}
    entries = {}
    for r in rows:
        if r["항목번호"] != 5:
            continue
        amort = abs(r["값"])
        if amort < MIN_EOK:
            continue
        p = prov[(r["원보험사코드"], r["공시분기"])]
        entries[f"{r['원수사명']}|{r['공시분기']}"] = {
            "wf_amort_eok": round(amort, 2),
            # the registry's own vocabulary is PARSER_GAP_CONFIRMED / UNADJUDICATED; here the parser cannot fill the cell (the
            # gate's lineage rule 3d forbids PL item 4 from the disclosure lineage), so the closest honest status is
            # UNADJUDICATED -- a dedicated status (REINSURER_PL_ITEM4_NOT_LOADABLE) is only suggested
            "status": "UNADJUDICATED",
            "suggested_status": "REINSURER_PL_ITEM4_NOT_LOADABLE",
            "note": (f"재보험사 국내지점(DART 비대상). 워터폴 상각은 감사보고서 주석(수재 일반모형 CSM 열) {p['pdf']} p{p['pages']} 의 "
                     f"'서비스를 제공한(당기손익으로 인식한) 보험계약마진' = {amort:,.2f}억이다. PL_breakdown 항목 4(원수CSM상각)는 "
                     f"validate_data_contract 3d 가 경영공시 계보 항목을 1·16·22·23·24 로 제한해 이 계보로 채울 수 없다."),
            "routed": "inbox/parser/20261011T0430Z__orchestrator__KR1101-KR1108_2024.4Q-2026.2Q__reinsurer_csm_masters.md",
        }
    out = {
        "_what": "재보사 CSM 워터폴 상각 ≥ 10억 (회사,분기) 건별 등재 후보. 등재는 owner 만 한다(이 파일은 제안일 뿐, data/_gold 는 건드리지 않았다).",
        "_which_ledger": {
            "pl_amort_coverage_baseline.json": "PL 에 (회사,분기) 버킷이 통째로 없을 때(지금 상태, 룰 PL_BUCKET_ABSENT_VS_WATERFALL)",
            "pl_csm_amort_missing_ledger.json": "재보사 PL 버킷이 생겼는데 항목 4 가 비었을 때(룰 PL_CSM_AMORT_VS_WATERFALL) — 같은 키·같은 박제값",
        },
        "_alternative": "건별 등재 대신 게이트 3z/3z-b 가 `source_id == DISCLOSURE` 계보의 워터폴 셀(감사보고서)은 PL 대조 대상에서 빼는 설계 변경(owner/validation, Opus)",
        "n_entries": len(entries),
        "entries": entries,
    }
    path = STAGE / "proposed_registry_entries.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print(f"wrote {path.relative_to(ROOT)}: {len(entries)} candidate entries")
    for k, v in entries.items():
        print("  ", k, v["wf_amort_eok"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
