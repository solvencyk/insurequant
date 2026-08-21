---
from: owner
to: publishing
created: 20260620T0859Z
status: resolved
route: build_pipeline
company: MULTI
period: "-"
iter: 1
---

## 미결 (owner) — owner 수정 영속성: gold-overlay를 *모든* 마스터의 마지막 빌드 단계로 통일

**근본 비효율(2026-06-20 회고)**: owner 수정의 영속성 구조가 깨지기 쉬움 — xlsx(수식)↔JSON↔diag 왕복에서 **리빌드가 owner 수정을 클로버**(카카오 89행 재삽입·코리안리 −11817 재발 위험), openpyxl 재저장이 **수식 캐시 wipe**, sync gap. 이 한 부류에 메모리만 5개([[master_xlsx_review_loop]]·[[rebuild_master_xlsx]]·[[reference_kics_gold_reviewloop]]·[[project_master_xlsx_formula_cache]]·[[project_owner_confirmed_registry]]) = "더 기억"으로 못 푸는 **구조 문제**.

**요청 — gold-overlay 패턴을 단일 영속 레이어로 통일:**
1. K-ICS는 이미 `data/_gold/user_kics_cells.json`(+image fills)로 owner 수정을 보존하고 빌드 후 reconcile함. **PL/CSM도 동일하게**: owner의 모든 수정(현재 xlsx H열/sync 경유분 포함)을 `data/_gold/user_pl_cells.json`(가칭)에 **durable 적재**.
2. **`build_root_masters`(및 publishing master 조립)의 *마지막* 단계에서 gold 오버레이를 무조건 덮어쓰기** → 리빌드가 절대 owner 수정을 클로버 못 함. idempotent.
3. owner는 더는 **깨지기 쉬운 수식 xlsx를 정정용으로 직접 만질 필요 없음** — 정정은 gold로. xlsx는 read-only 검토 산출물로 강등(빌드물, untracked).
4. 오늘 만든 `data/_gold/user_pl_confirmed_cells.json`(skeptic suppress용)은 이 통합 gold의 씨앗 — 같은 폴더/규약으로 흡수하거나 병행.

**효과**: 클로버·캐시wipe·sync gap 3종 동시 근절. 위 메모리 5개 중 다수가 obsolete가 되어 정리 가능. **검증**: 임의 마스터 리빌드 후 gold 셀(코리안리 −11817 등)이 그대로 남는지 회귀 테스트.

분할: gold 적재 스키마/오버레이 apply는 publishing(master 조립 소유). diag 상류 반영이 필요한 추출 정정은 별개로 parser inbox 유지. 게이트/레지스트리 연동은 validation.

## 답변 (recipient 작성 — 처리 후) — 2026-08-20, owner 착수 승인 후 처리

**요청 4개 항목 처리 결과 (`71914c3`, 로컬 커밋 — main 배포 대상 아님, scripts/tests):**

1. **놀란 점**: 조사해보니 PL/CSM은 이미 `build_root_masters.py`의 `_apply_pl_overrides()`/
   `_apply_csm_overrides()`가 `build_pl()`/`build_csm()`의 마지막 단계에서 오버레이 파일을
   **무조건 UPSERT**하고 있었다 — 리빌드가 owner 수정을 못 덮어쓰는 구조 자체는 이미 있었다.
   다만 그 파일이 `data/dart/viz/pl_manual_overrides.json`/`csm_manual_overrides.json`으로
   K-ICS의 `data/_gold/` 관례 밖에 있었을 뿐. → `data/_gold/user_pl_cells.json` ·
   `data/_gold/user_csm_cells.json`으로 이전(`git mv`), `build_root_masters.py`·
   `emit_ifrs17_provenance.py` 경로 갱신.
2. **진짜 구멍**: `sync_owner_fills_to_json.py`(xlsx H열→JSON 동기화)가 오버레이를 안 거치고
   **루트 마스터 JSON에 직접** 써서, 그 위에 리빌드가 한 번이라도 돌면 `_additive_merge`가
   fresh SRC의 non-null 값을 승자로 쳐서 owner 수정이 조용히 사라지는 경로였다. PL/CSM 두
   시트는 이제 gold 오버레이 파일에 먼저 UPSERT(영속) + 현재 루트 JSON에도 즉시 반영(기존
   즉시성 유지) — 두 마리 다 잡음. **K-ICS 시트는 안 건드림**(이미 별도 gold 플로우
   `apply_user_kics_gold.py` 보유).
3. `user_pl_confirmed_cells.json`(skeptic suppress용)은 **병행**으로 남김 — 값 오버레이가 아니라
   "이 값 맞다고 확인됨" advisory 매칭이라 스키마가 근본적으로 다름(강제 흡수하면 두 개념이
   섞임). `data/_gold/`에 같이 있으니 폴더 통일 요구는 충족.
4. **회귀 테스트**: `tests/test_gold_overlay_survives_rebuild.py` 신설 — 실제 `build_root_masters`
   함수를 tmp_path로 격리해서(레포 실파일 안 건드림) gold 셀이 틀린 fresh SRC를 이기는지 +
   **두 번째 리빌드에도** 살아남는지(2026-08-14/15 사고와 정확히 같은 재현 조건) 검증. 3/3 pass.

**의도적으로 안 한 것**: `build_root_masters.py`의 `main()`/`build_pl()`/`build_csm()`를 실제
레포 파일에 대고 실행하지 않았다 — `inbox/_resolved/20260815T1130Z`에서 publishing이 동의한
"루트 마스터 빌더 직접 실행 금지" 원칙 유지. 검증은 격리 회귀 테스트로 대체.

**부수 발견 (제 작업과 무관, 손 안 댐)**: 커밋 직전 재확인한 게이트가 `RED=12`
(`[IFRS17_BS] BS_CENSUS_MISSING_ITEM`, 서울보증보험·카카오페이손해보험) — `IFRS17_BS.json`이
제 마지막 배포(5,686행) 이후 6,209행으로 또 늘어나 있었다. 이건 다른 세션의 진행 중 작업으로
보여 제 커밋에서 제외했다(gold-overlay 변경분만 정확히 스코프). 배포 판단은 그 세션 완료 후
별도로.

**부수 사고(경미, 데이터 무관)**: 커밋 시 `git add -A`를 안 썼는데도, 세션 시작 전부터 이미
staged 상태였던 무관한 archive 이동 8건(png 7개 + md 1개, 전부 순수 rename)이 같이 커밋됐다 —
`git commit`이 방금 add한 것뿐 아니라 index 전체를 커밋한다는 걸 또 놓쳤다. 내용 변경 없는
순수 rename이라 데이터 위험은 없지만, 커밋 경계가 안 깔끔해진 점은 밝혀둔다.

---

### 종결 (owner status-sweep, 2026-08-20)

71914c3로 PL/CSM 오버레이를 data/_gold/로 통일 + sync_owner_fills_to_json.py의 진짜 유실경로 차단. 오케스트레이터가 tests/test_gold_overlay_survives_rebuild.py 직접 실행 → 3 passed 확인, 구경로 코드참조 0건 확인.
