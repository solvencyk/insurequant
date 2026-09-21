# Insurequant Parser TODO — K-ICS lane (Stage 2)

> Last updated: 2026-09-21(17회차 — inbox `20260921T0057Z`(KR0074 2026.2Q 금리민감도 검증)
> 1건 처리, owner 발주) — `status: answered`, 원 sender 재확인 대기.
>
> **KR0074 라이나생명보험 2026.2Q — 6칸 전부 원문 일치, 적용전=적용후는 진짜(경과조치
> 미신청). census 로 다른 3사(KR0050·KR0069·KR1098) 결측 9칸 발견 + 수정.**
>
> **① KR0074 cell-by-cell.** `md_inbox/FY2026_Q2/KR0074_라이나생명보험.md` L816-829
> "2) 금리 민감도 분석" 표 — 마스터 6행(적용전 3+적용후 3) 전부 원문과 숫자 단위까지 일치
> (지급여력비율 337.12/344.02/349.43/353.20/356.41 · 금액 72573/71988/71251/70442/69605 ·
> 기준금액 21527/20926/20390/19944/19529). RS1(비율=금액/기준금액×100)·RS2(base=item1/14/27
> anchor) 둘 다 수식대로 정확히 닫힌다. 듀레이션(2.0828/4.8995)·컨벡서티(-45.47/135.36)도
> `duration_convexity()` 재계산과 소수 4자리까지 일치. **수정 0건.**
>
> **② 적용전=적용후 판정: 진짜(경과조치 미신청), 미러링 아님.** 증거 4중: (a) 표 자체의
> 각주 "주3) (경과조치 미신청 회사) 당사는 선택경과조치를 적용하지 않아 경과조치 전·후 금액
> 및 비율이 동일함" — 이 표 고유의 각주, 공통적용 세부표가 아니라 **헤드라인급 금리민감도
> 표 자신**의 선언. (b) `_TRANSITION_KIND`(scripts/validate_kics_disclosure.py L536-556, FSS
> 붙임-1 정본) 18사 목록에 KR0074 **부재** — TFI(공통)만 적용받는 21사 쪽. (c) 별건 산출물
> `scripts/_probes/_build_kr0074_patch.py`(08-31, kics_disclosure.json 용, 이번 세션과 무관한
> 이전 라운드 산출물)가 raw p.18 O/X표로 독립 확인: TAC=TIR=TER=TIRR=PCA_DEFER 전부 X. (d) 같은
> 항등식이 마스터에 있는 KR0074 나머지 3개 분기(2024.4Q·2025.2Q·2025.4Q)에도 일관.
>
> **③ 2026.2Q 커버리지 census — 39사 완전 그리드(6칸×39=234) 확정, 수정 후 gap 0.**
> 수정 전 225행(39사 중 36사 6/6, 3사 3/6 — KR0050 하나손해·KR0069 삼성생명·KR1098
> 카카오페이손해 전부 **적용후 3행 결측**). 칸 단위 판정:
>   - **KR0050**: MD 표의 적용후 셀이 **공백**(대시도 아님) — 표 각주 "주3) (경과조치 미신청
>     회사) ...전·후 금액 및 비율이 동일함" 명시. → 우리가 못 뽑은 것(추출 갭), 원문 부재 아님.
>   - **KR0069**: MD 표의 적용후 셀이 "-"(대시) — MD 는 각주를 안 실었지만 raw PDF fitz
>     전체텍스트(0-idx p43)에 동일 각주 "주3) 당사는선택경과조치를적용하지않아경과조치전·후
>     금액및비율이동일함" 확인(docling 리딩오더가 표보다 앞쪽 다단 컬럼에 각주를 떨어뜨림).
>     → 추출 갭.
>   - **KR1098**: raw PDF 원문 자체가 두 번째 블록 라벨을 "경과조치전"으로 **오식**(후가
>     아님) — fitz 텍스트 + 480dpi 렌더(`artifacts/_kr1098_2026q2_labelzoom_480dpi.png`) 둘 다
>     확인, 숫자는 첫 블록과 완전 동일 재인쇄 + 같은 미신청 각주. 추출기의 dedup 로직(코드
>     주석 "dedup verbatim-duplicate blocks (OCR), e.g. KR1098 두 적용전 동일")이 이 블록을
>     진짜 적용후로 인식 못 하고 중복으로 버렸다 — **추출 갭**(원문엔 있음, 라벨 오식 때문에
>     파서가 놓침).
>   - 3사 전부 `_TRANSITION_KIND` 부재(TFI-only) — KR0074 와 같은 계열.
>
> **수정**: `scripts/fix_20260921_ratesens_2026q2_nonapplier_mirror.py` — 3사 각 3행(적용전
> 값을 적용후로 미러, 듀레이션·컨벡서티는 `extract_kics_rate_sensitivity.duration_convexity()`
> 재호출로 산출, 재타이핑 아님). 가드: 실행 전 (사,분기)당 적용전 3행·적용후 0행 assert,
> 실행 후 기존 789행 byte-identical 재확인. `kics_rate_sensitivity.json` 789→798행(+9).
> 백업 `kics_rate_sensitivity.json.bak_pre_20260921_nonapplier_mirror`.
>
> **게이트 재확인**: `validate_kics_rate_sensitivity.py` 수정 전후 **gate RED=0 불변**
> (RS1 0+1exc/RS2 0+4exc/RS3 64Y/RS4 1Y/RS5 0+17exc). 2026.2Q census 재실행:
> 39사 전부 6/6(=234행), 중복 키 0. 참고: RS4/RS5 어느 룰도 이 "적용전 있는데 적용후만
> 결측" 패턴을 못 잡는다(RS5는 (사,분기) 전체 결측만 봄, RS4는 회사 자체가 없는 분기만 봄) —
> **게이트 사각**으로 validation 에 별도 inbox 통지함(RS6 후보,
> `inbox/validation/20260921T0100Z__parser__ALL_2026.2Q__ratesens_phase_level_census_gap.md`).
>
> **미착수(범위 밖, 근거만 남김)**: KR0050·KR0069 는 2024.4Q/2025.2Q/2025.4Q 도 같은
> 적용전-only 패턴이고 grep 으로 미신청 각주 alt-hit ≥1(전분기), KR1098 은 2025.4Q 도 동일
> 패턴(footnote exact-hit 확인됨). **분기별 문구가 docling 공백 처리에 따라 갈려 정규식
> exact-hit 이 quarter 마다 0/1 로 흔들린다**(KR1098 2026.2Q 도 정확매치 0인데 이번 세션
> fitz/렌더 직접확인으론 각주가 실재) — 이번 세션은 2026.2Q 만 raw 로 직접 확인했으므로
> 나머지 분기는 손대지 않음(추측 채움 금지). 다음 라운드가 같은 방법(raw 개별 확인)으로
> 마무리하면 됨.
>
> 재현: `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
> scripts/validate_kics_rate_sensitivity.py` · 티켓 답변 전체 =
> `inbox/parser/20260921T0057Z__owner__KR0074_2026.2Q__rate_sensitivity_verify.md`.
>
> 변경 파일: `kics_rate_sensitivity.json`(+9행) · 신규
> `scripts/fix_20260921_ratesens_2026q2_nonapplier_mirror.py` · 프로브 6종
> `scripts/_probes/_20260921_*.py` · `artifacts/_kr1098_2026q2_*.png` · 신규 inbox
> `inbox/validation/20260921T0100Z__parser__ALL_2026.2Q__ratesens_phase_level_census_gap.md`.
>
> Last updated (이전): 2026-09-20(16회차 — inbox `20260920T0430Z`(KR0032 `BS_KICS_HARD_ZERO` 3분기)
> 1건 처리, orchestrator 발주) — `status: answered`, 원 sender 재확인 대기.
>
> **판정 = (a) 추출 갭 6칸 전부.** NH농협손해보험(KR0032)은 **비지배지분 행이 없는 6행 표**로
> 공시하는데(부모 라벨 `(1+2+3+4+5+6)`) 정본 슬롯은 7행이라 한 칸이 어긋난다.
> `AUDIT_LABEL_ALIASES` 의 `"6. 조정준비금" → "7. 조정준비금"` 이 **마지막 행만** 제자리로
> 돌려놓아, 그 위 두 행이 밀린 채 과거 write path 에 실렸다 — 이익잉여금 → item8(자본조정),
> AOCI → item10(비지배지분), item7·item9 에는 0. **오늘 코드는 이미 정상**이라(2024.4Q MD 재생 시
> item7=10279·item8=0·item9=-2617 정답) 마스터 행이 stale 이었다. `fill_period` 는 UPSERT 라
> `--refresh` 없이는 기존 셀을 안 덮는다. 2023.2Q·2023.3Q 는 현행 `extract_kics_detail_rows` 가
> 자본 표를 아예 못 잡아(7 pair 만 반환) raw PDF 로 직접 확정했다.
>
> **확정 경로 3중**: raw PDF fitz words→y버킷→x정렬 재구성 · **240dpi 렌더 3장 눈대조**
> (`artifacts/kr0032_render/`) · docling MD. 단위는 표 머리글 `(단위: 억원, %)` 라 환산 없음.
> 정정 12칸(6칸 채움 + 밀려 있던 6칸 0 복귀): item7 0→9,577/9,115/10,279 · item9 0→2,383/2,607/
> -2,617 · item8·item10 → 0. `scripts/_probes/_20260920_fix_kr0032_slot_shift.py`(guard 6종:
> 정확타격·기존값 assert·항목명 assert·`값_적용후` 존재 시 abort·Σ(5..11) 불변·**12개 외 행 변경
> 시 abort** + 쓰기 직전 mtime/size 재확인). 적용 후 `diff` **12줄**, 그 외 0.
>
> **게이트 실측**: `validate_kics_disclosure.py` RED=36 YELLOW=1675 GREEN=11599 SKIP=2830 ·
> exit=0 — 정정 전후 출력이 리포트 타임스탬프 한 줄 빼고 **완전 동일**(슬롯 맞교환이라 Σ(5..11)
> 보존 → rule 2 잔차 ±1 억원 그대로). `validate_data_contract.py` **`BS_KICS_HARD_ZERO` 6→0**,
> NH농협은 `BS_KICS_BASELINE_BREAK` 도 0(총계 36→33, 줄어든 3건 전부 KR0032, 신규 회사 0).
> 정정 후 17BS 잔차 0.001~0.015% = 같은 회사 나머지 11분기(0.000~0.041%)와 구분 불가.
> **전수 서명 스캔**(`item7==0 & item8!=0`, `item9==0 & item10!=0`) 25,522행 → 정정 후 **0 buckets**.
>
> **RED 승격 가능**: 6칸 전부 (a) 확정, 원천 부재 0 건 → `BS_KICS_HARD_ZERO` 축은 면제 없이
> YELLOW→RED 로 올려도 된다(현재 발화 0 이라 push 무영향).
>
> **미처리 2건(의도적, 승인 대기)**: ① `MASTER_XLSX_DRIFT` RED 1건 — K-ICS공시 시트가 12칸 밀렸다.
> 발주에 "마스터 xlsx 손대지 마라"가 있어 `sync_master_xlsx_sheet.py "K-ICS공시"` 미실행.
> ② 골든 입력 지문 RED=4(`kics_disclosure.json` 이 4개 빌더 입력). 이 중 `post_transition`·
> `dividend` 골든은 **직접 돌려 2 passed**(산출 불변). `ifrs17_bs`(~8분)·`pl_breakdown`(~95초)는
> **ifrs17 레인 마스터를 인플레이스 재빌드**하고 `build_pl_breakdown` 은 7,799→2,940행 사고 이력의
> 그 빌더라 kics 레인이 임의 실행하지 않았다. 오프라인 묶음 **93 passed / 1 failed**(실패=위 ①).
> `test_kics_rules_golden.py` 는 통과 — 룰 매트릭스 무변동.
>
> 변경 파일: `kics_disclosure.json`(12칸, 행 수 불변 25522) · 신규 프로브 7종
> `scripts/_probes/_20260920_*.py` · `artifacts/kr0032_render/*.png`.
>
> Last updated (이전): 2026-09-12(15회차 — inbox `20260912T0115Z`(KR0079 2023.2Q MD 결측) + KR0080-2326
> (item23-26 8분기 결측) 2건 직렬 처리, orchestrator 발주) — 둘 다 완료.
>
> **① KR0079 2023.2Q MD 결측**: census 결과 45칸(1-9·11-28·29-46)은 이미 적재돼 있었고 fitz
> 200-230dpi 렌더 9장 대조로 전부 일치 확인(불일치 0). item10(비지배지분)은 원문에 행 자체가
> 없어 미착수(마스터 전체 91/538 버킷이 이미 이 패턴, 정상). item47-54(TFI표) 8칸만 순수
> 결측이라 raw p12 신규 판독 적재(`fix_20260912_kr0079_2023q2_tfi.py`, INSERT 8행, 항등식
> 4종 GREEN). 재변환 1차 시도에서 `--period` 누락으로 `md_inbox/FY2025_Q4/KR0079` 를 일시
> 오염시켰으나 즉시 발견해 정본 재생성으로 복구(다른 파일 피해 없음 mtime 확인).
>
> **② KR0080-2326**: item23-26 8분기 결측 중 **7분기 disclosed-zero 확정**(fitz 200-600dpi
> 렌더 직접판독, 2025.4Q 는 발행사 템플릿 결함 발견 — 부모행이 가.지급여력금액을 오복제,
> 자식행은 깨끗해 부모 자신의 산식(1+2+3)으로 0 역산). **1분기(2024.2Q)는 원문 자체가 해당
> 분기 열만 완전 공백**이고 어떤 후속 보고서 이력창에도 재등장 안 해 교차검증 불가 —
> 0 추정 대신 미착수. `fix_20260912_kr0080_2326_other_capital.py`, INSERT 28행. 게이트
> `other_capital_children_sum` 축 적용전:부모결측 21→14(-7)·적용후 27→20(-7), 다른 축 무변동.
>
> **게이트/테스트 실측**: `validate_kics_disclosure.py` RED=36(불변, 전부 documented
> exception)·**blocking RED=0**. `validate_data_contract.py` xlsx sync 전 RED=1(MASTER_XLSX_
> ROW_MISSING, 예상된 일시상태) → `sync_master_xlsx_sheet.py "K-ICS공시"`(25486→25522행) 후
> **RED=0**. `pytest tests/test_kics_rules_golden.py tests/test_post_transition_golden.py
> tests/test_rule_coverage_manifest.py` 1건 실패(골든 sha256, 36셀 신규 적재로 당연히 이동)
> → `--update` 재생성(RED=36 불변 확인 후) → **85 passed**. `validate_golden_input_
> fingerprints.py --update` 실행.
>
> 변경 파일: `kics_disclosure.json`(+36행) · `insurequant_master_tables.xlsx` · 신규
> `scripts/fix_20260912_kr0079_2023q2_tfi.py`·`scripts/fix_20260912_kr0080_2326_other_
> capital.py` · `tests/fixtures/{kics_rules_golden,builder_input_fingerprints}.json`(재생성) ·
> `md_inbox/{FY2023_Q2,FY2025_Q4}/KR0079_미래에셋생명.md`(신규/복구).
>
> Last updated (이전): 2026-09-11(14회차 — inbox 3건 직렬 처리: `20260831T0705Z`(item48/item3 오염
> REOPEN) → `20260901T0420Z`(SCANNED_SECTION 부수관찰 REOPEN) → `20260911T1407Z`(stale-quarter
> 테스트 파손), orchestrator 발주) — 전부 `status: answered`, 원 sender 재확인 대기.
>
> **① item48/item3 오염 잔여 4셀 정정** (2026.2Q). KR0003 28741→10555.5 · KR0011 124792→
> 57549.42 · KR0029 754→1389.83 · KR0094 59367→26880.72(값_적용후는 이미 정답이라 무변경).
> `scripts/fix_20260821_tier2_limit_lines.py::extract_tier2()`(fitz)와 MD grep 두 독립경로로
> 재확인, 둘 다 오케스트레이터 제시값과 일치. 오염 주입점은 커밋 `8f5e3b8`(09-01, 39사 전원
> 적재)까지만 blame 으로 좁혔고 정확한 스크립트는 특정 못 함(현재 정본 추출기 둘 다 재실행하면
> 정답을 낸다 — 당시 코드가 이미 고쳐졌거나 세션 로컬 patch였던 것으로 추정). 대신
> `fill_tfi_table_to_disclosure.py`의 item48 자체검산이 item14 미로드 시 무검증 통과하던
> fail-open 구멍을 fail-closed 로 고침(`scripts/fix_20260911_item48_item3_contamination.py`).
>
> **② KR0079 TFI 3분기 24셀 백필 적용 + DATA 오기 1건 정정**. 2026-09-01 답변이 만들어 둔
> `scripts/fix_20260901_kr0079_scanned_section_tier2.py`를 `--apply`하기 전, item54
> 2023.4Q DATA 값 496.50 이 옆 회사(KR0071) item53 값이 새어든 오기임을 raw p36 재렌더로
> 확인 → 3003.59 로 정정 후 적용(INSERT 24, 항등식 4종 3분기 전부 GREEN). 부수 관찰 3건 중
> 2건 처리(KR0010 2025.4Q item8 "" →"0", KR0071·KR0010 item53/54 신규 4셀 — 전부 190dpi
> 렌더 직접판독, 신규 스크립트 `scripts/fix_20260911_side_observations_tier2_item8.py`).
> KR0080 item23-26 는 8분기×4항목=32셀 규모로 재스코프만 하고 미착수(아래 KR0080-2326 항목).
>
> **③ stale-quarter 테스트 6건 파손 — 회귀 아님, 데이터가 진짜 고쳐진 것.** `git show
> 7c33aae:kics_disclosure.json`(09-03 재제출 반영 직전 스냅샷)에 `validate_stale_quarter_
> tables.detect()`를 돌려 그때는 지문 A가 실제로 잡히는 것을 확인(탐지기 생존 증명) — 현재
> 마스터는 전사 히트 0건(대체 등재 불가). `_KNOWN`을 비우고 `test_stale_quarter_tables.py`의
> 라이브-히트 시험을 KR0003 2026.1Q 의 옛 오염 패턴을 사본에 합성 주입하는 변이시험으로 전환.
> `test_tier2_issuer_inconsistent_exemption.py` 의 죽은 핀 4개(파라미터 2건 삭제·2건은
> KR1000/2023.4Q·KR0087/2025.2Q 로 대상 이동) + 레지스트리 카운트 20→19(실측 확인) 정정.
> **부수로 `test_kics_rules_golden.py::_run()` 자체 버그도 발견·수정**했다 —
> `validate_kics_disclosure.py::main()`이 넘기는 4개 부수입력 중 `life_subrisk_source_absent`
> 가 누락돼 있어, 그냥 `--update`만 했으면 골든이 실제 게이트 산출(RED=36)과 다른 값(RED=60,
> `8_life_census` 2023 홀수분기 24버킷)으로 잘못 고정될 뻔했다 — 인자 추가 후 재생성해 RED=36
> 으로 게이트와 완전히 일치.
>
> **게이트/테스트 실측**: `validate_kics_disclosure.py` RED=36(불변, 전부 documented
> exception)·**blocking RED=0**. `validate_data_contract.py` **RED=0** YELLOW=88.
> `pytest tests/test_stale_quarter_tables.py tests/test_tier2_issuer_inconsistent_exemption.py
> tests/test_kics_rules_golden.py tests/test_rule_coverage_manifest.py -q` → **179 passed,
> 1 failed**. 실패 1건(`test_gold_overlay_census_matches_manifest`, CSM/PL gold overlay
> census)은 **ifrs17 레인 소관 — 이 세션이 시작하기 전부터 `CSM_waterfall.json`·
> `IFRS17_BS.json`·`data/_gold/user_csm_cells.json` 가 이미 수정 중이었다**(`git status`로
> 확인, 동시 ifrs17 세션의 미커밋 작업) — 두 번 재실행 사이에 PL 버킷 수(198→203)가 더
> 늘어난 것으로 활성 편집 중임을 재확인, K-ICS 코드/데이터는 원인이 아니고 건드리지 않았다.
> `sync_master_xlsx_sheet.py "K-ICS공시"` 실행, 검증 OK(25486행×9열 마스터와 완전 일치).
>
> 변경 파일: `kics_disclosure.json`(6셀 수정+28행 신규) · `scripts/fill_tfi_table_to_
> disclosure.py`(자체검산 강화) · `scripts/fix_20260901_kr0079_scanned_section_tier2.py`
> (DATA 오기 정정) · `scripts/validate_stale_quarter_tables.py`(`_KNOWN` 비움) ·
> `tests/test_stale_quarter_tables.py`·`tests/test_tier2_issuer_inconsistent_exemption.py`·
> `tests/test_kics_rules_golden.py`(+골든 재생성) · 신규 `scripts/fix_20260911_
> item48_item3_contamination.py`·`scripts/fix_20260911_side_observations_tier2_item8.py`.
>
> Last updated (이전): 2026-09-11(13회차 — inbox `20260831T0700Z`(REOPEN iter4) + `20260831T0800Z`
> §1 잔여 코드 처리, orchestrator 발주) — `kics_disclosure.json`은 읽기 전용(동시 세션이 셀
> 패치 적재 중)으로 유지, 코드·MD·SKILL 문서만 수정.
>
> **A. `--stage quality` AttributeError 복구.** `run_harness.py` L89가 읽는 `r.page_flags`를
> `QualityReport`(`src/solvency/parser/quality_check.py`)가 가진 적이 없어(다른 레인 커밋
> `09b4b26`이 kics 코드를 같이 실어나르며 추가한 블록) 모든 실행이 exit 1이었다. `QualityReport`에
> `page_flags: list[str]` 필드를 신설하고 `score()`가 `missing_window=<label,...>`/
> `ratio_critical=<ratio>` 형식으로 채우도록 수정. 실측: `run_harness.py --stage quality
> --md-root md_inbox/FY2026_Q2` exit 0, total=39 accepted=9 review=30, `page_flag_counts:
> {missing_window: 5}`(KR0079·KR0087·KR0095·KR0104·KR1010 — orchestrator 재확인 수치와 정확
> 일치). 전체 md_inbox(547개) 대상도 exit 0(review=407, flags 213건=missing_window 211+
> ratio_critical 7). `pytest tests/unit/ tests/test_deploy_assets.py` 141 passed.
>
> **B. census "32/39" 재현.** `probe_20260901b_market_window_census.py` 메인 트리 재실행 결과
> 재확인 티켓의 지적대로 31/8(REAL GAP 0)이었다 — KR0104 재변환 MD가 이미 삭제된 격리
> 워크트리에만 있었기 때문. `run_harness.py --stage parse --pdf-root data/disclosure/
> FY2026_Q2/raw --companies KR0104`로 메인 트리에서 재변환(187s, docling_status=SUCCESS,
> dropped_pages=[]) — mtime 대조로 md_inbox/FY2026_Q2 39개 파일 중 KR0104 1개만 변경 확인.
> source_page_ranges "6-10;13-28;34-37;40-46"→"6-10;13-36;43-46"으로 29-33p 편입, 재추출
> item36-40 5개 전부 마스터와 정확 일치(13866.27/7712.89/2818.93/3487.39/0), sqrt(V'MV)=
> 19271.87 vs item19=19272 rel 0.0007%. census 재실행 결과 **32/39 MD_FULL, landmine 7**
> (KR0010·KR0079·KR0080·KR0082·KR0087·KR0094·KR0099) — 답변 주장과 일치, 정정 불요. 구MD는
> `artifacts/kics_validation/md_backup_20260911/`에 백업. `kics_disclosure.json` 미접촉.
>
> **C. OCR 배율 판단 재확인 + 실행.** 2026-09-01 결정(정식 옵션 승격도 fitz+EasyOCR 우회도
> 안 함, fitz 렌더+직독으로 완전 대체)을 재검증 후 유지 — 이유는 스캔본 코드 트레일에 이미
> 있었으나 SKILL 문서에는 없었다(재론 2회 원인). `.claude/skills/kics-parser/references/
> quirks-and-traps.md`에 "Scanned PDFs: OCR is a lead, not a source" 절 신설(5/9 배율표 +
> 결정근거 + render_kics_page.py 안내 + "MD 텍스트만으로 마스터에 쓰지 말 것" 규칙) +
> "Docling loses pages" 가드 절의 stale 서술(`page_selection_flags()`/6종 enum 플래그 —
> 09-01 리라이트로 이미 소멸된 이름들) 정정. `compute_tier2_utilization.py`의 `MD_DIR`
> 하드코딩(FY2025_Q4)은 실측 0곳 import·subprocess(grep 전체 무출력) 확인 후 latest-quarter
> 자동탐지로 교체(`_latest_md_period()`, `md_inbox/FY*_Q?` 최댓값) — 명시 `--quarter`/
> `--md-dir` 경로는 git stash 전후 산출 diff 0으로 무영향 확인, bare 실행만 FY2025_Q4→
> FY2026_Q2로 개선.
>
> 재현: `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/run_harness.py
> --stage quality --md-root md_inbox/FY2026_Q2` · `scripts/_probes/
> probe_20260901b_market_window_census.py`. 상세 답변: inbox `20260831T0700Z`(iter4) ·
> `20260831T0800Z`(iter2).
>
> 📦 **Status 이력은 `docs/todo_archive_parser_kics.md` 로 이동했다** (2026-09-11, 내용 무수정 — 2026-09-01(9회차) 및 그 이전 항목). 세션 시작 시 읽지 않는다; changelog 처럼 특정 과거 결정의 배경이 필요할 때만 연다. **이 Status 는 최신 5개 항목만 유지**하고, 밀려난 항목은 그 파일 헤더 바로 아래에 그대로 잘라 붙인다.


Stage 2 — **parser, K-ICS lane**: solvency disclosure extraction. Source = Docling MD; output = `kics_disclosure.json`; validators = `validate_kics_disclosure.py` / RS1–4 / market census. The IFRS17 lane (CSM/PL extraction off DART XML) lives in `TODO_parser_ifrs17.md` and runs as a separate session.

Session start: read this file + `docs/agents/claude-agent-parser.md` + `docs/domains/claude-agent-kics.md`. English where Korean encoding is fragile (see `CLAUDE.md`).

## 🔴 Open — P1

### TRANS-18 — 경과조치 적용후 정본 18사, `transition_ratio_after_capture` 12셀 최종 (2026-07-07 마감)

정본 = FSS 2023-03-20 보도자료 붙임-1 → elective 경과조치 실제 적용 **18사**:
- 생보12: 에이비엘(KR0070)·흥국생명(0071)·케이디비생명(0072)·교보생명(0073)·아이엠라이프(0076)·DB생명(0082)·푸본현대(0083)·하나생명(0097)·처브라이프(0100)·교보라이프플래닛(1010)·IBK연금(1011)·농협생명(0104)
- 손보6: 악사손해(0049)·한화손해(0002)·롯데손해(0003)·예별손해(0004)·흥국화재(0005)·NH농협손해(0032)
- **나머지 전사(코리안리·메리츠·삼성생명·한화생명·신한라이프·KB라이프·동양생명 등) = 공통(TFI)만 → 적용후=적용전이 정상, 건드리지 말 것.**

**최종 12셀 = 전부 "더 파싱해도 안 바뀜"**(라이브 게이트 `transition_ratio_after_capture` 기준):
- **원천 미공시 7셀**(raw에 표 자체 없음): 흥국화재 2024.4Q(2)·악사손해 2024.3Q(2)·에이비엘 2025.3Q(1)·흥국생명 2024.4Q(1)·푸본현대 2023.1Q(1).
- **게이트 마진 오탐 5셀**(COPY, 소액/음수인접사의 진짜 개선폭을 반올림복사로 오판): 예별손해 3·롯데손해 1·IBK연금 1 → **validation 마진로직 재검토**(파서가 데이터 더 고쳐도 안 바뀜).
- 흥국화재·흥국생명 2024.4Q = raw 오염(정기경영공시서 아닌 사업/감사보고서 오수집) → downloader 발주됨.
- rule_8_post 3건(흥국생명·푸본현대·에이비엘) = item2후를 None으로 정직 유지한 셀에서 검증기 폴백버그 노출 → validation 로직 이슈(파서 소관 아님).

날짜별 라운드 상세(139→90→42→13→12) + 18사 확정 왕복 이력 → `docs/changelog_parser_kics.md` 2026-07-07.


### LOCALIZER-FITZ — 시장위험 localizer pdfplumber EOF 무음실패 → fitz fallback (2026-06-14)

**DONE**: `extract_market_section_pages.py`에 pdfplumber→fitz fallback 추가(EOF-PDF DB손해 24.4Q·NH 25.4Q ERR→OK). 상세 → changelog.
- [ ] (validation 측) ERR/NO_SIGNAL을 'TOOLING_FAIL' census 버킷으로 분리 — localizer 안착 후 wire-up(inbox/validation 합의). parser는 선결조건 해소.


### GOLD-CHAIN — review-loop 영속화 정합 + backfill 스크립트 체인 편입 (2026-06-20, inbox 0811Z)

owner xlsx fill·내 backfill이 rebuild에서 살아남는지 점검 → 2대 사각 (메모리 [[reference_kics_gold_reviewloop]]).
- [x] **DONE 2026-06-20**: owner image-OCR fill(카카오 KR1098 2023.4Q/2024.4Q·AIA KR0080·한화 KR0068 it37)을
  durable gold(`data/_gold/user_kics_cells.json`)에 영속화(+90셀, `append_owner_image_fills_to_gold.py`) +
  stale-gold 1건(한화 it37 45096.51→58590.96, owner 수정 클로버 차단) `reconcile_gold_to_xlsx.py`로 정합.
- [ ] **backfill 스크립트 rebuild 체인 편입**: `backfill_life_subrisk_positional.py`·`_from_pdf.py`·시장하위
  backfill이 `fill_*→apply_user_kics_gold→recalc` 체인 밖 → from-scratch 재빌드 시 미재현(+155 life-subrisk 등 소실).
  체인 러너(or 문서)에 `fill_market_*` 다음·`apply_user_kics_gold` 앞 단계로 편입. 현재는 커밋에만 존재.
- [ ] **gold git 추적 결정**: `user_kics_cells.json`은 현재 untracked(머신-로컬) — 다른 세션/머신 rebuild 시
  owner fill 소실. 추적 여부 owner 확인(민감정보 아님, 추적 권장).

### DEDUP — kics_disclosure 중복 행 slice (발견 2026-06-12, changelog (s))

`(원보험사코드, 공시분기, 항목번호, 항목명)` 중복 **94키 (값 상이 65키)** — 예: KR0001 2023.1Q item26 ×13, item12 값 {257, 32, 68431}. 과거 fill 누적 잔재. fill의 (code,item,name) index와 validator 입력이 어느 행을 읽느냐에 따라 흔들리는 잠복 리스크.
- [ ] dedup 스크립트: 같은 키 그룹 → 정답 판별(MD 재추출 대조 우선, 불능 시 최빈/최신) → 1행만 유지.
- [ ] fill_period에 신규-행 삽입 전 동일키 존재 가드 추가(이름 변형이 아닌 진짜 중복 차단).
- [ ] validation에 룰 입력의 중복 반응(first/last/any) 질의함 — inbox 20260612T1100Z 4).
- NOTE: FY2023_Q1 `--refresh` dry-run에서 메리츠 item12 257→68431 오매칭 신호도 관찰 — dedup 후 해당 라벨 매칭 재점검 (refresh는 그 전까지 금지).

### NEW-1 — 시장위험 하위(item36-40) 추가 backfill (inbox 20260612T0900Z 신규-1 + 20260611T2200Z systemic)

소스 MD에 5종 세부표(자산집중위험 행) 있는데 JSON 미적재인 (사,분기). validator는 "전사적 미파싱"으로 승격(19_market SKIP→RED). 분절표(`<!-- image -->`) 봉합 + 라벨변형(`(\d\.)?\s*(금리|주식|부동산|외환|자산집중)\s*위험(액)?`) + 값셀 탐색(방법 텍스트 다음 숫자).
- [x] **(종결 2026-08-20) 36-40 재추출** — 주장 224건은 stale. 실측: item19 보유 484 (사,분기) 중 36-40 결측 144건인데 **133건이 홀수분기**(세부표는 짝수분기 공시가 표준 = 구조적 정상). 진짜 후보는 **짝수분기 11건뿐**이고 KR0051(1)·KR0079 미래에셋(6)·KR0080 AIA(4) — 전부 이미지/스캔 원천으로 아래 KICS-IMG 코호트와 동일. 원래 남은 항목: gold anchor: 하나손해 2025.4Q(시장 76,839 / 금리 30,358 / 주식 62,491 / 부동산 2,643 / 외환 12,483 / 자산집중 5,251 백만원) + 삼성생명 2025.4Q. 도구 `fill_market_subs_from_pdf.py`(words-coordinate 전략) 또는 MD 분단표 합치기. **게이트: 19_market 행렬합 rel<2%** 통과분만 적재. 생보도 동일 스캔 후 일괄.
- [ ] 진짜 미공시 (사,분기)는 raw 표 부재 명시 회신 → validation `MARKET_BREAKDOWN_EXEMPT` 등록.
- [x] **(종결 2026-08-20) 2026.1Q 29-46 backfill** — 실측 **20사가 29-46 보유**('전무' 주장은 stale). 원문:(8_life 29-35 + 시장위험 36-46) → 29-46 backfill.
- [x] **(종결 2026-08-20) census 미싱셀** — 게이트 실측 `MISSING_CELLS(RED)=2`(28건 주장은 stale). 원문:(MD parsed인데 JSON 추출 누락): 미래에셋 7분기·코리안리 6분기·동양·하나생명 등 + 2026.1Q 6사(한화손해·롯데손해·삼성화재·하나손해·미래에셋·동양). 명단 inbox 20260611T2200Z.

### NEW-2 — 생보 경과조치 적용후 요구자본 20건 → 2026-07-07(9차)로 18사 일괄 적재, 상위호환 완결. 잔여 3사(예별·흥국화재·흥국생명)는 TRANS-AFTER-9 참조.


### TRANS-AFTER-9 — 적용후 잔여 3사 + item12 셀밀림 (2026-07-07, 9차 후속)

9차(`fill_post_transition_to_disclosure.py` 4버그) + 후속 라운드로 R1 53→0(TAC 도출 `_extract_tac_amount` 신설)·mmult 5→4·**item12 셀밀림 154→0**(labels_compatible 대칭가드 + 퍼센트파싱 + 8개 근본버그 + raw 수기 2건). 완결 상세 전부 → changelog 9차. 잔여 open 2:
- [ ] **R5/R6/mmult 51+4건, 예별손해(KR0004)·흥국화재(KR0005)·흥국생명(KR0071)**: 3사가 ③(주식·금리) 또는 시장위험 36-40 세부도 동시 적용인데 이 스크립트 스코프 밖 → 총괄표 파싱 실패 시 부분치 폴백으로 항등식 안 닫힘. ③표 파싱 또는 36-40후 추출(F12/NEW-1 계열) 필요, validation에 스코프 확장 발주(`inbox/parser/20260707T0600Z`).
- [ ] **DEDUP 선행**: 라이브 `--refresh --all-periods`는 고정밀 파생값 손실 부작용 → DEDUP(94중복키) 해소 전까지 전면 실행 금지. scratch-리다이렉트+방어적 병합이 표준 우회로.


### GOLD-SCAN — owner gold 필요 (이미지 스캔 PDF, 2026-06-12 확정)

자사+협회 모두 이미지 스캔 — 텍스트 추출 불가, KB(KR0010) xlsx-gold 전례 경로 권고:

> **⚠ 2026-08-30 실측 — 이 절은 낡았다.** 세 회사 모두 13개 분기 전부에 데이터가 있다
> (분기당 값 있는 항목: KR0079 21~46 · KR0080 28~53 · KR0087 29~54, 홀수분기가 적은 것은
> 정상 공시주기다). 항목1/14/27 은 세 회사 39셀 중 **결측 0**이고 `validate_kics_disclosure`
> 는 **RED=0 exit 0**이다. 즉 '이미지 스캔이라 못 넣었다' 는 더는 현황이 아니다.
> 다만 아래 세 줄이 정확히 어느 셀을 가리켰는지는 이 문서만으로 특정되지 않아 임의로
> 체크하지 않는다 — 남기려면 그 셀을 명시하고, 아니면 지워라.
- [ ] KR0079 미래에셋생명 — 전 구간 (기존 KICS-IMG 항목과 동일 코호트).
- [ ] KR0080 에이아이에이생명 — 2024.4Q~2026.1Q (2023.1Q~2024.3Q는 텍스트 있어 적재 완료, 신규 편입).
- [ ] KR0087 동양생명 — 2026.1Q만.
- [x] **(종결 2026-08-20) KR0049 악사손해 2026.1Q** — '게이트 잔여 RED 4건' 주장 stale. 현재 RED=12는 KR0087·KR0097·KR0079 셋뿐이고 **악사는 없다**(`TODO.md` L10).

---

## 🟠 Open — P2

### MARKET-P2 — 시장위험 Phase-2 잔여 (after 2026-06-09 (e), 정당/후속)

- [ ] **19_market 구조적 SKIP ~100** (삼성화재 전분기·삼성생명·현대해상·한화생명): PDF에도 하위5종 비공시 = 정당 SKIP, RED 아님 (NEW-1과 분류 확정 필요).
- [ ] **36_irr Q1/Q3 ~85**: 분기보고서에 시나리오표 원천부재 = 구조적 SKIP.
- [ ] **IRR 직접형/granular 15** (KR0097 하나생명·KR1010 교보라이프·KR0051 신한이지): derived≠item36 → 직접공시 시나리오위험액 별도 schema 필요(저장 보류, SKIP 유지).
- [ ] **PDF 레이아웃 미스** (하나손해 2024.x 등): interleaved/grouped/concat fallback에 words-coordinate 전략 추가.
- [x] **KB손해 image-only 4분기** — 위 KICS-IMG 와 같은 건, 결측 0 으로 닫힘(2026-08-30 실측).

### KR0080-2326 — 에이아이에이생명 item23-26 8분기 결측 (종결 2026-09-12)

- [x] **KR0080 item23-26(기타요구자본 세부) 8분기×4항목=32셀 결측** — fitz 200-600dpi 렌더
  직접판독으로 **7분기 disclosed-zero 확정**(2023.2Q·2024.4Q·2025.1Q·2025.2Q·2025.3Q·
  2025.4Q·2026.1Q, `fix_20260912_kr0080_2326_other_capital.py --apply`, INSERT 28행) +
  **1분기(2024.2Q) 원문 자체 해당분기 열 공백이라 SKIP**(교차검증 불가, 추정 미적재). 상세
  근거·페이지·2025.4Q 발행사 템플릿 결함(부모=가.지급여력금액 오복제, 자식은 깨끗해 산식
  역산) → `docs/changelog_parser_kics.md` 2026-09-12.

### FY2026Q1 — K-ICS PDF→MD docling 잔여 (inbox 20260612T0900Z)

- [ ] **FY2026_Q1 K-ICS PDF→MD docling** (`data/disclosure/FY2026_Q1/raw/` → md_inbox; 일부 대형 PDF std::bad_alloc) → 금리민감도·시장하위 추출기 재실행으로 흡수.

### F12 — K-ICS 시장위험 하위위험액 전체 파싱 (parser side)

Cross-stage feature (root `TODO.md` keeps a 1-line ref; full detail here). Parser + validation cross-stage. 화면 노출 X, 데이터 신뢰용. Validation half = V3 in `TODO_validation.md`.
- [x] 시장위험 하위 5개 추출 — **닫힘 (2026-08-30 실측)**: 항목36~40 각각 **356/488 버킷**에 값이 있다(73%). 나머지 132 는 아래 '19_market 구조적 SKIP ~100' 에 이미 등재된 비공시 구간이다. 미착수가 아니라 커버리지 상한에 도달한 상태.
- [ ] 금리위험액 (+5쇼크 순자산 민감도 = 듀레이션갭) display-ready 필드 분리
- [ ] 출력 schema에 `market_risk_breakdown` 신설 → validation R11 sqrt 정합성 룰의 입력

---

## 🟡 Open / waiting

- [x] **(종결 2026-08-20) RS1–4 룰** — `TODO.md`에 *"validation: RS1–RS4 룰 구현, 게이트 RED=0"*로 이미 완료 기록됨(2026-06-10). 원문: 마스터 ready 회신 = `inbox/validation/20260610T0830Z__parser__ALL__rate_sensitivity_master.md`. (RS1-4는 통과했으나 정식 룰 구현 확인 잔여.)
- [x] **MLG-2 시장위험 분해 — 닫힘 (2026-08-30, owner 확인)**. owner: "금리위험 하위위험 산식은 니가 전에 했잖아". 실측으로 확인: 유도식이 `kics_json_rules.irr_derive_expected` 에 구현돼 있고 `validate_kics_disclosure` 가 **적용전·적용후 양쪽 다** 돌린다 — `item36 = sqrt(max(R상승,R하락)² + max(R평탄,R경사)²) + R평균회귀, R = item41 − 시나리오`. 실측 판정: 적용전 grid 226/226 평가 100.0%, 적용후 118 중 107(90.7%), **불일치 0건**. 하위 5종(36~40) 추출도 356/488. 즉 'owner 결정 대기' 가 아니라 **이미 끝난 것**이었다. 종전 문구 — — 하위 5종 추출은 위와 같이 완료(356/488). 남은 것은 **금리 유도규칙 owner 결정 + R11 sqrt 정합성 룰**뿐이다. 종전 문구 — (owner 결정): PL-Tier2급 사별 핸들러 + 금리 유도규칙 owner 결정 필요. R11은 금리 확정 후. [xref: parser-ifrs17] (PL-Tier2급 핸들러 패턴은 IFRS17 lane이 owner; 본 항목은 시장위험액이 1차 데이터라 K-ICS lane 소관.)
- [ ] **IFRS-NORMALIZE** — 23-co full normalization: `row_aliases.yaml` 확장(현 PoC 930/2956 tagged) + K-ICS sensitivity 잔여 empty FY2025_Q4 생보사 normalize. (K-ICS sensitivity normalization이 1차; IFRS17 lane도 row_aliases.yaml 공유하므로 [xref: parser-ifrs17].)
- [x] **KICS-IMG** — **닫힘 (2026-08-30 실측)**: KR0010 KB손해·KR0079 미래에셋생명·KR0080 에이아이에이 세 회사의 항목1/14/27 을 전 분기(13분기) 전수 조회한 결과 **39셀 중 결측 0**. OCR 경로 없이 해소됐다. 종전 내용은 아래 보존 — — image-only PDF manual OCR: KR0010 KB손해(rule 2 ×2)·KR0079 미래에셋생명·KR0080. 정책: parser는 image-only 만나면 escalate, OCR 즉흥 금지 (`claude-agent-parser.md` §2.1). (KR0010은 2026-06-11 (r)에 owner gold로 RED=0 달성.)
- [ ] **REFACTOR-3 slice2 — PARKED (owner-gated, 2026-06-14)**: `make_quarter_column_picker` / `_canonicalize_table_label` 등 파라미터화 로직을 `company_handlers.REGISTRY[code]` dict-dispatch로 흡수. **착수 조건 = 진짜 KR-keyed 노브(column-picker quirk·값 reconcile 등)가 실제 발생할 때.** 현재 `src/`에 `if code==KR` 분기 0개(확인) → 지금 추출은 over-engineering(정적 config 아닌 predicate 로직). slice1(레지스트리)+DEDUP-1/2+GOLDEN-E2E(csm)는 완료 → changelog_parser_kics 2026-06-14. 원 스레드 inbox `_resolved/20260613T0200Z__owner__ALL__parser_refactor.md` (resolved).

---

## ✅ Done (archive)

One line per finished item. Full story in `docs/changelog_parser.md` + git. (Pre-split combined archive; K-ICS-lane items only — IFRS17-lane done items moved to `TODO_parser_ifrs17.md`.)

- K-ICS 금리민감도 추출 — `extract_kics_rate_sensitivity.py` → `kics_rate_sensitivity.json` 423행, RS1/RS2 pass — 2026-06-10 (changelog 2026-06-10)
- BNP(KR0075)/코리안리(KR1000) FY2025 재파싱 — docling v4 페이지선택 수정, +12행, RS4 hole=0 — 2026-06-10 (changelog (b))
- KB손해(KR0010) owner gold cell 적재 — `apply_kr0010_gold.py`, RED=0 최초 달성 — 2026-06-11 (changelog (r))
- 값_적용후 정합 2건 + recalc 분모버그 — 농협생명·삼성화재 + den14=post14 — 2026-06-11 (changelog (p))
- 2026.1Q 36/39사 적재 + MG/AIA 신규 편입 + 파서 버그 2건 — `append_kics_detail_from_pdf.py`·`seed_new_companies.py` — 2026-06-12 (changelog (s))
- 시장위험 하위분해 적재 (items 36–46) — `fill_market_subitems_to_disclosure.py`, +1,449행 — 2026-06-09 (changelog (c))
- 시장위험 커버리지 census + Phase-2 PDF 추출 — 36-46 복구 +150행, RED 0 — 2026-06-09 (changelog (d)·(e))
- K-ICS parser: split-table + row scope + Q4 reparse + KR0069/KR0097 fixes — 2026-05-24 (changelog archive)
- K-ICS RED reduction passes (419→311→217) + sub-items 29-35 + 값_적용후 historical — 2026-05-24/25 (changelog archive)
- Unit-hint mismatch auto-detect — 23 insurer-quarter latent bugs, 56 post 보정 — done (UNIT-HINT)
- B5-APPENDIX K-ICS sensitivity appendix headings + multi-period batch — 2026-05-25 (B5-APPENDIX)
- Pipeline foundation (Docling PDF→MD, 협회 파서 1차, kics_disclosure.json) — 2026-04-25~28 (changelog archive)

---

## Reading order for parser subagent (K-ICS lane)

1. This file (`TODO_parser_kics.md`) — open work + done archive
2. `docs/changelog_parser.md` — history (pre-split combined)
3. `docs/agents/claude-agent-parser.md` — master prompt + per-domain contract
4. Domain ref: `docs/domains/claude-agent-kics.md` for label variants and company quirks
5. Root `TODO.md` only for cross-stage items (F12) — full detail lives here
6. Sibling lane: `TODO_parser_ifrs17.md` (CSM/PL extraction) — for [xref] items

## Hand-off to validation

After parser produces normalized `kics_disclosure.json`, validation is invoked per `docs/agents/claude-agent-validation.md` §3 (retry loop, max 5). On RED, validation calls back the parser with the failing rule + suspected source.
