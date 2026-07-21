---
from: owner
to: designer
created: 20260624T0337Z
status: resolved
route: html
company: JP_MULTI
period: 2026.1Q
track: J-ESR
supersedes: 20260624T0113Z
---

## 미결 (owner) — 일본 보험사 전용 insurequant 화면 (별도 페이지) [J-ESR · 재발주]

**확정 방침**: 일본 보험사는 **한국 index.html과 분리된 독립 화면**. 한국 36사와 한 트리맵에 섞지 않는다(as-of·규제·시장 다름). 데이터 = `J-ESR/jesr_master.json`(parser 0337Z, read-only).

> ⚠️ **Korea index.html·K-ICS·IFRS17 페이지 일절 건드리지 말 것.** 신규 독립 페이지(예: `J-ESR/index.html` 또는 `insurequant-jp.html`). insurequant 브랜드 일관(**common.css 토큰 재사용** — [[project_designer_common_css]]).

**핵심 제약 — as-of 정직(우리 데이터 원칙)**:
- 지금 데이터는 **그룹HD 연결 ESR + as-of 짬뽕**(확정 2026.3末 4사: 東京海上238·MS&AD214·Sompo270·ソニー177 / 직전분기: 第一213·日本生命224·住友184·明治安田216·富国260.9 등). **개별사 전수는 10월(EDINET 有報)**.
- **as-of 섞인 트리맵 비교 금지**(2026.3 vs 2025.3 한 화면 = 금리환경 다른 시점 비교 = 오해). 한국에서 만든 게이트가 RED 때리는 그 위반.

**지금(6월) 화면 = "일본 주요 보험그룹 ESR 현황"**:
- 트리맵 아님 → **카드 또는 랭킹 바**. 각 항목에 `ESR% · as-of · basis(신J-ICS/旧SMR) · 그룹/개별/상호사` **명시**(as-of별 시각 구분: 2026.3末 강조, 직전분기 흐리게/배지).
- 상단 캡션: "그룹 연결 기준 · 개별사 전수는 2026.10 EDINET 有報 후" — 커버리지 정직(N사 표시, 미공개 X).
- 모바일 반응형(index.html 패턴).

**10월 확장 설계(지금 미구현, 훅만)**: 같은 페이지가 개별사 전수(일관 2026.3末)로 채워지면 **트리맵(크기=所要資本·색=ESR%, 한국 마켓맵 미러)으로 승격**되도록 컴포넌트 구조만 준비. 트리맵은 **일관 as-of subset일 때만 활성**.

→ 산출물 독립 HTML(`J-ESR/`). 답변란에 페이지 경로·현재 표시 회사 수.

## 답변 (recipient 작성 — 처리 후)
구현 완료. 페이지 = `J-ESR/index.html` (독립 HTML, Korea index.html/K-ICS.html/IFRS17.html 무변경). `common.css` 링크(`../common.css`)로 브랜드 통일, 자체 헤더에 한국판 되돌아가기 링크만 추가.

- **트리맵 아닌 카드+랭킹바**: `jesr_master.json`을 fetch해 `as_of_consistent` 플래그로 3구간 분리 렌더 — "2026.3末 확정"(4사, 서로 비교 가능 명시) / "직전분기 참고치"(5사, dim 처리 + "직접 비교하지 마십시오" 문구) / "공표 대기"(2사, T&D·かんぽ生命).
- 각 카드: ESR% 큰 숫자 + 미니 바(같은 구간 내부만 시각적 랭킹, 구간 간 비교 유도 안 함) + basis(新J-ICS, preliminary 표기) + entity_type 배지(그룹/상호) + yoy_change_pp(△/+, samo 관례) + 출처 링크(provenance.source_url).
- 상단 캡션 "그룹 연결 기준 · 개별사 전수는 2026.10 EDINET 有報 후" + 실시간 커버리지 카운트(수록 11社, 구간별 개수) — 데이터 정직 요건 충족.
- **10월 확장 훅**: JS에 주석으로 "as_of_consistent 커버리지 넓어지면 이 카드그리드를 RecSplit 트리맵으로 교체" 표시만 해둠(컴포넌트 자체는 미구현, 데이터 shape은 이미 treemap-ready).
- 검증: 로컬 서버로 `J-ESR/index.html` 프리뷰 — 콘솔 에러 0, 11社 전부 올바른 구간 렌더(4/5/2), 375px 모바일에서 1열 그리드로 접힘, 가로 스크롤 없음.
- 표시 회사 수: **11社** (2026.3末 확정 4 · 직전분기 참고 5 · 공표대기 2).
