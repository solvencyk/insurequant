---
from: owner
to: designer
created: 20260624T0113Z
status: resolved
superseded_by: 20260624T0337Z
route: html
company: JP_MULTI
period: 2026.1Q
track: J-ESR
---

## 미결 (owner) — 일본 ESR 마켓맵(트리맵) 1개 [J-ESR 신규 트랙 · LIGHT]

**목표**: `J-ESR/jesr_master_2026Q1.json`(parser 산출)으로 **일본 ESR 트리맵 1개**. index.html "K-ICS — 지급여력 마켓맵"과 **동형 미러링**.

> ⚠️ **신규 트랙 = Korea index.html 건드리지 말 것.** 산출물은 `J-ESR/` 안 독립 HTML(예: `J-ESR/jesr_treemap.html`) 또는 일본 전용 페이지. 데이터 JSON은 read-only. 배경 = wiki [[insurequant 글로벌 피벗...]] §일본 데이터 소싱 feasibility.

**트리맵 축 (Korea 미러)**:
- **크기** = ESR `所要資本`(요구자본; index.html은 지급여력기준금액=item14). 없으면 `적격자본` → `총자산` 폴백.
- **색** = `esr_pct`(ESR%; index.html은 지급여력비율). 동일 컬러스케일 로직 재사용.
- RecSplit(balanced binary partition) 트리맵 컴포넌트 + **common.css 토큰** 재사용([[project_designer_common_css]] — 단일 디자인소스). 모바일 리스트뷰(index.html M2 패턴) 동반.

**LIGHT 범위**: 트리맵 1개만. 버블맵·KPI strip·시계열 등 **확장 금지**(다음 슬라이스). 음수/결측은 △·"—" 처리(메모리 samo). 회사 hover=ESR%·요구자본·basis(신J-ICS/旧SMR) 툴팁.

**캡션**: as-of "2026.3末(FY2025)", basis 라벨(신 경제가치 ESR vs 旧 SMR 혼재 시 구분), 커버리지(N개사, 미공개 X개) 주석 — 데이터 정직.

## 답변 (recipient 작성 — 처리 후)
Superseded by `20260624T0337Z` before this order was implemented (as-of 혼재 확인 후 owner가 트리맵→카드/랭킹 화면으로 재발주). 처리 내역은 그 스레드 참조. resolved, archived together.
