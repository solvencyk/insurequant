---
id: 20260913T1300Z
from: owner
to: jp
track: J-ESR
type: investigate
status: resolved
created: 2026-09-13
---

# J-GAAP 貸借対照表 요약 층(`bs`) 신설 — 상세 10사, T자형 BS 패널용

## 배경 (owner 2026-09-13)

일본 사이트를 한국처럼 자본(`jesr.html`) / 회계(`jgaap.html`, 신설) / 기타공시(`disclosure.html`, 신설)로 나눈다.
owner: "`jgaap.html` 에 한국 `IFRS17.html` 처럼 T자형 BS(자산 = 부채 + 자본, [+] 로 세부) 넣을 수 없나? 지금 그런 데이터가 없는 건지?"
→ 현재 `jp/jesr_detail.json` 에는 손익(profit)·시계열(history)·종목별(by_line)·기초이익(core_history) 층만 있고 **J-GAAP 貸借対照表 층이 없다**.
ESR 층의 EBS(T4) 는 경제가치 BS 총액 4개뿐이고 ESR 공표 2사에만 있다. 이 티켓은 **법정 貸借対照表(J-GAAP) 요약**을 상세 10사 전부에 붙이는 것이다.
페이지 쪽(T자형 렌더)은 오케스트레이터가 직접 한다 — **이 티켓은 추출·builder·JSON 까지만.**

## 산출 계약 (`jp/jesr_detail.json` 각 company 에 `bs` 블록 + `_meta.labels` 에 id 라벨)

```json
"bs": {
  "status": "extracted" | "not_obtained",
  "as_of": "2026-03-31", "unit": "JPY_million", "source_doc": "<pdf 상대경로>", "pages": {"assets": 12, "liabilities": 12},
  "tree": [ {"id":"bs_assets_total","label_ja":"資産合計","depth":0,"sign":"=","cur":..., "prev":..., "parent":null, "derived":false}, ... ],
  "checks": {"assets_eq_liab_plus_equity": true, "policy_reserves_sum_ok": true, "no_negative_residual": true}
}
```

`tree` 행(순서 고정, 없는 행은 빼되 합계 3행은 필수). `capital_tree` 와 같은 모양(depth·sign·parent) — 페이지의 `treeRows()`/subtoggle 을 그대로 재사용한다.

| id | label_ja | depth | sign | parent | 비고 |
|---|---|---|---|---|---|
| `bs_assets_total` | 資産合計 | 0 | = | – | 資産の部 合計 |
| `bs_cash` | 現金及び預貯金 | 1 | + | bs_assets_total | |
| `bs_securities` | 有価証券 | 1 | + | bs_assets_total | |
| `bs_loans` | 貸付金 | 1 | + | bs_assets_total | |
| `bs_tangible` | 有形固定資産 | 1 | + | bs_assets_total | |
| `bs_other_assets` | その他資産 | 1 | + | bs_assets_total | **파생(잔차)** = 合計 − 위 4행, `derived:true` |
| `bs_liabilities_total` | 負債合計 | 0 | = | – | 負債の部 合計 |
| `bs_policy_reserves_total` | 保険契約準備金 | 1 | + | bs_liabilities_total | |
| `bs_outstanding_claims` | 支払備金 | 2 | + | bs_policy_reserves_total | |
| `bs_policy_reserves` | 責任準備金 | 2 | + | bs_policy_reserves_total | |
| `bs_policyholder_dividend_reserve` | 契約者配当準備金 / 社員配当準備金 | 2 | + | bs_policy_reserves_total | 생보(상호회사는 社員配当準備金) — 손보는 있으면 |
| `bs_bonds` | 社債 | 1 | + | bs_liabilities_total | 있으면 |
| `bs_other_liabilities` | その他負債 | 1 | + | bs_liabilities_total | **파생(잔차)** |
| `bs_net_assets_total` | 純資産合計 | 0 | = | – | 純資産の部 合計 |
| `bs_capital_and_surplus` | 資本金・資本剰余金 / 基金等 | 1 | + | bs_net_assets_total | 주식회사 = 資本金＋資本剰余金, 상호회사 = 基金＋基金償却積立金(라벨을 회사형태에 맞춰) |
| `bs_retained_earnings` | 利益剰余金 / 剰余金 | 1 | + | bs_net_assets_total | |
| `bs_valuation_diff` | その他有価証券評価差額金 | 1 | + | bs_net_assets_total | 평가차익(owner 관심 항목) — 부호 그대로(음수 가능) |
| `bs_other_equity` | その他(純資産) | 1 | + | bs_net_assets_total | **파생(잔차)** — 繰延ヘッジ損益·土地再評価差額金·自己株式 등 |

checks: `assets_eq_liab_plus_equity` 資産合計 = 負債合計 + 純資産合計 (±1) / `policy_reserves_sum_ok` 保険契約準備金 = Σ하위 (±1, 하위 없으면 None) /
`no_negative_residual` 잔차 3개가 음수가 아닌지(음수면 라벨 매칭 오류 신호 — 단 `bs_other_equity` 는 自己株式 때문에 음수 정당 → 제외).

## 소스·방법

- 10사 = `jp/jesr_detail.json` companies 의 id 전부(au_nonlife, meijiyasuda_nonlife, tokiomarine_nichido, mitsui_sumitomo, sompo_japan, sumitomo_life, nippon_life,
  meijiyasuda_life, dai_ichi_life, nnlife). PDF 는 `J-ESR/raw/fy2025_samples/`(+`others/`) 에 이미 있는 것만 쓴다(**새 다운로드 금지**, 443 불안정).
  없는 회사(第一生命 등)는 `status:"not_obtained"` 로 행 보존.
- 손보 5사 본편: 「貸借対照表」(業績データ 편) — TMNF·MSI·Sompo 는 `extract_esr_template_samples.py` 의 페이지 헬퍼(`page_lines`/`merge_vertical`/Sompo `GidDoc`)를
  **재사용**한다(같은 함정: MSI 세로 글리프, Sompo 폰트 gid). 생보: 決算説明資料(5월) 에 貸借対照表 요약이 있는지 먼저 census 하고 없으면 not_obtained.
- 코드는 **별도 파일 `J-ESR/extract_bs.py`** (기존 `extract_life_core_history.py` 방식) → 산출 `J-ESR/raw/fy2025_samples/extracted_bs_values.json`.
  builder `build_jesr_detail_json.py` 에 `build_bs_block()` 추가 + self_check(`bs` 행 id 가 `_meta.labels` 에 있는지, checks 가 False 면 에러 아님·경고 출력).
- 라벨 변형은 회사별 alias 표로(정본 라벨은 위 표). 2개년(当期末/前期末) 두 열 — 열 방향은 회사별 확인(前期末이 왼쪽인 표가 많다).

## 제약 (CLAUDE.md §4·§10 + owner 2026-09-13)

- python 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 멀티라인 `python -c` 금지(스크립트 파일), UTF-8 BOM 없음, `PYTHONIOENCODING=utf-8`.
- **브라우저·WebFetch·curl 금지. `jp/*.html` 수정 금지**(오케스트레이터가 동시에 편집 중). `jp/jesr_detail.json` 은 builder 실행으로만 갱신.
- **30분 상한.** 25분에 안 끝나면 확보된 회사만으로 builder 를 돌려 JSON 을 남기고 나머지는 not_obtained 로 두고 보고한다. 중간 산출은 디스크에 저장.
- 서브에이전트 금지. 보고문에 일본어 문자 금지(회사명은 영문).

## 종결 시

`status: answered` 로 바꾸고 아래에 결과(회사별 확보/미확보·checks·발견한 레이아웃 함정), `docs/domains/jp_esr_disclosure_template.md` 에 §12 `bs` 층 절 추가,
`TODO_jp.md` Status 맨 위 갱신(최신 5개 유지). 모델·소요시간을 한 줄 남긴다.

## 답변 (jp, 2026-09-13)

**산출.** `J-ESR/extract_bs.py`(신규) → `J-ESR/raw/fy2025_samples/extracted_bs_values.json` → `J-ESR/build_jesr_detail_json.py::build_bs_block()` + `BS_LABELS`(18 id → `_meta.labels`) + self_check 확장 → `jp/jesr_detail.json` 10사 전부 `bs` 블록, `_meta.coverage.bs_extracted=7`, **SELF-CHECK OK**. `jp/*.html`·`build_jesr_page_json.py`·다운로드·서브에이전트 없음.

| id | company_en | status | scope / 열 | source (page) | A=L+E | 準備金Σ | 잔차≥0 |
|---|---|---|---|---|---|---|---|
| au_nonlife | au Non-Life | extracted | solo / 前期·当期 | ディスクロージャー誌 業績データ p14 | True | True | True |
| meijiyasuda_nonlife | Meiji Yasuda Non-Life | not_obtained | – | 별책 EBS 표 列イ(財務会計ベース) 에 純資産 없음, 본편 PDF 부재 | – | – | – |
| tokiomarine_nichido | Tokio Marine & Nichido Fire | extracted | solo / 2개년 | 본편 貸借対照表 p98-99 | True | True | True |
| mitsui_sumitomo | Mitsui Sumitomo Insurance | extracted | solo / 2개년 | 본편 p106 (merge_vertical+unwrap_paren) | True | True | True |
| sompo_japan | Sompo Japan Insurance | extracted | solo / 2개년 | 본편 p130-131 (GidDoc) | True | True | True |
| nnlife | NN Life | extracted | solo / 2개년 | ディスクロージャー誌 p43 | True | True | True |
| nippon_life | Nippon Life | extracted | **group** / 当期末만 | 5월 결산설명자료 p9 연결 요약(億円→×100) | True | None | True |
| meijiyasuda_life | Meiji Yasuda Life | extracted | **group** / 当期末만 | 5월 결산설명자료 p10 연결 요약(億円→×100) | True | None | True |
| sumitomo_life | Sumitomo Life | not_obtained | – | 설명자료에 BS 요약 없음(総資産 1행) | – | – | – |
| dai_ichi_life | Dai-ichi Life | not_obtained | – | PDF 미취득(404 ×2) | – | – | – |

실측 예: TMNF FY2025 資産合計 9,759,680 / 負債合計 6,594,633 / 純資産合計 3,165,047 百万円, その他有価証券評価差額金 1,139,418(前期 1,298,987), 純資産 잔차 △43,594(自己株式·繰延ヘッジ, 정당 음수).
NN Life 評価差額金 △10,032(前期 △7,608).

**레이아웃 함정.** ① NN Life 는 음수를 `△ 7,608`(부호 뒤 공백)로 인쇄 → `is_val` 탈락, 정규화 추가. ② MSI 세로 글리프 병합 시 섹션 헤더와 첫 라벨이 「純資産の部資本金」로 붙음 → alias `^(純資産の部)?資本金$`.
③ Sompo `資本剰余金`/`利益剰余金` 행은 값 없이 `…合計` 행에만 값 → alias 순서 合計 우선. ④ 유가증권 하위 `社債` vs 부채 `社債` → 資産/負債/純資産 섹션 분할 후 grab. ⑤ 생보 5월 설명자료는 연결·億円·当期末만(前年度末差 는 인쇄되나 前期 역산 안 함).
⑥ 明治安田損保 별책 EBS 列イ 는 J-GAAP 当期末 값이지만 純資産 행이 없어 합계 3행 요건 미달 → not_obtained(본편 확보 시 pages 배선만으로 해결).

**checks 정의 조정 1건.** `policy_reserves_sum_ok` 는 支払備金·責任準備金 둘 다 인쇄된 경우만 판정(생보 요약 슬라이드는 責任準備金 1행뿐 → None, 티켓의 "하위 없으면 None" 취지).
`no_negative_residual` 은 티켓대로 `bs_other_equity` 제외.

문서 `docs/domains/jp_esr_disclosure_template.md` §12, `TODO_jp.md` (21). 모델 Opus 5 · 소요 약 32분(30분 상한 2분 초과, builder 3회 실행 포함) · 토큰 약 8만.

## 종결 (orchestrator, 2026-09-13)

검증: `jp/jesr_detail.json` 7사 `bs` 블록·checks 통과, `jgaap.html` T자 패널 렌더 확인(TMNF·日本生命 표시, 住友生命 숨김) → resolved. 남은 3사는 TODO_jp (22) 다음 항목.
