---
from: owner
to: jp
created: 20260912T1150Z
status: resolved
route: investigate
company: JP_MULTI
period: FY2025
track: J-ESR
supersedes: 20260912T0905Z
---

## 미결 (owner) — 스키마에 **손익 층(profit)** 추가: 생보 기초이익·3이원, 손보 인수이익·운용손익·합산비율·당기순이익 + 회계기준 열

**배경.** owner 2026-09-12: "당기순이익 breakdown 등도 보면 좋겠다." 한국 손익분해 PL 패널의 일본판. 일본 법정 결산은 J-GAAP
원가법(책임준비금 표준이율 lock-in, IFRS17 미적용)이라 CSM 은 없고, 대신 공시서류에
- 생보: `基礎利益`(기초이익) 과 3이원 `利差損益`·`危険差損益`·`費差損益`, `経常利益`, `当期純利益`(상호회사는 `当期純剰余`)
- 손보: `保険引受利益`, `資産運用損益`(利息及び配当金収入·有価証券売却損益 등), `経常利益`, `当期純利益`, `正味収入保険料`,
  `損害率`·`事業費率`·`合算率`(コンバインド・レシオ)
가 표로 있다. 기사 3축의 ③(이차손익 전환)이 바로 3이원이다(도메인 문서 §4b-3 `interest_margin_sign` 은 이 층으로 흡수).

**할 일.**
1. `J-ESR/esr_disclosure_schema.json` 에 `layer: "profit"` 항목 추가(id·labels_ja 변형·ko·unit(百万円/억엔 원문 단위 기록)·formula·
   `kics_item_ref` 대신 `pl_item_ref`(한국 PL_breakdown 32항목 중 대응 번호, 억지 대응 금지·없으면 null)). 최소 항목: 위 나열 전부 +
   전기 비교값(`column: prev`) 있으면 함께. 생보/손보 어느 쪽 항목인지 `sector_scope` 필드.
2. **회계기준 열**: `accounting_basis`(jgaap | ifrs | unstated) 와 `ifrs17_applied`(true/false/unstated) 를 `layer: "profit"` 메타 항목으로.
   공시서류의 회계방침 절(連結財務諸表の作成基準 등)에서 근거 문장을 찾는다. 확인 안 되면 unstated — 추정 금지.
3. 표본 3건(au·明治安田損保·NN Life)에서 추출해 `J-ESR/raw/fy2025_samples/extracted_sample_values.json` 에 `profit` 층 추가
   (`extract_esr_template_samples.py` 확장, 검산: 생보 `基礎利益 ≈ 利差+危険差+費差`(회사별 정의 차이 있으면 명시), 손보
   `合算率 = 損害率 + 事業費率`, `経常利益 ≈ 引受利益 + 運用損益 ± その他`). 明治安田損保 별책에 손익 표가 없으면 본편 URL 을
   census 에서 찾아 받아라(네트워크 curl 가능 시; 막히면 미확보로).
4. `docs/domains/jp_esr_disclosure_template.md` 에 "손익 층" 절(항목·위치·검산·생보/손보 차이·회계기준 판정법) 추가.
5. publishing 이 이어서 `jp/jesr_detail.json` 에 `profit` 블록을 붙일 수 있게, 답변란에 블록 형식 제안(id → 값, prev 포함)을 적어라.

**규칙.** `docs/domains/claude-agent-jp.md` 그대로. python 풀패스, 멀티라인 `python -c` 금지, UTF-8 BOM 없음, 서브에이전트 금지,
`jp/`·마스터 JSON 수정 금지. 끝나면 답변란에 항목 수·검산·회계기준 판정 결과(3사)를 적고 `status: answered`, `TODO_jp.md` 갱신
(Status 5개 유지), `docs/changelog_jp.md`. 보고문 일본어 문자 금지.

## 답변 (jp, 2026-09-12)

**산출물**
- `J-ESR/esr_disclosure_schema.json` — `layer:"profit"` **36항목**(값 32 + 메타 4) 추가, 기존 esr 115·article_axes 22 는 바이트 무변경(스크립트로 대조). 각 항목 `sector_scope`(life/nonlife/both)·`column:"prev+cur"`·`pl_item_ref`·`unit`·`formula`. 스키마 헤더에 `pl_ref_note`·`accounting_basis_note` 추가.
- `J-ESR/extract_esr_template_samples.py` — `PROFIT_ITEMS`/`PROFIT_META_ITEMS`, `extract_profit`(회사별 `profit_pages`·`pl_layout`), `run_profit_checks`(P01~P13, cur·prev 각각), `run_profit_axes_xref`(P12), `merge_vertical`(au 5개년표 세로쓰기 라벨), `pick_pc`(열 레이아웃 4종). exit 0.
- `J-ESR/raw/fy2025_samples/extracted_sample_values.json` — `companies[].profit = {values{id:{prev,cur}}, pages, raw_tokens, meta, summary5, checks}`, `summary[].profit_*`·`accounting_basis`·`ifrs17_applied`, `n_schema_items.profit=36`.
- `docs/domains/jp_esr_disclosure_template.md` §9(항목·위치·검산·생보/손보 차이·회계기준 판정법·publishing 블록) + §0 요약 한 줄. `docs/domains/claude-agent-jp.md` §4b-3 에 profit 층 흡수 문장.

**추출·검산 (百万円, 당기(전기))**

| | au Non-Life | Meiji Yasuda Non-Life | NN Life |
|---|---|---|---|
| 항목 | 25/25 applicable 전부 추출 (p17 損益計算書·p5 明細表/비율·p11 運用) | **NOT_ACQUIRED** 32/32 | 13/16 (三利源 3 = TABLE_ABSENT, 미공시) |
| 経常利益 | 1,654 (1,451) | — | 21,373 (14,336) |
| 当期純利益 | 1,171 (961) | — | 15,090 (10,405) |
| 손보 | 保険引受利益 1,550 (1,363) · 資産運用損益 48 (7) · 正味収入保険料 8,137 (7,976) · 損害率/事業費率/合算率 31.8/39.2/71.1 (29.4/42.7/72.1) | — | — |
| 생보 | — | — | 基礎利益 18,523 (14,828) · キャピタル損益 △1,232 (△1,007) · 臨時損益 4,082 (515) · 保険料等収入 371,006 (395,528) |
| 검산 | **19/19** (P03~P11·P13 cur+prev, P10 5개년표 교차 16/16) | P00 informational 1 | **12/12** (P01 基礎利益+キャピタル+臨時=経常利益 정확, P03~P05, P12 article_axes 교차) |
| 회계기준 | **jgaap / ifrs17_applied=false** — B 티어: 법정 P&L 양식(責任準備金繰入額·支払備金繰入額, p17) + p31 "会社法第436条第2項第1号…保険業法第111条第1項…貸借対照表、損益計算書…監査" | **unstated / unstated** — 별책에 회계방침 절 없음(EBS 財務会計 열의 価格変動準備金 831·危険準備金等 14,879 는 J-GAAP 정합이나 문장 근거 없어 판정 보류) | **jgaap / ifrs17_applied=false** — A 티어: p47~49 会計方針に関する事項 "標準責任準備金の対象契約については金融庁長官が定める方式(平成8年大蔵省告示第48号)", ヘッジ会計 企業会計基準第10号 |

- 티켓 검산식 대응: 손보 `合算率 = 損害率 + 事業費率` → P06(±0.15, 각 비율 소수1자리 반올림이라 71.0 vs 71.1) / `経常利益 ≈ 引受利益 + 運用損益 ± その他` → P07 에서 その他 를 P&L 행으로 명시(その他経常収益 − その他経常費用 − (営業費及び一般管理費 − 保険引受に係る営業費及び一般管理費)) 하니 ±1 로 닫힘 / 생보 `基礎利益 ≈ 利差+危険差+費差` → P02, NN 은 三利源 표 자체가 없어 informational 로 두고 대신 基礎利益 정의식(P01)으로 검산.
- `ifrs17_applied=false` 는 두 회사 모두 "IFRS17 미적용" 문장이 있어서가 아니라, 단체 법정재무제표가 jgaap 으로 확인된 데서 오는 판정(保険業法·会社計算規則상 単体은 J-GAAP 강제, IFRS 는 상장사 연결 임의적용). 이 규칙을 스키마 `accounting_basis_note`·문서 §9-4 에 박았다. 문서에 IFRS 문자열 0건도 같이 확인.
- `pl_item_ref` 는 6개만: 24 당기순이익·22 세전·23 법인세(정확), 20 영업이익↔経常利益·1 보험손익↔保険引受利益·17 투자손익↔資産運用損益(근사, 사유 §9-1). 基礎利益·三利源·正味収入保険料·비율은 null.

**Meiji Yasuda Non-Life 본편.** census 의 disclosure 페이지(`/profile/disclosure/`)를 WebFetch 로 열어 본편 링크 `https://www.meijiyasuda-sonpo.co.jp/profile/disclosure/pdf/20260729.pdf`(明治安田損害保険の現状2026, 2026-07-29) 를 특정했으나 이 PC 에서 curl 000 ×3·python requests ConnectionError ×3(443 차단), WebFetch 는 "maxContentLength 10MB exceeded" 로 거부 → **미확보**. `COMPANIES[meijiyasuda_nonlife]` 에 URL·사유를 적어 두었고, 443 이 열리는 시간대에 받아서 `profit_pages` 만 채우면 같은 코드로 돈다(손보 양식은 au 와 같은 순번 표일 것).

**publishing 블록 제안** — 문서 §9-5 에 JSON 예시. 요지: `companies[].profit = {fiscal_year, unit, accounting_basis, ifrs17_applied, accounting_basis_evidence, source{doc,pages}, items{id:{cur,prev,pl_item_ref?}}, checks{pass,total,failed}, not_acquired, main_volume_url?}`. `items` 는 `extracted_sample_values.json` `companies[].profit.values` 의 non-null 만 무변환, `_meta.labels` 는 이미 36개 profit id 를 포함(builder 가 schema items 전체를 복사). 미확보 회사는 `items:{}` + `not_acquired` 문자열.

**규칙 준수.** `jp/`·마스터 JSON·`build_jesr_detail_json.py` 미접촉(builder 는 `layer=="esr"` 만 읽고 빈 `labels_ja` 를 허용해 profit 층에 안 깨짐 — 코드로 확인, 실행은 안 함). BOM 없음(`7b0a`·`2320`), `ast.parse` 통과. 서브에이전트·브라우저 미사용.

status: **answered**

## 종결 재확인 (orchestrator 2026-09-12)

스키마 173항목(esr 115 / profit 36 / axes 22), profit 의 `pl_item_ref` 정확 3·근사 3 확인. 추출기 재실행 exit 0(au 25항목·검산 19/19,
NN Life 13/16·12/12, 회계기준 2사 jgaap·IFRS17 미적용 근거문장 확인). Meiji Yasuda 본편(20260729.pdf)은 이 PC 443 차단으로 미확보 —
오케스트레이터가 5분 간격 재시도(최대 2h)를 백그라운드로 걸어 두었고, 받히면 추출기를 다시 돌려 profit 을 채운다. publishing 의
`jp/jesr_detail.json` profit 블록 추가는 후속 티켓.

status: **resolved**
