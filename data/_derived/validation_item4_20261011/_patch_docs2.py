def edit(p, fn):
    raw = open(p, "rb").read()
    nl = "\r\n" if b"\r\n" in raw else "\n"
    s = raw.decode("utf-8").replace("\r\n", "\n")
    s = fn(s)
    open(p, "wb").write(s.replace("\n", nl).encode("utf-8"))

# changelog_validation
CH = '''## 2026-10-11 (23차) -- PL 항목 4 재무제표 주석 계보 허용 + owner 승인 등재 4칸 (티켓 `20261011T2000Z`)

- **배경**: parser-ifrs17 이 재보사 17버킷 + 라이나 3버킷의 PL 항목 4(원수CSM상각)를 경영공시 PDF 에 붙은 감사보고서·재무제표 주석에서 20칸 적재(`0a7632e`)해 `PL_CSM_AMORT_VS_WATERFALL` 20→0 이 되었으나,
  경로 계보(`data/disclosure/`)가 「요약 PL」 과 「붙은 주석」 을 못 가려 두 게이트가 새로 아팠다(§3d RED 20 · ZERO_LEGS 9→23).
- **게이트 변경 (둘 다 좁게)**: ① `validate_data_contract.PL_FS_NOTE_LINEAGE = {"fs_note_csm_amort": {4}}` + `_pl_fs_note_exempt_items` -- §3d 에서 사이드카 how 가 등재되고 `resolution` 과 같고 쪽·인쇄값이 있는
  contract_notes 블록의 **항목 4 하나만** 뺀다(17/20/21·항목 5·다른 how·근거 없는 how·income_statement 블록은 계속 RED, 허용 건수는 매 실행 인쇄). 항목 4 값 자체는 `PL_CSM_AMORT_VS_WATERFALL` 이 워터폴과 대조한다.
  ② `validate_master_tables` ZERO_LEGS 「sub-leg 전부 결측 = 원천 미수록」 판정에서 `원수CSM상각` 을 다리로 세지 않는다(`PL_ZLEG_NA_IGNORED_LEGS`; 항목 4 외 값이 하나라도 있으면 종전대로 ZERO_LEGS, DART 계보는 불변).
  새 예외 등재가 아니라 계보 규칙의 정당한 확장이다.
- **양방향 시뮬레이션(수정 전, 전수)**: §3d 현행 RED 20 → 제안 RED 0 (닫힘 20 = 항목 [4] 전부, 새로 깨짐 0) · ZERO_LEGS 현행 23 → 제안 9 (닫힘 14, 새로 깨짐 0, 남는 9 는 기존 9), src_na zleg 181→195, legcov 269 불변.
  재현 `data/_derived/validation_item4_20261011/sim_item4_lineage.py`. 수정 후 실게이트가 시뮬레이션과 일치(데이터계약 RED 34→11 = §3d 20 + YTD 3 + HOLE 1 소멸, 신규 PL RED 0 · 관계없는 xlsx 드리프트 1 은 동시 세션의 CSM_amortization 수정).
- **등재 B1**: `PL_YTD_COLLAPSE_TO_ZERO` 법인세 0.0 3칸 -- 스위스리아시아 2023.2Q(요약 PL 법인세 0, 세전 509 = 순이익 509) · 퍼시픽 2024.4Q·2025.4Q(감사보고서 당기·전기 법인세 `-`) 를 `data/_gold/user_pl_confirmed_cells.json`
  (예별 2025.3Q 와 같은 경로; 값 박제 + 원문 마커 매 실행 재확인, 읽는 쪽 `check_census` 의 `_ytd_collapse_confirmed_cells`). 원문 PDF 를 다시 열어 마커 4개 전부 재현. 승인 「법인세는 네 제안대로 승인」.
- **등재 B2**: 하노버 2025.3Q PL `MASTER_HOLE` 1버킷 -- 새 등재부 `validate_kics_disclosure._PL_SOURCE_ABSENT`(NOT_POSTED; K-ICS `_CENSUS_SOURCE_ABSENT` 와 **같은 재검산 함수** `_census_source_absent` 호출: 버킷 부재·raw 폴더·
  다운로더 매니페스트·근거 원장 registry `_PL_SOURCE_ABSENT` VERIFIED + 인용 재오픈) + 원장 기록 + `_exemption_registries()` 등록. **읽는 쪽**: `validate_master_tables.coverage_holes(source_absent=)` 가 재검산 통과 칸의
  「통째」 hole 만 뺀다 -- `_check_coverage`(master_tables)와 `check_census` 1c(데이터계약)가 둘 다 호출, 면제분은 YELLOW `MASTER_HOLE_SOURCE_ABSENT`/`ABSENT-PL` 로 매 실행 인쇄, SUMMARY `pl_src_absent:1ok/0red`.
  깨진 등재는 hole RED 유지 + `PL_SOURCE_ABSENT_*` RED. 승인 「하노버 25.3q만 예외 승인」. 신규 등재는 이 4칸뿐.
- **변이시험**: `_data_contract_selftest` 75→92 (Q9 주석 계보 8 · Q10 원천부재 읽는 쪽 5 · S7~S10 ZERO_LEGS 4), pytest 신규 36건 -- `tests/test_pl_fs_note_lineage.py`(허용 넓힘·좁힘·근거/resolution/블록 조건 제거 변이 9건 + 범위 pin + 라이브 사이드카),
  `tests/test_pl_source_absent_exemption.py`(원장 부재·K-ICS 원장으로 PL 못 덮음·claim_kind/status/마커/버킷 출현/형식/raw 유입/매니페스트 드리프트/원장 손상 + 읽는 분기 제거 변이 + 등록 제거 변이), `tests/test_pl_ytd_collapse_owner_confirmed.py` 범위 pin 4칸 + 4칸 재확인.
- **골든**: `--update` 안 함. 움직이는 것은 `tests/test_master_tables_golden.py` 1종(SUMMARY: `coverage_hole 3PL→2PL`, `pl_src_absent` 토큰 신설; `zero_legs 9`·`src_na 195zleg` 는 골든값으로 복귀; 같은 골든의 closing/identity/qoq 이동은 라이나 CSM 적재분이라 이 변경과 무관).
  kics 룰 골든·post_transition·지문(pl_breakdown ok)·offline 묶음(613 통과)은 불변. 지문 게이트 RED 3 은 viz_ifrs17_panels(동시 세션의 `csm_amort_schedule.json`·빌더 수정).
- **모델**: Sonnet 5.5.

'''
def f1(s):
    anchor = "## 2026-10-11 (22차)"
    assert s.count(anchor) == 1
    s = s.replace(anchor, CH + anchor, 1)
    return s.replace("> Last updated: 2026-10-11 (22차)", "> Last updated: 2026-10-11 (23차)")
edit("docs/changelog_validation.md", f1)

EX = '''## 2026-10-11 PL_breakdown 원천부재 등재 1칸 + 법인세 0 확정 3칸 (owner 승인 채팅, validation 23차)

| 등재부 | 키 | 근거 |
|---|---|---|
| `_PL_SOURCE_ABSENT` (validate_kics_disclosure.py, 원장 registry 동명) | KR1104 하노버재보험 2025.3Q (NOT_POSTED) | 사이트 공시 목록에 2025 3/4분기 항목 없음(K-ICS 쪽 `_CENSUS_SOURCE_ABSENT` 와 같은 사실, PL 게이트는 별개라 따로 등재). 재검산 = 버킷 부재 · raw 폴더 비어 있음 · 매니페스트 `not_posted` · 원장 VERIFIED. 읽는 쪽 `coverage_holes(source_absent=)`. owner 「하노버 25.3q만 예외 승인」(2026-10-11) |
| `user_pl_confirmed_cells.json` rule=`PL_YTD_COLLAPSE_TO_ZERO` | 스위스리아시아 2023.2Q 법인세 0.0 · 퍼시픽라이프리 2024.4Q·2025.4Q 법인세 0.0 | 원문에 0 인쇄(요약 PL 법인세 0 / 감사보고서 법인세비용 `-`). 값 박제 + 인용 마커 매 실행 재확인. owner 「법인세는 네 제안대로 승인」(2026-10-11) |

경영공시 PDF 에 붙은 재무제표 주석 계보(`PL_FS_NOTE_LINEAGE`, 항목 4 한정)는 예외 등재가 아니라 계보 규칙의 확장이다 -- `docs/changelog_validation.md` 23차.

'''
def f2(s):
    anchor = "## 2026-10-11 등재 해제 5묶음"
    assert s.count(anchor) == 1
    return s.replace(anchor, EX + anchor, 1)
edit("docs/kics_gate_exceptions.md", f2)

CC = "- **2026-10-11 validation 23차**: PL 항목 4 재무제표 주석 계보 허용(`PL_FS_NOTE_LINEAGE`) + 법인세 0 확정 3칸 + 하노버 2025.3Q PL 원천부재 장치 `_PL_SOURCE_ABSENT` -- 데이터계약 RED 34→11. 상세 `docs/changelog_validation.md`.\n\n"
def f3(s):
    anchor = "## 2026-10-11 — 재보사 8곳 K-ICS 스윕"
    assert s.count(anchor) == 1
    return s.replace(anchor, CC + anchor, 1)
edit("docs/claude-changelog.md", f3)
print("ok")
