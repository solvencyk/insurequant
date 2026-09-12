---
from: owner
to: publishing
created: 20260912T1120Z
status: answered
route: assemble
company: JP_MULTI
period: FY2025
track: J-ESR
---

## 미결 (owner) — `jp/jesr_detail.json` 조립: K-ICS.html 대응 회사별 상세 페이지의 데이터 (현재 규제양식 공시 2사)

**배경.** owner 2026-09-12 "2개사에 대해 K-ICS.html 에 대응되는 페이지 만들어라." 입력은 이미 있다:
`J-ESR/raw/fy2025_samples/extracted_sample_values.json`(생성기 `J-ESR/extract_esr_template_samples.py`, 회사 3: au_nonlife·
meijiyasuda_nonlife·nnlife — nnlife 는 ESR 미공시라 **제외**, `census.status == posted` 인 2사만), 항목 정의 `J-ESR/esr_disclosure_schema.json`
(id·labels_ja·ko·unit·kics_item_ref), 합산 규정 `J-ESR/esr_aggregation_rules.json`, 헤드라인/출처 `jp/jesr_esr.json`.

**할 일.** `J-ESR/build_jesr_detail_json.py`(stdlib) 신규 → `jp/jesr_detail.json`. `J-ESR/raw/` 는 gitignore 라 생성기가 먼저 돌아
표본값 JSON 이 있어야 한다(없으면 `extract_esr_template_samples.py` 를 먼저 호출). 계약(designer 와 고정, 키 이름 변경 금지):

```json
{
  "_meta": {
    "as_of": "2026-03-31", "as_of_label_ja": "2026年3月31日", "generated_at": "<UTC ISO>", "unit": "JPY_million",
    "schema_ref": "J-ESR/esr_disclosure_schema.json", "rules_ref": "J-ESR/esr_aggregation_rules.json",
    "labels": { "<schema_id>": {"ja": "...", "ko": "...", "unit": "JPY_million|pct|...", "kics_item_ref": 1|null} },
    "next_update": "2026-10-31", "coverage": {"detail_posted": 2, "posted_total": 13, "census_total": 79}
  },
  "companies": [
    {
      "id": "au_nonlife", "company_jp": "...", "company_en": "au Non-Life", "sector": "nonlife", "scope": "solo",
      "as_of": "2026-03-31", "source_url": "https://...", "doc_type": "...", "doc_date": "2026-07-30",
      "headline": {"eligible_capital": 9278, "required_capital": 1171, "esr_pct": 791.7, "preliminary": false},
      "capital": { "<schema_id>": value, ... },          // 적격자본 구성 항목(tier1_*·tier2_* 등 스키마 T2 계열, non-null 만)
      "risk": { "rc_life":..., "rc_nonlife":..., "rc_catastrophe":..., "rc_market":..., "rc_credit":..., "rc_operational":...,
                "diversification_effect":..., "rc_pre_tax":..., "tax_effect":..., "rc_post_tax":... },   // 없으면 null
      "market_sub": { "rc_mkt_interest":..., "rc_mkt_spread":..., "rc_mkt_equity":..., "rc_mkt_property":..., "rc_mkt_fx":..., "rc_mkt_concentration":... },
      "sensitivity": [ {"id": "<schema_id>", "label_ja": "...", "esr_pct": 736.7, "delta_pp": -6.5} , ... ],   // 기준 대비 pp 변화 포함
      "aggregation": { "top_sqrt": 1257.4, "simple_sum": 1531, "reproduced": true|false, "checks_pass": 43, "checks_total": 43,
                       "deviations": [ {"id": "G06_nonlife", "lhs":..., "rhs":..., "note": "..."} ] },
      "axes": { "<article_axes id>": value },             // 기사 3축 층, non-null 만
      "items": { "<schema_id>": value }                   // esr 층 전 항목 flat(non-null 만) — designer 가 라벨은 _meta.labels 로
    }
  ]
}
```
- `sensitivity[].delta_pp` = 시나리오 esr − 헤드라인 esr(소수 1자리). 시나리오 id·라벨은 스키마의 민감도 항목 그대로.
- self-check(실패 시 exit 1): companies 정확히 2, 각 headline 이 `jp/jesr_esr.json` 의 같은 회사 esr_pct 와 일치, `risk.rc_post_tax ==
  headline.required_capital`, `_meta.labels` 에 items 의 모든 id 가 있음, unit 표기 일관(百万円 원본 그대로, 억엔 변환 금지 — 화면에서 변환).
- 배포: `scripts/android_push_and_deploy.sh` 의 `NEW_FILES` 에 `jp/company.html jp/jesr_detail.json` 추가(한 줄). 그 외 keep-list·xlsx·
  public_exports 는 건드리지 않는다.

**규칙.** python 풀패스, 멀티라인 `python -c` 금지, UTF-8 BOM 없음, `ensure_ascii=False, indent=2`. 서브에이전트 금지. 루트 마스터·HTML 수정 금지.
끝나면 답변란에 2사 headline/risk 요약과 self-check 로그를 적고 `status: answered`, `TODO_jp.md` 갱신, `docs/changelog_jp.md` 기록.
보고문 일본어 문자 금지.

## 답변 (publishing, 2026-09-12)

`J-ESR/build_jesr_detail_json.py`(stdlib) 신규 → `jp/jesr_detail.json` 생성, exit 0.

**2사 headline/risk 요약:**

- **au_nonlife** (au損害保険): eligible_capital=9,278 / required_capital=1,171 / esr_pct=791.7% / preliminary=false.
  risk: rc_nonlife=1,119, rc_catastrophe=87, rc_market=247, rc_credit=78, rc_operational=251,
  diversification_effect=274, rc_pre_tax=1,510, tax_effect=338, rc_post_tax=1,171(=required_capital 일치).
  rc_life=null(손보사, 생명보험리스크 없음). aggregation: reproduced=true, checks=43/43, deviations=0.
  sensitivity=[](이슈어가 민감도 값 생략 — 절대변화 1%p 미만 주기 명시, 추정으로 채우지 않음).

- **meijiyasuda_nonlife** (明治安田損害保険): eligible_capital=40,290 / required_capital=5,420 / esr_pct=743.2% /
  preliminary=false. risk: rc_nonlife=2,096, rc_catastrophe=1,865, rc_market=4,613, rc_credit=475, rc_operational=463,
  diversification_effect=2,530, rc_pre_tax=6,985, tax_effect=1,564, rc_post_tax=5,420(=required_capital 일치).
  aggregation: reproduced=true, checks=49/51, deviations=2건(G06_nonlife: disclosed 2,096 vs recomputed 2,137.3 —
  다지역 상관통합 순서 차이, informational; G07_catastrophe: disclosed 1,865 vs recomputed 1,974.4) — 둘 다
  `esr_aggregation_rules.json`의 known_deviations에 이미 등재된 편차. sensitivity=7행(예: 엔금리+50bp → esr_pct=736.7%,
  delta_pp=-6.5).

**self-check 로그 (exit 0):**
```
wrote .../jp/jesr_detail.json -- companies=2
  au_nonlife: esr_pct=791.7 eligible=9278 required=1171 reproduced=True checks=43/43
  meijiyasuda_nonlife: esr_pct=743.2 eligible=40290 required=5420 reproduced=True checks=49/51
SELF-CHECK OK
```
검증한 4항목: companies==2 / 각 headline.esr_pct가 `jp/jesr_esr.json`(records ∪ excluded_subsidiaries) 대조와 일치 /
risk.rc_post_tax==headline.required_capital(양사 모두) / items의 모든 id가 `_meta.labels`(137개)에 존재 / 단위 무변환
(items.eligible_capital==headline.eligible_capital, 억엔 환산 없음 확인).

**소스 판단 근거 1건 추가.** source_url/doc_type/doc_date/preliminary 4필드는 `jp/jesr_esr.json`이 아니라 `J-ESR/jesr_master.json`
에서 조인했다. 부모-자회사 중복 제거(TODO_jp.md 2026-09-12 (3), 이번에 archive 이관됨) 이후 `jp/jesr_esr.json`은
明治安田損害保険을 `_meta.excluded_subsidiaries`에 esr_pct만 남기고 저 4필드를 비웠기 때문 — `jesr_master.json`(제외 전
15사 원본, 같은 lane 소유)에서 company_en으로 조인해 실제 값을 채웠다(au_nonlife는 두 파일 값이 동일함을 확인, 조인은
meiji손보에만 실질적으로 필요).

**위생 확인.** BOM 없음(`xxd` 첫 바이트 `7b0a`) · `ast.parse` 통과 · `git status --short J-ESR/ jp/` = 신규
`build_jesr_detail_json.py` · `jp/jesr_detail.json` 뿐(루트 마스터·xlsx·public_exports·keep-list·HTML 무변경).
`jp/_fixture_jesr_detail.json`은 designer 병렬세션 산출물이라 손대지 않았다.

**배포 등록.** `scripts/android_push_and_deploy.sh`의 `NEW_FILES`에 `jp/company.html jp/jesr_detail.json` 추가(한 줄) 완료.
아직 라이브 미반영(`jp/company.html`이 designer 쪽에서 완성돼야 하고, owner 승인 후 별도 배포 라운드).

재현: `PYTHONIOENCODING=utf-8 C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe J-ESR/build_jesr_detail_json.py`

TODO_jp.md Status (8)번 항목 및 docs/changelog_jp.md (8)번 항목에 동일 내용 기록. Status 최신 5개 유지를 위해 (3)번 항목을
`docs/todo_archive_jp.md`로 무수정 이관.
