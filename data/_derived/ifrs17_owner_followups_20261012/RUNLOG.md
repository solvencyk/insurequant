# IFRS17 owner 승인 후속 런로그 (parser-ifrs17, 2026-10-12)

티켓: `inbox/parser/20261012T1020Z__orchestrator__MULTI_2023.4Q-2026.2Q__ifrs17_owner_approved_followups.md`(공유 티켓, 고치지 않았다 — 오케스트레이터가 종결). owner 승인 = `TODO.md` 「owner 결정 대기」 ⑯·⑳·㉑·㉒·⑦·⑧·⑨·⑩·⑮.
규칙 준수: 마스터는 셀 단위 + 옛 값 guard + 백업(통째 read-modify-write 없음, `build_root_masters.main()`·`validate_master_tables.py`(`--no-build` 없이) 실행 없음), 서브에이전트 없음, docling 없음(PDF 텍스트층 + 쪽 렌더링), push 없음, 예외 등재 없음, xlsx·`public_exports`·패널·HTML 안 건드림.
증빙·백업·게이트 전후·스크립트는 전부 `data/_derived/ifrs17_owner_followups_20261012/`(백업은 `…_backup_20261012/`, git 에는 안 올림).

## 결과 한 표

| 항목 | 결과 | 바꾼 칸(HEAD 대비 키 대조, 삭제 0) |
|---|---|---|
| ⑯ 재보사 인쇄된 0 7칸 | validation 이 같은 날(`f0535af`) `data/_gold/user_pl_confirmed_cells.json` 에 7칸을 등재한 것을 이름·항목·분기로 확인한 뒤 `scripts/reinsurer_resweep_pl_followup.py --restore7 --apply` 로 복원 | `PL_breakdown.json` 13,794 → 13,801행(+7 = 뮌헨 투자손익 2023.4Q · RGA 영업외손익 2023.2Q·2025.3Q · 제네럴 2024.3Q·2025.3Q · 퍼시픽 2023.3Q·2025.3Q, 값 0.0) + 값_당분기 1칸(RGA 영업외손익 2023.3Q None → 700.0) + 사이드카 7블록 |
| ⑳ 퍼시픽 2023.4Q CSM 항목 4 | 인쇄값 950.76538 유지, `CSM_waterfall_provenance.json` 셀에 `note`(영업양수 1,069억 포함, 인쇄값 + 분해 + 원천 쪽) | 사이드카 1셀 필드 1개, 마스터 변경 0 |
| ㉑ 뮌헨 2023.4Q ILP 부호 반전 · ㉒ 하노버 2023.4Q ILP 충돌·제네럴 민감도 | 변경 없음: 뮌헨 ILP 2023.4Q 현 적재(항목 1~8·10~15) 그대로, 하노버 2023.4Q ILP 공란 그대로, `CSM_sensitivity.json` HEAD 와 내용 동일 | 0 |
| ⑦ 처브 항목 20 정의·ILP RED 5 | 원문 재독으로 정의 틀림 확인 → 중간분기를 특별계정 포함(D2)으로 통일. 포트폴리오 검증기 RED 7 → 2 | `IFRS17_BS.json` 항목 20 6칸 · `insurance_liability_portfolio.json` 항목 14·15 9셀(18값) · 오버레이·사이드카·파트·ILP provenance |
| ⑧ KR0029 2024.4Q 10배 규칙 | 원문 재확인: 값 맞음(구조). 데이터 변경 0, 등재 필요 목록에 올림 | 0 |
| ⑨ KR1102 2026.1Q ILP 합계 | 원문 재확인: 인쇄 합계가 두 절 모두 Indirect-Par 행을 뺐다(확인). 정정값은 파생값이라 「확정된 것만」 규칙으로 미적재, 등재 필요 목록에 올림 | 0 |
| ⑩ KR0004 2025.4Q CSM 0.0 대 6,227 | 원문 재확인: 두 숫자는 보고 주체가 다른 각자의 인쇄값, 6,227 워터폴을 원천에서 확정할 수 없음. 데이터 변경 0 | 0 |
| ⑮ 분할표 5사 + 한화생명 | 분할표 4사(AIA·처브·메트라이프·BNP) y9·y10 8칸 채움(뒷 반쪽 표 합침, 별도 파일 우선), 한화생명 y1~y10 10칸 연결 → 별도, 라이나는 이미 완전해서 변경 0 | `CSM_amortization.json` 18칸 |

## 1. ⑯ 복원 (7칸)

- 등재 확인: `data/_gold/user_pl_confirmed_cells.json` 33건 중 PL_breakdown 7건(뮌헨 · RGA ×2 · 제네럴 ×2 · 퍼시픽 ×2, 값 0.0, 원문 쪽 인용)이 있다(`p39_check_registry7.py`). 복원 전 데이터 계약 게이트는 이 7칸을 `PL_YTD_COLLAPSE_CONFIRMED_PENDING`(YELLOW, 복원 대기)로 말했고, 복원 뒤에는 `PL_YTD_COLLAPSE_OWNER_CONFIRMED`(YELLOW, 값 박제·원천 문구 재확인 통과, 비차단) 7건으로 바뀌었다 — **`PL_YTD_COLLAPSE_TO_ZERO` 는 나지 않는다**(`gate_after_data_contract.txt`).
- 키 대조(`p40_pl_keydiff_head.py`): 삭제 0 · 추가 7 · 변경 1. 마스터테이블 게이트 pl_bridge `3653P(진짜 1278 · 구성상 2040 · 부분 335)/29F/2748S/0NEW` → `3660P(1279 · 2046 · 335)/29F/2741S/0NEW`(통과 +7, SKIP −7), 나머지 SUMMARY 필드 동일. 복원 전 상태·되돌리기 정보 `restore7_state.json`, 백업 `data/_derived/reinsurer_resweep_backup_20261012/restore7/`.

## 2. ⑳ 퍼시픽 KR1107 2023.4Q

원문 FY2024 감사보고서 PDF 51쪽(인쇄 -49-) `(전기)` 표 「2. 자산양수도」: 공정가치법 17,979,692,063 + 완전소급법 88,963,487,826 = 106,943,179,889원(1,069.43억), 인쇄 기초 0, 「보험계약마진을 변경하는 추정치 변동」 FVA 1,043,243,466 + FRA −12,909,885,528 = −118.67억. 마스터 항목 4 = 잔차 950.76538 = 두 값의 합(순수 가정 변동 아님). `scripts/annotate_csm_prov_kr1107_20261012.py [--apply|--revert]`(백업 `CSM_waterfall_provenance.json.pre_note`).

## 3. ⑦ 처브 KR0100 — 정의 D2 로 통일

- 문제: 업무보고서 서식 재무상태표(FY2025_Q3 까지)는 일반계정 `1. 보험계약부채`(D1)와 `IV. 특별계정부채`(SA, 변액)를 따로 인쇄한다. 연말 DART 셀(2023.4Q·2024.4Q·2025.4Q)과 2026 K-IFRS 서식(`Ⅰ. 보험계약부채`, 2026.1Q p26)의 보험계약부채는 변액을 포함하는데 중간분기 BS 6칸·ILP 9셀은 D1 만 담았다(2025.1Q 연말 13,004억 → 10,717억 → 13,358억 계단; 2-4 합계가 변액 2,400~2,700억을 포함해 항목 20 < 항목 8, R3 RED 5). 메트라이프 항목 20 은 이미 같은 정의다.
- 원문 재독(9분기, `extract_chubb_d2_20261012.py`·`p20`~`p22`): D1·SA·가.잔여보장·나.발생사고 토큰이 PDF 쪽에 그대로 인쇄(합 − D1 ≤ 1원), 부채총계 − D1 − 재보험계약부채 − SA = 기타부채 + 계약자지분조정이 6분기에서 인쇄 토큰으로 원 단위 폐합(나머지 3분기는 2-2 요약표 억원값 일치), 2-2 요약 `책임준비금`·`특별계정부채` 9분기 반올림 일치. 특별계정은 LIC 를 안 담는다(일반계정 LIC 가 연말 DART LIC 와 같다 — 2023.12.31 222.82 대 222.83, 2024.12.31 250.05[2025.1Q p32 전기 열] 대 250.05). D2 대 연말 K-IFRS 라인 −0.110 %·−0.074 %.
- 쓰기: BS = `scripts/apply_ifrs17_bs_fix_20261012.py --spec …/chubb_d2_spec_bs.json --round chubb_d2 --apply`(master + 오버레이 + 사이드카 + 파트 파일; 2023.1Q 는 `KR0100_agent_gran.json`, 나머지 5칸은 `KR0100_agent_followup.json` — `merge_bs_disclosure_parts.py` 우선순위상 엔진 파트 `KR0100.json` 보다 위라 엔진 재실행이 D1 을 되살리지 못한다). **빌더 임시 실행(출력 경로 격리) 11,016행·값 차이 0·산출 바이트가 라이브와 동일(sha256 `0d88b860…`)** — 재빌드로 안 사라진다(`dry_build_bs.py`). ILP = `scripts/apply_chubb_ilp_d2_20261012.py [--apply|--revert]`(항목 14·15 18값 + provenance 9셀 + `value_corrections` 9 + `backfills` 1; 항목 10~13 불변).
- 주의(고친 실수): provenance 키로 처음 `original_basis*` 를 썼다가 `scripts/build_master_xlsx.py` 가 그 키를 가진 셀을 「소급재작성」 셀로 표시한다는 것을 보고 되돌린 뒤(`--revert`, 바이트 동일 복원 확인) `general_account_values_eok`·`d2_note` 로 바꿔 다시 적용했다.
- 효과: `validate_insurance_liability_portfolio.py` RED 7 → 2(남은 2 = KR0029 2024.4Q 10배 규칙, KR1102 2026.1Q R2), LIC 검산기 RED 0·YELLOW 23 불변(처브 줄 없음). 빈 BS 3분기(2023.2Q·2023.3Q·2024.2Q)는 채우지 않았다(D2 값은 `chubb_d2_evidence.md`).

## 4. ⑧ AIG · ⑨ 스위스리 · ⑩ 예별 — 원문 재확인 (데이터 변경 0)

상세·쪽 번호·수치 `item4_5_origin_checks.md`. 요지: ⑧ 4-6-2 합계 −2,350 · 775 · 923 · 683(PDF 21쪽) = 마스터, DART 순 LRC 30.23, BS 부채 기준 LRC 884.60 + LIC 2,033.08 = 2,917.68 — 구조(잔여보장자산 상계)이고 값은 맞다. ⑨ 2026.1Q 2-4 PDF 9쪽 렌더링: 생명 합계 (2,664)·313·197 = Indirect-Par 무배당사망 (4,842)·50·1,207 을 뺀 값, 손해 합계 (2,801)·411·487 = Indirect 질병 (1,914)·20·310 을 뺀 값; 2026.2Q·2025.4Q 합계는 그 행을 포함. 전체 행 합 BEL −12,221 · RA 794 · CSM 2,200(항목 8 −9,227)은 인쇄값이 아니어서 안 실었다. 별건: 2025.2Q 는 Indirect-Par 행이 아예 인쇄되지 않은 판(항목 1 −1,678, 인쇄값 그대로). ⑩ DART 엠지 FY2025 별도 XML 8768행 CSM 열 `계약이전 (271,333,145)천원` → 기말 `-` · 마스터 항목 1~6 은 인쇄값 그대로(항목 4 −3,534.1 = 추정치 −835.5 + 손실부담 +14.7 + 계약이전 −2,713.3); 경영공시(예별손해보험(주)) PDF 13·22·28쪽 CSM 6,227 · CSM 변동표 없음.

## 5. ⑮ 분할표

- 원인: 연간 CSM 상각 스케줄 표를 앞 반쪽(1~8년)과 뒷 반쪽(9년·10년·11~15·…·30년 이후·계)으로 나눠 인쇄하는 5사 중 4사(AIA · 처브 · 메트라이프 · BNP)가 마스터 2025.4Q 에 y1~y8 만 있고 y9·y10 이 비었다(라이나는 2026-10-11 에 PDF 로 이미 완전). 한화생명은 패널이 연결 표(88,752.04억)를 골라 마스터 y1~y10 이 연결 값이었다(기말 CSM 87,136.5 는 별도; 이유는 `csm_amort_schedule_fix_runlog_20261011.md` §9-2 — 행 수 점수가 별도 우선 규칙보다 먼저 결정한다).
- 읽기(`scripts/extract_amort_split_tables_20261012.py`, 원문 DART XML 직접): 별도 파일 우선(`_00760.xml`; AIA·메트라이프·라이나는 연결 파일과 전 행 일치 확인). 앞·뒤 반쪽을 문서 순서로 짝지어(첫 쌍 = 당기말, 64쌍 증명된 규칙) y9·y10 을 읽고 항등식: 모든 포트폴리오 행 `y1~y8 + 뒷 반쪽 = 계`(잔차 0~1 단위), 당기 합계 = 마스터 2025.4Q 기말 CSM(상대차 ≤ 3.4e-5), 전기 합계 = 마스터 2024.4Q 기말 CSM. 한화생명 별도 표(`_00760.xml` 18512행) 합계 87,136.52 = 마스터 기말 CSM.
- 쓰기: `scripts/load_amort_split_tables_20261012.py [--apply|--revert]` 18칸(옛 값 guard · 백업 `CSM_amortization.json.pre_amort_split` · 행 단위 증명). 표·전수 목록 `amort_split_evidence.md`/`.json`.
- 안 건드린 것: 패널 `csm_amort_schedule.json`·`viz_build_ifrs17_panels.extract_amort_schedule`(앞 반쪽만 읽음 — 라이나 행을 마스터값으로 바꿀지는 이번 범위 밖, 보고만)·xlsx. 마스터를 `build_tidy_exports.py --only amort` 로 패널에서 다시 만들면 이 18칸이 되돌아가므로 그 뒤 로더를 다시 돌린다.

## 6. 게이트 전후(`gate_overlay.py`: 같은 게이트 코드, 기준선 = 내가 바꾼 파일의 백업 바이트, 저장소 쓰기 차단; `run_gates.sh`)

| 게이트 | 전 | 후 |
|---|---|---|
| 포트폴리오 검증기 | RED 7 · YELLOW 605 | RED 2 · YELLOW 610 |
| LIC 검산기 | RED 0 · YELLOW 23 | RED 0 · YELLOW 23 |
| CSM 연속성 | RED 0 | RED 0 |
| `validate_master_tables --no-build` | pl_bridge 3653P(1278·2040·335)/29F/2748S/0NEW | 3660P(1279·2046·335)/29F/2741S/0NEW, 그 밖 필드 동일(closing 393P/0F · csm_amort_identity 383P · qoq 267Y …) |
| `validate_data_contract` | RED 0 · YELLOW 152 | **RED 5** · YELLOW 152 |

데이터 계약 RED 5 는 전부 xlsx 시트 동기화(publishing 몫, 내가 xlsx 를 안 만졌다): `MASTER_XLSX_DRIFT` 17BS 6셀 · CSM상각 18셀 · 보험계약부채 18셀 · 손익분해PL 1셀(값_당분기) + `MASTER_XLSX_ROW_MISSING` 손익분해PL 7행 → `scripts/sync_master_xlsx_sheet.py "17BS"` · `"CSM상각"` · `"보험계약부채"` · `"손익분해PL"`. YELLOW 152 는 같은 수(복원 대기 7건이 박제 확인 7건으로 바뀜).
골든: `tests/test_master_tables_golden.py`(pl_bridge 7칸 이동만) · `tests/test_ifrs17_bs_golden.py`(sha256 `ef70b026…` → `0d88b860…`, 행 수 불변) 를 `--update` 로 재생성, `validate_golden_input_fingerprints.py --update`(ifrs17_bs 한 항목만 이동) — 이유: ⑦ 처브 6칸 + ⑯ 복원 7칸. 시험: 마스터테이블 골든 · viz 골든 2종 · 배당 · 상각 단위시험 13 통과, `test_push_gate_wiring`·`test_quarter_horizon` 89 통과, `test_disclosure_raw_pdf_wiring` 520 통과, `test_deploy_assets` 는 K-ICS.html 쪽 3건 실패(다른 레인 작업 중, 내 변경과 무관).

## 7. 남은 것

- **등재 필요 목록(validation)**: ① (KR0029, 2024.4Q, 포트폴리오 검증기 `R3_CROSS_CHECK` 10배 규칙, 「순 LRC 가 잔여보장자산 상계로 0 근처(+31.0억, DART 순 LRC 30.23), BS 항목 20 은 부채 기준 LRC 884.60 + LIC 2,033.08」 — R3 분기에는 등재부를 읽는 쪽이 없어 규칙 변경 + 변이시험 필요) ② (KR1102, 2026.1Q, `R2_CENSUS`, 「발행사 합계 행 불완전: 두 절의 인쇄 합계가 Indirect-Par 행을 뺐다(PDF 9쪽 렌더링)」) — 파생 적재를 owner 가 원하면 ②는 등재 대신 한 번에 적재(BEL −12,221 · RA 794 · CSM 2,200; xlsx 기준표시에 「계산값」 표기 필요).
- publishing: xlsx 4시트 동기화(위), NB·패널은 불변. designer: `csm_combo` 패널 재빌드(처브 ILP 9셀 값 변경 + 처브가 LIC 「추정」 불신 목록에서 빠질 수 있음).
- 패널·추출기 분할표 읽기(앞 반쪽만) 수정은 별도 티켓(패널 재생성 + `test_viz_ifrs17_panels_golden --update` 동반).
- 예별 2025.4Q: 화면 0.0 표시·정의는 owner/designer 결정(원천에서 6,227 워터폴 확정 불가). 사이드카 비고(「항목 4 에 계약이전 −2,713억 포함」)는 지시가 없어 안 달았다.
