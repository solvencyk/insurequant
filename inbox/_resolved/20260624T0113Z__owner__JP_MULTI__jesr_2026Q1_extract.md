---
from: owner
to: parser
created: 20260624T0113Z
status: superseded
superseded_by: 20260624T0337Z
route: parse
company: JP_MULTI
period: 2026.1Q
lane: jesr
track: J-ESR
---

## 미결 (owner) — 일본 ESR headline 추출 → J-ESR master JSON [신규 lane · EDINET 추출 probe]

**목표**: downloader가 모은 `J-ESR/raw` + `jesr_sources_2026Q1.csv`를 **원수사별 ESR headline 구조화 JSON**으로. **이번엔 ESR 비율 + 크기지표만**(CSM/PL/민감도 X).

> ⚠️ **신규 lane(jesr) = kics/ifrs17 레인 코드와 별개.** Korea Docling/DART 파서 재사용 금지. 산출물 `J-ESR/`에만. 이 작업은 동시에 wiki [[insurequant 글로벌 피벗...]] §기술 전용성이 권고한 **"EDINET probe = LLM 추출 + 구조 validator를 hand-gold 없이"의 첫 실행**이다.

**추출 아키텍처 (글로벌용으로 검증할 것)**:
- caption 하드코딩·휴리스틱 cascade ❌ → **LLM 의미추출**(注記/ESR資料 표에서 ESR比率·所要資本·適格資本을 뜻으로 식별, 日 라벨 변형 흡수).
- **구조 validator(만국공통 수학)로 정답 보증**: `적격자본 / 所要資本 × 100 ≈ ESR%`(둘 다 있을 때) · ESR% plausible range(대략 100~400%, 벗어나면 flag) · downloader census 대비 완전성. hand-gold 없이 validator 통과로 신뢰.

**산출물** `J-ESR/jesr_master_2026Q1.json` (long/record):
- `{회사명_jp, 회사명_en, 그룹/개별, esr_pct, esr_basis, 所要資本_억엔, 적격자본_억엔, 총자산_억엔, as_of, provenance:{source_url, doc, page}}`.
- 단위 정규화(일본은 百万円 — 한국 억엔 환산 or 원 단위 명기). 음수는 △ 표기(메모리 samo).

**probe 보고(중요)**: hand-gold 없이 LLM추출+validator가 일본 공시에서 ESR을 정확히 뽑았는지 / 실패 케이스 / 라벨 변형 / EDINET XBRL이 PDF보다 쉬웠는지 — 답변란에 정리(이식 아키텍처 1차 검증 결과).

→ `J-ESR/jesr_master_2026Q1.json` 완성 후 `inbox/designer/`로(track: J-ESR).

## 답변 (recipient 작성 — 처리 후)
