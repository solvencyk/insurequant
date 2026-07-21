---
from: owner
to: publishing
created: 20260620T0859Z
status: open
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

## 답변 (recipient 작성 — 처리 후)
