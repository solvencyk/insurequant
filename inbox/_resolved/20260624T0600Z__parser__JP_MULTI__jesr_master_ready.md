---
from: parser
to: designer
created: 20260624T0600Z
status: open
route: handoff
company: JP_MULTI
period: 2026.1Q
lane: jesr
track: J-ESR
status: resolved
---

## 핸드오프 (parser-jesr → designer) — J-ESR 데이터레이어 완성 (`J-ESR/jesr_master.json`)

owner `inbox/parser/20260624T0337Z` 처리 완료. 일본 ESR headline 11사를 데이터레이어로 구조화.
**입력 = `J-ESR/jesr_master.json`** (long/record, `records[]` + `_meta`).

### ⚠️ 화면 설계 필수 제약 (as-of 혼재 — data-contract CHECK-2)
**as_of가 2025.3~2026.3로 섞여 있다. 한 비교 viz(treemap 등)에 통째로 넣지 말 것.** 레코드별 `as_of_consistent` 플래그로 분리:
- **`as_of_consistent: true` = 4사 (전부 2026-03-31, 동일 as-of = 안전 비교셋)**:
  東京海上 238% · MS&AD 214% · Sompo 270% · ソニーFG 177%.
- **`as_of_consistent: false` = 5사 (직전분기, basis 다름)**: 第一生命 213%(25.12) · 日本生命 224%(25.3) ·
  住友生命 184%(25.9) · 明治安田 216%(25.3) · 富国 260.9%(25.9). → 별도 표기(as_of 라벨 노출) or 흐리게.
- **`status: not_yet_disclosed` = 2사**: T&D HD · かんぽ生命 (2026.3末 미공표) → "공표대기" 표기.

### 표시 규칙
- 음수(`yoy_change_pp` 등)는 △ 표기 = **표시레이어(designer 몫)**. 데이터는 signed numeric(예 -12).
- 단위 = 億엔(`총자산_억엔` 등). 총자산은 東京海上·ソニーFG만 있음(나머지 null).
- `entity_type`: group(지주) vs mutual(相互会社, 日本生命 등 비상장). 그룹 vs 개별 단위 구분.
- provenance(source_url·doc·doc_date) 레코드별 보유 — 출처 링크 노출 가능.

### 데이터 한계 (화면 카피에 반영 권장)
- 所要資本·適格資本 컴포넌트 = **전사 미수집**(headline %만) → 도넛/누적 분해 불가, ESR% 단일값만.
- 같은 스키마에 **10월 개별사 전수 append 예정**(owner) — 레이아웃을 append-friendly로.

status: open (designer 처리 대기). 데이터 정확·validator 통과(아래 answer 참조), 표시/as-of 분리만 designer.

## 답변 (recipient 작성 — 처리 후)
반영 완료. `J-ESR/index.html`에서 `as_of_consistent`로 3구간(확정4/직전분기5/공표대기2) 분리 렌더, `status:"not_yet_disclosed"` 2사는 별도 pending 카드. `yoy_change_pp` △ 표시레이어 적용(samo). `所要資本`·`적격자본` 전부 null이라 도넛/분해는 미구현(데이터 한계 그대로 반영, ESR% 단일값만 표시) — 캡션에 "그룹 연결 기준"만 명시, 컴포넌트 분해 없다는 점은 향후 훅 주석으로 남김. append-friendly 구조(구간 분리 fetch→filter)라 10월 개별사 전수 추가 시 HTML 무변경으로 흡수 가능.
