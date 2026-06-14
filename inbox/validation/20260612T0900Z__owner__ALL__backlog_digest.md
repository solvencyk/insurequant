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
