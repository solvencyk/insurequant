---
from: owner
to: validation
created: 20260612T0900Z
status: open
route: backlog
company: ALL
period: ALL
rule: BACKLOG_DIGEST
iter: 1
---

## 미결 (sender 작성)

**owner 백로그 다이제스트 (2026-06-12 전수 점검).** 상세는 `TODO_validation.md` 해당 ID.

### 🔴 즉시
1. **inbox 드레인 — open 1건 방치 중**: `20260610T1700Z__parser__MULTI__csm_owner_review_fixes.md`.
   V9 작업(WFY/ZAMORT/ZLEG, 2026-06-11)이 요청사항 대부분을 이미 커버한 걸로 보임 — 대조 후 `## 답변`
   작성하고 종결할 것. 특히 ① 롯데 FY2023 continuity verdict 폐기(재진술 아님→구공시 오채택) ② continuity
   제외 = **신한이지(KR0051) 1사만** 확인 ③ AMORT_ZERO 요청 = ZAMORT로 충족 여부 ④ 미래에셋 경계 drift
   2건(2023.2Q Δ2.25억 / 2025.2Q Δ6.5억) tol/예외 처리.
2. **consolidate_inbox.py `VALIDATORS` 배선 잔여**: RS1–4(금리민감도) 핸들러 + waterfall validator
   (`must_reparse` 버킷) 핸들러. RS 답변에서 "후속(⏳)"로 미룬 항목 — RED 발생 전에 배선해 둘 것.

### 🟠 parser 작업 후 재검증 (트리거 대기)
3. parser 신규-1(시장하위 backfill) 적재 후 `19_market` 재검증 + RS4 census 갱신.
4. parser 신규-2(생보 item14후 적재) 후 **8_post/R7후 검증**: `(2후+3후)/14후 ≈ item27후` 전수.
5. V7: history 빌더 off-by-one 회귀 수정 후 `check_nb_csm_history.py` 재실행 (systemic 3건 재확인 보류 중).

### 🟠 기존 잔여
6. V2: 한화 fallback retire 재검증(`validate_nb_csm_multiple.py` → `fallback_used=false` 확인) +
   삼성화재 IR annual benchmark 보강.
7. V9 잔여: 교보생명 cont 3건(2024.3Q/4Q −2,905 · 2026.1Q +5,659) / 케이디비 spike(2024.1Q→2Q +58%) /
   저배수 4사 원인조사(교보 6.61 · 한화생명 9.84 · 교보플래닛 2.0 · 처브 2.4 — 분자 scope 의심).
8. **verify_parser_change 상설 하네스** (2026-06-09 세션 #4 pending): 추출기 변경 시 rebuild-diff
   (blast-radius) + validator 재실행을 한 명령으로. 손으로 짰던 절차의 스크립트화.
9. V4: QoQ yaml loader 본구현 (`config/qoq_thresholds.yaml` → validator hook).

### 🟢 housekeeping
10. `_resolved/20260609T0000Z__validation__KR0083_2026.1Q__continuity.md` — status가 `open`인 채
    archive돼 있음 → resolved로 정정. answered 상태로 남은 구 스레드들(market_risk 2건 등)도 일괄 종결 검토.
11. V6: KR0010/KR0079 OCR RED 2건 = owner 수기 대기 (documented exception 유지, 액션 없음).

## 답변 (recipient 작성 — 처리 후)

### 2026-06-12 진행 (이번 세션) — 즉시 가능분 처리

**🔴 #1 inbox 드레인** — ✅ 완료(전 세션). `csm_owner_review_fixes` 4점 풀런 대조 후 `## 답변`+resolved 이관. 롯데 verdict 폐기·제외=신한이지 1사·ZAMORT(AMORT_ZERO+양끝 양수 가드)·미래에셋 drift no-RED 전부 확인.

**🔴 #2 consolidate_inbox VALIDATORS 배선** — ✅ 완료. `_rate_sensitivity_findings`(RS1/RS2_base RED) + `_waterfall_findings`(must_reparse 버킷) 추가, `VALIDATORS=[continuity, rate_sensitivity, waterfall]`. TEMPLATE을 `{section}`/`{request}`로 일반화(continuity 패턴 보존). 세 버킷 현재 0건 = 선배선(RED 발생 시 자동 라우팅).
- 검증 3중: (a) `python scripts/consolidate_inbox.py` → findings=9(전부 기존 continuity, skip), 신규 0발신·크래시 없음. (b) finding↔TEMPLATE 플레이스홀더 계약 테스트 PASS. (c) 합성 RED end-to-end — RS1(DB손해→KR0011)·RS2(미래에셋생명→KR0079)·WF(라이나→KR0074/FY2024) 추출키·name→code·period유도 정상.

**🟠 #6 V2 한화 fallback retire** — ✅ 확인. `validate_nb_csm_multiple.py` 재실행: **한화생명 fallback_used=False = retire 확정.** 단 삼성화재(2025.3Q, computed 17.54 vs IR 14.1, rel_diff 0.244 = tol 0.25 **턱밑**)·현대해상(2025.1H, 16.16 vs 18.9)은 **aligned FY2024 행 실패** → period-mismatch fallback으로만 통과(validator가 "tolerance loophole may mask upstream bug" 경고). **삼성화재 IR annual benchmark 보강 = 미결**: FY2024 연간 IR 분모 소싱 필요(기계작업 아님). → 별건 추적.

**🟢 #10 housekeeping** — ✅ 완료. KR0083 status open→resolved(전세션). inbox/validation 큐 5건 `_resolved/` 이관: RS 2건(clean resolved) + **market 3건은 정정 후 이관**. market_coverage_phase2_loaded의 "잔여 SKIP 정당(삼성화재·삼성생명·현대·한화 PDF 비공시)" 결론을 **OVERTURN** 기록(하나손해 image-split·삼성생명 라벨변형 = 실공시 확인, 19_market SKIP→RED 승격·census 추가·재추출 발주로 연결). 검토 결과 "일괄 clean 종결" 아닌 "정정 후 종결"이 맞다고 판단.

### 미처리(파서 의존 또는 다단계 — 다음 우선순위 후보)
- 🟠 #3/#4: parser backfill(시장하위 36-40 / 생보 item14후) 적재 **대기 중**(어제 market_subrisk inbox 발주). 적재되면 19_market·8_post/R7후 재검증.
- 🟠 #5: V7 history 빌더 off-by-one **회귀** 수정 → check_nb_csm_history.py 재실행(systemic 3건). ← 회귀라 다음 1순위 후보.
- 🟠 #6잔여: 삼성화재 FY2024 IR annual benchmark 소싱.
- 🟠 #7: V9 잔여(교보 cont 3 / 케이디비 spike / 저배수 4사 분자 scope).
- 🟠 #8 verify_parser_change 상설 하네스 / #9 V4 QoQ yaml loader = 신규 스크립트(다단계).
- 🟢 #11 OCR RED 2건 = owner 수기 대기, 액션 없음.

digest는 위 미처리분 남아 **open 유지**.

### 2026-06-14 추가 진행 (파서 백필 완료분 종결)

- **🟠 #3/#4 = ✅ 완료**: parser가 시장하위 36-40 회수(146 all-five 영속) + 생보 item14후 적재 완료(changelog 06-14). 재검증: `19_market` 게이트 정상작동(짝수 결측만 RED), **rule 8_post = GREEN 442/RED 0**((2후+3후)/14후≈item27후 25/25 일치). 둘 다 종결.
- **🟢 신규**: `_scan_breakdown_presence` clean-cell 수정(삼성생명 odd-Q false RED 제거) + SENSITIVITY_UNIT_SANITY 룰 신설(owner 0712Z claim2). 별도 owner 메시지 답변 참조.
- **잔여 open**: #5 V7 history off-by-one 회귀 / #6잔여 삼성화재 FY2024 IR annual benchmark / #7 V9 저배수 4사·교보 cont / #8 verify_parser_change 하네스 / #9 V4 QoQ yaml loader. (파서/다단계 의존 — 다음 우선순위.)

### 2026-06-16 진행 — #5 V7 history off-by-one 재확인 완료 (systemic-3 근본원인 확정)

**#5 = ✅ 재확인 완료**(off-by-one 해소 확인 + systemic-3 = 실재·아티팩트 아님).
- **off-by-one-year 회귀 = FIXED**: 현 IR series(`data/ir/series/`)는 Q1 YTD-reset 정합(삼성화재 6782.7→14426→26068→34995, 2024.1Q 8855.5로 리셋 = 1년 시프트면 불가능). 06-08 stale check(10:35)와 재실행 ir_eok·flag 완전 동일 = 시프트 흔적 0.
- **복원 `scripts/check_nb_csm_history.py`**: 사라진 ad-hoc 도구를 self-contained로 복원(컨벤션을 series 메타에서 도출: singleQ field / units "YTD" / per-Q default). DART per-Q delta가 stale matrix와 정확 일치(faithful). `data/_derived/nb_csm_history_check.json` 현행 갱신. exit 2 if OVER/UNDER.
- **systemic-3 근본원인 = DART CSM_waterfall partial/no_csm_block 추출**(정렬 아님): 롯데 2025.2Q status=partial→NB_YTD=0→delta −1098.5(음수 NB 불가능); 미래에셋 2025.2Q/3Q partial→collapse-then-catchup spike(=‟↑↓ 교대"); 2025.2Q cohort-wide=동일. DB 2025.2-4Q 부호반전은 현재 DB DART 부재로 재현 안 됨(현상 롯데로 이동). 삼성생명 2025.2Q OVER(+26%)는 status=ok=진짜 DART↔IR 차이(별건).
- **라우팅**: parser/ifrs17 `inbox/parser/20260616T0230Z__validation__MULTI__nb_csm_partial_extract_corrupts_history.md`(partial 재추출 + 전사 sweep + 삼성생명 별건).
- **잔여 open**: #6잔여 삼성화재 FY2024 IR benchmark / #7 V9 / #8 하네스 / #9 QoQ yaml. (#5는 검증측 완료, parser 재추출 트리거 대기.)

### 2026-06-16 진행 — #6/#7/#8/#9 (4-에이전트 Workflow 병렬 + 통합)

**#6 = ✅ 삼성화재 RESOLVED / 🔴 현대해상 owner·downloader.** `validate_nb_csm_multiple.py`에 FY2024 aligned anchor 로더 추가(`load_fy2024_ir_anchors` — IR series 2024.4Q.multiple_derived_ytd) + 삼성화재 PREFERRED_SCOPE에 monthly_avg_from_ytd. **삼성화재 fallback retired**: computed 14.76 vs IR 15.16 rel 0.026, period_aligned=True, fallback_used=False(경고 해소). **fallback_pass 2→1**. 현대해상은 **in-repo에 FY2024 ANNUAL IR multiple 부재**(현대 IR=1H/2H cadence, FY-annual 미공시 가능) → fallback(2025.2Q=18.9) 잔존, owner 결정(영구 fallback or downloader가 현대 IR FY2024 배수 fetch). pytest 110.

**#7 = ✅ 조사완료 (parser-fix 0건; 전부 source-faithful/documented/frozen) + 🔧 validator 이중계상 수정.** raw 대조로 closing identity 전부 EXACT → 산술오류 없음, break는 boundary-level:
  - 교보 2024.3Q/4Q Δ−2905 = **WFY-documented 재작성을 CONT가 이중계상**(WFY엔 면제, CONT엔 면제 split 부재) → **수정**: `validate_master_tables.py`에 CONT도 RESTATEMENT_EXCEPTIONS(=기존 WFY set) 공유, documented는 CONTEX(보고만·게이트 제외). **cont 15→12(+3EXC: 교보 2024×2 + KB라이프 2024.4Q)**. 미등록 boundary(교보 2026.1Q +5659 등)는 RED 유지 = 새 신호 가시.
  - **[정정 2026-06-16 — 오진 시인]** 교보 2026.1Q +5659 등 **5사 2026.1Q boundary = REAL 재작성 아님 = 파싱오류**. owner가 DART 원본 직접검증: 2026.1Q 기시 CSM = 직전 2025.4Q 기말과 동일(교보 65,110·메리츠 111,037·신한라이프 75,537·에이비엘 9,702·푸본현대 1,907.45). master에 엉뚱한 opening이 박힘. 내가 "self-closing identity 닫힘→source 충실"이라 한 건 오진(항등식은 opening 검증 불가). → downloader FY2026_Q1 raw 복원(`…restore_fy2026q1_dart_raw`) + parser/ifrs17 재추출(`…csm_2026q1_opening_misparse`) 발주. CONT RED 유지=정당. (케이디비 2024.2Q +58%는 별건=within-period 가정·경험조정 +2897 실적변동, 유지.)
  - 저배수 4사 = **scope 오류 아님**(backlog framing 정정): 교보 6.61/한화 9.84는 2026.1Q **Q1 계절적 저점 YTD**(한화 9.84는 오히려 IR-validated FY 7.6보다 높음=‟low" 오독), 교보플래닛 2.0·처브 2.4는 micro/digital 실제 저배수. 분자 전부 waterfall item2와 정확 일치.

**#8 = ✅ DONE.** `scripts/verify_parser_change.py` 신설(stdlib, UTF-8): snapshot/diff(blast-radius, kics는 (code,quarter,item) cell-diff)/validate(6검증기 일괄 exit+summary 표)/all. 자가검증 snapshot+diff clean, full `validate` 통합실행 확인(6검증기 정상 표출). 추출기 변경 전후 1커맨드 회귀.

**#9 = ✅ 이미 배선됨(no-op).** `config/qoq_thresholds.yaml`은 `validate_master_tables.py:84 yaml.safe_load`로 이미 로드 중 = backlog 항목이 stale. 변경 불요.

**남은 owner 결정**: (a) 현대해상 FY2024 IR benchmark 영구fallback vs fetch, (b) 교보 2026.1Q 등 2026.1Q boundary 점프(frozen raw) 문서화 예외 등록 여부 + FY2026_Q1 재취득. **#8/#9 종결, #6 삼성화재·#7 validator-fix 완료.**
