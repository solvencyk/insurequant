# Validation Changelog (Stage 3)

> Last updated: 2026-10-23 (32차 죽은 등재 7줄 철거 + OCI 대 BS AOCI 공란 계수 수정 · 31차 교보 KR0073 재작성 기준 적재 독립 검수 + tax22_src 룰 수정 + 골든 정리 · 30차 IFRS17 최신 비교열 적용 249칸 독립 검수 + 29차 소진율·전망 재측정 + 콜일 규칙 정정 확인 + 28차 K-ICS 최신 공시 직전 컬럼 적용 독립 검수) · Stage 3/5 — validation
> Prompt: docs/agents/claude-agent-validation.md · Authoritative rules: docs/agents/kics-json-validation-rules.md

Validation-only history. Cross-stage changes also keep a 1-line cross-reference in [`docs/claude-changelog.md`](claude-changelog.md).

> 보관: 이전 달 항목은 `docs/changelog_archive/validation/` 에 월별로 무수정 보관한다(관리 `scripts/doc_rotate.py changelog`, 현행 = 최신 항목 달과 그 전 달).

## 2026-10-23 (32차) -- 최신 비교열 적재 뒤 죽은 등재 7줄 철거 + `PL_OCI_VS_BS_AOCI` 「공란 칸을 비교가능으로 센다」 계수 결함 수정 (대상 HEAD `62ba44ed`, 티켓 `20261023T0030Z`, 증거 `data/_derived/remaining_20261022/e22_gate_cleanup/`)

- **범위**: 마스터·골드 오버레이 값 파일·예외는 건드리지 않았다. 등재는 **삭제만** 했고(추가 0, 허용오차 확대 0) 게이트 코드 1곳 · 시험 2곳 · fixture 1개를 바꿨다. 커밋·push 없음.
- **JOB 1 철거 7줄(전부 게이트가 먼저 죽었다고 인쇄한 것)**: `pl_bridge_baseline.json` 5줄 -- master_tables 2d 가 `FIXED?` 로 인쇄(KB라이프 2024.1Q 보험손익(dual) · 롯데손해 2023.2Q · 메리츠화재 2023.2Q(dual) · 한화생명 2023.1Q · 2023.2Q 보험손익(leg-coverage)) ·
  `pl_csm_amort_missing_ledger.json` 롯데손해 2023.1Q 1줄 -- data_contract 가 `PL_CSM_AMORT_MISSING_LEDGER_INERT` 로 인쇄(마스터를 직접 읽어 확인: PL 원수CSM상각 39,284백만 = 392.84억 = 워터폴 상각 -392.84억, 실제로 채워졌다) ·
  `WFY_EXCEPTIONS` 한화생명 FY2023 · 메리츠화재 FY2023 2줄 -- 게이트가 인쇄하는 문구는 없다(면제는 걸려야만 WFYEX 로 보인다). 그래서 `probe_wfy_exceptions.py` 로 면제 8개를 비우고 두 소비처(master_tables WFY 축 · `validate_csm_continuity` within-FY 축)를 직접 돌렸다:
  적재 직전 마스터(`3e53aef8`)에서는 메리츠 FY2023(양쪽 걸림) · 한화생명 FY2023(master_tables 걸림) 이 필요했고, 지금은 둘 다 안 걸린다(`probe_wfy_exceptions_before_loads.txt` 대 `probe_wfy_exceptions.txt`). 교보 FY2023 은 두 축 모두 여전히 걸려 유지.
- **철거 전후 게이트**: `validate_master_tables --no-build` exit 2 -> 2 · SUMMARY 한 글자도 안 움직임 · 2d `등재부에만 남은 것` 5 -> 0 · 기지 18 / 신규 0 불변. `validate_data_contract` RED 0 -> 0 · YELLOW 169 -> 168(INERT 1줄 소멸, 나머지 168줄은 정렬 후 동일). `validate_csm_continuity` red 0 · flagged 1(교보) 불변. 시험 248 통과 · 1 skip.
- **철거 안 한 것(근거)**: `WFY_EXCEPTIONS` 의 KB라이프 FY2024 · 교보 FY2024 · 에이비엘 FY2023 · KDB생명 FY2023 · 현대해상 FY2023 5줄은 **적재 전(`3e53aef8`)에도 이미 안 걸렸다** -- 이번 적재가 죽인 것이 아니고 게이트가 죽었다고 말하지도 않는다(owner 등재라 이 세션 범위 밖, 아래 owner 결정). `GOLD_OVERLAY_REDUNDANT`(CSM 77 · PL 22칸이 소스와 같음)는 오버레이 값 파일이라 무수정. `EXEMPTION_ABSENCE_PIN_VALUE_PRESENT` KR0097 2024.4Q 는 K-ICS 장부라 이번 적재와 무관.
- **JOB 2 결함**: `_check_pl_oci_vs_bs_aoci` 가 PL 항목25 `값_당분기` 가 None 인 칸을 건너뛰면서도(`continue`) 「비교가능 N건은 tol 이내」를 `len(pl_dangi) - n_skip - len(rows)` 로 세어 공란 칸이 통과로 집계됐다. `load_pl_dangi` 소비처는 이 함수 하나뿐이고, 값_당분기를 읽는 다른 `_check_*` 는 없다(grep 전수) -- 같은 모양의 계수 결함은 이 칸 하나.
- **전 버킷 시뮬레이션(`sim_oci_counting.py`, 항목25 374버킷 x 적재 8단계 + 작업트리)**: 작업트리 기준 현행 인쇄 「비교가능 340」 = 실제 비교 232 + 공란 108. 정정 후 = 비교한 258건 중 tol 이내 232 · flag 26 · 비교 못 함 = 공란 108 + BS 결측 8(8칸 전부 2023.1Q -- 직전 분기가 없어 구조적). 단계별 과대집계 = 공란 수(`b8c37fff` 109 · `5419a817` 122 · 지금 108). flag 집합은 두 계수에서 동일(판정식 불변; 게이트 줄 26개 diff 0).
  공란 때문에 YELLOW 에서 사라진 행(적재 전후 단계 비교): 4건 -- NH농협손해 2023.4Q(resid +40,909.6) · 농협생명 2024.4Q(-31,361.1) · 동양생명 2024.4Q(+35,860.7) · KB손해 2023.4Q(+77,358.0). 값이 고쳐져서 닫힌 행은 교보 2023.4Q 1건. 참고용 그림자(게이트 입력 아님): 지금 공란 108칸 중 BS 두 분기+누계 값이 있어 누계 차로 재구성 가능한 17칸 중 6칸이 tol 을 넘는다(농협생명 2024.4Q -39,298 · 미래에셋생명 2023.4Q -36,084 · 동양생명 2024.4Q +32,151 · 한화생명 2025.3Q -22,291 · 농협생명 2025.3Q · 흥국생명 2025.3Q).
- **수정**: 공란 칸을 `n_blank` 로 따로 세고 인쇄를 `비교한 N건 중 tol 이내 M건 | 비교 못 함: 단일분기 공란 B건 + BS 결측 S건` 으로 바꿨다. SUMMARY 필드 `oci_vs_bs_aoci:26Y` -> `26Y/108blank/8bsskip`(`counts_out` 인자 방식, 반환값 불변이라 호출자 영향 0).
- **시험**: `tests/test_master_tables_golden.py::test_oci_vs_bs_aoci_counts_blank_cells_as_not_compared` 신설 -- 합성 마스터(통과 1 · 공란 1 · 진짜 불일치 1 · BS 결측 1)로 계수 `{compared 2, blank 1, bs_skip 1, flagged 1}` 와 flag 집합 `[(A, 2024.4Q)]` 를 박제한다. 변이(`n_compared` 에서 `n_blank` 제외 삭제)를 넣으면 FAIL 하는 것을 확인했다. 기존 단언은 하나도 약화하지 않았다. `tests/test_identity_registry.py` 의 `pl_oci_vs_bs_aoci` reason 에 새 SUMMARY 형식을 적었다.
- **골든**: `tests/fixtures/master_tables_golden.json` 은 `--update` 로 재생성. 이동 원인 = 새 SUMMARY 필드 `oci_vs_bs_aoci` 뿐(수정 전 fixture 가 직전 상태와 일치했고, JOB 1 철거는 SUMMARY 를 움직이지 않았다).
- **부작용 파일**: 게이트 실행이 `data/_derived/nb_csm_validation.json` · `data/dart/viz/csm_continuity_validation.json`(메리츠 FY2023 면제 표시 소멸 = 위 철거의 실제 효과) · `csm_waterfall_validation.json` 을 다시 썼다(커밋 판은 적재 이전). `qoq_warn.json` · `pl_oci_vs_bs_aoci_warn.json` 은 바이트 불변.

## 2026-10-22 (31차) -- 교보생명 KR0073 CSM·PL 「재작성 기준」 적재 독립 검수 + `tax22_src` 룰 수정 + 골든 정리 (대상 `3e53aef8`, 후속 `eea3f61c`, 티켓 `20261021T1310Z`)

- **범위**: 이 세션은 교보 건만(다른 inbox 티켓 미접촉). 마스터·골드·장부·xlsx 는 읽기만 했고 데이터 수정 0. 코드 변경은 `scripts/validate_master_tables.py`(룰) · 시험 3개 · 골든 fixture 2개 · 티켓 1건.
- **독립 재독(`data/_derived/kyobo_validation_20261022/vreader.py` 정규식 표 판독기 · `v_reread_pl.py` · `v_reread_item4.py` · `v_reread_csm.py`, `scripts/`·`src/` 미 import)**:
  원천 = 각 기간을 비교열로 인쇄한 가장 늦은 공시(2023.1Q~4Q = FY2024 Q1~Q4, 2024.1Q·2Q = FY2025 Q1·Q2, 2024.3Q·4Q = FY2025 Q3·Q4), 별도 `나. 포괄손익계산서` 표 · `5. 재무제표 주석` 측정요소 표(CSM 소계 열).
  PL 항목 1·17·19(=재보험금융수익−보험금융비용−재보험금융비용)·20·22·23·24·25·31 x 8분기 72칸 중 70 일치, 불일치 2 = 2024.4Q 항목 25·31 (−19,969백만원; 이번 커밋이 안 건드린 칸이고 open 티켓 `20261021T1556Z` 범위). 항목 4 = 보험수익 주석 「(3) 당기손익에 인식한 보험계약마진 금액」 8/8 일치.
  CSM 항목 1~6 x 9분기(2023.1Q~2024.4Q · 2026.1Q 3블록 합산) 54칸 일치(2024.3Q·4Q·2026.1Q 는 마스터가 1자리 표기라 허용오차 0.1/0.015억). 짝: CSM 항목 5 x 100 = PL 항목 4, 2023.1Q~2024.2Q 6/6 잔차 0(원문끼리도 6/6).
- **교보 밖 변동 0**: `3e53aef8~1` 대비 마스터 CSM 51셀·PL 152셀(키 추가·삭제 0)이 전부 KR0073, 출처표 CSM 4 leaf · PL 12블록(`company_code`=KR0073), 골드 `user_csm_cells` 41키 · `user_pl_cells` 122키 · 장부 `gold_overlay_ledger` 13제거/4추가 · `csm_amort_identity_ledger` 1제거(교보 2026.1Q)도 전부 KR0073. 2024.3Q 는 값_당분기만(값 불변), 2024.4Q 불변, 2026.2Q 는 값_당분기만.
- **`tax22_src` 룰 수정**: 교보 2023.3Q~2024.2Q 법인세(255,935 · 207,353 · 104,132 · 207,857백만)는 후속 공시가 소급재작성한 값인데 룰은 같은 분기 원공시 캐시(205,722 · 156,017 · 94,234 · 188,375)만 봤다. `_tax22_prior_tier1`(다음 해 같은 기간 캐시의 전기 열을 `thstrm_*` 칸에 얹어 빌더와 같은 `fetch_dart_fs._parse` 로 읽음)를 추가해 **둘 중 하나와 맞으면 통과**, 둘 다와 어긋나면 FAIL. 편집 전 전 버킷 시뮬(`sim_tax22_vintage.py`): 643버킷 중 대조 282(캐시 없음 259 · corp_code 미해결 102) — 닫힘 4 · 깨짐 0 · 잔여 FAIL 0, 3e53aef8~1 마스터에서도 깨짐 0, 주입(+max(10,000백만,30%)) 탐지 282/282(구 규칙과 동일). 실제 함수와 시뮬 수치 일치. 등재부 신설 없음.
  시험: `test_tax22_latest_comparative_vintage_branch_is_read_and_enforced`(분기를 빼면 교보 4칸만 RED · 어느 판과도 안 맞는 값 3종 FAIL · 원공시 판 값 통과 · 최신 비교열 판 값 통과) · `test_tax22_prior_tier1_reads_annual_and_quarterly_prior_columns`(4Q = frmtrm_amount, 분기 = frmtrm_add_amount) · 매니페스트 22번 문구 · `tests/test_identity_registry.py` 문구.
- **골든**: `tests/fixtures/master_tables_golden.json` SUMMARY 3필드 갱신 — pl_bridge 3676P(진짜 1291·구성상 2050·부분 335)/2731S -> 3696P(1299·2060·337)/2711S(F 23 · NEW 0 불변, F 줄 집합 동일: 교보 2023.1Q~3Q 신규 채움 54칸으로 건너뛰던 등식 20개가 평가돼 통과) · csm_amort_identity 386P/2PIN -> 387P/1PIN(교보 2026.1Q 박제 해제, 짝이 정확히 닫혀 장부 1줄 제거) · qoq_warn 266 -> 262(교보 CSM상각 YoY 4건 소멸). tax22_src 필드는 룰 수정 후 이동 없음(282P/0F/361S). **원인 입증**: 현재 마스터에서 교보 행만 `3e53aef8~1` 판으로 되돌리고 장부도 되돌린 혼합본(`hybrid_summary.py`)이 이전 골든 SUMMARY 와 바이트 일치 -> 이동은 교보 행 하나가 원인. `builder_input_fingerprints.json` 은 `viz_ifrs17_panels` 1개만 갱신(입력 `CSM_waterfall.json` +53바이트, 그 골든 자체는 통과), 나머지 5개 ok.
- **게이트(전 -> 후, 같은 `3e53aef8` 위)**: `validate_master_tables --no-build` exit 2 불변(기지 pl_bridge 23F) · tax22_src 278P/4F -> 282P/0F · 데이터계약 RED 0 · YELLOW 169(publishing `eea3f61c` 로 xlsx 동기 완료, `MASTER XLSX RED=0`) · 연속성 red 0 · 워터폴 41/0 · NB 5/0 · 커버리지 기존 RED 1 불변(KR1098 2023.4Q) · `test_rule_coverage_manifest` 104 passed(+2 신규) · `test_master_tables_golden` · `test_identity_registry` · 골드 오버레이 · 입력지문 · viz 골든 2종 통과. 17BS 골든(8분)·`prepush_check.py` 는 안 돌렸다(오케스트레이터 몫).
- **판정·발견**: (1) 2023.3Q 단일분기(값_당분기) 이음매 = parser 티켓 `inbox/parser/20261021T1655Z__validation__KR0073_2023.3Q__single_quarter_vintage_seam.md`. 2023.1Q·2Q 누계는 재작성 전 기준(재작성 후 상반기 값은 미공시)이라 3Q 단일분기가 재작성 효과를 통째로 얹는다 — 공시 3개월 열 대조: 보험손익 190,929 대 89,282 · 당기순이익 83,882 대 8,175 · 항목 4 252,287 대 150,548(백만원), CSM 단일분기 항등식 +960.03억. 누계 방식에서 불가피하다는 parser 판단에는 동의하나, 이 칸들은 적재 전 **빈 칸**이었으므로 값을 싣는 쪽이 원칙 위반 후보라 선택지(A 비움 · B 3개월 열 사용 · C 주석)를 티켓에 올렸다. 어떤 게이트도 단일분기 항등식을 안 보며 전 회사 5건 어긋남(룰 설계 범위는 TODO). (2) BS 2023.4Q·ILP 는 원공시 기준(보험계약부채 87,533,336 = 원공시, 재작성 87,242,879)이라 CSM 워터폴·PL 과 기준이 다르나 어느 게이트도 이 짝을 안 보고 새 RED 0 — 보고된 한계로만 둔다. (3) 교보 외 17사 51버킷에서 다음 해 전기 열이 마스터와 다름(참고, 방침 확인용).
- **부작용 파일**: 게이트 실행이 `data/_derived/qoq_warn.json` · `pl_oci_vs_bs_aoci_warn.json` · `data/_derived/nb_csm_validation.json` · `data/dart/viz/csm_continuity_validation.json` · `csm_waterfall_validation.json` 을 다시 쓴다(결정적 산출, 현 마스터 반영). 증거·재현: `data/_derived/kyobo_validation_20261022/`(`sim_tax22_vintage.txt` 시뮬 · `v_reread_*.txt` 재독 · `v_diff_scope.txt` 범위 대조 · `hybrid/` 원인 입증 · `gates_before/`·`gates_after/`).


## 2026-10-13 (30차) -- IFRS17 「최신 비교열」 적용 249칸 독립 검수 + 골든 정리 (티켓 `20261012T2230Z`, 대상 `b8c37fff` · 후속 `99c7ead7`·`638ebabb`)

- **방법**: parser 증거(`evidence_*`)·계획 표시는 열지 않고 `applied_cells.csv` 는 칸 목록으로만 썼다. 자체 코드(`lib_dart.py` lxml 표 판독 · `lib_pl.py` 손익계산서 행 정의 · `lib_tier2.py` 주석 표 레시피 탐색)로 원문 XML 을 읽었고, **레시피를 정하는 방법은 현재 기간 보정**이다: 같은 공시의 당기 열이 마스터의 당기 값(예: 2024.1Q)을 재현하는 행 조합을 먼저 찾고 그 조합을 전기 열에 적용한다(삼성화재 · DB손보 주석 13/13 보정, 메리츠 13/13, CSM 6/6). BS 는 같은 공시 당기말 열이 마스터 값과 맞는 표(별도 기준)를 고른 뒤 전기말 열을 읽었다.
- **결과(249/249)**: BS 65 = 다음 결산 공시 전기말 열 · CSM 27 = 측정요소 변동표(삼성화재 12칸은 당기 표 6/6 · 전기 표 6/6, 메리츠·삼성생명·DB생명·동양·농협은 CSM 3열 합/소계 + 마감 항등식 잔차 0.0억; 동양 항목 4 −240.1 은 인쇄 −240.04 와 반올림 차, 농협 항목 4 1,836.4 는 부채 행 기준 마감 잔차로 2Q~4Q 와 같은 규약 — 인쇄 소계 1,866.15 와는 다르다) · PL 157 = 삼성화재·DB손보·메리츠 후속 공시 전기 열(주석 레시피 + 손익계산서 행) 141 + 3개월 열 정정 14(원 공시 2023.2Q 표의 **누적 열 인쇄값과 일치**) + 한화손보 기타사업비용 2(경영공시 PDF 두 판: 23.1Q 257억 · 23.2Q 529억, 마스터의 옛 39,900·84,500 은 24.1Q·24.2Q 열 399·845). 마스터 변경은 PL 157 · CSM 27 · BS 65 에서 정확히 그 칸뿐이고 파생 `값_당분기`(PL 236 · CSM 42행)는 규칙대로(잔액 항목은 재고 규칙). 골드 지속: `user_pl_cells` +157 · `user_csm_cells` +27 · `bs_manual_overrides` +65, 기존 owner 칸 변경·삭제 0, 계획 칸과 값 1:1. **gold 충돌 59블록**은 적용 칸이 하나도 그 블록 칸이 아니다(회사·분기가 같은 4블록은 다른 항목).
- **3개월→누적 14칸 분기 산술**: 12칸은 `2Q 누적 = 마스터 1Q + 인쇄 3개월` 잔차 0. 2칸은 새 값 = 인쇄 누적이지만 **마스터 1Q 칸이 어긋남**: 흥국화재 항목 19(1Q −83,304 대 후속 공시 −86,247, 재보험금융비용 2,943 누락 의심) · 푸본현대 항목 18·19(1Q −0.19 · 40,277.5 대 −72,286.4 · 112,563.7). 적용 전에는 옛 3개월 값이 우연히 흐름값을 맞췄다 — parser 티켓 `20261012T1820Z`로 발주(고치지 않음).
- **예외 해제 10줄**: DB손보 2023.1Q~3Q · 메리츠 2023.3Q 보험손익 dual(적용 형태 `ΣLOB + 기타영업수익 − 기타사업비용` 잔차 0.1~0.3) · 한화생명·한화손보 2023.2Q 세전이익 = 영업이익 + 영업외손익(잔차 0.000) · DB손보 CSM상각 PIN 3(PL 3,118.50/6,193.43/9,357.89억 대 워터폴 3,118.50/6,193.40/9,357.90억) · 농협생명 FY2023 기초 CSM 4분기 모두 42,505.2(2024.1Q 기초 = 2023.4Q 기말 44,773.9) — 전부 숨은 RED 없이 스스로 닫힌다(`k8_release.txt`).
- **파생 산출물(publishing `99c7ead7`)**: NB_CSM_multiple 변경 12잎 = 동양 2023.1Q·2Q · 메리츠 2023.3Q·4Q, 분자(`CSM_waterfall` 항목 2 연누계·당분기)로 재계산하고 분모(월납월초보험료)는 불변을 확인. `panel_csm_combo` 8잎 + `est_unreliable` 13→12(KB라이프가 빠짐: 2023.4Q 보험계약부채가 재작성 사이드카와 같아져 추정 편차 0.07%)를 마스터에서 재계산해 일치. `panel_compare` 12개 지표 × 658잎 전부 재계산 차이 0(적용 전부터 낡았던 6잎 = K-ICS `74a415bf` 의 현대해상·삼성생명 값, 지금 133,381 · 532,471 로 맞다); ROE 3잎(예별)은 자본 조건 차이로 내 재계산이 값을 내고 패널은 비움 — 이번 적용과 무관.
- **경영공시 PDF 미결정 116칸(parser 자동 대조 못 끝낸 칸)**: 요약 쪽 행 재독 63 + 전체 PDF 행 재독 24 + 스캔 쪽 육안(AIA 12 · 하나생명 5 · 카카오페이 10) 27 + 부호 분리 인쇄 1 + 인쇄 행 없음 1(하노버 2023.1Q 기타사업비용 0) = 116/116, 불일치 0.
- **게이트·골든**(`gates/`, 부작용은 `gate_overlay` 로 격리): `validate_data_contract` RED 0 · YELLOW 170 · `validate_master_tables --no-build` pl_bridge 29→23F(신규 0)·csm_amort PIN 5→2·qoq 267→266·oci_vs_bs_aoci 14→22(YELLOW) · 연속성 · ILP 포트폴리오 · ILP LIC · NB 5/5 · 워터폴 · xlsx 드리프트 0(대조 120,704행) 전부 적용 전과 같거나 의도한 이동. `csm_coverage` exit 1 = 카카오페이 2023.4Q(적용 전부터 있던 기지). **골든**: `master_tables`(SUMMARY 네 토큰 이동 전부 위 수치) · `ifrs17_bs`(sha 만 이동; 빌더 산출 바이트 = 커밋 마스터, 재빌드 안전) · 입력지문 2종(ifrs17_bs 입력 `bs_manual_overrides` +38,939바이트 · viz_ifrs17_panels +1바이트) `--update`. 무이동: PL 빌더 골든(`RUN_PL_GOLDEN=1`, 174초) · viz 패널 · viz CSM(출력 5파일 백업 대비 바이트 동일, publishing 커밋과 같음).
- **관찰 · 한계**: `oci_vs_bs_aoci` 새 YELLOW 8(삼성생명 2024.4Q +5.39조 · 2025.1Q −5.51조 = 2024.4Q 만 재작성 기준·2025.1Q 는 원 기준인 단절 등) 은 골든에 박제됐다 — 해소는 parser 몫. 이 일을 하던 중 느슨한 `python` 호출 2개가 남긴 고아 프로세스를 `taskkill` 로 정리했는데 `python3.13` 프로세스 2개를 이미지 이름으로 죽였다(다른 에이전트 것일 수 있다). 영향 확인은 하지 못했다.

## 2026-10-13 (29차 후속) -- 콜일 규칙 정정 독립 확인, 티켓 `20261013T0205Z` 종결 (HEAD `20a700a9`)

- **대상**: publishing `7e6e55d0`(데이터·코드: 기발행 차감 제외 = 첫 콜일 <= 분자 기준일, 원장 플래그는 보조) + `20a700a9`(공개본). 직전 판 `6fd00720` 대비 바뀐 감사 대상 파일은 `kics_tier2_utilization.json` 과 공개 시트 `보완자본소진율` 뿐이고, 기본자본 JSON · 전망 JSON · 타임라인 JSON · 원장 · 등재부 · 마스터 · `K-ICS.html` · `theme.js` 는 **바이트 동일**이다(`h1h_delta_vs_previous_20a700a9.txt`).
- **독립 재계산(`h1_tier2_recompute_47.py`, 규칙을 첫 콜일 <= 2026-06-30 으로 바꿔 구현 코드 없이 다시 계산)**: 47/47 일치(0.1%p), 원장 차감액 · 인쇄값 보존 · 적용 전 열 · 한도 47사 일치. 메리츠 **37.5** · 아이엠라이프 **70.4** · KB라이프 **0.8**, 발행 JSON 의 이전 판 대비 변동도 이 3사뿐(44사 불변)이고 내 재계산의 변동과 회사·값이 같다. 콜일이 기준일 당일인 채권을 제외하지 않는 경계 변형은 변동 0(그런 채권 없음), 잔존만기 체감 변형도 변동 0(체감이 움직이던 콜 경과 채권이 빠졌다).
- **기본자본 · 전망 · 타임라인**: 기본자본 47/47(결속 갈래 없는 33사 한도 10%, 하나생명 238.2 · 교보 70.1 · DB손보 151.6), 전망 7사 손계산 35점 차이 0 · 전망 JSON 행 변경 0, 타임라인 JSON 대 원장 126건 차이 0.
- **공개 시트(`e11_public_sheet_delta_20a700a9.txt`, `e7`)**: 기본자본소진율 · 자본비율전망 · 자본성증권발행현황 변경 0. 보완자본소진율은 658행 · 열 · 항목명 구조가 같고, 값 변경 = 3사의 분자(메리츠 9,724.88→11,824.88, 아이엠라이프 2,109.54→2,609.54, KB라이프 0.0→108.51) · 소진율 · 레거시 후순위(5,960→3,860, 500→0, 1,999.51→699.8), 나머지 변경은 47사 3개 행의 비고 문구(「첫 콜일이 분기말 이전인 채권 제외」)뿐이다. 시트 대 JSON 불일치 0, 시트 대 내 재계산 329칸 불일치 0.
- **화면**: 같은 필드를 읽는다. 47사 x 1280/375 DOM · 도넛 · 숫자 줄 · 툴팁 불일치 0(`h5`·`h6`), 툴팁 잘림 0(`h7`). 메리츠 37.5%(「보완자본 한도 적용 전 11,825억원 / 한도 31,554억원 경과조치 기발행 후순위 3,860억원」) · 아이엠라이프 70.4%(「2,610억원 / 3,707억원」, 차감 후순위 0 이라 그 줄 없음) · KB라이프 0.8%(「109억원 / 13,586억원 경과조치 기발행 후순위 700억원」)를 두 폭에서 확인하고 375px 은 캡처로도 읽었다.
- **판정**: 티켓 `20261013T0205Z` resolved(`_resolved/` 로 이동, 종결 노트에 측정값과 재현 명령). 공유 감사 티켓 `20261012T2040Z` 가 요구한 불일치 항목(원 감사 S-1~S-7, 재측정 1건)은 모두 닫혔고 최종 판정은 PASS 다. 남은 것은 owner 결정(판정 불가 분류 · 기본자본 결합 규칙 · IBK TAC 등, `TODO_validation.md` 열린 일)뿐이다. 공유 티켓은 오케스트레이터가 종결한다. 하네스: 한 번에 47사 툴팁을 돌리면 45초 제한에 걸려 24사씩 나눴다.
- **모델**: Sonnet 5.5, 이번 구간 토큰 약 0.2M.

## 2026-10-13 (29차) -- 소진율·전망 재측정 (티켓 `20261012T2040Z` 재실행, 읽기 전용)

- **범위·방법**: 코디네이터 재측정 요청(① tier2 새 규칙 ② tier1 한도 ③ 전망 ④ 타임라인 ⑤ 화면·공개 시트). 대상 HEAD `6fd00720`(publishing `48c7c3ac`·`c05170a7`·`10b45d71`·`392efee2`, designer `75234ddf`·`258d3c30`, parser-kics `74a415bf`). 마스터 `kics_disclosure.json` 은 `dbbffcb5` 대비 38칸이 바뀌었지만 2026.2Q 칸은 0건이다(`h0_master_diff_6fd00720.txt`, `a2` 덤프가 이전 덤프와 바이트 동일). 스크립트는 구현 코드를 import 하지 않고 git 고정판을 읽는다(`audit_io.py`; `a2`·`d1` 도 고정판 읽기로 바꿈). 마스터·등재부·HTML·`public_exports`·게이트 코드·공유 티켓은 건드리지 않았다.
- **① tier2(새 규칙)**: 분자 = 항목 47(적용 전) - 항목 49(인쇄 47 이 49 를 포함할 때) - 원장 신종 - 원장 후순위(분자 기준일 잔액 중 발행일 <= 2022-12-31 이고 `past_call_outstanding`=false), 분모 = 항목 14 값 x 50%. 독립 재계산 **47/47 일치(0.1%p)**, 원장 차감액 47사 일치, `*_printed_eok` 인쇄값 보존 47사 일치, 적용 전 열 소진율 47사 일치, 한도 47사 일치(`h1_tier2_summary_6fd00720.txt`). 이전 판(`dbbffcb5`) 대비 15사 변동(메리츠 0.2→30.8 · 한화손해 46.7→46.6 · 롯데 53.5→58.6 · 흥국화재 45.3→53.3 · KB손해 20.3→20.5 · 농협손해 103.9→102.8 · 악사 2.0→29.2 · 한화생명 70.5→74.8 · 흥국생명 10.6→37.0 · 교보 51.6→51.5 · 아이엠라이프 49.5→56.9 · 푸본 86.6→73.1 · KB라이프 0.8→0.0 · 농협생명 18.8→21.1 · IBK 76.0→76.2)은 전부 위 규칙으로 설명된다. 설명 요청 회사(`h1g_sensitive_companies_6fd00720.txt`): 흥국화재(+8.1%p = 콜 경과 제1회 신종 920억을 안 뺌, 발행사 인쇄값과 반대로 움직임) · 악사(JPY 후순위 1건, 발행일 없음·콜일 「지금」 추정·플래그 true 라 차감 0, 29.2% 는 그 추정 위에 있음) · 아이엠라이프(원장이 2025-12-31 기준이고 전환우선주가 없음: 해석에 따라 16.0~70.4%).
- **불일치 1건(발주)**: 원장 `past_call_outstanding` 가 각 행 `as_of` 기준이라 첫 콜일이 분자 기준일(2026-06-30) 이전인 3건이 차감에 남는다 - 메리츠 제7회 후순위 2,100억(행이 2026-06-30 기준인데 콜일 2026-04-12 가 앞, 같은 원장의 다른 6건은 true) · 아이엠라이프 사모사채 500억 · KB라이프 제1회 후순위 1,299.7억(두 행은 2025-12-31 기준). 규칙의 근거(콜일이 지난 채권은 실효 만기 경과)를 그대로 적용하면 메리츠 30.8→37.5 · 아이엠라이프 56.9→70.4 · KB라이프 0.0→0.8(`h1b_pastcall_flag_check_6fd00720.txt`). publishing `20261013T0205Z`. 표기 1건 동봉(신한이지 `rule` R1 인데 `item47_scope` EXCL, 값 0).
- **② tier1**: 47/47(0.15%p, 한 자리 반올림), 인쇄 한도(결속 갈래 없는 33사 = SCR x 10%, 15% 로 남은 곳 0) 47/47, 초과분 두 JSON 47/47, 이전 판 대비 소진율 변동 0, 하나생명 238.2 · 교보 70.1 · DB손보 151.6(DB손보는 owner 확정이라 다시 플래그하지 않음)(`h2_tier1_check_6fd00720.txt`). 증권별 X 검정을 마스터 변경 반영해 재실행: AGREE 12 · AGREE(weak) 1 · DISAGREE 2(DB손보) · UNDECIDED 4, 등재부 분류가 뒤집히는 건 0.
- **③ 전망**: 7사 35 시리즈점 손계산 차이 0, 이전 판 대비 총자본 경로 230점 차이 0 · 기본자본 경로 차이 0, 이전 판과 다른 행은 KR0050 `confidence` 뿐(`d1_forward_handcalc_6fd00720.txt`). 46사 내부 정합(자본/SCR)은 예별·롯데 잘림 + 마이브라운 반올림 3사 그대로(`d2_...`)이고, 화면이 이제 이를 거짓 개선 없이 다룬다.
- **④ 타임라인·공개 시트**: 타임라인 JSON 대 원장 126건 값 차이 0(DB손해 제1·2회 `outstanding_eok` null + `call_date_unconfirmed`, 하나손해 추정 행 999억 `estimated`; `e9`). 공개 시트 기본자본소진율 · 보완자본소진율 · 자본비율전망은 JSON 대 47/47/460점 불일치 0, 내 재계산 대비 329칸 불일치 0(분자·차감 신종/후순위·2022년 이전 잔액 행·한도 10%/15%), 자본성증권발행현황 124행 대 원장 필드 차이 0(`e7`·`e10`).
- **⑤ 화면(`h9_screen_results_6fd00720.txt`)**: 47사 x 1280/375 모두 DOM·Chart.js 객체 불일치 0(`h5`), 툴팁 본문 불일치 0(`h6`; 100%+ 두 줄, 자본잠식 해는 숨은 3번째 시리즈만 활성, 하나손해 2026 막대 「추정(원장 미갱신)」 꼬리), 상자 폭이 캔버스를 넘는 툴팁 0(`h7`; 375px 최대 223 대 325, 이전 판 329·341·349), 가로 넘침 0. 실제 호버로 동양·하나생명 도넛(두 줄 전체 표시)·예별 전망 2027(「자본잠식」)·하나손해 막대(꼬리)를 육안 확인. 예별·롯데 노트는 기준선 △ · 변화 「—」 · 안내 한 줄이고 거짓 개선이 없다. 공유 이미지 15사 x 섹션(`h8`)에 차트가 들어 있다. 라벨은 메모 §5 와 같다.
- **하네스 메모(제품 결함 아님)**: 내장 브라우저는 유휴일 때 `requestAnimationFrame` 이 0회 돌아 새로 만든 Chart.js 차트가 빈 채로 복사된다 -> 공유 이미지 검사는 `Chart.defaults.animation=false` 로 했다. 합성 호버 이벤트에는 `native: true` 가 있어야 Chart.js 가 좌표를 읽는다(처음에 빠뜨려 전망·막대 툴팁이 비어 보였고 고쳤다). 이번 작업 중 `python3 -`(스토어 파이썬 stdin 대기)를 잘못 한 번 실행해 멈춘 프로세스를 즉시 종료했다.
- **한계**: 분자 기준일 이후의 상환 여부는 2025-12-31 기준 원장 22행에서 알 수 없다(그래서 위 3건은 「기준일 이전 콜 = 차감 안 함」이 상환됐든 남았든 맞다고 본다). 악사 JPY 후순위는 원문 PDF 를 읽지 않았다. 툴팁 폭은 Pretendard 가 로드된 상태의 글리프 폭이라 수 px 달라질 수 있다.
- **모델**: Sonnet 5.5, 이번 재측정 구간 토큰 약 0.35M, 소요시간은 오케스트레이터 측정.

## 2026-10-13 (28차) -- K-ICS 「최신 공시 직전 컬럼」 적용 65칸 독립 검수 + 골든 정리 (티켓 `20261013T0010Z`)

- **대상·방법**: parser-kics `74a415bf`(owner 2026-10-12 승인) = 16블록 65칸(primary 33 · 적용후 미러 22 · 파생 27·28 10), 보류 10블록. 감사 산출물 `data/_derived/kics_latest_prior_apply_audit_20261013/`(parser 증거 파일은 열지 않고 `applied_blocks.csv` 는 칸 목록으로만 썼다). 원본 PDF 를 자체 판독기(`lib_kics.py`: PyMuPDF word 좌표 -> 행·열 군집, 열 머리 분기 라벨로 컬럼 확정)로 읽었고, 자동 판독이 못 닫은 칸과 스캔 쪽은 행 덤프·240dpi 렌더링 육안으로 읽었다.
- **① primary 33칸**: 새 값 = 최신 공시(F+2, 2026.1Q 둘은 F+1)의 직전/전전 컬럼 인쇄값 **33/33**. F+1·F+2 두 공시가 같은 값이다. 자기 공시 인쇄값 대조: 28칸은 자기 공시 = 옛 마스터(진짜 재작성), **5칸은 마스터 오류**(KR0049 2025.1Q 항목 3 자기 2,331 · KR0049 2026.1Q 항목 4 자기 3,820 · KR0071 2024.4Q 항목 4 자기 33,924 · KR0080 2026.1Q 항목 3 자기 4,280 = 스캔/그림 쪽을 렌더링으로 읽음, KR0003 2023.4Q 항목 4 = 자기 공시 활자 오류 `2,481`, 구성합 24,808, 후속 둘 24,807). KR0072 2025.2Q 항목 12 는 자기 `-`(0) 이고 후속 둘이 328. 육안 렌더링 10쪽 = 위 스캔 4 + KR0003 p41 + KR0009·KR0004·KR0032·KR0072·KR0003 의 F+2. 원장 신규 29칸(`h1_ledger_check.txt`) = primary 33 중 자기 공시값이 새 값과 다른 29칸과 1:1(as_filed · restated · 마스터 현재값 일치). 표 `e1_final_table.csv`(65행, 쪽 번호·인쇄값).
- **② 미러 22칸 · 파생 10칸**: 미러는 새 primary 값의 복사이며 전제(그 줄은 경과조치가 안 바꾼다)를 후속 공시 본문에서 읽었다(KR0009 비적용 · KR0049 TIR 만 적용 -> 보완자본 불변 · KR0050 · KR0069 · KR0080 · KR0095 비적용 · KR0099 TFI 만 적용 -> 구성항목 불변). 파생 10칸은 항목 1·2·14 에서 재계산해 |차| ≤ 1e-5(적용전·적용후), 16블록 전 칸 27·28 재검산 불일치 0. **마스터 diff = 정확히 65칸**(레코드 30,011 · 추가/삭제 0 · 필드 `값`·`값_적용후` 만).
- **③ 보류 10블록 전부**: KR0070 2024.3Q 항목 22 = 자기·F+1·F+2 모두 1, 마스터 0, `recalc_kics_derived.py`(항목14=항목15 · 항목23=0 이면 항목 22 를 0 으로) 가 1 을 다시 0 으로 되돌림을 메모리에서 재현(f2_kr0070). 나머지 9블록은 F+1 과 F+2 가 서로 다르다(8블록: 자기=F+1=마스터, F+2 만 ±1 · KR0051 2023.3Q: 자기 -321 · F+1 -332 · F+2 -333 · KR0100 2025.2Q: F+2 만 항목 5 4,941 · 항목 11 275, 둘이 서로 상쇄해 산수로 판별 불가). 보류 타당, 10블록 마스터 불변.
- **④ 게이트**(한 번에 하나, `gates/`): `validate_kics_disclosure` exit 0 · RED 56->54(풀린 KR0003 2025.1Q·KR0032 2024.3Q 의 `2_tier1_bridge` 2건, **새 RED 0**) · 이동한 (회사,분기,룰,상태) 31건은 전부 적용 16블록 안(블록 밖 0) · 반올림 GREEN->YELLOW(잔차 ±1~2, tol 2) 포함. `validate_data_contract` exit 0 RED 0 YELLOW 165(재작성 박제 14버킷 재검산 통과) · `validate_master_tables --no-build` SUMMARY 가 parser 최종 판과 한 줄도 다르지 않다(exit 2 는 기지 29건 pl_bridge 때문, 골든이 고정) · `check_master_xlsx_drift` 드리프트 0 · `test_rule_coverage_manifest` 102 통과 · identity 계열 통과.
- **⑤ 골든·시험 정리**: `kics_rules_golden` — 기준선(`74a415bf^` 마스터)을 같은 엔진으로 돌리면 골든 sha 와 일치(골든 = 적용 직전 상태)하고 현재와의 차이는 위 31건뿐이라 의도된 변화로 판정해 `--update`(YELLOW 1,936->1,934 · GREEN 13,705->13,709 · RED 56->54). `builder_input_fingerprints` 4종(ifrs17_bs·pl_breakdown·dividend·post_transition)은 입력 `kics_disclosure.json` +3바이트뿐 — 앞 셋은 이 파일에서 회사명·티커·생손보만 읽으므로(코드 확인) 산출 불변, post_transition·dividend 골든은 실행해 통과. 시험 고침: `test_rule_coverage_manifest.KICS_RESTATEMENT_CENSUS` 10->39(원장 +29, 검사는 느슨하게 하지 않고 숫자만) · `test_tier2_issuer_inconsistent_exemption` 3건 = 등재 22->20, 결측 시험 대상 KR0003 2025.1Q -> KR0004 2025.1Q, 갈래 박제 시험은 `branch=` 박제 버킷이 0 이 돼 KR0029 2025.3Q 의 flag 를 시험 안에서만 `branch=CAPPED` 로 monkeypatch(대조군 추가, 지우지 않음).
- **⑥ 하지 않은 것 · 관찰**: ① PL·17BS 골든 미실행(빌더가 마스터를 인플레이스로 덮고 parser-ifrs17 이 같은 시간에 작업 중 — 동시 쓰기 위험; 입력지문 갱신 근거는 위 코드 확인) ② `tests/test_data_contract_selftest.py` 는 단독 실행 시 실패한다(`validate_master_tables.py:31` 의 무가드 `sys.stdout.reconfigure` 가 StringIO 리다이렉트 중 import 에 걸림). 훅의 묶음 실행에서는 앞선 시험이 먼저 import 해 통과하며(42 통과로 확인), 직접 `--selftest` 는 102/102 — 적용과 무관한 순서 의존 결함, 미수정. ③ KR0009 2023.1Q 의 적용후 항목 2·3·28(미러)은 자기 공시 `해당사항 없음`·후속 공시는 적용후 지급여력금액 합계만 인쇄해 독립 확증이 없다(같은 회사 2023.2Q 는 TFI 로 적용후 기본자본이 +5,000 이동) — 적용 전에도 전=후였던 기존 가정이고 이번 적용이 만든 문제는 아니다. ④ `scripts/validate_kics_disclosure.py`·마스터·원장은 손대지 않았다.
- **커밋 범위**: 시험 2 · 골든 fixture 2 · 감사 폴더 · TODO/changelog/archive. 티켓 파일은 고치지 않았다(오케스트레이터가 종결).

## 2026-10-12 (27차) -- 소진율·전망 복원 독립 감사 (티켓 `20261012T2040Z`, 읽기 전용)

- **범위·방법**: 오케스트레이터 티켓 4항목(① 47사 독립 재계산 ② 규정 대조 ③ 전망 7사 손계산 ④ 화면 대 JSON 10사 이상·375px). 대상 = publishing `dbbffcb5`·`24a3dd6c`, designer `496d359e`·`47f983ea`(HEAD `8fe48b1b` 까지 대상 파일 동일, `git diff dbbffcb5..HEAD` 로 확인). 스크립트는 `scripts/`·`src/` 를 import 하지 않고 `audit_io.py` 로 git 고정판만 읽는다 -- 공유 워킹트리에서 publishing 이 도중에 등재부·JSON 을 고치는 것을 겪어 도입했고, 처음 `ef62969` 로 잰 결과는 `dbbffcb5` 재측정 뒤 지웠다. 마스터·등재부·HTML·`public_exports`·게이트 코드·공유 티켓은 건드리지 않았다. 재현물 전부 `data/_derived/capsec_audit_20261012/`.
- **① 재계산(2026.2Q, 허용오차 0.1%p)**: 기본자본 47/47 · 인정한도(항목 14 값 × 50%) 47/47 · 초과분 필드(두 JSON) 47/47 · 보완자본 정의 문자 그대로 45/47 · 적용 전 열 46/46. 불일치 2 = 미래에셋(24.5 대 0.0)·DB생명(31.6 대 0.0): 항목 54 인쇄값에 2023년 이후 신규채가 섞여 발행연도로 덮어쓴 것(문서화됨). 발행사 헤드라인 항목 3 으로 닫는 검산은 42/46 -- 안 닫힌 4 = 위 2사 · IBK(TAC 1,138.9억을 발행사가 한도 밖에 둠: 76.0 대 107.6) · 스위스리(항목 49 인쇄 0, 4,274억). 100%+ 5사(tier1 DB손보 151.6·하나생명 238.2·아이엠라이프 221.7, tier2 동양 105.0·농협손해 103.9)는 tier2 두 곳이 발행사 항목 3 = 한도 + 49(+54)로 닫히고 tier1 세 곳은 X ≥ 초과분 필요조건을 만족한다. (`b1_summary_dbbffcb5.txt`, `b2_gap_and_regulation_dbbffcb5.txt`)
- **② 규정 대조 13항(`b3_regulation_check_dbbffcb5.txt`)**: MATCH 8 · MATCH_WITH_CAVEAT 3 · INTERPRETATION 2. 어긋나는 점 = 보완자본 분자가 발행사 인쇄 항목 54 를 기발행분으로 쓰는데 규정의 제외 기준은 발행일(시행일 이전)이다(메리츠 0.2→32.2, 흥국생명 10.6→37.0, 농협생명 18.8→21.1 ...; 이미 `TODO.md` ③). 기본자본 두 갈래(기발행 15%/신규 10%) `max` 결합과 TAC 층은 규정에 문장이 없다(해석). 증권 분류 근거 등급(`c5_evidence_grade_dbbffcb5.txt`): PRIMARY 34 · OWNER 6 · SECONDARY 2 · INDIRECT 1 · ISSUER_TABLE_ONLY 5 -- DB손보 제3회는 owner 지시에만 기댄다.
- **증권별 X 검정(`c2_per_security_xtest_dbbffcb5.txt`, 양방향, 19 발행 블록)**: AGREE 11 · AGREE(weak) 2 · DISAGREE 2 · UNDECIDED 4. DISAGREE = DB손보 제3회, 제4·5회(2026.1Q+2Q 합산 X 증가 +8,914.9 대 기본자본형 기대 +5,942.1[잔차 3.2σ]·보완자본형 기대 +8,802.0[잔차 0.1σ]; 제1·2회는 기본자본형으로 맞음 -- `c2b_dbnonlife_reverse_test.txt`). UNDECIDED = 코리안리 제5·6회 · 농협생명 제5회 · 푸본 2023-02(첫 마스터 분기가 발행 분기라 흐름이 없거나 다른 항목이 같은 분기에 들어옴). 하나생명 제1회·교보 2024-11 의 기본자본형 전환은 발행사 처리와 일치. 뒤집기 영향표: `b4_tier1_what_if_dbbffcb5.txt`.
- **③ 전망 손계산(`d1_forward_handcalc_dbbffcb5.txt`)**: 한화생명·DB손보·하나손보·하나생명·교보·메리츠·코리안리 35 시리즈점 차이 0(콜일 상환·SCR 선형 보간·한도 재계산·후순위 잔존만기 체감·단위·연도 경계), 총자본 경로는 분류와 무관하게 불변, 직전 커밋 `ef62969` 대비 230점 차이 0, `baseline_basis_flag` 잔존 0. 한도 기준을 보간 SCR 대신 경과조치 적용 전 SCR 로 둔 변형은 하나생명만 최대 1.22%p 달라진다(모델 선택 사항). 추가로 46사 전체의 비율이 자기 자본/SCR 과 같은지(`d2_forward_internal_consistency_dbbffcb5.txt`): 3사가 다르다 -- 예별(5년 모두 0.0 으로 잘림)·롯데(기본자본비율 0.0)는 `capacity_exhausted` 자름, 마이브라운은 SCR 20.3억 반올림. 기준선 금액은 46/46 마스터와 일치, 기준선 비율은 발행사 인쇄 비율과 최대 0.40%p 차.
- **④ 화면(`e6_screen_results_dbbffcb5.txt`)**: 47사 전부를 페이지의 `<select>` 로 골라 도넛·숫자 줄·전망·발행현황 막대/셀·툴팁 본문을 독립 기대값과 대조 -- 불일치 0, 가로 넘침 0/47, 부제·캡션·? 팝오버·툴팁 문구는 정의 메모 §5 와 글자까지 같음. 공개 시트 3종 47/47/460점 불일치 0(`e7`), 발행현황 타임라인 JSON 대 채권 원장 값 차이 0(`e9`). 툴팁은 Chart.js 툴팁 객체를 `setActiveElements` 로 구동해 본문을 읽고(`e4`) 일부 회사는 실제 마우스 호버로도 확인, 박스 폭은 Chart.js 계산식으로 쟀다(`e5`, 하나생명 실제 호버 329px = 식 329px 로 보정). 페이지는 CSP 때문에 `eval` 불가라 `<script src>` 주입, 창이 안 보이면 Chart.js 가 그리지 않아 공유 이미지가 비는 것을 확인(제품 결함 아님).
- **발견 7건(전부 발주, 직접 수정 없음)**: S-1 전망 노트가 잘린 0.0 을 써서 거짓 개선 인쇄(예별 「+41.8%p」·롯데 기본자본 「+5.4%p」, 실제 −0.24/+4.77, −1.57%p) · S-2 같은 노트의 음수 ASCII 마이너스(△ 규칙 위반) · S-3 375px 도넛 툴팁 폭 초과 6사(329·341·349 대 캔버스 325; 글자까지 잘리는 곳은 푸본·동양·농협손해) · S-4 「경과조치 기발행 후순위」가 인쇄값이라 신규채 포함 · S-5 DB손보 제1·2회 콜일자 엇갈림(발행사 문서끼리도 불일치; 셀의 금액 짝 의심) · S-6 기본자본 인정한도를 33사가 15% 로 인쇄(정의는 10% 원칙) · S-7 하나손해 원장 미갱신(총발행액 1,000억 대 항목 6 1,999억). 발주: publishing `20261012T2235Z`(S-4~S-7 + 분류 결정 4건), designer `20261012T2236Z`(S-1~S-3).
- **한계**: 전망은 7사 손계산 + 46사 내부 정합까지이고 나머지 사의 콜 사다리는 원장을 믿는다(원장 47행 중 22행이 2025-12-31 기준; 한화생명은 반기 잔액표로 일치 확인, 하나손해만 간극). 공유 이미지·실제 호버는 창이 보이는 구간에서만 확인했다. 툴팁 폭은 Pretendard 로드 상태의 값이라 글꼴이 다르면 수 px 달라진다. 규정 쪽은 별표22·해설서 PDF 쪽수로 읽었고(`a1_*`), 발행사 서류 해석이 필요한 4건은 판정하지 않고 owner 결정으로 올렸다.
- **모델**: Sonnet 5.5, 토큰 약 1.4M(전 구간), 소요시간은 오케스트레이터 측정.

## 2026-10-12 (26차) -- 골든 갱신 + AIG R3 박제 등재 (티켓 `20261012T1400Z`)

- **골든 `--update`(이유: parser-kics `acd351a` 하나)**: 직전 마스터(`acd351a^`)로 룰 엔진을 돌리면 `kics_rules_golden` 5키(sha·buckets·findings·by_status·by_rule)가 전부 일치 -> 이동은 그 커밋(퍼시픽 KR1107 2025.3Q·2026.2Q 항목 47~54 +16행, 악사 KR0049 2024.3Q 4칸)뿐. buckets 634·findings 19,020·RED 56 불변, YELLOW 1,935->1,936·GREEN 13,684->13,703·SKIP 3,345->3,325. 입력지문 INPUTS_MOVED x4(17BS·PL·배당·적용후)는 `--verbose` 로 `kics_disclosure.json` 1파일뿐, 4종 모두 +5,195바이트(= 순증 176줄 x CRLF 1바이트 + blob 차 5,019)로 동일.
- **무이동 확인(`--update` 안 함)**: dividend · post_transition · master_tables · viz 2종 · PL(`RUN_PL_GOLDEN=1` 186초) · 17BS(419초) 전부 통과(빌더가 `kics_disclosure.json` 에서 회사 메타만 읽는다는 보고 실증). 빠른 시험: deploy_assets 12 · push_gate_wiring 65 · prepush_scope 65 · golden_input_fingerprint 23 통과.
- **AIG KR0029 2024.4Q R3**: `validate_insurance_liability_portfolio.py` 에 `R3_PINNED_EXEMPTIONS`(값 박제) + 읽는 쪽 `check_r3`(R3 루프를 함수로 추출, 판정식 불변) 신설. 박제 값이 맞으면 `exceptions` 로 인쇄, 값이 움직이면 `R3_PIN_DRIFT` RED, 면제가 불필요해지면 `R3_EXEMPTION_INERT` RED. 변이시험 11건(`tests/test_ilp_r3_pinned_exemption.py`: 대조군·item8/item20 이동·타사/타분기·INERT·음의 간극 분기·읽는 쪽 무력화·라이브 마스터) + 훅 묶음 편입. 게이트 RED 2->1, YELLOW 610 불변. 남은 RED = KR1102 2026.1Q `R2_CENSUS`(owner 결정 대기, 등재 안 함). 이 게이트 자체는 여전히 `NOT_A_PUSH_GATE`.
- **CSM 룰 설계 범위 메모**: `TODO_validation.md` 열린 일에 기록(설계는 하지 않음).
- **2차 갱신(같은 날, parser-kics `33635d1` 뮌헨 KR1101 2026.2Q TFI 50/52 + 51=0 도출, +3행)**: 직전 마스터로 돌리면 1차 갱신 골든과 5키 일치 -> 이동은 그 커밋뿐. `kics_rules_golden` GREEN 13,703->13,705 · SKIP 3,325->3,323(RED 56 불변), 입력지문 4종 각 +978바이트(`kics_disclosure.json` 한 파일). 재실행: dividend · post_transition · master_tables 통과. PL·17BS 무거운 골든은 이 2차에서 재실행하지 않았다(기존 회사·분기에 3행 추가, 빌더는 회사 메타만 읽음 -- 1차 실행에서 무이동 실증).
- **모델**: Sonnet 5.5.

## 2026-10-12 (25차) -- owner 승인 등재: 재보사 인쇄된 0 7칸 · 서울보증 PL 2칸 · 마이브라운 거짓 양성 1칸 (티켓 `20261012T1010Z`)

- **승인 근거**: owner 2026-10-12 채팅 「나머지는 다 승인」(오케스트레이터 제안 그대로), 티켓 본문에 원문 인용. 등재 직전·직후 게이트 출력 비교와 재현 스크립트는 `data/_derived/validation_registrations_20261012/`. 데이터 셀·마스터·xlsx·HTML 은 안 건드렸다.
- **① 재보사 「인쇄된 0」 7칸 -> `data/_gold/user_pl_confirmed_cells.json`** (rule=`PL_YTD_COLLAPSE_TO_ZERO`, 값 0.0): 뮌헨 2023.4Q 투자손익 · RGA 2023.2Q·2025.3Q 영업외손익 · 제네럴 2024.3Q·2025.3Q 영업외손익 · 퍼시픽 2023.3Q·2025.3Q 영업외손익. 원문 PDF 쪽을 다시 열어 열 머리글·행·영업이익/세전 행 마커를 게이트 함수(`_verify_absent_markers`)로 먼저 재현한 뒤 썼다(마커가 안 맞으면 쓰기 중단).
  파서 후보(`proposed_owner_confirmed_cells_ytd_collapse_resweep_20261012.json`)와 달리 상대경로를 쓰고(절대경로 박제 금지), 「항등식이 닫힌다」를 「±1억 반올림 이내」로 고쳐 적었다 -- 영업이익+영업외손익 대 세전이익이 7칸 중 4칸에서 정확히 1억 어긋난다. 제네럴 2024.3Q 는 `(0)`(억원 해상도에서 반올림된 음수 0)이라 마스터 0.0 은 억원 해상도 인쇄값이라고 노트에 적었다. 퍼시픽 2023.3Q 는 좌표(`get_text("words")`)로 열을 확정했다: 라벨 열의 `-` 는 별개이고 해당분기 1 / 전년동기 0 / 증감 -1.
  **읽는 쪽 확인(복원 가정 시뮬레이션)**: 마스터에는 아직 이 7셀이 없다(보류 중). 라이브 PL 마스터 메모리 복사본에 7셀을 0.0 으로 넣고 `check_census` YTD 블록을 그대로 실행 -> RED 0 · `PL_YTD_COLLAPSE_OWNER_CONFIRMED` 7, 대조군(등재부 비움) -> 7칸 정확히 RED(+이전 승인 4칸), 같은 회사 다른 분기 붕괴는 면제 안 됨, 값이 0.0 이 아니면 `PL_YTD_COLLAPSE_CONFIRMED_INERT`. 같은 칸을 잡는 다른 룰은 없다(7칸이 마스터에 있던 시점의 게이트 로그 `reinsurer_resweep_20261012/gate_live_data_contract.txt` 대 기준선: 새 RED 는 `CONCEPT_MIXED_DISCLOSURE_INTO_DART` 102(재보사 17/20/21 계보 -- 이후 `PL_DISCLOSURE_REINSURER_LINEAGE` 로 해소) · `PL_YTD_COLLAPSE_TO_ZERO` 7 · xlsx 행 차이뿐).
  **새로 만든 상태 `PL_YTD_COLLAPSE_CONFIRMED_PENDING`**(YELLOW): 등재는 있고 마스터에 셀이 아직 없을 때. 종전에는 이 경우가 `CONFIRMED_INERT`(「등재를 풀어라」)로 인쇄돼, 방금 승인한 등재를 다음 세션이 풀 뻔했다. 셀이 있는데 붕괴가 사라졌을 때만 INERT.
- **② 서울보증 KR0150 PL 2024.2Q·3Q -> `_PL_SOURCE_ABSENT`** (+ 원장 registry 동명 2기록, 새 사유 종류 `SITE_ROLLED_OFF`). 재보사 전용 매니페스트(`reinsurer_{code}_manifest.json`)가 없는 회사라 `_census_manifest_entry` 에 **fallback** 을 넣었다: 전용 매니페스트 파일이 없으면 다운로더 사이트 판 census(`site_edition_census_result_20261011.json`)의 (회사,분기) 칸 정확히 1개를 근거로 하고 status 가 `NO_RAW` 여야 통과. 재보사는 종전 경로 그대로(하노버 판정 불변, 시험으로 고정).
  재검산 4겹은 하노버와 같은 함수 `_census_source_absent`: 버킷 부재 · raw 폴더 박제 `{}`(2024.2Q·3Q 와 이듬해 2025.2Q·3Q 폴더 모두 KR0150 0개) · census status · 원장 VERIFIED + 인용 재오픈(census 의 해당 칸 + 2025.x 칸 마커). **게이트 효과**: `validate_master_tables` 0번 절 PL real hole 2 -> 0, `pl_src_absent:1ok -> 3ok`, `ABSENT-PL` 2줄(통과가 아니라 「원천이 없다」로 매 실행 인쇄). 한계: 회사 사이트 기준의 원천 부재이며 협회 공시 시스템은 직접 확인하지 않았다(원장 노트에 적음).
- **③ 마이브라운 KR1108 2025.3Q `TIER2_LIMIT_STALE` -> `kics_json_rules.TIER2_STALE_FALSE_POSITIVE`** (+ 원장 registry 동명, 읽는 쪽 `_tier2_cross_bucket_context`). 기존 `_TIER2_ISSUER_INCONSISTENT` 은 셀이 마스터에 이미 있어야 서는 장치(결측이면 INPUT_MISSING RED)라 적재 전 사전 등재가 안 돼서 별도 장치로 만들었다. **박제**: 그 컬럼(값·값_적용후 각각)에 47/48/49 가 적재돼 있고 박제값 0.0 과 정확히 같을 때(53/54 적재 시 역시 0.0)만 stale 지문에서 제외, 아니면 면제 없음. 원문 근거(FY2025_Q3 p16 이 보완자본·한도 적용 전·한도·초과분·신종·후순위를 전부 `-` 로 인쇄 + 지급여력기준금액 619 + 「기발행 신종자본증권 및 후순위채무가 없어」 주석)는 원장 기록의 마커 2개를 게이트가 매 실행 PDF 에서 재확인한다.
  주의해서 고친 근거: 처음 주석에 「직전 분기 값은 비영」이라 적었다가 틀렸다 -- 직전 2025.2Q 의 47/48/49 도 0 이라 값만으로는 재탕과 구분이 안 된다. 구분 근거는 원문이 그 분기 표에 대시를 직접 인쇄한다는 사실뿐이라 그렇게 고쳐 적었다.
  **읽는 쪽 확인**: 5칸(47/48/49/53/54=0)을 (값·값_적용후)에 적재 가정 -> 등재 있음: 새 RED 0 (`47_tier2_census` 전·후 `TIER2_LIMIT_STALE` 이 사라짐), 전수 라이브 대비 새 RED 0 · 변동은 KR1108 2025.3Q 의 SKIP/YELLOW -> GREEN/YELLOW 10쌍뿐. 등재부 비움 -> 정확히 RED 2. 다른 분기·회사 키 -> 면제 안 됨. 박제 어긋남(48=0.3 / 53=0.2 / 47=1.0)·49 결측 -> RED 복귀. 지금(미적재)은 `DORMANT` 로 매 실행 인쇄.
- **④ 뮌헨 KR1101 2026.2Q 50·52 -- 등재하지 않았다(원문에 있다).** FY2026_Q2 p17 (1) 공통적용 경과조치 표(백만원)가 지급여력금액·기본자본 271,642 를 적용 전·후 모두 인쇄하고(2,716.42억) 나머지 행은 공란이다. 티켓 규칙대로 「있으면 등재하지 않고 보고」 -> parser-kics 가 채울 몫. 인메모리 시뮬레이션: 50·52 만 적재 -> `50_tfi_tier_split`(전·후) `TFI_TIER_PARTIAL_ROWS` 새 RED 2, 51=0 을 함께 적재해 50+51=52 가 닫히면 새 RED 0. 51=0 은 p16 헤드라인이 보완자본 0 을 인쇄하나 TFI 표 자신은 그 행이 공란이라 owner 판단.
- **⑤ CSM 워터폴 대 ILP 기준 차이 -- 등재하지 않았다(등재할 게이트 줄이 0).** `CSM_WATERFALL_VS_ILP_CSM_STOCK` 은 22차 「제안만」이었고 코드·시험 어디에도 없다. 룰 없이 등재부만 만들면 읽는 쪽 없는 등재(이 저장소가 반복해서 데인 형태)가 된다. 대신 지금 마스터를 다시 쟀다: 공유 287칸 중 1억 이내 262 · max(1억,0.5%) 이내 281 · 초과 6(예별 2025.4Q 0.0 대 6,227 · 교보 2024.1Q·2Q +3,279/+3,642 · KB라이프 2023.4Q -1,622 · 하나생명 2024.4Q +57 · 롯데 2024.3Q +129), 임계 안 롯데 2023.4Q~2024.2Q +105~+121. 칸별 분류·현재 게이트 줄은 `csm_wf_vs_ilp_basis_diff_cells.md`(예별은 티켓 지시대로 제외). **롯데 2024.3Q 잔차 -23 은 22차에도 설명 안 됨** -- 등재로 덮으면 숨기게 되므로 새 룰 설계(Opus 유형)에서 칸별로 분류해야 한다.
- **게이트 전후(같은 코드 외 이번 변경만)**: K-ICS 게이트 exit 0 · RED 56 불변(finding 0 추가·0 삭제, 차이는 새 인쇄 1줄 `tier2_stale_false_positive_exception` 와 마커 신뢰도 census LABELLED 73 -> 79) / `validate_master_tables --no-build` 변화는 `coverage_hole 2PL->0PL`·`pl_src_absent 1ok->3ok` 두 토큰뿐(HOLE-PL 2줄 소멸, ABSENT-PL 2줄 신설) / `validate_data_contract` 비-xlsx RED 0 -> 0, 새 YELLOW 9(`MASTER_HOLE_SOURCE_ABSENT` 2 + `PL_YTD_COLLAPSE_CONFIRMED_PENDING` 7). **데이터계약 RED 2 -> 4 는 전부 `[master_tables.xlsx]`**(손해율 시트 -> 보험계약부채·CSM상각·17BS 시트로 이동): 동시 세션의 `CSM_amortization.json`·ILP 갱신과 publishing 의 xlsx 동기화 사이 지연이고 내 변경은 마스터·xlsx 를 건드리지 않았다.
- **시험**: 신규 `tests/test_pl_source_absent_site_rolled_off.py`(서울보증 2칸: 범위 박제·원장 일치·raw 유입·census status 변이·셀 결측/중복·census 파일 부재·사유 종류 불일치·원장 부재/종류/status/마커/무마커·INERT·하노버 경로 불변 + 소스 변이 2: fallback 삭제·status 비교 삭제) · 신규 `tests/test_tier2_stale_false_positive_exemption.py` 18건(범위·원장·등록 · 읽는 쪽 · 대조군 · 다른 키 · 박제 어긋남 3 · must_have 결측 · 전수 새 RED 0 · 소스 변이 2: 읽는 분기 삭제·박제 비교 삭제 · 원장 부재/마커 반증/부재마커 반증/등록 누락) · 확장 `test_pl_ytd_collapse_owner_confirmed.py`(범위 4 -> 11칸 + 복원 가정 시뮬레이션 + PENDING) · `test_pl_source_absent_exemption.py`(범위 pin 1 -> 3칸, 하노버 시험은 하노버 칸으로 한정). 두 신규 파일은 `prepush_check.py` 오프라인 묶음에 편입. selftest 102/102. 골든: `--update` 는 `master_tables` 1종뿐(위 두 토큰), kics 룰 골든은 무이동(findings 동일).
- **미결/관측(내 변경 무관)**: `tests/test_rule_coverage_manifest.py` 99건 중 2 FAIL = 알려진 `public_export_clean_state`(보험계약부채 108셀)·`master_xlsx_clean_state`(17BS 6셀) 동기화 대기 -- 나머지 97 통과. `tests/test_data_contract_selftest.py` 는 단독 실행 시 `sys.stdout.reconfigure` AttributeError(기존 순서 의존, 직접 `python scripts/_data_contract_selftest.py` 는 102/102).
- **모델**: Sonnet 5.5.

## 2026-10-12 -- 재보사 PL 경영공시 계보 허용 + 마감 골든 (티켓 `20261012T0600Z`)

- **원인**: parser `3727438` 이 재보사 8곳(KR1101~KR1108)의 PL 투자손익(17)·영업이익(20)·영업외손익(21)을 경영공시 §2-1 요약 포괄손익계산서에서 적재했다. §3d `CONCEPT_MIXED_DISCLOSURE_INTO_DART` 는 DISCLOSURE 계보 PL 셀을 동일개념 5항목(1·16·22·23·24)으로 제한해 **102건 RED**(셀 102 / 값 299). 17·20·21 이 reference_only 인 이유는 같은 회사 시계열에 DART 개념과 경영공시 개념이 섞이기 때문인데, 이 8곳은 DART 사업보고서가 없어 원천이 하나뿐이다(항목 4 주석 허용 `1db7c2d` 와 같은 구조).
- **수정(좁게)**: `validate_data_contract.py` `PL_DISCLOSURE_REINSURER_LINEAGE = {disclosure_summary_pl_reinsurer: {17,20,21}}` + `_pl_dartless_companies`(사이드카 셀이 전부 DISCLOSURE 계보이고 마스터 발행 블록이 전부 사이드카에 정확 키로 있는 회사 -- 코드 목록이 아니라 데이터 조건) + `_pl_reinsurer_exempt_items`(income_statement · 등재 how · DISCLOSURE 경로 · 쪽 · **항목별** 인쇄값 dict). 그 entry 의 items ∩ 등재 항목 **한 칸씩**만 뺀다. 항목 4 때와 달리 셀 `resolution` 은 기본 적재 라벨(`disclosure_summary_pl`)이라 how==resolution 비교는 못 한다 -- 대신 항목별 인쇄값을 요구한다. 매 실행 건수·회사를 notes 에 인쇄한다.
- **시뮬레이션(양방향)**: 데이터계약 RED 102 -> **0**, YELLOW 147 -> 147, 새 RED 0. 게이트가 센 수혜 = 102셀/299값/8곳 = 사이드카 `how` 사용 105 entry 중 17/20/21 포함분과 일치. 라이브 사이드카 전체에서 「DART 계보 없는 회사」 = 정확히 KR1101~KR1108 8곳.
- **변이시험**: `tests/test_pl_reinsurer_disclosure_lineage.py` 14건(허용 삭제·항목 확대·how 검사 제거·항목별 인쇄값 제거·dict 검사 제거·쪽 검사 제거·블록 검사 제거·**회사 조건 제거**·AND->OR·발행블록 검사 제거·entry 밖 항목까지 제외 = 11 변이 + 대조군 + 범위 박제 + 라이브 사이드카 대조/트립와이어). selftest 92 -> 102(Q11~Q11j). `prepush_check.py` 오프라인 묶음에 편입.
- **관측(미수정)**: `verify_provenance_sidecar` 가 (회사,분기) 블록불문 폴백 매칭을 해서, 마스터가 발행하는 블록이 사이드카에 정확 키로 없어도 `MISSING_PROVENANCE` 가 안 난다. 라이브는 발행 1,040블록 전부 정확 키가 있어 지금은 무해(probe `data/_derived/validation_reinsurer_pl_20261012/probe_fallback.txt`). 허용 쪽은 정확 키로 따로 막았다.
- **골든**: `--update` 3종 = `master_tables`(closing 390->393P, pl_bridge 3456->3653P(진짜 1177->1278·구성상 1944->2040)·S 2945->2748, csm_amort_identity 380->383P, qoq_warn 262->267Y; F/NEW 불변) · `ifrs17_bs`(빌더 산출 sha = 현 마스터 sha `ef70b02`, 10,967->11,016행 = BS +49칸) · 입력지문(`ifrs17_bs` 재생성 + `viz_ifrs17_panels` 입력 5.4KB 이동 -- 산출 바이트 불변이라 지문만). 무이동: PL 골든(`RUN_PL_GOLDEN=1`, 해시 전부 일치) · viz 2종(4패널·csm_waterfall 바이트 동일) · kics 룰 · post_transition · dividend.
- **훅**: `prepush_check.py --full` 직접 실행 = gate-clear, exit 0 (오프라인 795 통과 · 1 skip, 부하 큰 PC 에서 34분). push 는 안 함.
- `PL_YTD_COLLAPSE_TO_ZERO` RED 0 (parser 가 인쇄된 0 7칸을 보류 -- 등재 안 함).

## 2026-10-12 -- 게이트 속도: 원문 PDF 텍스트 읽기 캐시 (티켓 `20261012T0300Z`, 판정 불변)

- **원인**: `validate_kics_disclosure.py` 가 등재 예외 근거(인용 PDF 59개, 전체쪽 읽기 16개)를 매 실행 `fitz.open`+`get_text` 로 재검산(`_verify_absent_markers`·`_row_anchor_check`·`_marker_grade_census`·`_cited_page_text_density`). 커버리지 변이시험은 마스터 값만 바꾸고 PDF 는 그대로인데 게이트를 49번 돌려 같은 PDF 를 49번 다시 읽었다.
- **수정**: 신규 `scripts/_pdf_text_cache.py`(프로세스 내 캐시, 키=(절대경로, 크기, mtime_ns), 같은 경로 옛 키 즉시 폐기, 파일 단위 LRU 400MB 상한, 열기 실패는 캐시 안 하고 예외 그대로) + 게이트 5곳이 이 헬퍼로 읽기만 교체. **텍스트만 캐시, 판정(마커 존재·행 귀속·밀도·등급)은 매번 계산.** 마스터·등재부·골든·룰 불변.
- **실측(같은 마스터 스냅샷, 연속 실행)**: 게이트 1회 전 40.7·40.0초 -> 후 첫 회 ~28초(프로파일 하) · 재실행 **3.5초**. `FULL_COVERAGE_SWEEP=1 test_full_gate_coverage_matches_manifest` **1,120초 -> 210초**. 판정 불변: 전/후 stdout(39,535B)·리포트 JSON(7.5MB, generated_at 제외) **바이트 동일 4/4 조합**(RED=56 YELLOW=1935 GREEN=13684 SKIP=3345).
- **변이시험** `tests/unit/test_pdf_text_cache.py` 9건(훅 `tests/unit/` 묶음에 자동 편입): 값=fitz 직접값 · 재호출 무재오픈 · 같은 경로 다른 내용/같은 크기 새 mtime 이면 새로 읽음 · 옛 키 누수 없음 · 메모리 상한 · 실패 비캐시 · `_verify_absent_markers`/`_row_anchor_check` 판정이 파일 교체를 따라감. 키에서 크기/mtime 을 빼는 변이로 5건 FAIL 확인.
- **추가 후보 측정**: `validate_data_contract.py` 는 PDF 가 아니라 `check_master_xlsx`(`check_master_xlsx_drift.read_workbook` openpyxl 읽기, 프로파일 100초/135초)가 지배 -- 반복이 아닌 1회 읽기라 이 캐시로 안 줄어든다(별도 과제). `_scan_breakdown_presence` MD 읽기는 재실행 ~0.3초라 생략.
- **관측(내 변경과 무관)**: `tests/test_rule_coverage_manifest.py` 2건 FAIL(`public_export_clean_state`: CSM 워터폴 +18·ILP +110행, `master_xlsx_clean_state`: 17BS 49행) = parser 재보사 재적재가 마스터에 들어갔고 public_exports/xlsx 동기화 전 -- publishing 대기. `test_data_contract_selftest` 는 `validate_master_tables` 가 첫 임포트면 `redirect_stdout` 하에서 `sys.stdout.reconfigure` AttributeError(훅은 앞선 골든이 먼저 임포트해 가려짐; 단독 실행 시 실패하는 기존 순서 의존).

## 2026-10-11 (24차) -- push 직전 최종 골든 · 훅 사전 실행 (티켓 `20261011T2200Z`)

- **훅 전체 사전 실행**(`prepush_check.py`, FULL, ~28분): 데이터계약 RED 0 · K-ICS exit 0(blocking 0) · 도메인 7종 중 `validate_live_artifacts` 만 exit 2 · DART raw 0 · 지문 RED 0(`--update` 후) · JS clear · inbox 0 · 오프라인 772 통과. **막는 것은 1건**: `INSPL_CENSUS_MISSING` 8(마이브라운·뮌헨·스위스리아시아·스코리·RGA·제네럴·퍼시픽·하노버) -- 6841689 에서는 PL 마스터에 없던 회사 8곳이 첫 적재로 들어왔는데 보험손익 원표 패널(DART 표 기반)에는 구조상 못 들어간다. 데이터 오류 아님. 등재 제안만 작성(`data/_derived/pre_push_final_20261011/pre_push_final_proposed_baseline_inspl_20261011.json`, 미적용 -- owner 결정), 대안은 census 를 DART 제출사로 좁히기.
- **등재 8줄 적용(티켓 `20261011T2300Z`, owner 채팅 「8줄 등재 (권장)」, 커밋된 inbox 티켓에 인용)**: `data/_gold/live_artifact_baseline.json` entries 17->25 (`INSPL_CENSUS_MISSING` 7->15, 상세·first_seen 2026-10-11, 사유=구조상 DART 패널 불가·데이터 오류 아님), 게이트 코드는 좁히지 않음. `validate_live_artifacts` RED 8->0 · YELLOW(baselined) 17->25 · STALE 0. 기존 `_counts.entries`=18 은 이미 DURGAP 1줄이 지워져 실제 17줄보다 1 많았다(이번에 실제 개수 25로 맞춤, `DURGAP_NAV_CROSSCHECK:1` 카운트 줄은 손대지 않음). 제안서의 `뮌헨재보험` 키가 `뮤헨재보험` 으로 오타였고 게이트가 STALE 1 + RED 1 로 즉시 잡아 고침. 테스트 `test_push_gate_wiring` · `test_rule_coverage_manifest` · `test_identity_registry` 178 통과.
- **골든 `--update` 3종**: viz_ifrs17_panels(`csm_amort_schedule` 2c8cfdd9 -> 2ee72b7f, `cf66dce` 의도 이동, 나머지 3패널 불변, 커밋본 = 재빌드) · master_tables SUMMARY(coverage_hole 3->2PL, `pl_src_absent:1ok/0red` 신설, closing 381->390, csm_amort_identity 22S->5S, qoq_warn 252->262Y, exit 2 유지) · builder_input_fingerprints(viz_ifrs17_panels 항목만 이동). 나머지 골든 5종 불변, PL 골든(RUN_PL_GOLDEN=1) 통과·해시 불변, BS 골든은 마스터 sha 가 골든과 같아 생략.
- **`test_disclosure_raw_pdf_wiring` 2건**: 훅 묶음 밖(훅에 안 걸림)이지만 일회성 스크립트 2개의 raw 글롭을 `disclosure_pdfs()` 로 최소 수정, 466 통과. 예외 등재 없음.
- **보고만**: 서울보증 2024.2Q·3Q PL 통째 구멍 2 · 라이나 CSM 2023.1Q·2Q 보류 · 분할표 5사 부분합(YELLOW 4 baselined) · 한화생명 연결 표 선택(+1.85%). 표는 런로그.
- **모델**: Sonnet 5.5.

## 2026-10-11 (23차) -- PL 항목 4 재무제표 주석 계보 허용 + owner 승인 등재 4칸 (티켓 `20261011T2000Z`)

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
- **변이시험**: `_data_contract_selftest` 75→92 (Q9 주석 계보 8 · Q10 원천부재 읽는 쪽 5 · S7~S10 ZERO_LEGS 4), pytest 신규 37건(훅 묶음 `prepush_check.py` 에 편입; selftest 래퍼 `tests/test_data_contract_selftest.py` 포함 -- selftest 는 UH-4 이후 훅이 한 번도 안 돌렸다) -- `tests/test_pl_fs_note_lineage.py`(허용 넓힘·좁힘·근거/resolution/블록 조건 제거 변이 9건 + 범위 pin + 라이브 사이드카),
  `tests/test_pl_source_absent_exemption.py`(원장 부재·K-ICS 원장으로 PL 못 덮음·claim_kind/status/마커/버킷 출현/형식/raw 유입/매니페스트 드리프트/원장 손상 + 읽는 분기 제거 변이 + 등록 제거 변이), `tests/test_pl_ytd_collapse_owner_confirmed.py` 범위 pin 4칸 + 4칸 재확인.
- **골든**: `--update` 안 함. 움직이는 것은 `tests/test_master_tables_golden.py` 1종(SUMMARY: `coverage_hole 3PL→2PL`, `pl_src_absent` 토큰 신설; `zero_legs 9`·`src_na 195zleg` 는 골든값으로 복귀; 같은 골든의 closing/identity/qoq 이동은 라이나 CSM 적재분이라 이 변경과 무관).
  kics 룰 골든·post_transition·지문(pl_breakdown ok)·offline 묶음(613 통과)은 불변. 지문 게이트 RED 3 은 viz_ifrs17_panels(동시 세션의 `csm_amort_schedule.json`·빌더 수정).
- **모델**: Sonnet 5.5.

## 2026-10-11 (22차) -- 최종 라운드: 등재 해제 5묶음 · 골든 정리 · 거짓 녹색 사냥 (티켓 `20261011T1510Z`)

- **게이트 전후**: 데이터계약 RED 22→21 · YELLOW 150→143(해제한 7 finding 만 소멸), K-ICS 게이트 exit 2→0(RED 56 · blocking 0, finding 0 추가·0 삭제·0 변경), 지문 RED 10→0, LIC 검산기 RED 0 불변, live_artifacts RED 8 불변(후보 보고만).
- **증거 기반 해제(신규 등재 0)**: `_CENSUS_SOURCE_ABSENT` KR1102 2023.2Q · 악사 KR0049 2024.3Q 15~23후 부재 박제 · `AFTER_IDENT_ISSUER_INCONSISTENT` KR0073 2026.1Q 938.25 · 재작성 연쇄 KR0073 2026.1Q 19_market · `pl_amort_coverage_baseline` 5줄. 근거 원장은 고아 기록(`resolved_note`)으로 보존. 상세 `docs/kics_gate_exceptions.md` 맨 위 절.
- **골든 `--update`**: kics 룰(634버킷 19,020 finding, RED 57→56 = 19_market 1→0) · post_transition(555→556 cq, 7,123→7,166셀; 옛 마스터+옛 MD 가 옛 sha 를 정확히 재현, 이동 65셀은 새 MD 4개의 6버킷뿐) · master_tables · ifrs17_bs(빌더 재빌드 == 라이브 마스터 바이트 동일 증명 후, 9,030→10,967행) · viz 패널(39→46 · 32→39사, 기존 항목 변경 0) · 입력지문. PL·dividend·viz_csm 골든은 산출 불변.
- **결함 수정(테스트·검증기 코드)**: ① `test_kics_rules_golden` 지문 키 `company_code`/`quarter` 는 엔진이 안 내는 필드라 모든 행이 `[None,None,룰,상태]` 였다(버킷 신원 못 봄) → `원보험사코드`/`공시분기`. ② `test_post_transition_golden` 이 `*.md` 직접 글롭으로 병존 MD 를 이중 집계 → `md_files_latest`. ③ `validate_insurance_liability_lic.py` 손으로 적은 분기 목록 → `quarter_horizon()`(출력 바이트 동일). ④ 해제에 맞춰 테스트 3종(census·absence_pin·manifest 선언) 갱신.
- **거짓 녹색 사냥**: 재보사 PL 은 실질 등식이 없다(진짜 pass 1,177 불변, 증가분 104 전부 구성상) → 원천 대조 287셀 일치, 항목16 인쇄·공란 7칸 parser 발주. 레인별 표본 20×5 중 miss 8 전부 설명됨(파생합·양식·재작성 채택·글리프). 법정준비금 R-RSV-4 10건은 데이터계약이 `run_components` 를 안 불러 미강제. 상세 런로그 Findings.
- **CSM 워터폴 대 ILP 잔액**(코디네이터 추가): 공유 273칸 중 267칸 일치, 차이 난 칸은 전부 기준 차이(재작성 대 원공시, 예별 계약이전) — 추출 오류 0. 런로그 Section 6.

## 2026-10-11 (21차) -- 재보사 단계 10: 금리민감도 RS1·RS5 근거 박제 면제 장치 `rs_pinned_exemptions` 신설 · owner 승인 5건 등재

- **새 장치**(scripts/validate_kics_rate_sensitivity.py): 이 게이트의 등재부(RS1/RS2/RS5_EXCEPTIONS)는 근거를 다시 보지 않는 키 집합이었다. 새 등재부
  `_RS1_ISSUER_INCONSISTENT`(입력 셀 3칸 × 컬럼 + 잔차 비율 − 금액/기준금액×100 박제) · `_RS5_SOURCE_ABSENT`(`SECTION_ABSENT`/`STATED_NOT_APPLICABLE`, raw sha 박제).
  매 실행 형식 · 여전히 발화하는가(아니면 `RS_EXEMPTION_INERT` RED) · 셀·잔차 ±0.01 · raw sha·매니페스트(K-ICS census 장치와 같은 함수) · 근거 원장(VERIFIED·claim_kind·expected_residual·마커 재확인).
  깨지면 원래 RED + 장치 RED 가 gate RED 에 들어간다. 면제분은 `PIN` 줄·산출 JSON 에 매 실행 남는다.
- **집계 게이트 전수 조사**: RS1·RS5 를 세는 곳은 금리민감도 게이트뿐(데이터계약=사이드카, 라이브=듀레이션 갭, K-ICS=미참조) → 장치를 `run()` 안에 둬 main·매니페스트 시험이 같은 답을 받게 했다.
  두 번째 겹으로 K-ICS 게이트 `_exemption_registries()`·`_code_pin_map()` 에 등록 → 원장 누락·잔차 불일치를 K-ICS·데이터계약 게이트가 한 번 더 막는다.
- **등재 5건**(owner 2026-10-10): 제네럴 KR1103 2026.2Q +100bp 적용전·적용후(p16 856/270 = 317.04 대 인쇄 319.78, 잔차 +2.743) · 마이브라운 KR1108 2025.2Q(민감도 절 없음)·2025.4Q(p50)·2026.2Q(p34) 「해당사항 없음」.
  원장 +5 VERIFIED, 대조군 4/4 반증. 문서화 `docs/kics_gate_exceptions.md` 맨 위 절.
- 시뮬: 변경 전후 금리민감도 결과는 5칸 이동뿐 · 원장 없으면 면제 0(RED 9) · K-ICS finding 변화 0 · 데이터계약 finding 134=134(원장 제거 시 RED +4). 변이시험 70건(`tests/test_rate_sens_pinned_exemption.py`, 훅 오프라인 묶음 편입).
  매니페스트(등재부 크기·배선 문자열)·원장 대조 대상·항등식 레지스트리(`_RS_PIN_TOL`) 갱신. 골든 재생성 불필요(통과).
- **하노버 KR1104 적용후 12행 독립 검산 통과**: 비적용사(`_TRANSITION_APPLIERS` 밖) · 같은 문서 「전·후 동일」 명문 · 헤드라인 1·2·14·27·50·52 후 == 전 · 후 블록 0 은 0/0 빈 블록 → 미러 정당, parser 발주 없음.
- **최종**: 금리민감도 RED 5→0 · K-ICS exit 0 · 데이터계약 RED 0 · 라이브 RED 0 · 나머지 훅 게이트 전부 exit 0. 런로그 `reinsurer_runlog_KR1101-1108_12.md`. 모델 Opus 5.5.

## 2026-10-10 (20차) -- 재보사 단계 9: census 원천부재 면제 장치 `_CENSUS_SOURCE_ABSENT` 신설 · 8칸 등재

- **새 장치**(scripts/validate_kics_disclosure.py `_census_source_absent`): coverage census `MISSING_CELLS` 에는 면제 경로가 없어 원천에 채울 것이 없는 재보사
  헤드라인 전용 분기가 영구 RED 였다. 등재 키 (회사, 분기) · 사유 종류 3(`DOCUMENT_PENDING_NOTICE`·`NOT_POSTED`·`COLLECTION_POLICY`) · raw 폴더 sha 박제.
  매 실행 ① 여전히 결측인가(버킷 생기면 `CENSUS_EXEMPTION_INERT` RED) ② raw 파일 집합·sha ③ 다운로더 매니페스트 status·sha·versions ④ 근거 원장 VERIFIED·claim_kind·
  인용 원천 마커 재확인 ⑤ 형식 — 하나라도 깨지면 면제 없이 census RED + 장치 RED(exit). 면제 칸은 두 게이트가 매 실행 목록 인쇄. 데이터계약 게이트 `check_census` 가 같은 함수를 부른다.
- **등재 8칸**(owner 2026-10-10): KR1102 2023.2Q·3Q · KR1104 2023.4Q·2024.1Q · KR1105 2023.2Q(공시 예정) · KR1104 2025.3Q(미게시) · KR1107 2023.1Q·2Q(수집 정책).
  원장 +8 VERIFIED(한계: 회사 사이트 기준, 협회 미확인). census 10→2(남은 2 = 새 문서 수령분, parser 적재 대기).
- **데이터계약 게이트 룰엔진 위임 입력 정합**: `tfi_applicability`·`life_subrisk_source_absent` 를 안 넘겨 원천부재 등재부가 K-ICS 게이트에서만 먹히는 구조였다.
  넘기도록 고침(시뮬 차이 0 — 표시 분기 등재가 그때까지 없어 안 드러났다).
- 시뮬: 기존 39사 finding·report 절 변화 0 · 원장 없으면 면제 0(fail-closed) · 사본 버킷 추가 변이 → INERT RED. 변이시험 69건(`tests/test_census_source_absent_exemption.py`),
  매니페스트 2건·배선 1건 추가.
- **KR1107 P9 신규 RED**: 2023.4Q `8_life_census`·`19_market` 은 FY2024_Q2 p11·p13 「직전 반기(2023.4Q)」 열에 값이 있어(시뮬 8_life Δ0.04 · 19_market Δ0.31) 등재하지 않고
  parser 발주(`20261010T1215Z`) → parser 가 29~46 적재해 닫힘. 2023.3Q `8_life_census` 는 `kics_subrisk_source_absent.json` 에 verdict `DOCUMENT_NOT_COLLECTED`(owner 승인)로 등재,
  룰 SKIP 문구에 사유 분기(`kics_json_rules.py`).
- **예별 PL `PL_YTD_COLLAPSE_TO_ZERO`(owner 결정 ② 유지+셀 등재)**: `user_pl_confirmed_cells.json` 에 `rule`·`verify` 필드를 확장해 2025.3Q 법인세 0.0 등재(신설법인 제1기 6/16~9/30 문구 마커).
  값 박제·마커 재확인 통과 시만 YELLOW. 변이시험 8건. `pl_bridge_baseline.json` FIXED? 2줄 삭제.
- **골든**: kics_rules(633버킷·18,990)·post_transition(555·7,123)·master_tables(KR0004 + ba32077 몫)·PL 빌더(마스터 바이트 불변, 진단 KR0074 1행) `--update`, 입력지문 4항목(17BS·dividend 는 골든 실행 통과로 산출 불변 확인). 기존 39사 슬라이스 sha 불변.
- **최종(kics sha 4f2eb284…)**: K-ICS 게이트 RED 57 · blocking 0 · exit 0 · 데이터계약 RED 3(xlsx). push 훅 BLOCKED — publishing(xlsx·public_exports) + parser 신규 발주 2건
  (금리민감도 재보사 RED 40 단위·적용후 0 · 듀레이션 갭 재보사 46칸). 3·4 는 단계 8 이 도메인 게이트를 안 재서 놓친 것. 런로그 `reinsurer_runlog_KR1101-1108_10.md`. 모델 Opus 5.5, 약 2시간.

## 2026-10-10 (19차) -- 재보사·마이브라운(KR1101~KR1108) K-ICS 스윕 1~8단계 요약 + 단계 8: 룰 2·4·5·6 잔차 박제 장치 신설 · owner 승인 29건 등재

- **스윕 1~8단계(2026-10-08~10)**: downloader 가 7개 지점 + 마이브라운의 경영공시 PDF 를 회사 사이트에서 수집(매니페스트 `data/disclosure/_meta/reinsurer_KR11##_manifest.json`),
  parser-kics 가 적재(1a·1b) → 패치(2) → 공백 보충(3) → validation 기계 검산(4) → owner 결정 1~8 반영 수정(5) → validation 독립 재검증·스코리 적용사 편입·골든 재생성·
  남은 RED 분류(6) → parser 의 R1 미완·되돌림·하노버 2023.3Q 비전 적재(7) → validation 등재·게이트(8). 기존 39사 25,522행은 전 단계 내내 git HEAD 와 `list ==`.
  런로그 `data/disclosure/_meta/reinsurer_runlog_KR1101-1108_{1a,1b,2,3,4,5,6,7,8}.md`. 게이트 RED 80(단계 5 시작) → 71 → 65 → **57**, blocking 44 → 35 → 29 → **0**.
- **새 장치 `_IDENT_ISSUER_INCONSISTENT`**(scripts/validate_kics_disclosure.py): 룰 2 순자산합·4 기본요구자본·5 기준금액·6 분산효과에 잔차 박제 장치가 없던 구멍을 막았다.
  등재 단위 (회사, 분기, 룰, 적용전/후) → 박제 잔차(tol `AFTER_IDENT_PIN_TOL` 0.01) + 입력 셀 박제. 적용전은 룰엔진 diff, 적용후는 거울 축(R2후·R5후·R6후·mmult 축15후)이
  같은 식으로 직접 대조. 셀·잔차가 움직이면 RED 복귀, 축이 닫히면 INERT. K-ICS 게이트와 데이터계약 게이트가 같은 함수(+ 축17후 8_life 공유 필터 `_mmult_after_life8_exempt`)를 부른다.
  시뮬: 기존 회사 finding 변화 0 · 변이 178건(셀 154 · 잔차 24) 전부 RED 복귀 · 게이트 단위 사본 변이로 blocking 0→5 재현.
- **등재 29건**(owner 2026-10-10): 발행사 자기모순 21(신규 장치 17 · `_TIER2_*` KR1105 3 · `_LIFE8_*` KR1103 2025.2Q 1) + 원천 부재 8
  (`MARKET_BREAKDOWN_EXEMPT` 3 · `IRR_SCENARIO_EXEMPT` 1 · `kics_subrisk_source_absent.json` 4). 원장 `kics_exemption_provenance.json` +23건(VERIFIED, 행 귀속 마커).
  퍼시픽 KR1107 2023.3Q·4Q 는 owner 미결정이라 등재 안 함. 등재부 `docs/kics_gate_exceptions.md` 맨 위 절.
- 골든 `--update` 2종(룰 629버킷·18,870 / 적용후 553·7,113, 기존 39사 슬라이스 sha HEAD 일치). pytest 7 실패 중 5 수정:
  stale-table `_KNOWN` KR1107 2026.1Q(오탐, raw p22 근거) · `_TFI_MEMO_TABLE_NOT_SCANNED` 죽은 핀 2(시뮬 변화 0) · xlsx 시트 선언 14→16 ·
  `validate_deployed_js.py` 메서드 축약 파라미터 오탐(IFRS17.html `afterDatasetsDraw(ch){`, 5페이지 시뮬 변화 = 그 1건). 발주 3: publishing(xlsx·public_exports) · parser ifrs17(예별 PL hole·master_tables 골든) · parser kics(금리민감도 provenance 25).
- 포트폴리오 검증기: 스캔 3사 죽은 예외 삭제 · 재보사 R2 census 범위 제외(인쇄) → RED 49→3(KR0100 R3, owner 판단).
- 남은 차단: K-ICS 게이트 exit 2 = census 헤드라인 전용 12칸(면제 장치 없음, owner 결정). 모델 Opus 5.5, 약 75분.

## 2026-10-07 (18차) -- 채널별 유지율(신규 도메인) 검증 VP: verdict RED 1 · YELLOW 8

- 대상 `data/persistency/`(추출 원본·census·selfcheck·errata·triage·vision v1~v4·마스터 변환) + 추출기·변환기·분류기. 산출·스크립트 무수정(mtime 불변).
  보고서 `data/_derived/validation_20261007_persistency.md`. 재현 스크립트는 세션 scratchpad `10fdb815…/scratchpad/vp/`(a1~a16, render/locate/contact/dump).
- 원문 충실도: 표 45개(텍스트 27·vision 18) 렌더 전체 대조 오독·열 밀림·채널 오귀속 0. 항등식 10,312행 독립 재계산(vision 포함) — errata 17칸 17/17 인쇄값,
  보정 9건 9/9 정당, 숨은 break 0(엄격 기준 추가 32칸은 발행사 반올림, ±0.06 안). census 277칸 무사유 결측 0, ABSENT 렌더 5/5, RAW_TRUNCATED 확인. 마스터 1:1·열·채널 §5-1 일치.
- **RED-1(false-green)**: KR0004 예별 2026.2Q p57 머리 "백만원" 인데 금액이 1/1000 규모(61회차 법인기타 대상 82,949·96,633 -> 94.18). 항등식·census·회사합이 전부 통과해
  기존 검사가 못 봄. 잡은 수단 = 회사별 Σ대상신계약액 규모 검사 + 코호트 연속성(D(13,t)≈D(25,t+1y)) — 추출기 selfcheck 에 넣자고 제안.
- YELLOW: KR0150 2Q raw 미수집 무티켓 · 추출기가 vision 항등식 미재계산 · triage KR0071 2023.4Q DEFINITION 근거 미달 · MI 오적재 2칸(KR0051 2024.4Q·KR1000 2024.2Q) 라우팅 누락 ·
  대상신계약액=0 행 760 무플래그 · 금액 열 회사·분기 간 비교 불가(단위 4종 + 원문 기준 x1/12·x1/2·x4 + 원문 채널 재분류) · '건' 64행 금액 규모 · errata 표시 규칙.
- 발주: `inbox/parser/20261007T1001Z__validation__MULTI_2023.2Q-2026.2Q__persistency_validation_findings.md` · `inbox/parser/20261007T1001Z__validation__KR0051_KR1000_2024.4Q-2024.2Q__mi_persistency_shift_addendum.md`
  · `inbox/downloader/20261007T1001Z__validation__KR0150_2023.2Q-2025.2Q__missing_halfyear_disclosure.md`. 모델 Opus 5.5, 약 75분.

## 2026-10-06 (17차) -- `PUBLIC_EXPORT_INTERNAL_JARGON` 신설 (공개 다운로드 내부 진단 문자열 재발방지)

- 티켓 `inbox/validation/20260921T0335Z__publishing__ALL__public_export_jargon_check_proposal.md`(`status: answered`).
  `scripts/validate_live_artifacts.py::check_public_exports` 6번째 축. 마스터·`public_exports/` 무수정.
- 후보 정규식을 사고 직전 스냅샷(`c130062^`, 자본비율전망 2090행)에 먼저 시뮬레이션 — `…_eok\b` 후보는
  `numerator_eok_fallback` 을 놓쳐 660행 중 550행만 검출. `…_eok(?![a-z0-9])` 로 수정, 4패턴 합집합 660/660.
- 현재 14개 시트 4패턴 0건. 스캔은 전 열의 문자열 셀(새 열로의 유출 방지).
- 회귀: 양성 5 · 음성 4(티켓의 false-positive 2건 포함) + 변이시험 `jargon` + 룰 매니페스트 +1. `-k public_export` 10 passed.
- 잔여 보고(룰 범위 밖): 넓은 snake_case 스캔에서 가정민감도 1행 · 기본자본소진율 22행 · 자본성증권발행현황 `비고` 123행·`콜근거` 59행.
- 별건: AIA 2024.4Q 항목46 정정으로 `live_artifact_baseline.json` 의 `DURGAP_NAV_CROSSCHECK|KR0080|2024.4Q|item46` 1줄을 삭제
  (게이트 STALE 1→0). 상세 `docs/changelog_parser_kics.md` 2026-10-06.

## 2026-09-21 (15차) -- 금리민감도 `RS6_PHASE_LEVEL_CENSUS`(RED) 신설 · RS2 적용후 앵커 · 36_irr 티켓 판정(c)

- 발주 2건 처리(둘 다 `status: answered`): parser `inbox/validation/20260921T0100Z__parser__ALL_2026.2Q__ratesens_phase_level_census_gap.md`
  · owner `inbox/validation/20260921T0215Z__owner__KR0094_2025.4Q-2026.2Q__36irr_not_red.md`. 마스터 무수정.
  후속 발주 `inbox/parser/20260921T1400Z__validation__MULTI_2024.4Q-2025.4Q__ratesens_phase_level_holes.md`(lane: kics).
- **36_irr(owner)** — 룰 엔진 전수 census `scripts/_probes/_probe_20260921_36irr_census.py`: 538 버킷 / 538 finding / 미평가 0.
  짝수분기 item36 보유 270 버킷 전부 41-46 완비(GREEN 209 · YELLOW 55 · 박제 SKIP 6). tol 밖인데 RED 아닌 6건 = 전부
  `IRR_DERIVE_ISSUER_INCONSISTENT` 등재분. 신한 2025.4Q 잔차 +863.8221 · 2026.2Q +2,979.8031 = 박제와 Δ 0.0(tol 0.01).
  `report_latest.json` 36_irr×2026.2Q 39건(티켓 "0건" 재현 안 됨). **분류 (c)** — 코드·원장(6 VERIFIED)·`tests/unit/test_irr_pin_exemption.py`
  (6쌍)에는 있었고 **TODO.md §36_irr 표에만 2026.2Q 행이 없었다** → 행 추가(owner 2026-09-01 승인·기대잔차·"선례 금지" 명시) + "5건"→"6건".
  룰·tol·골든 픽스처 무수정("내부모형사" 사유 불사용).
- **RS6 신설(parser 티켓)** — `scripts/validate_kics_rate_sensitivity.py` 를 `run(rs_rows, kd_rows)`(순수) + `main()` 으로 나누고 RS6 추가.
  코호트 (회사,분기) 마다 적용전·적용후 × 3 measure × 충격 5칸 기대 그리드, 종류 `ROW_MISSING·NULL_CELLS·UNKNOWN_LABEL·ORPHAN`.
  전 분기 실측(`scripts/_probes/_probe_20260921_ratesens_phase_census.py`): 결측 **30행/10버킷**(적용후만 9 · 서울보증 2024.4Q 적용전만 1)
  + null 셀 1행 5칸(서울보증 적용후 기준금액, RS1 이 건너뛰던 칸). 파서 열거 7 버킷에 KR0051 2025.4Q · KR0087 2024.4Q · KR0150 2024.4Q 3건 추가.
  **RED**(census 는 YELLOW-first 아님). 선행 31행은 `RS6_KNOWN_HOLES`(routed worklist, 정당부재 아님) — 매 실행 EXC 인쇄, 안 발화하면 inert YELLOW.
- **🔴 RS2 가 적용전만 앵커하고 있었다** — 스펙 §5 는 "적용후는 값_적용후 있을 때만" 인데 구현은 `if gj != "적용전": continue`. 파서의
  2026.2Q 미러 채움을 대조하는 룰이 0개. 적용후 base ↔ `값_적용후` 로 확장(대조불가 `rs2_na` 인쇄, 서울보증 1칸). 결과 기존 예외 미러 4
  (DB손해 2025.2Q 3 · 현대해상 2026.2Q 1 — (회사,분기) 키를 두 phase 에 적용) + **신규 RED 2 흥국생명 2025.2Q·2025.4Q 적용후 기준금액**:
  rs 18,412 / 19,350(총괄표 MD L197·L84 + 민감도표 L589·L503 억원 정수 직접 인쇄) vs `kics_disclosure` item14 `값_적용후` 18415.27 / 19354.44
  (= item1_후/item27_후×100 역산, MD 에 부재). 15/22/23 후도 역산값에 닫혀 있어 파서가 함께 정리하도록 발주. 같은 역산 40 버킷은 관측만 넘김.
  **push 게이트는 지금 이 2칸으로 막힌다**(`validate_kics_rate_sensitivity.py` exit 2 → `prepush_check.py` `n_dom |= returncode` → `blocked`). 면제·우회 안 함.
- **매니페스트** `tests/test_rule_coverage_manifest.py` 금리민감도 절 신설: 룰 id 6종 · 등재부 크기 4종(RS1 1·RS2 2·RS5 17·RS6 11) · known-hole 31행
  전건 발화 · `rs2_na` 침묵 금지 · 변이 7종(phase 통삭제 → RS6 3행 **and RS4/RS5 무발화** · null 셀 → NULL_CELLS and RS1 무발화 · 라벨 오타 · 고아 ·
  적용후 base +10 → RS2 적용후만 · 등재 구멍 채움 → inert) · 훅 배선/exit 전파 정적 확인 → 12 passed. 변이는 메모리 사본만(디스크 무수정).
  `scripts/consolidate_inbox.py` RS2 메시지에 phase 1줄. `tests/test_push_gate_wiring.py` 는 이미 WIRED 라 무수정(56 passed·2 skipped).
- 검증: `validate_kics_disclosure.py` RED=36(전부 documented)·blocking 0·exit 0 · `test_kics_rules_golden`+`test_rule_coverage_manifest`+`test_push_gate_wiring`
  152 passed/2 skipped · `test_irr_pin_exemption` 9 passed. 문서: `kics-rate-sensitivity-spec.md` §5(RS5 소급·RS6·RS2 정정) · `claude-agent-validation.md` RS 표.
- 잔여: 적용후 `36_irr` 축 144 중 19건 미평가(`POST_SCENARIO_ABSENT`) · item14 `값_적용후` 역산 40 버킷 원천 확인(파서) · `RS5_EXCEPTIONS` 17건 inert 검사 없음.
- 모델: Opus 5.

## 2026-09-21 (14차) -- 배포 HTML 의 JS 런타임 축 신설: `DEPLOYED_JS_UNDEFINED_CALL` (훅 §1f)

- 발주: owner `inbox/validation/20260921T0057Z__owner__ALL__deployed_js_runtime_blind_spot.md`(status: answered).
  포스트모템 `docs/postmortems/PM-20260921_kics_sens_iqp_referenceerror.md`(**closed**, 5칸).
- **사고**: designer 커밋 `2dbc4ca`(2026-09-20 05:55)가 `K-ICS.html` 의
  `function IQP(){ return (window.IQTheme && IQTheme.chart().primary) || '#0f6e68'; }`
  **한 줄**만 지우고 호출부 2곳(`renderSensDetail` 의 `borderColor`/`backgroundColor`)을 남겼다.
  라이브에서 `ReferenceError: IQP is not defined` 로 금리민감도 패널이 죽은 채 하루 넘게 배포됐고
  **`prepush_check.py` 전 단계가 초록이었다.** 데이터는 100% 정상 = 고칠 마스터 셀 0개.
  owner 가 눈으로 잡았다.
- **못 잡은 이유는 단순하다 — 검사 축 자체가 없었다.** 저장소에서 배포 HTML 의 `<script>` 내용을
  읽는 검사기가 **0개**였다. `tests/test_deploy_assets.py` 는 keep-list·인라인금지·BOM·삭제경로·
  골든표만 본다. 즉 불변식 1번("게이트가 검사하는 파일 = 사용자가 보는 파일")을 데이터 축에서는
  지켜 왔는데 **화면 축에서는 한 번도 지킨 적이 없었다** — 맞는 파일의 안 본 부분.
- **영향 범위를 재측정해 티켓의 "39사 중 36사" 를 정정했다.** 예외는 `if (postRatio) { … IQP() … }`
  안에서만 터지므로 **적용후 지급여력비율 행이 있는 버킷**만 죽는다. 실측: 선택 가능한 (회사,분기)
  버킷 **138 중 129(93.5%)** 사망, 살아난 9버킷은 적용전만 있어 색상이 리터럴인 경우(동양생명
  2024.4Q · 삼성생명 2024.4Q/2025.2Q/2025.4Q · 신한이지 2025.4Q · 카카오페이손보 2025.4Q ·
  하나손보 2024.4Q/2025.2Q/2025.4Q). **기본 화면(최신 분기)에서는 39/39 사 전부.**
- **신설 `scripts/validate_deployed_js.py`** — 페이지가 실제로 로드하는 스크립트(인라인
  `<script>` + 같은 저장소 `<script src>` 4개)를 렉서로 토큰화해
  `참조 − 바인딩 − 브라우저내장 − CDN전역 ≠ ∅` 이면 RED. 같은 게이트에
  `DEPLOYED_JS_SCRIPT_MISSING`(로컬 `<script src>` 부재) ·
  `DEPLOYED_JS_UNSCANNABLE`(렉서 실패 = **fail-closed**, SKIP 금지)도 있다.
- **헤드리스가 아니라 정적을 골랐다(판단 근거를 박아 둔다).** 헤드리스를 차단축으로 쓰면
  ① 배포본이 CDN 4종을 로드하는데 훅은 오프라인에서도 돌아야 하고(스텁 = "진짜 페이지가 아닌
  것"을 검사) ② 브라우저 없는 클론에서 **SKIP 이 fail-open** 이 된다. 둘 다 이 저장소가 반복해서
  데인 형태다. 정적 축은 0.09초·오프라인·결정론적이고 이번 사고형태를 정확히 덮는다.
  헤드리스로만 잡히는 부류는 **UH-26 으로 등재**했다(안 잡힌다는 사실을 적었다).
- **오탐 억제가 설계의 전부다 — 양쪽을 반대로 틀었다.** `바인딩` 은 과대추정(스코프 미해석,
  구조분해 파라미터 통째), `참조` 는 과소추정(멤버호출·옵셔널체이닝·메서드축약 정의 제외,
  자유 식별자 전수 해석 안 함). 둘 다 "못 잡는 쪽" 으로 틀려 있어 **잡으면 진짜**다.
  노이즈는 렉서가 원천 차단 — CSS `var()`/`rgba()`·한국어 산문은 문자열·주석 안이라 토큰에 안
  들어오고, 템플릿 `${…}` **안쪽만** 재귀 토큰화한다(거기는 진짜 코드다).
- **실측**: 배포 4종 토큰 **73,175** · 참조지점 **3,627** · **RED=0**(오탐 0).
  `function NAME(` 전수 변이 **183건 중 172건(94%) 검출**, 미검출 11건 사유 전건 규명 —
  9건은 같은 이름이 `download-survey.js`/`theme.js` **IIFE 안에도** 정의돼 과대추정에 흡수
  (UH-26), 2건은 진짜 무해(`fillMissingCompanies` 즉시실행 명명함수식 · `plResolve` 호출처 0).
  designer 가 임시 스윕에서 만난 `formatter`·`afterDraw` 오탐은 **안 난다**
  (`name(…){` = 객체 메서드 축약/플러그인 훅 **정의**로 판정).
- **작업 중 내 룰의 버그를 실측으로 잡았다.** `.catch(err => {…})` 를 catch 절로 읽어 콜백 본문의
  이름을 통째로 바인딩으로 삼켰다 → 거짓음성 3건(`render`·`setMapStatus`·`fetchFirst`).
  키워드 규칙에 멤버 위치 가드(`prev ∉ {., ?., #}`)를 넣어 168→172 회복.
  **`gtag`/`dataLayer` 는 CDN allowlist 에서 뺐다** — `gtag.js` 는 `window.gtag` 를 만들지 않고
  인라인 GA 스니펫이 만든다. 넣어 두면 그 스니펫이 지워져도 안 걸린다(빼고도 RED 0 실측).
- **배선(그 자리에서 확인, 문서 아님)**: `scripts/prepush_check.py` **L35** import ·
  **L409** `n_js = deployjs.main([])`(§1f, `_run_korean_master_gates()` 본문) · **L450** 언팩 ·
  **L581** `blocked = … or n_js` · **L600** `return 2 if blocked else 0` ·
  `.githooks/pre-push:23`(`core.hooksPath=.githooks` 확인) ·
  `tests/test_push_gate_wiring.py` `WIRED["validate_deployed_js"]` ·
  오프라인 묶음 `prepush_check.py:547`.
- **범위 목록은 안 고쳤다.** §0 `ROOT_FULL_SUFFIXES` 에 `.html`·`.js` 가 이미 있어 루트 HTML/JS
  번들은 자동 FULL → "화면을 고쳤는데 화면 게이트를 건너뛰는" 조합이 구조적으로 안 나온다.
  `tests/test_prepush_scope.py` 는 무수정 통과(단 `_run_korean_master_gates` 가짜 반환값에 `js`
  키를 더했다 — 안 더하면 `main()` 이 KeyError).
- **엔드투엔드 exit code 를 실행으로 봤다**: `origin/main` 의 깨진 `K-ICS.html` 을 스크래치패드
  트리에 놓고 같은 호출 경로로 `prepush_check.main()` →
  `PRE-PUSH VERDICT … 배포 JS 런타임=BLOCK … → BLOCKED`, **exit 2**. designer 복구본이면
  `배포 JS 런타임=clear … gate-clear`, **exit 0**.
- **회귀 박제** `tests/test_deployed_js_gate.py` **24케이스 8.6초** — ① 배포 4종 오탐 0(상주판)
  ② `IQP` 정의를 **메모리에서** 지우면 RED(호출부 2줄)·원본이면 GREEN ③ 같은 사고형태를 4종
  전부에서 잡는지 전수 변이(검출률 하한 70% 강제, 고정 심볼 목록을 박지 않아 개명에 안 죽는다)
  ④ **killer 변이 6종**(allowlist 확대 / 호출을 정의로 계상 / 참조 수집 제거 / 인라인 스크립트
  미독해 / 렉서 실패 묵인 / 없는 `<script src>` 묵인) 전부 케이스를 죽이는지 ⑤ 노이즈 내성.
  **`K-ICS.html` 은 디스크에서 한 번도 수정하지 않았다**(designer 소관 — 변이는 전부 문자열에만).
- **비용**: 인-프로세스 **0.09초**(훅이 부르는 방식) · 단독 실행 2.9초(파이썬 기동 2.2초 포함) ·
  라이브 감사 축 포함 시 +2.3초(git show 8회, ref 별 메모이즈 후). 오프라인 묶음 +8.6초.
- **미배선 잔여(조용히 남기지 않는다)**: **UH-26** 런타임 전용 실패(TypeError · `getElementById()`
  null · 차트 옵션 스키마 · fetch 모양 변화 · **스코프 오류**) →
  `inbox/validation/20260921T0630Z__validation__ALL__headless_runtime_smoke_feasibility.md`.
  **UH-27** 라이브(`origin/main`) 축은 `_live_audit()` 이 **인쇄만 하고 안 막는다**(차단하면
  designer 가 main 을 고칠 때까지 무관한 작업까지 막힌다) — 지금 라이브 RED=2, 배포 발주
  `inbox/publishing/20260921T0630Z__validation__ALL__live_main_still_broken_deploy_iqp_fix.md`.
- 마스터 JSON·배포 HTML·`data/_gold/` **무수정**. 골든 6종 중 영향 있는 것 없음(산출 불변).
- 모델·소요: Claude Opus 5(1M), 단일 세션.

## 2026-09-20 (13차) -- 경영공시 PL 백필 ⑤ 병합 후속: `_check_pl_bridge`(leg-coverage 2e · ZERO_LEGS 2b) 소스인식

- 발주: parser/ifrs17 `inbox/validation/20260920T1730Z__parser__MULTI_2023.1Q-2026.2Q__pl_bridge_legcoverage_not_source_aware.md`(status: answered). 12차가 `coverage_holes` 만 소스인식으로 바꾸고 `_check_pl_bridge` 의 두 축을 빠뜨려, ⑤ 병합 직후 `pl_new=153` 으로 `tests/test_master_tables_golden.py` 가 push 를 막고 있었다.
- **원인은 데이터가 아니라 룰이다.** 경영공시 §2-1 요약 포괄손익계산서는 LOB 다리(생명장기/자동차/일반)도 생명장기 10개 sub-leg 도 싣지 않는다. leg-coverage 는 결측 다리를 **0 으로 채워** 검산하므로 그 셀에서는 우변이 통째 0 이 되어 잔차 = item1 전액. 신규 실패 153/153 이 `|잔차| == |item1|` 이었다 = 실패가 아니라 **검산 불가(NOT_TESTABLE)**.
- **같은 resolver 재사용**(`validate_master_tables.py` L1044). `coverage_holes` 가 `pl_key_items_for()` 로 쓰는 `pl_cell_source_ids()` 를 그대로 `_check_pl_bridge(source_ids=)` 에 물렸다 — 두 번째 계보 판정기를 만들지 않았다(12차에 census 가 두 곳에 따로 구현돼 118 vs 6 으로 갈릴 뻔한 것과 같은 형태의 재발 방지).
- 배선: `_check_pl_bridge()` 에 `source_ids`·`src_na_out` 키워드 추가(**반환 arity 5 유지** — `tests/test_rule_coverage_manifest.py:745` 보호) · 2e L1091-1105 · 2b L1225-1227 · `src_na_out` L1317 · `main()` L1833 · SUMMARY L1868.
- **가드를 "계보가 DISCLOSURE 면 SKIP" 으로 넓히지 않았다.** 그러면 거짓 면제가 된다. leg-coverage 는 `LOB 3다리 전부 결측 + 추가 LOB(2-N) 없음`, ZERO_LEGS 는 `sub-leg 10개 전부 결측` 일 때만 SKIP. 한 칸이라도 값이 있으면 계보와 무관하게 검산한다(라이브 숫자 동일, 미래 회귀만 막는다).
- **SKIP 을 조용히 하지 않는다**: SUMMARY 신설 필드 `src_na(DISCLOSURE):155legcov/112zleg` + 본문 `LEGNA` 155줄 · `ZLEGNA` 112줄 건별 인쇄.
- **거짓 PASS 2건 동반 해소**: 처브라이프 2023.1Q·2024.1Q 는 다리가 하나도 없는데 `bare+기타영업수익-기타사업비용` 후보가 우연히 허용오차에 들어 PASS 였다 → SKIP(`진짜(REAL)` pass 1173 -> 1171).
- **전 버킷 시뮬레이션은 같은 함수를 토글해 쟀다**(`source_ids={}` = 수정 전). leg-coverage FAIL 172(DISCLOSURE 153/DART 19) -> **19(DART 19)** · ZERO_LEGS 97(88/9) -> **9(DART 9)**. strict 토글이 수정 전과 집계·`fail_ids`·`zleg_ids` 집합까지 전건 동일(회귀 0) · **새로 생긴 FAIL 0**(단방향).
- **골든은 `병합 전` 기준이었다 -> 2x2 로 귀속을 갈랐다.** `e83b619^` 에서 마스터·사이드카·등재부를 꺼내 `{병합전,병합후} x {strict,aware}` 로 `main()` 실행. **골든 == 병합전+수정후(전 필드 일치) = 내 룰은 병합 전 마스터에서 no-op.** 병합이 움직인 축 = `pl_bridge`·`tax22_src`·`zero_legs`·`lob_na`(parser 티켓 §1 표와 숫자 일치) / 내 수정이 움직인 축 = `pl_bridge`·`zero_legs`·신설 `src_na` **3개뿐**. `zero_legs` 는 9 -> 97 -> **9** 로 골든 값 복귀.
- **153건을 등재부에 넣지 않았다** — `data/_gold/pl_bridge_baseline.json` 31건 불변(31/31 DART). 등재부의 의미는 "기지 **실패**" 인데 이건 검산 불가이고, 등재하면 그 15사가 나중에 진짜 LOB 를 얻어도 축이 영원히 침묵한다. `등재부에만 남은 것` 도 0 건이라 지울 줄이 없었다.
- **ZERO_LEGS DART 9건은 살렸다**: 아이엠라이프 2024/2025.4Q · AIA 2024.4Q · 예별 2024/2025.4Q · 카카오페이 2024/2025.4Q · 하나손보 2024/2025.4Q. **9/9 가 4Q(DART 사업보고서)** 이고 12차에 "DART 4Q 에 생명장기손익 실재" 로 실측한 12사 안에 있어 **추출 갭 가능성**이 높다 — 원문 확정은 parser 레인.
- **selftest 69 -> 75**(`_data_contract_selftest.py` `_mt()` L933 · `MT_CASES` L948 · `run_master_tables_cases()` L971). 이 축은 `run_gate` 안에 없어 `Env(inject=)` 로 못 찌른다 -> `_check_pl_bridge` 를 직접 부르는 가족을 신설(run_gate 에 얹으면 "그 룰이 거기 있다" 는 거짓말이 된다). S1 DART 생존 / S2 SKIP 이고 세어진다 / S3 다리 일부결측이면 검산 / S4 계보 미상 엄격 / S5 sub-leg 값 있으면 ZERO_LEGS 문다 / S6 추가 LOB 있으면 검산.
- **killer 변이 7종으로 반증**(게이트 파일 변조 후 복원, md5 `365d8f25cbacc8f4f2a298e039b3b18f` 전후 동일): M-A/M-B(2e 가드) · M-C/M-D(2b 가드) · M-E(fail-closed) · M-F/M-G(축 통째 소멸). **6/6 케이스가 최소 1변이로 사망(동어반복 0) · 7/7 변이가 최소 1건 사망(안 보이는 변이 0).** S3 는 처음에 fixture 가 틀려서 FAIL 했다(3다리를 다 채우면 라벨이 `보험손익(dual)` 로 가 leg-coverage 축을 안 찌른다) — 룰이 아니라 케이스를 고쳤다.
- **미배선 잔여**: ① `tests/test_rule_coverage_manifest.py:749` 의 `coverage_holes` 는 아직 resolver 없이 부른다(매니페스트 `holes` 축만 게이트보다 엄격). 오늘은 무해 — 그 변이는 값만 흔들고 결측을 안 만들어 `holes` 가 baseline·mutated 양쪽 동일. 결측을 만드는 변이가 생기면 커버리지 과대선언이 된다. ② `zleg_exc` 는 세기만 하고 인쇄 안 된다(이전부터).
- 마스터 무수정: `PL_breakdown.json`·`PL_breakdown_provenance.json`·`kics_disclosure.json`·`insurequant_master_tables.xlsx` 전부 `git status` 깨끗. 바꾼 파일은 게이트 3개(`validate_master_tables.py`·`_data_contract_selftest.py`·`tests/fixtures/master_tables_golden.json`).
- 검증: `validate_master_tables --no-build` `pl_bridge:3309P/31F/1950S/**0NEW** · zero_legs:9 · src_na(DISCLOSURE):155legcov/112zleg` · `validate_data_contract` **RED=0 YELLOW=123 exit 0**(불변) · `--selftest` **75/75** · `test_master_tables_golden` `--update` 후 1 passed · `test_rule_coverage_manifest`+`test_identity_registry`+`test_push_gate_wiring`+`test_identity_tautology` **162 passed / 2 skipped**(매니페스트 수정 불요).

## 2026-09-20 (12차) -- 경영공시 PL 백필 병합 선행조건 ②③④ 배선 (계보 등재 · PL provenance 첫 검증 · 기대그리드 소스화 · 개념 등재부 리더)

- 발주: 오케스트레이터. 판정 원본 `inbox/_resolved/20260918T0205Z__orchestrator__ALL__disclosure_sourced_pl_contract.md` 결정 1/3/4. ① 사이드카 발행은 parser 가 먼저 끝냈다(커밋 `fa08bfe`, 638->748셀). **⑤ 병합은 하지 않았다** -- parser 소관이라 조건부 승인으로 회신(`inbox/parser/20260920T1500Z__validation__ALL_2023.1Q-2026.2Q__disclosure_pl_merge_authorized.md`). 마스터(`PL_breakdown.json`·`kics_disclosure.json`·마스터 xlsx) 미수정.
- **② 계보 등재 4건**(`validate_data_contract._SOURCE_LINEAGE`): `data/disclosure/`->DISCLOSURE · `md_inbox/`->DISCLOSURE_MD · `data/_gold/`->OWNER_GOLD · `scripts/build_pl_breakdown.py`->OWNER_GOLD. 동시에 `SOURCE_ID_LINEAGE_MISMATCH` 를 `_CAPITAL_SECURITIES_MASTERS` guard **밖으로**(전 마스터 공통), `effective_filtered` 만 capsec 전용 잔류.
- **등재와 guard 해제는 같이 해야 한다(실측).** 등재 없이 guard 만 풀면 `kics_rate_sensitivity` **138셀이 한꺼번에 RED**(`md_inbox/…` <-> `DISCLOSURE_MD` 인데 계보 미등록 -> 판정 None). 등재만 하고 guard 를 안 풀면 PL 은 여전히 무검증. 부수: 코드 주석이 "계보 일치를 검사한다" 고 적어 놓고 실제로는 안 하던 상태가 해소(138/138 MATCH).
- **`DERIVED` 는 계보에 등재하지 않았다.** 계보 판정기는 `source_file` **경로**에서 라벨을 유도하는데 빌더 파생값엔 경로가 없다(`null`) -- 널에 라벨을 주려면 빈 접두를 등재해야 하고, 그러면 `source_id_for_lineage(None)` 이 라벨을 돌려주어 **전 마스터의 모든 null source_file 이 계보 검사를 통과**한다(보편적 탈출구). 대신 `verify_provenance_sidecar(builder_derived_keys=)` 로 **게이트가 마스터에서 재계산한 셀**(생보·contract_notes·published⊆{13,14}·값 정확히 0.0)에만 좁은 면제. 사이드카 자기 라벨은 근거가 아니다(PM-2026-08-03). 양방향 -- 라벨 도용도, 파생값에 필링 경로 다는 것도 RED. 라이브 면제 1셀(KR0080 2023.4Q).
- **PL provenance 는 호출처가 0 이었다.** 사이드카는 2026-06-20 부터 있었는데 `verify_provenance_sidecar()` 호출처 4곳에 PL 이 없었고, `_fallback_note`(부재 RED)조차 그 4개 분기 **안에서만** 도달 가능해 "사이드카가 없다" 는 RED 도 안 났다. 배선 후 published **731셀** 검증(마스터에서 독립 재계산 -- 사이드카가 검사 대상을 고르면 빠뜨린 셀이 영원히 무검사), RED 0. `target_q=None`(이력형 마스터).
- **③ `coverage_holes` 기대그리드를 셀 계보별로**(`validate_master_tables.PL_DISCLOSURE_*` · `pl_cell_source_ids()` · `pl_key_items_for()` · `coverage_holes(key_items_for=)`). DISCLOSURE -> §2-1 5항목, 그 외·**계보 미상 -> 종전 전량(fail-closed)**. 사이드카 부재·파손·중복계보는 전부 엄격 쪽. 실측: `LIVE 종전규격 real=3` == `LIVE 소스인식 real=3`(바이트 동일 -> 골든 `--update` 불요) / `MERGED 종전규격 118` -> `MERGED 소스인식 6`.
- **`LOB_LEG_NA` 등재 금지 근거를 회사별로 실측**: 백필 15사 중 12사는 DART 4Q 에 생명장기손익이 실재. 예외는 AIG(3개 4Q·3개 LOB 전부 결측, 원문 확인 전 등재 금지) · 신한이지(2025.4Q 에 실재하므로 2024.4Q 는 확정 결손). 병합하면 진짜 RED 3건이 드러난다 -- parser 발주.
- **④ `CONCEPT_REGISTRY["pl_disclosure_vs_dart"]` 등재 + 리더**(`check_cross_source` §3d). 경영공시 `투자손익=투자수익-투자비용`(감독회계) vs 마스터 `#17=#18+#19`(336/336). 등재만 하면 다음 라운드에 또 샌다 -> DISCLOSURE 계보 셀 항목을 **allowlist `{1,16,22,23,24}`** 로 강제, 위반 시 `CONCEPT_MIXED_DISCLOSURE_INTO_DART` RED. 금지 3항목 열거가 아니라 허용 5항목(fail-closed). 라벨과 경로를 둘 다 본다.
- **🔴 배선 도중 같은 census 의 두 번째 구현 발견**: `check_census` §1c 가 PL 에 `coverage_holes` 를 **resolver 없이** 부르고 있었다. ③ 을 `validate_master_tables` 에만 넣고 끝냈으면 병합 후 이쪽만 `MASTER_HOLE` 118 RED, 저쪽은 6 이 된다. 같은 resolver 를 `Env.pl_source_ids` 로 한 번만 만들어 양쪽에 물렸고 병합 전/후 두 게이트 숫자 일치를 실측(LIVE 3=3 · MERGED 6=6).
- **selftest 57 -> 69**: Q1~Q8b(PL provenance + guard 탈출 + census 1c 소스인식, 오탐금지 Q5b·Q8b 포함) · **R1~R2(`BS_KICS_HARD_ZERO`·`BS_KICS_BASELINE_BREAK`) = 직전 11차가 "미배선 잔여" 로 박제한 잔여분 해소.** 12건 전부 killer 변이로 반증(M1b·M2b·M3·M3b·M4·M5·M6·M7·M8·M9·M10). 1차 변이 M1·M2 는 "옛 동작 복원" 이 아니라 다른 버그 주입이라 무의미했다 -- 변이는 되돌리려는 동작과 정확히 같아야 한다.
- 검증: `validate_data_contract` **RED=0 YELLOW=123 exit 0**(불변) · `--selftest` **69/69** · `validate_master_tables --no-build` SUMMARY 불변 · `test_master_tables_golden` 1 passed · `test_push_gate_wiring`+`test_identity_tautology` 65 passed 2 skipped · `test_rule_coverage_manifest` 83 passed(불변) · `prepush_check.py` FULL 범위 **gate-clear**.
- 재현: `$py scripts/_probes/_probe_20260920_pl_merge_precondition.py` (읽기전용, 임시 사이드카는 끝나면 지운다).
- 미배선 잔여: PL 사이드카 `as_of_date` 748/748 null(`STALE_AS_OF` 침묵, downloader 발주) · `kics_disclosure`(1,123셀)·`CSM_waterfall`(327셀) 사이드카는 존재하나 `source_file` 전건 null + 호출처 0(PL 과 같은 상태) · `IFRS17_BS`·`dividend` 는 사이드카 파일 자체 없음 -> provenance 축은 등록 마스터 10종 중 **6종**만 본다(5->6) · `pl_disclosure_vs_dart` 의 `comparable` tol 은 리더 없음(겹치는 칸 0).

## 2026-09-13 (6차) -- jp `JP_ESR_ADJUSTED_FIGURE` 배선 (UH-21 해소, PM-2026-09-13 `closed`)

- 사고 유형: **"없는 숫자" 가 아니라 "있는 숫자 중 틀린 것".** 5차의 `JP_ESR_NOT_IN_SOURCE` 는 "그 문서에 그 숫자가 있나" 만 물어서 かんぽ 220% 를 원리상 못 잡는다 -- 220 은 그 자료 p35 에 **실재**한다(「大量解約リスクを除いた場合のESRは220%」 + p18 「ESR適正水準 150~220%」, 실측 d=1 -> `found`). 한정 조건이 붙은 조정치를 헤드라인으로 고른 것이고, 같은 문서에 한정어 없는 진짜 헤드라인 181% 가 나란히 있었다.
- 판정식: ① 화면값이 나오는 ESR 라벨동반 **산문 조각**(`。`/개행 분할)이 1개 이상(0개면 **기권**) ② 그 조각이 **전부** 한정어를 달았다 ③ **같은 문서에 한정어 없는 다른 ESR 값이 있다** -> `adjusted_alt`(본 룰). ②까지면 `adjusted_only`(보조).
- **③ 을 본 룰로 고른 근거(실측, 한정어 목록 4변형 x 15사)**: 확정본 -> ①② 단독 1 · ①②③ 1(정상사 오탐 0) / `適正水準` 제거 -> **사고를 놓친다**(p18 조각이 한정어 없는 조각이 되어 220 이 빠져나간다) / definition marker 4종(`ベース`·`内部管理`·`規制`·`速報値`) 오염판 -> **①② 단독은 정상 3사 거짓 발화**(日本生命·住友·朝日), ③ 을 붙이면 전부 조용 / 빈 목록 -> 0. 정상 상태에선 둘이 같은 답이지만 **룰이 망가지는 현실적 경로에서 ③ 만 버틴다**. 근거가 가설이 아닌 이유: `適正水準` 은 かんぽ **정답값 181 의 조각에도** 붙어 있고(「適正水準の範囲内にある」), 朝日의 정답 헤드라인은 「ESR(グループ)(内部管理ベース)は258.9%」다.
- 한정어 목록은 **15사 실측으로 확정**(seed 를 그대로 쓰지 않았다): 라벨동반 조각 전체에서 관측된 것은 `除いた場合`(2) · `適正水準`(4) · `ターゲットレンジ`(1)뿐. `を除く`·`レンジ`·`目安`·`調整後`·`参考` 는 **관측 0**, definition marker 4종은 **일부러 제외**.
- 오탐억제: 정상 14사 중 **7사가 라벨동반 산문 조각 0개**(표·차트 전용 문서) -- 기권 조건 없이 걸면 거짓 YELLOW 7건. 기권은 SKIP 이 아니라 **따로 세는 분류**(`unqualified=7 adjusted_alt=0 adjusted_only=0 abstain_no_prose=7 not_applicable=1` 을 수집기·게이트가 인쇄).
- 배선: `check_esr_in_source.py::scan_adjusted`(판정식 정본, 네트워크) -> 기존 `esr_in_source_health.json` rows 에 필드 6개(**새 증거 파일 없음** = 신선도 검사 재사용) -> `build_jesr_page_json.py::_adjusted_figure_check`(오프라인). 면제는 `jp_source_exceptions.json` 셀 단위(등재 0건, owner 권한).
- **severity YELLOW, 이빨은 push 묶음.** RED 로 걸면 조건부 값을 정당하게 헤드라인으로 쓰는 회사의 정상 배포를 오탐 1건이 막는다(UH-5·UH-9 선례). 대신 "인쇄만 하는 YELLOW 는 통제가 아니다" -- 2026-09-12 에는 census notes 에 조정치임이 **적혀 있었는데도** 그 값이 나갔다. `test_live_esr_evidence_has_no_unexempted_adjusted_figure` 가 **배포본 증거**(게이트가 읽는 그 파일 = 불변식 1)에 면제 없는 발화가 남으면 FAIL 한다.
- **소멸 경로 차단**: YELLOW 는 exit code 를 안 바꾸므로 축이 죽는 유일한 길은 "옛 수집기로 돌려 필드가 빠지는 것" -> **필드 부재는 RED**(`JP_SOURCE_EVIDENCE_INCOMPLETE`, 면제 불가) · 모르는 verdict 도 RED. 진짜 빌더로 exit 1 실증.
- **사고 재현(엔드투엔드, 사본에서만)**: census 를 かんぽ 220 으로 되돌리고 수집기를 원문 바이트로 재실행 -> `found(p35,d=1)`(NOT_IN_SOURCE 조용) + `adjusted_alt`/대안 `181` -> 빌더 exit 0 + 대안값을 찍는 메시지 -> **push 묶음 exit 1**. 현재값 181 은 `unqualified` = 발화 안 함.
- 회귀 **83**(63에서) + 26, 새 파일 없음(`REDUCED (jp-scope)` 유지). 이빨 변이 **10/10 발화**(사본에서만, 원본 md5 복원 확인).
- PM 종결: 5칸이 다 차 `PM-2026-09-13` -> **`closed`**, README 색인·UH 표 갱신. 잔여 **UH-22**(severity 승격 판단, 10/31 라운드 재측정 + 승격 3조건 명문화 / P2) · **UH-23**(한정어 목록 정본이 코드에만 있다 / P3).
- 검증: 빌더 exit 0 · RED 0 · YELLOW 1(T&D) · 산출 `generated_at` 외 전량 동일 · `prepush_check.py` = `REDUCED (jp-scope)` · **238 passed · 4 skipped** · `gate-clear`.

## 2026-09-13 (5차) -- jp `JP_ESR_NOT_IN_SOURCE` 배선 (PM-2026-09-13 의 마지막 미배선 축, UH-18 해소)

- 사고 유형: **자기참조 게이트.** jp self-check 는 census 안에서만 닫히는 범위·형식·합계 검사라 "그 문서에 그 숫자가 있나" 축이 없었다. 東京海上HD 238%(2차보도 인용값)와 MS&AD 의 무관한 출처(ESR 한 줄 없는 합병 보도자료)가 그 구멍으로 통과했다.
- 신설: `J-ESR/check_esr_in_source.py`(수집기, 네트워크) → `J-ESR/esr_in_source_health.json`(증거) → `build_jesr_page_json.py::_esr_in_source_check`(게이트, 오프라인). 봉투는 `source_url_health.json` 과 동일해서 신선도 검사를 `_load_evidence_envelope` 한 벌이 두 파일에 공유한다 -- **증거가 낡으면 두 룰이 같이 낡는다(한 쌍)**.
- **증거 키는 (url, esr_pct).** url 만으로 잡으면 값만 고치고 수집기를 안 돌린 상태가 옛 값의 `found` 를 물려받는다(= 2026-09-12 사고의 모양). 실측 재현 A: 東京海上HD 268→238 · かんぽ 181→220 으로 되돌리면 `JP_SOURCE_EVIDENCE_INCOMPLETE` 2건 · exit 1.
- **사고 재현 B(수집기까지 재실행 = 사고 당시 상태)**: 東京海上HD 238 → `JP_ESR_NOT_IN_SOURCE` RED · exit 1. 238 은 決算プレゼン 56페이지 **어디에도 없다**(근접 문턱을 100,000자로 풀어도 not_found) -- 200자 문턱은 사고 탐지가 아니라 **거짓 RED 억제**가 전부인 파라미터다.
- **재현 C**: MS&AD 를 사고 당시 URL(2026-02-13 합병 보도자료)로 되돌리면 `not_found` → RED. 그 URL 은 지금 probe 해도 `ok_requires_headers`(살아 있음)라 **먼저 배선한 4종으로는 못 잡는다** -- 이 축만 잡는다.
- **못 잡는 것을 기록에 남겼다**: **かんぽ 220 은 안 걸린다**(p35 「大量解約リスクを除いた場合のESRは220%」 로 실재 → `found`). PM 이 주장하던 "이 축이 東京海上HD·かんぽ 2건을 잡는다" 는 **틀렸고**, 실제로 잡는 2건은 東京海上HD·MS&AD 다. PM 은 `open` 유지하되 사유를 3번 칸(배선)에서 **2번 칸(룰 정의)**으로 옮겼다 -- **UH-21 신규 / P1**.
- **UH-21 오탐억제 실측 선행**(배선은 안 함, UH-5·UH-9 선례): 한정어(`を除いた場合`·`調整後`·`適正水準`·`ターゲットレンジ`) 없는 라벨동반 등장이 0개면 조정치 후보 → かんぽ 220 발화 / 181 미발화. **단 정상 14사 중 7사는 라벨동반 산문 조각이 0개**(표·차트 전용 문서)라 "라벨동반 조각 >= 1 일 때만 판정" 조건이 필수 -- 붙이면 표본 발화 1건·오탐 0.
- 오탐억제(실측): posted 15사 전수 `found=14 · not_found=0 · skip_landing=1(T&D) · skip_no_text=0` -- PM §4c-pre-실측 과 **정확히 일치**. 초안의 "같은 문장" 규격을 되돌려 재보면 `found=7/14` = **거짓 RED 7건**(예고치와 같다). 확정 규격(±200자 / 같은 표 행)은 14/14·거짓 RED 0.
- RED 로 읽는 verdict 는 `not_found` 하나. `skip_landing`·`skip_no_text` 는 YELLOW 인쇄만. `skip_no_text` 문턱은 **공백 제외 0자** -- 올리면 SKIP-on-missing 이다. 문서를 못 받으면 판정이 아니라 `fetch_failed` 로 적고 게이트가 절차 룰(면제 불가)로 잡는다.
- 라벨 정본은 `docs/domains/claude-agent-jp.md §3`, 코드는 기계본이고 테스트가 한 줄씩 대조(`test_esr_labels_are_all_named_in_the_domain_doc`). 구기준 단독 `ソルベンシー・マージン比率` 는 ESR 이 아니라 같은 페이지에 신기준 표지(`所要資本`·`適格資本`·`UFR`)가 있을 때만 라벨 -- 없으면 au損保·明治安田損保 5개년 구기준 표가 라벨로 읽혀 **거짓 통과**.
- **fixture 가 게이트를 덮고 있던 것도 같이 고쳤다**: `tests/test_jp_deploy_matches_census.py` 의 10/31 flip 시뮬레이션이 census 만 뒤집고 선행 단계를 안 돌린 라운드를 흉내 내고 있어 새 룰에 전부 걸렸다 -- **거짓 RED 가 아니라 게이트가 제 일을 한 것**. 게이트를 안 풀고 fixture 를 완성(`_synthetic_esr_evidence`) + 음성대조군(`test_flipped_census_without_fresh_esr_evidence_is_red`) 추가.
- 회귀는 **새 파일 없이** 기존 jp 2종에 얹었다(63 + 26; 새 파일을 만들면 `--scope-only` 판정이 FULL 로 뒤집힌다). 이빨 변이 **8/8 발화**(사본에서만, 원본 md5 복원 확인).
- 검증: 빌더 **exit 0** · `RED 0건 · YELLOW 1건` · 산출 2종이 `generated_at` 외 전량 동일 · `prepush_check.py` = `REDUCED (jp-scope)` · **218 passed · 4 skipped** · `gate-clear`.

## 2026-09-13 (4차) -- jp 빌더의 `records count != 15` 를 census 파생 항등식으로 (TODO_jp(27) ②)

- 사고 유형(예방): **게이트가 사실이 아니라 옛 숫자를 지킨다.** 10/31 J-ICS 공시기한 직후 census 의 posted 가 15 → 60~70사로 뒤집히면 `build_jesr_page_json.py::self_check` 의 리터럴이 정상 데이터를 RED 로 막는다. 2026-08-29 분기 지평 사고(리터럴 분기목록 3곳 → 2026.2Q 미순회)와 같은 형태.
- 되돌려 재본 실측: `not_yet` 62사를 posted 로 뒤집은 합성 census(posted 77)를 **HEAD 빌더**에 물리면 `SELF-CHECK FAIL: records count = 77, expected 15` · exit 1. 새 빌더는 exit 0 · RED 0건.
- 숫자 대신 항등식: `census posted == _meta.census.posted == len(master) == len(deploy) + len(excluded)`. 개수는 "한 건 빠지고 한 건 중복" 을 통과시키므로 **집합**(company_jp·company_en)으로도 건다. `check_census_identity` · `check_deploy_identity` 신설.
- **0 으로 닫히는 등식 차단**: posted==0 이면 모든 등식이 성립하고 화면만 빈다 → `JP_CENSUS_EMPTY`. 종전에는 리터럴 15 가 우연히 이 구멍을 막고 있었다(리터럴 제거의 부작용을 같이 닫았다).
- 리터럴 전수 감사(AST): 일부러 둔 것 = `ESR_PCT_MIN/MAX`(100~1000%; 데이터에서 파생하면 틀린 값이 스스로 범위를 넓힌다) · `AS_OF_TARGET`(기간 선언; 10/31 은 같은 기간에 회사만 는다) · `SECTOR_MAP` · `PRELIM_KEYWORDS` · `DEAD_CLASSIFICATIONS` · `_SUFFIX_ABBREV`. 고친 것 = 회사 수 15 · `AS_OF_LABEL_JA`(→ `AS_OF_TARGET` 파생) · sector 어휘(→ `SECTOR_MAP.values()` 파생) · status/preliminary 어휘 상수화.
- 같이 닫은 사각: `company_en` 중복(2026-09-13 `6e051be` 실사고인데 게이트 침묵, 하류가 이 키로 조인) · `preliminary` 모르는 값(결측이 아니라 **오독** — 속보가 확정치로 표시된다) · `JP_CENSUS_SHAPE`(따옴표 없는 쉼표로 열이 넘친 posted 행) · esr_pct 결측 시 정렬 TypeError → 이름 붙은 RED.
- 새 발견 → jp 발주: census 14행 第一ライフグループ 이 18열(헤더 16열)이라 notes 가 잘려 읽힌다. 지금 `not_yet` 이라 무영향, 10/31 에 posted 로 뒤집히면 실린다. 티켓 `inbox/jp/20260913T1730Z__validation__JP_MULTI__census_ragged_row.md`. `jesr_sources_2026Q1.csv`·`jp_insurers.csv` 의 같은 모양 5행은 **읽는 열이 넘침 앞쪽**이라 영향 0(실측) — RED 로 걸지 않았다.
- 회귀는 **새 파일을 만들지 않고** `tests/test_jp_deploy_matches_census.py` 에 얹었다(23케이스 → 파일 전체 25). 근거: `prepush_check.py` §0 실측에서 빈 테스트 파일 하나만 추가해도 판정이 `REDUCED (jp-scope)` → `FULL` 로 뒤집힌다(`tests/` 는 jp 2종만 예외).
- 변이시험 11/11 발화(사본에서만, 종료 후 원본 md5 동일). "배선했다 ≠ exit code 가 바뀐다" 는 ① 진짜 빌더 exit-code 케이스 5종 ② 데이터로 도달 불가능한 배포 항등식은 AST 배선 검사로 나눠 잡았다.
- `NEXT_UPDATE` 는 데이터에서 파생 불가(편집상 약속)라 리터럴 유지 + 지나면 **경고만**. RED 로 하면 데이터 무변경 상태에서 날짜 경계에 빌더와 배포 테스트가 동시에 터진다.

## 2026-09-13 (3차) -- push 게이트 **범위 판정**을 훅에 구현 (문서에만 있던 CLAUDE.md §5 규칙)

- 사고 유형: 규칙이 문서에만 있고 코드가 안 본다. 방향만 반대일 뿐 "문서에 mandatory 라고 썼다 ≠ 강제" 와 같은 병이다. jp 만 고친 번들이 한국 원문 부재(`data/disclosure/`)로 `RED=197 → BLOCKED` — 인과 0.
- `scripts/prepush_check.py` §0 신설: `classify_path`(경로 1개 판정) · `decide_scope`(**git 을 안 부르는 순수 함수**) · `collect_changed_paths`(merge-base(@{upstream},HEAD)..HEAD + 스테이지 + 워킹트리 + 미추적, `-z`·`--no-renames` 필수) · `resolve_scope` · `print_scope`. 한국 축 게이트 5종은 `_run_korean_master_gates()` 한 함수로 묶어 **호출 지점을 하나로** 만들었다.
- fail-closed: upstream 없음/ git 실패 / 빈 diff / 미분류 경로 1개 → 전체 게이트. 축소는 전 경로가 명시 목록에 있을 때만.
- verdict 에 `SKIPPED(jp-scope)` 를 도입 — **0 을 'pass' 로 인쇄하지 않는다**("안 돌렸다"와 "통과했다"의 구분). 판정 근거(비교 ref·파일 수·결정적 파일)를 매 실행 인쇄.
- 오버라이드는 `--full` · `--scope-only` 둘뿐. **환경변수 우회로는 만들지 않았다**(켜진 채로 잊힌다).
- 셀프테스트 `tests/test_prepush_scope.py` 65케이스(1.5초) — 기대 경로 목록을 판정기 상수와 **따로 손으로 적어** 목록 삭제가 통과하지 않게 했다. 임시 git 저장소로 수집기까지 실검증(한글 경로·rename·미추적).
- 변이시험 12/12 발화(심링크 그림자 트리의 **사본만** 훼손, 종료 후 원본 md5 동일 확인).
- 실측: 축소 `exit=0` 4.97초(173 passed·4 skipped) ↔ 같은 트리 `--full` `exit=2` 16초(RED=197). 이 클라우드 클론은 한국 원문이 없어 전체 게이트가 원래 BLOCKED 다 — owner 머신의 ~18분과 다른 수치다.
- 매니페스트 갱신: `tests/test_push_gate_wiring.py::test_wired_means_wired_in_the_full_gate_only` — WIRED 의 뜻이 "전체 게이트에서 돈다" 로 좁아진 것을 명시.

## 2026-09-13 (후속) -- UH-18 배선 완료 · UH-19 신규·즉시 해소

- 룰 4종을 `J-ESR/build_jesr_page_json.py::source_gate_check` 에 배선, `self_check` → `main()` exit 1 까지 **변이시험으로 실증**. 회귀 43케이스(`tests/test_jp_source_gate.py`).
- 오프라인 유지: 네트워크 판정은 선행 단계가 증거 파일에 박제, 빌더는 박제를 읽는다. **dead 룰과 신선도 룰은 한 쌍** — 증거가 낡으면 dead 판정도 같이 낡는다.
- 예외 등재처 신설(셀 단위 키, fail-closed, `expires_on` 자동 해제, 절차 룰 면제 불가). 현재 0건.
- **UH-19**: "빌더를 안 돌리면 게이트도 안 돈다" 를 `tests/test_jp_deploy_matches_census.py` 가 막는다(빌더 재실행 후 커밋본과 전량 비교). 불변식 1번의 jp 판.
- 두 테스트를 `scripts/prepush_check.py` offline 묶음에 등재 — 배선과 강제는 다른 말이라는 2026-08-21 교훈 적용. `prepush_check.py` 를 고쳤으므로 그 라운드는 전체 게이트를 돌렸다.
- PM-2026-09-13 은 `open` 유지: `JP_ESR_NOT_IN_SOURCE` 미배선(선행조건 = 오탐억제 3종 실측 분포).

## 2026-09-13 -- jp 레인 false-green 3건: PM-2026-09-13 + UH-18(룰 4종 미배선)

- 사고: jp 빌더 self-check RED=0 인데 화면 수치 2건이 2차보도·조정치, 출처 1건은 무관 문서. 상세 `docs/postmortems/PM-2026-09-13_jp_secondary_source_and_dead_url.md`.
- 원인 유형: **"산술만 검사"(PM-2026-06-16)의 jp 판** — 범위·형식·합계가 census 내부에서 닫혀 외부 대조 축이 없다.
- 룰 4종 정의(입력·판정식·임계값·severity·오탐억제). 오탐억제가 핵심이다: 봇차단 403·WAF 4xx·파이썬 TLS 실패를 dead 와 섞으면 전수 254건 중 41건이 거짓 RED 이 된다.
- **배선 0.** 도구만 신설(`J-ESR/check_source_urls.py` exit 1, `J-ESR/edinet_esr_probe.py`). UH-18 등재, 티켓 발주.
- 파생 결정: jp 예외 등재처가 없다 — 배선 시 `J-ESR/jp_source_exceptions.json` 을 같이 만든다(exemption 추가는 owner 권한).

## 2026-09-11 — `public_exports/` 변이시험을 임시 복사본으로 (제자리 훼손 폐지)

> 끊긴 실행이 남긴 가짜 행 1건(`존재하지않는보험`)이 워킹트리 `public_exports/CSM워터폴.json` 에 남아 prepush 오프라인 테스트(`test_public_export_clean_state_has_no_findings`)를 막았다 — 2026-09-01 두 번에 이어 세 번째. 커밋·라이브는 무관(HEAD 깨끗). 구조 수정: `validate_live_artifacts.check_public_exports(fd, out_dir=None)` 폴더 주입, `test_mutation_public_export_fires(mutation, tmp_path)` 는 `shutil.copytree` 사본만 훼손. dirty-check·백업·`finally` 복원 삭제. 실측 149 passed · 변이시험 후 워킹트리 깨끗 · 게이트 RED=0.

## 2026-09-02 — `MASTER_XLSX_*` 축 신설: 마스터 JSON ↔ 마스터 xlsx 13시트 전수 대조 (CHECK 8)

**무엇이 통과하고 있었나.** 루트 마스터 JSON 의 하류 사본은 **둘**이다 — `public_exports/`
스냅샷과 `insurequant_master_tables.xlsx`. 그런데 검사기는 하나뿐이었다:
`PUBLIC_EXPORT_*`(`validate_live_artifacts.py` check 6)가 스냅샷만 본다. **마스터 ↔ xlsx 를
대조하는 룰은 저장소에 0건이었고**, xlsx 만 조용히 뒤처져도 RED 가 구조적으로 나올 수 없었다.
`sync_master_xlsx_sheet.py` 는 요청받은 시트 하나만 동기화하고 스스로 뒤처짐을 탐지하지 않는다
— 정합성이 "누가 어느 시트를 동기화할지 기억하는 것"에 걸려 있었다.

**사고 2건(2026-09-02).** ① owner 라이브 QA: NH농협손해 2026 기본자본비율 전망이 라이브·마스터
102.77 인데 xlsx `자본비율전망` 만 79.8(= 그 회사 **2026.1Q** 값). 마스터가 baseline 을 2026.2Q
로 옮겼는데 시트만 1Q 기준 옛 산출이었다 — 38개사 전부, 2090칸 중 **1219칸 stale**.
② owner 가 "소진율 2종도 stale 하겠네" 라고 지적해 13시트를 전수 측정했더니 **가설과 결과가
달랐다**: 소진율 2종은 깨끗했고 아무도 안 보던 `K-ICS공시` 가 stale(33셀·121행). 교훈은
**"어느 시트가 stale 한지 추측하지 말고 전수로 재라"**. 데이터 수정은 `d1f1e7f`·`ee11c1d`.

### 신설

- `scripts/check_master_xlsx_drift.py` — 13시트 전수 셀 단위 비교기. 시트목록·평탄화·타입강제는
  `build_master_xlsx`(`MASTERS`/`FLATTEN`/`coerce`/`TEXT_COLS`)에서, 목표행·비교정규화·행식별키는
  `sync_master_xlsx_sheet`(`target_rows`/`norm`/`key_of`)에서 **import** 한다. 재타이핑하면
  빌더가 바뀌는 순간 검증기가 검증 대상과 다른 스키마를 쓰게 된다(상관행렬 재타이핑 금지와 같은 이유).
- `validate_data_contract.py` CHECK 8 `check_master_xlsx` → `run_gate` → `prepush_check.py` §1
  → `.githooks/pre-push`. **훅이 실제로 부르는 것을 소스에서 확인함**(L39 `gate.run_gate(env)`,
  L246 `blocked = n_red or ...`).
- 룰 14종: `MASTER_XLSX_DRIFT`·`ROW_MISSING`·`ROW_EXTRA`·`SHEET_MISSING`·`COLUMN_MISMATCH`·
  `KEY_AMBIGUOUS`·`FILE_MISSING`·`UNREADABLE`·`FORMULA_PRESENT`·`MASTER_UNREADABLE`·
  `SUMMARY_ROWCOUNT`·`SUMMARY_SHEET_MISSING` (RED) + `UNTRACKED_SHEET`·`CENSUS` (YELLOW).

### 판단 3개와 근거

- **비교 기준은 동기화 스크립트와 정확히 같다**(`norm()` 을 import). 느슨하면 값 차이를 놓치고,
  **엄하면 더 나쁘다** — 어떤 도구도 만들 수 없는 상태를 요구해 영원히 못 고치는 RED 이 된다.
  그래서 `'154'`(문자열) vs `154.0`(실수)는 **드리프트가 아니다**(셀 타입 차이일 뿐. `coerce()` 가
  값 아닌 열을 문자열로 만드는데 Excel 로 열어 저장하면 숫자로 되돌아간다). float 는 `%.15g`
  (xlsx 가 실제로 저장하는 정밀도)로 접는다. 그 위에 **추가 tolerance 는 두지 않는다**.
- **행 식별키 = `TEXT_COLS` ∪ `{항목번호}`** — 동기화와 같은 규칙. `비고` 도 여기 들어가므로
  비고 문구 변경은 EDIT 이 아니라 ROW_MISSING+ROW_EXTRA 쌍으로 나온다(자본비율전망 169행이 그랬다).
  키를 다르게 잡으면 동기화가 방금 만든 상태를 게이트가 계속 드리프트라고 부르게 된다.
- **`요약` 은 행수만 검사한다.** 행수는 기계가 유지하지만(sync L292-303) **설명 열은 다른 레인이
  손으로 관리한다**(sync L21-22·L271-272 가 "손대지 않는다"고 명시). 기계가 정본을 갖고 있지
  않은 열을 검사하면 정당한 손질이 매번 RED 이 된다. `MASTERS` 밖 수기 시트는 허용된 설계라
  RED 이 아니라 YELLOW census(무검사 축의 가시화).

### 검증

- **배선 전 시뮬레이션(규율)**: 전 시트에 먼저 돌려 **RED=0 · YELLOW=0** 확인
  (13시트 · 53,288행 — 워크북의 전 데이터 행과 정확히 일치).
- **되돌려 재본 실측**(`scripts/_probes/probe_20260902_master_xlsx_retrodiction.py`): 두 수정
  커밋이 xlsx 만 건드렸으므로 그때 워크북을 꺼내 오늘 마스터로 대조 →
  `d1f1e7f~1` **RED=5**(자본비율전망 DRIFT 1111 / ROW_MISSING 169 / ROW_EXTRA 169 ·
  K-ICS공시 DRIFT 33 / ROW_MISSING 121) · `ee11c1d~1` **RED=2** · `HEAD` **RED=0**.
  숫자가 두 커밋의 자체 기록과 **셀 단위로 일치**한다 — 이 룰이었으면 사람이 발견하기 전에 막았다.
- **변이시험**: `tests/test_rule_coverage_manifest.py` 신규 18개 — 변이 8종(값·행누락·행잉여·**행복제**·헤더·
  요약행수·요약행소실·미등재시트) + **2026-09-02 사고 값 그대로 재생**(79.8) + 타입변경
  비드리프트(양방향) + import-대신-재타이핑 금지 + 읽기전용 정적검사 + run_gate 배선.
  ⚠️ **변이는 전부 메모리 안에서 한다 — 워크북을 재저장하지 않는다.** openpyxl load+save 한 번에
  다른 시트 수식 캐시가 날아가고 실행이 끊기면 복원도 안 된다(memory
  `project_master_xlsx_formula_cache`). 그래서 `compare_sheet`/`scan(sheets=...)` 을 순수 함수로
  분리했다. 픽스처가 읽기 전후 **바이트 해시 대조**로 무변경을 실측한다.
- 회귀: `--selftest` **57/57 유지** · `test_push_gate_wiring` 55 passed · `test_deploy_assets` 등
  오프라인 묶음 통과 · 게이트 **RED=0 유지**(YELLOW 96→97, census 한 줄 추가).
- **실행 비용**: 게이트 안에서 **+11.9초**(15.2 → 27.1초). 훅 전체 17분 33초 대비 **+1.1%**.

### 잔여

**UH-15**(하류 사본 매니페스트 부재 — 세 사본이 전부 사고 후에야 검사 대상이 됐다.
PM-2026-08-25 의 UH-14 와 같은 뿌리라 합류) · **UH-16**(`sync` 가 시트 무변경 시 `요약` 행수를
안 고친다 — 현재 무해, 발화하면 그때 `--summary-only` 추가) · **UH-17**(워킹트리 기준 대조라 sync 후 커밋 없이 push 하면 안 잡힌다 — `PUBLIC_EXPORT_*` 와 달리 마스터 쪽을 `git show HEAD:` 로 읽지 않는다. 커밋 기준은 정상 sync 중 상시 발화라 미배선). 포스트모템
`docs/postmortems/PM-2026-09-02_master_xlsx_stale_unchecked.md`.

## 2026-09-01 — 소급재작성(restatement) 축 신설: 탐지기 + 등재부 + 게이트 CHECK 7

**무엇이 통과하고 있었나.** 정기경영공시의 `[경과조치 적용 전 지급여력비율 세부]` 표는
해당·직전·전전분기 **3열**을 인쇄한다. 그래서 같은 (회사,분기) 값이 두 번 인쇄되고, 발행사가
그 값을 다르게 인쇄하면 소급재작성이다. **그 두 인쇄값을 대조하는 검사기가 저장소에 0개였다.**
교보생명(KR0073)의 2026.1Q 재작성이 분기 변동 분석 중 손으로 발견되면서 드러났다.

**왜 중요한가 — 이 저장소는 이미 같은 병으로 데였다.** `data/_gold/csm_amort_identity_ledger.json`
의 `RESTATEMENT_BASIS` 3건(DB손해 2023.1~3Q): 루트 `CSM_waterfall` 은 2024년 필링의 비교컬럼
(=재작성값)인데 `PL_breakdown` 은 2023년 원 필링값이라 두 마스터가 서로 안 닫힌다. 한 축만
재작성값으로 갈아끼우면 축이 갈라지고, **그 순간을 잡는 검사가 없었다.**

### 39사 전수 재스캔 (실측)

판정 축은 **필링 대 필링**이다 — FY2026_Q1 공시본의 `해당분기` 열 vs FY2026_Q2 공시본의
`직전분기` 열. 둘 다 발행사가 인쇄한 값이라 마스터가 판정에 끼지 않는다.

| | |
|---|---|
| 회사 | 39/39 (미판독 **0**) |
| 비교 셀 | **830칸** (그중 마스터 대역 6칸) |
| 미비교(검사 사각) | **0칸** |
| 재작성 회사 | **1개사 — 교보생명(KR0073) 2026.1Q, 10칸** |
| 마스터 != 1Q 원공시본 | **0칸** (K-ICS 마스터가 as-filed 기준임을 실측 확인) |

교보 10칸: item1·2·4·11 각 +1 / item14 +871 / item15 +888 / item16 +445 / item19 +779 /
item20 +553 / item22 +16. 발행사 사유가 2026.2Q 공시본에 직접 인쇄돼 있다
(`data/disclosure/FY2026_Q2/parsed/KR0073_교보생명보험.md` L455).

### 오탐 3원인을 코드로 막았다

1차 손스캔이 기타포괄손익누계액·신종자본증권을 재작성으로 잘못 잡았던 원인:

1. **표를 정확히 하나 특정한다.** `분산효과`+`기본요구자본`+`지급여력기준금액` 이 같은 페이지에
   있는 곳만 표로 인정하고, 숫자 x좌표 히스토그램의 우측 3개 컬럼대만 취한다. 표의 마지막 행
   (`다. 지급여력비율 : 가 ÷ 나 × 100`)에서 페이지 창을 닫는다 — 안 닫으면 같은 절의 백만원
   단위 경과조치표를 같이 긁어 매핑이 밀린다(KR0097 실측: 가짜 재작성 1건).
2. **소수자리를 원 토큰에서 센다.** float 로 바꾼 뒤 문자열화하면 정수 `"4160"` 이 `"4160.0"`
   이 되어 1자리로 잡히고, 소수를 가진 마스터(4159.89)와의 반올림 차가 전부 '재작성' 이 된다
   — 악사손해 8건이 그렇게 나왔다.
3. **item27(지급여력비율)은 파생값이라 축에서 뺀다.** 마스터는 item1/item14×100 을 소수
   8자리로 담는데 공시본은 1~2자리로 인쇄한다. 부모 item1/item14 의 재작성이 이미 말해 준다.

### 커버리지 — "CLEAN" 에 안 본 칸을 섞지 않았다

- 표가 **두 페이지에 걸치는 회사**가 있다. 단일 페이지만 보던 초안은 삼성생명 항목 1~13 을
  통째로 안 보고도 CLEAN 을 찍었다(신한이지·카카오페이·처브·BNP 는 반대로 22~26).
- **행 자기 라벨 우선 매핑**: 이웃 행 라벨이 병합돼 들어오면 앵커가 둘 잡혀 매핑이 밀린다
  (KR0097 조정준비금 행에 `6. 비지배지분` 이 붙어 item10 으로 매핑 → 가짜 재작성 1건).
- **발행사 오식 대응**: KR0099(KB라이프)는 `Ⅱ. **지분**여력금액으로 불인정하는 항목` 으로
  인쇄한다. 변형을 안 넣으면 그 회사 item12 가 통째로 미비교로 빠진다.
- **스캔 PDF 5사**(KR0010·KR0049·KR0079·KR0080·KR0087)는 fitz 로 못 읽는다.
  "키워드 0회 = 원문 없음" 으로 단정하지 않고 **150dpi 렌더링 육안 판독** 후
  `VISION_ANCHORS` 에 인용(파일·페이지)과 함께 박았다. 5사 전부 **재작성 0** 확인.
- 좌표가 못 잡는 잔여 10칸은 `MANUAL_CELL_ANCHORS` 에 원문 인용과 함께 박았다.
- 결과: 미비교(마스터는 값이 있는데 양쪽에서 못 뽑은 칸) **0**.

### 심각도 — 왜 YELLOW 인가 (과거 13개 분기쌍 시뮬레이션)

| pair | 재작성사 | 셀 | 미판독사 | 비교칸 |
|---|---|---|---|---|
| 2023.3Q→4Q | 5 | 29 | 3 | 781 |
| 2023.4Q→2024.1Q | 3 | 5 | 3 | 776 |
| 2024.1Q→2Q | 5 | 12 | 5 | 729 |
| 2024.2Q→3Q | 5 | 24 | 6 | 731 |
| 2024.3Q→4Q | 4 | 6 | 9 | 669 |
| 2024.4Q→2025.1Q | 2 | 5 | 8 | 683 |
| 2025.1Q→2Q | 4 | 10 | 5 | 751 |
| 2025.2Q→3Q | 3 | 4 | 5 | 746 |
| 2025.3Q→4Q | 4 | 12 | 5 | 732 |
| 2025.4Q→2026.1Q | 1 | 5 | 6 | 694 |
| **2026.1Q→2Q** | **1** | **10** | **0** | **830** |
| 합(13쌍) | **37** | **122** | 132 | — |

**재작성은 드문 사고가 아니라 상시 현상이다** — raw 가 갖춰진 2023.4Q 이후 매 분기 1~5개사.
RED 로 내면 거의 매 라운드 push 가 막히는데, 막아서 고칠 것이 없다(발행사가 자기 과거 분기를
정정하는 것은 정당한 행위이고 우리 데이터의 결함이 아니다). 그래서:

- 재작성 발견 자체 → **YELLOW**(등재부 박제)
- **RED 은 마스터가 원공시본 기준을 벗어날 때만** — `MASTER_ADOPTED_RESTATED`(재작성값
  채택) · `PIN_DRIFT`(제3의 값) · `CELL_MISSING`(결측은 SKIP 이 아니다) + 등재부 위생 3종
  (`FIELD_MISSING` · `KEY_MISMATCH` · `LEDGER_UNREADABLE`)
- 침묵 방지 YELLOW 4종: `CENSUS` · `LEDGER_ABSENT` · `SCAN_STALE`(새 분기가 오면 다시 재라)
  · `COVERAGE_GAP`(못 읽은 회사가 있으면 그 CLEAN 은 측정이 아니라 부재다)

과거 122칸은 **등재부에 넣지 않았다.** 컨트롤 컬럼 대조·잔여셀 육안 판독을 안 했고 쌍당
3~9개사가 미판독이라 검증된 census 가 아니다 — `_history_probe` 에 **미검증 표시로만** 남겼다.
검증 안 된 건을 박제하면 그 박제가 곧 무검사가 된다.

### 배선 — "배선했다" 와 "강제된다" 를 따로 확인했다

- `check_kics_restatement` 를 `run_gate()` 에 넣었고, `scripts/prepush_check.py` L38-39 가
  `gate.Env()` / `gate.run_gate(env)` 를 부른다 → **훅에 걸린다**(`.githooks/pre-push`).
- 게이트는 **PDF 를 읽지 않는다.** `data/disclosure/` 는 .gitignore 대상이라 slim 클론엔 PDF 가
  없고, 매번 읽으면 클론마다 답이 달라진다. 필링 대 필링 판정은 탐지기
  (`scripts/detect_kics_restatement.py`, ~28초)가 분기마다 한 번 돌려 등재부에 굳히고,
  게이트는 그 등재부를 **라이브 마스터에 대고 매 실행 재검산**한다(결정적).
- `tests/test_push_gate_wiring.py` `DATA_CONTRACT_CHECKS` 에 `WIRED` 선언(빼면 테스트가 막는다).
- `tests/test_rule_coverage_manifest.py` 에 17개: 룰 id 대조 · **등재 칸 수 박제**
  `KICS_RESTATEMENT_CENSUS=(10,1,39,0)` · 근거 완전성 · 변이시험 10종 · tol 양방향
  (0.4 침묵 / 0.6 RED) · **탐지기와 게이트가 같은 등재부 경로를 본다**(베껴 쓰면 갈라져도
  아무도 모르는 그 패턴 차단) · `run_gate` 배선.
- `--write` 는 손으로 붙인 최상위 필드를 **보존**한다(통째 덮어쓰면 한 번에 조용히 사라진다).

### 실측 (전후)

```
scripts/validate_data_contract.py     RED=0 YELLOW=201 exit 0   (적용 전)
scripts/validate_data_contract.py     RED=0 YELLOW=203 exit 0   (적용 후, +버킷1 +census1)
scripts/_probes/probe_20260901_restatement_rule_simulation.py   ALL PASS
   ① 닫힘 RED=0  ② 변이 15/15 검출  ③ 등재 밖 200칸 변이 신규 RED 0
pytest tests/test_push_gate_wiring.py                 53 passed 1 skipped
pytest tests/test_rule_coverage_manifest.py -k restatement    17 passed
```

### 곁가지 — 정책이 선언된 적이 없다 (owner 판단 필요)

“K-ICS 마스터는 각 분기 원공시본을 담는다” 는 **저장소 어디에도 선언돼 있지 않았다.**
가장 가까운 서술은 `kics_exemption_provenance.json` KR0032 2024.3Q 엔트리인데, 같은 엔트리가
“as-disclosed 를 유지할지 as-restated 를 채택할지는 owner/parser 정책 결정이고 이 세션은
정하지 않았다” 라고 명시한다. **그리고 IFRS17 CSM 축에서는 owner 가 반대로 결정했다**
(2026-06-20 교보/라이나: 후속 분기 비교표에서 재작성값 pull → 재작성 기준으로 통일).
따라서 “저장소가 전부 as-filed 로 정렬돼 있다” 는 서술은 사실이 아니다 — K-ICS 는 as-filed,
`CSM_waterfall` 은 일부 셀이 as-restated 다. 새 등재부의 `_policy` / `_policy_note` 에 이
사실관계를 그대로 적었고, 기준 변경은 owner 결정 사항으로 남겼다.

### 곁가지 2 — 공개 스냅샷이 마스터보다 2커밋 뒤처져 있다 (내 변경 아님)

`tests/test_rule_coverage_manifest.py::test_public_export_clean_state_has_no_findings` 가
`PUBLIC_EXPORT_DRIFT` 36건 + `MISSING_CELL` 1건으로 실패한다. 원인은 커밋 순서로 확정했다 —
`31c5598`(스냅샷 재생성) 이후 `523002e`·`e684f69` 가 `kics_disclosure.json` 을 고쳤는데
`scripts/export_public_sheets.py` 를 다시 안 돌렸다. 이번 세션은 마스터·스냅샷을 건드리지
않았다. publishing 에 발주:
`inbox/publishing/20260901T1200Z__validation__MULTI__public_exports_stale_after_kics_fixes.md`.
(`test_full_gate_coverage_matches_manifest` ERROR 는 pytest tmp 디렉토리 `PermissionError`
= 환경 문제이지 코드 문제가 아니다.)

### 곁가지 4 — 떨어진 음수부호. **마스터가 옳았고 내 추출기가 틀렸다**

마스터 2026.1Q 를 1Q 원공시본과 셀 단위로 맞춰 보다가 삼성생명 item8(자본조정)에서
Δ −42,340억이 나왔다(마스터 −21,170 vs 내 판독 +21,170). 원문 확인 결과 발행사가
`- 21,170` 처럼 **마이너스와 숫자 사이에 공백**을 두고 인쇄하고, fitz 가 그걸 두 단어로
돌려주는데 내 토크나이저가 앞의 `-` 를 라벨로 흘려 부호를 잃은 것이었다. **마스터는 정확했다.**

이건 그냥 오탐이 아니라 **부호를 가진 셀 전체(item8·9 등)의 판정을 무력화하는 결함**이라
탐지기에 붙였다: 같은 줄에서 x 간격 6pt 이내에 홀로 선 `-`/`△`/`▲`/`−` 가 앞서면 숫자에
붙인다. 수정 후 마스터↔원공시본 일치 817 → **818**, 불일치 5 → **4**(남은 4건은 전부 ±1억 —
마스터가 더 정밀한 백만원 표에서 왔고 억원 표와 반올림이 갈리는 자리다: KR0010 항목3·4,
KR0049 항목4, KR0080 항목3).

**교훈**: "마스터가 틀렸다" 로 가기 전에 내 추출기부터 의심할 것. 이번엔 그 순서가 맞았다.

### 곁가지 3 — KR0029 2025.3Q 면제의 `registered_by` 가 자기부정 문장이었다

`kics_exemption_provenance.json` 의 그 엔트리는 커밋 `17286e0` 으로 **이미 살아있는 원장에
반영돼 있고** 게이트가 박제잔차 −58.0 을 실측 −58.0(Δ 0.00, tol 0.01)으로 재검산하는데,
`registered_by` 는 “DRAFT — 미적용 … 살아있는 원장에 아직 반영되지 않았다” 라고 적혀 있었다.
다음 세션이 “이 면제는 아직 안 걸렸다” 로 오독할 문장이라 **그 한 줄만** 고쳤다(판정·잔차·
인용 불변, diff 1줄). 이 티켓(`inbox/validation/20260831T203021Z`)은 그 사이 다른 세션이
`_resolved/` 로 옮겼다.

## 2026-09-01 — KR0094 신한라이프 2026.2Q `36_irr` 면제 등재 + 41-46 적용후가 순회조차 안 되던 사각 폐쇄

owner 2026-09-01 승인. 2026-08-21 최초 5건 승인의 연장(등재 5 -> 6건).

**등재.** `IRR_DERIVE_ISSUER_INCONSISTENT[("KR0094","2026.2Q")] = {"적용전": 2979.8030762296203,
"적용후": 2979.8030762296203}`. 잔차 = item36(공시 10655.45) − `irr_derive_expected(41~46)`
(7675.64692377038), 잔차/item36 **+27.97%** 로 기존 대역(+5.25%~+25.62%)을 처음 넘었다.
**대역을 넘었는데도 등재한 근거는 '같은 성질' 이지 '크기' 가 아니다**: ① item36 은 이번에도
시장위험 축에서 닫힌다(item19 27,807.00 vs sqrt(item36~40·MARKET_M) 27,807.2756, rel
**−0.00099%**, 기존 대역 −0.00157%~+0.00222% 안, 적용전·적용후 동일) ② 41-46 은 raw p28
자기완결 표와 소수점까지 일치(순자산가치 6,319,163/6,448,867/5,427,499/7,105,796/6,348,177/
6,219,031 · 금리위험액 1,065,545 백만원). 후속 세션은 이 확장을 선례로 삼지 말 것 — 잔차
크기는 등재 사유가 아니고 위 두 조건을 매 건 실측해야 한다.

**진짜 발견은 따로 있다 — 적용후 축이 이 버킷을 순회조차 안 하고 있었다.** 등재 전 실측:
`_transition_irr_after` fails **0**, 그 대신 `POST_SCENARIO_ABSENT(짝수Q·적용전완비)` **142**.
41-46 적용후가 결측이라 검사 대상에서 아예 빠져 있었던 것이고, 게이트는 그걸 RED 로도
SKIP-사유로도 보고하지 않았다. **"룰이 0이라고 말한다" 와 "그 축이 깨끗하다" 가 갈린 자리다.**

원인은 데이터가 아니라 **커버리지 상수**였다: `scripts/fix_20260716_nonapplier_requirement_mirror.py`
의 `TIER3_ITEMS = list(range(36, 41))` — 36~40 에서 끊긴다. **41-46 은 어느 tier 에도 없어서**
비적용사 미러가 한 번도 그 6칸을 건드린 적이 없다. 그래서 KR0094 2026.2Q 는 36-40 에는 미러가
있고 41-46 만 비어 있었다.

**미러를 채운 근거는 추론이 아니라 발행사 명시다.** raw `data/disclosure/FY2026_Q2/pdf/
KR0094_신한라이프생명보험.pdf` — p19 경과조치 적용여부 O/X 표가 **전 항목 X**(TFI·TAC·TIR·TER·
**TIRR**·적기시정조치 유예), p21 ②-iii "당사는 주식위험 경과조치 또는 금리위험 경과조치를
적용하지 않아 경과조치 전·후 금액 및 비율이 동일함"(이 축을 직접 지목), p22 주2 동일 취지.
KR0094 는 `_TRANSITION_APPLIERS` 밖이고 owner 상시룰은 "비적용사 적용후는 미러 가능, 적용사인데
미공시면 공란 유지"다(`scripts/fix_20260821_kr0097_2024q2_irr_post_denull.py`). p28 표의
컬럼축은 충격 전/충격 후 = **시나리오 축이지 경과조치 축이 아니다**.
채운 스크립트: `scripts/fix_20260901_kr0094_2026q2_irr_post_mirror.py` (6칸 UPSERT, 전후 지문
대조로 범위 밖 변경 0 단언). **채우는 것이 검사를 넓힌다**: fails 0->1 · ABSENT 142->141 이 되고
그 잔차를 박제한다. 빈칸으로 뒀으면 적용후 축은 영구 사각이었다.

**실측 전/후.** `validate_kics_disclosure.py` 36_irr RED **1 -> 0**(다른 룰 불변, 면제 12축 전부
MATCH) · `validate_data_contract.py` RED **67 -> 62** 중 내 몫은 `KICS_36_irr 신한라이프 2026.2Q`
**1건**(나머지 4건은 병행 흥국화재 세션). 신규 RED 0.
`tests/unit/test_irr_pin_exemption.py` **3 failed/6 passed -> 9 passed**.
근거 원장 `data/_gold/kics_exemption_provenance.json` +1(40->41), `EXEMPTION_*` 소견 12 -> 12 무변
(신규 항목이 provenance·pin-ledger 검사를 그대로 통과). 원장 마커는 `present_markers` 14개 +
`present_rows` 3개(행 귀속 Δ 0.00~0.37pt, 밴드 3.0pt)로 **행 귀속까지** 건다.

**2026.1Q 는 면제 대상이 아니다 — 추출갭도 아니다.** 41-46 결측은 **서식 부재**다. 실측: 2026.1Q
filing 은 36쪽 축약본으로 `6-4. 시장위험 관리`·`② 금리위험액 현황` 이 통째로 없고(36쪽 전수 fitz
스캔, 텍스트레이어 정상 — 최저 59자는 섹션 구분면), 산업 전체로도 item41 보유 회사가 2026.1Q
**0/39** · 2025.1Q **0/39** · 2025.3Q **0/38** 이다(시나리오표는 2Q/4Q 전용 서식). 룰이 이미
`홀수분기 서식부재` 로 정확히 SKIP 하고 있어 손댈 것이 없다. 파서 발주 불요.

**미결(내 범위 밖).** ① `tests/fixtures/kics_rules_golden.json` 은 재생성하지 않았다 — 내 기여는
`36_irr` RED->SKIP **1행뿐**임을 통제실험으로 확인했으나(내 변경을 뺀 대조군 해시가 픽스처와도
불일치), 픽스처가 병행 세션 때문에 이미 stale 이라 지금 `--update` 하면 남의 미완 상태를 박제한다.
그 세션이 정착한 뒤 재생성해야 하고, 그때 내 1행도 같이 들어간다. ②
`tests/fixtures/post_transition_golden.json` 드리프트(6574->6632셀)는 **내 것이 아니다** — 내
변경 유무로 해시가 동일하고(`b1581fe2…`) KR0094|2026.2Q 는 그 도출에 등장조차 안 한다. ③
`src/solvency/validation/kics_json_rules.py` 주석과 `validate_kics_disclosure.py` 가 가리키는
`tests/test_exemption_pin_ledger.py` 는 **실존하지 않는 파일**이다(dangling 참조). ④ 41-46
적용후 결측은 저장소 전체로 144 (회사,분기) 남아 있다(적용전 완비·적용후 전무, 부분결측 0).
다수는 경과조치 적용사라 공란이 정답이지만, 비적용사 몫은 위 `TIER3_ITEMS` 갭이 원인이라 같은
사각이 그대로 열려 있다.
