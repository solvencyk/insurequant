# Insurequant Parser TODO — K-ICS lane (Stage 2)

> Last updated: 2026-08-29(2회차) — 같은 inbox `20260829T0100Z` 코디네이터 검토 후속: 스키마·
> 검증 전부 통과 확인 + **`기본자본소진율` 시트 100%초과 13행 비고 보강**. census 재확인
> (`probe_20260829b_tier1_strict_list.py`): `utilization_pct`>100 6개사(NH농협192.9·
> 하나생명187.0·하나손해144.1·코리안리139.8·한화생명138.5·KDB113.4) + `utilization_pct_strict`
> >100 7개사(위 6개사+교보생명, primary=79.4인데 strict=119.1인 "엄격만 초과" 케이스) = 정확히
> 13행. `_flatten_tier1`에 `_TIER1_BASIS_NOTE`(SCR×15%대SCR×10%로 엄격이 1.5배라는 상시 설명,
> 소진율 관련 78행 전체) + `_TIER1_OVER100_NOTE`(파싱오류 아님·화면 100%+ 표기, 값>100인 13행에만
> 조건부 부착) 신설 — 근거는 `docs/tier1_hybrid_utilization_definition.md`(owner 2026-06-14/
> 2026-08-25 결정)를 그대로 인용, 하드코딩 회사목록 아니고 flatten 시점에 직접 판정. 검증
> (`probe_20260829c_tier1_note_check.py`): 78행 빈 비고 0·13행 전부 문구 포함·오탐 0. xlsx sync
> "기본자본소진율" 만 재실행(변경 셀 78·추가/삭제 0, EDIT만이라 항목명=행식별키 불변), 검증 OK·
> 3시트 재-dry-run 전부 idempotent. `git add`(내 파일만)+커밋 완료(push 안 함). 상세는
> `inbox/parser/20260829T0100Z...md` `## 답변 추가` 절.
>
> Last updated (이전): 2026-08-29 — inbox `20260829T0100Z`(orchestrator, 자본 마스터 3종
> xlsx 편입) 드레인: 1단계 설계 보고 도중 코디네이터가 owner 승인 스키마를 전달하며
> 2단계 구현까지 지시 — 같은 세션에서 이어 처리. **`insurequant_master_tables.xlsx`
> 에 신규 시트 3개 추가**(`기본자본소진율` 390행·`보완자본소진율` 546행·`자본비율전망`
> 2090행, 합계 49,570행) — `kics_tier1_utilization.json`/`kics_tier2_utilization.json`/
> `kics_forward_capital.json` 을 기존 8시트와 동일한 long-format(원보험사코드·원수사명·
> 티커·생손보여부·공시분기·항목명·값 + 신규 `비고`)으로 flatten. `build_master_xlsx.py`
> 는 **실행 안 함**(MASTERS 에 3항목 추가 + flatten 함수만 정의) — 반영은
> `sync_master_xlsx_sheet.py` 로만(신규 시트 생성 지원을 새로 추가: 이전엔 기존 시트
> cherry-pick 전용이라 `wb[sheet]` 가 KeyError 났음). 3회 sync 전부 자체 사후검증
> ("나머지 시트 값 동일") 통과 + 재실행 dry-run 0 drift 확인, 동시작업 중이던
> `손익분해PL`(ifrs17 레인) 무손상.
>
> **중요 발견**: 원 티켓의 "tier2 4개사 이상치(분자 파서 추출 불안정)" 전제가 **stale**
> 로 실측됨 — `output/tier2_utilization/outlier_report_20261Q.json`(2026-06-16)의
> 5개사(동양240%/하나손해235%/KB218%/악사197%/미래126%)를 가리키는데, 이미
> `inbox/_resolved/20260620T0238Z`(owner)에서 분자를 DART 채권별 발행잔액으로 교체해
> 해소됨. 라이브 게이트(`validate_data_contract.py` CHECK4 도메인identity)·직접 census
> 둘 다 현재 tier2 utilization_pct 이상치 **0건** 확인(39개사 전부 0~100% 안). 없는
> 4개사를 지어내지 않고, 대신 census 로 실제 살아있는 한계(tier1 issued_source=missing
> 7개사, forward 콜옵션미공시폴백 20개사·저신뢰 14개사·DART무자료 11개사, 서울보증보험
> forward_capital 결측 신규발견)를 시트 `비고`열에 실었다. status: answered(owner/
> orchestrator 가 "4개사" 전제·서울보증보험 갭 재확인 필요). 상세:
> `inbox/parser/20260829T0100Z__orchestrator__MULTI__capital_masters_into_xlsx.md`
> `## 답변` 절.
>
> Last updated (이전): 2026-08-28 — 채팅 발주(owner, designer 세션 경유): KR0097(하나생명보험)
> 2024.2Q 원수사명 오철자 "하나생명" → "하나생명보험" 정정, 40셀. K-ICS 드롭다운에 같은
> 회사가 두 줄로 뜨는 걸 owner가 지적 → 조사해보니 단순 표시 중복이 아니라
> `K-ICS.html:getFilteredData()`의 `row['원수사명'] === company` **완전일치 필터** 때문에
> 실제로 "하나생명보험"(13개 분기)을 선택하면 2024.2Q 한 분기가 화면에서 통째로 빠지는
> 사일런트 결측이었음. 다른 12개 분기가 전부 "하나생명보험"이라 오탈자로 판단, raw 재대조
> 없이 다수결로 정정(다른 12분기와 100% 동일 회사·형식이라 모호성 없음). 게이트 재확인
> RED=0(blocking) 불변, main 배포 완료. 상세: [changelog_parser_kics.md](docs/changelog_parser_kics.md#2026-08-28).
>
> Last updated: 2026-08-25(20회차) — inbox `20260825T0400Z`(orchestrator, item52 적용후
> 분기 미배선 주장) 드레인: **티켓의 가설은 틀렸다(코드는 이미 적용전·적용후 대칭이었다) —
> 실제 원인은 item52 커버리지가 100%가 되며 item1[값_적용후]의 유일한 엔진 가드였던
> 폴백이 죽은 코드가 된 것.** `7_post`(item27후=item1후/item14후×100, 기존 `8_post`의
> 대칭짝) 신설로 복원.
>
> - **가설 반증**: `_validate_tfi_tier_rows()`의 item52 등식 분기(`kics_json_rules.py`
>   L1648)는 `post` 값과 무관하게 이미 하나의 코드 경로다 — "적용전만 배선되고 적용후는
>   안 됐다"는 코드 구조상 불가능했다. 변이시험(`scripts/_probes/
>   probe_20260825_item1_post_coverage.py`) 실측: item1[값_적용후] 488칸 흔들어도
>   반응 0건(양성대조군 item1[값] 적용전은 976건 반응 — 하니스는 정상). 분해: 50/51 둘 다
>   있는 450버킷 **전부**가 item52도 갖고 있어(없음 0), item1_적용후를 참조하던 옛 폴백이
>   0/450에서만 산다 — 즉 죽은 코드. 그 폴백이 엔진에서 item1 post를 보는 유일한 코드였다
>   (rule "7"은 pre만 봄).
> - **수정**: `_validate_tfi_tier_rows`/`50_tfi_tier_split_post`는 안 건드림(item52 등식이
>   이미 더 강한 검사). 대신 `_validate_transition_basic()`에 `7_post` 신설 — 기존
>   `8_post`와 정확히 대칭(same-basis 가드·동적허용오차 동일).
> - **전 버킷 시뮬레이션**(`scripts/_probes/probe_20260825_7post_before_after.py`, git HEAD
>   vs 현재를 임시 모듈 2개로 로드해 대조): 기존 13,664개 (회사,분기,rule) 키 status 변경
>   **0건**(회귀 없음, 8_post 포함) · 신규 7_post **RED 0 · YELLOW 6(전부 소액분모 반올림,
>   기존 카카오 사례와 동일 패턴) · GREEN 482** → item1_적용후 488칸 전량 커버리지 복원,
>   새 RED 없어 판정할 대상 없음.
> - **item52 census**(부탁 3번, `scripts/_probes/probe_20260825_tfi_skip38_census.py`):
>   50/51 있는데 item52만 빠진 버킷 **0개** — 이번 건 백필은 이미 완료 상태였다. 남은
>   SKIP 38(NO_TABLE 28 · BACKLOG 10)은 전부 이미 다른 티켓에 추적 중(NO_TABLE 13칸=
>   미래에셋생명 `task_66ee6d43` 스핀오프분, 나머지는 룰 docstring에 이미 문서화된 표
>   부재/50-51 백로그) — 중복작업 방지 위해 이번엔 추가 적재 안 함.
> - **부수 2건**: ① `validate_kics_disclosure.py::_print_tier2_axis_report`의
>   `_TIER2_POST_RANGE_ONLY` 노트가 하드코딩이라 item52 100% 채워진 뒤에도 "결측이라
>   범위검사"를 계속 인쇄하던 것(티켓이 지적한 정확히 그 증상) — 이번 실행 실측 폴백
>   히트수를 세어 0이면 "전량 등식 검사됨"으로 동적 출력하게 고침. ② `tests/
>   test_tfi_memo_rows.py::test_axis_e_fallback_still_exists_for_missing_item52` —
>   라이브 마스터에서 폴백이 자연발생하길 기대하던 테스트가 30버킷 적재로 그런 버킷이
>   0개가 되며 **내 세션 이전부터** 깨져 있었다(전/후 시뮬레이션으로 7_post와 무관함을
>   확인). 대표 버킷 하나의 item52를 인위적으로 지우는 변이로 바꿔 메커니즘은 계속 검증.
> - **골든**: `tests/test_kics_rules_golden.py --update` — findings 13,664 → 14,152
>   (+488 = 신규 7_post 전량), by_status GREEN +482 · YELLOW +6 · RED/SKIP 불변. 사유는
>   해당 파일 "2026-08-25 (7차)" 문단.
> - **게이트/prepush 실측**: `test_rule_coverage_manifest.py` **11 passed**(38.99s,
>   FULL_COVERAGE_SWEEP 포함) · `validate_kics_disclosure.py` **exit 0**(RED=36 전부
>   기존 documented exception, blocking RED=0, 내 변경 전후 동일) · **`prepush_check.py`
>   전체 실측 완료(450초)**: K-ICS RULE GATE exit=0(clear) · DOMAIN GATES pass(4개 전부
>   exit=0) · INBOX HYGIENE 기계적위반=0 · OFFLINE TESTS(FULL_COVERAGE_SWEEP=1, 8파일+
>   tests/unit/) **176 passed, 1 skipped, 0 failed**(test_rule_coverage_manifest.py 전수
>   스윕 포함) · **overall verdict = BLOCKED(exit 2)**, 유일한 사유는 data-contract 게이트
>   SUMMARY RED=2(`[PL_breakdown] 하나생명보험 2023.4Q`·`[CSM_waterfall] 하나생명보험
>   2025.4Q`, 둘 다 ifrs17 레인 소관, K-ICS·item52·item1과 무관 — 병렬 세션이 처리 중).
>   내 몫(K-ICS 게이트·offline tests·domain gates)은 전부 clear/pass. `kics_disclosure.json`
>   은 이번 세션에서 바이트 0 변경(git diff 없음), xlsx sync 불필요(dry-run 변경 0, 이미 최신).
> - 티켓 status: resolved → `inbox/_resolved/` (이동 완료).
>
> Last updated (이전): 2026-08-25(19회차) — orchestrator 발주(재감사 부수발견 승계):
> **item52(경과조치표 자신의 지급여력금액 행) 30버킷 적재 완료 — 다만 담당 에이전트가
> 문서 작성 전에 멈춰(watchdog stall) 오케스트레이터가 검증·기록을 대신했다.**
>
> - **적재 결과(오케스트레이터 실측)**: item52 행 428 → **458**(신규 30행), 적용전·적용후
>   **458/458 전부 값 있음**. 신규 버킷은 KR0004(4) · KR0010(5) · KR0080(6) · KR0087(4) ·
>   KR0068(3) · KR1098(3) · KR0005 · KR0009 · KR0071 · KR0097 · KR0100 각 1.
> - **게이트**: `validate_kics_disclosure.py` **exit 0** · blocking RED=0 유지.
>   `50_tfi_tier_split` [적용전] RED=1 YELLOW=1 GREEN=448(적재 전과 동일 — 이 축은
>   원래 item1 폴백으로 돌고 있었다), [적용후] YELLOW 2 → **1**.
> - **🔴 미완 1건 (다음 세션이 이어받을 것)**: 데이터는 두 컬럼 다 들어왔는데
>   **게이트 적용후 경로가 아직 item52 를 안 쓴다.** 리포트가 여전히
>   `※ 등식 아님 — item52(TFI표 자신의 지급여력금액 행) 결측이라 범위검사` 를 인쇄한다.
>   축 라벨과 적용전 분기만 바뀌고 적용후 분기가 안 바뀐 반쪽 변경이다 —
>   **"메시지는 X 라는데 코드는 Y"** 유형이라 그대로 두면 다음 세션을 오도한다.
>   티켓: `inbox/parser/20260825T0400Z__orchestrator__MULTI__item52_post_branch_unwired.md`
> - **부수**: 같은 커밋에 게이트 리포트의 stale 산문 2건 제거(KR0004 2025.1Q · KR0003
>   2023.1Q 를 "미등록" 이라 설명했으나 실제로는 `_TIER2_ISSUER_INCONSISTENT` 에 등록돼
>   있었다 — 재감사보고서 F2 지적분). 차단집계에는 영향 없고 산문만 고쳤다.


> Last updated: 2026-08-24(18회차) — orchestrator 발주(재감사 보고서
> `artifacts/validation/reaudit_20260824_KR0097_KR0049_KR0079_plus_ledger_quality.md`
> 파트 1-A 승계): **KR0097 하나생명보험 2024.4Q 생명장기 하위위험 값_적용후 4셀 정정
> — 마스터 결함(면제가 가리고 있던 것) 확정 처리.** status: resolved → `_resolved/` 대상
> (root TODO에 이 티켓 자체가 없어 별도 이동 없음, 아래 상세 참조).
>
> - **재현**: raw `KR0097_하나생명보험.pdf`(347p) p281(item17후 200,189,811천원=2,001.898억)
>   ·p296(item29-35 적용전, 적용후 컬럼 없음)·p326(최초산출액 표) 전부 fitz 텍스트로 직접
>   재확인 — 감사보고서 claim과 소수점까지 일치. `942.86`·`896.15`·`94,286`·`89,615` 전수
>   grep 0 hit(원문에 없음), `200,189,811` 1 hit(p281). phase-in 식
>   `적용후=max(0,적용전−(1−인식비율)×최초산출액)`을 13분기 전부 재계산 →
>   **2024.4Q 를 뺀 12분기 전부 derived==master(±0.01억)**.
> - **결함**: item33후="942.86"·item34후="896.15" 가 2024.3Q 값의 **stale carry-forward**
>   (원문 어디에도 없음), item30후·item35후는 결측. 이 4셀은 `_AFTER_SUBRISK_NOT_DISCLOSED`
>   면제가 `_transition_mmult_after` 부모 조회 전에 축 전체를 스킵시켜 **어떤 룰도 검사한
>   적이 없었다**(감사기 발견).
> - **정정**(`scripts/fix_20260824_kr0097_2024q4_after_subrisk.py`, dry-run 지원·
>   idempotent·expect_old guard): item30후 신설="0", item33후 942.86→**1377.71**,
>   item34후 896.15→**714.73**, item35후 신설="0". R7([230.82,0,391.46,0,1377.71,
>   714.73,0])=2001.896 vs 공시 item17후 2001.898 → **잔차 −0.0023억**(구값은 −201.08,
>   tol 100.09 대비 2배 초과 FAIL). `git diff` 로 딱 4필드만 변경됐음을 확인(행 추가/삭제 0).
> - **게이트**: `validate_kics_disclosure.py` exit **0**(불변) — `git stash` 로 수정전/후
>   양쪽 실행해 대조한 결과 RED=37/YELLOW=1519/GREEN=9522 findings **바이트단위로 완전
>   동일**(면제가 이 4셀을 여전히 검사 밖에 두고 있다는 뜻, 감사보고서 판정과 일치).
> - **골든**: `test_kics_rules_golden.py` **PASS 그대로**(재생성 불필요) — 예상과 달리
>   findings matrix가 안 바뀐 이유는 위와 동일(면제가 순회에서 이 4셀을 아예 뺌).
>   관련 137개 테스트(`test_identity_tautology`·`test_kics_item_registry`·
>   `test_post_transition_golden`·`test_rule_coverage_manifest`·
>   `test_source_vision_verified`·`test_tfi_memo_rows`·
>   `test_tier2_issuer_inconsistent_exemption`·`test_irr_pin_exemption`·
>   `test_kics_disclosure_parser`) 전부 PASS.
> - `sync_master_xlsx_sheet.py "K-ICS공시"`: EDIT 4·INSERT 0·DELETE 0, 22658행×9열 검증
>   OK, 재실행 drift 0.
> - **면제 레지스트리는 안 건드림**(발주 범위 밖). `_AFTER_SUBRISK_NOT_DISCLOSED` claim
>   자체(29-35 세부표 없음)는 참이지만 레지스트리 효과가 축15·19·census까지 덮는 과대스코프
>   문제(감사보고서 H8)는 owner/validation 판단 대기.
>
> Last updated (이전): 2026-08-24(17회차) — inbox `20260821T0620Z`(validation, §3
> `SOURCE_UNREADABLE_NOT_VERIFIED` 잔여 9쌍) 드레인: **9쌍 전부 vision 판독으로 "미러링이
> 원문으로 확정됨" — 마스터 변경 0건**(KB손해 2025.3Q/2026.1Q · 미래에셋생명 2025.1Q/2025.3Q/
> 2026.1Q · AIA생명 2025.1Q/2025.3Q/2026.1Q · 동양생명 2026.1Q). raw PDF를 `fitz.get_pixmap
> (dpi=240)`로 렌더링해 육안 판독한 결과 **9쌍 전부 진짜 래스터 스캔이 아니라 벡터 텍스트**였고
> (KB손해 2025.1Q 선례와 같은 폰트매핑 계열), 매 쌍마다 원문이 "적용하지 않아 ~ 동일함" 각주 또는
> 적용전=적용후 완전동일 표로 명시 확인됨(item17전·item19전 값도 마스터와 소수점까지 일치). 상주
> 스크립트 `scripts/_probes/render_kics_pages.py` 신설(1회성 `render_kr0010_2025q1.py` 일반화).
> 게이트 read-only 재확인: `validate_data_contract.py` YELLOW 20건 그대로(사이드카 휴리스틱은
> 못 바꿈, 등재는 권한 밖) · `validate_kics_disclosure.py` exit 0. status: answered(sender
> 재확인 대기 — validation이 반복 적대적 재검증하던 티켓이라 관례상 self-close 안 함). 부수 발견
> (안 건드림): 미래에셋생명(KR0079) 3개 분기 item47-54 결측인데 raw엔 표 존재 — task_66ee6d43
> (item47-54 전수감사) 세션 참고용으로 티켓에 기록.
>
> Last updated (이전): 2026-08-24(16회차) — inbox `20260821T2010Z`(orchestrator, leaf 감사기 잔차
> 4건) 드레인: **마스터 무변경 — 감사기 자신의 버그 2종을 코드로 고쳐 불일치 4→0.** 예별손해
> (KR0004) item36후=대시를 carry-forward로 오독하던 `scan_occurrences()` dash 처리(전
> 버킷 시뮬레이션으로 234버킷 중 정확히 4건만 영향·역행 0건 확인 후 수정) + 처브라이프
> (KR0100) item35 발행사 내부 표간 불일치를 exact-value pin. `kics_disclosure.json` git diff
> 0(마스터 변경 0건), 게이트 exit 0(수정 전후 byte-identical RED 목록).
>
> Last updated (이전): 2026-08-24(15회차) — inbox `20260824T0400Z`(validation, item52-54 적재결함
> A~E) 드레인: 5건 원문재확인·정정 + 근본원인 코드패치 1건 + opportunistic 2건.
> row_count 22,653→22,658(EDIT 14·DELETE 2·INSERT 5).
>
> - **A. 카카오페이(KR1098) 5분기 item52 100배 — 근본원인 규명+패치.** `fix_20260824_tfi_
>   capital_memo_rows.py::_infer_scale()`의 `ALL_ZERO_TRIVIAL` 숏컷(47/48/49/51 전부 0일 때
>   "스케일 무관")이 같은 버킷 item52(대개 실값)에도 그대로 적용돼 5분기가 100배로 실렸다.
>   ALL_ZERO_TRIVIAL이어도 item52 vs 마스터 item1로 재확인하도록 패치 + 460버킷 전수
>   재스캔으로 **변경은 정확히 이 5버킷뿐**임을 확인(다른 버킷 무손상, `probe_20260824_
>   scale_diff.py`). 기존 5셀은 idempotent guard 때문에 직접 UPDATE(÷100).
> - **B(=원 티켓 G). 삼성화재(KR0008) 2025.3Q item52_적용후 — owner 예외승인(2026-08-24)
>   반영.** raw p16 재확인(자릿수 전치 28,650,195↔28,605,195, 비율·각주·item50+51 합계 전부
>   650,195쪽과 일치) — 286051.95→286501.95. `50_tfi_tier_split`·`_post` 둘 다 GREEN 전환
>   확인.
> - **C. 농협생명(KR0104) 2024.3Q item53/54_적용후 — 원인 규명(2단 레이아웃 행클러스터링
>   오염) + 삭제.** 해당 페이지가 "(1)공통적용경과조치"(좌)+"②장수위험경과조치"(우) 2단
>   배치인데 y좌표만 보는 행클러스터링이 우측 표 값(기본요구자본·생명장기손해보험위험액)을
>   좌측 메모행에 섞었다 — 삭제한 값과 우측 표 PRE값이 정확히 일치해 원인 확정. **처브라이프
>   (KR0100) 2023.1Q item54[값]도 동일 원인**이라 같이 정정(840.06→0, opportunistic).
> - **D. 푸본현대(KR0083) 2024.3Q — 티켓 주장과 반대, 변경 안 함.** raw p15를 dpi=400
>   확대해 시각확인 — 메모행 PRE 칸이 대각선 취소선으로 명시적 공란처리, 실값은 POST 칸에
>   인쇄(좌표로도 재확인, POST 앵커와 거의 정확히 일치). 현재 마스터가 이미 정확 — 스왑
>   안 함. **부작용**: 이 판정 때문에 `53_tfi_memo_rows` 룰이 새 blocking RED 1건을 냄(룰이
>   PRE만 보고 POST를 안 보는 것으로 보임) — validation 판단 대기.
> - **E. 행 유실 3건 INSERT** — 롯데손해(KR0003) 2026.1Q item53(라벨손상 U+302E), 동양생명
>   (KR0087) 2024.1Q item53·54, 하나생명(KR0097) 2025.2Q item53. 전부 좌표로 PRE단일컬럼
>   확인 후 적재. **동양생명(KR0087) 2024.3Q item54(원 티켓 F, "판독불가")도 페이지 경계
>   너머(다음 페이지 맨 위)에서 발견해 같이 적재(opportunistic).**
> - **게이트**: `validate_kics_disclosure.py` blocking RED **2**(예상 1과 다름 — 사유는 위
>   D 부작용 + NH농협 KR0032 2024.3Q `2_tier1_bridge` diff=-522는 validation 소관 미조사
>   건으로 내 세션과 무관하게 남음). 한화생명(KR0068) 2025.2Q는 내 세션 도중 validation이
>   동시에 owner 승인 documented exception으로 등재해 더 이상 단순 blocking RED가 아님(내
>   작업과 무관, 공유 워킹트리 병렬편집 관찰).
> - **pytest**: `317 passed, 1 skipped, 1 failed`. golden(`test_kics_rules_golden.py`)은
>   데이터 변경 반영해 `--update`. 남은 1 FAIL은 validation 소유
>   `test_tier2_issuer_inconsistent_exemption.py`(`tests/*` 금지라 못 고침) — 그 테스트
>   자신의 docstring이 "삼성화재 고쳐지면 실패해야 정상"이라 명시해 뒀다(내 수정이 반영됐다는
>   신호, validation이 다음 세션에 `held` 셋 갱신하면 해소).
> - `sync_master_xlsx_sheet.py "K-ICS공시"`: 14 EDIT·5 INSERT·0 DELETE, 22658행×9열 검증
>   OK, 재실행 drift 0.
> - 신규 스크립트: `scripts/fix_20260824_item52_54_load_defects.py`(A~E+부수2건, dry-run
>   지원, idempotent, raw근거 docstring). 패치: `fix_20260824_tfi_capital_memo_rows.py`
>   (A 근본원인). 진단: `scripts/_probes/probe_20260824_item52_54_defects.py` ·
>   `probe_20260824_verify_raw_AE.py` · `probe_20260824_scale_diff.py`(전부 read-only).
> - **spawn_task 발주(task_66ee6d43)**: C·처브라이프가 보여준 "TFI 2단 레이아웃 행클러스터링
>   오염" 패턴이 item47-54 전체 431버킷 중 다른 곳에도 더 있을 수 있어 전수감사 별도 세션
>   스핀오프.
> - **owner/validation 판단 대기**: (a) 푸본현대(KR0083) 2024.3Q 새 RED — 룰 확장 또는
>   문서화 예외. (b) `test_tier2_issuer_inconsistent_exemption.py`의 `held`에서
>   `("KR0008","2025.3Q")` 제거(validation 소유 파일). (c) NH농협 KR0032 2024.3Q 조사(내
>   소관 아님). 상세는 `inbox/parser/20260824T0400Z...md` `## 답변 (parser-kics)` 절.
>
> Last updated (이전): 2026-08-24(14회차) — inbox `20260821T1425Z`(§7 "KR0032 2025.4Q parser 발주",
> 내 iter-10) 처리: TFI표 마지막 두 메모행 `(기발행 신종자본증권)`·`(기발행 후순위채무)`를
> **item53·54**로 신설 적재(460버킷 전수 스캔, 440건 성공, 신규 1291셀). **번호충돌 발견·정정**
> — 처음 52/53에 앉혔다가 게이트에서 `src/solvency/validation/kics_json_rules.py`(축E)가
> item52를 "TFI표 맨 윗줄 지급여력금액"용으로 이미 예약해 뒀음을 발견, 백업 복구 후
> 52=지급여력금액(validation 예약분 대신 채움)/53=신종자본증권/54=후순위채무로 재배정.
> NH농협 2025.4Q는 `item51==min(47,48)+49+item54`로 정확히 닫힘(잔차 0) — **단 전사공식
> 아님**: 361버킷이 기존식으로 이미 닫혀 있었고 그중 214버킷은 `+item54`를 강제하면 새로
> 깨진다(item47이 이미 후순위채무 포함값인 회사가 대다수) — 등식 승격은 validation 판단
> 사항, NH농협 1건 documented exception 근거로만 권고. 게이트 RED=40/blocking=13 불변(내
> 추가분 inert 재확인, 백업본과 바이트 동일). **pytest 1건 FAIL**(`test_rule_coverage_manifest.
> py` — item52-54 무방비 항목 검출, `tests/*` 금지라 못 고침 — validation 후속 필요).
> xlsx sync 1291 INSERT·drift 0. 상세는 `inbox/parser/20260821T1425Z...md` `## 답변
> (parser-kics, iter-10)`.
>
> Last updated (이전): 2026-08-24(13회차) — inbox `20260821T1425Z`(validation, iter-5→ 내 iter-9)
> 잔여 5버킷(BNP카디프 24.4Q/25.1Q·동양생명 25.2Q·한화생명 25.2Q·예별손해 25.1Q) 전부 raw
> 전체 텍스트 덤프로 재대조. **마스터 값 전부 원문과 일치 — 수정한 셀 0개.** BNP 2건·동양생명
> 1건은 발행사 표 자기모순 재확인(item51≠min(47,48)+49, gap이 item49 대비 상수비율 아님 —
> 6.2%/26.3%/20.1%로 확인). 한화생명은 판정불가 유지 + 새 단서(item51_후−item51_전=825.75
> ≈ bridge잔차 826, 인과 미확정). **예별손해는 분류 정정** — bridge(item2)는 원래도 잔차 0으로
> 닫혀 있었고, 실제 잔차는 composition(item3 vs TFI표 스코프차이)뿐이었다(기존 면제 초안이
> 이미 맞는 축에 걸려 있었음). blocking RED 39 불변(수정 없음이 기대대로). 상세는 최상단
> 항목 참조 · Stage 2/5 — parser (kics lane)
> Prompt: docs/agents/claude-agent-parser.md · Changelog: docs/changelog_parser_kics.md (pre-split: docs/changelog_parser.md)

Stage 2 — **parser, K-ICS lane**: solvency disclosure extraction. Source = Docling MD; output = `kics_disclosure.json`; validators = `validate_kics_disclosure.py` / RS1–4 / market census. The IFRS17 lane (CSM/PL extraction off DART XML) lives in `TODO_parser_ifrs17.md` and runs as a separate session.

Session start: read this file + `docs/agents/claude-agent-parser.md` + `docs/domains/claude-agent-kics.md`. English where Korean encoding is fragile (see `CLAUDE.md`).

## Status

**2026-08-29(2회차) — 코디네이터 검토 통과 + 기본자본소진율 100%초과 13행 비고 보강 완료.
git add(내 파일만)+커밋 완료. status: answered(owner 재확인은 대기, 코드/xlsx 작업은 종결).**

**2026-08-29(1회차) — inbox `20260829T0100Z`(orchestrator, 자본 마스터 3종 xlsx 편입): 신규 시트 3개
(기본자본소진율·보완자본소진율·자본비율전망, 3,026행) 추가 완료·검증 통과. "tier2 4개사 이상치"
전제는 stale 로 실측(현재 0건) — 지어내지 않고 실제 census 결과로 대체. 상세는 최상단 참조.**

**2026-08-24(18회차) — orchestrator 발주(재감사 보고서 파트 1-A 승계): KR0097 하나생명보험
2024.4Q 생명장기 하위위험 값_적용후 4셀 정정. status: resolved.**

발주 근거: `artifacts/validation/reaudit_20260824_KR0097_KR0049_KR0079_plus_ledger_quality.md`
파트 1-A. validation stage 의 면제 재감사가 KR0097 2024.4Q 를 `MASTER_DEFECT`로 뒤집었다 —
등재된 면제 claim("29-35 적용후 세부표가 원문에 없다")은 참이지만, 그 면제가 `_transition_
mmult_after` 축을 부모 조회 전에 통째로 스킵시켜 마스터 안의 실제 결함(item33후·34후가
직전분기 값의 stale carry-forward, item30후·35후는 결측)이 등재 이후 오늘까지 한 번도
검사받지 않았다.

- **raw 독립 재현**(감사기 주장을 액면 그대로 믿지 않고 재확인 — `scripts/_probes/
  probe_20260824b_kr0097_raw_verify.py`): `data/disclosure/FY2024_Q4/raw/KR0097_하나생명보험.pdf`
  (347p, 텍스트레이어 정상) p281 `[지급여력기준금액]` 표에서 `1. 생명·장기손해보험위험액`
  경과조치 적용후 = **200,189,811천원**(=2,001.89811억) 직접 확인. p296 `B.1.1
  생명·장기손해보험리스크` 표는 사망/장수/장해질병/장기재물/해지/사업비/대재해 7개 항목의
  **당기말(=적용전)·전기말 두 컬럼뿐, 적용후 컬럼이 없음**을 확인(claim 그대로). p326
  `(2) …경과조치` 표에서 최초 산출 금액(장수 14,325,093·해지 66,403,015·사업비
  43,877,926·대재해 7,847,532 천원)과 "2024년 인식비율 10%"를 확인. 전수 grep으로
  `942.86`·`896.15`·`94,286`·`89,615` **0 hit**(원문 어디에도 없음), `200,189,811`
  **1 hit**(p281) — 마스터의 두 stale 값이 원문 출처가 아님을 재확인.
- **식 검증**(`scripts/_probes/probe_20260824_kr0097_phasein.py` 재실행): `적용후 = max(0,
  적용전 − (1−인식비율)×최초산출액)`을 2023.1Q~2026.1Q 전체 13분기에 적용 → **2024.4Q를
  제외한 12분기 전부** derived 값이 마스터 값_적용후와 ±0.01억 이내로 일치(부동소수 반올림
  수준, 사실상 동일 — 이 회사가 13분기 내내 따르는 식임을 확인).
- **정정 적용**(`scripts/fix_20260824_kr0097_2024q4_after_subrisk.py`, `--dry-run` 지원,
  `expect_old`/`_MISSING` sentinel guard로 동시편집 방지, 셀 단위 UPSERT — JSON 통째
  read-modify-write 아님):
  - item30후(장수) 신설 = **"0"** (95.51 − 0.9×143.25093 = −33.42 → clamp 0, 다른 12분기와
    동일 패턴 — item30후는 2024.4Q를 제외한 전 분기가 "0")
  - item33후(해지) 942.86 → **"1377.71"** (1975.34 − 0.9×664.03015 = 1377.712865)
  - item34후(사업비) 896.15 → **"714.73"** (1109.63 − 0.9×438.77926 = 714.728666)
  - item35후(대재해) 신설 = **"0"** (52.08 − 0.9×78.47532 = −18.55 → clamp 0, 2024.3Q까지도
    동일 패턴이었다가 2025.1Q부터 적용전이 커지며 양수 전환 — 2024.4Q는 아직 그 전)
  - `git diff -- kics_disclosure.json`으로 **정확히 이 4필드만** 바뀌었음을 확인(행 추가/
    삭제 0, 다른 회사·분기 무손상).
- **잔차 재계산**(`scripts/_probes/probe_20260824e_kr0097_final_check.py`, 반올림된
  2decimal 값으로 재확인 — 파생 float 그대로가 아니라 마스터에 실제로 쓰는 문자열 기준):
  R7([230.82, 0, 391.46, 0, 1377.71, 714.73, 0]) = **2001.8958** vs 공시 item17후
  raw p281 기준 **2001.89811** → **잔차 −0.0023억**(≈230원, tol 100.09 대비 무시 가능).
  구 값(942.86/896.15, 결측 2칸은 0 취급)으로는 R7=1800.8172, 잔차 **−201.08**(tol을
  2배 초과, FAIL) — 참값만 닫히고 구 값은 깨진다는 감사보고서 판정을 절대값까지 재현.
- **게이트**(`validate_kics_disclosure.py`): exit **0** 그대로. `git stash`로 수정 전/후
  양쪽을 각각 재실행해 리포트를 대조 — 타임스탬프 한 줄만 빼고 **RED=37/YELLOW=1519/
  GREEN=9522/SKIP=2586 findings 가 바이트단위로 완전 동일**. 즉 이 수정은 게이트가 보는
  어떤 것도 바꾸지 않았다 — `_AFTER_SUBRISK_NOT_DISCLOSED` 면제가 여전히 이 4셀을 룰
  순회에서 빼고 있다는 뜻이며, 정확히 감사보고서가 지적한 사각과 일치한다.
- **골든**(`tests/test_kics_rules_golden.py`): 재실행 결과 **PASS 그대로**(해시 재생성
  불필요). 발주 지시는 "findings 매트릭스가 바뀔 것"으로 예상했으나, 위 게이트 대조가
  보여주듯 findings 자체가 이 4셀을 포함하지 않으므로 값 변경이 골든에 반영되지 않는다
  — 손으로 만지지 않았고 `--update`도 돌리지 않았다(돌릴 필요가 없어서). 연관 테스트
  137개(`test_identity_tautology`·`test_kics_item_registry`·`test_post_transition_golden`
  ·`test_rule_coverage_manifest`·`test_source_vision_verified`·`test_tfi_memo_rows`·
  `test_tier2_issuer_inconsistent_exemption`·`tests/unit/test_irr_pin_exemption`·
  `tests/unit/test_kics_disclosure_parser`) 전부 PASS.
- **xlsx**: `sync_master_xlsx_sheet.py "K-ICS공시"` — EDIT 4·INSERT 0·DELETE 0, 22658행×9열
  마스터와 완전 일치 검증, 재실행 drift 0.
- **면제 레지스트리는 건드리지 않음**(발주 범위 — "너는 값만 고친다"). `_AFTER_SUBRISK_
  NOT_DISCLOSED` 의 claim(29-35 적용후 세부표가 원문에 없다) 자체는 참이라 자동 해제
  대상이 아니다. 다만 그 면제 효과가 claim 스코프(29-35)보다 넓게 축15·19·census 전체까지
  덮고 있다는 것(감사보고서 H8), 그리고 이번 사고처럼 부재형 면제에는 "채워지면 즉시 RED"가
  되는 부재 박제가 없다는 것(H1)은 이 세션이 고치지 않았다 — validation/owner 후속 판단
  대기 사항으로 남긴다.
- 신규 파일(전부 read-only 진단 + 1개 정정 스크립트, BOM 없음·ast.parse 확인):
  `scripts/_probes/probe_20260824b_kr0097_raw_verify.py` ·
  `probe_20260824c_kr0097_schema.py` · `probe_20260824d_kr0097_fmt_survey.py` ·
  `probe_20260824e_kr0097_final_check.py` · `scripts/fix_20260824_kr0097_2024q4_after_subrisk.py`.

Last updated (이전) — 2026-08-24(17회차) — inbox `20260821T0620Z`(validation, §3 `SOURCE_UNREADABLE_NOT_VERIFIED`
잔여 9쌍) 드레인: 9쌍 전부 vision 판독으로 확정, 마스터 변경 0건. status: answered.

이 티켓은 §1(면제근거 거짓)·§2(축 동어반복)가 이미 해소됐고 §3만 미결이었다(KB손해 2025.1Q 1쌍만
기왕 vision 검증됨, 나머지 9쌍 미판독). 오늘 세션이 그 9쌍을 처리했다.

- **실측 재확인**: `validate_data_contract.py` 재실행 → 오늘도 정확히 10쌍×2항목=YELLOW 20건,
  목록 동일(위 목록을 안 믿고 다시 뽑으라는 지시 이행).
- **방법**: `fitz.get_pixmap(dpi=240)`로 각 raw PDF의 경과조치 관련 페이지를 렌더링해 Read 도구로
  육안 판독. **9쌍 전부 실제로는 벡터 텍스트**(래스터 스캔 아님) — KB손해 2025.1Q의 "폰트 유니코드
  매핑 실패" 계열과 동일. 미래에셋생명(KR0079) 3개 분기는 fitz `get_text()`로 대상 페이지 텍스트가
  그대로 나왔다(사이드카 UNREADABLE 판정은 문서 전체 평균 밀도 왜곡 — 공백에 가까운 페이지가
  많아서였지 대상 페이지가 안 읽혀서가 아님).
- **판정**: 9쌍 전부 **"미러링이 원문으로 확정됨"** — 매 쌍마다 raw 원문이 "적용하지 않아 경과조치
  전·후 금액 및 비율이 동일함" 각주(KB손해·미래에셋·AIA·동양생명 전부) 또는 적용전=적용후 완전동일
  값표로 명시 확인. item17전·item19전 값도 마스터와 소수점까지 정확히 일치(9쌍×2항목=18셀
  cross-check). KB손해는 공통(TFI)=O이지만 TFI는 가용자본측 조치라 item17/19(요구자본)엔 원천
  무관(지급여력기준금액 적용전=적용후 완전 동일로 확인) — 선택 ①②③은 전부 미신청.
- **마스터**: `kics_disclosure.json` 셀 변경 0건(원래 값이 이미 정확했음). `sync_master_xlsx_sheet.py`
  실행 안 함(변경 없어서).
- **게이트**(read-only, 영향 없음을 실측 확인): `validate_data_contract.py`의
  `SOURCE_UNREADABLE_NOT_VERIFIED` YELLOW 20건 그대로(vision 판독이 사이드카의 텍스트밀도
  휴리스틱 자체를 못 바꿈 — 등재 여부는 내 권한 밖). `validate_kics_disclosure.py` exit code 0
  (`blocking RED=0`, 38건 전부 이 티켓과 무관한 기존 documented exception).
- **신규 파일**: `scripts/_probes/render_kics_pages.py` — 일반화된 렌더 스크립트(1회성
  `render_kr0010_2025q1.py` 패턴을 재사용 가능하게 승격, BOM 없음·ast.parse 확인).
- **부수 발견(스코프 밖, 안 건드림)**: 미래에셋생명(KR0079) 3개 분기 item47-54가 전부 결측인데
  raw엔 "1) 공통적용경과조치 관련" 표가 매 분기 존재(TFI=X라도 표 자체는 인쇄, 전부 적용전=적용후).
  또한 이 표의 "(기발행 신종자본증권)"·"(기발행 후순위채무)" 메모행은 **적용전/적용후 중 어느 쪽에
  대각선 취소선이 그려지는지가 회사마다 다르다**(KB손해·미래에셋=적용후 쪽 취소선, 반면 15회차
  기록의 푸본현대(KR0083) 2024.3Q=적용전 쪽 취소선) — 고정 컬럼 가정으로 읽으면 회사에 따라 반대로
  읽을 위험. `task_66ee6d43`(item47-54 전수감사, 15회차가 스핀오프) 세션이 참고할 수 있게 원 raw
  값과 함께 티켓에 기록해 뒀다(직접 안 고침 — 스코프 밖 + 병행 세션과 충돌 회피).
- 상세는 `inbox/parser/20260821T0620Z...md` `## 답변 (parser-kics, 2026-08-24)` 절.

**2026-08-24(16회차) — inbox `20260821T2010Z`(orchestrator, leaf 감사기 잔차 4건) 드레인:
마스터 무변경, 감사기(`leaf_scale_residue_audit.py`) 자체의 버그 2종을 코드로 고쳐 불일치
4→0(재실행 실측). status: resolved → `_resolved/` 이동.**

- **① 예별손해(KR0004) 2023.4Q/2024.1Q/2024.2Q item36_적용후 — 근본원인=감사기 dash 오독,
  코드 수정.** raw fitz 원문 직접 재확인(`probe_20260821_kr0004_pages.py` 재실행): "③
  주식위험 경과조치 또는 금리위험 경과조치" 표에서 금리위험 적용후 칸이 3개 분기 전부
  리터럴 대시(`-`). `MARKET_M` 상관행렬 재현(`probe_20260821_kr0004_verify.py` 재실행)으로
  가설 A(금리후=0)가 회사 인쇄 시장위험액후 합계(110,677/116,622/134,130백만)를 소수점
  이하 오차로 재현, 가설 B(대시=carry-forward)는 26,000~38,000백만 어긋남을 재확인 —
  2026-08-21 답변의 결론이 뒤집히지 않음을 독립 재검증했다. **원인은 마스터가 아니라
  `scripts/rebuild_combined_transition_after.py::scan_occurrences()`** — 시장위험(36-40)
  리프의 적용후 대시를 무조건 carry-forward(`b=a`)로 스냅하는 규칙이 롯데손보 2026.1Q류
  (형제 5개 전부 대시=선택 자체 안 함)에만 맞고, 예별손해처럼 같은 표 안 형제(주식위험)가
  진짜 감소값을 보이는 "선택적용이 실제로 걸린 표"에는 틀렸다(그 경우 대시=적용후 인정액
  0). **수정 전 전 버킷 시뮬레이션**(`probe_20260824_market_dash_simulate.py`, APPLIERS
  18사×234버킷 구법/신법 나란히 계산) — 값이 달라지는 버킷은 정확히 4건(예별손해 3분기 +
  흥국화재 2023.4Q, 후자는 앵커불가 버킷이라 감사기 집계엔 원래 안 잡힘), 넷 다 신법이
  마스터와 같거나 더 가까움, 역행 0건 확인 후 `scan_occurrences()`를 수정(dash 위치만
  기록해 뒀다가 표 전체를 다 읽은 뒤 형제 중 진짜 변화 유무로 사후 판정).
- **② 처브라이프(KR0100) 2024.4Q item35(적용전) 46.81 vs 44.99 — 발행사 내부 표간 불일치
  확정, exact-value pin.** raw p55-56(업무보고서 AH725/AI725 "[생명·장기손해보험위험액-
  대재해위험]" 전용표) "Ⅲ.총계" 당기=4,681백만=46.81억(마스터와 일치, 정본). raw
  p47-48("②" 선택적용 경과조치 결합표)의 대재해위험 행=4,499백만=44.99억(감사기가 대조하는
  값). 같은 개념을 발행사가 두 표에서 다르게 인쇄한 것 — `scan_occurrences()`가 "경과조치"+
  "기본요구자본" 두 단어가 함께 있는 페이지만 훑어 정본표(경과조치 언급 없음)를 구조적으로
  못 본다. item29-34(나머지 6항목)는 raw 재확인 결과 두 표가 이미 일치해 대재해위험만
  유일하게 갈리는 걸로 보여, 새 파싱 경로를 여는 대신 감사기에
  `KNOWN_ISSUER_TABLE_INCONSISTENCY` exact-value pin 1건 추가(마스터/대조값 어느 한쪽이라도
  바뀌면 즉시 재발화).
- **③ "앵커불가 21" 설명을 감사기 출력 자체에 인쇄.** `no_occ`(기본요구자본 occurrence
  없음, 10건)와 `bad_ratio`(스케일비율 이상, 11건)를 감사기 내부에서 직접 분리 집계하도록
  고쳐, 별도 스크립트 없이 본 실행 한 번으로 "왜 21건인지" 한 줄 설명이 뜨게 했다
  (`probe_20260821_anchor_fail_census.py` 재실행으로 10+11=21 재확인).
- **재실행(수정 후, 실측)**: `대조 셀 4,516 | 불일치 0 | 앵커불가 21 (기본요구자본occ없음
  10 + 스케일비율이상 11)`, exit code 0. 처브라이프 pin 1건은 "발행사 내부 표간 불일치" 로
  별도 표시(bad 집계 제외).
- **게이트**: `validate_kics_disclosure.py` 수정 전/후 재실행 — **exit 0, Top RED offender
  10줄 byte-identical**(마스터 미변경 확인). `kics_disclosure.json` git diff 없음(마스터
  변경 0건). xlsx sync 불필요.
- **수정 파일**: `scripts/rebuild_combined_transition_after.py`(`scan_occurrences()`),
  `scripts/_probes/leaf_scale_residue_audit.py`(pin + 앵커불가 분해출력). **신규(read-only)**:
  `scripts/_probes/probe_20260824_kr0004_master_state.py`,
  `scripts/_probes/probe_20260824_market_dash_simulate.py`.
- 상세 근거·원문 인용·시뮬레이션 표는
  `inbox/_resolved/20260821T2010Z__orchestrator__MULTI__leaf_audit_residual_4_cells.md`
  `## 답변 (parser-kics, 2026-08-24 iter-2)` 절.

---

**2026-08-24(15회차) — inbox `20260824T0400Z`(validation, item52-54 적재결함) 드레인: A~E
5건 raw재확인·정정 + 근본원인 코드패치 1건 + opportunistic 2건(원 티켓 B·F). row_count
22,653→22,658(EDIT 14·DELETE 2·INSERT 5).**

- **A. 카카오페이(KR1098) 5분기 item52 100배 — 근본원인 패치.** `fix_20260824_tfi_capital_
  memo_rows.py::_infer_scale()`의 `ALL_ZERO_TRIVIAL`(47/48/49/51 전부 0 → "스케일 무관")이
  같은 버킷 item52(대개 실값, 채무성자본 0인 회사도 지급여력금액 자체는 억대)에도 그대로
  적용돼 scale=1.0을 반환, 그 뒤 더 나은 폴백(`ITEM52_VS_ITEM1_ANCHOR`)이 애초에 실행 안
  됐다. ALL_ZERO_TRIVIAL이어도 item52 vs 마스터 item1로 재확인하는 코드 추가 + 460버킷
  전수 재스캔(`probe_20260824_scale_diff.py`)으로 **변경은 정확히 이 5버킷뿐**임을 확인
  (나머지 455버킷 scale_method 완전 동일 — 다른 버킷 무손상). 기존 5셀은 idempotent guard로
  재실행해도 자동 정정 안 돼 직접 UPDATE(÷100, 5분기 raw 좌표 전부 재확인).
- **B(=원 티켓 G). 삼성화재(KR0008) 2025.3Q item52_적용후 — owner 예외승인 반영.** raw
  p16(FY2025_Q3) 재확인: 지급여력금액 PRE=28,650,195/POST=28,605,195(자릿수 전치), 비율은
  전후 275.92로 동일 인쇄, 각주 "기발행 신종자본증권 및 후순위채무가 없어 전후 동일함", 기본+
  보완자본 합계도 650,195쪽과만 일치 → 286051.95→286501.95로 정정(item50·51·item1은 이미
  정확, 불변). `50_tfi_tier_split`·`_post` 둘 다 GREEN 전환 확인. **저장소 기본원칙("발행사
  자기모순은 원문대로")의 명시적 예외 — owner 승인 2026-08-24, 이 건 1건만.**
- **C. 농협생명(KR0104) 2024.3Q item53/54_적용후 — 원인 규명(2단 레이아웃 행클러스터링
  오염) + 삭제(결측 복귀).** 해당 raw 페이지가 "(1)공통적용경과조치"(좌)+"②장수위험경과조치"
  (우) 좌우 2단 배치인데, y좌표만 보는 기존 행클러스터링(`_cluster_rows`)이 x좌표(어느 표
  소속인지)를 안 봐서 같은 높이의 우측 표 값(기본요구자본 PRE=3,791,342·생명장기손해보험
  위험액 PRE=1,900,863)이 좌측 메모행에 섞여 들어왔다 — ÷100 값이 삭제 대상 값과 소수점까지
  정확히 일치해 원인 확정. **처브라이프(KR0100) 2023.1Q item54[값]도 동일 원인**(우측 표
  "해지위험" PRE=84,006이 섞임)이라 같이 정정(840.06→0, opportunistic — 원 티켓 B).
- **D. 푸본현대(KR0083) 2024.3Q — 티켓 주장과 반대, 변경 안 함(중요).** raw p15를
  `get_pixmap(dpi=400)`으로 확대해 직접 시각확인 — 메모행(신종자본증권·후순위채무) PRE 칸이
  **대각선 취소선으로 명시적 공란처리**돼 있고 실값(40,000·505,185)은 POST 칸에 인쇄돼
  있다. 좌표로도 재확인(x1=547.9, 전각공백 보정시 ~537.9 — POST 앵커 536.9~537.2와 거의
  정확히 일치, PRE 앵커 389.5~389.8과는 148pt 이상 이격). **현재 마스터가 이미 원문과 일치
  — 스왑하지 않았다.** 티켓의 아스키 표는 좌표 없는 평문 추출로 보여 대각선 정보가 소실된
  것으로 추정(validation 재확인 요청). **부작용**: 이 판정으로 `53_tfi_memo_rows` 룰이 새
  blocking RED 1건을 냄(PRE만 보고 POST를 안 보는 것으로 보임) — 룰 파일이 금지목록이라
  못 고침, validation 판단 대기.
- **E. 행 유실 3건 INSERT(전부 raw 좌표로 PRE단일컬럼 확인).** 롯데손해(KR0003) 2026.1Q
  item53(라벨손상 "신〮자본증권" U+302E 혼입 확인, PRE=453.70) · 동양생명(KR0087) 2024.1Q
  item53·54(PRE=3445.67/0.0) · 하나생명(KR0097) 2025.2Q item53(PRE=0.0, item54 기존패턴과
  동일). **동양생명(KR0087) 2024.3Q item54(원 티켓 F, "페이지경계로 판독불가")도 다음
  페이지(p14) 맨 위에서 발견해 같이 적재**(PRE=0.0, opportunistic).
- **게이트**: `validate_kics_disclosure.py` RED=39, blocking RED **2**(D 부작용의
  `53_tfi_memo_rows`[KR0083] + validation 소관 미조사건 `2_tier1_bridge`[KR0032 2024.3Q,
  diff=-522, 내 세션과 무관] — 애초 예상 1건과 다름, 사유는 위 D 참조). 한화생명(KR0068)
  2025.2Q는 내 세션 도중 validation이 병행 owner 승인 documented exception으로 등재해
  더 이상 단순 blocking RED 아님(공유 워킹트리 병렬편집 관찰, 내가 한 일 아님).
- **pytest**: `317 passed, 1 skipped, 1 failed`(기존 302 대비 증가는 validation 동시세션이
  신규 테스트 4개 추가). golden(`test_kics_rules_golden.py`)은 데이터 변경 반영 `--update`
  (13,664 findings/488버킷, RED=39). 남은 1 FAIL=`test_tier2_issuer_inconsistent_exemption.py`
  (validation 소유, `tests/*` 금지라 못 고침) — 그 테스트 docstring이 "삼성화재 고쳐지면
  실패해야 정상"이라 명시(내 수정이 반영됐다는 신호), validation이 `held`에서
  `("KR0008","2025.3Q")` 빼면 해소.
- `sync_master_xlsx_sheet.py "K-ICS공시"`: 14 EDIT·5 INSERT·0 DELETE, 22658행×9열 완전
  일치 검증, 재실행 drift 0.
- 신규 스크립트: `scripts/fix_20260824_item52_54_load_defects.py`(A~E+부수2건, dry-run
  지원, idempotent, 항목별 raw근거 docstring). 패치: `fix_20260824_tfi_capital_memo_rows.py`
  (A 근본원인, `_infer_scale` ALL_ZERO_TRIVIAL 오적용 수정). 진단(read-only):
  `scripts/_probes/probe_20260824_item52_54_defects.py` ·
  `scripts/_probes/probe_20260824_verify_raw_AE.py` ·
  `scripts/_probes/probe_20260824_scale_diff.py`.
- **spawn_task 발주(task_66ee6d43)**: C·처브라이프가 보여준 "TFI 2단 레이아웃 행클러스터링
  오염" 패턴이 item47-54 전체 431버킷 중 다른 곳에도 더 있을 수 있어 전수감사를 별도
  세션으로 스핀오프(이번 세션은 발견된 2건만 확정 정정).
- 상세 원문 인용·좌표 재구성·게이트 대조표는
  `inbox/parser/20260824T0400Z__validation__MULTI__item52_54_load_defects.md`
  `## 답변 (parser-kics)` + `## 답변 추가 (parser-kics, 이 sender 재확인에 대한 응답)` 절
  참조(같은 파일에 validation이 병행 세션으로 붙인 "sender 재확인" 절이 있어 그에 대한
  응답도 같이 남겼다).
- **owner/validation 판단 대기**: (a) 푸본현대(KR0083) 2024.3Q 새 RED — `53_tfi_memo_rows`
  룰이 값_적용후도 보게 확장하거나 발행사 공란(PRE) 문서화 예외로 등재. (b)
  `test_tier2_issuer_inconsistent_exemption.py`의 `held`에서 `("KR0008","2025.3Q")` 제거
  (validation 소유 파일, 내가 못 고침). (c) NH농협 KR0032 2024.3Q `2_tier1_bridge` 조사(내
  소관 아님, validation이 다음 라운드에 하겠다고 명시). (d) spawn_task 전수감사 착수 여부.

---

**2026-08-24(14회차) — inbox `20260821T1425Z`(§7 "KR0032 2025.4Q parser 발주") 처리: TFI표
마지막 두 줄 신설 적재, item52 번호충돌 정정.**

- **적재**: `(기발행 신종자본증권)`→item53, `(기발행 후순위채무)`→item54. 460버킷(47/48/49/51
  중 하나라도 기존 적재) 전수 스캔 → 440버킷 성공(95.7%) · 신규 1291셀(52:428/53:431/54:432).
  row_count 21,362→22,653, combo-diff로 기존 21,362행 바이트 단위 무손상 확인, 중복 키 0,
  idempotent 재실행 확인. 미해결 20버킷은 전부 스캔/이미지 전용 필링(KB손해 6·AIA 6·카카오페이
  3·흥국화재·흥국생명·미래에셋·동양생명·하나생명 각 1) — 텍스트 추출 자체 불가, documented
  exception 후보(발주 지시문이 이 회사군 명시).
- **번호충돌 발견·정정(중요)**: 처음 표 인쇄순서대로 52=신종자본증권/53=후순위채무로 적재하고
  게이트를 돌렸는데, 출력에 "item52(TFI표 자신의 지급여력금액 행)"라는 문구가 있어 확인해보니
  `kics_json_rules.py`(축E `50_tfi_tier_split_post` 주석)·`TODO_validation.md`(§"parser 발주
  3건" ②)가 **이미 item52를 "TFI표 맨 윗줄 지급여력금액"용으로 예약**해 뒀었다(validation이
  범위검사를 등식으로 승격하는 데 쓰려던 값). 백업(`kics_disclosure.json` 21,362행 시점)으로
  되돌려 재적재 — **52=지급여력금액(validation 예약분을 이번에 같이 채움, 같은 표·같은 패스라
  추가비용 0)/53=신종자본증권/54=후순위채무**로 최종 확정. 룰 코드가 `src.get(52)`를 아직 안
  읽어서(하드코딩된 범위검사 분기) 이 값이 자동으로 등식 승격을 일으키지는 않는다 — 그건
  validation 몫.
- **자체검산 `item51==min(47,48)+49[+item54]`(432버킷)**: 기존식으로 이미 닫힘 361 · 신규식으로
  새로 닫힘 **1건(NH농협 KR0032 2025.4Q, 발주 대상 그 버킷)** · **회귀 후보 214건**(기존식은
  닫혀 있는데 item54가 실값이라 강제로 더하면 깨짐 — 현대해상 12분기 전부·한화생명 12분기·
  코리안리 다수 등, item47이 이미 후순위채무 포함값으로 보고되는 회사가 대다수) · 여전히 안
  닫힘 70건(전부 기존에 이미 알려진 발행사 자기모순/all-zero 패턴, 이번 작업과 무관). **결론:
  이 식은 전사공식이 아니라 NH농협 발행사 고유 관행 — 등식 승격보다 그 버킷 1건의 documented
  exception 근거로 쓰기를 권고.**
- **게이트**: `RED=40, blocking=13`(문서화 면제 27건 제외) — **세션 적재 전후 바이트 단위
  동일**(백업본에 게이트 별도 실행해 재확인, item52-54 완전 inert). RED를 억지로 0으로 만들지
  않음(정상 — 룰이 새 항 아직 미사용).
- **pytest**: `284 passed, 1 skipped, 1 failed`. 실패=`test_rule_coverage_manifest.py::
  test_item_coverage_matches_manifest`(item52-54가 아직 어떤 룰도 안 봐서 변이시험이
  "무방비 칸"으로 잡음 — **예상된 결과, `tests/*` 금지라 못 고침**). PRE_UNGUARDED 등재 또는
  룰 배선은 validation 후속.
- `sync_master_xlsx_sheet.py "K-ICS공시"`: 1291 INSERT·0 EDIT·0 DELETE, 검증 OK, 재실행 drift 0.
- 신규 스크립트 `scripts/fix_20260824_tfi_capital_memo_rows.py`(idempotent, `--dry-run`/`--only`,
  좌표기반 행클러스터링 — 교보류 텍스트순서 뒤섞임·한화생명류 라벨 중복인쇄·현대해상류 SCR
  단일컬럼·신한라이프 "기발생" 오식·페이지 경계 표분할 전부 실측 대응). 진단용
  `scripts/_probes/probe_tfi_full_table_rows.py`.
- **owner/validation 확인 필요**: (a) item52를 `50_tfi_tier_split_post` 등식으로 승격할지(승격
  시 214버킷 새 RED 감수 필요). (b) item54를 `51_tfi_tier2_composition`에 어떻게 반영할지(등식
  아닌 NH농협 단건 면제 권고). (c) `test_rule_coverage_manifest.py` PRE_UNGUARDED 갱신. (d)
  KB손해 등 20버킷 vision 재판독 여부. 상세: `inbox/parser/20260821T1425Z...md`
  `## 답변 (parser-kics, iter-10)`.

---

**2026-08-24(13회차) — inbox `20260821T1425Z`(orchestrator 발주, iter-9) 드레인: 잔여 5버킷
(BNP카디프 24.4Q/25.1Q·동양생명 25.2Q·한화생명 25.2Q·예별손해 25.1Q) 전부 raw 원문 재대조,
데이터 변경 0.** `fitz.get_text()` 전체 페이지 텍스트 덤프로 5필링 다 재확인 — 마스터 값이
원문과 완전히 일치했다(숨은 행·미러링·좌표오독 전부 없음). 판정: BNP 2건·동양생명 1건은
발행사 표 자기모순 재확인(item51≠min(47,48)+49 — gap이 item49 대비 상수비율 아님, 3분기
실측 6.2%/26.3%/20.1%). 한화생명은 판정불가 유지(item51_후−item51_전=825.75 ≈ bridge잔차
826 이라는 새 단서는 남겼으나 인과 미확정). **예별손해는 분류 정정**: item2 bridge는
`-2,629-0-19=-2,648=item2` 로 원래도 잔차 0이었다 — 실제 잔차는 `3_tier2_composition`
(TFI표 스코프차이)뿐이고 기존 면제 초안이 이미 맞는 축에 걸려 있었다. 게이트
`exit 2, blocking RED=39`(iter-8과 동일, 변경 없음) · `pytest 256 passed 1 skipped` ·
xlsx sync drift 0. 상세: `inbox/parser/20260821T1425Z...md` `## 답변 (parser-kics, iter-9)`.

**2026-08-22(12회차) — inbox `20260821T1425Z`(validation, iter-5) 드레인: tier2 "데이터
결함 17건" 처리 + 하나생명 false-green 정정. row_count 21,359 → 21,362(EDIT 15·INSERT 8·
DELETE 5).**

- **A. 신한이지(KR0051) 2023.1Q~2023.3Q — census PARTIAL_ROWS 6건 수정.** 이전 라운드가
  "라벨/값 완전분리 블록이라 저신뢰"라며 되돌린 진단(`task_288fece4`, `fix_20260821_revert_
  sinhanez_low_confidence.py`)이 틀렸다 — `page.get_text("words")`로 y를 반올림 없이 정렬하면
  라벨-값이 1.1pt 오프셋으로 명확히 페어링된다(스트림 순서(block index)만 뒤섞였을 뿐, 좌표는
  정상). 2023.1Q/2023.2Q는 item47에 item49(해약환급금 초과분) 값이 잘못 들어가 있었다(원문
  47은 "-"=0). 47을 0으로 정정, 48/49 신규 INSERT. 2023.3Q는 47은 이미 정확, 48 신규
  INSERT(0), 49는 0→1.45로 정정(원문 145백만원 명시). 3분기 전부 `min(47,48)+49==item51스코프`
  자체검산 소수점까지 통과.
- **B. 교보생명(KR0073) 2023.3Q·2024.1Q·2024.3Q·2025.3Q — `50_tfi_tier_split_post` 4건
  수정.** 교보 특유의 fitz 텍스트순서 뒤섞임(기존 결함A·버그4/5와 동일 계열)이 이번엔 item47_후·
  50_후·51_후 세 항목에서 터졌다 — 47_후·50_후는 적용전 값이 그대로 미러링, 51_후는 쓰레기값
  (0.10~0.15)이었다. word-좌표로 4분기 전부 재구성(validation이 준 정답 후보를 그대로 안 쓰고
  독립 재현 — 1원 단위까지 일치). 적용전/48/49는 이미 정확해 불변, 적용후 3항목만 EDIT.
- **C. 미래에셋생명(KR0079) 2023.3Q — census(+-post) 2건 수정(신규 INSERT).** TFI=O인데 표
  부재로 판정된 유일한 진짜 RED. 전 페이지 스캔본(텍스트 30~230자/p, 이미지 100+개/p)이라
  `get_pixmap(dpi=240)` 렌더링 필요 — p12에 `[지급여력비율의 경과조치 적용에 관한 사항]` 표가
  실제로 있다(육안 판독 후 zoom 재확인). 47/48/49 신규 적재(8153.24/9993.36/3207.02, 이
  회사는 "업무보고서 보고·공시기한 연장만 적용"이라 전=후).
- **D. 하나생명(KR0097) 2024.4Q — false-green 정정(최우선 처리).** raw(347p 번들 "2024년
  하나생명보험회사의 현황", 보험업법 124조 근거 **연간 종합공시** — 정기경영공시 아님)에
  "보완자본 한도 적용 전" 정확 문구가 0회인데 마스터엔 `item47=item48=item51=item3=3452.36`
  으로 헤드라인 item3가 그대로 복사돼 있었다. 그 복사가 `3_tier2_composition`을 속여 GREEN을
  냈다(진짜 false-green — validation이 census 중복행 검사로 잡음). item49=1776.3도 이 문서
  어디에도 근거 없음. **item47/48/49/50/51 5개 항목 전부 DELETE(결측 복귀)** — item1/2/3/14는
  이 문서의 다른 표(p280 Ⅳ.기본자본/Ⅴ.보완자본/Ⅵ.자본감소분경과조치)에서 이미 올바르게
  파생돼 손대지 않았다(단 item2_후가 Ⅵ 전액을 기본자본에 귀속시킨 값인지는 별도 확인
  필요 — items 47-51 스코프 밖이라 관찰만 기록).
- **E. `item47==item48==item51==item3` 동시성립 지문 전수 스캔(핵심 산출물, 21,359행 기준
  460버킷) — 하나생명 1건(위 D로 정정) + 카카오페이(KR1098) 7분기(전부 legit).** 카카오페이는
  raw가 47/48/49/51/item3 전부 "-"(=0)로 명시 인쇄하는 채무성자본 무보유 회사 — 2023.1Q를
  word-좌표로 독립 재확인(기존 "raw 직접 인쇄 재확인" 결론과 일치). 정정 후 재스캔 결과
  하나생명 지문은 사라지고 카카오페이만 남음 — **다른 오염 사례 없음.**
- **F. downloader 발주 — 5건 냈다가 스스로 철회, 최종 0건.** 처음엔 하나생명 2024.4Q·AIA
  2024.4Q·AIA 2025.4Q·KB손해 2025.4Q·흥국생명 2024.4Q 를 "raw 표지가 OOO보험회사의 현황(연간
  종합공시)"이라며 발주했으나, `docs/changelog_parser_kics.md` "2026-08-21(7회차)"(흥국생명
  wrong-document 3연속 오판정 전례)를 뒤늦게 보고 마스터를 재확인 — **4건(AIA×2·KB손해·
  흥국생명)은 이미 items 1-51 이 정상 적재돼 있었다**(흥국생명 raw p49 를 다시 렌더링해
  확인 — 스캔 페이지라 텍스트 키워드 검색만으론 0회로 보일 뿐, 표는 있었다). **하나생명도
  "wrong document"가 아니라 raw p48 이 `TFI = X`(제도시행前 기발행자본증권 인정범위 확대
  미선택)를 명시**하고 있었다 — 47-51 결측은 맞지만 이유가 달랐다. 발주할 게 없어
  `inbox/downloader/...wrong_source_document...` 삭제,
  `data/_derived/kics_transition_applicability.json`(`scripts/apply_transition_vision_
  overrides.py`) 정정(하나생명 TFI UNKNOWN→X, 나머지 4건 WRONG_DOCUMENT 오분류 철회).
  상세는 inbox 답변 §4(자기정정 기록으로 남김 — "키워드 0회=원문 없음"을 나 스스로도
  반복했다).
- **G. 롯데손해(KR0003) 2026.1Q·예별손해(KR0004) 2025.1Q — raw 재확인, 무변경.** 롯데손해는
  2025.4Q TFI표를 비율만 바꿔 재게시(기확정 재검증, raw p22 vs p77 word-좌표 완전대조 — 6개
  항목 전부 백만원 단위까지 동일). 예별손해는 raw가 47/49=0을 명시 인쇄(결측 아님), 헤드라인-
  TFI표 스코프차이(코리안리 등과 동일 패턴). 둘 다 면제 초안만 남김, **등재 안 함**(owner
  승인 필요).
- **게이트**: `validate_kics_disclosure.py` blocking RED **53 → 39**(rule 3_tier2_composition
  14·2_tier1_bridge 8·47_tier2_census 5·51_tfi_tier2_composition 5·47_tier2_census_post 4·
  50_tfi_tier_split 2·50_tfi_tier_split_post 1). 내가 손댄 6개 버킷(17칸)은 전부 RED=0
  확인(JSON report 개별 대조), 롯데손해·예별손해는 §G대로 RED 유지(억지로 0 안 만듦).
  `pytest tests/ -q --ignore=tests/test_pl_breakdown_golden.py --ignore=tests/test_ifrs17_bs_
  golden.py` = 256 passed·1 skipped. `test_kics_rules_golden.py --update`(데이터 반영,
  룰 코드 무변경). `sync_master_xlsx_sheet.py "K-ICS공시"` — 변경 셀 4(내 세션분) + 추가
  955행(item50/51 백필 누적 drift — 이전 세션들 몫, 이번에 처음 xlsx sync됨) + 삭제 0, 검증
  OK(21,362행×9열 완전일치), 재실행 drift 0.
- 상세 원문 인용·좌표 재구성 로그·항목별 표는
  `inbox/parser/20260821T1425Z__validation__MULTI__tier2_limit_lines_missing.md`
  `## 답변 (parser-kics, iter-8)` 절 참조. 신규 스크립트:
  `scripts/fix_20260822_tier2_dataquality17.py`(dry-run 지원, idempotent, 근거 docstring
  포함).
- **owner/validation 판단 대기**: (a) 롯데손해·예별손해 면제 초안 2건 승인 여부(§G). (b)
  하나생명 item2_후(Ⅵ.자본감소분경과조치 귀속) 재검토 필요 여부 — 47-51 스코프 밖 관찰사항.
  (c) downloader 발주 없음(§F 철회) — 후속 대기 항목 아님.

---

**2026-08-22(사이드 조사, orchestrator 발주) — 경과조치 적용여부표(TFI 등 7종) 전수 추출,
`kics_disclosure.json` 변경 없음(신규 파생 파일만 생성).** orchestrator가 `TIER2_TABLE_ABSENT_
INTERMITTENT` 38버킷 RED 승격 기준("다른 분기에 공시했으니 추출갭")이 틀렸다고 자체 철회 —
교보라이프플래닛(KR1010) 확인 결과 TFI(제도시행前 기발행자본증권 가용자본 인정범위 확대)가
X인 분기엔 발행사가 item47-51 근거표 자체를 안 그린다(결측 아님, 정상). (회사×분기) 494버킷
전수를 열어 TFI 포함 7종 적용여부(O/X)를 뽑았다.
- **신규 산출물**: `data/_derived/kics_transition_applicability.json`(494레코드, 키=
  (원보험사코드,공시분기)) — TFI: O 354·X 108·NA 8·UNKNOWN 24(95.1% 확정). NA=원문이 "-"를
  직접 인쇄한 3번째 실측값(에이비엘생명 등), UNKNOWN=못 읽음(X로 안 채움).
- **우선순위 25버킷 중 21건 확정**(O 9·X 8·확정불가 4) — 교보라이프플래닛 6/7분기·카카오
  페이손해·AIA 5/6분기 등 TFI=X(정상 부재, RED 아님) vs KB손해·흥국화재·롯데손해·동양생명·
  삼성생명·BNP카디프 TFI=O(진짜 추출갭). 확정불가 4건(AIA 2건·KB손해 1·흥국생명 1)은
  **raw PDF가 정기경영공시가 아닌 다른(번들) 문서로 추정**(96~538p인데 '경과조치' 키워드
  raw PDF 전체 0회) — vision으로 못 고침, 4건 중 3건이 4Q(결산)에 몰려 있어 downloader
  재확인 후보.
- **`_TRANSITION_KIND` 레지스트리 대조 71건 불일치** — 고신뢰 갭 3건(BNP카디프 TIR 13/13분기
  O인데 registry `{}`·에이비엘생명 TAC 최근 5분기 연속 O인데 registry에 AC 없음·카카오페이
  초기 3분기 TAC+TIR O 후 중단), 조건부INT 메커니즘과 일치하는 정상 39건(NH농협손해·DB생명·
  하나생명 TIRR 100% X — 코드 주석의 "조건부 발동"과 부합), 저신뢰 초기분기(2023.1~3Q)
  단발성 29건은 검증 안 함.
- 게이트는 이 데이터를 아직 안 씀(요청대로 RED 수는 지표 아님).
  `pytest tests/ --ignore=...golden×2` = 249 passed·1 skipped(악화 없음, `kics_disclosure.json`
  등 골든 대상 파일 미변경).
- 상세 원문 인용·재현 커맨드·전수표는
  `inbox/parser/20260821T1425Z__validation__MULTI__tier2_limit_lines_missing.md`
  `## 답변 (parser-kics, iter-6)` 절 참조(같은 티켓, 별개 스레드 — tier2/item47-51 조사와
  무관). 신규 스크립트: `scripts/extract_transition_applicability.py`(메인 추출기)·
  `scripts/apply_transition_vision_overrides.py`(vision 8버킷+wrong-document/structurally-
  absent 5버킷 병합). 진단 probe: `scripts/_probes/render_pages.py`(vision용 PDF 렌더)·
  `cross_check_transition_registry.py`(레지스트리 대조).
- **owner/orchestrator 판단 대기**: (a) AIA 2024.4Q/2025.4Q·KB손해 2025.4Q·흥국생명 2024.4Q
  raw PDF 재확인 필요 여부(downloader 발주 후보, 내가 직접 발주 안 함). (b) 레지스트리 3건
  갱신 여부(내가 손 못 대는 파일). (c) 남은 TFI UNKNOWN 24건(미래에셋생명 9·KB손해 잔여 등,
  전부 확인된 스캔전용) vision 추가 발주 여부 — 이번엔 우선순위 밖이라 안 함.

---

**2026-08-22(사이드 조사, orchestrator 발주) — "나중에 공시 예정" 근거 결측 전수 재확인,
`kics_disclosure.json` 변경 없음(읽기 전용).** owner 지적("2024년말 공시예정이 2026년 8월까지
안 올라왔겠냐") 대응. 악사(KR0049) 2024.3Q tier2(47-49) 5줄은 raw 전수(FY2024_Q4·2025 4개
분기·메리츠 대조군) 확인 결과 **구조적 결측 확정**(15-23후와 동일 원인 — "[지급여력비율의
경과조치 적용에 관한 사항]" 표가 당분기 전용이라 과거분기 열 자체가 없음). "공시예정/유예/
부칙" 문구 저장소 전수 census(497개 parsed MD grep) = 6회 출현/5개(회사,분기), **결측은
악사뿐**, 나머지 4개(회사,분기)는 이미 완전 적재+raw 일치 확인(문구는 안 지워진 stale 각주).
현대해상·하나손해 2023.1Q도 재확인 — 결측 아니고 "경과조치 전면 미적용"이 원문 그대로 완전
적재돼 있음(하나손해는 "전후 동일" 명문 진술까지 있어 기존 B3b 분류보다 강한 근거, validation
참고용). TODO.md L221 documented exception에 staleness 재확인 노트 + 47-49 동일사유만
추가(등재 삭제 없음). 로드할 값이 없어 `--dry-run` 스크립트 없음. 상세는
`inbox/parser/20260821T1425Z` `## 답변 (parser-kics, iter-7)`.

**2026-08-22(11회차) — inbox `20260821T1425Z`(validation, iter-2 재확인) 드레인: tier2
잔여 blocking RED 34건 중 데이터 쪽 처리. row_count 20,390 → 20,407(EDIT 13·INSERT 17·
DELETE 0).**

- **A. AIA(KR0080) 2023.2Q 코어항목 오염 발견 + 수정(tier2 조사 중 우연히 발견, 스코프
  밖이지만 즉시 수정).** items 1/2/3/12/13/14/15/16/19/20/22/27/28(총 13항목)이 raw
  PDF·Docling MD 어디에도 없는 값으로 채워져 있었다(예: item2=29645, "29,645" 문자열이
  35페이지 전체에 0회). fitz 텍스트 + `get_pixmap(dpi=240)` 시각대조로 raw 재확인 후
  정정. item19 정정이 `19_market` 룰을 새로 RED로 노출시켜(item37도 같은 오염, 1745.46→
  1957.14) 같이 잡음(R4·MARKET_M 공식 재현으로 재귀검증, diff ±0.5 이내). items 5-11 은
  raw 와 다르지만 합계가 item4 와 우연히 일치해 룰 무방비 — 손 안 대고 `task_cf8eebfb`
  로 전사감사 발주(다른 AIA 분기·다른 회사에도 있는지 미확인).
- **B. 롯데손해 2026.1Q 전기잔존 — 확정, 수정 불가.** raw p22 `(1)공통적용경과조치` 표가
  2025.4Q 필링과 지급여력비율 행만 빼고 완전히 동일(발행사 자체가 비율만 갱신하고
  나머지 복붙). 표 자체 내부모순 확인(인쇄비율 131.93% vs 표 자체 재계산 126.07%).
  당분기 진짜 값이 필링 어디에도 없어 결측 유지. 439칸 전수 스캔으로 이 회사만의
  유일 사례임을 확인.
- **C. 중복행4+계열이탈2 — 6건 전부 예측 반증, 현재 마스터 값이 이미 정확.** BNP카디프
  3분기(한도적용전=한도 그대로 원문 인쇄, `get_pixmap` 확인)·동양생명 2025.2Q(동일
  패턴)·NH농협손해 2025.4Q·한화생명 2025.2Q 전부 raw 재확인 결과 예측값이 틀렸고 현재
  값이 맞았다. 데이터 변경 없음.
- **D. 원문재확인 6건(원 티켓 5항목) — 전부 정당, 발행사 헤드라인표 vs TFI표 소액~중액
  불일치.** 롯데손해 3분기·NH농협손해 1건·예별손해 1건 전부 개별항목 raw 일치, 자기무결성
  (기본자본+보완자본=지급여력금액) 확인. 데이터 변경 없음, 원인미상 잔차는 있는 그대로 둠.
- **E. 코리안리 6분기+1(2024.4Q) — item50/51 신규 항목 적재 완료(룰 배선 없음, 요청대로).**
  `(1)공통적용경과조치` 표 자신의 기본자본·보완자본 행 7분기분 raw 재추출(자체검산: 같은
  표 안 기본자본+보완자본=지급여력금액 diff≤1). **6분기(2023.2Q~2024.3Q)는 item51_후
  (POST)가 마스터 item3(헤드라인)과 일치**("헤드라인=TFI-POST 스코프") — composition 룰
  배선 시 GREEN 전환 유력. **2024.4Q는 반대로 item3/item2 가 item51_전/item50_전(PRE)과
  일치**하는데, 이 분기는 다리식을 PRE 스코프로 다시 짜도 잔차 −1,090 이 그대로 남는다
  (직접 계산 확인) — **bridge 1건은 item50/51 적재로 저절로 안 풀린다**(최초 초안의
  "7건 자동 GREEN" 주장은 재계산 후 정정, 상세는 티켓 참조).
- **F. 동양생명(KR0087) 2026.1Q vision 판독 완료 — item47/48/49 신규 적재.** 완전 스캔본,
  `get_pixmap` 3페이지(p13/16/17) 판독. items 1-46 은 이전 라운드 vision 값과 전부
  재확인 일치. 47/48/49 적재만으로 bridge 잔차 943 자동 해소(값 수정 없음, 순수 결측
  채움). "판독불가" 아니었음.
- **G. `tier2_scale_provenance.json` ambiguous 11칸 — 전부 확정, 데이터 변경 없음.**
  롯데손해 2026.1Q(=B 항목) · 신한이지 9칸(3칸 저신뢰 SKIP 유지 확인·6칸 CAPPED 자명
  통과 재확인) · 카카오페이 2025.1Q(CAPPED 통과 재확인).
- **게이트**: `validate_kics_disclosure.py` blocking RED **34 → 31**(3_tier2_composition
  15→14·2_tier1_bridge 10→8·47_tier2_census 5(불변)·47_tier2_census_post 4(불변)).
  잔여 31건 = 코리안리 7(데이터 공급 완료, 룰 배선 대기) + 발행사 원본 불일치 24(수정
  불가 확정). `validate_data_contract.py` RED 20→19(부분집계라 축소폭 다름, 같은 회사·
  분기). `pytest tests/ -q --ignore=tests/test_pl_breakdown_golden.py
  --ignore=tests/test_ifrs17_bs_golden.py` = 220 passed·1 failed(예상됨)·1 skipped —
  실패는 `test_rule_coverage_manifest.py::test_item_coverage_matches_manifest`(신규
  item50/51 이 아직 룰 무방비라 정확히 잡아냄, 이 테스트는 손대지 말라는 파일이라
  안 고침 — validation 이 `PRE_UNGUARDED` 에 등재하거나 룰을 배선해야 해소됨).
  `test_kics_rules_golden.py` 는 데이터 변경 반영해 `--update`(룰 코드 무변경).
  `sync_master_xlsx_sheet.py "K-ICS공시"` 20,407행×9열 완전일치, drift 0.
- 상세 원문 인용·재현 커맨드·항목별 표는
  `inbox/parser/20260821T1425Z__validation__MULTI__tier2_limit_lines_missing.md`
  `## 답변 (parser-kics, iter-4)` 절 참조. 신규 스크립트:
  `scripts/fix_20260822_tier2_followups.py`(A·B의 AIA 정정 + 코리안리 item50/51 + 동양생명
  47-49, 전부 dry-run 지원·idempotent). 진단 probe 다수는
  `scripts/_probes/probe_20260822_*.py`(전부 read-only).
- **owner/validation 판단 대기**: (a) 코리안리 item50/51 을 쓰는 RED 룰 신설 여부(§E,
  자체검산 근거 있음). (b) `test_rule_coverage_manifest.py::PRE_UNGUARDED` 에 item50/51
  등재 여부(내가 손 못 대는 파일). (c) AIA 코어항목 오염 전사감사(`task_cf8eebfb` 발주됨) —
  다른 AIA 분기·다른 회사에도 있는지 미확인.

---

**2026-08-21(10회차) — inbox `20260821T1425Z`(validation, iter-3) 드레인: tier2(항목47-49)
룰 8축 배선 후 blocking RED 63건 대응. row_count 20,381 → 20,390(INSERT 9·EDIT 4·DELETE 0).**

- **버그 5종 원인규명 + 수정 (RED 63 → 43, 20건 해소)**: ① item49 라벨 4-way 단어분할
  미탐지(동양생명 5분기·NH농협손해 2분기 census 결측) — `LABEL49_HEAD` 접두어매칭 허용으로
  해결. ② `"ㅡ"`(U+3161 한글채움문자, 박스드로잉 대시 아님) 미인식(라이나생명 1분기 item47
  결측) — ZERO/DASH 집합에 추가. ③ item48≈0 스케일단축이 47/49에도 무차별 적용(카카오페이
  2025.1Q item49 100배 오류) — 47·49도 함께 trivial일 때만 단축, 아니면 SCR앵커 2차축으로
  재시도. ④⑤ 교보생명 텍스트순서뒤섞임으로 item49가 엉뚱한 행(기본자본) 값을 집음
  (2024.4Q composition diff -58,059·2025.4Q census 결측) — `page.get_text("words")` 좌표로
  진짜 값 확정, 전·후 컬럼 다 CAPPED 공식 diff≤0.15로 재현 확인 후 수기 정정.
  (부수발견·즉시원복: 신한이지 3분기 라벨/값 완전분리 블록 — 저신뢰라 4행 INSERT 후 DELETE,
  RED-63 범위 밖이라 `spawn_task`로 별도 티켓(`task_288fece4`) 발주.)
- **잔여 43건 — 8개 원인 카테고리, 전수 원문대조 완료(고칠 셀 없음)**: A) "제로패턴"
  13건(메트라이프 10·카카오페이 2·예별손해 1 — 채무성 자본 자체가 없는 회사, raw에 47=48=
  49=0 직접 인쇄 재확인, 최우선 재확인 과제였던 "0이 진짜 인쇄값인가" 원래 판정 유지).
  B) "재분류전액(RECLASS_ONLY)" 7건(BNP카디프 5·AIA 2 — item13==item3 소수점까지 정확
  일치, 47/48/49와 무관한 세 번째 보완자본 구성패턴, 룰의 CAPPED/UNCAPPED 이분법에 없음).
  C) "헤드라인표 vs TFI표 스코프차이" 7건(코리안리 6분기연속·NH농협손해 1 — 코리안리는
  word좌표까지 대조, "해당분기" 헤드라인 컬럼이 TFI-post와 일치하는 회사가 있음을 확인).
  D) "item12<한도초과로 다리식 뺄셈이 음수붕괴" 6건(KDB생명 4·아이엠라이프 1·NH농협손해 1)
  + 한화생명 2025.2Q 극단사례(diff -69,995, RED-63 중 최대, 8개 항목 전부 raw 확인).
  E) "한도초과=0, 순수 코어잔차(tier2 무관)" 4건. F) 미세잔차(<1%) 6건. G) 원인미상 1건
  (롯데손해 2026.1Q). H) 스캔본 결측 1건(동양생명 2026.1Q, fitz 텍스트 0·Docling MD도 0건).
  전부 원문 인용 포함 상세는 inbox 파일 참조. **면제 등재는 안 함** — owner/validation
  승인 후보 6개를 §3에 나열만.
- **스케일 provenance 산출**(validation §4 요청): `fix_20260821_tier2_limit_lines.py` 계측,
  `data/_derived/tier2_scale_provenance.json`(전수 스캔시만 갱신). 439건 중 해결 438·
  미해결(삼성생명 2025.4Q, 기존에 알려진 반전레이아웃) 1·ambiguous 11(신한이지 9 포함,
  롯데손해 2026.1Q는 validation의 기존 "발행사자기모순, 스케일사고 아님" 판단과 실측 정확히
  일치).
- **게이트**: `validate_kics_disclosure.py` blocking RED 63→**43**(exit 0 못 만듦, 사유
  = 43건 전부 개별항목 원문일치·룰 차원 미해결). `validate_data_contract.py` RED=24(같은
  43건의 부분집계). `pytest tests/test_kics_rules_golden.py tests/test_tier2_limit_rules.py
  tests/test_rule_coverage_manifest.py tests/test_identity_tautology.py
  tests/test_post_transition_golden.py tests/test_deploy_assets.py` 63 passed(골든은 데이터
  변경 반영해 `--update` 재생성, 룰 코드는 미변경). `sync_master_xlsx_sheet.py "K-ICS공시"`
  20390행×9열 완전일치, drift 0.
- 상세 원문 인용·재현 커맨드·카테고리별 표는
  `inbox/parser/20260821T1425Z__validation__MULTI__tier2_limit_lines_missing.md`
  `## 답변 (parser-kics, iter-3)` 절 참조. 신규 스크립트:
  `fix_20260821_kakaopay_2025q1_item49_scale.py` ·
  `fix_20260821_kyobo_2024q4_item49.py` · `fix_20260821_kyobo_2025q4_item49.py` ·
  `fix_20260821_revert_sinhanez_low_confidence.py`(전부 dry-run 지원, idempotent).
  진단 probe 다수는 `scripts/_probes/probe_20260821b_*.py`(읽기전용).
- **owner/validation 판단 대기**: TODO_parser_kics.md 위 "잔여 43건" 6개 카테고리의 룰
  개정/면제 여부(inbox §3 상세). 동양생명 2026.1Q vision 판독 시도 여부.

---



**2026-08-21(9회차+정정) — orchestrator가 tier2(항목47-49) 커밋 전 전수검산에서 결함 2건을
잡아 정정 요청. 근본원인 규명 + 수정 + 재검증 완료. row_count 최종 19,082→20,381.**

- **결함A(교보생명 홀수분기 5개, 47/48/49 최대 150배 오류) — 수정.** 근본원인은 raw 추출값이
  아니라 **스케일 판별**이었다 — 교보생명 일부 페이지는 fitz 텍스트순서가 뒤섞여(라벨보다
  값이 먼저 나옴) 기존 "표 자신의 지급여력기준금액 종결행" 앵커탐색이 엉뚱한 occurrence를
  집어 스케일을 1.0으로 오판(진짜는 0.01)했다. **앵커를 표 자기참조에서 `item48==마스터
  item14×50%`(신뢰도 높은 독립 항등식, 결함C 조사로 435/436=99.8% 검증됨)로 교체**해 해결.
- **결함B(DB생명 2026.1Q item48, 100만배 오류) — 수정.** 근본원인은 일부 행이 전/후 두 값을
  **한 줄에 공백으로 붙여** 인쇄하는데(`"743,755   743,755"`), 기존 코드가 줄 전체를 공백제거
  후 한 토큰으로 봐서 콤마만 있는 "743,755743,755"가 우연히 숫자 정규식을 통과, 두 수가
  이어붙은 채 하나의 값으로 읽혔다(÷100=74억 vs 실제 74.4). **값 캡처를 줄 전체가 아니라
  공백 토큰 단위로 재작성**(`_collect_values` 신설)해 해결.
- **결함C(item48_적용후가 429/430칸에서 적용전과 동일 — 복사 의심) — 조사 후 "버그 아님"
  판정, 결측처리 안 함.** raw 직접대조로 4중 확증: ① 한화손해·AIA 등에서 "한도" 행이
  원문 그대로 두 컬럼에 동일 숫자로 인쇄돼 있음(같은 표의 다른 행은 실제로 다름 — 못 읽는게
  아니라 이 행만 원래 같음). ② `item48=item14(마스터,전)×50%` 항등식이 표 자신의 SCR이
  컬럼간 실제로 다른 41개 사례에서조차 **항상 전(前) 기준**으로 고정됨을 확인 — "한도"는
  TFI(공통적용경과조치)범위 안의 값이라 규정상 SCR변동과 무관. ③ 220칸("item14는 전≠후인데
  item48은 미러")의 정체 = **스코프 차이**(마스터 item14_후=TFI+선택 전체결합, 이 표의
  한도_후=TFI단독 — 다른 개념을 비교했을 뿐). ④ 단일값(len==1) 미러링 폴백은 "전후동일"
  각주가 있는 회사(메트라이프·카카오페이 등)에서만 발동, raw 자체가 단일컬럼임을 확인.
  **validation에 알림**: `item48_후`를 `item14_후(전체결합)`와 비교하는 RED 룰을 짜면 이
  스코프차이로 220건이 체계적으로 어긋난다 — 룰 설계 시 반영 필요.
- **재커버리지**: 39사 488(회사,분기) 중 OK 435(89.1%, 결함 수정 전 432보다 오히려 증가 —
  결함C 조사 중 발견한 "전후동일 각주 회사는 0/0/0 원문 그대로가 정상"이라는 사실로
  메트라이프·카카오페이 다수 분기가 추가 복구됨). 잔여 미검출 49 + 스케일불명 4(신한이지
  홀수 3개·삼성생명 2025.4Q 1개, 이 필링만 라벨-값 순서가 반전된 유일 레이아웃이라 게이트가
  안전하게 적재 거부 — 강제 재파싱 안 함, 위험 대비 이득 낮음 판단).
- **자체검산(orchestrator 요청) 결과**: `item48==item14×50%` 전사 검사 — 값(전) 436건 중
  411 일치(94.3%, 배율>10x **0건**), 값_적용후 436건 중 195 일치(44.7%, 결함C 스코프차이로
  설명됨, 최대배율도 2.1x로 스케일사고와 질적으로 다름). 신규 상주 스크립트
  `scripts/_probes/probe_20260821_tier2_item48_anchor_check.py`.
- **게이트**: `validate_kics_disclosure.py` exit=0(RED=1 불변, 기존 documented exception) ·
  `validate_data_contract.py` exit=0(RED=0 YELLOW=296) · pytest 3종 12 passed(골든 불변,
  룰이 47-49를 아직 안 봐서). xlsx 재동기화 완료(20,381행, drift 0).
- 상세 원문 인용·재현 커맨드는 `inbox/parser/20260821T1425Z__validation__MULTI__tier2_limit_lines_missing.md`
  "## 정정" 절 참조.

---

**2026-08-21(9회차) — inbox 3건 순차 드레인: 임무1(leaf잔차 4셀 판정, 전부 마스터 정확·수정 0)·
임무2(신규 항목47-49 "보완자본 한도" 3줄, 432/488(회사,분기) 1,285셀 INSERT)·임무3(KB손해
2025.1Q item17후·19후 vision 판독, 기존 미러링 정확 확인). row_count 19,082→20,367
(전부 INSERT, DELETE 0). 게이트 `validate_kics_disclosure.py`·`validate_data_contract.py`
둘 다 RED=0 유지. (아래 원 기록 — 정정 내용은 위 최상단 항목 참조)**

- **임무1 — leaf 잔차 4건 전부 마스터가 이미 맞음(수정 0건).** 예별손해(KR0004) item36후=0.00은
  틀린 게 아니라 옳다 — raw "③ 주식위험 경과조치 또는 금리위험 경과조치" 표의 금리위험 행이
  전=65,239/후="-"인데, 이 회사는 그 대시를 "캐리포워드"가 아니라 "인정액 0"으로 산출한다.
  증거: 회사가 직접 인쇄한 시장위험액후 합계(110,677/116,622/134,130백만)를 MARKET_M으로
  독립 재현하면 금리후=0 가설이 diff 0.03~0.58(사실상 정확)로 맞고, 금리후=652.39(캐리포워드)
  가설은 26,000~38,000백만 벗어난다(`scripts/_probes/probe_20260821_kr0004_verify.py`).
  처브라이프(KR0100) item35전=46.81도 맞음(전용 대재해위험표 p55 소싱, `_is_life_catastrophe_
  table` 가드 설계대로) — 감사기가 집은 44.99는 다른 표(② 경과조치 결합표)의 발행사 내부
  별도산출치일 뿐. 아이엠라이프(KR0076) parent17=1459.26도 맞음(회사 직접 공시 subtotal,
  leaf 역산과의 diff 9.91=0.68%는 정상 반올림 캐스케이드, 게이트 8_life 허용오차 72.96 이내).
  "앵커불가 21"의 정체 확인: 11건=4Q 필링 후미 감사보고서 부속명세서가 같은 표를 천원단위로
  중복인쇄(감사기가 최댓값을 앵커로 오채택) · 10건=교보생명(KR0073) 홀수분기(6건, 텍스트스트림상
  라벨·값이 분리된 레이아웃) + 기존에 알려진 wrong-document/스캔본 4건. 전부 진단
  스크립트(`leaf_scale_residue_audit.py`)만의 한계, production 파이프라인은 영향 없음.
- **임무2 — 신규 항목번호 47/48/49("보완자본 한도" 3줄) 적재, 432/488(회사,분기) 88.5%.**
  `[지급여력비율의 경과조치 적용에 관한 사항] 1) 공통적용 경과조치` 표에서 추출. **처음
  블라인드 ÷100(티켓 지시)으로 구현했다가 전사검산(item14 대조)에서 439건 중 128건(29%)이
  이미 억원으로 인쇄돼 있음을 발견 — `git checkout`으로 되돌리고, 표 자신의 "지급여력기준금액"
  종결행을 앵커로 (회사,분기)별 스케일을 직접 판별하는 방식으로 재작성**(기존
  `rebuild_combined_transition_after.py` 앵커링 방법론 재사용). 라벨 줄바꿈 3변형(한줄/두줄/
  단어중간줄바꿈)과 텍스트 인접중복(한화생명 등, 라벨·값이 연속 2~4회 찍힘)도 처리.
  자체검산 중 티켓의 공식(`보완자본=min(한도적용전,한도)+초과분`)이 **보편적이지 않음을
  발견**(한화생명·BNP카디프·KB손해는 `보완자본=한도적용전` 그대로, 공식 대입시 오차 큼) —
  validation에 반례 원문인용과 함께 보고, RED 룰 배선 전 재확인 권고. 미검출 49건 대부분
  기존 KICS-IMG(KB손해·미래에셋) 코호트와 겹침, 신규 발견은 교보라이프플래닛(KR1010)의
  "TFI 자체 미신청"(구조적 결측, 정상) 뿐.
- **임무3 — KB손해(KR0010) 2025.1Q item17후·item19후 SOURCE_UNREADABLE_NOT_VERIFIED 판정
  완료.** raw는 fitz 텍스트밀도 10.0자/p로 게이트가 UNREADABLE 분류했으나, `get_pixmap(dpi=220)`
  렌더링은 또렷하게 읽힌다(래스터 스캔본이 아니라 폰트매핑 문제). 3페이지 vision 판독으로
  이 회사가 공통(TFI)·선택(TAC/TIR/TER·TIRR) **전부 미신청**임을 원문 명시 각주로 확인
  (p17 "당사는 ~ 적용하지 않아 경과조치 전·후 금액 및 비율이 동일함" ×3). 마스터의 기존
  item17후=59603·item19후=31978 미러링은 이미 정확 — **데이터 변경 없음**(값 검증만). 게이트의
  텍스트밀도 휴리스틱은 fitz 결과가 안 바뀌어 계속 YELLOW를 찍겠지만 RED 아니라 비차단.
  부수: 같은 페이지에서 항목47/48/49도 발견해 vision 판독으로 추가 적재(임무2 커버리지
  +1(회사,분기), `scripts/fix_20260821_kr0010_2025q1_vision.py`).
- **게이트 재검증(최종)**: `validate_kics_disclosure.py` RED=1(불변, 기존 documented exception
  KR0079 2023.2Q 8_life). `validate_data_contract.py` RED=0 YELLOW=296(KB손해 등 YELLOW는
  텍스트밀도 휴리스틱상 불변, 비차단). `pytest tests/test_kics_rules_golden.py
  tests/test_identity_tautology.py tests/test_post_transition_golden.py` 12 passed(`--update`
  불요 — 신규 항목47-49를 참조하는 룰이 아직 없어 골든 스냅샷 범위 밖).
  `insurequant_master_tables.xlsx` `sync_master_xlsx_sheet.py "K-ICS공시"`로 동기화
  (20367행×9열, 마스터와 완전 일치 검증).
- **xlsx 동기화 완료**(이번 세션 내). 신규 상주 스크립트: `fix_20260821_tier2_limit_lines.py`
  (임무2, --dry-run 지원) · `fix_20260821_kr0010_2025q1_vision.py`(임무3 부수). 진단 probe 다수는
  `scripts/_probes/`(`probe_20260821_leaf_residual4.py`·`probe_20260821_kr0004_*.py`·
  `probe_20260821_anchor_*.py`·`probe_20260821_tier2_*.py`·`probe_20260821_chubb_item35.py`·
  `render_kr0010_2025q1.py` 등), 전부 read-only 또는 자체 dry-run 지원.
- **owner/validation 판단 대기 (parser는 등재하지 않음)**: (a) 임무2 공식 비보편성(한화생명류)
  확인 후 RED 룰 배선 여부/조건분기. (b) KB손해 2025.1Q `EXEMPTION_VERIFIED_BY_IMAGE_ONLY`류
  등재 여부(판독은 끝났으나 게이트 문구 갱신은 validation/owner 소관).

---

**2026-08-21(8회차) — inbox `20260821T1830Z`(validation, iter-2) 드레인: R2_순자산합 동어반복
회사단위 원인규명, 데이터 수정 0건.**

- **과제**: 전 라운드(iter-1)가 image-only 24셀 제외 가설을 반증하고 "초과분이 회사단위로
  이봉분포"를 발견 — 상위권(KR0069 9/9·KR0008 12/13·KR0050 12/13 등)이 왜 100%대인지, 반대편
  KR0073(교보, 13칸 중 1칸만 resid=0)이 왜 그런지 원문 대조로 확정하라는 요청.
- **A절(상위 7사, KR0069·KR0008·KR0050·KR0094·KR1000·KR0099·KR0095) raw-sourced 확인**: 각
  2분기 이상 raw PDF/md_inbox 직접대조(총 14개 회사·분기 샘플) + 전수 census
  (`probe_item4_raw_vs_master.py`, 442버킷 중 441 same·9사 필터링시 diff=0). **핵심 물증**:
  다수 회사의 item4 라벨이 원문에 그냥 "Ⅰ.순자산" 이 아니라 **"Ⅰ.순자산(1+2+3+4+5+6[+7])"**
  로 인쇄돼 있다 — 발행사 스스로 이 셀을 성분의 합으로 정의·표기한다. 즉 총계와 성분합이
  대수적으로 종속이라 Irwin–Hall 독립반올림 귀무가 이 표본에 구조적으로 안 맞는다 — **파서
  버그가 아니라 표본(발행사 공시 관행) 특성.** 드물게 어긋나는 분기(±1)도 원문 자체에 이미
  있는 반올림差였고 master 는 그대로 정확히 담고 있었다(수정 대상 0).
- **B절(KR0073 교보·KR0097 하나) 별건 확인**: 두 회사도 raw==master 100%. 다만 원문 자체가
  대부분 분기에서 "총계≠성분합" 이고 격차가 **방향 고정**(교보 = 항상 +1~+2 / 하나 = 항상 −1).
  8번째 항목 누락 아님·표/컬럼 혼선 아님·단위 불일치 아님(3가지 다 원문으로 배제). **결정적
  증거**: 교보 2023.2Q(같은 페이지 해당분기 컬럼, resid=0) vs 2023.1Q(같은 페이지 직전분기
  컬럼, resid=−1) — 같은 라벨 "(1+2+3+4+5+6)" 이 컬럼(분기)에 따라 성립/불성립이 갈린다 →
  그 라벨은 교보 시스템의 실제 계산식이 아니라 정적 템플릿 문구이고, 총계 셀은 성분과
  **독립적으로** (더 정밀한 내부 수치를 총계만 별도 반올림해서) 채워진다는 뜻. 둘 다 발행사가
  실제 공시한 값이라 `[[feedback-issuer-inconsistent-keep-as-disclosed]]` 관례대로 손 안 댐.
- **수정 내역**: 없음. `kics_disclosure.json` 무변경(git diff 0) — 확인한 23개 샘플 + 전수
  census 442버킷 전부 master==raw. 신규 파일은 읽기전용 probe 2종
  (`scripts/_probes/probe_r2_item4_source_dump.py`·`probe_r2_company_detail.py`)뿐.
- **게이트**: `validate_kics_disclosure.py` exit=0 불변(rule 8_life 1건만 documented exception).
  R2 동어반복 documented exception 박제값과 Δ+0.00/Δ-0.00 정확히 일치(적용전 excess 1.25 z5.4,
  적용후 excess 1.43 z6.4) — 데이터를 안 건드렸으니 표류 없음, 예상대로. `pytest
  tests/test_identity_tautology.py tests/test_kics_rules_golden.py` 11 passed, golden 재생성
  불요. `insurequant_master_tables.xlsx` 무변경.
- **validation/owner 에게 권고(내 권한 밖, 결정 안 함)**: 기존 documented exception 의 "해제조건:
  R2 되맞춤 원인 규명" 은 이번 조사로 원인이 규명됐지만, R1(item3)처럼 고치면 수렴하는 종류가
  아니라 "발행사마다 총계 셀 산출 파이프라인이 다르다"는 **구조적·영구적** 표본 특성이라
  미래 분기가 쌓여도 초과분이 사라지지 않을 가능성이 높다. 등재 문구를 "원인 규명 중"→"원인
  확정(구조적)"로 바꿀지는 validation/owner 판단. `_TAUT_EXEMPT`/threshold 는 지시대로 불변.
- inbox: `20260821T1830Z` → `## iter-2 답변 (parser-kics)` 절 추가, status 는 validation/
  orchestrator 가 정리(내가 안 건드림).

---

**2026-08-21(7회차) — inbox `20260821T1720Z`(orchestrator) 드레인: 흥국생명(KR0071) 2024.4Q
`POST_TRANSITION_PARENT_MISSING` 4건(item15/16/22/23후) 종결.**

- **근본원인**: raw(`data/disclosure/FY2024_Q4/raw/KR0071_흥국생명보험.pdf`, md5 `25ee539046c51cf5`,
  538p)가 downloader→orchestrator 순으로 "DART 사업보고서(오문서)"로 3연속 오판정됐다 — 근거는
  fitz `"경과조치"` 전페이지 0회. 실제로는 **p1-112가 전부 스캔 이미지**(K-ICS 본문)이고 텍스트가
  잡히는 p113-450은 재무제표·감사보고서라 그 키워드가 원래 없다. 페이지당 533자(text-layer 존재)인데도
  본문이 이미지인 사례라 "텍스트레이어 有=키워드로 판정 가능"이 깨진다. 같은 함정을 흥국화재(KR0005)에서
  이미 겪고 240dpi 렌더링으로 풀었던 교훈이 이 회사엔 적용 안 됐던 것 — 세 명이 순서대로 반복.
- **해결**: `get_pixmap(dpi=260)`으로 p44/47/49/50/51 직접 렌더링·육안판독(fitz 텍스트 0자 재확인).
  이 회사는 TIR(신규보험위험=장수·사업비·해지·대재해, p50)·TER(주식위험, p51) 둘 다 신청한
  다중경과조치사라 결합값이 필요했다 — 기존 검증된 알고리즘(`scripts/rebuild_combined_transition_after.py`,
  leaf는 "누가 줄였는지"로 합치고 부모는 R4/R7/MARKET_M 재계산, 기준금액은 헤드라인(p44: 16,987억)에
  앵커, 법인세는 잔차, `AFFILIATE={"KR0071":"KR0005"}`로 item23=관계회사 흥국화재 item14 환산치)를
  import로 재사용하고, 이 스크립트의 `main()`이 놓치던 타겟(값_적용후가 "틀림"이 아니라 "아예 없음")만
  새로 짠 상주 스크립트 `scripts/fix_20260821_kr0071_2024q4_post_combine.py`로 채웠다. `scan_occurrences()`
  (fitz 텍스트 스캔)는 스캔본이라 0건 반환 확인 후, p50/p51에서 직접 읽은 값을 `occ` 딕셔너리에 수기
  입력 — 그 뒤 R4/R7/MARKET_M 재계산·단조성·affiliate 비율(13분기 중앙값 0.40061 vs 이 분기 0.40062,
  diff 0.00001)·법인세잔차 검증은 전부 기존 코드 로직 그대로 통과. 교차검증으로 item14/17/19/27/28/
  36-40후를 독립 재계산했더니 기존 저장값과 전부 정확히 일치 확인(그래서 그 항목들은 안 씀, 4셀만 UPSERT).
  identity 검산: item15후(14747.27)−item22후(3360.12)+item23후(5599.84)=16987.00=item14후(diff 0).
- **`_POST_PARENT_NOT_DISCLOSED` 등재 해제**: validation이 같은 날 이미 해제해 둔 상태였음(2026-08-21,
  "image-only PDF" 사유가 거짓으로 확인) — 이번 라운드는 그 자리를 실값으로 채운 것.
- **게이트**: `validate_data_contract.py` RED **12 → 8**(흥국생명 4건 전부 소멸, 잔존 8건은
  신한라이프/교보생명 `KICS_36_irr`+`TRANSITION_AFTER_IRR_MISMATCH` — owner 결정 대기, 이 라운드 밖).
  `validate_kics_disclosure.py` RED=6 불변(다른 룰셋, 무관). golden 배터리 123 passed, drift 0.
  `sh .githooks/pre-push` 4분2초 — `RED=8 · inbox 위반=0 · offline tests=pass → BLOCKED`
  (잔존 8건이 스코프 밖이라 여전히 BLOCKED, 이 티켓 인수조건은 달성).
- **부수 발견(안 건드림)**: KR0005(흥국화재) 2024.4Q item23 값_적용후=null(다른 전 분기는 0으로 미러) —
  RED는 아님(review 등급), spawn_task로 후속 플래그만 남김.
- inbox: `20260821T1720Z` → answered(원문 캡처 답변 첨부). `python scripts/check_inbox_hygiene.py` 위반 0.

---

**2026-08-21(6회차) — inbox `20260821T1600Z`(orchestrator)·`20260821T1620Z`(validation) 드레인:
`INTERNAL_MODEL_36IRR_EXEMPT` 반증(owner 승인분 5건 전건 해제, `20260614T0930Z` 등재 사유가 raw
대조로 거짓 확인)으로 드러난 RED 처리.**

- **A. 36_irr 5건**(교보생명 2025.2Q · 신한라이프 2024.2Q/2024.4Q/2025.2Q/2025.4Q) — items 41-46(금리위험
  순자산가치 6-시나리오)을 raw에서 "당기" 컬럼으로 직접 로드(30셀 신규, `scripts/fix_20260821_
  36irr_and_hana_post.py`). 컬럼오독 함정 실측: 오케스트레이터 원 티켓의 교보 수치(456,919)는 실제로
  전기(비교)열이었음(정정, p21 당기=459,988이 맞음) — 세션 자체는 라벨을 직접 대조해 이 함정을
  피했다. **여전히 GREEN 아님**: 게이트 36_irr derive식(sqrt(max(상승,하락)²+max(평탄,경사)²)+평균회귀)
  으로 재현하면 공시 금리위험액과 5.25~25.62% 벗어남(`run_validation()` 직접 호출로 확인, 값 안
  맞춤). 유력 가설(KR0094 raw p144 주2: 2024년부터 표 모수가 "금리노출 자산부채 한정"으로 변경)은
  미확정 — owner 결정 대기(새 면제 또는 허용오차 조정), **새 면제 등록 안 함**. 완전성 확보 부수효과로
  `TRANSITION_AFTER_IRR_MISMATCH` 4건(신한24.2Q 제외, display-scope)도 동일 근본원인으로 새로 노출(회귀
  아님 — 이전엔 41-46후 결측이라 미판정/SKIP이었을 뿐 통과였던 적 없음).
- **B. 하나생명(KR0097) 2024.4Q item16/17후 — 종결.** raw p281 `[지급여력기준금액]` 표(천원, 적용전/후
  두 컬럼 명문)로 item16후 신설(1613.67) + item17후 정정(1757.32→2001.90, 기존값은 phase-in 10% 역산
  파생값으로 추정). 검산 2001.90+0+2003.45+1548.78+364.85−1613.67=4305.31=item15후 정확히 닫힘.
  `POST_TRANSITION_PARENT_MISSING`(하나생명분) RED 종결.
- **C. 흥국화재(KR0005) 2024.4Q — 종결(코디네이터 중간 재수집 지시).** 세션 도중 downloader가 올바른
  정기경영공시(96p, **데이터 표 전부 래스터 이미지** — fitz "경과조치" 0회는 정상, 원 wrong-document는
  `data/_archive/20260821T044328Z/`로 격리)를 새로 받아옴. items 36-40후(개별 leaf)는 이미 정확했고,
  문제는 item19후(결합) — 저장값(3860.81)이 회사가 공시하는 4개 단일축 표 중 ③(주식위험 경과조치)
  자체의 서브토탈이었을 뿐, EQ+INT 두 축(`_TRANSITION_KIND`)을 동시에 반영한 결합값이 아니었다.
  게이트 R4/MARKET_M을 직접 import해 재계산(`scripts/fix_20260821_kr0005_2024q4_market_combined.py`):
  item19후 3860.81→2801.44(=게이트 자체가 이미 "계산"이라 표시하던 값과 정확히 일치) + 연쇄
  item15/16/22후 재계산. item14후(13978, 공시 총괄표 앵커)는 불변, item27=27894/13978×100=199.56%로
  공시와 정확히 재현. `TRANSITION_AFTER_MMULT_MISMATCH`(흥국화재분) RED 종결.
- **D. 흥국생명(KR0071) 2024.4Q — 손 안 댐.** downloader가 두 채널(생명보험협회·자사)로 재수집
  시도했으나 둘 다 기존 wrong document(DART 사업보고서)와 SHA256 동일 — issuer 자신이 잘못된 문서를
  공시채널에 올려놓은 상태. 면제 등록 안 함, 값 조작 안 함. 코디네이터가 owner 에스컬레이션 중.
- **게이트**: `validate_data_contract.py` RED 10(세션 시작, display-scope) → 13(A~B 반영,
  TRANSITION_AFTER_IRR_MISMATCH 신규 노출 포함) → **12(최종, C 반영)** — 8건(36_irr류, owner 결정
  대기) + 4건(흥국생명, downloader 대기) = parser 권한 밖. `validate_kics_disclosure.py` Status
  RED=6(불변, 기존 documented). `pytest`(4개 골든+deploy_assets) 13 passed, `--update` 불요(이번
  변경이 그 골든들의 스냅샷 범위 밖). `sh .githooks/pre-push < /dev/null` exit=2(BLOCKED, RED=12,
  inbox 위반 0, offline tests 131 passed) — 예상된 결과, 남은 12건 전부 parser 밖 결정 대기.
- **TODO.md**: `INTERNAL_MODEL_36IRR_EXEMPT` 항목 갱신(허위 사유 제거 + raw 재검증 근거 + 잔존 잔차 +
  owner 결정 필요사항), cross-stage 요약줄에 2026-08-21 갱신 추가.
- **후속(parser 밖)**: 흥국생명 raw 정상화는 owner/issuer 소관. 36_irr 8건 스코프 가설(금리노출
  자산부채 한정)은 owner 재조사 필요 시 KR0094 전체 분기 census로 검증 가능(미착수).

---

**2026-08-21(5회차) — inbox `20260821T1505Z`(오케스트레이터, item4 되맞춤+census 2건) 드레인 +
중간에 코디네이터 긴급정정(KR0097 2024.2Q item41-46후 조작 컬럼) 처리. item4·item3 두 스크립트의
동어반복(reconcile) 버그 근본수정 + 129셀 원문복원, 카카오페이 census 2셀(65행) 로드,
KR0087 시장하위 후미러 4셀. 게이트 `validate_kics_disclosure.py` MISSING_CELLS 2→0(원 티켓 인수조건
달성) — 단 그 사이 validation이 새 메타룰 `IDENTITY_TAUTOLOGY`를 배선해 넣어 exit는 여전히 2, 원인은
전부 이 티켓 밖(아래 참조). row_count 18987→19052(+65, 전부 INSERT).**

- **① item4(Ⅰ 순자산) 되맞춤 버그 — 최우선 항목, 완료.** `fill_period_to_disclosure.py::_reconcile_
  item4_from_components`(잔차≤10이면 자식합으로 교체)와 `recalc_kics_derived.py`(상대오차>5%면 교체)
  둘 다 제거 — item4는 이제 추출값만, 절대 재계산 안 함. **부수 발견**: `recalc_kics_derived.py`
  L188-210이 item3(보완자본)도 **허용오차 없이 무조건** `item1-item2`로 덮어쓰고 있었다(R1 적용전
  축이 잔차 97.7% 정확0이던 원인) — 같이 제거(존재하는 값은 이제 절대 안 건드림, 결측일 때만 역산
  생성은 유지).
  - **복원(자식합 역산 아님, md_inbox 원문 재추출)**: item4 435건 비교 → 122건 불일치(전부
    "master==Σ자식≠raw" 지문) → 121건 복원(diff 대부분 ±1, 억원 반올림 정상 신호). **KR0003
    2023.4Q 1건은 보류**(raw p41 총계행 자체가 자기모순 — 같은 행 성분합 24,808 vs 인쇄된 총계
    2,481, 인접분기·item1과도 10배 이탈 — 필러 오타로 판단, 현재값 유지, 등재는 안 함). 라운드2에서
    미변환 6분기 docling 재실행(KR0051×4·KR0071·KR0074·KR0080, `run_harness --stage parse`) +
    수기 3건(KR0032×2·KR0049, md_inbox 직접 대조) 추가 복원. 그 과정에서 **KR0080 2023.2Q
    item7/9/11**(이익잉여금·기타포괄손익·조정준비금)도 같이 깨져 있던 것 발견·raw로 동시정정(같은
    표 같은 컬럼). item3 쪽도 80건 복원 중 **KR0004 2024.2Q 1건**을 되짚어 정정(내 첫 복원값 3085가
    부정확한 표에서 왔다 — 백만원 단위 정밀표(48,998/308,195)가 더 정확, 3081.95로 재정정. 이 표는
    **이미 있던 값_적용후(3081.95)의 출처**이기도 해서 전/후 정합이 됨).
  - **손 안 댐(정책)**: KR0010·KR0079·KR0080(2024.4Q~)·KR0071(2024.4Q) 24셀 — `IMAGE_OCR_COMPANIES`/
    GOLD-SCAN 코호트, 텍스트레이어 실질 부재 확인(fitz `total_chars` 실측), 즉흥 OCR 금지 정책 준수.
  - **잔차 분포 before/after**: 적용전 452/486(93.0%)→327/488(67.0%), 적용후 212/230(92.2%)→
    172/232(74.1%). 귀무기대(반올림 Irwin-Hall) ~54%대에 근접, 남은 초과분은 위 24셀(스캔본, resid=0
    로 고정) 때문으로 추정.
- **② KR0087 2023.2Q item36-39후 — 완료.** raw p11 신청현황표(TAC/TIR/TER/TIRR 전부 X)·p12-13
  서술("지급여력비율 경과조치 미적용으로 경과조치 전·후 금액 및 비율이 동일")·공통TFI표(지급여력
  기준금액 전후 동일) 3중 확인 후 item36-39후=item36-39전 미러 4셀. item19(부모)는 이미 미러
  상태였음(추측 아니라 확인 후 채움).
- **③ 카카오페이손해(KR1098) 2024.2Q/2024.3Q — 완료(census 2셀→행 65개).** raw 존재 확인
  (`data/disclosure/FY2024_Q{2,3}/raw/`) → **파싱갭**(다운로더 발주 안 함). 두 PDF 모두 텍스트레이어
  실질 0(fitz: 622자/45p, 28자/19p) — 스캔본. `get_pixmap(dpi=100)` 렌더링+vision으로 Q3 PDF p11의
  3분기 비교표(24.3Q/24.2Q/24.1Q 동시 수록, 24.1Q 컬럼이 기존 마스터와 완전일치해 판독법 자체를
  교차검증) 판독 → items1-28 양분기 로드(27항목×2, 비적용사 확인되어 값_적용후=값 미러) + item36-40
  시장하위(p26-29, item36=derive식 검산 diff 0.24 exact) + item41-46 IRR(p26-27, item36 재도출과
  cross-check). 29-35는 item17=0(2Q)/2(3Q, 미미)이라 미적재.
- **코디네이터 긴급정정 (작업 도중 수신, 즉시 처리)**: KR0097 2024.2Q item41-46 값_적용후가 이전
  라운드에서 값과 동일하게 미러돼 있었는데, 이 항목군(3-1-0~3-1-5 금리위험 순자산가치)은 원문에
  경과조치 적용전/후 축 자체가 없다(충격전/충격후 축만 존재, p27 확인) — 조작된 컬럼. 6셀 값_적용후
  삭제(키 자체 제거, null 아님 — 이 파일의 "결측=키부재" 관례와 일치). 18사 적용사 전수 스윕으로
  KR0097만 유일한 오염 확인(다른 17사는 전부 정상 결측), KR0087 2023.2Q도 같이 확인했으나 이미
  정상(결측)이었음.
- **게이트 재검증**: `validate_kics_disclosure.py` — census(MISSING_CELLS) **2→0**(원 티켓 인수조건
  충족). regular rule 개별 findings 신규 RED **0건**(내가 만든 파생 불일치는 발견 즉시 같은 라운드에서
  정정 완료). 단 **exit는 여전히 2** — 이 티켓이 진행되는 동안 validation이 새 메타룰
  `IDENTITY_TAUTOLOGY`(오케스트레이터 별도 티켓 `20260821T1500Z`로 발주)를 게이트에 배선해 넣었다.
  R1(item3 관련)은 내 수정으로 자동 해소(97.7%→81.3%, 귀무 이내). **R2(item4)는 아직 RED**(67.9%/
  78.0%, 귀무 대비 여전히 높음) — 남은 초과분이 위 정책보호 24셀(KR0010/KR0079/KR0080/KR0071 스캔본)
  때문임을 확인했으나 그 이상은 손 안 댐(SKILL 정책). **rule 36_irr 5건**(KR0094 4분기+KR0073
  2025.2Q, item36 있는데 41-46 결측)도 exit=2에 기여하는데 — **내가 안 건드린 회사, 체크포인트
  비교로 확인**(item3 라운드 직후엔 없었다가 이후 라운드에 나타남 → 동시편집 세션 추정, 이 티켓
  스코프 아님). `pre-push` 훅(`validate_data_contract.py` 포함, ~6.5분)도 exit=2 — RED 10건 전부
  대조 결과 **미접촉 회사/이미 문서화된 과거 이슈**(흥국생명·흥국화재 2024.4Q raw 오염=2026-07-07
  경 downloader 기발주, 하나생명 2024.4Q=2026-07-15(3차) 보류 결정, 신한라이프/교보생명 36_irr=위
  R2와 동일건). 상세 근거는 inbox 답변 참조.
- **골든 재생성**: `test_kics_rules_golden.py`·`test_post_transition_golden.py` `--update`(의도된
  이동, 사유 위와 동일). `pytest tests/test_kics_rules_golden.py tests/test_post_transition_golden.py
  tests/test_master_tables_golden.py tests/test_deploy_assets.py tests/unit/` = **123 passed**.
- **xlsx 미동기화** — 이번 세션 변경분 `insurequant_master_tables.xlsx`에 반영 안 함(티켓이 명시적으로
  금지, "손대지 마라"). 다음 라운드에 `sync_master_xlsx_sheet.py`로 K-ICS공시 시트 cherry-pick 필요.
- **owner/validation 판단 대기**: (a) rule 36_irr KR0094/KR0073 원인 규명 — 내가 안 건드렸는데 언제
  나타났는지 불명, 다음 세션이 raw로 재확인 필요. (b) IDENTITY_TAUTOLOGY R2 잔존분(24셀)을 축
  정의에서 image-only 코호트로 제외할지는 validation 판단(내가 임의로 축 정의 못 바꿈). (c) KR0003
  2023.4Q item4 총계행 자기모순 — 필러 오류로 추정만, 확정 불가.
- 신규 상주 스크립트: `fix_20260821_item4_writepath_restore.py`·`fix_20260821_item3_writepath_
  restore.py`·`fix_20260821_item4_manual_stragglers.py`·`fix_20260821_kr0080_2023q2_children.py`·
  `fix_20260821_kr0004_item3_revert.py`·`fix_20260821_kr0087_2023q2_market_post_mirror.py`·
  `fix_20260821_kr1098_2024q2q3_load.py`·`fix_20260821_kr1098_2024q2_market_subs.py`·
  `fix_20260821_kr1098_2024q2_irr.py`·`fix_20260821_kr0097_2024q2_irr_post_denull.py`. 진단 probe
  다수는 `scripts/_probes/`(`probe_item4_raw_vs_master.py`·`probe_item3_raw_vs_master.py`·
  `probe_item4_residual.py`·`probe_item4_unmatched_residual.py` 등). 전부 cell-by-cell UPSERT/INSERT,
  실행마다 전/후 census 출력.

---

**2026-08-21(4회차) — 크래시 복구 세션: inbox 4건(F1/F2/F3 leaf잔차·KR0071 item24·KR0087 2023.2Q 26항목·
KR0097 2024.2Q 스캔본) 순차 처리. 게이트 RED 12→1(KR0087 7건·KR0097 4건 완전 해소, 잔여 1건은
KR0079 8_life — 오케스트레이터 소관, 안 건드림). row_count 18918→18987(+69, 전부 INSERT, DELETE 0).**

- **`20260821T1030Z`(F1/F2/F3 leaf 스케일 잔여) — 크래시 전 에이전트가 이미 완료.** 코드 확인 결과
  F2(문턱 0.005억 고정)·F3(연속페이지 포함+시장leaf 대시=전후동일)가 이미
  `scripts/rebuild_combined_transition_after.py`에 반영돼 있었고, `--leaves --dry-run`(전 APPLIERS
  스코프, `--only` 없이)이 **"갱신 0셀"**을 반환 — 111셀 전부 이미 정확. 감사기 재실행(F2/F3 반영된
  스캐너로) → 182건(오늘 아침 stale) → **7건**으로 급감, 그중 4건은 감사기 자체의 새 버그(동률 tie-break
  `max(set(cand), key=cand.count)`가 엉뚱한 값을 고름, 교보생명 item35전 3건+처브라이프 1건 — **값
  컬럼**이라 이 티켓 스코프 밖이기도 함), 3건(예별손해보험 KR0004 2023.4Q/2024.1Q/2024.2Q item36후
  =0 vs raw 652.39~716.06)은 `_leaves_mode`의 부모후 재현 가드가 정당하게 막은 **미해결 실사례**
  (item19 계열에 별도 오류가 있을 가능성, 추측 기입 안 함 — 다음 라운드 후보, 아래 잔여 항목 참조).
- **`20260821T1105Z`(KR0071 item24) — 1셀.** 원문 "-"(해당없음)이 8313(item23/26 복붙 오염)으로
  저장돼 있던 것을 0으로 정정(item25 처리와 일관). 전사 스윕(item23=24+25+26, tol 1.5억)으로 이 1건
  외 위반 없음 확인.
- **`20260821T1140Z`(KR0087 2023.2Q 메인표) — 29셀.** raw p11/p12 직접 재추출로 26항목(item10 제외,
  raw에 행 자체 없음 확인) INSERT + item2/3후 원문 TFI표에서 채움 + item15-26후는 item14후=item14전
  정밀일치를 근거로 기존 미러링 룰 적용 + item28후 산출. **부수: item19 적재가 19_market을 새
  RED로 노출**시켜 raw p20-22에서 item37-40(주식/부동산/외환/자산집중위험액) 4셀 추가 발견·적재,
  MARKET_M 검산(diff 0.07억) 후 반영. **KR0087 2023.2Q RED 7→0(19_market 포함).**
- **`20260821T1230Z`(KR0097 2024.2Q, 세션 중 신규 발주) — 40셀.** 순수 스캔본(fitz 0자) —
  `get_pixmap(dpi=300)`로 p15·p17·p18 직접 렌더링해 오케스트레이터 판독과 별개로 재판독, 100% 일치
  확인 후 34셀 INSERT(item4-13후는 원문 부재로 null 유지). **부수: item36 적재가 36_irr을 새 RED로
  노출**시켜 p27(당기 금리위험 IRR 시나리오표, 렌더링 재확인)에서 item41-46 6셀 추가 발견·적재,
  derive식 검산(diff 0.002) 후 반영, 41-46후는 TIRR 미신청 확인되어 전=후 미러. **KR0097 2024.2Q
  RED 4→0(36_irr 포함).**
- **게이트**: RED 12(세션 시작, baseline과 일치) → 5(티켓3 후) → 1(티켓4 후, 잔여=KR0079 2023.2Q
  8_life만, documented·오케스트레이터 소관). `pytest tests/test_kics_rules_golden.py
  tests/test_post_transition_golden.py tests/test_master_tables_golden.py tests/test_deploy_assets.py
  tests/unit/` = **123 passed**(`test_kics_rules_golden`만 `--update` 재생성 필요, 나머지는 무변경
  PASS). `validate_master_tables.py --no-build` 별도 확인(ifrs17 레인 마스터라 내 변경과 무관, 정상).
- **신규 상주 스크립트**: `fix_20260821_kr0071_item24_fabricated_dash.py` ·
  `fix_20260821_kr0087_2023q2_main_table.py` · `fix_20260821_kr0087_2023q2_market_leaves.py` ·
  `fix_20260821_kr0097_2024q2_vision_ocr.py` · `fix_20260821_kr0097_2024q2_irr.py`. 전부 cell-by-cell
  UPSERT(통짜 rewrite 아님), 실행마다 자체 전/후 census(row_count·combo delta) 출력.
- **xlsx 미동기화** — 이번 69셀(4개 티켓 합산)을 `insurequant_master_tables.xlsx`에 아직 반영 안 함
  (지시대로 이번 턴엔 손 안 댐). 다음 라운드에 `sync_master_xlsx_sheet.py`로 K-ICS공시 시트
  cherry-pick 필요.
- **다음 라운드 후보(미해결, 강제 기입 안 함)**: (a) 예별손해보험(KR0004) 2023.4Q·2024.1Q·2024.2Q
  item36(금리위험액)_적용후 — raw는 전후 동일(652.39/716.06/567.90)로 명확한데 `_leaves_mode`의
  부모(item19)후 재현 가드가 막는다(계산 1,446~1,601 vs 저장 1,106~1,341) → item19나 다른 leaf에
  별도 문제 있을 가능성, raw 재조사 필요. (b) 아이엠라이프(KR0076) 2023.1Q parent17 hold(diff 9.91) —
  미조사. (c) `leaf_scale_residue_audit.py`의 동률 tie-break 버그(`max(set(cand), key=cand.count)`가
  카운트 동률일 때 임의값 선택) — read-only 진단 스크립트라 게이트는 안 막지만 다음 감사 때 오탐
  유발. 재현: `scripts/_probes/leaf_scale_residue_audit.py` 실행 후 교보생명 2023.2Q/2024.2Q/2026.1Q
  item35 값(전) 3건 확인.

---

**2026-08-21(3회차) — inbox `20260821T0400Z` 드레인(validation 적대적 재검증, raw-only). ①REVERT+REDO 1건·②③④ raw 오류/결측 셀 로드·⑤ 36_irr 미러 확인. RED 12(회귀 0, 도중 15까지 갔다가 원인 규명 후 복귀).**

- **① 한화손해(KR0002) 2024.2Q — REVERT 확인.** 어젯밤 `item1후 53541→53537.72`는 틀렸다(validation
  지적대로). raw p14 "공통적용 경과조치"표(기본자본 2,638,159→2,872,265·보완자본 2,715,975→2,481,870,
  합 5,354,135=item1전 불변)를 직접 재확인 → `item1후=53541`(원복)·`item2후=28722.65`·
  `item3후=24818.7`. 2024.1Q/2024.3Q도 같은 관례(총괄표=item1후, 공통표=item2/3후) 확인.
  **부수: item28후가 옛 item2후에서 도출된 값(103.12)으로 정체돼 새 RED 유발 → item28후=112.28로
  캐스케이드 수정**(item2/14후 재계산, `fix_20260821_hanwha_kr0002_item28_cascade.py`).
- **② 롯데손해(KR0003) 2026.1Q item29~35후 7셀 — raw p24 직접 재확인 후 5셀 교체**(29·31·32·33·34,
  30·35는 이미 일치). ticket 인용과 완전 일치.
- **③ 면제 사유 오류 2건 — raw에 표가 있다.** `_AFTER_SUBRISK_NOT_DISCLOSED`의 `("KR0003","2026.1Q")`
  "②③표 부재" 및 `("KR0073","2026.1Q")` "섹션 자체 없음" 둘 다 **거짓**(docling MD 유실, raw PDF엔
  표가 있음) — 등재 해제는 validation/owner 소관이라 안 건드림. **KR0073 2026.1Q item29~35는 행
  자체가 없었다** → raw p15 ②표(전/후 둘 다)로 7행 신설, R7-sqrt로 item17전/후 둘 다 소수점 단위로
  재현(diff -0.09/-0.01) 확인 후 반영.
- **④ 미공시 3건 로드 + 스윕 중 신규 결함 2건 추가 발견.**
  - 신한이지(KR0051) 2024.4Q item30 신설(raw p33 "-"=0) + **item31~35가 이미 /100 스케일 오류로
    적재돼 있었음**(0.04 등, 있어야 할 값의 1/100) 발견 → ×100 정정(4/1/2/2/2). 전분기 census로
    2024.4Q만의 단발 오류 확인(다른 전 분기는 item17=sum(29-35) 비율 정상).
  - 신한이지 2023.1Q item29~35 신설 — get_text() 컬럼 순서가 뒤섞여 pdfplumber 단어좌표로 재구성,
    R7-sqrt로 item17=2.93 정확히 재현(diff 0.00).
  - AIA(KR0080) 2023.3Q item40 신설(0) + **item19가 오류(3643, 참값 3779)였고 이게 item14·15·16·
    20·22·27·28 전체 클러스터와 자기정합적으로 얽혀 있었음**(전부 서로 다른 잘못된 값끼리만
    맞아떨어짐) → raw p9(헤드라인)·p10(공통경과조치표)·p11(②표) 3중 인용 일치 확인 후 10개 항목
    (1·2·3·14·15·16·20·22·27·28) 전/후 동시 교체. R1/R5 정확히 닫히고 R4/R6 잔차 1~2(정상 반올림)로
    수렴.
  - **홀수분기 미러링 스윕(요청4) — B3b 5셀 개별 확인, 패치 불요 3건 + OCR 재분류 2군.** 롯데
    2023.1Q item19: raw p10 재확인 결과 item29~40 **이미 마스터가 raw와 정확히 일치**(해지·사업비·
    대재해만 진짜 "-"=0, 나머지 불변 — 이전 세션이 이미 정확히 반영). item36~40은 그 분기 raw
    자체에 시장위험 세부표가 없어(1개 결합표만 존재) 소스 결측, 패치 대상 아님. 현대해상(KR0009)
    2023.1Q: raw p8/p10에 **"경과조치 후: 해당사항 없음"이 명시 문구로 박혀있음** — 결측이 아니라
    구조적 정당(2023.1Q 최초분기라 선택경과조치 자체 미신청 추정), 새 면제 카테고리 후보로 보고만.
    AIA(KR0080) 2025.1Q·2025.3Q·2026.1Q: 페이지 텍스트가 "페이지 N/32" + 산발적 "0"뿐 →
    **스캔본(텍스트레이어 실질 부재)**, ticket의 B3a(OCR 큐) 버킷으로 재분류 요청(B3b 아님).
- **⑤ 36_irr(item41~46) 적용후 — ticket 결론 전수 확인, 미수정.** 코드로 618셀(103 (사,분기)×6항목)
  전수를 직접 스캔 → **618/618 전부 정확히 값_적용전과 동일**(오차 0). raw 2건(흥국화재 기존 인용+
  한화손해 KR0002 p32 신규 확인)에서 시나리오표 헤더가 `충격 전|충격 후(평균회귀·금리상승·…)`뿐이고
  경과조치 축 자체가 없음을 직접 확인 — "경과조치 적용후" 개념이 원천에 없다는 ticket 결론 재확인.
  **null 처리 + `POST_SCENARIO_NOT_IN_SOURCE` 면제 신설은 owner 결정 대기, 셀 미변경.**
- **재검증**: `validate_kics_disclosure.py` RED **12**(불변 — KR0087 7룰·KR0097 4룰·KR0079 8_life
  1건, 전부 기존 documented). 적용후 mmult 불일치 2→1(잔여 KR0079 2023.2Q, 기존 documented) ·
  적용후 항등식 위반 2→0 · 선택경과조치 적용후 AMT_MISMATCH 1→0. (수정 도중 RED가 일시 15까지
  올라갔다 — item19 교정이 KR0080의 자기정합적 오류 클러스터를 노출시켰기 때문. 원인 추적 후 클러스터
  전체 교정으로 12 복귀. 상세는 스크립트 주석·inbox 답변 참조.) `pytest tests/unit/` 110 +
  `test_deploy_assets` 10 + `test_kics_rules_golden`(`--update`, 6804 findings/486 buckets, RED 12
  불변) + `test_master_tables_golden`(`--no-build`) 1 + `test_post_transition_golden`(`--update`,
  6114 cells/428 company-quarters) = **123 passed**.
- **xlsx 미동기화** — `insurequant_master_tables.xlsx`에 이번 셀 반영 안 함(`sync_master_xlsx_sheet.py`
  로 K-ICS공시 시트 cherry-pick 필요, 다음 라운드로 이연).
- **owner 판단 대기 (parser는 등재하지 않음)**: (a) `_AFTER_SUBRISK_NOT_DISCLOSED`에서
  `("KR0003","2026.1Q")`·`("KR0073","2026.1Q")` 해제(사유가 raw와 불일치, 값은 이미 로드됨).
  (b) item41~46 적용후 103셀(618개 값_적용후 cell) null 처리 + `POST_SCENARIO_NOT_IN_SOURCE` 면제
  신설. (c) 현대해상류 "해당사항 없음" 명시-부재를 새 면제 카테고리로 등재할지. (d)
  `fix_20260716_nonapplier_requirement_mirror.py` L115 짝수분기 게이팅을 부모후결측 조합까지 포함해
  완화할지(코리안리·AIA·신한이지 3반례 확인됨, 다른 홀수분기는 이번 스윕에서 추가 반례 없음).
  (e) KB손해 5분기·미래에셋 6분기·동양 2026.1Q(+AIA 2025.1Q/2025.3Q/2026.1Q 신규)를 OCR 큐에 등록할지.
- 신규/변경 스크립트: `scripts/fix_20260821_adversarial_reverification.py`(①②③④ 핵심 36셀) ·
  `scripts/fix_20260821_hanwha_kr0002_item28_cascade.py`(① 캐스케이드 1셀) ·
  `scripts/fix_20260821_aia_kr0080_2023q3_headline.py`(④ 헤드라인 클러스터 20셀).

---

**2026-08-21(2회차) — inbox `20260821T0155Z` 드레인: validation이 게이트를 적용사 18사→전사 39사로
확대 배선한 뒤 새로 드러난 RED 3종(적용후 항등식·mmult·하위census) 중 2종 해소.**

- **한화손해보험(KR0002) 2024.2Q item1후**(53541→53537.72): 적용전 복사 버그, raw로 확정 수정.
  **전사 스윕**(item1후==item1전인데 item2후+item3후와 불일치)을 돌리니 486버킷 중 138개가 걸렸지만
  거의 전부 정수/소수 반올림 경계 노이즈였다 — `round()` 기준으로 좁히니 7건, 그중 raw 대조로
  **4건은 진짜 오탐**(케이디비생명 3분기·하나생명 1분기 — 전부 TAC 적용사라 item1이 `①자본감소분`
  표에서 item2/3와 별개로 산출됨, item1=item2+item3 가정 자체가 안 맞음), 2건은 반올림 경계일 뿐
  버그 아님(DB생명·하나손해), 1건은 검증불가(카카오페이, image-only PDF, RED 임계 밖이라 비차단).
  **진짜 버그는 최초 지적받은 한화 1건이 전부** — naive 규칙으로 138건을 일괄 처리했으면 정상인
  TAC 반영값을 깨뜨릴 뻔했다.
- **코리안리재보험(KR1000) 2023.3Q 세부위험 12셀**(item29-35·36-40 적용후 결측): ticket의 "백필
  경로 버그" 가설은 틀렸음을 raw로 확인 — 2023.3Q 자체 raw에 ②③표가 존재하고, 전 행이 "-"로
  채워진 채 "당사는 ~ 적용하지 않아 경과조치 전·후의 금액 및 비율이 동일함" 각주가 명시돼 있다
  (필러의 "전후 동일" 표기 관례이지 결측이 아님). `fix_20260716_nonapplier_requirement_mirror.py`
  L115가 세부위험 미러링을 짝수분기로만 게이팅해놨는데(대부분 회사는 홀수분기에 세부표 자체가
  없다는 전제가 맞지만) 코리안리는 예외 — 그 예외만 게이트를 피해갔다. 같은 신호(부모 전후 동일 +
  세부전 존재 + 세부후 결측, 홀수분기 전수)로 스윕해 **롯데손해보험(KR0003) 2026.1Q 시장위험
  5셀**도 동일 패턴으로 발견, raw(직전 짝수분기 2025.4Q의 확립된 미러 패턴)로 근거 확인 후 같이
  수정. 총 17셀, 전부 자기 값_적용전 그대로 미러링(값 자체는 raw에 이미 있던 것).
- **재검증**: 적용후 항등식 위반(RED) 1→**0**, 적용후 하위 census 결측(RED) 2→**0**, 적용후
  mmult 불일치(RED)는 KR0079(documented, owner 승인 대기) 1건 불변(지시대로 미터치). RED 전체
  12→**12**(회귀 0). `pytest` unit 110 + deploy_assets 10 + master_tables_golden(--no-build) 1 +
  post_transition_golden 1 = 122 passed. `test_kics_rules_golden`은 이번 셀들이 그 골든 스냅샷
  범위(8-rule 엔진, 확대 전 코어) 밖이라 재생성 불요, 그대로 통과.
- **게이트 코드(2Q/4Q 게이팅) 자체는 안 고침** — 이번엔 셀 데이터만 직접 수정(parser 스크립트
  코드 변경은 별도 판단 필요, 지금 스윕으로 이 2건 외 추가 후보 없음 확인됨).
- 상세 raw 인용·전수스윕 커맨드는 `inbox/parser/20260821T0155Z__validation__MULTI__after_column_widening_findings.md`
  (`status: answered`) 참조.

---

**2026-08-21 — inbox `20260821T0010Z` 드레인: 적용후 mmult 3축 감사(축C 기본요구자본 9~36건 미closure,
axis A 비적용사 3건, R1 1건) 전부 해소. RED 12(불변, 회귀 0).**

- **⚠️ 이 작업 도중 같은 브랜치·같은 파일(`kics_disclosure.json`)을 편집하는 다른 세션이 동시에
  돌고 있었다**(커밋 없이 워킹트리만 — `git show --stat`로 그 세션의 커밋 3개(`404581a`/`88f059c`/
  `f90d38c`)는 TODO/changelog/inbox/probe만 건드리고 데이터는 안 건드린 것 확인. 값이 세션 중간에
  두 번 다르게 읽혀서 발견). 그 세션의 축-C 수정 방법론(총괄표 헤드라인 우선+R4/MARKET_M 역도출)을
  내가 독립적으로 재도출한 것과 교차검증해 대부분 일치 확인 → 이미 고쳐진 셀(에이비엘 3분기·농협생명
  2분기·흥국생명 2분기·흥국화재 2023.2Q)은 안 건드리고, **그 세션이 아직 안 건드린 잔여만** 직접
  수정. 상세 방법론·재현 커맨드·셀별 raw 근거는 티켓 `## 답변` 섹션(2026-08-21T0230Z) 참조.
- **내가 직접 수정한 셀 (raw 근거 포함, 전부 티켓에 인용)**:
  - 흥국화재(KR0005) 2023.1Q item15/16/19/22/36후 — 이 회사만 유일하게 시장위험 경과조치가 ③(주식)
    ④(금리) **별도 표 2개**로 분리공시되는데 기존 item19후가 ③표만 반영하고 ④표(금리위험
    454,370→272,622백만)를 누락한 부분치였음 + item14후 자체가 이 회사 PDF의 비-브래킷 헤드라인
    레이아웃을 못 찾아 ②표(TIR 단독)의 자체 기준금액으로 오인돼 있었음(둘 다 raw fitz로 재확인).
  - 신한이지(KR0051) 2025.1Q item35후(43→2)·하나손해(KR0050) 2025.2Q item34후(44.43→381.53)·
    KB라이프(KR0099) 2024.2Q item33후(12364→10787.13) — 전부 **비적용사**(선택경과조치 미신청,
    `_TRANSITION_APPLIERS` 밖)인데 `_transition_mmult_after`가 적용사 18사만 순회해 게이트를 한번도
    안 거친 오염 셀. 전=후 미러가 정상인 회사라 전값으로 복원.
  - KB라이프(KR0099) 2026.1Q item3후(23071→22573) — 공통TFI표 보완자본 재분류(2,307,119→2,257,319
    백만) 반영 누락. item1=item2+item3 R1 항등식 복원.
- **재검증**: `validate_kics_disclosure.py` RED=12(전부 기존 documented: KR0087 동양생명 image-only·
  KR0097 하나생명·KR0079 미래에셋 8_life scan-only), 적용후 mmult 불일치=0, 적용후 항등식 위반=0.
  축C 기본요구자본 mmult 적용후 **480/480 PASS(FAIL 9→0)**. 축A/B 적용후 고유 FAIL 4/1→0(잔여 각 1건은
  기존 documented, 신규 아님). `pytest tests/unit/` 110 passed·`test_deploy_assets`·
  `test_master_tables_golden`(--no-build)·`test_post_transition_golden` 통과. `test_kics_rules_golden`
  은 의도된 데이터 이동이라 `--update` 재생성(6,804 findings/486 buckets, RED=12 불변, 룰엔진 코드는
  무변경).
- **owner 승인 대기 (self-close 안 함)**: item5-11(순자산 구성요소)·41-46(IRR 시나리오) 적용후 커버리지
  47%/21% — item5 계열은 raw 전수 확인 결과 **적용사 0%/비적용사 91%**로 극명히 갈려, "적용후 순자산
  구성요소"라는 공시 개념 자체가 없고 비적용사만 baseline 미러로 채워져 있음이 원인(파싱갭 아님).
  41-46은 미검증(시간배분상 5-11 우선). `MARKET_BREAKDOWN_EXEMPT`류 census 면제 등재 여부는 owner
  판단 필요 — 임의 등재 안 함.
- **게이트 배선(범위구멍 2개) 변경 없음**: `_transition_mmult_after`의 18사 스코프 제한·
  `_TRANS_PARENT_SUBS`의 item15 부재는 코드상 그대로. 데이터만 고쳤고 룰엔진(validation 소관)은
  손 안 댐. 데이터가 깨끗해졌으니 축C를 전사·item15 포함으로 확장 배선해도 즉시 RED는 안 뜬다(0/0).
- **xlsx 미동기화**: 위 셀 수정을 `insurequant_master_tables.xlsx`에 아직 반영 안 함 — 동시편집
  세션이 아직 활성이라(§ 위) 부분 동기화가 곧바로 stale해질 위험 판단, 다음 라운드(그 세션 마무리 후)
  로 이연. `sync_master_xlsx_sheet.py`로 K-ICS공시 시트 cherry-pick 필요.

**2026-08-21 (이어서, 병렬 세션) — 같은 티켓을 동시에 잡은 두 번째 세션의 기록.** 위 항목을 쓴
세션과 내가 같은 브랜치에서 `kics_disclosure.json`을 각자 통째로 read-modify-write 했다.

- **⚠️ lost update 실발생 1건**: KB라이프 2026.1Q `item3후`(공통TFI 보완자본 재분류 22,573.19)가
  내 전체쓰기에 덮여 사라져 있었다. R1 전수감사로 재적발 → raw p21 대조 후 복구
  (`scripts/fix_20260821_missing_life_subs.py`). **감사 스크립트가 유일한 안전망이었다** — 이 마스터를
  통째로 쓰는 스크립트는 동시 세션에서 조용히 서로를 지운다. 다음 라운드에 셀 단위 write 로 바꿀 것.
- **축 C 를 36건 전건으로 확대 종결** (`scripts/rebuild_combined_transition_after.py`, 신규·상주).
  결합 모델 = leaf 는 그 leaf 를 줄인 표에서, 부모는 R7/MARKET_M/R4 로 재계산, **기준금액후는 회사
  공시 헤드라인 비율에 앵커**하고 법인세조정액후는 잔차. 쓰기 전 가드 3개(적용전 재현 / 표 공시
  부모후 재현 / 단일표 대비 단조성) 통과분만 반영. 36/36 이 원문 헤드라인을 소수 둘째자리까지 재현.
  **흥국생명 11분기**의 기타요구자본(관계회사 환산치)은 **흥국화재 item14 로 환산**해 풀었다 —
  환산계수 0.40060±0.00003 (13분기 실측). `20260706T0502Z`에서 "추정 금지"로 비워 둔 셀이 근거를
  갖고 채워졌다.
- **비적용사 오염 전수 스윕 21셀 복원** (`scripts/fix_nonapplier_after_drift.py`, 상주). 게이트가
  `_TRANSITION_APPLIERS` 18사만 보느라 한 번도 안 거친 구간이다. + `item29(사망위험)=0`인데 원문엔
  값이 있는 케이스 전수 확인 → 1건(KB손해 2023.2Q 258,369백만) 반영.
- **0값 leaf 행 누락 41건 중 71셀 복원** (`scripts/fill_zero_subrisk_rows.py`, 상주). 판정은 추정이
  아니라 검산 — 결측 leaf 를 0 으로 놓았을 때 mmult 가 저장된 부모를 재현할 때만 쓴다. 계산불가
  A 141→131 · B 190→138. **이 항목이 아래 "남긴 잔여 1"의 해소분이다.** 보류 17건(0 으로 놓으면
  부모 재현 실패 = 진짜 결측)은 다음 라운드.
- **요청4 판정 — item41~46 적용후는 원천 부재**(census 면제 대상). 전수 결과 **전≠후 셀이 0건**이고,
  원문 금리위험 순자산가치 표는 경과조치 전/후 컬럼이 아예 없는 단일 표다(농협생명 FY2024_Q2
  p23·p24 등 확인). 경과조치는 산출된 금리위험액에 적용될 뿐 순자산가치를 바꾸지 않는다.
  item5~11 도 동일(①②③④ 어느 표에도 순자산 구성요소 행이 없음).
- **xlsx 동기화 완료** — `sync_master_xlsx_sheet.py`로 `K-ICS공시` 시트 cherry-pick(변경 셀 455 ·
  신설 행 21), 나머지 7개 시트 값 동일 검증. 위 항목의 "다음 라운드로 이연"을 이 세션에서 처리.
  (도구 버그도 하나 잡음: 다중 삽입 시 인덱스 보정 누락 — 검증 가드가 저장 전에 막았다.)
- **재검증**: `validate_kics_disclosure.py` RED=12(회귀 0) · 적용후 mmult 0 · 적용후 항등식 0 ·
  적용후 하위 census 0 · continuity break 0 · 조정항목 review 5→3. R1 적용후 FAIL 1→0.
  `pytest` 122 passed. `test_kics_rules_golden` 은 의도된 이동(rule 8_life SKIP 136→128 ·
  GREEN 337→344, RED 불변)이라 `--update` 재생성.

---

**2026-08-20 — inbox 드레인 2건 종결(`20260706T0502Z` iter-2 · `20260803T0520Z` UH-8).
경과조치 적용후 continuity break 34셀/5쌍 → 0, 적용후 하위 census 결측 4 → 0.**

- **다섯 (회사,분기)의 원인이 전부 달랐다.** 전부 raw PDF를 fitz로 직접 읽어 처리(Docling MD는
  다섯 중 넷에서 경과조치 섹션을 통째로 흘렸거나 열을 밀어 넣었다).
  - **KR0050 하나손해 2023.2Q = 결측이 아니라 오염.** 저장된 값_적용후가 [경과조치 적용 전 …세부]
    3분기 비교표의 **전분기(2023.1Q) 컬럼**이었다(컬럼 한 칸 밀림). raw는 "경과조치를 적용하고 있는
    사항이 없습니다" + 네 표 전부 "전·후 동일" 주석 → 전값 미러로 교체. 같은 시그니처
    (후(q)==전(q−1)≠전(q))로 전 그리드 스윕 → **이 한 건이 유일**.
  - **KR0097 하나생명 2023.2Q · KR1011 IBK연금 2023.2Q · KR0004 예별손해 2023.1~3Q = ②+③ 비중첩
    결합.** 결합 벡터 R4 재계산이 공시 헤드라인 지급여력기준금액후를 백만원 단위로 재현
    (360,712.71/3,607억 · 517,910.57/5,179억 · 820,515.73/820,516 · 785,931.40/785,937 ·
    767,461.88/767,462). ② 단독·③ 단독도 각각 재현되므로 우연이 아니다. **IBK 2023.2Q에 대한
    2026-07-12(5차) "다중경과조치 결합공식 불명" 판정은 오판으로 정정.**
  - **KR0100 처브라이프 2024.3Q** — "②표 값이 행별로 다른 컬럼 착지"는 Docling 아티팩트였고 raw는
    fitz로 깨끗하다. `_AFTER_SUBRISK_NOT_DISCLOSED`에서 **해제**(면제로 두면 새로 채운 값이 mmult
    검사에서 영구 skip).
  - **KR0049 악사손해 2024.3Q = 유일한 진짜 미공시.** 그 분기 공시서에 지급여력비율 섹션이 통째로
    없고(부칙 제3조 유예), 값의 출처인 FY2024_Q4 공시서는 과거분기 경과조치후를 [지급여력비율 총괄]
    3줄로만 싣는다 → 15-23후 원천 부재. `TODO.md` documented exception + `_POST_PARENT_NOT_DISCLOSED`
    등재. 가용자본측 item3후만 TIR 단독 적용 근거로 확정해 채움(2,326).
  - **KR0071 흥국생명 2023.1Q** — 공통TFI 재분류(신종자본증권 50,000백만 보완→기본)로 item1후
    26,499 · item3후 17,737.26 확정. R1 닫힘.
- **부수 적발 — ③표 미반영 실데이터 오류 2분기.** 예별손해 2023.1Q·2023.3Q의 item36(금리)·
  item37(주식) **적용후가 ②표(시장 불변) 값**이었다(③표 주식·금리 경과조치 미반영). **item19후가
  결측이라 mmult가 영구 skip 되면서 숨어 있던 값**이다. 정정 후 MARKET_M 정확히 닫힘. 같은 조합
  ("부모후 결측 + 세부후 present")을 전 그리드 스윕 → 이 3분기가 전부, 지금은 0.
- **조정항목(22 법인세·23 기타요구자본) 적용후 전수 종결.** 적용사 121(회사,분기)이 비어 있었고
  게이트 review는 그중 17만 보여 주고 있었다(직전 분기에 후가 있을 때만 발화 → 채울 때마다 앞
  분기가 새로 드러나는 구조). 3중 가드(행 라벨 정확일치+②/③ 페이지 / raw 적용전이 저장값과 단위까지
  일치 / R5 적용후 항등식 성립)로 **148셀 채움, 7건 보류** → review 17 → **5**.
- **재검증**: 핵심룰 RED=12(전부 기존 documented 이미지·스캔 3건, 회귀 0) · 적용후 mmult 0 ·
  적용후 항등식 0 · `pytest tests/unit/` 110 passed · `test_deploy_assets`·`test_post_transition_golden`·
  `test_master_tables_golden` 통과. `test_kics_rules_golden`은 **의도된 이동** 3건(rule10 KR0050
  GREEN→SKIP·rule8_life KR0097 SKIP→GREEN·rule8_post SKIP→GREEN)이라 `--update` 재생성.
- **UH-8(금리민감도 provenance) 종결**: `kics_rate_sensitivity_provenance.json` 87셀 발행 +
  발행기 `scripts/emit_rate_sensitivity_provenance.py` 상주. `validate_data_contract.py` RED=0 유지,
  validation이 CHECK 2 2a(iv) 배선하면 됨.
- **신규 상주 스크립트**: `scripts/fix_20260820_post_transition_sandwiched.py`(티켓 6쌍+예별 3분기,
  값별 raw 인용은 docstring) · `scripts/fill_post_transition_adjust_items.py`(22/23후 전수, 매 분기
  재실행 안전) · `scripts/emit_rate_sensitivity_provenance.py`. 진단 probe 6종은 `scripts/_probes/`.

**남긴 잔여 (다음 라운드 인계):**
1. **0값 세부위험 행이 통째로 빠지는 별건 — 31(회사,분기).** 29-35 중 일부 행 결측 17건 · 36-40 중
   일부 결측 14건, 거의 전부 **원천 값이 0인 행**(item32·item40이 압도적). 행이 없으면 mmult·census가
   그 부모를 통째로 건너뛴다(= 이번 KR0097 2023.2Q가 딱 그 케이스라 raw 근거로 행 신설했다).
   재현: `scripts/_probes/probe_subrisk_rowcensus.py`.
2. **조정항목 보류 7건** — KR0071 2023.1Q·2024.3Q·2025.3Q(기타요구자본=관계회사 환산치가 ②표/③표로
   갈려 결합 불명, 추정 금지) · KR0071 2024.4Q + KR0005 2024.4Q(image-only, 기존 documented) ·
   KR0002 2024.3Q·KR0082 2023.3Q(raw 행에 값 칸 자체가 빔) · KR0032 2023.1Q(item15후 결측).
**✅ `insurequant_master_tables.xlsx` 동기화 완료 (cherry-pick).** owner 상시 지시(`inbox/_resolved/
20260819T0500Z` L119: *"전체 재생성 금지 — 해당 시트만 cherry-pick 동기화할 것"*)에 따라
`build_master_xlsx.py`는 **쓰지 않았다.** 신규 상주 도구 `scripts/sync_master_xlsx_sheet.py`로
`K-ICS공시` 시트만 셀 단위 반영 — **변경 셀 260 · 추가 행 1 · 삭제 0**(전부 `값_적용후` 컬럼,
`값` 컬럼은 한 칸도 안 건드림). 사후 독립검증: K-ICS공시 18,879행 × 9열이 마스터와 **셀 불일치 0**,
나머지 7개 데이터 시트 **값 기준 완전 동일**, 수식 0개·파트 17개 유지(피벗/차트 유실 없음).
덤으로 `요약` 시트 행수가 실측과 어긋나 있던 것 보정(17BS 6,953→6,855 · 배당 1,924→2,043 —
다른 레인이 시트를 cherry-pick 한 뒤 `요약`을 안 고쳐서 생긴 stale, 설명 칸은 손대지 않음).

---

**2026-07-16 — owner 지시("경과조치 미적용 확실 + 비율 동일하면 하위항목 미러링") 대응, 전사 스윕
241셀 + 기존 스크립트의 데이터오염 버그 발견·정정.**
- **비적용사 정의**: `validate_kics_disclosure.py`의 `_TRANSITION_APPLIERS`(owner FSS 정본 18사) 밖
  전 회사. **미러링 안전기준을 owner 제안(item27·28 둘 다 동일)에서 item14(지급여력기준금액) 단독
  동일로 정교화** — item27/28 둘 다 확인하면 실제로는 놓치는 셀이 많았음: TFI(공통조치, 비적용사도
  다 적용)가 자본 티어(기본자본↔보완자본)만 재배분해도 item28(기본자본비율)이 5~15%p씩 움직이는
  사례가 수두룩(item27은 그대로인데) — 이건 요구자본(15-46) 안전성과 무관한 자본측 재분류일 뿐이라
  item14만 보는 게 더 정확(raw로 다수 확인된 K-ICS 구조: TFI는 요구자본측을 아예 안 건드림).
  `scripts/_probes/survey_item14_gap.py`로 tolerance 보정(247/252 exact-0, 노이즈 상한 0.45, 진짜
  이상치 1건(하나손해 2023.2Q, diff=45)만 정확히 걸러짐 확인).
- **⚠️ 부수 발견 — 기존 스크립트 데이터오염 버그**: 1차 라운드 초반 실행했던
  `backfill_post_transition_when_not_applied.py`(item1/14/27만 보고 판정)가 KB라이프생명 2024.2Q·
  동양생명 2024.1Q에서 item12/13(불인정항목/보완자본재분류)을 잘못 미러링했던 것 발견 — 이미 정확히
  채워져 있던 item2(기본자본)값과 항등식(item2=item4-item12-item13)이 안 맞음. 되돌림
  (`fix_20260716_revert_wrong_item1213_mirror.py`). 해당 스크립트에 경고 docstring 추가, items 1-13은
  더 이상 이 방식으로 안 건드림.
- **신규 영구 스크립트** `fix_20260716_nonapplier_requirement_mirror.py`(idempotent, 매 분기 재실행
  안전) — items 15-26(item14 게이트)·29-35(item17 게이트, 2Q/4Q만)·36-40(item19 게이트, 2Q/4Q만)
  3단 게이팅, items 1-13은 아예 스코프 밖(위 버그 재발 방지).

**결과**: 241셀/20(회사,분기) 신규 채움 — 코리안리(6분기, 3차에서 미룬 "non-display" 건도 이걸로
해소)·동양생명(7분기, 3차 잔여분 포함)·DB손해보험(2분기, 신규)·한화생명/삼성생명(item24-26, 15-23은
1-2차에서 이미 완료였는데 24-26은 놓쳤던 잔여). continuity break 62→**34셀/10→5쌍**(잔여 5쌍은 전부
18사 적용사 관련 raw확인필요·documented exception, 이 스윕 스코프 밖). core RED 12(무관 기존건, 회귀
0). `pytest` 110 passed. xlsx 재생성 완료.

---

**2026-07-15(3차) — validation이 신설 게이트(`_post_transition_parent_census`, inbox `20260715T0835Z`)로
적발한 continuity-break(적용후 공시하다 특정 분기만 결측) 14쌍/96셀 처리, 62셀/10쌍 잔존.**
- **완전 해소(raw 재대조, 전부 선택경과조치 완전 미적용)**: 삼성생명(KR0069) 2025.1Q, 동양생명(KR0087)
  2024.2Q·2024.4Q·2025.1Q·2025.2Q(연쇄 노출분 포함) — 16-23후=전 미러링.
- **부분 해소**: 하나생명(KR0097) 2024.4Q — raw가 표준양식 아닌 "지급여력 및 건전성감독기준
  재무상태표"(감사보고서 첨부, 단위 천원) 스타일임을 확인, 18-23 채움. **item17후=1757.32(기존값)가
  이 페이지 값(2001.90)과 불일치·출처 불명** — item16과 함께 보류(validation에 원 출처 문의).
  흥국생명(KR0071) 2024.4Q — **image-only PDF, 비전으로 스캔페이지 직접 판독**(8차 changelog 선례
  재현). item17/18/19/20/21 disjoint-derive로 채움, **item22/23가 두 경과조치 표에서 서로 달라
  R4 역산도 헤드라인과 ~2,240 차이로 재현 안 됨** — 진짜 다중결합 불명, item15/16/22/23 보류.
- **손 안 댐**: ticket이 명시한 "non-display/비차단"(코리안리 3분기·처브 2024.3Q) + 기존
  documented exception(IBK연금 2023.2Q, 5차 라운드 `_AFTER_SUBRISK_NOT_DISCLOSED`).
- **미확인 잔여**: 하나손해 2023.2Q·하나생명 2023.2Q(별개 분기)·악사손해 2024.3Q — 다음 라운드.

재검증: RED 12(무관 기존건, 회귀 0), `pytest` 110 passed. inbox `20260715T0835Z`에 상세 회신
(`status: answered`). 스크립트: `scripts/fix_20260715_round3_continuity_gaps.py` +
`fix_20260715_round3b_dongyang_2025q2.py`.

---

**2026-07-15(2차) — owner 지시로 "2차(과거분기 유사갭)" 이어서 처리, 완료 + 2026-07-12(2차) 오판정
정정.** 한화생명(KR0068) 2024.3Q·2025.2Q·2025.3Q, 농협생명(KR0104) 2023.1Q·2023.2Q raw 재대조:
- 한화생명 3개 분기: 전부 선택경과조치 완전 미적용(raw 명시, 1차와 동일 패턴) → 15-23후=전 미러링.
- 농협생명 2개 분기: ②+③ 동시적용, 1차와 동일 비중첩 구조로 item17/19 개별신뢰 + R4 역산 검증. 부수로
  농협 2023.2Q 시장하위(36-40후)도 해소(1차 패턴과 동일).
- **⚠️ 오판정 정정**: 농협생명 2023.1Q item17후가 `10,899.56`("다중 경과조치 결합공식 불명", 2026-07-12
  2차)으로 저장돼 있었는데, raw `[지급여력비율총괄]`(지급여력기준금액후=22,802 직접공시) 앵커 + R4
  역산이 `8,979.7`로 수렴(원 ②표 값과 일치) — 10,899.56은 어떤 raw 표·항등식도 만족 못 함을 확인,
  **오류로 정정**. 함께 None 처리됐던 33/34/35(해지·사업비·대재해)도 raw dash(=0)로 복원.
  (`scripts/_probes/verify_r4_kr0104_2023q1.py`)

50셀 추가+정정. 재검증 RED 12(무관 기존건, 회귀 0), census 결측 4(회귀 0, 신규노출분도 해소).
`pytest` 110 passed. inbox `20260715T0801Z`에 2차 회신 추가. **owner가 언급한 과거분기 갭은 이 5건이
전부, 2차도 종결.**

---

**2026-07-15 — owner ticket `20260715T0801Z`: 2026.1Q 요구자본(15-23) 적용후 5개사 결측 → raw 재대조로
46셀 채움, 하나생명 기존 오류 4셀 정정.** 신규 로드된 FY2026_Q1에 대해 `fill_post_transition_to_
disclosure.py`/`backfill_post_transition_when_not_applied.py`가 아직 재실행 안 된 것이 근본원인
(과거 분기는 이미 처리됨, 2026.1Q는 처음). 5개사(한화생명·교보생명·하나생명·롯데손해·농협생명)
raw PDF 직접 재대조:
- 한화생명: 선택경과조치 완전 미적용(raw 명시 확인) → 15-23후=전 미러링.
- 교보·농협: ②(장수)+③(주식/금리) 동시적용이지만 두 표가 서로 다른 항목만 건드리는 비중첩 구조 확인
  (상대방 항목 불변을 각 표가 자체 교차확인) → item17=②표/item19=③표 개별신뢰, item16=derive.
  R4 공식으로 역산해 각사 헤드라인 item14와 ±0.5억 이내 재현 확인(우연 아님).
- **하나생명: 기존 item14/15/27/28후가 ②표 단독(isolated) 값으로 잘못 저장돼 있던 것 발견·정정**
  (진짜 헤드라인=`[지급여력비율총괄]` 5,558억인데 저장값은 5,769.44억=②만 적용했을 때 값이었음).
- 롯데손해: ②만 단독 적용(raw 명시) → ②표가 곧 결합 정답, 경합 없음.
- 부수: 농협생명 item19 채우자 census가 시장하위(36-40후) 결측도 지적 → 같은 raw(③표)로 마저 해소,
  MARKET_M 공식 역산이 item19=10865.69 소수점까지 정확 재현.

재검증: RED 12(전부 무관 기존 건, 회귀 0), 적용후 census 결측 5→4(농협 해소, 잔여 4=예별손해
2023.1-3Q·IBK 2023.2Q 기존 documented). `pytest tests/unit/` 110 passed. xlsx 재생성 완료. inbox
`20260715T0801Z`에 상세 회신(`status: answered`). **2차(과거분기 유사갭)는 위 2026-07-15(2차) 항목에서
완료.**

---

**완결 이력 (2026-07-12, 6개 라운드) — 상세는 `docs/changelog_parser_kics.md` 해당 날짜:**
- (6차) IBK 재정정(공통TFI 합산 누락)+예별손해 3분기 동형 정정. 전수재조정 119건 시도는 포맷 불균질로 폐기(커밋 안 함).
- (5차) KR1011 2023.2Q 다중경과조치(②+③) 값 혼합→분산효과 음수 정정. item16/17/19후 결합불명 판정, None+`_AFTER_SUBRISK_NOT_DISCLOSED`.
- (4차) 요구자본 census 322셀 결측 처리(CARRY206+DERIVE96+EXTRACT20), 322→2(raw부재 영구잔존).
- (3차) items4/12/13 적용후 결측=구조적 미공시(raw 자체 없음) 확인, designer에 표시방식 재고 권장 회신.
- (2차) KR0104 fill오류 발견·원복, "다중경과조치 결합공식 불명" 최초 판정(⚠️ **2026-07-15(2차)에서 오판정으로 재정정됨** — 10,899.56은 오류, 8,979.7이 정답).
- (무번호) validation 재검 잔여10셀 중 9셀 raw 재대조 해소, 추출갭 10→3.

**완결 이력 (2026-07-11, 4개 라운드) — 상세는 `docs/changelog_parser_kics.md` 해당 날짜:**
- (4차) owner 재지시로 세부위험 갭 계속 착수, post_transition/market 스크립트 실버그 6개 발견·수정. 추출갭 52→10.
- (3차) owner "진짜 다 끝났냐" 재확인 요청, fill_subitems 실버그 4개 발견·수정(SKIP 3건 GREEN 전환). 추출갭 52→40.
- (2차) owner ticket `20260703T1138Z` Tier C(금리민감도) 재검증, 실데이터 오염 2건(푸본현대·예별손해) 수정. RS1/RS2/RS4 RED=0.
- (무번호) Tier B 세부위험 후컬럼: 근본버그 4개+회귀 3개 수정. 추출갭 206→52.

**완결 이력 (2026-07-08, 3개 라운드) — 상세는 `docs/changelog_parser_kics.md` 해당 날짜:**
- (3차) 세션 재개, 라이브 게이트 전수 트리아지: KR0051 `19_market` 단위힌트 버그 수정. RED 14→13.
  ⚠️ 별건(당시 미해결, 이후 해소): `scripts/` 다수 파일+xlsx가 git 미추적이었던 문제 — 현재는 추적됨(git 확인).
- (2차) 적용후 R1 가용자본(item1=item2+item3) 항등식 3건 해소(농협생명·롯데손해·하나생명), raw 원인 3건 전부 다름.
- (ROUND2 반려 대응) ③표(주식·금리위험) 미반영 근본수정 — 이전 라운드가 ②표만 고치고 "완료" 보고했다 반려됨. R5/R6 45+6→0, mmult 4→1, COPY 7→2.

**완결 이력 (2026-07-07, 5개 라운드) — 상세는 `docs/changelog_parser_kics.md` 해당 날짜(9차 관련은 후속 3항목 포함):**
- (9차) 적용후 전체룰 재검증 대응, 근본버그 4개 수정. `transition_ratio_after_capture` RED 39→8, R8 147→0 완전해소.
- (9차 후속) item12=item1 셀밀림 154셀 근본원인 확정(라벨 fuzzy-매칭 충돌), 95셀 수정(154→63).
- (9차 후속2/3) item12 잔여 63→0 완료(owner "0 될 때까지 멈추지 마라").
- (8차, downloader) "원본 결측" 판정이 fitz 텍스트추출 실패를 오해석한 것이었음 정정 — 흥국화재·흥국생명 비전으로 직접 판독, item2/3/14/27/28후 복원. 상세는 `docs/changelog_downloader.md` 2026-07-07.
- (7차) ⚠️ 8차 정정으로 무효화된 결론(원본 정상 파일이었음) — 기록만 유지.
- (6차) 악사손해 2024.3Q item27/28 복구, 4→2셀.
- (무번호) FSS 정본으로 선택경과조치 적용사=18개사 확정(`_TRANSITION_APPLIERS`), item28 검사+AMT_MISMATCH 룰 추가.

**2026-06-14 — REFACTOR closure + market 36-46 fitz root-cause + inbox 드레인(4개 항목)**: pdfplumber
localizer 무음실패 root-cause 확인, fitz 재추출로 RED 52→42→23→21. 상세는 `docs/changelog_parser_kics.md`
2026-06-14(4항목).

**K-ICS lane 성숙도**: disclosure+rate-sensitivity+market-subitem 마스터 전부 구축(`kics_disclosure.json`
조립, xlsx 재생성 완료). 게이트는 2026-06-11 RED=0 도달 이력 — 현재 상태는 이 파일 최상단 최신 라운드 참고
(2026-07-16 기준 core RED 12, 전부 documented).

---

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
- [ ] **KB손해 image-only 4분기**: 스캔본 → OCR 경로.

### FY2026Q1 — K-ICS PDF→MD docling 잔여 (inbox 20260612T0900Z)

- [ ] **FY2026_Q1 K-ICS PDF→MD docling** (`data/disclosure/FY2026_Q1/raw/` → md_inbox; 일부 대형 PDF std::bad_alloc) → 금리민감도·시장하위 추출기 재실행으로 흡수.

### F12 — K-ICS 시장위험 하위위험액 전체 파싱 (parser side)

Cross-stage feature (root `TODO.md` keeps a 1-line ref; full detail here). Parser + validation cross-stage. 화면 노출 X, 데이터 신뢰용. Validation half = V3 in `TODO_validation.md`.
- [ ] 시장위험 하위 5개 + 분산효과 row 추출 추가
- [ ] 금리위험액 (+5쇼크 순자산 민감도 = 듀레이션갭) display-ready 필드 분리
- [ ] 출력 schema에 `market_risk_breakdown` 신설 → validation R11 sqrt 정합성 룰의 입력

---

## 🟡 Open / waiting

- [x] **(종결 2026-08-20) RS1–4 룰** — `TODO.md`에 *"validation: RS1–RS4 룰 구현, 게이트 RED=0"*로 이미 완료 기록됨(2026-06-10). 원문: 마스터 ready 회신 = `inbox/validation/20260610T0830Z__parser__ALL__rate_sensitivity_master.md`. (RS1-4는 통과했으나 정식 룰 구현 확인 잔여.)
- [ ] **MLG-2 시장위험 분해** (owner 결정): PL-Tier2급 사별 핸들러 + 금리 유도규칙 owner 결정 필요. R11은 금리 확정 후. [xref: parser-ifrs17] (PL-Tier2급 핸들러 패턴은 IFRS17 lane이 owner; 본 항목은 시장위험액이 1차 데이터라 K-ICS lane 소관.)
- [ ] **IFRS-NORMALIZE** — 23-co full normalization: `row_aliases.yaml` 확장(현 PoC 930/2956 tagged) + K-ICS sensitivity 잔여 empty FY2025_Q4 생보사 normalize. (K-ICS sensitivity normalization이 1차; IFRS17 lane도 row_aliases.yaml 공유하므로 [xref: parser-ifrs17].)
- [ ] **KICS-IMG** — image-only PDF manual OCR: KR0010 KB손해(rule 2 ×2)·KR0079 미래에셋생명·KR0080. 정책: parser는 image-only 만나면 escalate, OCR 즉흥 금지 (`claude-agent-parser.md` §2.1). (KR0010은 2026-06-11 (r)에 owner gold로 RED=0 달성.)
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
