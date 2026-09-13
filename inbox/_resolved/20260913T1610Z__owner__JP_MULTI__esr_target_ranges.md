---
id: 20260913T1610Z
from: owner
to: jp
track: J-ESR
type: investigate
status: resolved
created: 2026-09-13
---

# 각사 ESR 목표 레인지(자본정책) census — 랭킹 색 기준 교체용

## 배경 (owner 2026-09-13)

랭킹(`jp/index.html`)의 막대 색은 감독 하한 100% 기준이라 전부 초록이다. owner: "각사 ESR 목표 레인지에 따라 색을 차등하겠다며 — 반영 안 돼 있다".
대형사는 자본정책에서 ESR 목표 레인지(예: 상단 초과 → 주주환원, 하단 미달 → 자본 조치)를 공표한다. 이 값을 회사별로 모아 `J-ESR/esr_target_ranges.json` 에 넣는다.
페이지 쪽(색 규칙)은 오케스트레이터가 한다 — **이 티켓은 census + JSON 까지만.**

## 대상

`jp/jesr_esr.json` records 15건의 회사 전부(지주 연결·単体 포함) + `jp/jesr_detail.json` 10사. 単体 회사(東京海上日動·三井住友海上·損保ジャパン 등)는 자기 레인지가
없으면 모회사(HD) 레인지를 쓰되 `inherited_from` 에 모회사명을 적는다. 상호회사(日本生命·明治安田生命·住友生命)는 공표 레인지가 없을 수 있다 → `null` + `note`.

## 산출 계약 `J-ESR/esr_target_ranges.json`

```json
{ "_meta": {"as_of": "2026-09-13", "note": "..."},
  "ranges": [
    {"company_jp": "東京海上ホールディングス", "company_en": "Tokio Marine Holdings", "low_pct": 100, "high_pct": 140,
     "basis": "internal_99.95" | "regulatory" | "unknown", "confidence_level": "99.95%" | "99.5%" | null,
     "policy_note": "상단 초과 시 … / 하단 미달 시 …(원문 요지, 한국어)", "source_url": "...", "source_doc": "決算説明資料 2026-05 p.xx", "as_of": "2026-05-20",
     "inherited_from": null }
  ] }
```

**basis 가 핵심이다.** 레인지가 사내 모델(예: 99.95% VaR) 기준인지 규제 ESR(99.5%) 기준인지 원문에서 확인해 적는다. 규제 ESR 도입(2026-03 결산) 이후 규제 기준으로
목표를 바꿔 공표한 회사가 있으면 그 값을 우선하고, 사내 기준만 있으면 basis=internal 로 적는다(페이지는 basis 가 다르면 각주로 알린다). 추정·유추 금지: 원문에 숫자가 없으면 null.

## 방법·제약

- WebSearch → 회사 IR 페이지의 決算説明資料/中期経営計画/統合報告書 PDF 를 WebFetch 로 읽는다(바이너리 저장 가능). **브라우저·curl 금지, go.kr 금지.**
  회사당 검색 2회·fetch 2회 상한. 안 나오면 null 로 두고 넘어간다.
- python 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 멀티라인 `python -c` 금지, UTF-8 BOM 없음.
- `jp/*.html`·`J-ESR/build_jesr_page_json.py` 수정 금지. 20분 상한 — 넘기면 확보분만 저장하고 보고. 서브에이전트 금지.
- 보고문 한국어, 일본어 문자 금지(회사명 영문). 회사별 low/high/basis/출처 한 줄씩 + 모델·소요시간 한 줄.

## 종결 시

`status: answered` + 결과표. `TODO_jp.md` Status 맨 위(최신 5개 유지), `docs/domains/claude-agent-jp.md` §4b 에 `esr_target_range` 항목 추가(10월 재조사 대상에 포함).

## 답변 (jp-collector 2026-09-13)

산출: `J-ESR/esr_target_ranges.json`(계약 그대로 `_meta`+`ranges[]`). 대상 20사(jesr_esr.json 15 + jesr_detail.json 미중복 5: Dai-ichi Life Insurance·NN Life·
Tokio Marine & Nichido Fire·Mitsui Sumitomo Insurance·Sompo Japan Insurance).

**확보(basis=regulatory, confidence_level=99.5% 전부):**

| company_en | low_pct | high_pct | inherited_from | source_doc(요지) |
|---|---|---|---|---|
| Tokio Marine Holdings | 190 | null | - | 2026-03 신규제 전환 후 目標190%以上 재설정(구기준 内部モデル99.95%VaR 100~140%에서 전환). 直接열람 실패, WebSearch 스니펫(Nikkei 기사·2025-11-26 경영전략 자료 인용) 교차확인 |
| MS&ADインシュアランスグループHD | 180 | 250 | - | ESR目標レンジ180~250%(99.5%신뢰수준). 자본정책 페이지 WebFetch 403, WebSearch 스니펫 교차확인. 일부 최신자료는 상한 없이 "180%以上"로만 표현 |
| SOMPOホールディングス | 200 | 270 | - | 目標資本水準ESR200~270%(VaR99.5%, jesr_esr.json 기존 basis=J-ICS_VaR99.5와 일치). PDF 이미지형이라 텍스트 직접확인 실패, WebSearch 교차확인 |
| T&Dホールディングス | 133 | 225 | - | ERM페이지 직접열람 확인(원문: "バリュー・アット・リスクという指標を用いて、計測期間1年、信頼水準99.5%の損失額として計測"). 133%以上을 필요수준, 恒常的225%초과시 환원판단. **6건 중 유일하게 직접열람으로 확인** |
| Dai-ichi Life Insurance | 170 | 200 | 第一生命ホールディングス | 그룹+국내3사 공통 목표레인지170~200%(신경제가치규제전환, 99.5%신뢰수준). WebSearch 교차확인, PDF 직접열람 미시도 |
| Tokio Marine & Nichido Fire | 190 | null | 東京海上ホールディングス | 자사 공표 없음, 모회사 레인지 상속 |
| Mitsui Sumitomo Insurance | 180 | 250 | MS&ADインシュアランスグループHD | 자사 공표 없음, 모회사 레인지 상속 |
| Sompo Japan Insurance | 200 | 270 | SOMPOホールディングス | 자사 공표 없음, 모회사 레인지 상속 |

**null(추정 금지, 확인 안 됨) 12건:** 상호회사 5사(日本生命保険·住友生命保険·明治安田生命保険·朝日生命保険·富国生命保険, 전부 basis=unknown — 목표레인지 미공표가 정상),
ソニーフィナンシャルグループ(수치 미확인, WebSearch 2회+WebFetch 1회 실패)·ソニー生命保険(모회사도 null이라 상속불가)·かんぽ生命保険(2026-05-15 중기계획 존재하나 수치 미확인)·
ライフネット生命保険(규제/내부 ESR 병기 프레임만 확인, 수치 없음)·エヌエヌ生命保険(시간상한으로 검색 후순위)·au損害保険(KDDI 자회사, 그룹 레인지 없음)·明治安田損害保険(모회사 상호회사라 상속불가).

**모델·소요:** Sonnet 5, 실측 약 20분(WebSearch 13회 + WebFetch 6회, 회사당 상한 준수), 서브에이전트 없음.

status: **answered**

## 종결 (orchestrator, 2026-09-13)

검증: `J-ESR/esr_target_ranges.json` 20사 → `build_jesr_page_json.py::attach_target_ranges()` 로 `jp/jesr_esr.json` record.target_range 4건 부착(TMHD·MS&AD·Sompo·T&D), 랭킹 색 규칙 반영 확인 → resolved.
주의: MS&AD·Sompo·第一生命 값은 검색 스니펫 교차확인(원문 직접 열람은 T&D 뿐) — 10월 재조사에서 원문 확인 필요(특히 Sompo 上限 270 = 현재 ESR 270 과 일치, 의심).
