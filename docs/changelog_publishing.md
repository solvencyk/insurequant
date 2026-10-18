# Insurequant Changelog — Publishing Stage

> Last updated: 2026-10-19 · Stage 4/5 — publishing
> Prompt: docs/agents/claude-agent-publishing.md · TODO: TODO_publishing.md

**Scope:** master JSON assembly + change reporting + git push command recommendation. HTML structure/styling is **designer** ([`docs/changelog_designer.md`](changelog_designer.md)).

**Cross-stage history:** `docs/claude-changelog.md`.
**This file:** entries scoped to publishing work only.

---

> 보관: 이전 달 항목은 `docs/changelog_archive/publishing/` 에 월별로 무수정 보관한다(관리 `scripts/doc_rotate.py changelog`, 현행 = 최신 항목 달과 그 전 달).

## 2026-10-19 — IFRS17 8절 현재가치 이중 반올림 수정 (티켓 `20261018T0700Z`, 커밋만 · push 보류)

- 저장 빌더는 `scripts/viz_build_persistency_lossratio_panels.py` 였다. `_ratio()` 가 공시 2자리 값이 금액으로 재현되면 반올림 전 비율(소수 6자리)을 싣고, 아니면 공시값을 유지한다(가드 `b != 0` 으로 위험보험료 음수 잎 32칸도 포함). `data/loss_ratio/panel_loss_ratio.json` 206,474 → 281,737 바이트, 구조 동일 · 바뀐 숫자 18,853개 모두 변화 0.005 이하 · meta.note 한 곳.
- 효과: 화면 표시값과 마스터 금액 재계산값의 차이가 0.05pp 를 넘는 칸이 약 800개(현재가치 77) → 0(약 21,900칸 전수). 마스터 · HTML 무수정. 이 패널을 고정하는 골든은 없어 `--check` 와 `tests/test_push_gate_wiring.py` 가 고정한다. 독립 검증 통과.

## 2026-10-13 — parser-ifrs17 `b8c37fff` 파생 산출물 재생성 (NB 배수 · 비교 패널 · CSM 콤보 · xlsx/공개본, 커밋 `99c7ead7` + 공개본 커밋, 커밋만 · push 보류)

- 배경: `b8c37fff` 가 `CSM_waterfall`·`PL_breakdown`·`IFRS17_BS` 의 249셀을 고쳤으나 파생 파일을 다시 만들지 않아 `validate_live_artifacts` RED `NB_VS_WATERFALL` 메리츠 2023.3Q(NB 12,346.8 대 워터폴 12,197.6).
- 재생성(확립된 빌더만, 마스터는 안 씀): `build_nb_csm_multiple.py` -> `NB_CSM_multiple.json` **12칸**(동양 2023.1Q 신계약CSM 1,762.7 -> 1,762.9 · 2023.2Q 당분기 1,825.1 -> 1,824.9, 메리츠 2023.3Q 12,346.8 -> 12,197.6 · 2023.4Q 당분기 3,659.7 -> 3,808.9 과 배수). `viz_build_compare_panel.py` -> `data/compare/panel_compare.json` **69잎**(재구성 시험 `z2_attribute_panels.py`: 63잎 = b8c37fff + NB, 6잎 = b8c37fff 이전부터 낡아 있던 현대해상·삼성생명 지표). `viz_build_csm_combo_panel.py` -> `data/csm_combo/panel_csm_combo.json` **8잎**(메리츠·동양·흥국화재 2023 분기 CSM 4칸 + `est_unreliable` 명단 1사 교체). xlsx `신계약CSM배수` 12칸 `sync_master_xlsx_sheet.py` 시트 반영, 공개본 `신계약CSM배수`·manifest 재생성.
- 변경 없음(재실행으로 확인): `viz_build_ifrs17_panels.py`(csm_amort_schedule · insurance_pl_breakdown · bs_snapshot · sensitivity_heatmap) 와 `viz_build_csm_waterfall.py` 는 `data/dart/extracted` 를 읽어 산출이 HEAD 와 바이트 동일. 손해율·유지율·`data/company_segment.json` 은 이 마스터들을 티커 조회로만 읽어 재생성 대상 아님. `downstream_kpis.json` 은 어느 화면도 안 읽어 건드리지 않음(기존 보류).
- 크기: 지시한 249셀 범위 안(NB 12칸 + 패널은 그 파생값). 249셀 밖의 큰 변동 없음; 단 `panel_compare` 의 6잎은 이전부터 낡은 상태였다.

## 2026-10-13 — 독립 감사 티켓 `20261012T2235Z` 요청 1·2·3 + owner 결정 8: 콜일 상충 · 하나손해 추정 행 · 기본자본 인쇄 한도 · 보완자본 기발행 차감 (커밋 `48c7c3ac` + 공개본 커밋, 커밋만 · push 보류)

- **요청 1 (DB손해보험 제1·2회 콜일).** 원 공시 전수 대조(`y1_db_call_dates_all_filings.txt`): FY2025 3Q·사업보고서는 두 회차 모두 2030년 9월 1일, FY2026 1Q·반기보고서는 제1회 9월 25일·제2회 9월 1일, 발행일+5년이면 제1회 09-01·제2회 09-25 - 발행사 문서끼리 어긋나 확정 불가.
  바뀐 필드: `data/bonds/capital_securities_fy2026h1.json` KR0011 두 건 `call_source` disclosed -> `conflicting_filings`, 신규 `call_date_unconfirmed`·`call_date_candidates`·`call_date_note` (`call_date` 는 forward 가 연 단위로 읽어 그대로).
  `kics_capital_securities_timeline.json` 두 건: `outstanding_eok` 7,470/1,200 -> **null** + `call_date_unconfirmed: true`(커밋된 K-ICS.html `75234ddf` 가 잔액 null 인 콜 후보는 날짜만 그리므로 셀이 「콜 상환 도래일 : 2030-09-01」 만 보인다). 공개 시트 `자본성증권발행현황` 두 행: 콜만기도래일 비움, 콜근거 「공시 원문 상충(콜일 미확정)」. 검사기 `CAPTL_FIELDS`·잔액 null 허용(표지와 함께일 때만).
- **요청 2 (하나손해 원장).** 선택: 추정 행(`estimated`) - 「원장 미갱신」 표식은 HTML 이 필요해 제외. KR0050 에 2026-06-29 발행·999억(항목 6 +999)·금리/콜/만기 null 한 건 추가(회사 합계 199,900백만), 등재부 2026.2Q 항목의 `issue_date` 를 2026-06-29 로 맞춤. 결과: 신종 발행잔액 1,000 -> 1,999억(`hybrid_outstanding_eok`), 총발행액·2026 막대 반영, 최근 발행금리는 「—」. forward: 콜일이 없어 이벤트가 안 생기므로 투영 전 항목 동일(KR0050 행의 `confidence` 만 갱신: 기본자본 격차 -50% -> 0%), 나머지 46행 불변.
- **요청 3 (기본자본 인쇄 한도).** `capital_utilization_rules.tier1_binding`: 결속 갈래 없음(기발행 0·기본자본형 신규 0)이면 `binding_limit_eok` = SCR x 10%(예전 15%). 33사 `tier1_hybrid_limit_eok` 변경(한화생명 22,517 -> 15,011 · 하나손해 702 -> 468), `utilization_pct` 47사 전부 불변(`z4_tier1_limit_before_after_47.csv`). 공개 시트 `기본자본소진율` 은 이 필드를 읽지 않아 셀 변동 0. 시험: 독립 사례 + 47사 배포본(결속 갈래별 한도) 단정 신설.
- **요청 8 (owner 최종 규칙 2026-10-12 밤).** 보완자본 분자의 기발행 차감액 = 채권원장의 2022-12-31 이전 발행 잔액(신종·후순위 각각), 인쇄 항목 53/54 는 `grandfathered_*_printed_eok` 로만 보존(맹목 min·증거 판정·회사별 예외 없음). 분자 = 항목 47(적용 전) - 항목 49 - 원장 신종 - 원장 후순위, R0~R5 이름은 발행사 인쇄 관행 표지로 유지(DB생명·미래에셋 특례 흡수, 숫자 불변·이름 R3). 21사 변동(`z3_tier2_before_after_47.csv`): 메리츠 0.2 -> 30.8 · 흥국생명 10.6 -> 37.0 · 한화생명 70.5 -> 74.8 · 푸본 86.6 -> 73.1 · 농협생명 18.8 -> 4.8 · 아이엠라이프 49.5 -> 56.9 · 현대해상 70.5 -> 64.2 · DB손해 38.9 -> 36.0 · 롯데 53.5 -> 50.1 · 농협손해 103.9 -> 102.8 · 악사/KB라이프 -> 0.0 외. 화면 필드: `grandfathered_subordinated_eok`(K-ICS.html 「경과조치 기발행 후순위 X억원」)가 차감액(원장)을 싣는다 - HTML 변경 불필요. tier1·forward 값 불변.
  보고 전용(변경 없음): 15% 갈래 항목 53 인쇄값이 원장 2022년 이전 신종보다 큰 회사는 아이엠라이프 1곳(+1,517 = 원장 밖 전환우선주, 등재부엔 있음)뿐, 나머지 10곳은 인쇄 <= 원장(`z6_item53_vs_ledger_report_only.txt`).
- **요청 8 정정 (coordinator 2026-10-13, 커밋 `10b45d71`).** 원장 차감액에서 **콜일이 지났는데 상환 안 한 채권(`past_call_outstanding`=true)을 제외**했다(자본증권 실효 만기 = 콜일; 발행사는 DB손해 제1-2회·현대해상 2-2·농협생명 공모채 1-2회를 기발행 줄에 넣지 않음). 제외 7건: DB손해 1,700 · 롯데 08차 899 · 흥국화재 제1회 신종 920 · 현대해상 2,330 · 농협생명 2,800 · 엠지(예별) 680 · 악사 JPY 459(원장 플래그만, PDF 안 읽음). `load_ledger` 가 `data/bonds` 원본에서 직접 낸다. 바뀐 회사(직전 표 대비): 현대해상 64.2 -> 70.5 · DB손해 36.0 -> 38.9(메모 값으로 복귀) · 농협생명 4.8 -> 21.1(감사 예측치와 같음) · 롯데 50.1 -> 58.6(2,289 - 899 = 1,391) · 흥국화재 45.2 -> 53.3 · 악사 0.0 -> 29.2 · 예별은 R0 라 0 유지(`z9_pastcall_vs_prev.txt`). 흥국화재·악사는 발행사 인쇄값이 그 콜 경과 채권을 포함한 사례라 발행사 처리와 반대로 움직인다(owner 확인). 변동 회사 수 21 -> 19. 시험: 정확값 박제 + 합성 원장 변이시험(`test_past_call_exclusion_is_load_bearing`). 정의 메모 `definition_memo.md` §2 에 past-call 제외 문서화.
- **요청 8 재정정 (validation 티켓 `20261013T0205Z`, 커밋 `7e6e55d0`).** 제외 판정을 원장 플래그가 아니라 **첫 콜일 <= 분자 기준일(분기 말일)** 로 바꿨다(`legacy_stock`·`quarter_end`; 플래그는 보조로 유지, `compute_quarter` 가 분기 말일로 재계산). 플래그는 채권 행마다 그 행의 as_of 로 계산돼 메리츠 제7회 2,100억(콜 2026-04-12, 행 as_of 2026-06-30)·아이엠라이프 DGB 사모 500(콜 2026-05-07)·KB라이프 제1회 1,299.7(콜 2026-05-31, 둘 다 2025-12-31 행)이 false 로 남아 차감에 들어갔다. 변동 3사뿐(`z11_calldate_vs_flag_only.txt`): 메리츠 30.8 -> 37.5 · 아이엠라이프 56.9 -> 70.4 · KB라이프 0.0 -> 0.8, 그 밖 변동 0. 필드 이름 불변이라 HTML 변경 없음. 시험: 정확값 + 합성 원장 변이시험(날짜 판정 삭제·표지 삭제 두 변이) + 독립 재계산도 날짜 규칙으로 갱신.
- **재동기화.** `insurequant_master_tables.xlsx` 시트 4개(`보완자본소진율` 178행 교체 · `자본성증권발행현황` 4칸+1행 · `자본비율전망` 55칸 · `기본자본소진율` 0)를 `sync_master_xlsx_sheet.py` 로 시트별 반영, `보완자본소진율` 비고/`경과조치 인정 후순위·신종(레거시)` 비고에 원장 기준을 적음. 증빙 패널 `x1_panel`·`x2` 는 parser 의 최신 전기 칸 반영(`74a415bf`)으로 낡아 재생성(판정 불변). 공개본 `public_exports/` 재생성 커밋 별도.

## 2026-10-12 — 발행사 처리 기준 재분류 · 증권별 X 검정 · 보완자본 재분류 칸 정정 (티켓 `20261012T2115Z`, 커밋 `dbbffcb5` + 공개본 커밋, 커밋만 · push 보류)

owner 「회사에서 그렇게 분류했으면 회사 분류를 따르는 게 맞다」: 등재부 `type` 은 발행사가 K-ICS 공시에서 실제로 처리한 형을 따른다(발행조건·기사 해석은 `terms_note` 에만). 정의(분자·분모)·`kics_disclosure.json`·HTML 불변. 증빙 `data/_derived/capsec_reinstate_20261012/x1~x6`.

- **검정 방법**(`x2_per_security_x_test.py`): X = 항목13 - 항목49. 발행 분기 X 가 발행액만큼 오르면 보완자본형, 한도(SCR x 10%) 초과분만 오르면 기본자본형. 오차는 직전 비이벤트 3개 분기 |dX| 최대의 1.5배(하한 30억). 첫 공시 분기가 발행 분기인 증권은 수준 시험(나머지 항목의 안정성)과 필요조건(X >= 발행액)을 쓴다. 총액 비교(13-49 >= 차감액)는 증명이 아니라 쓰지 않았다.
- **결과 17건**: 변경 2건 - 하나생명 제1회(X 가 13분기 중 12분기 발행액 1,799 보다 작아 보완자본형이 산술상 불가, 기본자본형이면 나머지 29~502 로 안정), 교보 2024-11(발행 분기 X +89, 보완자본형이면 +5,983) -> tier1. 보완자본형 확인 12건 - 흥국화재 제5회(X +1,989/1,993) · 농협손해(+4,848/4,500) · 하나손해 2건(+974/1,000 · +992/999) · 한화생명 4건(2024.3Q 두 건은 합산 시험, 한 건씩 뒤집어도 불일치; 신종8 +5,972/6,000; 외화 +13,176/13,819) · KDB생명 2건(X = 항목 6 이 13분기 오차 0.5 이내) · 교보 2023(+4,985/4,985) · 코리안리 제5회(수준 시험: 6분기 0.3 이내, 단 기발행+제5회에 15% 한도를 함께 씌우는 읽기와는 구분 불가). **판정 불가 3건(현 분류 유지, 추측 안 함)** - 푸본 2023-02 600(첫 공시 분기가 발행 분기, 나머지 항목 ±400 흔들림) · 농협생명 제5회(같은 이유, 한도가 발행액보다 항상 커서 한도 변동으로도 못 가름) · 코리안리 제6회(기발행 상환과 겹치고 항목 6 변동 없는 X +1,7xx·+3,456 이 따로 들어옴).
- **소진율**: `apply_disclosure_utilization.py --quarter 2026.2Q` - tier1 은 하나생명 0.0 -> 238.2 만 변경(분자 1,799 / SCR x 10% 755.4), 교보 70.1 불변(엄격 쪽 0 -> 56.8), tier2 47사 전부 불변. 하나생명 한도 초과분 1,043.6 은 보완자본 한도 적용 전(항목 47 = 1,275.6)에 이미 들어 있다(81.8%, 나머지 232 는 다른 재분류 항목).
- **`tier1_overflow_into_tier2_eok` 정정**: 이 칸(공개 `보완자본소진율` 시트 「기본자본 한도초과분의 보완자본 재분류」)은 옛 `wire_capital_securities_to_utilization.py`(채권원장 발행액 - SCR x 15%, 하나생명 1,798.8 - 1,133.1 = 665.7)가 한 번 쓰고 갱신이 끊겨 있었다. `apply_tier2` 가 tier1 의 한도 초과액(공시 항목 6 + 등재부 분류)을 같은 값으로 쓰도록 바꿔 47사 일치(시험 추가). 바뀐 8사: 농협손해 2,483.6->0 · 하나손해 298.5->0 · KDB생명 80.7->0 · 한화생명 8,302.2->0 · 코리안리 1,297.1->0(전부 보완자본형이라 한도 초과 재분류가 아님) · 아이엠라이프 0->1,353.9 · DB손보 225.2->5,942.1 · 하나생명 665.7->1,043.6. 시트 비고에 정의를 적었고, 기본자본 소진율 시트의 「스텝업 등 기본자본요건을 못 맞춘」 문구는 「발행사가 경영공시에서 보완자본으로 처리한」 으로 바꿨다(발행조건 해석을 공개 문장에 쓰지 않는다).
- **Forward Outlook**: 등재부 type 이 발행사 처리와 같아져 기본자본 경로는 47사 전 연도 불변(하나생명·교보는 종전에도 발행사 처리 기준으로 계산), 총자본 경로 바이트 동일(`x5_forward_before_after.txt`). **사라진 필드**: 회사 행 `baseline_basis_flag`·`baseline_basis_note`, 연도 행 `basic_capital_by_type_eok`·`basic_ratio_by_type_pct`, `hybrid_classification[].issuer_type`(어긋난 증권이 있을 때만 다시 나타난다). 값이 바뀐 필드: `hybrid_classification[].type`(하나생명·교보 2건 tier2 -> tier1), `outstanding_hybrid_by_type_eok`(두 회사). K-ICS.html 은 `row.baseline_basis_flag && ...` 로 읽어 필드가 없으면 그냥 안 그린다. 손계산 9사 불일치 0(`x6_handcheck.txt`).
- **재공개**: `export_public_sheets.py` - `기본자본소진율`·`보완자본소진율` 시트와 manifest 만 변경, `자본비율전망` 불변. xlsx 시트 `기본자본소진율`(값 4칸, 비고 교체 48행)·`보완자본소진율`(비고 교체 47행)을 `sync_master_xlsx_sheet.py` 로, `check_master_xlsx_drift` 0.
- **되돌리는 방법**: 등재부는 커밋 `dbbffcb5` 의 `data/bonds/capital_tier_registry.json` 두 줄(하나생명·교보)을 되돌리고 `apply_disclosure_utilization.py` -> `forward_capital_simulation.py` 순으로 재실행. 오버플로 칸만 되돌리려면 `apply_tier2` 의 `tier1_overflow_into_tier2_eok` 한 줄.
- 시험: `tests/unit` 259 통과(하나생명 기대값 0.0 -> 238.2 는 위 재분류 때문이며 느슨하게 푼 것이 아니다; 등재부-검정 연결·패널-마스터 일치·오버플로 일치·필드 부재 시험 추가) · `test_private_deploy` 14 · `test_push_gate_wiring` 66(1 skip) · `test_deploy_assets` 12 · `test_rule_coverage_manifest` 102. 게이트 `validate_data_contract` RED=0 · `validate_live_artifacts` RED=0(baselined 25) · `check_master_xlsx_drift` 0.

## 2026-10-12 — 소진율 도넛 · Forward Outlook 재공개 (티켓 `20261012T2030Z`, 커밋 `ef62969`·`2729a53`, 커밋만 · push 보류)

owner 「분류 근거가 확정돼 소진율 도넛과 Forward Outlook 을 다시 살린다」, 정의(계정 단위 · 해설서 p13 각주 ⑴)는 불변. 증빙 `data/_derived/capsec_reinstate_20261012/`.

- **등재부** `data/bonds/capital_tier_registry.json`: tier2 확정 4사(하나생명 제1회 1,799 · 푸본 2023-02 600 · 농협생명 제5회 2,500 · 코리안리 제5/6회 2,500+2,300) = 증권 6건, `type_unconfirmed` 5건 해제(푸본의 채권원장에 없는 50억만 미확정으로 남음). 교보 2024-11 6,000억은 `type`=tier2(발행조건 스텝업) + 새 필드 `issuer_type`=tier1(발행사 K-ICS 표 처리), 하나생명은 `type`=tier2 + `issuer_type`=tier1. DB손보 5건·하나손해 2건은 분류 불변, 근거 문구에 owner 확정 추가. 새 필드 `issuer_type` 은 `type` 과 다를 때만 적는다(시험이 하나생명·교보 두 건임을 강제).
- **소진율** (`apply_disclosure_utilization.py --quarter 2026.2Q`): tier1 4사만 변경 - 하나생명 238.2->0.0 · 코리안리 205.1->94.0 · 농협생명 72.7->48.5 · 푸본 42.1->17.3. 교보 70.1(결속 쪽이 기발행이라 불변)·tier2 47사 불변. 전후 47사 표 `utilization_before_after_47.csv`, 분자 자기검산 47사 불일치 0(`r7_numerator_selfcheck.txt`).
- **Forward Outlook** (`forward_capital_simulation.py`): 신종 기본자본 기여 = legacy_tfi `min(잔액, SCR_y x 15%)` + tier1 `min(잔액, SCR_y x 10%)`, tier2(보완자본형)는 0 -> 콜은 총자본에서만 빠진다. 한도는 매 연말 SCR 로 다시 계산하므로 「한도 초과로 재분류된 부분이 먼저, 그다음 기본자본」이 자동으로 나온다. 계층 정본은 `issuer_type`(없으면 `type`): 기준시점 기본자본이 회사 공시값이라 콜 차감 계정은 발행사 실제 처리를 따른다. **총자본(지급여력비율) 경로: 47사 전 연도 바이트 동일**(`forward_before_after_summary.txt`: total-path diffs 0, confidence diffs 0). 기본자본비율 경로가 바뀐 회사 11곳. 한화생명 56.76 -> 56.76 -> 56.76 -> 54.97(2029) -> 41.76(2030) 이던 것이 2026~2030 내내 56.76 (신종 4건 전부 보완자본형). 표 `forward_before_after_47.csv`, 손계산(한화생명·DB손보·하나손해·하나생명·교보·메리츠) 불일치 0(`handcheck.txt`).
- **새 필드(additive, 기존 이름·뜻 불변)**: 회사 행 `baseline_basis_flag`(하나생명·교보만 true) · `baseline_basis_note`(기본자본 경로를 발행사 처리 기준으로 계산했고 우리 분류 기준 경로는 `basic_ratio_by_type_pct` 라는 한 줄) · `type_unconfirmed` · `outstanding_hybrid_by_type_eok` · `hybrid_classification[]`(증권별 type/issuer_type/출처). 연도 행 `hybrid_legacy_remaining_eok` · `hybrid_tier1type_remaining_eok` · `hybrid_tier2type_remaining_eok` · `hybrid_limit_tier1type_eok`(SCR x 10%) · `basic_capital_by_type_eok` · `basic_ratio_by_type_pct`(어긋난 회사만) · `basic_ratio_if_tier2_type_pct`(미확정 증권이 있는 회사만). 기존 `hybrid_tier1_eok` = 기본자본 인정분 합, `hybrid_tier2_overflow_eok` = 두 한도 초과 재분류분 합, `hybrid_limit_eok` = SCR x 15% 그대로.
- **재공개**: `export_public_sheets.PRIVATE_SHEETS`·`PRIVATE_ROOT_JSONS`·`android_push_and_deploy.sh PRIVATE_PATHS` 를 비움(메커니즘·시험은 합성 목록 주입으로 유지). main 이 비공개 배포로 6개 경로를 이미 지웠으므로 `NEW_FILES` 에 `kics_tier1_utilization.json` `kics_tier2_utilization.json` `kics_forward_capital.json` `public_exports/{기본자본소진율,보완자본소진율,자본비율전망}.json` 추가. `public_exports` 3시트 신규 + manifest, 다른 13시트 바이트 동일. xlsx 시트 `기본자본소진율`(10칸·6행 교체)·`자본비율전망`(127칸·3행 교체)은 `sync_master_xlsx_sheet.py` 로, 열 구성 불변, `check_master_xlsx_drift` 드리프트 0.
- **되돌리는 방법**: `PRIVATE_SHEETS = ("기본자본소진율", "보완자본소진율", "자본비율전망")` · `PRIVATE_ROOT_JSONS = (3개 파일)` 복원 + 배포 스크립트 `PRIVATE_PATHS` 에 같은 6개 경로 복원(+ NEW_FILES 에서 6개 제거) + exporter 재실행. 분류만 되돌리려면 registry 커밋 `ef62969` 의 해당 줄을 되돌리고 `apply_disclosure_utilization.py` -> `forward_capital_simulation.py` 순으로 재실행.
- **미결/불일치 보고**: (a) census 최종본 `census_securities_final.csv`(20:02 생성, 작업 중간에 도착)를 등재부와 대조했다(`vs_final_census.txt`): 43건 중 같음 37, 「다름」 6건은 전부 이 라운드 이전 등재부 기준이고 최종본 type 이 지금 등재부(tier2)와 일치한다 - 교보 2024-11(스텝업, 발행사 표 상충 병기)·푸본 600·하나생명 제1회·농협생명 제5회·코리안리 제5/6회. DB손보 5건 tier1·하나손해 2건 tier2 도 최종본과 같아 등재부 추가 변경 없음. (b) 하나생명·교보는 발행사 처리와 분류가 달라 `baseline_basis_flag`. (c) 경과조치 기발행분 15% 는 2032 까지라 전망 범위(2026~2030) 안이다 - 2032 이후 처리는 범위 밖이라 모델에 넣지 않았다. (d) 한도 분모는 종전대로 보간한 SCR_y (규정상 Ⅵ.1.라 경과조치 적용 전 총요구자본과의 차이는 종전 모델과 같다). (e) 하나손해 2026-06 신규 신종(약 1,000억)은 채권원장 미등재라 콜 차감에 안 들어간다(콜 2031 이후라 범위 밖).
- 시험: `tests/unit/test_capital_utilization_rules.py`(재분류 이유로 값 4개 갱신 + 변이 3건 추가) · 신규 `tests/unit/test_forward_capital_tiers.py` 13건(한도 분리·보완자본형 기본자본 불변·총자본 불변·종전식 재현·issuer_type 플래그·미확정 대체 경로·한도 비율 변이·유형 뒤집기 변이·배포본 == 모델) · `test_private_deploy` 14 · `test_push_gate_wiring` 63(1 skip) · `test_deploy_assets` 12 · `test_rule_coverage_manifest` 102. 게이트 `validate_data_contract` RED=0 · `validate_live_artifacts` RED=0(baselined 25) · `check_master_xlsx_drift` 0.

## 2026-10-12 — 타임라인 JSON 읽는 검사기 선언 + 죽은 선언 정리 (티켓 `20261012T1945Z`, 커밋만 · push 보류)

- 원인: owner 가 작업 브랜치를 배포하자 라이브 `K-ICS.html` 이 `kics_capital_securities_timeline.json` 을 fetch 하는데 `tests/test_push_gate_wiring.py::LIVE_ARTIFACT_READERS` 에 그 파일의 선언이 없었다(`test_every_live_fetched_artifact_has_a_declared_reader`). 같은 시험의 ghost 검사도 실패: `kics_forward_capital`·`kics_tier1_utilization`·`kics_tier2_utilization` 은 비공개 3시트가 돼 화면이 더는 fetch 하지 않는데(원격 main HTML 도 0건) 선언만 남아 있었다. designer 가 말한 「나머지 1건」은 이것이다(마스터 시트 요구 시험 `test_every_live_fetched_artifact_lands_in_a_master_sheet` 는 `PANEL_DERIVED_FROM` 선언이 없어 같이 걸렸다).
- 검사기: `scripts/validate_live_artifacts.py::check_capsec_timeline`(게이트 check 8) - ① 구조(`securities[코드][]`, `tier`·`issue_date`·`face_eok`·`outstanding_eok` 필수·형식) ② 허용 필드 밖의 키(인정액·한도·분류 계열 포함) 금지 ③ 회사별 건수·`face_eok` 합이 `data/bonds/capital_securities_fy2026h1.json` 에서 독립 파생한 값과 일치(회사 census 포함). 룰 id `CAPTL_STRUCTURE`·`CAPTL_EXTRA_FIELD`·`CAPTL_SOURCE_MISMATCH`. 실측 배포본: 26사 125건, RED 0.
- 선언: `LIVE_ARTIFACT_READERS["kics_capital_securities_timeline.json"] = ["validate_live_artifacts"]`, `PANEL_DERIVED_FROM[...] = "kics_capital_securities.json"`(`자본성증권발행현황` 시트. 실측 타임라인 125건 중 122건이 시트와 (회사,발행일,권면) 일치, 3건 타임라인 전용, 시트 전용 1건은 발행일 없음). 죽은 선언 3개 삭제(파일 자체는 검사기가 계속 읽는다).
- 변이시험: `tests/test_rule_coverage_manifest.py` 의 `test_capsec_timeline_gate_*` 3개(정상 통과 · 변이 11종 + 원천 변조 각 룰이 잡힘 · 배포본 통과).
- 시험: `test_push_gate_wiring` 63 passed 1 skipped(기존 skip) · `test_deploy_assets` 12 · `test_prepush_scope` 65 · `test_rule_coverage_manifest` 102 · `unit/test_capital_securities_timeline` 15 passed. 게이트 `validate_live_artifacts` RED=0.
- 놓친 이유: 「새 fetch 파일 → 선언」 시험은 `origin/main` 의 HTML 만 보는 구조라 배포 후에야 걸린다. 의견: 같은 시험의 fetch 목록을 `origin/main ∪ 작업트리 HTML` 로 넓혀 gap 검사도 배포 전(작업 브랜치 push 훅)에 걸 수 있다. `_worktree_fetches()` 가 이미 있어 한 줄 수준이고, 부작용은 작업 브랜치에 임시로 붙인 fetch 도 선언을 요구받는다는 것뿐이다(구현은 별도).

## 2026-10-12 — 비공개 3시트 · 자본성증권 공개 열 제한 · 뮌헨/스위스리 재동기화 (티켓 `20261012T1420Z`·`1440Z`, 커밋만 · push 보류)

owner 지시 「내린 시트들은 비공개로 돌리고」 / 「3 승인」. 저장소의 마스터 JSON·마스터 xlsx 시트·`output/` 은 그대로, 공개 스냅샷과 main(라이브)에서만 내렸다.

- **비공개 시트**: `export_public_sheets.PRIVATE_SHEETS`(기본자본소진율·보완자본소진율·자본비율전망)는 스냅샷을 만들지 않고 manifest 에 싣지 않으며 옛 파일이 있으면 지운다. `PUBLIC_MASTERS`(= MASTERS - 비공개 3)가 게이트의 검사 대상이다. 새 룰 `PUBLIC_EXPORT_PRIVATE_SHEET_PRESENT`(비공개 시트 파일이 있으면 RED).
- **main 에서 지우기**: `scripts/android_push_and_deploy.sh` 의 `PRIVATE_PATHS`(공개 스냅샷 3 + 루트 `kics_tier1_utilization.json`·`kics_tier2_utilization.json`·`kics_forward_capital.json`)는 갱신 대상에서 빠지고 main 에 있으면 배포 커밋에서 `git rm`. tier1 은 designer `1624aba`(타임라인 JSON 계산, tier1 fetch 제거) 뒤에 넣었다. 목록 일치는 `tests/test_private_deploy.py` 가 exporter `private_paths()` 와 대조한다.
- **자본성증권발행현황 공개본**: `_SHEET_DROP_COLS` 로 기본자본인정액_억·보완자본인정액_억·기본자본한도_억·SCR_억·보완자본인정율·경과조치·경과조치종료일 제외(경과조치는 발행일로 우리가 붙인 구분이라 같이 뺐다). 남은 열: 회사명·구분·종류·발행일·콜만기도래일·법정만기일·콜근거·액면가_억·잔액_억·공시분기·잔액기준일·출처·비고. 게이트는 시트별 제외 열(`drop_cols(sheet)`)로 대조한다(느슨하게 풀지 않고 제외 열만 뺀 기대값과 셀 단위 일치).
- **재동기화**: 뮌헨 KR1101 2026.2Q +3행(`33635d1`) -> xlsx `K-ICS공시` 30008->30011, 스위스리 KR1102 2026.1Q +8행(`4147fc1`) -> xlsx `보험계약부채` 6335->6343. `build_master_xlsx._ilp_basis_note` 가 provenance `how=derived_sum_of_rows` 를 읽어 기준표시 「계산값(전 행 합)」 + 비고(인쇄 합계가 Indirect-Par 행을 뺀 값이라 전 행을 더함)를 붙인다. `csm_combo` 패널은 KR1102 2026.1Q 노드 1개(+18 슬롯)와 `meta.lic_recon` 문구만 바뀌었다.
- **되돌리기**: `PRIVATE_SHEETS`/`PRIVATE_ROOT_JSONS` 와 `PRIVATE_PATHS` 에서 경로 제거 + `download-survey.js` 주석 해제 + exporter 재실행. 공개 열 복원은 `_SHEET_DROP_COLS` 에서 열 제거 후 재실행.
- **증빙**: `data/_derived/private_sheets_20261012/`(`proof_changes.txt` = HEAD 대비 공개본 변화, `panel_csm_combo_diff.txt`).

---

## 2026-10-12 — 최종 재동기화 (push 직전 정합, 티켓 `20261012T1330Z`, 커밋만 · push 보류)

오늘 바뀐 마스터(재보사 손해율 세그먼트 `268002b`, 재보사 PL 7칸 복원·처브 BS 20/ILP 14-15·분할표 상각 `3bf1690`, K-ICS 퍼시픽 +16행·악사 4칸 `acd351a`)에 xlsx·공개본·패널을 맞췄다.

- **패널**: `viz_build_persistency_lossratio_panels.py` -> `panel_loss_ratio.json` 41노드(재보사 KR1101~1107 의 세그먼트가 `생명보험`/`장기손해보험` 으로 나뉘고 옛 `손해보험`·빈 구분 노드 삭제, `--check` OK), `viz_build_csm_combo_panel.py` 21노드(처브 KR0100 만, 포트폴리오 부채열), `viz_build_compare_panel.py` 2칸(악사 K-ICS 2024.3Q 286.4->286.5, KR1101 투자손익 null->0). ifrs17 viz 4패널·`csm_waterfall` 은 재빌드해도 바이트 동일. 증빙 `data/_derived/final_resync_20261012/panel_*.txt`.
- **xlsx**(`sync_master_xlsx_sheet.py` 시트별, 백업 `.bak_20261012_final_pre`): `17BS` 6칸(처브 보험계약부채 K-IFRS 기준 값->값), `CSM상각` 18칸(메트라이프·BNP·AIA·처브 2025.4Q 9·10년차 빈칸->값 8, 한화생명 분할표 정정 10), `손익분해PL` +7행·1칸(`값_당분기`), `보험계약부채` 18칸(처브 값->값), `K-ICS공시` +16행(퍼시픽 2025.3Q·2026.2Q 47~54)·4칸(악사 2024.3Q). 삭제 0, 나머지 12시트 값 SHA 동일(`xlsx_invariance.txt`), `요약` 은 행수 칸만 다름.
- **공개본** `export_public_sheets.py`: 5시트 + `manifest.json`(`build_id` `538cbe7`). 임시로 목록에서 내린 3시트 파일은 그대로 둠.
- **게이트**: `check_master_xlsx_drift` RED 7 -> 0, `validate_data_contract` RED 0(YELLOW 152), `validate_live_artifacts` RED 0(baselined 25), `validate_master_tables --no-build` 실행(exit 2 는 골든이 고정한 값), 골든 3종(master_tables·ifrs17 panels·csm_waterfall) passed, `test_deploy_assets`+`test_push_gate_wiring`+`test_prepush_scope` 142 passed.
- **미반영(의도)**: `downstream_kpis.json`(213칸 어긋남, 옛 `cf66dce` 미반영분이라 이번 범위 밖·HTML 무참조), `viz_build_nb_csm_ratio.py`(IR 원문 입력).

## 2026-10-12 — `kics_capital_securities_timeline.json` 신설 (티켓 `20261012T1210Z`, owner 정정으로 채권 단위 발행 내역으로 축소, 커밋만 · push 보류)

K-ICS 「자본성증권 발행현황」 누적 막대(발행일 기준, 아래 신종자본증권 + 위 후순위채)의 원천. owner 지시(2026-10-12): 시점별 잔액을 DART 에서 새로 뽑지 않고 이미 있는 채권 단위 자료만 쓴다(중간에 만들던 시점별 추출기는 폐기).
- 파일 `kics_capital_securities_timeline.json`(루트, 배포 keep-list 등재: `android_push_and_deploy.sh` NEW_FILES · 발행 프롬프트 §1 표), 빌더 `scripts/build_capital_securities_timeline.py`, 입력 `data/bonds/capital_securities_fy2026h1.json`(`securities_summary` 와 같은 입력 = 회사별 최신 기준일 자료).
- 명세: `{"generated":"YYYY-MM-DD","unit":"억원","source":"...","securities":{"<회사코드>":[{"tier":"hybrid"|"subordinated","issue_date":"YYYY-MM-DD","call_date":"YYYY-MM-DD"|null,"coupon_pct":number|null,"face_eok":number,"outstanding_eok":number,"as_of":"YYYY-MM-DD"}]}}`. 회사코드는 JSON 키로만. 회사 안에서 발행일 순. 억원 = 백만원/100, 소수 둘째 자리. `face_eok` = 발행 권면, `outstanding_eok` = `as_of` 시점 잔액(상환돼 0 이어도 발행 내역이라 싣는다). `as_of` 는 채권별 기준일(2025-12-31 또는 2026-06-30). tier 는 원천 그대로이고 기본자본/보완자본 판단·인정액 필드는 없다.
- 범위: 26사·125건(신종 45·후순위 80). 원천 127건 중 2건 제외(동양생명 2020 신종 - 권면 없음·잔액 0, 악사손해 JPY 후순위 - 발행일 없음; 추측하지 않는다). **원천에 한 번도 오르지 않은 과거 상환 증권은 없다**(원천이 2025-12-31·2026-06-30 잔액 기준 목록이라 그 전에 상환된 채권은 발행 막대에서 빠진다 - 과거 연도의 발행량이 낮게 보일 수 있다).
- 시험 `tests/unit/test_capital_securities_timeline.py` 15 passed(단위 변환 · 상환 0 포함 · 발행일/권면 없음 제외 · 정렬 · 변이 3종 검출 · 배포본 = 원천 재생성 · 분류 필드 없음 · 한화생명 신종 4건 손계산).

## 2026-10-12 — `보험금예실차비율` xlsx 시트·공개 스냅샷 신설 (티켓 `20261012T1130Z` 3번, 커밋만, push 보류)

owner 승인 「나머지는 다 승인」(스키마 변경, `TODO.md` ㉓). 소스 `data/loss_ratio/claims_ae_ratio.json`(44사, 162행). 빌더 `scripts/build_master_xlsx.py` 의 `MASTERS` 에 항목 1개 + `FLATTEN`(`_flatten_claims_ae_ratio`), `scripts/export_public_sheets.py` 의 `MASTERS` 1개.
- 열(13): 원보험사코드 · 원수사명 · 티커 · 생손보여부 · 공시분기 · 기준연도 · 사업구분(코리안리 공동재보험 등 6행만) · 예상손해율 · 실제손해율 · 예실차비율 · 단위 · 출처쪽(PDF 쪽 번호) · 플래그(영문 코드는 한글 문구로: 기준연도 읽은 위치·전치 표·빗금 등, 모르는 코드는 KeyError). 내부 파일 경로·추출방식·원문은 JSON 에만 남긴다. 공개본은 원보험사코드 제외 12열.
- `sync_master_xlsx_sheet.py "보험금예실차비율"` 로 그 시트만 추가(백업 `insurequant_master_tables.xlsx.bak_20261012_ae_sheet`): 162행 x 13열, 마스터와 셀 단위 일치. **다른 17시트 값 해시 동일, 요약 시트만 1행 증가(21→22)** (`data/_derived/ae_sheet_20261012/v1_other_sheets_identity.txt`).
- 공개본 `public_exports/보험금예실차비율.json` 162행 + manifest 항목 1개(`export_public_sheets.py --only`, 다른 시트 파일·항목 불변).
- 선언 갱신: `PUBLIC_EXPORT_SHEETS` 15→16, `MASTER_XLSX_SHEETS` 17→18(`tests/test_rule_coverage_manifest.py`), 공개본 대조 식별열에 `기준연도`·`사업구분` 추가(`validate_live_artifacts._PE_ID_COLS` — 안 하면 74행 중복으로 KEY_AMBIGUOUS), `android_push_and_deploy.sh` NEW_FILES 에 신규 파일 등재, 발행 프롬프트의 공개 파일 수(17개).
- **designer 용 위치**: 시트 이름이 나열된 곳은 `download-survey.js` 의 시트 목록(`SHEETS`, 보험계약부채 다음 줄에 `{ name: "보험금예실차비율", file: "public_exports/보험금예실차비율.json", code: ..., label: ... }` 한 줄 추가가 필요 - 안 하면 사이트 다운로드에 안 보인다). `공시보고서.html` 등 다른 HTML 에는 시트 목록이 없다.
- 게이트: `check_master_xlsx_drift` 새 시트 드리프트 0(전체 RED 5건은 다른 시트 - 17BS·CSM상각·손익분해PL(2)·보험계약부채 - 로 파서 ifrs17 의 미반영 마스터 변경), `validate_live_artifacts` RED 0(공개본 16시트 중 이 시트 포함), `tests/test_rule_coverage_manifest.py` 98 passed·1 failed(=위 다른 시트 드리프트), `test_push_gate_wiring` 65 passed.

## 2026-10-12 — `securities_summary` 필드 신설 (K-ICS 소진율 도넛 밑 신종·후순위 큰 셀용, 커밋만, push 보류)

티켓 `inbox/publishing/20261012T1150Z__orchestrator__MULTI_2026.2Q__capital_securities_summary_fields_for_cells.md`. 산식 `scripts/capital_securities_summary.py`(순수 함수), 쓰는 곳 `scripts/apply_disclosure_utilization.py`(소진율 산출과 같은 경로, 재실행해도 소진율 변경 0건), 입력 `data/bonds/capital_securities_fy2026h1.json`(소진율 분자는 경영공시 항목이지만 발행금리·콜일은 증권 단위 자료에만 있다. 채권원장 `kics_capital_securities.json` 에는 쿠폰이 없다).
- **필드 명세**(`kics_tier1_utilization.json`·`kics_tier2_utilization.json` 47사 행 모두에 같은 값, 기존 필드 변경 없음):
  `securities_summary: { as_of, hybrid, subordinated }` — `as_of` = 분기말(2026-06-30, 콜 도래 판정 기준일). `hybrid`(신종자본증권)·`subordinated`(후순위채)는 **잔액이 남은 증권이 없으면 객체 전체가 null**, 있으면 아래 키:
  - `latest_coupon_pct`: 잔액이 남은 증권 중 발행일이 가장 늦은 증권의 쿠폰(%). 같은 날 여러 건이면 잔액이 큰 쪽. 그 증권의 쿠폰이 원천에 없으면 **null**(이전 증권 값으로 대신하지 않는다). `latest_issue_date`: 그 증권 발행일(툴팁용).
  - `issued_since_2023_eok`: 발행일 >= 2023-01-01 인 증권의 잔액(`outstanding_mn`) 합 / 100, 정수 반올림. 해당 없으면 0.
  - `next_call_date`·`next_call_eok`: `past_call_outstanding`=false 이고 콜일 >= as_of 인 증권 중 가장 이른 콜일과 그날 잔액 합(같은 날 여러 건이면 합). 해당 증권이 없으면 둘 다 null.
  - 추가 필드 2개(명세 밖, 화면이 정직하게 쓰도록): `next_call_estimated`(콜일이 원문 공시가 아니라 발행일+5년 등 추정이면 true, 콜일 없으면 null) · `balance_as_of`(그 tier 잔액 중 가장 오래된 기준일 - 22사는 잔액이 2025-12-31 기준이라 2026-06-30 과 다르다).
- 판정: 47사 x 2 tier = 94칸 중 신종 null 30·후순위 null 23. 발행일 미상 증권(악사손해 후순위 1건)은 최근 발행·2023 이후 합계에서 빠진다(추측 안 함). 흥국화재 후순위의 가장 최근 발행(2026-03-31)은 쿠폰이 원천에 없어 `latest_coupon_pct` null, 콜일도 없어 그 증권은 콜 후보에서 빠진다. 푸본현대 후순위처럼 같은 날 콜이 여러 건이면 합산(3,995억). 증빙 `data/_derived/capital_securities_summary_20261012/s1_judgment_table.{csv,txt}`(채권원장 2023 이후 합계와 94칸 전부 일치 · 배포본 대조 차이 0).
- 한화생명(KR0068) 사람 검산 일치: 신종 최근 = 2025-06-24 외화 6.30%, 2023 이후 합계 30,819억(5,000+6,000+6,000+13,819), 가장 가까운 콜 2029-07-17 5,000억. 후순위 최근 4.45%(2024-12-12), 2023 이후 12,968억(4,988.23+7,979.32), 가장 가까운 콜 2027-02-04 10,720억(발행일+5년 추정이라 `next_call_estimated`=true).
- xlsx: `기본자본소진율`·`보완자본소진율` 시트는 `build_master_xlsx.py` 의 고정 항목 목록(`_TIER1_ITEMS`·`_TIER2_ITEMS`)만 행으로 만들어 이 필드는 **시트·공개본에 실리지 않는다**(항목행 추가는 스키마 변경이라 하지 않았다, 필요하면 owner 결정).
- 시험 `tests/unit/test_capital_securities_summary.py` 20 passed(경계 2022-12-31/2023-01-01 · 콜 경과 · 콜일 동일 다건 · tier 없음 · 쿠폰 없음 · 변이 5종 모두 검출).

## 2026-10-12 — 자본성증권 인정한도 소진율 규정 근거 재정의 반영 (커밋만, push·배포 보류)

티켓 `inbox/publishing/20261012T0800Z__orchestrator__MULTI_2026.2Q__capital_utilization_redefinition_apply.md`(Opus 실행). 정본 `data/_derived/capital_utilization_definition_20261012/definition_memo.md`(owner 결정 ①~⑦ 권고안 채택).
- 산식 `scripts/capital_utilization_rules.py`(신설, 순수 함수): 보완자본 = 항목 47 적용후 열 + 발행사 인쇄 관행 R0~R5(메모 s5 와 같은 계산, 항목 47 스코프는 `kics_json_rules._tier2_i47_scope_map` import) ÷ 항목 14(적용 전) × 50%. 기본자본 = max(기발행 신종 항목 53 ÷ SCR×15%, 기본자본형 신규 ÷ SCR×10%). `apply_disclosure_utilization.py` 가 47사 전부를 이 산식으로 쓴다(교보라이프플래닛의 옛 `no_bonds` 0.0 경로 → null + "경과조치 표 미공시", 스위스리 `numerator_undisclosed` → 0.0).
- 등재부 `data/bonds/capital_tier_registry.json`(신설, 18사 증권별 legacy_tfi/tier1/tier2 + 근거). 미정 4사: 흥국생명 = 기본자본형 확정(2022-12 전환우선주 2,300억 = 티시스 2,000·티캐스트 300 보도, X 실현가능성 검정 7개 분기, 경과조치 표는 496.5 만 이동 → 원칙 10%, 81.4%). 코리안리·농협생명·푸본 = 미확정(공개 자료에 스텝업 조건 없음, 시계열 검정으로 못 가름 `a5`·`a5b`) → 보수적 상한 205.1·72.7·42.1 + `type_unconfirmed`(보완자본형이면 94.0·48.5·17.3).
- 47사 메모 대조 차이 0(`a7_memo_diff.txt`). 전후 `b1_before_after_47.csv`: tier2 23사(한화생명 222.4→70.5, 메리츠 55.4→0.2, 미래에셋 112.4→24.5, 푸본 130.1→86.6, IBK 120.4→76.0, 농협손해 117.7→103.9 등, 교보라이프플래닛 0.0→null, 스위스리 미공시→0.0), tier1 14사(한화생명 136.3→0.0, 하나손해 284.9→0.0, 농협손해 223.2→0.0, KDB 103.2→0.0, 하나생명 158.8→238.2, DB손해 101.1→151.6, 코리안리 230.7→205.1 등).
- 파생물: `kics_forward_capital.json` 은 confidence 가 tier 값을 읽어 같은 인자로 재실행(`20261012T015750Z`) — confidence 109칸만 바뀌고 전망값은 같다, 신뢰도 low→high 5사(신한이지·한화생명·미래에셋·푸본·IBK). `data/bonds/capital_securities_forward_outlook.json`·`capital_securities_utilization_20261Q.json` 은 archive/ 스크립트 산출이라 아무도 읽지 않아 그대로 둠. `kics_capital_securities.json` 은 tier1 의 `scr_eok` 만 읽어 값 의존 없음(그 인정표의 "신종 15% 공유" 정책과 forward 모형의 신종 15% 일괄 가정은 새 정의와 다르다 - 보고만).
- xlsx(`sync_master_xlsx_sheet.py`, 백업 후): 기본자본소진율 값 54칸·비고 188칸, 보완자본소진율 값 47칸·비고 141칸, 자본비율전망 비고 275칸·_diagnostics 605칸(행 수 불변, `c4_xlsx_change_list.csv`). 손해율은 `268002b` 재보사 세그먼트 표준화가 미동기화돼 있던 기존 드리프트 1,520행(값 변경 0)을 같이 맞췄다. 시트 이름·열 불변. 기본자본소진율은 항목명을 그대로 두고 읽는 필드만 바꿨다("기본자본 인정한도(SCR x 15%)" ← `tier1_legacy_limit_eok`, "신종자본증권 인정액" ← `tier1_basic_new_eok`) - 항목명을 규정 표기로 바꾸는 것은 owner 승인 사항.
- 공개본: 3시트 + manifest(`build_id` c3ebcc3), 나머지 13시트 바이트 동일.
- 게이트: data-contract RED 0(YELLOW `T2_UTIL_OVER_100_DISCLOSED` 2 = 농협손해 103.9·동양 105.0, 종전 6), live_artifacts RED 0(공개본 재생성 후), xlsx 드리프트 0, K-ICS 룰 게이트 exit 0(입력 불변). 새 RED 0. tier1 100% 초과(DB손해 151.6·하나생명 238.2·아이엠라이프 221.7·코리안리 205.1 상한)는 tier1 도메인 룰이 없어 RED 가 나지 않는다 - 정당 초과 허용 규칙을 둘지는 validation 판단.
- 시험: `tests/unit/test_capital_utilization_rules.py` 25 passed(훅의 tests/unit 묶음에 들어간다), 코드 변이 3종 모두 검출(`e1_mutation_run.txt`), `test_deploy_assets`+`test_push_gate_wiring` 77 passed·1 skipped.
- **designer 용 새 필드**(기존 필드 이름·구조 유지, 추가만):
  - tier1 행: `utilization_pct`(새 값) · `tier1_hybrid_recognized_eok`/`tier1_hybrid_limit_eok`(결속 쪽 분자/한도 = 숫자 줄 "기본자본 자본증권 X억원 / 인정한도 Y억원") · `binding_leg`(`legacy_15` 기발행 SCR×15% · `basic_10` 기본자본형 신규 SCR×10% · null 자본증권 0) · `tier1_legacy_eok`/`tier1_legacy_limit_eok`/`tier1_legacy_pct` · `tier1_basic_new_eok`/`tier1_basic_new_limit_eok`/`tier1_basic_new_pct` · `tier1_excluded_tier2_type_eok`(보완자본형이라 뺀 금액) · `type_unconfirmed`(bool) · `tier1_pct_if_unconfirmed_tier2`(미확정일 때 범위 아래 끝, 아니면 null) · `type_note`(근거 문장) · `no_capital_securities`(true 면 "발행 없음"). `tier1_hybrid_issued_eok` 는 종전대로 항목 6 전체 - 화면 분자로 쓰지 않는다.
  - tier2 행: `utilization_pct`·`numerator_eok`(새 값, `rule`="NA" 이면 둘 다 null) · `tier2_limit_eok` · `rule`(R0·R1·R2·R3·R4·R5·R-none·NA) · `rule_basis` · `numerator_source` · `reason`(NA 일 때만 "경과조치 표 미공시") · `numerator_tfi_off_eok`/`utilization_pct_tfi_off`(경과조치 종료 시 관점) · `item47_scope` · `rule_flags` · `supplementary_capital_eok`(항목 3) · `lapse_excess_item49_eok`(항목 49) · `no_capital_securities`.
  - 표시(결정 ④): 분자 0 → "0%", `no_capital_securities` 면 "발행 없음" 덧붙임 · `rule`="NA" → 가운데 "—", 캡션 "산출 불가", 툴팁 `reason` · 스위스리는 항목 49 인쇄가 0 이라 보완자본 4,274억 설명은 `reinsurer_basis.note` 참고.
- owner 보고(메모 밖 새 발견): 메리츠·흥국생명은 「(기발행 후순위채무)」 행(항목 54)에 2023년 이후 신규 후순위채가 섞여 있다(메리츠 2024.3Q +6,581 = 2024-08 6,500억 발행, 흥국생명 2025.1Q +2,132·2025.4Q +901 = 2025 발행분, `a2`·`a3`). 메모 R2 대로면 메리츠 0.2%·흥국생명 10.6%, 원장 기발행분만 빼면 30.8%·37.0%(`a11`). 결정 ② 를 두 회사로 넓힐지 owner 결정 대상이라 이번에는 메모 값을 실었다.
- 커밋 `c3ebcc3`(산식·등재부·마스터·xlsx·forward·시험·증거), `00bab2a`(공개본), `bd69673`(문서), `3fe9a53`(배포본 대조 시험이 배포본의 분기를 따라가게). 증거 `data/_derived/capital_utilization_apply_20261012/`.

## 2026-10-12 — 미니 재동기화 2차 (재보사 PL·BS·CSM 재스윕 반영, 커밋만, push·배포 보류)

티켓 `inbox/publishing/20261012T0500Z__orchestrator__MULTI_2023.1Q-2026.2Q__mini_resync_2_reinsurer_resweep.md`. 마스터 JSON 은 읽기만 했다(3727438·57b7d78).
- xlsx 7시트를 시트별로 동기화(`sync_master_xlsx_sheet.py`, 기존 행 삭제 0): 손익분해PL 13,491→13,794(+303행, 값 변경 25칸 = 15행·KR1102/1103/1105 전부 값→값) · 17BS +49 · CSM워터폴 +18 · CSM상각 +15 · 가정민감도 +6 · 보험계약부채 +110 · 신계약CSM배수 +3. 마스터 diff 와 칸 단위로 일치, 다른 10시트 SHA 동일, 요약 시트는 행수 칸만 변경. 드리프트 RED 7→0.
- `NB_CSM_multiple.json` 390→393(재보사 KR1104 2025.4Q·KR1105 2025.4Q·KR1107 2023.4Q, 배수 null). 기존 390행 변경 0.
- 패널: ifrs17 viz 4패널·csm_waterfall 바이트 동일(재보사 상각·민감도는 최신 분기만 싣는데 신규 행이 모두 2023.4Q). csm_combo 52노드·compare 137리프 변경, 전부 재보사(다른 회사 0). compare 의 손해율 항목은 직전 라운드 재보사 행을 처음 반영한 것.
- `public_exports/` 7시트+manifest 재생성(build_id b4b6a71). 게이트: data-contract RED 102(전부 CONCEPT_MIXED_DISCLOSURE_INTO_DART, MASTER_XLSX_* 0), live_artifacts RED 0·YELLOW 25(baseline), 테스트 142 passed/1 skipped, viz 골든 2종 통과.
- 커밋 `b4b6a71`(xlsx·NB·패널·증거), `5079688`(public_exports). 상세 `data/_derived/mini_resync_20261012/runlog.md`.


## 2026-10-12 — 재보사 손해율 패널 확장 + 예실차 블록 + xlsx `손해율` 동기화 (커밋만, push·배포 보류)

- `scripts/viz_build_persistency_lossratio_panels.py`: `build_ae()` 추가(읽기 `data/loss_ratio/claims_ae_ratio.json`). 패널 최상위에 `ae` 블록: `ae[회사코드]={n, q:{공시분기:[[기준연도, 사업구분, 예상손해율%, 실제손해율%, 예실차비율%p, [플래그]]]}}` — 값은 마스터 그대로, 공시값 '-'는 null, 플래그는 마스터 `플래그` + `identity_break`/`dash`. `companies` 처리 코드는 바꾸지 않았다(재보사는 마스터에 행이 들어와 자동 편입).
- 패널 전후: 37사→44사(+KR1101~1107), 크기 180,325→206,065 바이트, `meta.quarters` 불변. 기존 37사 `companies` 항목 37/37 바이트 동일, `panel_persistency.json` 바이트 동일, `ae` 162행이 마스터와 불일치 0. `--check` OK.
- xlsx `손해율` 시트: 36,344→38,248행(+1,904, 변경 셀 0, 삭제 0), 나머지 시트 값 동일(sync 사후검증 OK). 백업 `insurequant_master_tables.xlsx.bak_20261012_lossratio`. 예실차·긴 형식 표용 시트는 `MASTERS` 에 없다(신설은 owner 승인 사항, 이번엔 안 만듦).
- 검증: `test_push_gate_wiring` 65 passed·`test_deploy_assets` 12 passed. `check_master_xlsx_drift`/`validate_data_contract` 의 RED 는 전부 다른 레인이 쓰는 중인 마스터(PL_breakdown 3종 112건·MASTER_XLSX_ROW_MISSING 6시트=17BS·가정민감도·CSM워터폴·CSM상각·손익분해PL·보험계약부채)이고 손해율·유지율은 0. `public_exports/` 는 이번에 재생성하지 않았다.
- 원자료·스크립트: `data/_derived/lr_panel_20261012/`.

---

## 2026-10-11 — 미니 재동기화: 라이나 CSM·PL 항목 4·상각 정정 반영 (커밋만, push·배포 보류)

- **xlsx**(`5d320c9`): 손익분해PL +33행·2칸 · CSM워터폴 +54행·15칸 · CSM상각 +50행·172칸 · 신계약CSM배수 +9행·6칸, 삭제 0. 마스터 diff 와 맞고 나머지 13시트는 값 SHA 동일. 드리프트 189 -> 0.
- **NB 마스터**: `build_nb_csm_multiple.py` 재빌드 381 -> 390행. 라이나 +9행·빈칸 3개 채움만 바뀜, 다른 회사 0 변경. `NB_CENSUS_MISSING` 0.
- **패널**: IFRS17 viz 4개·csm_waterfall 바이트 동일(라이나는 DART 행이라 마스터 상각이 패널에 안 간다), csm_combo 라이나 nb_csm 11칸, compare 53칸(라이나 + 재보사 신계약 CSM 18칸).
- **공개 스냅샷**(`812b007`): 4시트 + manifest(`build_id` 5d320c9). 게이트 data-contract RED 0 · live_artifacts RED 8(`INSPL_CENSUS_MISSING` 뿐). 골든 `csm_amort_schedule` 해시만 어긋남(validation `--update` 대기). 상세 `data/disclosure/_meta/mini_resync_runlog_20261011.md`.

## 2026-10-11 — 마감 라운드: xlsx 12시트 동기화 · 공개 스냅샷 · IFRS17 viz 재보사 · 패널 재빌드 · 자본성증권 정리 (커밋만, push·배포 보류)

- **xlsx**(`8848cb8`): 시트 12개를 `sync_master_xlsx_sheet.py` 시트 단위로 동기화(드리프트 434 -> 0, `MASTER_XLSX_*` RED 0). 추가 행 17BS 1,937 · 손익분해PL 517 · 가정민감도 116 · CSM워터폴 108 · CSM상각 180 · K-ICS공시 103 · 금리듀레이션갭 1 · 보험계약부채 114 · 기본자본소진율 80 · 보완자본소진율 112 · 자본비율전망 440, 바뀐 칸 17BS 93 · 손익분해PL 121 · K-ICS공시 107 · 금리민감도 62 · 금리듀레이션갭 39 · 보험계약부채 12. 유지율·손해율·신계약CSM배수·배당·자본성증권발행현황은 행수·값 SHA 동일. 경영지표는 xlsx 시트가 아니다(신설 안 함).
- **공개 스냅샷**(`61babb6`): `export_public_sheets.py` 전체 재실행, 13파일 갱신(3개 무변), manifest `build_id` 6f92fb0 · 15시트. 공개 게이트 발견 0. `android_push_and_deploy.sh` NEW_FILES 는 main 에 없는 새 공개 시트(`보험계약부채.json`)만 필요 — 나머지 둘(금리듀레이션갭·자본성증권발행현황)은 이미 main 에 있어 추가 불필요.
- **IFRS17 viz**(`17dca81`): `viz_build_ifrs17_panels.py` 가 마스터(CSM_amortization·CSM_sensitivity)의 재보사 7곳(마이브라운은 PAA 전용이라 해당 없음)을 DART 산출 뒤에 덧붙인다. 상각 39 -> 46, 민감도 32 -> 39, 기존 행은 JSON 동일(접두 동일), 보험손익·BS 패널은 바이트 동일. 상각은 마스터가 경과차년 1~10만 가져 total·y5_plus·y10plus 를 비운다. 민감도 provenance 사이드카에 DISCLOSURE 셀 7개(`emit_sensitivity_provenance.py`). 로컬 서버에서 8곳 전부 확인: 7곳 상각·민감도 정상, 마이브라운은 「상각 버킷 없음」·「민감도 데이터 미수록」 안내.
- **골든**: `test_viz_ifrs17_panels_golden` 은 상각 +7·민감도 +7 행만큼 달라져 실패(`--update` 안 함, validation 몫 — 그 뒤 `validate_golden_input_fingerprints.py --update`). `test_viz_csm_waterfall_golden` 통과.
- **패널**(`89ecf9a`): csm_combo 40 -> 48사 · 분기 8 -> 14 · `--check` OK, compare 패널 `--check` OK.
- **자본성증권**(`8848cb8`): `compute_tier{1,2}_utilization.py` 회사명을 마스터 원수사명으로(파일명이 K-ICS.html 매칭 규칙에 안 맞을 때만 -> KB라이프 1건 외 46건 동일 증명). `kics_forward_capital.json` 서울보증보험 제외 행(`status: excluded` + `exclusion_reason`), 생성기 `EXCLUDE_PAA` 도 같은 행을 낸다. designer 가 HTML 에서 `exclusion_reason` 을 읽기 전에는 서울보증 문구가 일반 문구가 된다(티켓 `inbox/designer/20261011T1600Z…`).
- **게이트**: `validate_data_contract` RED 22 = 알려진 것뿐. `validate_live_artifacts` RED 26 = 새 두 부류(`NB_CENSUS_MISSING` 18 · `INSPL_CENSUS_MISSING` 8) — 재보사에 NB 배수 행/보험손익 원표가 없어서(원인 구조적, 아래 TODO).
- **NB 재보사 18행**(orchestrator 승인, `1412aaf`·`04ea6c6`): `build_nb_csm_multiple.py` 실행 -> `NB_CSM_multiple.json` 363 -> 381행(git diff 234 추가·0 삭제, 배수 null), 신계약CSM배수 시트 +18행(기존 363 불변)·`public_exports/신계약CSM배수.json` 381행. `NB_CENSUS_MISSING` 18 -> 0, `validate_live_artifacts` RED 26 -> 8(INSPL 8만 남음).
- 상세 `data/disclosure/_meta/final_resync_runlog_20261011.md`.

## 2026-10-11 — 보험계약부채 마스터 시트 · 공개 스냅샷 신설 + KB라이프 소진율 도넛 이름 수정

- **xlsx**: 시트 `보험계약부채` 6,111행 x 13열(마스터 10열 + 단위·기준표시·비고). `sync_master_xlsx_sheet.py` 시트 단위만 — 기존 16시트의 행 수·값 SHA-256 전후 동일, 요약 시트 행 1개 추가. 백업 `insurequant_master_tables.xlsx.bak_20261011_ilp`.
- **공개 스냅샷**: `export_public_sheets.py` MASTERS 15개로, `--only <시트>` 옵션 신설(그 시트 파일 + manifest 항목만). `public_exports/보험계약부채.json` 6,111행, 게이트 발견 0.
- **선언**: `build_master_xlsx.MASTERS`·TEXT_COLS(`기준표시`)·FLATTEN, `MASTER_XLSX_SHEETS` 17, `PUBLIC_EXPORT_SHEETS` 15, `MASTER_SHEET_PENDING` 비움, `android_push_and_deploy.sh` NEW_FILES.
- **KB라이프**: tier1/tier2 배포본·빌더 20262Q 산출물의 `company` 1칸 `케이비라이프생명보험` -> `KB라이프생명`(K-ICS.html 매칭 이름). 컴퓨트 스크립트 재실행 시 옛 이름 부활 위험은 남음.
- 상세 `data/disclosure/_meta/ilp_master_sheet_runlog.md`. designer 필요 변경: `download-survey.js` SHEETS 1줄.

## 2026-10-11 — 재보사 8곳(KR1101~KR1108) 자본비율 Forward Outlook · 자본성증권 소진율 추가

- **원인 = 데이터 부재.** 재보사는 2026-10-09 에 `kics_disclosure.json` 에 들어왔고 `kics_forward_capital.json`(9/23)·`kics_tier{1,2}_utilization.json`(9/1)은 그 전 산출이라 8곳 행이 없었다. 화면은 「forward simulation 데이터 없음」·도넛 「데이터 없음」. 이름 매칭은 문제 아님(드롭다운 value = 원수사명 전체, 약칭은 라벨만).
- 추가만(기존 38/39행 `==` 동일 증명): `capital_securities_fy2026h1.json` 빈 레코드 8개(「스캔 후 무발행」 명시, 안 하면 게이트 `CAPSEC_COVERAGE_REGRESSION` RED) · tier1/tier2 산출+배포본 8행 · forward 빌더를 라이브와 같은 인자(`--baseline-quarter 2026.2Q --tier-quarter 2026.2Q --bonds-source …fy2026h1.json`)로 재실행해 38→46행. 도구 `scripts/add_reinsurers_to_capsec_panels.py`(멱등; `build_capital_securities_fy2026h1.py` 를 다시 돌리면 이것도 다시 돌린다).
- 스코리(요구자본 경과조치 적용사) 190.13%→187.80→185.53→183.31→181.15%(2030), 시작=K-ICS 적용후 공시, 2032 적용전 종점 176.97%(공시 176.99). 나머지 7곳 flat.
- 소진율: 7곳 0%. **스위스리 보완자본만 빈 칸** — 보완자본 4,274억(순자산 재분류분)인데 한도 적용 전·한도 '-' 라 확정 불가("틀린 값을 싣느니 빈 칸"). RGA 는 발행사 표의 한도 적용 전 5,499(=지급여력금액)가 보완자본 0 과 모순이라 0 + 원값 보존.
- 남은 것: xlsx 3시트(기본자본소진율 80행·보완자본소진율 112행·자본비율전망 440행) 동기 + public_exports 재생성(안 하면 `MASTER_XLSX_ROW_MISSING`), KB라이프 tier 행 이름 불일치(기존 행이라 이번엔 안 건드림). runlog `data/disclosure/_meta/reinsurer_forward_capsec_runlog.md`.

---

## 2026-09-23 — main 배포 7차 `22e2471`: K-ICS 금리 민감도 패널 교체 + 금리듀레이션갭 마스터 신설 (owner GO)

- 배포 4파일: `K-ICS.html` · `kics_duration_gap.json`(신규 270행) · `PL_breakdown.json`(라이나생명 2023.4Q 20칸) · `public_exports/manifest.json`(build_id `fa21ec9`). main `a5118f3..22e2471`.
- **새 마스터가 같이 올라가야 하는 배포다.** `K-ICS.html` 이 `kics_duration_gap.json` 을 fetch 하므로 HTML 만 올리면 fail-soft 로 카드가 통째 숨겨진다(에러는 안 나고 조용히 사라진다). keep-list 는 기억이 아니라 각 HTML 의 `fetch(` grep 으로 재파생해 확정했다.
- 게이트 `prepush_check` FULL **gate-clear** (RED=0 · 605 passed · 1,739초).
- **1차 BLOCKED 와 그 처리 (기록 가치 있음).** 골든 입력지문이 `pl_breakdown` 에 CODE_MOVED + OUTPUT_DRIFT 를 냈다 — `build_pl_breakdown.py` 의 `_GOLD_CELL_OVERRIDE` 에 라이나생명 2023.4Q 20칸을 추가했으니 정확한 발화다. 지문이 시킨 대로 **빌더를 실제로 재실행**(`RUN_PL_GOLDEN=1`, 372초)했고 `non_null_values` 10,257 → 10,277 = **정확히 +20** 이 나왔다. 손으로 넣은 칸 수와 일치한다. 이어서 `--update` 로 재생성한 산출을 커밋본과 셀 단위 대조해 **값 다른 셀 0 · 키 추가/삭제 0** 을 확인했다 — 즉 손으로 넣은 20칸을 빌더가 그대로 재현하고, 산출 바이트는 재작성 후에도 안 움직였다. 해시를 손으로 고치지 않고 `--update` 로 재생성(CLAUDE.md 불변식 3), 커밋 `a0f0607`.
- **2차 `offline tests=FAIL` 은 가짜였다.** 내가 게이트에 건 `timeout 900` 이 오프라인 묶음 도중에 잘라서 나온 것이고(EXIT=124), 묶음만 1,739초다. 묶음의 모든 테스트를 개별로 돌려 전부 pass 를 확인한 뒤 제한을 2,700초로 늘려 재실행해 `gate-clear` 를 받았다. **게이트 verdict 를 읽을 때 종료코드 124 를 같이 봐야 한다** — "FAIL" 과 "안 끝났다" 가 같은 문구로 나온다.
- 배포 후 검증: 라이브 4파일을 받아 `git hash-object` 로 커밋 블롭과 대조 **4/4 바이트 일치**. 회사망이 TLS 폐기검사(CRYPT_E_NO_REVOCATION_CHECK)로 막아 `curl -k` 가 필요했다(연결 자체가 막힌 게 아니다 — `http=000` 을 도달불가로 오독하지 말 것). 라이브 렌더 삼성생명 2026.2Q `5.94 / 6.60 / △0.26`.
- 작업 브랜치 `fix/csm-product-segmented-columns` 도 `37e4cd2..a0f0607` push 완료. 이 PC 에서 직접 push 가 됐다(폰 Termux 번들 불필요).
- 남은 것: `금리듀레이션갭.json` public_exports 스냅샷은 안 올렸다 — main 은 원래 `17BS.json`+`manifest.json` 만 싣고 있어 기존 관행을 그대로 뒀다. 다운로드 기능에 새 시트를 노출할지는 별건.

---

## 2026-09-21 — main 배포 6차 `a5118f3`: IFRS17·기타공시 헤더셀렉트+토글 이식 + K-ICS item14 적용후 30칸 원문 정정 (owner GO)

- IFRS17·기타공시 헤더셀렉트+토글 4파일 + K-ICS item14 후 30칸. main 커밋 `a5118f3`(`6741dea..a5118f3`), owner GO 후 push.
1차 시도(같은 날 앞 세션)는 `validate_kics_rate_sensitivity.py` RS2_BASE_ANCHOR RED=2(흥국생명 2025.2Q/4Q
item14 후 역산치)로 BLOCKED. parser-kics 에이전트가 `inbox/parser/20260921T1400Z` §B 를 처리하다 중단됐고
오케스트레이터가 마무리(`32ebfb0`, 상세는 `TODO_parser_kics.md` 18회차): item14 후 30칸 원문 정수 교체(30/30
MD 대조) + 흥국생명 item23 후 5분기 R5 재폐쇄 + 등재부 pin 갱신 + xlsx sync. `deb21e6` public_exports 재생성
(build_id `32ebfb0`). `21594e6` 골든 입력지문 갱신(kics_disclosure.json 을 입력으로 쓰는 4빌더 — 골든 4종 전부
pass, 산출 불변 확인 후 `--update`).
- 작업 트리 `prepush_check.py --full` 2회: 1차 `골든 입력지문=FAIL → BLOCKED`(예상, 위 갱신으로 해소) → 2차
  **gate-clear**(gate RED=0 · K-ICS 룰게이트 clear · 도메인게이트 pass · 골든 입력지문 pass · 배포 JS 런타임 RED=0 ·
  inbox 위반 0 · 605 passed).
- 격리 워크트리 cherry-push 7파일: `common.css` · `K-ICS.html` · `IFRS17.html` · `공시보고서.html` ·
  `kics_disclosure.json` · `public_exports/K-ICS공시.json` · `public_exports/manifest.json`.
- **라이브 확인**: `manifest.json` build_id `32ebfb0` · 라이브 바이트 ↔ HEAD 블롭 **5/5 일치**(한글 파일명은 curl 에
  URL-encoded 경로로 — 안 그러면 GitHub Pages 404 페이지를 받아 오탐) · `kics_disclosure.json` 흥국생명 2025.2Q
  item14 후 18,412 확인.
- 화면 숫자 변경: K-ICS 세부항목 표 적용후 컬럼 item14 30칸(8사, 대부분 ±1억) · 흥국생명 item23 후 5칸(±3~6억).
  item27 후(비율)는 헤드라인 소스라 불변.
- 워크트리 제거, 로컬 `main` = origin/main `a5118f3`. 남은 티켓: `inbox/parser/20260921T1400Z` §A(RS6 31칸) open.

## 2026-09-21 — 6차 배포 시도: IFRS17·기타공시 헤더셀렉트+토글 이식 (BLOCKED, 미배포)

- owner 승인("고치고 나면 main에 배포까지 진행") + designer 커밋 `6a51b7a`(orchestrator 사전검증
  완료: headless Playwright 1400/375px, deploy_assets 11 passed, validate_deployed_js --no-live RED=0)
  4파일(`common.css`·`K-ICS.html`·`IFRS17.html`·`공시보고서.html`)을 격리 워크트리
  `../insurequant-main-deploy`(main 기준)에 cherry-push 준비 — 로컬 커밋(`9ff5093`, push 안 함)까지만
  진행하고 **push 는 하지 않았다**.
- 사유: `scripts/prepush_check.py`(scope=FULL — diff 에 루트 HTML 포함돼 축소 불가) 가
  `validate_kics_rate_sensitivity.py` RS2_BASE_ANCHOR RED=2 로 BLOCKED. 흥국생명보험(KR0071)
  2025.2Q·2025.4Q item14 지급여력기준금액 `값_적용후`(비율역산 18415.27/19354.44)가 원문 헤드라인
  총괄표 인쇄값(18,412/19,350 억원)과 어긋남 — **이번 배포 payload 와 무관한 기존 K-ICS 데이터
  이슈**, 오늘 validation 이 신설한 RS2 적용후 앵커 룰이 처음 잡은 것이고 이미
  `inbox/parser/20260921T1400Z__validation__MULTI_2024.4Q-2025.4Q__ratesens_phase_level_holes.md`
  §B 로 parser 발주돼 있다(open). K-ICS 룰게이트 자체·offline tests 605 passed·골든 입력지문 6종·
  배포JS런타임게이트는 전부 clear/RED=0 — 막은 건 이 도메인게이트 하나.
- CLAUDE.md "RED 1건이라도 있으면 push 안 함, exception 우회 불가" + 이번 발주문의
  "RED 블록되면 --no-verify 쓰지 말고 멈추고 보고" 원칙 그대로 적용.
- 정리: 워크트리 제거, 로컬 `main` ref가 실수로 그 커밋(9ff5093)만큼 origin 보다 앞서 남았던 것을
  `git branch -f main origin/main` 으로 재동기화(6741dea) — stale-local-main 재발 방지.
  세션 도중 별개로 local `main` 이 origin 보다 32 커밋 뒤처져 있던 것도 발견해
  `git fetch origin main:main` 으로 정정(이 stale 참조가 원래 있던 것 — 이번 배포 시도가 만든 게 아님).
- 재현: `TODO_publishing.md` 최상단 항목에 커밋 diff·커밋 메시지 전문 기록 — RED=0 확인 후 워크트리
  재생성부터 push 승인까지 바로 재개 가능.

## 2026-09-21 — 자본비율전망 비고 내부 게이트 진단 문구 분리 (`44ae5fb`/`a61c8b2`/`c130062`, 배포 안 함)

- owner 티켓 `inbox/publishing/20260921T0320Z`: `public_exports/자본비율전망.json` 비고
  660행(추정 610행)에 `compute_confidence()`(`forward_capital_simulation.py`) 내부 게이트
  진단 문자열(필드명 `subordinated_eok`·`tier1_hybrid_issued_eok`·`numerator_eok_fallback`,
  게이트 용어 `advisory, not in overall`)이 그대로 노출.
- **원천 정정**: 실제 조립 지점은 `forward_capital_simulation.py`가 아니라
  `build_master_xlsx.py::_flatten_forward_capital()`이었다 — `kics_forward_capital.json`
  루트 마스터에는 `비고` 필드가 없다(flatten 시점 파생값). `forward_capital_simulation.py`·
  루트 마스터·provenance는 무변경.
- 수정: `비고`에는 `"신뢰도 낮음(발행잔액 vs BS 괴리)"`만 남기고, `reasons` 원문은 신설
  `_diagnostics` 컬럼으로 이동(`44ae5fb`). `export_public_sheets.py`의 `_DROP_COLS`에
  `_diagnostics` 추가 — 공개 다운로드만 제외, 내부 xlsx에는 남음.
- `sync_master_xlsx_sheet.py`에 "기존 시트에 신설 컬럼 추가"(순수 추가일 때만) 케이스를
  새로 지원(`a61c8b2`) — 자본비율전망 시트 sync. `public_exports` 재생성(`c130062`).
- 검증: 총 2090행 불변, jargon 660→0행, `_diagnostics` 제외 키로 재매칭한 '값' 컬럼
  불일치 0, `check_master_xlsx_drift.py` 드리프트 셀 0, `validate_live_artifacts.py`/
  `validate_data_contract.py` RED=0(YELLOW 전부 기존 baseline).
- validation에 재발방지 정규식 검사 제안(구현 안 함): `inbox/validation/20260921T0335Z`.
- 브랜치 `fix/csm-product-segmented-columns`에만 커밋, push 안 함(오케스트레이터/owner 판단 대기).

---

## 2026-09-21 — main 배포 5차 `92159dd`: K-ICS IQP ReferenceError 복구 + 금리민감도 9칸 + 가정민감도 caption (owner 지시 "고치고 나면 main 에 배포까지")

- 사고: 2차 배포 `2dbc4ca` 가 `K-ICS.html` 의 `function IQP()` 정의만 지우고 호출 2곳을 남김. 라이브 금리민감도
  패널 36/39사 ReferenceError, 같은 예외가 부팅 `.then` 을 죽여 `.catch` 가 세부항목 표를 오류 문구로 덮음.
  owner 가 라이나생명 2026.2Q 로 발견. 데이터 수정 0건(parser 원문 대조).
- 배포 5파일: `K-ICS.html` · `kics_rate_sensitivity.json`(789→798) · `data/dart/viz/sensitivity_heatmap.json` ·
  `public_exports/금리민감도.json` · `manifest.json`. 격리 워크트리 `deploy-20260921` cherry-push 후 제거.
- 게이트: 1차 FULL 은 뒷정리 3겹(xlsx 금리민감도 시트·viz_ifrs17_panels 지문·public_exports)으로 BLOCKED →
  `3633b21`·`273a4d8` 로 닫고 2차 FULL gate-clear(593 passed). 신설 §1f 배포 JS 런타임 게이트 RED=0.
- 라이브 검증: 블롭 5/5 일치 · 헤드리스 4사 렌더(세부항목 41행·민감도 7행·pageerror 0) · manifest build_id `3633b21`.
- 4차 배포(`3e9af35`·`8ba15d9`, 09-21 새벽) 기록을 TODO 에 소급 작성. Status 6개 이상 항목은
  `docs/todo_archive_publishing.md` 신설로 바이트 무수정 이동(재조립 cmp 3/3).
- 세션: Opus 5 오케스트레이터 직접(기계적 cherry-copy), 배포 소요 ~5분 + 게이트 2회 ~27분.


## 2026-09-17 — KR0073 2026.1Q 경과조치 후 지급여력비율 정정, main 배포 (owner 발주+승인)

FSS 보도자료(`R26090720.pdf`, 2026.9.17)와 `kics_disclosure.json` 대조(38개사×2분기×전/후 152칸,
항목27)에서 KR0073(교보생명) 2026.1Q 경과조치 후만 진짜 오류(214.23 vs 정답 211.39) 발견 — 26.1Q
원본 공시의 미정정 값이 26.2Q 공시의 정정 비교컬럼에 반영되지 않았다("적용후 컬럼 파싱 불안정"
사각의 구체 사례).

`scripts/fix_20260917_kr0073_2026q1_headline_afterapply.py`로 3칸 정정(item1/14/27_적용후).
부수효과로 R5_기준금액 적용후 항등식이 깨져(하위 세부항목은 재공시 안 됨) `validate_kics_disclosure.py`·
`validate_data_contract.py`에 `AFTER_IDENT_ISSUER_INCONSISTENT` documented-exception 등재부 신설
(잔차 938.25 박제, owner 승인 — 이 배터리는 R1/R2/R5/R6/R7/R8 중 R5만 해당, 나머지 축은 등재 없음).
`sync_master_xlsx_sheet.py "K-ICS공시"` xlsx 동기화. 게이트 `RED=0`(양쪽) 확인 후
`scripts/export_public_sheets.py` 재실행(`K-ICS공시.json`·`manifest.json`만 변경).

격리 워크트리(`../insurequant-main-deploy`, `origin/main` 기준) cherry-push — kics_disclosure.json
+ public_exports 2개 파일만, 커밋 `a84520c`. 라이브 검증: `kics_disclosure.json` 200, KR0073
2026.1Q item27_적용후="211.39" 확인. HTML 무수정, keep-list 밖 파일 섞임 없음.

## 2026-09-14 (2차) — 손보 2사 추가(24→26사) + `value_verified` UH-25 화면축 배선 (owner 승인)

두 가지 독립 변경, 둘 다 jp 범위.

**① 共栄火災海上保険·ヤマップネイチャランス損害保険 적재**: `J-ESR/nonlife_ratio_retry.json`(오케스트레이터가 원문 PDF로
독립 확인, 항등식 2/2)을 `J-ESR/merge_nonlife_ratio_census.py`에 override 소스로 배선(`load_retry()` 신설,
company_jp 매칭 시 A/B/C 그룹 원본 행을 통째로 대체, 고아 override는 `SystemExit`). `nonlife_ratio_census.json`
found 24→26·unreachable 3→1(大同火災만 잔존), 항등식 재검산 71건 중 불일치 0. `build_jesr_detail_json.py`
`RATIO_ONLY_ID_BY_JP`에 `kyoei_fire_marine`·`yamap_naturance` 2개 id 추가(caveat 없음) — `build_ratio_only_companies()`가
census를 그대로 읽어 26사를 자동 생성. census CSV(`fy2025_esr_census_20260912.csv`) 2행의 `disclosure_url`·
`doc_type`·`checked_at`·`notes` 갱신(`fy2025_esr_status`는 무변경 — 共栄火災=not_yet, ヤマップ=not_found 유지),
notes에 재현 가능한 방법 기록(共栄火災=TLS 중간인증서 보강, ヤマップ=Playwright route-intercept 우회). 행-인덱스
csv.reader/writer + utf-8-sig/LF 보존, git diff 2줄만 확인.

**② `value_verified` 계약**: `jp/jesr_esr.json`/`jp/jesr_detail.json`의 posted record마다
`{"state":"verified"|"unverified"|"exempt","reason":null|str}` 부착 — 판정은 재타이핑하지 않고 게이트 정본
`unverified_value_reasons()`·`load_source_exceptions()`을 그대로 재사용(`build_jesr_page_json.py`에
`compute_value_verified()`/`_exception_reason_by_key()`/`check_value_verified()` 신설). `build_jesr_detail_json.py`는
`public_by_en.get(company_en,{}).get("value_verified")`로 가져오고(비posted는 자동 None), ratio_only는 명시적
None + self_check 3중 강제. 오늘 기준 **16/16 전부 verified**(발화 0, 기대치와 일치). ④→⑤→④ 고정점 확인
(`generated_at` 제외 바이트 동일), ESR 16사 5필드 전건 diff 0. `pytest tests/test_jp_source_gate.py
tests/test_jp_deploy_matches_census.py` 127 passed, `scripts/prepush_check.py` REDUCED(jp-scope) gate-clear
(258 passed 2 skipped). commit/push 없음. 상세: `TODO_publishing.md` 2026-09-14 (2차) 항목.

---

## 2026-09-14 — 손보 손해율 24사 `jp/jesr_detail.json` ratio_only 레이어 + SOMPOダイレクト source_url 교체 (owner 승인)

배경: `J-ESR/nonlife_ratio_census.json`(손보 29사 전수조사, verdict `found` 24 / `not_applicable_holding` 2 /
`unreachable` 3, 오케스트레이터가 合算率 항등식 69/69 전건 검산 완료)을 `jp/jesr_detail.json`에 싣는 owner 승인
작업. HTML/CSS/`jesr_app.js`는 designer가 같은 라운드에 병행 — publishing은 JSON만.

**1) 24사 추가 (`J-ESR/build_jesr_detail_json.py` 확장)**: `EXTRACTED_PATH`(schema-item 추출) 파이프라인과는
완전히 분리된 새 함수 `build_ratio_only_companies()`를 신설해 `J-ESR/nonlife_ratio_census.json`을 직접 읽고
`build()`의 `companies_out`에 append(life_core_only 브랜치 뒤). 신규 계약 필드 2개(designer 합의):
- `data_scope: "ratio_only"` — 패널 스킵 신호. 기존 10사는 이 키 자체가 없음(="full" 취급).
- `ratio_caveat: {code, text} | null` — 4사만. `text`는 census의 `caveat` 필드를 **런타임에 그대로 복사**
  (하드코딩 재입력 금지, 전사 오류 방지). 코드 매핑만 하드코딩: トーア再保険→`lae_excluded`, ソニー損害保険→
  `ei_basis`, レスキュー損害保険→`ocr_read`, MS&ADインシュアランスグループHD→`simple_sum`.

shape는 sompo_japan(not_yet) 선례보다 한 단계 더 얕음: `profit.ratios`(pl_loss/expense/combined_ratio_pct,
cur=FY2025/prev=FY2024, FY2024 없으면 null)만 채우고 `profit.items`/`core`={}, 최상위 `capital`/`items`={},
`capital_tree`/`risk_tree`/`sensitivity`=[], `risk`/`market_sub`=스키마 키(`RISK_KEYS`/`MARKET_SUB_KEYS`)
전부 null, `aggregation`/`by_line`/`core_history`/`profit_flow`=null(life_core_only 선례 재사용), `bs`는
`build_bs_block(None)`을 그대로 호출(={"status":"not_obtained",...} — 기존 함수의 "비어있음" 표현을 재사용,
새 shape 발명 안 함), `headline`은 ESR 4필드 전부 null. `history`는 fiscal_years를 loss/expense/combined
3개 dict의 연도 합집합으로 구성(회사마다 2~5년, index 정렬 보장) + `hist_loss/expense/combined_ratio_pct`
3종만. `esr_status`는 `jp/jesr_esr.json`의 posted 레코드 멤버십으로 파생(census CSV 재파싱 안 함 — 24사
전원이 posted 아니면 not_yet뿐이라 이걸로 충분): MS&AD만 `posted`(랭킹엔 이미 실제 ESR 수치로 존재하지만
이 detail 레이어는 ratio만이라 headline은 여전히 null — 이 불일치는 후속 검토 대상으로 명시적으로 남김, 이번
티켓 범위 밖), 나머지 23사 `not_yet`.

`self_check`에 ratio_only 전용 블록 추가: 24건 카운트 + id 유일성 + `RATIO_ONLY_ID_BY_JP` 매핑 일치, esr-layer
블록(`capital`/`items`/`capital_tree`/`risk_tree`/`sensitivity`) 전부 빈값, `risk`/`market_sub` 전부 null,
headline ESR 3필드 null, `profit.items`/`core` 빈값, 合算率 항등식(loss+expense≈combined) **cur/prev 및
history series 전부 ±0.15 tol로 재검산**(census 검산과 동일 tolerance), caveat는 지정된 4사에만 붙었는지 확인.
기존 `n_posted != 2 or n_not_yet != 5` 구조 단언은 `data_scope != "ratio_only"`로 필터링해 그대로 유지 —
`_meta.coverage`의 `esr_posted`/`esr_not_yet`/`life_core_only`도 동일하게 분리하고 `ratio_only` /
`ratio_only_posted` / `ratio_only_not_yet` / `ratio_only_caveat` 4필드 신설.

**2) SOMPOダイレクト source_url 교체 (owner 승인)**: `J-ESR/fy2025_esr_census_20260912.csv`에서 분책
(`insgenjo2026_05.pdf`, 재산상황편 21p, 손해율 표 없음) → 전체책(`insgenjo2026.pdf`, 100p, 全冊)으로 교체.
행-인덱스 `csv.reader`/`csv.writer`로 편집(BOM·LF 라인엔딩 원본 그대로 보존, `diff` 1행만 확인). **교체 전
검증**: `J-ESR/jesr_http.get`으로 200 · `content-type: application/pdf` · 2,486,089 bytes 확인 → PyMuPDF로
본문 추출해 p9·p68에서 「正味損害率72.8%／正味事業費率24.3%」 직접 대조(`nonlife_ratio_census.json` B조 수치와
일치) → p64 5개년표 주석에서 esr not_yet 플레이스홀더("2025年度の単体ベースのソルベンシー・マージン比率の開示は
2026年10月末の予定です。")를 전체책에서도 재확인(`esr_status`는 `not_yet` 그대로, URL만 교체). `doc_type`에
"全冊" 표기 추가, `checked_at` 2026-09-14, `notes`에 교체 근거 기록.

**3) 파이프라인 순서 + 재실행 함정**: census 수정 → `check_source_urls.py --all`(dead=0) →
`check_esr_in_source.py --all`(found=16/not_found=0) → `build_jesr_page_json.py` 1차 →
`build_jesr_detail_json.py`(24사 추가) → **`build_jesr_page_json.py` 2차 재실행이 필수임을 이번에 발견**:
`_meta.group_children`이 `jp/jesr_detail.json`을 읽어 지주(연결)↔자회사(単体) 상세페이지를 잇는데, 1차 실행
시점엔 아직 24사가 jesr_detail에 없어 stale — `test_jp_deploy_matches_census.py`가 `_meta.group_children`
불일치로 이 순서 문제를 실제로 잡아냈다(재실행 후 Nisshin/Tokio Marine Direct/Aioi Nissay Dowa/Mitsui
Direct/Sompo Direct가 각 지주 아래 신규 연결됨). 고정점 확인(④⑤를 한 번씩 더 돌려 `generated_at` 제외 바이트
동일 재확인) → `pytest tests/test_jp_source_gate.py tests/test_jp_deploy_matches_census.py` **111 passed** →
`scripts/prepush_check.py` **REDUCED(jp-scope) gate-clear**(비교대상 13개 파일 전부 jp 범위, 242 passed
2 skipped). **ESR 16사 값 불변 확인**: `esr_pct`/`eligible_capital`/`required_capital`/`as_of`/`scope` 5필드
전건 실행 전/후 byte diff 0.

공유 워킹트리 메모: `jp/*.html`·`jesr_app.js`·`jp.css` 6개 파일이 이번 세션 내내 `git status`에 M으로 잡혔으나
이 세션은 그 파일들을 Read/Edit/Write한 적이 없음(designer 병렬 세션의 미커밋 변경) — 커밋 시 반드시 이 티켓의
7개 파일만 명시 add: `J-ESR/build_jesr_detail_json.py` · `J-ESR/esr_in_source_health.json` ·
`J-ESR/fy2025_esr_census_20260912.csv` · `J-ESR/jesr_master.json` · `J-ESR/source_url_health.json` ·
`jp/jesr_detail.json` · `jp/jesr_esr.json`. git commit/push는 오케스트레이터 소관, 이번 세션은 미실행.

모델: Sonnet 5. 소요: 약 45분(케이스 조사 15분 + 빌더 확장 20분 + 파이프라인 검증 10분).

## 2026-09-12 — J-ESR `/jp/` 페이지 데이터 JSON 신설 (`inbox/publishing/20260912T0446Z`)

배경: owner가 `/jp/` 일본어 ESR 현황 페이지 초안 킥오프(designer 병행 티켓 `inbox/designer/20260912T0446Z`). 화면 규칙
"그래프 데이터는 HTML 인라인 금지, JSON fetch"에 따라 페이지가 읽을 JSON을 publishing이 먼저 조립.

신규 `J-ESR/build_jesr_page_json.py` — stdlib만(csv/json/re/datetime/pathlib), self-check 내장(실패 시 exit 1).
입력은 `J-ESR/fy2025_esr_census_20260912.csv`(downloader 산출, 79사 census, utf-8-sig)의
`fy2025_esr_status == "posted"` 15행과, `J-ESR/jesr_sources_2026Q1.csv`(6월 수집 11사)의 보조 열(`ticker` ·
`total_assets_bn_jpy` · `target_pct` · `basis`)을 `company_jp`로 조인. 조인 규칙은 필드별로 다르게 뒀다: `ticker`는
상장코드라 시간불변이므로 무조건 조인, 나머지 세 필드는 sources 행의 `as_of`가 census 행의 `as_of`(2026-03-31)와
**일치할 때만** 조인했다 — 상호회사 4사(日本生命保険·住友生命保険·明治安田生命保険·富国生命保険)는 sources csv에
2025-03-31~2025-09-30 구분기 값만 있어서, as_of를 안 걸고 그대로 조인하면 새로 posted된 2026-03-31 수치에 옛 분기의
총자산/목표비율/basis 라벨이 잘못 붙는 사고가 난다("틀린 값을 싣느니 빈칸" 원칙 적용, CLAUDE.md). `preliminary`는
census `notes`+`doc_type` 문자열에 속보/잠정/速報 중 하나라도 있으면 true로 판정하고, 어느 키워드로 잡았는지를
`notes` 끝에 괄호로 남겼다(티켓 지시 "어느 표현을 잡았는지 notes에 남김" 반영). `doc_date`는 `doc_type` 문자열에서
정규식 3단(YYYY-MM-DD → YYYY年M月D日 → YYYY年M月) 파싱으로 추출 — 15건 전부 육안 대조 확인.

출력은 두 곳에 동일 바이트: `J-ESR/jesr_master.json`(2026-06 스키마를 전량 교체 — 이 스크립트가 유일한 생산자라
"마스터 통째 read-modify-write 금지" 원칙 예외 적용, 프롬프트·티켓 양쪽 명시)과 `jp/jesr_esr.json`(신규 `jp/` 폴더,
배포용 사본). 스키마는 designer와 합의된 고정 계약이라 키 이름은 손대지 않았고, 티켓이 derivation을 명시하지 않은
두 필드(`basis`는 조인 실패 시 상수 `"J-ICS"` 기본값, SOMPO만 sources 원본 `"J-ICS_VaR99.5"`를 그대로 반영)는
판단 근거를 답변 티켓에 남겼다.

실측 검증: `PYTHONIOENCODING=utf-8 C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe J-ESR/build_jesr_page_json.py`
→ exit 0, `15 records`, `census: {total:79, posted:15, not_yet:62, not_found:2}`, `preliminary=5`
(LifeNet·朝日生命保険·富国生命保険·かんぽ生命保険·住友生命保険). `cmp J-ESR/jesr_master.json jp/jesr_esr.json` 바이트
동일. `head -c3 | xxd -p` 양쪽 `7b0d0a`(BOM 아님), 스크립트 자체도 `23202d`. `ast.parse` 통과. `git status --short
J-ESR/ jp/` = 정확히 3건(`M jesr_master.json` · `?? build_jesr_page_json.py` · `?? jp/`) — 루트 마스터·HTML·xlsx·
public_exports·keep-list 무변경 확인(티켓 4번 제약 준수).

**라이브 미반영(이번 범위 밖)** — 필요 항목 3가지를 조사해 답변 티켓에 기록:
1. keep-list(§1/§9) 신규 페이지 경로 추가 필요. **실측**: 4-페이지 하드코딩(`["index.html","K-ICS.html","IFRS17.html",
   "공시보고서.html"]`)이 `claude-agent-publishing.md` §1 grep 스니펫 · `tests/test_deploy_assets.py:27` `PAGES` ·
   `tests/test_push_gate_wiring.py:378` `_HTML` 세 곳에 그대로 박혀 있어, `/jp/` 페이지를 여기 추가하지 않으면 그
   fetch가 세 게이트 어디서도 "통과"가 아니라 아예 안 보이게 된다(불변식 1번: 게이트가 보는 파일=사용자가 보는 파일).
2. master xlsx 신규 시트는 불요 — `scripts/build_master_xlsx.py`의 `MASTERS`, `scripts/sync_master_xlsx_sheet.py`
   둘 다 "jesr" grep 매치 0(J-ESR은 K-ICS/IFRS17 xlsx 체계 밖 독립 트랙). 시트를 만들지는 owner 결정 사항으로 남김.
3. `scripts/status_report.py` §4("화면 fetch ↔ 마스터 시트")는 1번의 `_HTML`을 갱신하기 전까지 `jp/jesr_esr.json`
   fetch 자체를 못 보므로 지금은 무검사 상태 — 갱신하는 순간 `MASTERS`에 대응 시트가 없어 GAP으로 잡힐 것(2번과 연결).

티켓 `status: answered`로 전환(`_resolved/` 이동은 owner 확인 후). 서브에이전트 생성 없이 직접 처리.

---

## 2026-09-11 — 지식재산 보호 0원 조치, 저장소 쪽 (LICENSE · robots.txt · manifest 지문 · 투자기록 · IR xlsx 추적해제 · 상시유지 파일 배선)

배경: `artifacts/legal/ip_protection_report_20260911.md`(등록권리 없는 개인 운영 사이트가 지금
자동으로 가진 권리 = 저작권 + 데이터베이스제작자권 + 도메인, 그 중 0원으로 강화되는 것들).
owner 지시 3개: 약관 페이지 따로 만들지 말 것(privacy.html 에 추가, designer), 실명 조상욱 OK,
**진입장벽 낮게**(동의 절차·팝업 추가 금지, 금지 항목은 자동수집·대량재배포 둘만). 화면·JS 는
designer 가 같은 시간에 작업했고 이 항목은 publishing 소관 파일만 다룬다. commit/push 없음.

**① `LICENSE`(루트, 신설).** 19줄, 한국어 본문 + 영어 요약. All rights reserved 이되 허용 범위를
먼저 적었다(열람·캡처, 출처 표기 인용, 사내 분석). 금지는 둘 — 자동화 수단으로 통째 수집, 대량
재배포·재판매·유사 서비스 구축. 저작권법 제4장의2 데이터베이스제작자권 고지("개별 수치가 공개
사실이라는 점은 DB 전체·상당부분 권리에 영향 없음"), 원천 권리는 각 공시 주체, 전문 링크
`privacy.html#terms`, 운영자 조상욱 2026. 조문식 "제N조" 안 씀.

**② `robots.txt`.** 기존 상단 주석(keep-list 는 HTML grep 도출이라 이 파일은 상시 유지) 살림.
`User-agent: *` 는 `Allow: /` 유지 + `Disallow: /public_exports/`(다운로드 방명록 스냅샷 —
렌더링에 안 쓰여 색인 불필요; 루트 `*.json` 은 렌더링 리소스라 **일부러 안 막음**). AI **학습용**
크롤러 8종(GPTBot·CCBot·ClaudeBot·anthropic-ai·Google-Extended·Bytespider·meta-externalagent·
Applebot-Extended)만 `Disallow: /`. 보고서 초안에 있던 ChatGPT-User·PerplexityBot 은 **뺐다** —
사용자가 질문할 때 대신 읽어 오는 fetcher 라 막으면 AI 검색 유입이 끊긴다(owner 편의 원칙).

**③ `public_exports/manifest.json` 지문.** 생성 스크립트는 `scripts/export_public_sheets.py`
(`grep manifest.json scripts/` 로 확인). designer 가 먼저 `license`(URL)·`build_id`(HEAD short
sha) 를 넣어 두어 그 위에 얹었다: `license` 는 조건 문장으로, `terms_url`·`copyright` 추가.
안전 근거 두 개를 코드 주석으로 남김 — download-survey.js 는 `sheets`·`generated_at_utc`
(+`build_id` 있을 때만) 만 읽고, `validate_live_artifacts.py` CHECK 6(L636-663) 은
`man["sheets"]` 만 대조하므로 top-level 키 추가는 둘 다 안 깨진다. 재실행 결과: 13개 시트
스냅샷 **바이트 동일**(HEAD 대비 드리프트 0), `manifest.json` 만 +5줄. xlsx 표지 "이용 조건"
행은 **클라이언트**(`download-survey.js buildCoverSheet`) 가 만들고 designer 가 이미 넣었으므로
publishing 은 손대지 않았다. 이 경로엔 마스터 xlsx 가 없어 수식 캐시 위험 0.

**④ `docs/ip/investment_record.md` + `scripts/measure_investment_record.py`.** "상당한 투자"
증거 1장. 추정치 없이 전부 잰다(git log/rev-list, os.walk 줄 수, 골든 fixture `by_rule`,
`rule="…"` 리터럴, 마스터는 `git show HEAD:` 로 읽어 동시 세션 반쯤 쓴 파일 배제, 원천 파일은
디스크 census). 첫 실행에서 회사 수가 전부 0 으로 나왔다 — 회사 키가 `회사명` 이 아니라 13개
공통 `원보험사코드` 였다(export 단계에서 드롭되는 키라 눈에 안 띔). 고쳐서 39사 확인. 실측 요약:
첫 커밋 2025-09-15 · 561 커밋 · 57 작업일 · scripts 278파일 84,175줄(+probes 1,295파일) ·
src 33/8,822 · tests 41/10,392 · K-ICS 룰 id 30, findings 16,140 · validator rule id 123 ·
골든 8 · 테스트 함수 266 · 마스터 13개 53,530행 · 39사 · 16분기 · 공시 PDF 550 · DART raw 1,297 ·
KIDI 548 · gold xlsx 44 · `_gold` 22 · resolved 티켓 386 · 포스트모템 10. 갱신 명령을 문서 맨 위에
박아 분기마다 같은 축으로 다시 잰다.

**⑤ IR xlsx 추적 해제.** `git ls-files 'data/ir/**/*.xlsx'` = 11(전부 FY2026_Q2 팩트시트, 각
보험사 저작물). 읽는 코드 전수 grep: `crawl_ir_db.py`·`_build_lob_cross_check.py`·
`check_data_file_integrity.py`·`download_ir_*.py` 전부 **디스크 경로**, `git show` 로 data/ir 를
읽는 곳 0 → `git rm --cached` 11건(디스크 잔존 확인 11), `.gitignore` 에 `data/ir/**/*.xlsx` +
사유 주석. 이력 purge 는 하지 않음(owner 결정, 현 PC push 불가 사정도). main 에는 원래 없음.

**⑥ "HTML 무참조 상시 유지 파일" 배선 — LICENSE 의 keep-list 등록 근거.** §1 keep-list 는
HTML grep 으로 도출되는데 `LICENSE` 는 아무 HTML 도 참조하지 않는다. 그러나 공개 `main` 이 곧
GitHub 공개 저장소이고 `https://www.insurequant.com/LICENSE` 로도 열리므로 거기 없으면 의미가
없다 → robots.txt·`.nojekyll`·CNAME 과 같은 부류. designer changelog 2026-09-11 "미배선 잔여"
(robots.txt 상시 유지를 문서·테스트에 배선, publishing 소관)가 정확히 이 작업이라 같이 처리:
`claude-agent-publishing.md` §1 에 표 신설 + §9 스냅샷에 `.nojekyll`·`LICENSE`·`robots.txt`·
`sitemap.xml` 5줄, `docs/launch_runbook.md` §2 에 소절 신설(robots.txt 주석이 가리키던 절이
실제로는 없었다), `tests/test_deploy_assets.py::test_always_keep_files_exist_and_are_documented`
— `ALWAYS_KEEP` 5개의 존재·BOM 없음·두 문서 등재를 강제. "배선했다 ≠ 강제된다" 원칙대로 테스트가
정본이고 문서는 테스트가 검사하는 대상이다. `pytest tests/test_deploy_assets.py` **11 passed**.

**다음 배포 주의.** §3 절차 2) 의 `git checkout <branch> -- …` 목록에 `LICENSE`·`robots.txt` 를
넣을 것 — 둘 다 grep 으로는 안 나온다.
