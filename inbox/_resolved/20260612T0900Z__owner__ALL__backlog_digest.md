---
from: owner
to: publishing
created: 20260612T0900Z
status: resolved
route: backlog
company: ALL
period: ALL
rule: BACKLOG_DIGEST
iter: 1
---

> **RESOLVED 2026-06-16 (publishing):** 모든 decision-free 항목 완료 — 🔴-1(rate-sens)·🔴-2(kics_disclosure 배포 dbbb096)·🔴-3(xlsx)·🟠-4/5(bubble)·🟠-6(V7 gate). 잔여 **🟡-7/8/9는 upstream-gated**(F17 Tier2=parser / F18 IR=parser·downloader / F13 재보험=downloader F8 / F4 v2=Cat C/D 리서치) — `TODO_publishing.md` "Open work"에 추적. 이 digest의 triage 목적 소진.

## 미결 (sender 작성)

**owner 백로그 다이제스트 (2026-06-12 전수 점검) — publishing inbox 신설 첫 메시지.**
상세는 `TODO_publishing.md` 해당 ID. (리마인드: push는 추천만, 실행은 사람.)

### 🔴 즉시 — 커밋 번들 추천 작성
1. **금리민감도 feature 일괄**: `kics_rate_sensitivity.json`(435행, RS게이트 RED=0) +
   `extract_kics_rate_sensitivity.py` + `validate_kics_rate_sensitivity.py` + diag/validation JSON +
   K-ICS.html 민감도 패널(designer 완료분) + 스펙 `docs/agents/kics-rate-sensitivity-spec.md`.
   feature 단위 커밋 메시지·파일 리스트 추천안 작성 → 사람 승인 대기.
2. **kics_disclosure.json 정정분**: KR0104 후레그 복사적재 정정 + KR0008 2025.3Q 후분해/item1후 오타
   정정 + `recalc_kics_derived.py` 공식수정 + item28후 62셀 재유도. 게이트 RED=2(기존 OCR만) 확인됨.
3. **`insurequant_master_tables.xlsx` 재생성 확인** (`python scripts/build_master_xlsx.py`) — 마스터
   JSON 갱신 시 필수 룰. 신규 `kics_rate_sensitivity` 시트 포함 여부 결정 포함.

### 🟠 착수 가능
4. **INDEX-BUBBLE-V2 4축 빌더**: X=당기순이익(net_income_breakdown.json, Tier1 28사 존재) ×
   Y=CSM잔액 × size=신계약CSM × color=배수(csm_bubble.json 존재). join 빌더 신규 → ECharts spec은
   designer 핸드오프.
5. **INDEX-IFRS17-BUBBLE 완성도**: 27/28 (코리안리 N/A) 데이터 파이프라인 점검.
6. **V7 gate enforcement** (validation→publishing 이관 항목): NB_CSM_DART_VS_IR RED 시 어셈블 차단
   로직이 publishing 플로우에 실제로 걸려있는지 확인.

### 🟡 대기 (선행조건)
7. F17 Tier2 LOB 어셈블 — parser F17 결정 대기. / F18 IR 통합 — parser `data/ir/<period>/parsed/` 대기.
8. F13 재보험 지표 — downloader F8(knia consumer) 대기.
9. F4 v2 — Cat C/D 리서치(자본성증권 carrying value 정의) 후 over/under_deduct 재정의.

## 답변 (recipient 작성 — 처리 후)

- [x] **🔴-1 금리민감도 feature 커밋 묶음** — 완료 (commit `f8bb6ff`, fix/csm-product-segmented-columns). 8파일(master+gold+diag/validation+추출/검증/gold스크립트+spec). RS게이트 RED=0 확인. K-ICS.html 드롭다운 helper는 designer 소관이라 제외(→designer manual_html_edit). 리포트: artifacts/publishing/ratesens_feature_20260614T073954Z.md. **push는 owner GO 대기.**
- [x] **🔴-2 kics_disclosure.json 정정분** — 배포 완료(2026-06-16 `dbbb096`). 정정분 + 예별 13Q 백필 포함, K-ICS 게이트 RED=24 전부 documented. origin/main 라이브.
- [x] **🔴-3 master xlsx 재생성** — 완료(2026-06-16, xlsx skill 채택 발주 `20260616T0043Z` 첫 적용). master JSON 2건 신규(kics_disclosure/rate_sensitivity) → `build_master_xlsx.py` 재생성, 7시트 한글 무결, CSM워터폴 1,926행 유지. untracked 빌드물이라 미배포.
- [x] **🟠-4 INDEX-BUBBLE-V2** — 폐기(완결). 버블맵은 3축으로 main 라이브 완결(X=신계약CSM·Y=NB배수·크기=기말CSM). 4축 재설계 불필요(owner 2026-06-14). TODO 정리 완료.
- [x] **🟠-5 INDEX-IFRS17-BUBBLE** — 완결(위와 동일 차트). IFRS17-CSM-BUBBLE 도 흡수 완결.
- [x] **🟠-6 V7 gate enforcement** — 조사 완료(2026-06-16). **결론: NB_CSM_DART_VS_IR RED는 publishing 어셈블을 차단하지 않음 — 전용 차단이 어디에도 미배선.** 3층 확인: (1) `build_root_masters.py` 검증게이트 전무(diag→마스터 무조건 빌드); (2) V7 도구 `check_nb_csm_widespread.py`·`check_nb_csm_history.py` **소스 둘 다 부재(.pyc만)**, 파이프라인 미호출, `validate_master_tables.py` 미포함, validation_report.json 0건; (3) publishing §3.1 게이트는 generic("validation subagent report summary.red==0→else BLOCKED")이라 V7가 그 리포트에 올라오면 이미 차단 가능. **판정: publishing 코드 갭 아님 = validation 측 배선 갭.** V7는 parser-loopback 설계 + V1으로 retire 예정이라 전용 게이트 신설 비권장. 갭은 validation inbox로 발주(`20260616T0100Z__publishing__MULTI__v7_gate_enforcement_findings`). publishing 무코드(체크리스트 1줄만).
- [ ] 🟡-7/8/9 — upstream 대기(미착수).
