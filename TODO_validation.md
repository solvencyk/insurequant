# Insurequant Validation TODO (Stage 3)

> Last updated: 2026-06-16 · Stage 3/5 — validation
> Prompt: docs/agents/claude-agent-validation.md · Changelog: docs/changelog_validation.md

Session start: read this file + `claude-agent-validation.md` + domain refs (`docs/domains/claude-agent-{kics,ifrs17}.md`). English where Korean encoding is fragile (`CLAUDE.md` rule).

## Status

Stage 3 = numerical consistency + QoQ anomaly + cross-domain checks on parsed numbers. **K-ICS gate RED=23** (2026-06-14 (b) 수렴 후, ~20:55 KST; parser 실시간 reparse 반영으로 RED 52→42→23) + census hole 21. 잔여 23 = **전부 owner 결정 또는 parser 활성도메인**: 등식 2(AIA rule2 + 미래에셋 8_life = documented_exception 대기) + 시장 21(19_market 10 + 36_irr 11 = localizer fitz-fallback 진행 + INTERNAL_MODEL/OCR/micro EXEMPT owner 결정). **validation-actionable reparse = 0.** **금리민감도 RED 0** / **IFRS17 closing·crosscheck 0F · sens 0R/0Y**(pl_bridge 14F = 2023 known + 한화생명 2023.2Q 이상치, 비차단).
> ⚠️ 마스터가 **동시변경 중**(다른 parser 세션 실시간 백필 — kics_disclosure mtime 19:59, sens 19:58). 세션 중 RED 52→42, 시장 31→21. 단일 스냅샷=잠정. 시장 RED은 parser 활성 도메인(localizer fitz-fallback 진행 중)이라 라우팅 제외.
> 비-시장 등식 RED 4종은 근본원인 검증 Workflow로 raw 확정 → 메리츠/코리안리 reparse 발주 + AIA/미래에셋 documented_exception **owner 결정 권고**(아래 P1).

## 🔴 Open — P1

### V10 — KICS gate coverage census + 19_market SKIP blind spot (2026-06-12 owner 적발)
Root cause: gate didn't census "cells that should exist" + treated SKIP as pass. RED=292 after fix.
- [x] **19_market 과잉 RED 수정** (2026-06-13c, source-grounded cadence): 내 06-12 RED 승격이 cadence 미처리로 홀수 간이공시를 과잉flag. `_scan_breakdown_presence()`(disclosure MD 직접확인) + 짝수=항상RED·홀수=MD표유무로 판정. **RED 148→21**(EVEN 18 + 삼성생명 odd 3 = 진짜갭), cadence-SKIP 127(전부 홀수 간이공시). raw 확증(삼성화재/현대 홀수 MD에 세부표 부재).
- [→] **parser 재추출 (19_market 진짜갭 21건만)**: 짝수 full-form 결측 18(KB손해2024.4Q/2025.2Q·한화생명2023.4Q/2024.2Q·흥국생명/흥국화재2024.4Q·DB생명2025.2Q·DB손해2024.4Q·NH2025.4Q·신한이지3·처브3·AIA2025.4Q·카카오2025.4Q) + 삼성생명 odd 3(2023.3Q/2024.1Q/2024.3Q, MD에 표 있음). gold: 하나손해·삼성생명 2025.4Q(이미 GREEN). 148→21로 정정 inbox 발송.
- [→] **2026.1Q 항목 절단 (parser)**: 30사 적재됐으나 전 회사 항목 1–28까지만, 29–46 전무 → backfill.
- [→] **census 미싱셀 28건 (parser)**: 미래에셋(7분기)·코리안리(6분기)·동양·하나생명 등 MD는 parsed인데 JSON 추출 누락.
- [x] **`36_irr` SKIP맹점 폐쇄** (2026-06-13): cadence-aware RED 승격 — item36 공시·41–46 결측이 **짝수분기(2Q/4Q)면 RED**(시나리오표는 2Q/4Q 서식에만 존재, 실증: 41–46 전 분기 짝수에만 적재), **홀수분기는 SKIP**(원천부재 정당). `IRR_SCENARIO_EXEMPT` 면제셋(빈값). 결과: RED 23(전부 짝수, 홀수 false 0). 19_market 동형. → parser 41–46 재추출(아래 23건, market_subrisk inbox 후속).
- [x] **`report_latest.json` fresh-write** (2026-06-13): 게이트가 매실행 `artifacts/kics_validation/report_latest.json` 덮어쓰게 함 → stale glob 함정 제거(소비자 코드 0, orphan 5/25본이 문제였음).
- inbox: `20260611T2200Z__validation__MULTI_ALL__kics_market_subrisk_systemic_underparse.md`. 메모리: `coverage-census-mandatory`.

### V12 — CSM 민감도 전수 재추출(25.4Q 경영공시 기준) + direction sanity (2026-06-15, parser 대기)
owner: IFRS17.html 흥국생명 CSM 민감도 이상 지적. 진단 = 현 소스가 FY2024 DART 사업보고서(1년 stale·비전수), parser 추출 자체는 정확.
- [→] **parser(ifrs17) 전수 재추출 발주**: `sensitivity_heatmap.json`을 25.4Q 경영공시(`data/disclosure/FY2025_Q4`) 기준으로. inbox `20260615T0415Z__validation__MULTI_2025.4Q__csm_sensitivity_refill_disclosure_basis`. risk 전수(사망/해지/사업비/장해질병 정액·실손/…), 당기말만, csm_delta=CSM·pl_impact=손익효과, 억원 정규화, unavailable 정직표기. 미다운로드면 downloader bounce.
- [x] **SENSITIVITY_DIRECTION_SANITY 룰 신설**(`validate_master_tables.py` 5b): sign(csm_delta)≠sign(pl_impact) YELLOW. fill 후 재검증 시 sign-opposition 전수 triage(real vs 파싱오류).
- 참고: 흥국 해지율 역행=source-faithful(건강보험 견인), 장해질병 누락=FY2024 사업보고서 부재 → 경영공시로 해결. recency는 사업보고서≈경영공시(둘다 2025.12.31), 전수·granular가 경영공시 우위.

### V13 — 부모-자식 정합 룰 + INTERNAL_MODEL_36IRR 등록 + 카카오 cadence 정정 (2026-06-16, owner 라이브 QA 3차)
owner SGI 게이트 사각 + parser INTERNAL_MODEL 승인 inbox 드레인.
- [x] **`_parent_zero_child_nonzero` 룰 신설**(`validate_kics_disclosure.py`): 부모 위험액 present&≈0인데 하위 비0 = 구조상 불가능 RED(게이트 차단). item17→29-35, item19→36-40 명시매핑. 전수 3셀: 서울보증 2025.4Q(item35=5212)·2023.4Q(5264)·카카오 2023.3Q(4.72) 전부 대재해 오정렬.
- [→] **parser 발주(3셀 재파싱)**: `inbox/parser/20260616T0130Z__validation__MULTI__parentzero_catastrophe_plus_kakao_19market`. owner K3가 25.4Q만 적시 → 3분기 전부 커버 요청. 서울보증=보증사라 생명장기 0 정상, 대재해를 일반손해 분해→1-7 슬롯 셀밀림 의심.
- [x] **INTERNAL_MODEL_36IRR_EXEMPT 등록**(owner 승인 2026-06-15): `kics_json_rules.py` frozenset 5셀(KR0073 2025.2Q·KR0094 ×4) RED→SKIP. **36_irr RED 11→6**. pytest 110 passed.
- [→] **카카오 2023.3Q 19_market 재특성화**: parser "cadence SKIP" 제안 = 부적절(MD L177-186에 분해표 실재 = 19_market RED 참). micro 억원-coarse라 카카오 2023.2Q 동류 artifact. 처분(파서 적재 후 micro / owner micro exception) = owner 결정. TODO.md(root) line 79-80 카카오 cadence 분류 정정 필요(owner 갱신).

### V14 — backlog #6/#7/#8/#9 (2026-06-16, owner "전부다 진행", 4-에이전트 Workflow)
- [x] **#6 삼성화재 FY2024 IR benchmark RESOLVED**: `validate_nb_csm_multiple.py` `load_fy2024_ir_anchors`(IR series 2024.4Q.multiple_derived_ytd) + 삼성화재 PREFERRED_SCOPE monthly_avg_from_ytd → computed 14.76/IR 15.16 rel 0.026 fallback_used=False. **fallback_pass 2→1**.
- [x] **#6 현대해상 = 영구 fallback 확정 (owner 2026-06-16: "현대해상 IR은 CSM배수 없어 패스")**: 현대 IR이 신계약 CSM 배수를 아예 미공시 → benchmark 불가, fallback(2025.2Q=18.9)이 정상·영구. fetch 불요. V2 line 87 "현대 IR multiple 부재→영구 fallback"과 일치. fallback_pass=1은 이 1건(현대)으로 고정.
- [x] **#7 CONT 면제 → REVERT (owner 2026-06-16)**: 한때 CONT에 documented-재작성 면제를 넣었으나 owner 지시로 즉시 되돌림 — **continuity break(기시≠직전기말)는 무조건 RED, "소급재작성"이라 면제 금지**. cont=15 유지(면제 0), WFY 면제만 존치. pytest 110. 메모리 [[continuity-break-is-red]] + [[route-by-raw-availability]] 저장.
- [→] **#7 2026.1Q boundary = 파싱오류 (정정 2026-06-16, owner 원본검증; 내 #7 오진 시인)**: 5사 2026.1Q 기시 CSM이 misparse — 정답은 직전 2025.4Q 기말(교보 65,110·메리츠 111,037·신한라이프 75,537·에이비엘 9,702·푸본현대 1,907.45). self-closing identity는 opening 검증 못 함(오진 원인). **재작성 아님 = RESTATEMENT_EXCEPTIONS 등록 금지, CONT RED 유지.** `data/dart/FY2026_Q1/` 부재(purge) → downloader raw 복원(`inbox/downloader/…restore_fy2026q1_dart_raw`) → parser/ifrs17 재추출(`inbox/parser/…csm_2026q1_opening_misparse`). 복원 후 재검증.
- [i] **#7 저배수 4사 = scope 오류 아님**(framing 정정): 교보 6.61/한화 9.84=2026.1Q Q1 계절저점 YTD(한화는 IR FY 7.6 초과), 교보플래닛 2.0·처브 2.4=micro 실제 저배수. 분자 전부 waterfall item2 일치. **조사 종결, 액션 없음.**
- [x] **#8 verify_parser_change.py 신설**: snapshot/diff(blast-radius, kics cell-diff)/validate(6검증기 일괄)/all. 추출기 변경 회귀 1커맨드. 통합 validate 검증 완료.
- [x] **#9 QoQ yaml loader = 이미 배선**: `validate_master_tables.py:84` 이미 `yaml.safe_load(config/qoq_thresholds.yaml)`. backlog 항목 stale, no-op.

### V11 — 2026-06-14 (b) 정합성 전수검증 후속 (라우팅 발주 + owner 예외 결정 대기)
근본원인 검증 Workflow(8 에이전트 raw 대조) 후 비-시장 등식 RED 4종 disposition:
- [x] **메리츠 KR0001 rule5 reparse → ✅ RESOLVED**: parser가 item23+item25 12분기 적재(항등도출=공시값 일치). 재검증 **rule5 12 RED→0**. `_resolved/` 이관.
- [x] **코리안리 KR1000 2025.2Q reparse → ✅ RESOLVED**: parser가 코어 1-28 + item28 파생(156.19) + 시장37-40 fitz 적재. 재검증 **7 RED + 19_market→0**. `_resolved/` 이관.
- [x] **푸본현대 sensitivity (ifrs17 발주) → ✅ RESOLVED**: parser 근본원인=mis-tag 롤포워드(shock행0), `_has_shock_rows` 가드로 KB·푸본현대 ok→partial 정직화. 재검증 **SENSITIVITY YELLOW 1→0**. `_resolved/` 이관.
- [ ] **(owner 결정) AIA KR0080 2025.1Q rule2 documented_exception**: image-only scan, item8/item9 819 중복 OCR키잉, 텍스트 reparse 불가. owner TODO.md 예외 등록 시 해소.
- [ ] **(owner 결정) 미래에셋 KR0079 8_life documented_exception**: image-only(파싱 MD조차 부재), subs 29-35 OCR ~8.5% spread, 단일 culprit 없음. **기존 KR0079 rule2 예외를 8_life로 확장** 권고.
- [ ] **(owner 결정) parser irr_exempt v2 잔여**: INTERNAL_MODEL_36IRR = **신한라이프 KR0094×4 + 교보 KR0073 2025.2Q = 5건만**(IBK KR1011은 parser fitz로 41-46 적재·derive rel 0.0% GREEN → 면제 불요, 2026-06-14 정정) + OCR(KB/한화생명/흥국×2) + micro(신한이지 KR0051×3) EXEMPT — 전부 owner 권한. inbox/validation answered 참조.
- [x] **scan false-positive fix**: `_scan_breakdown_presence` clean-cell화 → 삼성생명 odd-Q 3 false RED 제거(19_market 15→10). parser D 종결.
- [x] **SENSITIVITY_UNIT_SANITY 룰 신설**(owner 0712Z claim2): `validate_master_tables.py` RED>1000x/YEL>100x. 640배 회귀가드. 푸본현대 YEL 1(÷100 미정규화 의심) + 미래에셋·롯데·한화손해 sensitivity 0건 → parser/ifrs17.
- [x] **TOOLING_FAIL census 배선 완료**(2026-06-14, owner "AB go"): `validate_kics_disclosure.py._market_tooling_fail()` — nonok.json을 현 데이터와 대조해 여전히-갭 셀만 're-localize' 노출(stale 제외, 비차단). 현 0건. parser fitz-fallback 안착분 이행.
- [x] **hyundai_pl ZLEG 등록 완료**(KR0009): 현대 2024.1Q~2025.2Q `ZLEG_LEGIT_CQ` 등록 → zero_legs 6→1. thread 종결.
- [→] **KR0083 푸본현대 2026.1Q continuity**: FY_BOUNDARY 2025.4Q기말 1906≠2026.1Q기초 1669(Δ12.4%) 현 RED + sensitivity flagged = 실데이터 의심, 잔여 유지.

### V7 — NB CSM cross-source + 시계열 전수 (parser P1/P2 회귀 잔여)
Rule `NB_CSM_DART_VS_IR_ANNUAL_SUM` codified (§1.2, RED, tol max(5%·|IR|, 100억)). Tools: `check_nb_csm_widespread.py` (FY24 snapshot, 6/7 OK) + `check_nb_csm_history.py` (13Q×9사 baseline). FY24 widespread: 롯데 1.233 (+23%, FY25 의존), 나머지 ~1.00 OK.
- [→] **Parser P1**: 롯데 FY2025 구성요소별 차이조정 표 capture + NB override (412,168 = IR FY25 일치). Raw: `data/dart/FY2025_Q4/raw/KR0003_롯데손해보험_20260319001293/_00760.xml:27375`.
- [x] **🚨 Parser P2 회귀 = 재확인 완료 (2026-06-16)**: off-by-one-year **해소 확정**(현 `data/ir/series/` Q1 YTD-reset 정합, 삼성화재 6782.7→14426→...→2024.1Q 8855.5 리셋). `check_nb_csm_history.py` **복원**(self-contained, 컨벤션 series 메타 도출) + `nb_csm_history_check.json` 갱신. **systemic-3 = 실재(정렬 아티팩트 아님), 근본원인 = DART CSM_waterfall partial/no_csm_block 추출**: 롯데 2025.2Q partial→NB_YTD=0→delta −1098.5(음수 불가) / 미래에셋 2025.2Q·3Q partial→collapse-then-catchup spike(=↑↓ 교대) / 2025.2Q cohort-wide 동일. DB 부호반전은 DB DART 2025.2Q+ 부재로 재현 안 됨. 삼성생명 2025.2Q OVER(+26%)=status ok=진짜 scope 차이(별건). → parser/ifrs17 `20260616T0230Z__...nb_csm_partial_extract_corrupts_history` 발주.
- [→] **한화손해 stale carryover** (별도 parser 버그): 2025.1Q DART NB가 2024.1Q 값 그대로 복제됨. 한화손해 IR note에 기록.
- [ ] (passive) V1 활성화 시 `CSM_WATERFALL_DART_VS_IR` new_business step과 overlap → retire 검토.
- Regression cmds (parser P1+P2 후): `check_nb_csm_widespread.py` → ok=7/7; `check_nb_csm_history.py` → OVER/UNDER 0 수렴.
- Gate enforcement는 publishing stage 측(사용자가 publisher에 전달).

## 🟠 Open — P2

### V8 — DART 자기완결 정합성 (CSM_waterfall 도메인 잔여)
PL_BRIDGE + CSM_CROSSCHECK 소비자 코드 구현 완료(2026-06-07). 빌드→검증 통합(`validate_master_tables.py`가 `build_root_masters.py` 자동 선행, idempotent; `--no-build`로 끔). 회귀 명령: `python scripts/validate_master_tables.py`. 현재 dup:0 spike:1 cont:12 crosscheck:0F closing:0F.
- [→] **데이터 채움 (parser/수집)**: 미래에셋 CSM상각 2025.2Q·3Q·2026.1Q 누락(2025.1Q는 있음), 롯데 생명장기손익 2025.2Q 누락(1Q·3Q는 있음). closing/pl_bridge가 skip하던 진짜 hole.
- [→] **잔여 확인 대상 (소수)**: 교보생명 cont(2024.3Q/4Q −2,905·2026.1Q +5,659), 케이디비 spike(2024.1Q→2Q +58%). 그 외 cont 회색지대(삼성생명 −1,452 등 작은 Δ)는 IFRS17 기초 재작성 가능 → 무조건 오류 아님, YELLOW로 둠.
- [→] **PL 잔여 14F**: (1) 2023 분기 사이트 비노출 → 넘어감. (2) 소액 잔차(흥국 2025.1Q +714·KB라이프 +1,136·악사 +3,483) — 종목합산 기타비 내재 또는 미세, 지나감. (3) bare로 닫히는 분기(흥국 2024.4Q 등)는 정상.
- 참고: dual-form은 의도된 설계(사용자 확인) — bare 통과 분기 flag 안 함. 과잉진단 금지(§1.5). 단위: pl 백만원 / waterfall 억원 (cross-check ×100 정렬).

### V9 — 사용자 xlsx 수기검수 후속 (룰 3종 WFY/ZAMORT/ZLEG, parser 대기)
영속성 해결(`csm_manual_overrides.json` + `_apply_csm_overrides()` 훅, 빌드 생존). WFY 10/10 판별 완료(wfy 0). ZLEG 23→1(동양 2025.3Q 잔여). 메모리 `validation-blind-spots`·`master-xlsx-review-loop`.
- [ ] 교보(6.61)·한화생명(9.84)·교보플래닛(2.0)·처브(2.4) 저배수 별도 원인 조사(분자 scope?).
- [→] **신규 (parser)**: 메트라이프 영업이익 등식 2분기 FAIL(+12,086/+12,897) + 코리안리 crosscheck 2F(wf 상각 1년 lag 의심) + 동양 2025.3Q zleg 1건.
- [→] **현대해상 PL 8분기 재추출 (parser, 경고 inbox)**: 생명장기원수/기타원수/재보험손익/기타재보 — legit_absent 오판, 답지 anchor. 2025.2Q 패스.
- inbox: `20260611T0900Z__validation__MULTI_ALL__user_xlsx_audit_followup.md`.
- 참고: 보험손익 잔차 = LOB 별도/연결 기준 오선택부터 의심(§1.5). 신계약 CSM은 pl_breakdown_master에 구조상 없음 → V7 NB_CSM_DART_VS_IR + closing identity가 검증 담당.

### V1 — DART↔IR cross-source 2개 룰 활성화 (segment 폐기로 3→2)
룰 [§1.2 + §1.4]. RED → DART parser loopback. **현재 IR-side 정형 JSON 부재로 전사 SKIP.** (segment 룰 폐기 → V8 대체)
- [ ] **IR parser delivery 대기**: `data/ir/<period>/parsed/<KR>.json` (root TODO F18). 도착 cohort 9사: 메리츠·삼성화재·현대·KB·DB·한화생명·삼성생명·미래에셋·동양. 도착 즉시 룰 자동 ON.
- [ ] **Threshold v1 튜닝**: 활성화 후 실제 diff 분포 보고 조정. v1: `CSM_WATERFALL_DART_VS_IR` max(5%·|IR|,100억)/step; `CSM_BREAKDOWN_DART_VS_IR` max(5%·|IR|,100억)/item (메리츠는 보종 비교 영구 SKIP — 측정요소별 표만, total만).
- IR factsheet NB CSM multiple 가용성: 부재(현대해상·KB손해); 간접 산출 가능(DB손해 = 신계약 CSM + 월납보험료 derive).

### V2 — IFRS17-NB-RECONCILE 정합성 (한화 fallback retire 완료)
`validate_nb_csm_multiple.py` period-aware denominator + fallback flagging. 한화 fallback retire 완료(2026-06-12 재검증, `fallback_used=False`). 결과: tested 5 / pass 5 / fallback_pass 2(삼성화재·현대).
- [ ] 삼성화재 IR annual benchmark 보강 — 잔여 fallback 1건 해소. 2026-06-12 재확인: aligned FY2024 행 실패 → 2025.3Q fallback(rel 0.244=tol 0.25 턱밑, tolerance-loophole 경고). FY2024 연간 IR 분모 소싱 필요. (현대는 IR multiple 부재 → fallback 영구 유지.)

### V3 — K-ICS 시장위험 분산효과 validation (F12 cross-stage)
validation 룰 2개 구현 완료(2026-06-09b, `kics_json_rules.py`): `19_market`(item19=sqrt(V'·M·V), V=[36–40], MARKET_M 5×5) + `36_irr`(금리위험액 시나리오 분해). 정본 `docs/agents/kics-market-risk-decomposition.md`. 골든 3/3 일치. 화면 노출 X.
- [→] parser stage가 item36–46 적재(시장위험 세부표 5종 + 금리 시나리오 순자산가치 6종) — 진행 중. (V10 재추출과 동일 작업축.)
- [ ] 적재 단위(억원 vs 백만원) parser 회신 확인 → 백만원이면 대조식 ×100 조정. 적재 후 게이트 RED=0 확인.

### V4 — QoQ threshold registry
`config/qoq_thresholds.yaml` §2 + `QOQ_DELTA_WARN` 소비자 코드 구현 완료(2026-06-09, `validate_master_tables.py` 4번). CSM 항목 대상(누적→YoY / 시점→QoQ, floor 50억), PL 손익 제외. 193 YELLOW, 진짜 의심=이자부리 부호반전 3건(동양·교보·코리안리) → parser inbox. 전체 `data/_derived/qoq_warn.json`.
- [ ] (잔여 미구현) yaml loader precedence(item→domain→global) + prior-snapshot fetch + 누적 net-quarterly 변환 + finding emit(YELLOW, summary 기록, loopback 안 함). 진입점: K-ICS는 `validate_kics_disclosure.py` hook, IFRS17은 `validate_csm_waterfall.py` / 별도 스크립트 결정 필요.

## 🟡 Open / waiting

### V5 — 누적 항목 등록 목록 확장
§2.3 등록: IFRS17 `new_business_csm`, `csm_amortization`, `insurance_revenue`. 신규 누적 항목 발견 시 등록 + net 분기 기준 비교로 자동 전환.
- [ ] (운영 중 발견 시 갱신)

### V6 — KR0010 KB손해 OCR 잔여 RED 2건
K-ICS rule 2 OCR 미정확 (KR0010, KR0079도 image-only). 사용자 owned (`TODO.md` `KICS-IMG`). validation gate는 documented exception 처리 중.
- [ ] 수기 OCR 완료 → KICS-VALIDATE RED 2 → 0 회복.

## ✅ Done (archive)
- V10 19_market SKIP→RED 승격 + coverage census 신설 — 2026-06-12 (changelog 06-12)
- V-RS K-ICS 금리민감도 RS1–RS4 룰 구현 + 검증(RED=0, KR0011 basis 예외) — 2026-06-10 (changelog 06-10); consolidate_inbox VALIDATORS 선배선(RS/waterfall) — 2026-06-12 (changelog 06-12 b)
- V8 소비자 코드 구현 + 룰 정식화(PL_BRIDGE 8단·CSM_CROSSCHECK 4Q-only) — 2026-06-07 (changelog 06-07)
- V8 CSM_waterfall closing 40F→0F — 2026-06-07b (changelog 06-07 b)
- V8 CSM_CROSSCHECK tol 3단계 + 진짜 2F 해소→0F(KB라이프 wf 이중합산·코리안리 룰 스코프) — 2026-06-07c/d (changelog 06-07 c/d)
- V8 보험손익 잔차=LOB 별도/연결 진단 + DB손해·KB손해 fix(PL_BRIDGE 31F→16F) — 2026-06-07e/f (changelog 06-07 e/f)
- V8 흥국화재 해소(빌드 누락 원인) + 빌드→검증 통합 — 2026-06-07h/2026-06-08 (changelog 06-07 h)
- V8 CSM_PLAUSIBILITY 룰 신설(dup/spike/cont) + 메트라이프 2배·케이디비 복붙·흥국·롯데 해소 — 2026-06-07g/2026-06-08 (changelog 06-07 g)
- V8 MASTER_COVERAGE 룰 신설(HOLE 1급 검증) — 2026-06-08 (changelog 06-08)
- V9 룰 3종 WFY/ZAMORT/ZLEG 신설 + 4갈래 조사 — 2026-06-11 (changelog 06-11)
- V9 overrides 영속성·NB EX-기타·아이엠 정정 재검증 + exception 등록(WFY 9건·ZLEG_LEGIT) — 2026-06-11b (changelog 06-11 b)
- V9 AIA 사코드 KR0080 + 불가능-0 leg 룰 + 현대 legit 오판 정정 — 2026-06-11c (changelog 06-11 c)
- V2 PREFERRED_SCOPE 한화 monthly_avg_from_ytd + 정직성 플래그 + retry max 8→5 + 한화 fallback retire — 2026-05-31/2026-06-12 (changelog 06-12 b)
- V7 history check 도구(`check_nb_csm_history.py`) + systemic 3건 발견 + 한화손해/코리안리 오진 정정 — 2026-06-01 (changelog 06-01 archive)
- V4 `config/qoq_thresholds.yaml` v1 + QOQ_DELTA_WARN 구현 — 2026-05-31/2026-06-09 (changelog 06-09)

## 🛡️ Documented exception 관리
운영자(사용자)만 `TODO.md`에 `(도메인, 회사코드, 분기, rule_id, 사유)` 추가 가능. 서브에이전트가 자체 RED waiver 쓰지 말 것. `escalate_to_human` 단계에서만 "재파싱 5회 실패" 사유 기록.

현재 활성 exception:
- KR0010 KB손해 / KICS rule 2 / image-only PDF OCR 미정확 (V6)
- KR0079 미래에셋생명 / KICS rule 2 / image-only PDF OCR 미정확

## 📞 Loopback contract
§3. **max 5회**. RED packaging에 `suspected_source: "DART" | "IR" | "internal"` 명시. cross-source 룰은 항상 `"DART"`.

| 조건 | next_action | exit |
|---|---|---|
| RED=0 | `pass` | 0 |
| YELLOW만 (RED=0) | `pass` | 0 |
| loop_iteration==5 & RED>0 | `escalate_to_human` | 2 |

## 🔗 참조 룰셋 / 코드
- 권위 doc: [`docs/agents/kics-json-validation-rules.md`](docs/agents/kics-json-validation-rules.md) (R1–R10 formulas, tolerance, R4/R7 matrices, item-label mapping)
- K-ICS 구현: [`src/solvency/validation/kics_json_rules.py`](src/solvency/validation/kics_json_rules.py)
- 러너: K-ICS `python scripts/validate_kics_disclosure.py` · IFRS17 CSM `scripts/validate_csm_waterfall.py` · NB CSM multiple `scripts/validate_nb_csm_multiple.py` · reconcile loop `scripts/run_ifrs17_csm_reconcile_loop.py`
- Output: `artifacts/validation/<domain>_<timestamp>.json`
