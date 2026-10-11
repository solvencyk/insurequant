# -*- coding: utf-8 -*-
"""Step 70: write the two proposal files (nothing in data/_gold or in an existing master cell is touched).

  proposed_registry_entries.json     the 3 new RED (PL_CSM_AMORT_VS_WATERFALL, Lina 2025.3Q / 2026.1Q / 2026.2Q) as candidate entries for
                                     data/_gold/pl_csm_amort_missing_ledger.json (registration is the owner's)
  proposed_fixes_existing_cells.json existing KR0074 cells that are NOT changed here (ticket: existing cells stay): the 2025.4Q amortisation
                                     rows (prior-year-end schedule) and the derivable 2025.4Q 값_당분기 cells
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
W = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
TICKET = "inbox/parser/20261011T1700Z__orchestrator__MULTI_2023.1Q-2026.2Q__csm_backfill_annual_filers_from_disclosure.md"

rep = json.loads((W / "build_report.json").read_text(encoding="utf-8"))
wf = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
amort = {r["공시분기"]: r["값"] for r in wf if r["원보험사코드"] == "KR0074" and r["항목번호"] == 5}
pages = {"2025.3Q": ("FY2025_Q3", 63), "2026.1Q": ("FY2026_Q1", "66+68"), "2026.2Q": ("FY2026_Q2", "91+93")}

entries = {}
for q in ("2025.3Q", "2026.1Q", "2026.2Q"):
    fy, pg = pages[q]
    entries[f"라이나생명보험|{q}"] = {
        "wf_amort_eok": round(abs(amort[q]), 2),
        "status": "UNADJUDICATED",
        "suggested_cause": "DISCLOSURE_LINEAGE_PL_ITEM4_NOT_LOADABLE",
        "note": (f"비상장 연 1회 DART 공시사(분기 DART 보고서 없음). 워터폴 상각은 정기경영공시 PDF data/disclosure/{fy}/raw/KR0074_라이나생명보험.pdf p{pg} "
                 f"'제공한 서비스 반영 인식한 보험계약마진'(CSM 3열 합, 유배당+유배당 외) = {round(abs(amort[q]), 2)}억이다. PL_breakdown 에는 이 분기 버킷이 있으나 "
                 f"(경영공시 §2-1 계보 항목 1·16·22·23·24) 항목 4(원수CSM상각)는 validate_data_contract 3d 가 경영공시 계보 항목을 그 5개로 제한해 "
                 f"이 계보로 채울 수 없고, 분기 DART 필링이 없어 DART 계보로도 채울 수 없다(재보사 17건과 같은 구조)."),
        "routed": TICKET,
    }
out = {
    "_what": "라이나 KR0074 CSM 워터폴 분기 3칸(2025.3Q·2026.1Q·2026.2Q) 적재로 새로 생긴 PL_CSM_AMORT_VS_WATERFALL RED 3건의 건별 등재 후보. 등재는 owner 만 한다(이 파일은 제안일 뿐, data/_gold 는 건드리지 않았다).",
    "_which_ledger": "data/_gold/pl_csm_amort_missing_ledger.json (PL 버킷은 있는데 항목 4 가 비었을 때: 룰 PL_CSM_AMORT_VS_WATERFALL). PL 에 버킷이 통째로 없는 경우가 아니라 pl_amort_coverage_baseline.json 이 아니다.",
    "_alternative": "건별 등재 대신 게이트 3z 가 source_id == DISCLOSURE 계보의 워터폴 셀은 PL 대조 대상에서 빼는 설계 변경(owner/validation). 재보사 17건(proposed_registry_entries.json in reinsurer_ifrs17_csm_20261011)과 같은 결정이다.",
    "_resolves_if": "PL 레인이 항목 4 를 채우면 룰이 사라진다. 단 3d 가 막고 있고 라이나는 분기 DART 필링이 없다.",
    "n_entries": len(entries),
    "entries": entries,
}
(W / "proposed_registry_entries.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

ex = rep["existing_master_amortisation_2025.4Q"]
pend = rep["pending_derived_2025.4Q_값_당분기_NOT_WRITTEN"]
cur_dangi = {r["항목번호"]: r["값_당분기"] for r in wf if r["원보험사코드"] == "KR0074" and r["공시분기"] == "2025.4Q"}
fix = {
    "_what": "라이나 KR0074 의 기존 칸 중 이번 적재에서 바꾸지 않은 것(티켓: 기존 칸 변경 0). 적용 여부는 오케스트레이터/owner 결정. 적용하려면 셀 단위 + 옛 값 guard + 백업 규칙으로.",
    "csm_amortization_2025.4Q": {
        "problem": ("마스터 KR0074 2025.4Q 상각 10행은 2025-12-31 스케줄이 아니라 2024-12-31(전기말) 스케줄이다. 근거: ① 값이 PDF p246/FY2025 사업보고서 두 번째 표 "
                    "(전기말, 계 2,764,859,849천원 = 27,648.6억 = 2024.4Q 기말)와 1~8년 8칸 일치, 2025-12-31 표(p245, 계 23,760.6억)와는 불일치 "
                    "② 원인: viz_build_ifrs17_panels._pick_amort_block 이 같은 캡션 <당기말> 을 물려받은 두 후보(2025 / 2024) 중 line_no 가 큰 쪽(2024)을 고른다 "
                    "③ 9·10년 칸은 공시 표의 둘째 반쪽 표를 못 읽어 None. 같은 원인이 다른 14개사에도 있다(s34_amort_panel_year_census.json)."),
        "current_master_1_to_10": ex["master_rows_1_to_10"],
        "correct_2025-12-31_1_to_10_억원": ex["correct_2025-12-31_1_to_10_억원"],
        "correct_source": "data/disclosure/FY2025_Q4/raw/KR0074_라이나생명보험.pdf p245 (당기말, 회사) = p374 (연결); 합계 행, 천원 → 억원 /1e5",
        "the_2024-12-31_schedule_as_currently_stored_is_really_2024.4Q": "p246 전기말 합계 행(1~10년)은 s12_read_amort.json 의 sep_p246.total0 + total1[:2] — 2024.4Q 상각 10행으로 추가 가능(마스터에 2024.4Q 라이나 상각 행은 없다)",
        "also_wrong_in": "data/dart/viz/csm_amort_schedule.json (라이나 FY2025 entry, yearly y1..y8 = 2024-12-31 값) — 사이트 IFRS17.html 상각 스케줄 패널이 보여주는 값",
    },
    "csm_waterfall_2025.4Q_값_당분기": {
        "current_master": cur_dangi,
        "derivable_now_by_build_csm_convention": pend,
        "note": "2025.3Q YTD 가 마스터에 생겨 build_root_masters.build_csm() 이 다음 재빌드 때 항목 1~5 의 값_당분기를 이 값으로 채운다(마스터의 2025.4Q YTD 는 1자리 반올림이라 정확 값 1,225.73 대비 +0.03 차). 이번엔 기존 칸이라 쓰지 않았다. NB 당분기 배수 2025.4Q 는 이 5칸이 채워져야 계산된다(KIDI 월납 당분기 97.56억 → 신계약 1,225.76 ÷ 97.56 = 12.56).",
    },
}
(W / "proposed_fixes_existing_cells.json").write_text(json.dumps(fix, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
print("wrote proposed_registry_entries.json (", len(entries), "entries ) and proposed_fixes_existing_cells.json")
print({q: round(abs(v), 2) for q, v in amort.items()})
