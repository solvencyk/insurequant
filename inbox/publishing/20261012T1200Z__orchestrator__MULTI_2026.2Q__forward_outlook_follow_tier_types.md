---
from: orchestrator
to: publishing
created: 20261012T1200Z
status: open
route: fix
company: MULTI
period: 2026.2Q
iter: 1
---

## 미결 (sender 작성)
owner 지적(2026-10-12 채팅): 「그럼 그에 맞게 forward outlook 숫자들도 다 바뀌어야겠네? 예를 들어 한생은 기존에 기본자본비율이 steep 하게 내려온다고 가정했는데(원래는 기본자본으로 분류했을 거라 생각했으니까) 이제는 그게 아니겠네?」 → 맞다. 확인 결과 `c3ebcc3` 의 재산출은 `kics_forward_capital.json` 의 **신뢰도 블록만** 바꿨고 **전망값은 그대로**다(규칙 `scripts/forward_capital_simulation.py` 가 채권 `tier=hybrid` 를 무조건 `tier1_hybrid`(기본자본, 한도 SCR×15%)로 취급하기 때문 — 약 63행 `_TIER_MAP`, 약 515~528행 `hybrid_t1_y = min(hybrid_remaining, limit_y)`, `basic_y = basic_baseline + (hybrid_t1_y - hybrid_t1_baseline)`).
예: 한화생명(KR0068) 현행 전망 — 기본자본 85,209억(2026) → 82,511억(2029) → 62,692억(2030), 기본자본비율 56.76% → 54.97% → 41.76%. 신종 30,819억이 전부 기본자본(`hybrid_tier1_eok` 22,517억 + 한도초과 8,302억은 보완자본)이라고 보고 콜이 오면 기본자본이 깎이게 계산한 것이다. 그러나 한화생명 공시상 신종은 기본자본에 반영되지 않았다(기준일 기본자본 85,209억은 신종 미포함 — 신종이 들어온 2024.3Q·2025.1Q·2025.2Q 에 기본자본 항목 2 가 △1,197·△7,658·△5,987억, 보완자본 항목 3 이 +7,912·+5,087·+17,051억). owner 는 이 분류(보완자본형)를 이번 라운드에 받아들였다(tier1 소진율 0% 유지 선택).

### 해 줄 것
1. **전망 모델이 증권별 계층 등재부를 따르게 한다**: `data/bonds/capital_tier_registry.json`(`c3ebcc3`; `legacy_tfi`·`tier1`·`tier2` 형, 미확정 `type_unconfirmed`) + `scripts/capital_utilization_rules.py` 의 tier1 규칙과 **같은 정의**를 쓴다.
   - `tier2` 형(보완자본형) 신종 = 콜이 오면 **총자본(지급여력금액)에서만** 빠지고 기본자본은 변하지 않는다(후순위채와 같은 취급). 기준시점 기본자본에 이미 들어 있지 않으므로 `hybrid_t1_baseline` 에서도 제외.
   - `legacy_tfi`(2022년 이전 기발행, 한도 SCR×15%)와 `tier1`(기본자본형 신규, 한도 SCR×10%) = 기본자본 기여를 각각 그 한도로(`min(H, L)`) 계산하고 한도초과분은 보완자본으로(현행 로직의 한도 비율만 증권별로 분리). 경과조치 기발행분의 한도 15% 는 공통적용 경과조치(2032년까지) 기한을 넘기는 시점에 규정대로 처리할지 확인(해당 시점이 전망 범위 2026~2030 밖이면 보고만).
   - `type_unconfirmed`(코리안리·농협생명·푸본현대): 보수적으로 기본자본형 처리(기존과 같게)하되 전망 행에 `type_unconfirmed=true` 와 `basic_ratio_if_tier2_type`(보완자본형이면 나올 기본자본비율 경로)를 같이 싣는다.
2. 재산출: `kics_forward_capital.json`·`templates/forward_capital_latest.json`·`data/bonds/capital_securities_forward_outlook.json`·`output/kics_forward_capital/…`(규약대로). **총자본 경로(지급여력비율)는 바뀌지 않아야 한다**(콜 차감은 tier 무관) — 바뀌면 이유를 보고. 바뀌는 것은 기본자본·기본자본비율 경로(한화생명 등 보완자본형 회사는 기본자본이 평평해진다). 전후 표(47사 × 연도 × 기본자본비율)를 증빙으로 저장하고 한화생명·KDB생명·하나손해·농협손해·흥국화재·교보·DB손해·하나생명은 손계산으로 검산.
3. **화면**(`K-ICS.html` 자본비율 전망 영역)이 새 필드(`type_unconfirmed` 등)를 쓰려면 designer 몫 — 필드 명세를 보고에 적고 HTML 은 건드리지 않는다. 기존 필드 이름·구조는 유지(새 필드 추가만).
4. 단위시험·변이시험 추가(보완자본형이면 기본자본 불변, 한도 10%/15% 분리, 미확정 플래그), `validate_data_contract.py`·`validate_live_artifacts.py`·`tests/` 의 forward 관련 시험 통과, xlsx `자본비율전망` 시트·`public_exports/자본비율전망.json` 은 **다른 JSON 재산출(티켓 `1150Z`·`1130Z`)과 한 번에** `sync_master_xlsx_sheet.py` 로 반영(시트 이름·열 구성 변경 금지, 행·칸 변경 목록으로 증명).
5. 순서: `1150Z`(요약 필드) → **이 티켓** → `1130Z`(메리츠·흥국생명 + 예실차 시트). 한 번에 정합하게 재산출하고 커밋은 분리.

### 규칙
- `kics_disclosure.json` 등 마스터·HTML 수정 금지, 예외 등재 금지. 커밋은 자기 파일만 명시 경로(`git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json`·다른 에이전트 미커밋 제외), 끝에 `Co-Authored-By:` 줄. **push 금지.** 서브에이전트 금지. 파이썬은 풀패스·스크립트 파일만. 시험·게이트는 한 번에 하나씩 끝까지. 이 공유 티켓은 고치지 않는다.

### 보고 (3~6줄 존댓말)
- 바뀐 회사 수·한화생명 전후(기본자본비율 경로), 총자본 경로 불변 여부, 미확정 3사 처리, 새 필드 명세, 게이트 결과, 커밋 해시.

## 답변 (recipient 작성 — 처리 후)
