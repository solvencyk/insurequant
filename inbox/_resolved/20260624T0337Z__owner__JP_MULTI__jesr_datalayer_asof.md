---
from: owner
to: parser
created: 20260624T0337Z
status: resolved
route: parse
company: JP_MULTI
period: 2026.1Q
lane: jesr
track: J-ESR
supersedes: 20260624T0113Z (owner)
---

## 미결 (owner) — 일본 ESR 데이터레이어 구조화 (as-of 엄격 플래그) [J-ESR · 재발주]

입력 = downloader 핸드오프 `inbox/parser/20260624T0200Z`(수집 11사: `J-ESR/jesr_sources_2026Q1.csv` + `raw/`). 이걸 **별도 일본 화면용 데이터레이어** `J-ESR/jesr_master.json`으로 구조화.

> ⚠️ **이번엔 데이터레이어만. 비교 viz(treemap)에 바로 쓰지 말 것** — as-of 짬뽕이라(2025.3~2026.3) 한 화면 비교는 우리 data-contract 원칙(CHECK-2 as-of 일치) 위반. designer가 as-of별로 안전하게 처리하도록 **플래그만 정확히 달아 넘긴다.**

**필수 필드(레코드별)**:
- `회사명_jp/en, 그룹HD_or_개별_or_상호사, esr_pct, esr_basis(신J-ICS/旧SMR), as_of(YYYY-MM-DD), 所要資本, 적격자본, 총자산, 단위, provenance{source_url,doc,page}`.
- **`as_of_consistent` 플래그**: 2026.3末이면 true, 직전분기면 false. **`not_yet_disclosed` 목록 별도**(미공개사).
- 음수 △(메모리 samo). 단위 정규화(百万円→억엔 등 명기).

**구조 validator(만국공통 수학, hand-gold 없이)**: `적격자본/所要資本×100 ≈ esr_pct`(둘 다 있을 때 ±tol) · plausible range(대략 100~400%, 벗어나면 flag) · downloader census 대비 완전성. → 이게 글로벌 이식 아키텍처 1차 검증(probe).

**probe 보고**: LLM 의미추출이 일본 라벨변형(ソルベンシー/ESR/経済価値)·그룹vs개별 단위를 정확히 구분했는지 / EDINET XBRL이 IR PDF보다 쉬웠는지 — 답변란에.

→ `J-ESR/jesr_master.json` 완성 후 designer(0337Z)로. **10월 개별사 전수가 들어오면 같은 스키마에 append**(설계 시 염두).

## 답변 (parser-jesr 2026-06-24 — 데이터레이어 완성 + EDINET probe 보고)

**✅ `J-ESR/jesr_master.json` 완성** (`J-ESR/build_jesr_master.py`, 신규 jesr 레인 코드·산출물 J-ESR/에만,
한국 파서 무재사용). designer 핸드오프 발송: `inbox/designer/20260624T0600Z`.

### 데이터레이어 (11사, downloader 11사 census 완전 일치)
- record별: `회사명_jp/en·ticker·entity_type(group/mutual)·esr_pct·esr_basis(新J-ICS)·as_of·as_of_consistent·
  所要資本_억엔·適格資本_억엔·총자산_억엔·target_pct·yoy_change_pp(signed)·provenance{url,doc,doc_date,page}·notes`.
- **as_of 엄격 플래그**: `as_of_consistent=true` 4사(東京海上238·MS&AD214·Sompo270·ソニーFG177, 전부 2026-03-31)
  / `false` 5사(第一生命213·日本生命224·住友184·明治安田216·富国260.9, 직전분기) / `not_yet_disclosed` 2사(T&D·かんぽ).
- 단위 정규화: 兆円→億엔(×1e4), 십억円(bn)→億엔(×10). △는 표시레이어(designer)로 위임, 데이터는 signed.

### 구조 validator (만국공통 수학, hand-gold 0)
- **plausible range(100~400%)**: 9사 전부 통과(위반 0).
- **census 완전성**: downloader 11 = master 11(값 9 + 미공표 2), 누락 0.
- **`적격자본/所要資本×100 ≈ esr_pct` 항등식**: ⚠️ **실행 불가** — 所要資本·適格資本 컴포넌트가 **전사 미수집**
  (downloader가 headline %만 web추출). 컴포넌트 들어와야 가동. = 글로벌 이식 validator의 핵심축이 아직 미검증.

### 🔬 EDINET XBRL probe 보고 (owner 핵심 질문 답)
**받아둔 EDINET XBRL 6사(E03823/24/27/33/50, E04506 第一生命) = 전부 FY2024 有価証券報告書(2025-03-31).**
PublicDoc 본문 grep 실측:
| 용어 | 검출 파일수 | 해석 |
|---|---|---|
| `ESR` / `所要資本` / `適格自己資本` | **0 / 0 / 0** | **신ESR 구성요소 有報 XBRL 미태깅** |
| `ソルベンシー・マージン`(구SMR) | 8 | 구 지표만 구조화 존재 |
| `経済価値`(서술) | 9 | 경제가치 언급은 narrative뿐 |

**결론 — "EDINET XBRL이 PDF보다 쉬웠나?": FY2024 기준 NO.** 신J-ICS ESR(2026.3末 첫 의무화)은 有報 XBRL에 없고
**決算説明資料/決算短信 PDF에만** 존재(= downloader가 web/IR로 뽑은 그곳). downloader의 第一生命 XBRL 추출도
`xbrl_stub`(esr/적격/所要 전부 null)으로 남은 게 이 때문. → **FY2025 有報(2026.6~7월 제출, 신규제 첫 반영)부터
ESR 태깅 기대 → 그때 재probe.** EDINET key는 등록 완료(`J-ESR/edinet_key.txt`).

**probe 종합**: 이번 라운드는 "LLM 의미추출+구조 validator"의 **완전 검증은 미달** — (a) 컴포넌트 부재로 수학
validator 미가동, (b) 현 XBRL이 ESR 미포함이라 의미추출 대상 자체가 PDF. **현 신뢰 근거 = downloader web추출 +
plausible-range/census 통과.** 글로벌 이식 아키텍처 1차 검증은 **FY2025 XBRL(컴포넌트 포함 기대) 도착 후**가 진짜 시험대.

### 후속 (전부 owner "선택", 차단 아님)
- FY2025 有報 XBRL 도착 시 ESR/所要/適格 element 추출 재probe(컴포넌트 → 수학 validator 가동).
- T&D·かんぽ 決算説明 PDF OCR로 % 보강 / 비상장 상호사 4사 FY2025末 IR PDF 재수집(downloader).

status: **resolved (데이터레이어 + probe 완료, designer 라우팅).** 후속은 전부 optional·미차단.
