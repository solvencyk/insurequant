---
from: owner
to: downloader
created: 20260624T0113Z
status: resolved
route: collect
company: JP_MULTI
period: 2026.1Q
track: J-ESR
---

## 미결 (owner) — 일본 ESR(J-ICS) headline 지표 수집 [J-ESR 신규 트랙 · LIGHT 첫 슬라이스]

**목표**: 일본 원수사별 **ESR 비율(%) headline + 크기지표**만 긁어서 index.html "지급여력 마켓맵"과 동형의 **일본 ESR 트리맵** 1개를 만들 최소 데이터 확보. CSM/PL/민감도는 **이번에 안 함**(headline ESR만).

> ⚠️ **신규 트랙 = Korea 파이프라인과 분리.** 모든 산출물은 **`J-ESR/` 폴더에만** 넣는다(루트 직하 `J-ESR/`). data/disclosure·DART 등 한국 경로 건드리지 말 것. 배경·근거 = wiki [[insurequant 글로벌 피벗 - Solvency II·아시아 규제데이터 시장]] §일본 데이터 소싱 feasibility (검증완료).

**as-of**: 일본 FY2025末 = **2026-03-31** (한국 컨벤션 "2026.1Q"에 대응). 신 경제가치기반 ESR(J-ICS) **첫 의무 사이클**, 5~6월 결산발표/6월 有価証券報告書로 공개되기 시작.

**수집 대상** (新基準 ESR 공개한 生保·損保 그룹/개별사, 그룹 holding 단위 우선):
- 시드: 다이이치HD(FY24末 신기준 ESR 210% 공개 — 2026.3末 갱신값), Tokio Marine HD(5월 결산서 "New ESR end-Mar 2026"), Sompo HD, MS&AD HD, T&D HD, 간포생명, 메이지야스다, 닛폰생명, 스미토모생명, 소니FG 등. **2026.3末 신기준 ESR을 공개한 곳을 폭넓게.**

**소스**: 각사 IR(決算短信·決算説明資料·ESR資料·統合報告書) + **EDINET**(有価証券報告書, API v2 REST/JSON + XBRL). → **EDINET API/XBRL 기계수집 접근성을 이번에 실측**(DART 대응 여부 = 파이프라인 이식성 probe).

**산출물** `J-ESR/jesr_sources_2026Q1.csv`(utf-8-sig) + 원문 → `J-ESR/raw/`:
- 컬럼: `company_jp, company_en, group_or_solo, esr_pct, esr_basis(신J-ICS / 旧SMR), 所要資本, 적격자본, 총자산, as_of, source_url, doc_type`.
- **각 셀 provenance(URL·문서·페이지) 필수.** 없는 값은 공란(추정·날조 금지).

**census(필수)**: 2026.3末 신기준 ESR을 **아직 안 낸** 회사는 별도 리스트로 명시(커버리지 갭 투명화). odd하면 旧 SMR이라도 basis 라벨 달아 같이.

→ 끝나면 `inbox/parser/`로 핸드오프(track: J-ESR). 답변란에 수집 회사 수·EDINET 접근 결과 적기.

## 답변 (recipient 작성 — 처리 후)

처리 완료 (2026-06-24).

**수집 회사 수: 11사** (확정 4 / 직전분기 5 / 미수집 2)

**확정 2026.3末 J-ICS ESR:**
- 東京海上HD 238% · MS&AD HD 214% · Sompo HD 270% · ソニーFG 177%

**직전분기 (2026.3末 미확인):**
- 第一生命HD 213% (2025.12末) · 日本生命 224% (2025.3末) · 住友生命 184% (2025.9末)
- 明治安田生命 216% (2025.3末) · 富国生命 260.9% (2025.9末)

**미수집:** T&D HD (IR PDF 바이너리) · かんぽ生命 (暫定値 공표됐으나 % 불추출)

**EDINET API 실측:** Subscription-Key 필요(무료등록). 등록 후 상장 7사 XBRL 자동수집 가능.
비상장 4사(日本生命·住友生命·明治安田·富国生命)는 EDINET 비대상 → IR PDF만.

산출물: `J-ESR/jesr_sources_2026Q1.csv` + `J-ESR/raw/` + `J-ESR/probe_edinet.py`
Parser handoff: `inbox/parser/20260624T0200Z__downloader__JP_MULTI__jesr_2026Q1_collected.md`
