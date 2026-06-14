# Validation Changelog (Stage 3)

> Last updated: 2026-06-12 · Stage 3/5 — validation
> Prompt: docs/agents/claude-agent-validation.md · Authoritative rules: docs/agents/kics-json-validation-rules.md

Validation-only history. Cross-stage changes also keep a 1-line cross-reference in [`docs/claude-changelog.md`](claude-changelog.md).

---

## 2026-06-14 — 파서 회신 2건 처리: 시장위험 146 회수 재검증 + item14후(8_post) 검증

새 parser inbox 2건 드레인(둘 다 resolved → _resolved):

- **`market_subrisk_recovered_146` 재검증 ✅**: 파서가 LLM추출+sqrt reconcile<2% 게이트로 36-40을 103→**146 all-five** 회수(41-46 144→**177**), gold 1325셀 영속화. master 반영 확인(all-five=146/41-46=177 실측). 게이트 19_market RED **148→21**(파서 회수 + 내 source-grounded cadence 합산). 파서가 이전 SKIP 요청 철회("200+ RED은 룰 아티팩트 아니라 underparse, owner·validation 옳았다") — 내 cadence 진단(홀수=간이공시) 독립 확인.
  - **핵심 회신**: 파서의 "odd-Q 103 EXEMPT 등록" 요청 **불필요** 통보 — source-grounded 룰이 disclosure MD 직접 읽어 홀수 간이공시를 자동 SKIP(수동 명단관리 불요, 분기 자동갱신). MARKET_BREAKDOWN_EXEMPT는 "짝수인데 원천도 부재" 예외만.
  - 잔여 19_market 21 = scan/OCR(AIA·카카오) + 짝수 full-form 결측(한화생명·흥국·DB·NH·KB손해·신한이지·처브) + 삼성생명 odd 3(텍스트표 존재·누락). `19market_real_gaps_21` inbox와 일치.
- **`post_transition14_done` (owner #4 / xlsx #3 blocker) 검증 ✅**: 파서가 생보 경과조치 적용후 item14후 적재(전=후 스킵버그 + _is_market_section 오분류 수정). 게이트 **rule 8_post = GREEN 442 / RED 0**(hollow SKIP 아님). 검증식 (2후+3후)/14후×100≈item27후 25/25 일치.
  - 파서의 룰 SKIP 요청 2건(36_irr/19_market 부분데이터 SKIP) **승인 안 함**: 0600Z에서 파서 철회. 올바른 해결은 SKIP rubber-stamp 아니라 데이터 회수 + source-grounded cadence(이미 적용). PDF census AGGREGATE 244 blanket 등록도 안 함(잠정후보).

게이트 현재: K-ICS RED 58(19_market 21 + 36_irr 16 + census 21), RS RED 0, IFRS17 closing/crosscheck 0F. owner #4 done.

## 2026-06-13 (c) — 19_market 과잉 RED 적발·수정 (source-grounded cadence; 148→21)

owner "19_market 148 진짜 어려운 거냐" 질문 → raw 추적으로 **내 2026-06-12 19_market RED 승격이 cadence 미처리로 과잉 flag**임을 적발(36_irr엔 넣은 cadence를 19_market엔 안 넣음 = 내 버그, owner 격노건과 반대방향).

- **진단(raw 확증)**: 148 RED을 MD 직접 확인 — 삼성화재 2025.1Q(홀수) MD엔 item19=60,822만 있고 36–40 세부표 없음(주식/금리위험액은 경과조치 문맥뿐). 생보 9사+삼성화재 등 **1Q/3Q는 간이공시라 세부표 원천부재**(69/72 raw 확증). 현대해상도 2023.3Q엔 표 있었으나 2025.3Q엔 없음 = 시기별 cadence 변화.
- **수정 (source-grounded + parity)**: `validate_kics_disclosure.py._scan_breakdown_presence()` — item19 공시·36–40 결측 후보셀의 disclosure MD를 직접 읽어 세부표 5종 라벨 distinct≥3이면 표 존재로 판정. `run_validation(source_has_breakdown=...)` 파라미터로 전달. `kics_json_rules.py` 19_market: **짝수분기(2Q/4Q full form)는 결측이면 무조건 RED**(텍스트스캔이 이미지/스캔표를 못 보므로 짝수는 숨기지 않음), **홀수분기는 MD에 표 있으면 RED·없으면 SKIP**(간이공시 cadence). `IRR_SCENARIO_EXEMPT`처럼 MARKET_BREAKDOWN_EXEMPT는 override 유지.
- **결과 19_market: RED 148→21** (EVEN 18 full-form 갭 + ODD 3 삼성생명 텍스트갭 = 진짜 추출가능 갭) / **cadence-SKIP 127 전부 ODD**(간이공시 원천부재, 짝수 숨김 0). GREEN 289 불변. 하나손해·삼성생명 2025.4Q는 파서가 이미 추출(GREEN).
- **자기정정**: 직전에 "148 전부 파서갭"이라 한 진술 철회 — raw 보니 ~127은 cadence-legit(내 룰 과잉), 진짜 갭은 21. 게이트 RED 264→**58**(19_market 21 + 36_irr 16 + census 21).

## 2026-06-13 (b) — 36_irr SKIP맹점 폐쇄(cadence-aware RED) + report_latest fresh-write

owner "TODO에서 확실히 고쳐야 하는 것만 골라 즉시 수정" 지시 → validation 단독 must-fix 2건(파서 무의존, 결정적):

- **36_irr SKIP→RED (cadence-aware)** (`kics_json_rules.py`): 19_market과 동일 맹점(부모 present·자식 결측인데 SKIP=통과). 단 41–46(금리위험 순자산가치 6시나리오)은 **짝수분기(2Q/4Q) 서식에만 존재**(실증: 41–46 보유분기 = 2023.2Q~2025.4Q 짝수 6개뿐, 홀수 0). 규칙: item36 공시·41–46 결측이 **짝수분기면 RED**(parser gap), **홀수분기면 SKIP**(원천부재 정당). `IRR_SCENARIO_EXEMPT`(빈값) 문서화 면제. 결과 **RED 23 (전부 EVEN, ODD false 0)** — 기존 SKIP에 은폐됐던 짝수분기 갭. 23건: 2023.2Q(BNP파리바·흥국화재) / 2023.4Q(KB손해·신한이지·에이비엘·하나생명·하나손해·흥국화재) / 2024.2Q(KB손해·교보플래닛·BNP·신한이지·흥국화재) / 2024.4Q(교보플래닛·신한이지) / 2025.2Q(교보플래닛·교보생명·하나생명) / 2025.4Q(IBK연금·KB손해·교보플래닛·케이디비·하나생명). → parser 41–46 재추출(market_subrisk inbox 후속).
- **report_latest.json fresh-write** (`validate_kics_disclosure.py`): 게이트가 매실행 `artifacts/kics_validation/report_latest.json`을 fresh로 덮어씀. 기존엔 orphan stale(5/25본)이 glob 정렬에서 timestamped 최신보다 뒤로 정렬돼 mis-read 유발(소비자 코드 0). 함정 제거.
- **게이트**: RED=268(19_market 220 + 36_irr 23 + census 21 + 등식 ~). 19_market 여전히 작동, compile OK.

## 2026-06-13 — owner 직접지시 kics_disclosure 데이터 정정 (dedup + 스케일 + AIA 적용후) + 19_market 면제 거부

owner가 kics_disclosure.json 다수 데이터 버그 지적. validation이 직접 정정(파서 무의존, 결정적):

- **중복행 dedup** (`scripts/dedup_kics_disclosure.py`, backup .bak): 16,160→15,665(−495). key+값 동일 34키 축약 / 값상이는 항등식 채택(비영단일 56, 23=24+25+26 closure 12 code·q, 27·28 정의식 13, 최빈 9; **FLAG 0**). garbage 기각(item12 68431·71335, item26 8313). 리포트 `artifacts/kics_validation/dedup_report_*.md`. 파서엔 "파이프라인 끝에 dedup 상설" + first/last/any 질문 답(="항등식으로 1행").
- **하나손해 2026.1Q 기본자본비율 2861%→28.62%** (`scripts/fix_kics_targeted.py`): 근본원인 item2(기본자본)=132375 ×100 스케일오류(item2>item1 불가 식으로 적발 — blanket threshold 아님; 카카오페이 6310%는 item2≤item1이라 정상 보존). item2→1323.75, item3 plug(−125617=item1−item2_old)→5434.25 복구, item28(적용전+적용후)→28.62. rule 1·8_post RED 해소.
- **AIA(KR0080) 적용전=적용후 강제** (owner: 경과조치 미적용사): 값_적용후 16행 copy-leak(item2=39162·item3=75984 frozen) 일소 + item27 8분기 도출(item1/14×100). rule 7 RED 해소. 적용전(값)은 파서 재적재로 이미 클린.
- **코리안리 자동차손익 null→0** 권고(owner: 자동차=일반 sub항목, 별도 미분리 = 정상). 파서 빌드 반영 요청.
- **19_market 면제 요청 거부**: 파서가 "fitz no-pdf 0건 = 223건 구조적 미공시"로 MARKET_BREAKDOWN_EXEMPT 등록 요청 → **blanket REJECT**. 근거: 하나손해(image-split)·삼성생명(라벨변형) 실공시 입증(2026-06-12a) = 추출기 한계지 부재 아님. reconcile-fail 3건은 표 존재. 조건부만 허용(image-split 스티칭+라벨변형 재추출 후, 그래도 없으면 raw 페이지 근거 첨부분만 셀단위 등록). MARKET_BREAKDOWN_EXEMPT 여전히 비어있음.
- **게이트**: dedup+정정 후 RED 293(19_market 229 + census 22 + 등식 ~42). 내가 유발한 RED(rule1 KR0050, 8_post KR0050) 전부 해소, 신규 0. 잔여 등식 RED(rule5/8 메리츠 등)는 기존 파서 추출 이슈.
- **진행 중(서브에이전트)**: 금리민감도 11사 2025.4Q 추출시도 + 현대 PL 2023–24 IR대조. 결과 도착 시 파서 라우팅. inbox 회신: `20260612T1100Z__parser__...2026q1_loaded_and_19market_exempt_request.md` ## 답변.

## 2026-06-12 (b) — consolidate_inbox 선배선(RS/waterfall) + V2 fallback 재검증 + market 스레드 정정종결

owner 백로그 다이제스트(#2/#6/#10) 즉시가능분 처리.

- **#2 consolidate_inbox VALIDATORS 배선**: `_rate_sensitivity_findings`(RS1/RS2_base RED) + `_waterfall_findings`(must_reparse) 추가, `VALIDATORS=[continuity,rate_sensitivity,waterfall]`. TEMPLATE을 `{section}`/`{request}`로 일반화(continuity 보존). 세 RED 버킷 0건 = **선배선**(owner "RED 발생 전 배선"). 06-09(a) "waterfall 항목 생기면 추가/untested 안 씀" 방침 → 스키마 확정(RS=runner dict키, waterfall=`failed` 버킷 동형)되어 pre-wire. 검증 3중(idempotent run findings=9 skip / 계약 플레이스홀더 테스트 / 합성 RED e2e: name→code·period유도 정상).
- **#6 V2 fallback**: `validate_nb_csm_multiple.py` 재실행 — **한화생명 fallback_used=False = retire 확정.** 삼성화재(2025.3Q 17.54 vs IR 14.1, rel 0.244=tol 0.25 턱밑)·현대해상(2025.1H)은 aligned FY2024 행 실패→fallback 통과(validator tolerance-loophole 경고). 삼성화재 IR annual benchmark 보강 미결(FY2024 IR 분모 소싱 필요).
- **#10 housekeeping**: inbox/validation 5건 `_resolved/` 이관(RS 2 clean + market 3 정정후). market_coverage_phase2_loaded의 "잔여 SKIP 정당(삼성화재·삼성생명·현대·한화 PDF 비공시)" 결론 **OVERTURN** 기록(=2026-06-12(a) 적발과 연결). "clean 종결" 아닌 "정정 종결"로 판단.

## 2026-06-12 — KICS 게이트 2대 사각 적발: coverage census 부재 + 19_market SKIP맹점

owner 격노 적발: (1) `kics_disclosure.json` 2026.1Q가 한때 KB손해 1개사(26셀)만 적재됐는데 게이트가 RED=0 통과 (2) 시장위험 세부 5종(item 36–40)이 거의 미적재인데 19_market이 SKIP으로 통과. 다른 세션은 즉시 적발. **근본원인 = 게이트가 "있는 셀이 맞나"만 보고 "있어야 할 셀이 있나"를 안 봄.**

**근본원인 (코드 레벨):**
- `validate_kics_disclosure.py`는 `run_validation(records)` — 데이터에 **존재하는 (회사×분기) bucket만** 순회. 분기/회사가 통째로 빠지면 finding 0개 → RED=0. 기대 universe 개념 부재.
- `kics_json_rules.py` `19_market`: 부모 item19 공시 + 자식 36–40 **전부 결측이면 RED이 아니라 SKIP**. 게이트가 RED만 세니 SKIP=사실상 통과. (`36_irr`도 동형 — 추후 검토.)

**수정 2건:**
- **`19_market` SKIP→RED 승격**: 부모 item19 공시인데 36–40 전무 → RED(parser gap 추정). 부분결측은 0 처리 허용 유지. 진짜 미공시는 `MARKET_BREAKDOWN_EXEMPT`(회사,분기) 문서화 면제(현재 비어있음).
- **coverage census 신설** (`validate_kics_disclosure.py` `_coverage_census`): regular-filer(≥분기절반 출현) × 분기 기대그리드 → 빠진 (회사,분기) RED + exit code 반영. 리포트에 `coverage_census` 블록·콘솔 분기별 미싱 출력.

**재실행 결과**: RED=292 (수정 전 사실상 은폐). 내역: 19_market 224건(36개사·13분기 전부 — 삼성생명/삼성화재/현대/DB/메리츠 포함) + census 미싱셀 28 + 등식 RED 40. **224건은 수정 전 전부 SKIP**이었음.

**raw 교차검증 (미공시 반증)**: 하나손해 2025.4Q는 5종 실재(금리30,358/주식62,491/부동산2,643/외환12,483/자산집중5,251)이나 표가 `<!-- image -->`로 분절 → 파서 미봉합. 삼성생명 2025.4Q는 "1.금리위험액"+충격시나리오방식 중간열 라벨변형. 둘 다 미공시 아님 = 전사 파서 갭. 2026.1Q는 항목 1–28에서 추출 절단(29–46 전무).

inbox: `20260611T2200Z__validation__MULTI_ALL__kics_market_subrisk_systemic_underparse.md` (route reparse — 36–40 전사 재추출 + 분절표 봉합·라벨변형 가이드 + 2026.1Q 29–46 backfill + census 28셀). 메모리: `coverage-census-mandatory` 신설.

## 2026-06-11 (c) — 현대해상 PL legit_absent 오판 적발 + AIA 사코드 + 불가능-0 leg 룰

owner가 현대해상 2026.1Q PL 답지(`gold/보험손익 breakdown_현대해상_2026.1Q.xlsx`)로 parser의 legit_absent 판정 반박.

- **AIA 사코드** (owner 재지시): `CSM_amortization.json` 10행 사코드 공란 → KR0080 채움. 원인: `build_tidy_exports.py meta()`가 kics_disclosure 원수사명만 봐서 kics 미수록 AIA는 None. `NAME_CODE_FALLBACK`(에이아이에이생명보험→KR0080) 추가(영속) + json 즉시 패치.
- **불가능-0 leg 룰** (`IMPOSSIBLE_ZERO_LEGS`): 생명장기 원수손익·기타원수·재보험손익·기타재보 4종은 장기보험사면 0원 불가 → 0.0이면 RED. 현재 0건(전부 None)이나 미래 가드. 메모리 `validation-blind-spots` 보강.
- **현대해상 legit_absent 오판 정정**: parser가 4종을 도출불가로 판정했으나 답지로 실재 확인(생명장기원수 279,302=241,253+37,322−126,865+127,592 검산 일치). raw에 보험수익 분석공시 멀쩡. ZLEG_LEGIT에서 **현대 회사면제 제거 → 8분기 재노출**. 단 **2025.2Q만** 진짜 미공시(보험서비스비용·재보험수익 자체 부재, owner 확인) → `ZLEG_LEGIT_CQ` 분기단위 면제.
- 교훈: legit_absent 주장은 **raw 표 존재로 교차검증** 필수 — 회사 전체 면제는 분기단위 진짜 미공시를 가린다.

inbox: `20260611T1000Z__validation__KR0009__hyundai_pl_legit_misjudge.md` (경고, route reparse, 8분기 재추출 + 2025.2Q 패스).

## 2026-06-11 (b) — parser 회신 재검증 통과: overrides 영속성·NB EX-기타·아이엠 정정 확인 + exception 등록

parser가 V9 inbox에 회신: ⓪ `csm_manual_overrides.json` + `_apply_csm_overrides()` 훅 구축(빌드 생존) ③ NB EX-기타 + `_MULT_FLOOR=1.0` 적용 ④ 아이엠 분자 CSM열로 정정(0.02→8.36/8.82) ① WFY 10/10 판별(DB손해 re-anchor 18셀 / 9건 legit restatement) ② PL None 분류 + gold-cell +170셀, 신한이지 CSM 제외(×1000 단위오류).

**재검증 (기본 빌드 포함)**: 정정 전부 빌드 생존 ✅ (롯데 16,774.38 / 아이엠 1,599.8 / DB re-anchor / 신한이지 제외). `--no-build` 모드 해제.

**exception 등록**: `WFY_EXCEPTIONS` 9건(legit restatement — 교보 3Q24 공식 소급재작성 등) + `ZLEG_LEGIT` (현대 분리미공시 4종 / ABL 재보 4종 / 서울보증·AIG·교보플래닛·신한이지 ALL). 결과: **wfy 9→0, zleg 23→1**(동양 2025.3Q 잔여).

**신규 발견 → parser 회신**: 메트라이프 영업이익 등식 2분기 FAIL(+12,086/+12,897, gold-cell 후 표면화) + 코리안리 crosscheck 2F 재출현(wf 2024.4Q 상각 ≈ pl 2023.4Q → 1년 lag 의심, KR1000 basis 연관).

SUMMARY: coverage 0/0 | closing 0F | dup0/spike1/cont16/wfy0/zamort0 | pl_bridge 2209P/16F(2023 12+메트라이프2+KB라이프·흥국 소액2) | zleg 1 | crosscheck 2F(코리안리) | qoq 195Y.

## 2026-06-11 — 사용자 xlsx 수기검수 적발 → 검증 사각 4종 보강 + 4갈래 조사

사용자가 마스터 xlsx 수기검수로 validation 미스 적발 (롯데 2023.2Q 기초, KDB 2023 상반기 상각 공란, 미래에셋 상각 누락, 현대해상 PL leg "0", 아이엠라이프 배수 0.02). **검증 사각 4종을 메모리+룰로 영구 반영**:

**신규 룰 3종** (`validate_master_tables.py`):
- **WFY**: FY내 기초 CSM 동일성 (YTD 컨벤션). 기존 연속성은 FY 경계만 봄. → 즉시 10건 적발 (DB손해 FY2023 4분기 전부 상이 등 — 롯데 동형 정정공시 의심, parser 재확인).
- **ZAMORT**: CSM상각 == 정확히 0 불가능 (사용자 룰 지시).
- **ZLEG**: PL 생명장기 sub-item 10종 중 0/None ≥4 무더기 flag → 28건 (현대해상 13분기 — **None이 bridge SKIP으로 은폐되던 패턴**; "0"으로 보인 건 xlsx의 None 렌더링).

**4갈래 병렬 조사 결과**:
- **xlsx diff**: 사용자 수정 24셀+신규 12행 식별 (롯데 2023.1Q신설+2Q전항목 / 케이디비 2023상반기 / 미래에셋 2023.1Q신설+2025.2Q~26.1Q 상각신설·가정재분해). → parser가 root JSON·xlsx까지 ingest 확인(19:12). ⚠️ diag stale — 다음 빌드 시 소실 위험, inbox CRITICAL로 전달. validation은 당분간 `--no-build`.
- **NB 분모**: 기타(비월납, 대부분 단체) 초회보험료 혼입 확정. EX-기타 시 농협생명 3.71→11.20, NH손해 1.74→11.38, KB라이프→10.48, 삼성생명→11.47 (10~17 정상권 진입). **삼성생명 EX-기타가 IR에 5분기 전부 근접**(MAE 0.43 vs 1.10; IR 정의=월납월초) → builder EX-기타 전환 권고. 교보·한화는 기타로 설명 안 됨(별도 원인). 568억은 NH손해 기타(농협생명은 649.8억).
- **PL zeros**: 정확히-0 무더기 0건 — 실체는 None. 예실차=0 45셀은 미공시→identity 유도(정상).
- **소스 추적**: DART 미공시 11사 전부 **연간 감사보고서(00760 별도, pblntf_ty=F)** 소스 — 검증된 공시지만 4Q만. **하나손해/하나생명/신한이지는 지주 분리가 아니라 자체 별도 감사보고서 파싱** (지주 보고서 미사용 — 분리 시도 자체가 없었음). 아이엠라이프 DART 분기 부재 = 비상장 지주 자회사(사업보고서 의무 없음). **아이엠라이프 0.02 = 분자 오염**(BEL+RA+CSM 행합 4.4억; 실제 CSM 1,599.8억) → parser 수정 대상.

inbox: `20260611T0900Z__validation__MULTI_ALL__user_xlsx_audit_followup.md` (diag 영속성 CRITICAL + WFY 10건 + ZLEG 28건 + NB EX-기타 + 아이엠라이프). 메모리: `feedback_validation_blind_spots` + `project_master_xlsx_review_loop`.

## 2026-06-10 — K-ICS 금리민감도 RS1–RS4 룰 구현 + 검증 통과 (RESOLVED)

owner 발주(RS1–RS4) + parser 마스터 적재(`kics_rate_sensitivity.json` 423행, 74 사·분기) → `scripts/validate_kics_rate_sensitivity.py` 신규 구현. 정본 `docs/agents/kics-rate-sensitivity-spec.md` §5.

- **RS1_RATIO_IDENTITY** (RED): (사,분기,경과조치)·충격컬럼별 `비율≈금액/기준금액×100`, tol max(0.5%p, 0.5%·비율). → **0 RED** (705 컬럼 전수 통과).
- **RS2_BASE_ANCHOR** (RED): 적용전 base vs kics_disclosure item1/14/27, tol 금액 2억/비율 0.5%p. → **0 RED** + KR0011 DB손해 2025.2Q 3 measure documented exception(별도/연결 basis, `RS2_EXCEPTIONS`).
- **RS3_DIRECTION_SANITY** (YELLOW): 생보 −100bp 비율 상승(역방향) 28건 — ALM상 정상 가능, 플래그만.
- **RS4_COVERAGE_CENSUS** (YELLOW): **회사 cadence 인식**(1Q/3Q 보유 이력 없으면 반기공시 → 1Q/3Q 부재 정상) → 손보 1Q/3Q 과탐 40→**1**(코리안리 2025.2Q hole).

**gate RED=0.** 룰표 `claude-agent-validation.md` §1.1 등재. 결과 `data/_derived/kics_rate_sensitivity_validation.json`. inbox owner/parser 2건 resolved. (consolidate_inbox 핸들러 배선은 RED 발생 시 후속 — 06-12(b)에서 선배선.)

## 2026-06-09 (d) — 시장위험 Phase-2 적재 재검증 통과 (RESOLVED)

parser Phase-2(PDF 직접추출, +150행 → 14,394) 재검증. `run_validation`:
- **게이트 RED=2**(KB손해 KR0010 rule2 OCR, KICS-IMG; **신규 RED 0**). 통과.
- `19_market` GREEN 163→**185** / SKIP 221→199. `36_irr` GREEN 42→**47** / YELLOW 17→23 / SKIP 314.
- 교보(KR0073) 전치표 5분기 스폿: derived vs item36 diff 0.1~2.8%(tol 5% 이내, YELLOW=정당).
- 잔여 SKIP 정당: 19_market 구조적 ~100(삼성화재·삼성생명·현대·한화생명 PDF 비공시) / 36_irr Q1·Q3 ~85(시나리오표 원천부재) / IRR 직접형 15(별도 schema 보류). ⚠️ 이 "정당" 결론은 2026-06-12(a)에서 OVERTURN(분절표·라벨변형 = 파서 갭).

inbox `phase2_loaded` **resolved**. **V3 시장위험 검증 한 사이클 완결**: 룰 구현 → 골든 → 1차적재 → 결손census → Phase-2 PDF추출 → 재검증 RED 0. 추가 적재 시 동일 게이트 재실행.

## 2026-06-09 (c) — 시장위험 item36–46 1차 적재 검증 통과 (RED 0)

parser가 item36–46 1차 적재 → `validate_kics_disclosure.py` (19_market/36_irr 활성) 재실행:
- **19_market: 163 GREEN / 221 SKIP / 0 RED**
- **36_irr: 42 GREEN / 17 YELLOW / 325 SKIP / 0 RED**
- 게이트 RED=2 불변(기존 KR0010 OCR).

**단위 정합 확인** (앞 (b)의 회신 요청 해결): item36–40을 억원(세부표 백만원 ÷100) 적재한 게 맞음 — 19_market GREEN 163건이 item19(억원)와 일치. YELLOW 17(36_irr)은 0.0~3.4% 미세편차(`classify_diff`). 게이트 무관. SKIP은 미적재 분기 — parser 적재 계속 시 자동 GREEN. parser inbox 회신: `inbox/parser/20260609T0300Z__validation__MULTI_ALL__market_risk_loaded_pass.md`.

## 2026-06-09 (b) — V3 시장위험 룰 19_market + 36_irr 구현 (8_life 복제)

parser inbox(`market_risk_rule`, `market_irr_rules_19_36`) 요청 → `src/solvency/validation/kics_json_rules.py`에 2룰 구현. 정본: `docs/agents/kics-market-risk-decomposition.md`.

- **`19_market`**: `item19 = sqrt(V'·M·V)`, V=[36–40](금리·주식·부동산·외환·자산집중). `MARKET_M` 5×5(대각1.0/외환-주식 −0.25/자산집중 행열 0/그외 0.25). `_diversified_sqrt` 재사용. **부분결측 허용**(없는 하위=0; item19 또는 36–40 전부 결측 → SKIP). dynamic tol `max(eff_tol, 5%·expected)`, IMAGE_OCR 10.0 승계.
- **`36_irr`**: `item36 = √[max(R상승,R하락)² + max(R평탄,R경사)²] + R평균회귀`. R=base(41)−시나리오순자산(43/44/45/46), 평균회귀=41−42(signed). 41–46 중 결측 → SKIP.

**골든 3/3 정확 일치**: 19_market 흥국 FY2023_Q1 sqrt(V'MV)=813,201백만=8,132억(=item19) / 36_irr 흥국 157,128(공시 157,127) / 현대 322,767(공시 일치).

**상태**: item36–46 적재가 parser 진행 중 → 신규 2룰 **전사 SKIP**(게이트 미반영). RED=2 불변(회귀 없음). 적재 후 자동 활성. 단위: 룰은 item36–40을 억원(=item19 동일단위) 가정 — parser 적재 단위 회신 대기. inbox 2건 answered.

## 2026-06-09 (a) — consolidator 스크립트화 (mechanical=script, judgment=agent)

운영 개선 #2: validator JSON → inbox 메시지 변환을 에이전트/수동 → **스크립트** [`scripts/consolidate_inbox.py`](../scripts/consolidate_inbox.py)로.

- **왜**: smoke-test에서 emit(consolidator)·eval을 에이전트로 돌리니 1 finding에 208k 토큰. 변환은 기계적이라 에이전트 낭비. 원칙 **에이전트=판단·신규성, 스크립트=기계** 적용.
- **consolidate_inbox.py**: continuity validator(`csm_continuity_validation.json`) findings → `inbox/parser/` reparse 메시지(값 시계열 + 내부 closing-identity precompute 포함). **idempotent** — `parser/`·`_resolved/`에 같은 (회사·기간·토픽) 있으면 skip. 신규 validator는 `VALIDATORS` 리스트에 핸들러 추가. waterfall must_reparse 버킷은 당시 비어 미적용(항목 생기면 추가 — untested 코드 안 씀). → 06-12(b)에서 RS/waterfall 핸들러 선배선.
- **루프**: validator 실행 → `python scripts/consolidate_inbox.py` → 사람이 "inbox 확인해라". (driver 상설화는 안 함 — 사람 킥으로 충분, owner 결정.)
- **배선**: `inbox/README.md` "consolidator 향후 작업" → 스크립트 명시; validation 프롬프트 §3.0 route 분류를 mechanical(script)/judgment(agent)로 분리.
- **inbox 정리**: parser fix로 해결된 3건(흥국 FY2023·코리안 FY2024·코리안 2024.1Q) + 스모크 데모 1건 → `_resolved/`. `parser/`에 live finding 9개만 남김. 폐기된 probe `_seed_continuity_inbox.py` 제거.

## 2026-06-09 — V4 QOQ_DELTA_WARN 구현 (시계열 anomaly) + parser inbox

V4 `QOQ_DELTA_WARN` 소비자 코드 구현 (`validate_master_tables.py` 4번). spec(`config/qoq_thresholds.yaml`)의 CSM 항목 대상:
- 누적 항목(신계약/이자부리/상각) → **YoY**(전년 동기 YTD 대비). net-quarterly QoQ는 분기 계절성으로 노이즈 폭발(645건) → YoY로 계절성 상쇄.
- 시점 항목(기말 CSM) → QoQ. floor 50억(작은 분모 % 폭발 제거).
- **PL 손익(보험손익/투자손익/당기순이익) 제외**: 시장·금리 민감 본질적 고변동 + spec items 미등록. (임의 추가했다가 590건 노이즈 → 철회.)
- YELLOW(다운스트림 차단 안 함). 전체 → `data/_derived/qoq_warn.json` (sign_flip 플래그 포함).

**결과**: 193건 YELLOW (신계약 69 / 이자부리 59 / 상각 51 / 기말 14). 대부분 사업변동. **진짜 데이터 의심 = 이자부리 부호반전 3건** (양수→음수): 동양 2025.4Q(1,134→−2,140)·교보 2025.3Q(3,242→−5,290)·코리안리 2025.2Q(318→−116).

→ parser inbox: `inbox/parser/20260609T0200Z__validation__MULTI_2025__qoq_interest_signflip.md` (route: blind_spot, 이자부리 부호 raw 확인 요청).

**교훈**: QoQ anomaly는 임계·기준(net/YoY/raw) 선택이 신호품질을 좌우. flow는 YoY, stock은 QoQ, 고변동 손익은 제외. 부호반전이 단순 %급변보다 강한 데이터-오류 신호.

## 2026-06-08 — MASTER_COVERAGE 룰 신설 (hole을 SKIP으로 숨기던 사각지대 보강)

**검증 결함 인정**: closing/pl_bridge/crosscheck가 항목 None을 전부 SKIP 처리 → 거대한 skip(pl_bridge 456 / crosscheck 227) 뒤에 "있어야 하는데 없는" 데이터(hole)가 숨어 있었음. parser census(WRONG vs HOLE 분리)가 먼저 짚음 — validation이 했어야 할 일.

신규 룰 `MASTER_COVERAGE` (`validate_master_tables.py` 0번): active 회사(핵심항목 ≥7분기)의 빈 분기 = hole. **2024+ = real hole**, 2023 = known(사이트 비노출), <7분기 = structural(외국계·소형 미공시, 제외).

**검출**: real hole(2024+) **4건** / 2023 known 40 / struct 18.
- **미래에셋생명 CSM 2025.2Q·3Q·2026.1Q** — `CSM상각` None (2025.1Q는 −483.6 있음). closing identity가 skip하던 것.
- **롯데손해 PL 2025.2Q** — `생명장기손익` None (1Q·3Q는 있음). pl_bridge가 skip하던 것.
→ **parser 데이터 채움 대상**. 둘 다 절댓값 검증을 통과한 게 아니라 *검증 자체를 skip*당한 케이스.

검증 철학 갱신: "값이 틀린 것(WRONG)"뿐 아니라 **"값이 없는 것(HOLE/coverage gap)"**도 1급 검증 대상. skip은 침묵이 아니라 분류돼야 함.

## 2026-06-08 — 빌드→검증 통합 (build_root_masters 자동 선행)

`validate_master_tables.py`가 검증 전 `build_root_masters.py`를 자동 선행(idempotent). 빌드 누락으로 "고쳤는데 검증에 안 보임" 문제 구조적 차단(아래 06-07(h) 교훈). `--no-build`로 끔. 회귀 명령: `python scripts/validate_master_tables.py` (빌드+검증 한 방).

## 2026-06-07 (h) — 흥국 해소 (빌드 누락이 원인) + 빌드 체인 교훈

흥국화재 "고쳤다"는데 3번 재검증해도 루트 `CSM_waterfall.json`에 변화 0 → **빌드 한 단계 누락**. 체인: `csm_waterfall_master_diag.json`(소스) → `build_root_masters.py` → 루트 `CSM_waterfall.json`. parser가 **diag는 22:13에 제대로 고쳤는데** **루트는 21:31 옛것** — `build_root_masters.py`를 안 돌려 미반영. validation이 빌드 실행 → 루트 갱신 → **흥국 완전 해소** (복붙 6→0 / spike 4→1 / cont 21→14).

**⚠️ 운영 교훈 (핸드오프 필수)**: parser가 소스(diag/viz)를 고쳐도 **`build_root_masters.py` 재실행 전엔 루트 마스터에 반영 안 됨**. mtime 비교(소스 > 루트)로 빌드 누락 탐지 가능.

**빌드가 드러낸 새 건**: 롯데손해 2025.4Q wf CSM상각 −980(거의 0, 이상치) → crosscheck +99.5% RED. 롯데 FY25 양식 이슈(V7)와 연관 의심 → parser.

## 2026-06-07 (g) — CSM_PLAUSIBILITY 룰 신설 (closing identity 사각지대)

사용자가 흥국화재 2025.4Q 기말 CSM이 **34.1억**(직전 26,693억)으로 비정상 폭락한 걸 지적. closing identity는 **내부 산술 합산만** 검증 → 가정조정(−28,929.9억)이 폭락을 흡수해 closing이 우연히 닫혀 통과(0F). **절댓값 plausibility 검증 부재가 validation 갭**.

신규 룰 `CSM_PLAUSIBILITY` (`scripts/validate_master_tables.py` 1b):
- **복붙(dup)**: 같은 회사 내 서로 다른 분기의 기말 CSM이 소수점까지 동일 → 복붙 의심.
- **기말 QoQ 폭변(spike)**: 기말 CSM `|ΔQoQ| > 50%`.
- **연속성(cont)**: `FY[t] 각 분기 기초 CSM = FY[t-1].4Q 기말`. tol max(0.5%·|전년말|, 2억). 2023은 SKIP. — 사용자 지적으로 추가, 가장 근본적인 sanity.

**연속성 검출 21건**:
- 🔴 진짜 오류: **메트라이프 2025.4Q 기초 48,134 = 2024말 24,067 ×2 (이중계상, KB라이프형)**, 케이디비생명 2025.1~4Q 기초 복붙, 흥국화재 2025.2Q·3Q 기초 복붙.
- 🟡 회색지대 (IFRS17 기초 재작성 가능): 삼성생명 2024 Δ−1,452·신한라이프·메리츠·에이비엘·푸본 작은 Δ; 교보(±2,905/+5,659)·KB라이프(+1,622)는 parser 확인.
- severity 권고: 배수/큰 Δ = RED, 작은 Δ = YELLOW.

**dup/spike 검출**: 6 dup + 4 spike, 케이디비생명·흥국화재 집중.
→ **parser 전달 대상**: 케이디비생명·흥국화재 2025 CSM_waterfall 재추출 + 메트라이프 2025.4Q 기초 2배. closing 0F였어도 절댓값이 틀린 케이스.

## 2026-06-07 (f) — DB손해·KB손해 별도/연결 fix → PL_BRIDGE 31F→16F

parser가 별도/연결 LOB 레그 fix를 DB손해·KB손해로 확장 → **2024+ 보험손익 fail 10건 완전 해소** (DB손해 5 + KB손해 5). 진단(DB=ΣLOB 결손 / KB=ΣLOB 과대, LOB 내부는 정합)이 정확히 별도/연결 레그 오선택이었음.

**PL_BRIDGE 31F → 16F**. 잔여: 2023 분기 11건(사이트 비노출) + 2024+ 5건(KB라이프 2024.1Q +1,136 / 악사손해 2024.4Q +3,483 / 흥국화재 2025.1Q −714·2025.4Q +1,684·2026.1Q +968).

**dual-form의 정당성 (사용자 확인 2026-06-07)**: 보험손익은 통상 `종목별 합 − 기타사업비`(adj)지만 일부 회사·분기(흥국 2024.4Q, KB 등)는 종목별 합산에 기타사업비가 이미 녹아있어 bare(`= ΣLOB`)로 닫힘. dual-form은 이 케이스를 통과시키려는 의도된 설계 → bare로만 통과하는 분기는 정상, flag 안 함. (앞서 "숨은 275억 LOB 결손/dual-form 허점" 진단·"회사별 form 고정 flag" 제안 철회.) 단 한화손보→삼성화재 LOB 별도/연결 교훈(§1.5)은 유효 — 과잉진단 금지.

## 2026-06-07 (e) — 보험손익 잔차 = LOB 별도/연결 레그 오선택 (진단 가이드 정정)

삼성화재 2026.1Q +2,067, 한화손보 2025.2~4Q를 "기타영업수익 누락"으로 진단했으나 **2건 연속 오진**. parser FS-API 검증 결과 진짜 원인 = **ΣLOB 별도/연결 레그 오선택**:
- 별도(OFS) 기준 회사는 FS-API상 **기타영업수익 구조적 0**.
- parser `pmin`(최소합계=별도) 휴리스틱이 **재보험 레그에서 뒤집힘**(연결이 그룹내부 재보험 상계) → 기준 불일치 → ΣLOB 결손.
- 분기마다 별도/연결 대소가 달라 같은 회사도 일부 분기만 fail.

parser fix(별도 보험수익 anchor + cost/재보험 레그 same-block `first_from`) → **삼성화재 2026.1Q + 한화손보 2025 둘 다 해소**. pl_bridge **36F → 31F**. 진단 가이드 §1.5에 박음: 보험손익 잔차는 "기타영업수익 누락"이 아니라 **LOB 별도/연결 기준 일관성부터 의심**.

## 2026-06-07 (d) — CSM_CROSSCHECK 진짜 2건 해소 → 0F

진짜 의심 2건이 서로 다른 원인이었음 ("재보험 혼입" 가설은 둘 다 빗나감):
- **KB라이프 2023.4Q — wf 버그 (parser fix)**: 사업결합(KB생명+푸르덴셜)으로 기초가 2줄. 전기 블록 기말이 사업결합 전 기초와 같아 값연속성 검사 통과 → wf가 당기 블록(−283,905)에 전기 블록(−146,769)을 합산해 **정확히 2배**(−430,674). closing identity는 비례 2배라 우연 통과, crosscheck만 잡음. parser `_is_prior_header()`(`['구분','전기']`) 추가 → KB라이프 13분기 OK, 상각 −2,839.1억(=pl ✓).
- **코리안리 2025.4Q — validation 룰 스코프 버그 (validation fix)**: 파서 정확. 재보험사 PL은 발행계약을 `원수CSM상각(4) + 수재CSM상각(4-1)`로 분리(41,154+32,210=73,364=wf 상각). crosscheck 룰이 PL 수재(4-1)를 빼먹어 false-positive → `p = 원수CSM상각 + (수재CSM상각 or 0)`로 수정(출재 9-1 제외). §1.2 반영.

**결과**: CSM_CROSSCHECK **66P/2M/2F → 68P/2M/0F**. CSM_waterfall 도메인(closing 0F + crosscheck 0F) 완전 정합. 잔여 MINOR 2건(에이비엘 6.9%·흥국화재 6.4%)은 경고만.

## 2026-06-07 (c) — CSM_CROSSCHECK tol 3단계 정책

`CSM_CROSSCHECK`는 **서로 다른 DART 표**(PL 보험수익 구성 vs CSM 변동표) cross 비교라 표간 반올림·집계 차이로 수% 편차가 구조적. **3단계 tol** 도입 (§1.2):
- **OK**: `|s| ≤ max(5%·|pl|, 300백만)` · **MINOR** (경고, pass): `5% < |s| ≤ 10%` · **RED**: `|s| > 10%` → parser loopback.

결과: crosscheck **9F → 66P / 2M / 2F**. 진짜 불일치(KB라이프 51.7%·코리안리 78.3%)만 RED, 경계 7건 흡수. 진짜 2건과 경계(최대 6.9%) 갭이 51%+로 커서 10% 임계 안전.

## 2026-06-07 (b) — CSM_waterfall closing 완전 해소 (parser 재추출 후 재검증)

parser가 CSM_waterfall 측정요소 변동표 재추출 → 재검증 (`scripts/validate_master_tables.py`):
- **CLOSING_IDENTITY: 40F → 0F** (299P / 0F / 6S). 23사 × 13분기 전부 `기초+신계약+이자+가정+상각 = 기말` 정합. 🎯
- **CSM_CROSSCHECK: 20F → 9F** (61P / 9F / 224S). 잔여 9건은 (c) tol 3단계로 정리(진짜 의심 2건 KB라이프·코리안리 + 경계 7건).

## 2026-06-07 — V8 마스터테이블 검증 소비자 코드 첫 실행 + 룰 정식화

사용자가 (거의) 전사·전분기 마스터테이블 구축 완료 → V8 소비자 코드 `scripts/validate_master_tables.py` 작성·실행. 입력: `pl_breakdown_master.json` (백만원, 32사×13분기) + `CSM_waterfall.json` (억원, 23사×13분기).

**3개 룰 첫 실행**: CLOSING_IDENTITY 218P/40F/41S · PL_BRIDGE(8단) 2023P/36F/469S · CSM_CROSSCHECK 33P/20F/190S.

**룰 정식화 (오탐 제거)**:
- **보험손익 dual-form**: `보험손익 = ΣLOB`(손보) 또는 `ΣLOB + 기타영업수익 − 기타사업비용`(삼성화재 등). 둘 중 하나 닫히면 PASS → 손보 bare-close 오탐 ~19건 해소.
- **영업이익 abs floor 200→600백만**: 0근처 회사(KDB 등) 과민 방지.
- **CSM_CROSSCHECK 4Q-only**: pl·wf 모두 YTD 누적 → 1~3Q 분기배분 노이즈 제거. 136F→20F.

**parser 1차 수정 반영**: item16 음수 7건 abs 정규화, item19 account_nm fallback 277셀 포착, item17 net 통일.

**남은 fail**: CSM_waterfall 도메인 60건(closing 40F + crosscheck 20F) = parser 재추출 · PL 잔여 36F(대부분 known FY2023 HTML fallback + 한화손해 dual 미닫힘).

회귀 명령: `python scripts/validate_master_tables.py`.

---

## Archive (pre-2026-06)

> 1줄 요약. 전문은 git log/blame. dead-end/폐기 근거는 프롬프트에 보존(SEGMENT cross-source 폐기·PL_BRIDGE §1.5 / 메리츠 보종 영구SKIP §1.2 / off-year→continuity §3.0 / dual-form 과잉진단 금지 §1.5 / 빌드체인 gotcha §3.0). K-ICS RED 진행 + 분기별 batch 원문은 `docs/claude-changelog.md` Historical archive(2026-05-24/25, 2026-04-26~28).

- 2026-06-01 (밤) — SEGMENT cross-source 폐기 + PL_BRIDGE_DART_INTERNAL 신설(§1.5, DART 자기완결 10등식, 삼성화재 2025.4Q PASS) → V8
- 2026-06-01 (밤 b) — 메리츠 CSM waterfall: breakdown 영구 SKIP + CSM_AMORT cross-table 신설
- 2026-06-01 (밤 c) — 통합 마스터테이블 입력 계약 + CSM_CROSSCHECK 확장
- 2026-06-01 (저녁) — 🚨 history 재빌드 off-by-one-year 회귀 발견 + check 도구 cohort 가드
- 2026-06-01 — V7 history-wide check 도구(`check_nb_csm_history.py`, 13Q×9사) + systemic 이슈 3건 발견(2025.2Q cohort-wide / DB 2025.2-4Q 부호 반전 / 미래에셋 ↑↓ 교대); FY24 widespread 6/7 OK(롯데 FY25 의존); 한화 V2 fallback retire 가능
- 2026-06-01 — V7 6/7 OK 회복 (parser 별도·당기 disambiguation + 소계 이중계상 fix)
- 2026-05-31 — V7 `NB_CSM_DART_VS_IR_ANNUAL_SUM` 룰 + convention-aware check 도구
- 2026-05-31 — NB CSM multiple validator: period-aware + fallback flagging (V2), retry max 8→5
- 2026-05-31 — QoQ threshold registry v1 (`config/qoq_thresholds.yaml`, V4 spec)
- 2026-05-31 — DART ↔ IR cross-source 3개 룰 추가 + IR-side input 계약 §1.4 (V1 spec)
- 2026-05-30 — Validation prompt 초안 (R1–R10, IFRS17 CSM 룰셋, `QOQ_DELTA_WARN`, retry loop max=5)
- 2026-05-29 — Plausibility gate (`MAX_PLAUSIBLE_MULTIPLE=60`) + Samsung Life 사망 misparse fix
- 2026-05-25 — K-ICS rules 9 + 10 추가 + RED reduction 419→2 (KR0010 OCR 잔여) + unit-hint mismatch auto-detect + Tier-2 utilization reconcile
- 2026-05-24 — K-ICS JSON validation rules doc + pipeline gate; KICS-VALIDATE harness; R7 matrix fix
- 2026-04-26 → 2026-04-28 — Foundational validation

세부 K-ICS RED 진행 + 분기별 batch 원문은 [`docs/claude-changelog.md`](claude-changelog.md) Historical archive에 압축 보존. 본 파일은 validation-relevant 분리본.
