---
from: owner
to: parser
created: 20260614T0712Z
status: answered
route: backlog
company: MULTI
period: 2025 (FY2024 연간 / 2025.1Q~4Q)
lane: ifrs17
iter: 1
---

## 미결 (sender 작성 — owner 라이브 사이트 QA)

CSM 민감도(sensitivity) 추출 파이프라인에 3건. 핵심 파일:
`scripts/viz_build_ifrs17_panels.py` (`_parse_sensitivity_deltas`, `_band_sensitivity_columns`, `extract_sensitivity`) + `src/ifrs17/sensitivity_extractor.py` (`is_mvp_table`).

**(A) 하드코딩 컬럼 인덱스 버그 — 손익영향/CSM delta 오매핑** [glitch G4b]
- `_parse_sensitivity_deltas()` (viz_build_ifrs17_panels.py ~line 779)가 CSM delta=cells[4], PL impact=cells[5]로 **항상 고정 추출**. 회사별 테이블 구조가 다르면 깨짐.
  - Generic(교보/삼성화재): 실제 [1]=보험계약마진, [4]=당기손익인데 [4],[5]를 읽어 오매핑 → 교보 pl_impact=null.
  - Band(DB생명/라이나/케이디비/흥국): "손익영향" 못 찾고 "당기손익"만 있어 pl_idx=None → pl_impact=null. 라이나는 CSM delta의 100배 규모 등 비정상.
- → 사용자 관찰("손익영향이 어떤 회산 있고 없고, CSM변동보다 큰 회사도 있다")의 정체 = **추출 버그**(잔액초과손실 아님).

**(B) 5개 손보사 시나리오 전체 누락** [glitch G7]
- 메리츠화재: extracted에 sensitivity_analysis 있으나 헤더가 band/product 어느 분류에도 안 맞아 scenarios=empty → status=partial.
- DB손해: block_type="reinsurance"라 `is_mvp_table()`(sensitivity_extractor.py ~line 84)가 명시적 제외 → status=unavailable.
- KB손해: MVP extract에 sensitivity_analysis 없음(원본엔 line 809/1357/3787에 있으나 MVP 필터서 탈락). OCR 아니라 **필터 문제**.
- NH농협손해·한화손해: 동일 MVP 필터 문제.
- → 사용자 관찰("CSM민감도 미제공 손보사 너무 많다")의 정체. 최소 25.4Q는 채워야.

**(C) 단위 스케일 오류 — 현대해상 ~640배 과대** [glitch G6]
- 현대해상(KR0009) 민감도표가 **원(won)** 단위인데 삼성화재(KR0008)는 **만원** 단위. 정규화 미적용.
  - 현대 `data/dart/extracted/현대해상_20250313001346_sensitivity_mvp.json` ~line 226: CSM delta -85,343,139(원), 기준금액 18,172,429,271(원).
  - 삼성 `..._삼성화재해상보험_20250311001055_sensitivity_mvp.json` ~line 35: CSM delta -133,356(만원). → 약 640배 차이.
- → 사용자 관찰("현대 CSM민감도가 삼성화재보다 큼, 맞나?")의 정체 = **단위 미정규화**.

권장 조치 (reparse):
- `_parse_sensitivity_deltas`/`_band_sensitivity_columns` 리팩터: 헤더에서 컬럼 의미(보험계약마진/당기손익/손익영향) **동적 탐지** 후 매핑. 못 찾으면 명시적 null.
- `is_mvp_table()`: reinsurance 블록이라도 유효 CSM 시나리오 있으면 include 검토.
- 단위 정규화: 캡션("백만원/억원/만원") 감지 → 통일 단위로 변환. 기준금액 규모비 1000배↑면 경고.
- (designer 연계) 흥국생명 shock 컬럼에 product line명(건강보험/연금저축)이 섞여 행이 깨짐 → 별도 시나리오 행으로 분리(parser fix) 후 designer 테이블 정상화.
- sanity: CSM_delta vs pl_impact 비율로 오매핑 조기감지. validation inbox에 단위/비율 sanity 룰 추가 요청함.

## 답변 (parser 2026-06-14 — A/C/B 3건 처리 완료)

`scripts/viz_build_ifrs17_panels.py`만 수정(파서 로직). 전사 회귀 검증 + production 빌드.

### (A) G4b 컬럼 오매핑 — 수정
원인은 하드코딩 `[4]/[5]`가 아니라(표준표는 band 경로) `_extract_sensitivity_band`가 **고정 csm_idx를
좌측기준**으로 써서, 기준금액 컬럼이 rowspan 생략된 2번째 행부터 셀이 밀린 것. → 표준 레이아웃(기타포괄손익
trailing) 한정 **우측기준(negative index)** 정렬. 교보·삼성·현대·라이나 2번째 행부터 csm/pl 정상.
케이디비(위험경감)·흥국 등 타 레이아웃 무회귀.

### (C) G6 단위 — 억원 통일 + 데이터 판정 (owner 노트 2건 다 오류였음)
cue(억원/백만원/천원/만원) 우선 → no-cue는 base CSM을 `CSM_waterfall.json`(억원) 총CSM과 대조해 배율
역산·power-of-10 스냅. **삼성=백만원**(owner '만원' ✗), **현대=천원**(owner '원' ✗ — 이행CF열 오참조).
현대 사망률 ΔCSM −85,343,139천원 → **−853억**, 삼성 −1,334억 = 동일규모(640배 해소). 출력에
`unit:"억원"` + `unit_detected` + `unit_source`. **sanity 가드**(owner 요청): max|ΔCSM| > 총CSM×3이면
단위오류로 보고 `unit_source="suspect"` + 값 null + `unit_warning`. 메트라이프(default 백만원 → −59조) 차단.

### (B) G7 5손보 — 전체 복구
근본원인: 패널이 `_sensitivity_mvp.json`만 읽어 is_mvp가 떨군 표가 안 보임 + picker가 CSM 없는 표
(이행CF/PL-only)를 더 높은 score로 오선택. → ①입력을 full `_sensitivity.json`로 전환(is_mvp 우회, raw
불요; kics 파일은 14자리 rcept 없어 build_panel이 skip) ②picker **CSM 컬럼 보유 최우선** ③방법론표
(산출방법/근거) penalty ④CSM 없는 표용 **PL-only 핸들러**(NH 출재경감 당기손익변동).
- 결과: 메리츠 ok/6·DB손해 ok/6·KB ok/1·NH ok/8(PL-only)·**한화=partial(별첨, 본문 CSM 민감도 없음=legit)**.
  보너스 AIA·케이비라이프 복구. **회귀 0**, 25/28 ok.

### 검증/blast-radius
production 빌드: 오직 `sensitivity_heatmap.json` 변경(타 패널 byte-identical). pytest 110 passed.
전사 mvp-vs-full 비교 CHANGED 0.

### 잔여(별건)
- **흥국생명 product-as-rows** shock 컬럼에 상품명 혼입(건강보험/연금저축) = TODO F16, designer 연계. 별도.
- 미래에셋/신한라이프 non-ok = owner 5손보 밖, 기존 상태(별도 확인 대상).
- validation: 단위/비율 sanity 게이트 룰은 검증 스테이지에서 추가 권장(파서측 가드는 구현됨).

status: answered
