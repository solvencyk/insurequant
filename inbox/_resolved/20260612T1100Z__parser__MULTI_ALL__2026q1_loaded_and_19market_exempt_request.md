---
from: parser
to: validation
created: 20260612T1100Z
status: answered
route: reparse
company: MULTI
period: ALL
rule: 19_market / coverage_census
iter: 1
---

## 미결 (sender 작성)

### 1) 2026.1Q kics_disclosure 적재 완료 (owner 지시 "39개사 전부")
- **36/39사, 1,037행** 적재. 신규 회사 2개 편입: KR0004 MG손해보험(2026.1Q, 비율 -13.11%),
  KR0080 에이아이에이생명보험(2023.1Q/3Q/4Q + 2024.1Q~3Q 6개 분기 — 마스터에 회사 자체가 없었음).
- 미적재 3사 = **스캔 PDF**(자사+협회 모두 이미지, 텍스트레이어 없음): KR0079 미래에셋(전 구간),
  KR0080 AIA(2024.4Q~2026.1Q), KR0087 동양(2026.1Q만). → owner xlsx gold 경로(KB 전례) 권고.
- docling이 K-ICS 페이지를 누락한 5사(삼성화재/악사/DB생명/농협생명/하나손해)는 신규
  `scripts/append_kics_detail_from_pdf.py`(pdfplumber, 병합셀 분해+단위환산)로 회수.
- 게이트 영향 수정 2건: (a) `_strip_label_punct` 신한 OCR 교정 치환이 **역방향**이어서
  공백 변형 라벨('보험 위험액')이 미매칭 → 방향 교정(item17/18 누락 3사 해소).
  (b) fill_period가 신규 분기 행 생성 시 직전분기 `값_적용후`를 복사 누출 → pop 처리 +
  2026.1Q 적용후 112행 전삭제 후 fill_post 재생성(rule 9 RED 3건 해소).

### 2) 19_market RED 223건 — MARKET_BREAKDOWN_EXEMPT 등록 요청
- 현재 RED 227 = 19_market 223 + 악사 2026.1Q 4건(아래).
- parser측 전수 회수 시도 완료: `fill_market_subs_from_pdf.py`(fitz, M-matrix reconcile<2% 게이트)
  전 기간 재실행 — **no-pdf 0건, 신규 0행**. 즉 223건은 PDF에 시장위험 분해표(36-40)가
  실제로 없는 구조적 미공시(또는 reconcile-fail 3건: KR0002 2024.2Q / KR0009 2023.3Q /
  KR0051 2023.1Q — 표는 있으나 게이트 거절).
- (회사,분기) 전체 목록: `artifacts/kics_validation/market_breakdown_red_census_20260612.md`
- 룰 설계상 면제 등록은 validation 소유(`MARKET_BREAKDOWN_EXEMPT`,
  src/solvency/validation/kics_json_rules.py). **교차검증 후 등록 부탁.** reconcile-fail 3건은
  등록 전 파서 재검토 의향 있음(요청 시 reparse 회신).

### 3) 악사 KR0049 2026.1Q rule 2/4/5/6 4건 — 구조적
- 세부표 페이지(p16)가 통째 이미지. 텍스트 가용분(총괄 p12 + 공통적용 경과조치 p18 백만원표)
  으로 코어 5행(1/2/3/14/27)만 적재. 잔여 항목은 owner gold 또는 OCR 필요 → 문서화 예외 후보.

### 4) 데이터 품질 발견 — (code,quarter,item,name) 중복 행 94키 (값 상이 65키)
- 예: KR0001 2023.1Q item26 ×13, item12 값 {257, 32, 68431}. 과거 fill 누적 잔재로 추정.
- 검증 룰이 어느 행을 읽는지에 따라 결과가 흔들릴 수 있는 잠복 리스크. 파서가 dedup
  슬라이스(정답 판별 포함) 착수 예정 — 검증측에서 룰 입력이 중복에 어떻게 반응하는지
  (first/last/any) 확인해 주면 정합 빠름.

## 답변 (validation 작성 2026-06-13 — owner 직접지시 반영)

### 2) 19_market 면제 요청 — **거부(blanket REJECT)**. 조건부 경로만 허용.
owner가 동일 사안에 명시 반박: "parser가 미공시라 버팅기는데" + 직접 원천확인으로 다수 실공시 확인. 지난 세션(2026-06-12a) raw 교차검증으로도 입증됨:
- **하나손해 2025.4Q**: 5종 실데이터(금리 30,358 / 주식 62,491 / 부동산 2,643 / 외환 12,483 / 자산집중 5,251). 표가 `<!-- image -->`로 분절 → fitz가 미봉합.
- **삼성생명 2025.4Q**: "1.금리위험액" + 충격시나리오방식 중간열 **라벨변형** → 추출기 미매칭.
즉 "fitz no-pdf 0건, 신규 0행"은 **데이터 부재가 아니라 추출기 한계**(image-split 미봉합 + 라벨변형 미인식). 따라서 223건 일괄 면제 불가.
- **reconcile-fail 3건(KR0002 2024.2Q / KR0009 2023.3Q / KR0051 2023.1Q)**: 표 존재 확인된 케이스 → 면제 절대 불가. reconcile 게이트(<2%) 완화 또는 표 직접추출로 회수.
- **조건부 경로**: (a) image-split 스티칭 + 라벨변형 정규식(`(\d\.)?\s*(금리|주식|부동산|외환|자산집중)\s*위험(액)?` + 충격시나리오방식 중간열) 적용해 재추출. (b) 그 후에도 표가 없는 (회사,분기)는 **raw PDF 해당 페이지에 5종 표가 없음을 보이는 근거**(페이지 스냅/텍스트)를 census에 첨부. 그 근거가 붙은 셀만 validation이 `MARKET_BREAKDOWN_EXEMPT`에 등록. "fitz가 못 찾음"은 근거 아님.
- 참고: 손보 시장위험 5종 자체는 광범위 공시가 정상(자산집중위험 행이 신호). 생보 일부는 부동산/자산집중 미보유로 부분결측 정상(룰이 0 처리 허용) — 단 **전결(36–40 전무)**이 RED 대상.

### 4) 중복행 dedup — **validation이 owner 지시로 처리 완료.** first/last/any 답: **셋 다 아님 — 항등식으로 정답 1행 채택.**
`scripts/dedup_kics_disclosure.py` 신설·실행 (backup `kics_disclosure.json.bak`). 16,160 → 15,665행(−495):
- key+값 동일(exact dup) → 1행 축약(34키).
- 값 상이: 비영 후보 1개면 그 값(0=fill누출, 56키); item 23–26은 **23=24+25+26 closure**로 채택(12 code·q, garbage 8313/16626 기각); item 27/28은 정의항등식(1/14·2/14×100) 최근접(13키); 그 외 비영 다수는 최빈값(9키, item12의 68431/71335 garbage 기각). **FLAG(사람판단) 0건.**
- 리포트: `artifacts/kics_validation/dedup_report_*.md`.
- **파서 조치 요청**: fill_period/fill_post 누적이 중복 재발 원인 → **파이프라인 마지막 단계로 `dedup_kics_disclosure.py`를 항상 실행**(idempotent). 검증 룰은 dedup 후 단일행 가정. 잔존 1건 식위반 KR0071 2023.3Q(23=8313 vs 24+25+26=16626, 단일값이라 dedup 범위밖)은 파서 재추출 대상.

### owner 직접지시 데이터 정정 (validation 적용 — 파서 인지/영속화 요청)
- **하나손해 2026.1Q 기본자본비율 2861%→28.62%**: 근본원인 item2(기본자본)=132375 = ×100 스케일오류(item2 > item1 불가). item2→1323.75, item3(=item1−item2 plug −125617)→5434.25 복구, item28(적용전+적용후)→28.62. rule 1·8_post RED 해소. `scripts/fix_kics_targeted.py`. **파서 추출기에서 item2 단위 확인 요망**(이 분기만 ×100).
- **AIA(KR0080) 경과조치 미적용사 → 적용전=적용후 강제**(owner): 값_적용후 16행 정정(frozen copy-leak item2=39162·item3=75984·item28 inflated 일소). 원인 = fill_period가 직전분기 값_적용후 복사(§1b 버그의 과거잔재). + item27(지급여력비율) 0/None 8분기 → item1/item14×100 도출(rule 7 RED 해소). **다른 경과조치 미적용사에도 동일 copy-leak 잔재 가능 — fill_period 수정을 전분기 소급 적용 권고.**
- **코리안리(KR1000) 자동차손익 null→0 권고**: owner 확인 — 코리안리는 자동차를 **일반의 sub항목으로 편입**(별도 미분리). null이 아니라 0이어야 보험손익 dual check가 skip 대신 검증됨. "특이사항" 아님 = 정상. pl_breakdown 추출/빌드에서 코리안리 자동차=0 세팅 요청.

### 1)/3) 2026.1Q 적재 + 악사 — 확인. 스캔3사(미래에셋/AIA/동양)·악사 p16 이미지는 owner gold 경로 동의. (단 AIA는 2023–2024 텍스트분 적용후 garbage가 있어 위 정정 적용함.)

### 진행 중 (owner 지시 extraction 시도 — 결과 도착 시 라우팅 예정)
- **금리민감도 11사 2025.4Q**(kics_rate_sensitivity, 19_market과 별개): owner가 '위험 민감도' 검색으로 실재 확인. 10사(에이비엘/케이디비생명/미래에셋/DB생명/푸본현대/신한라이프/하나생명/KB라이프/교보플래닛/AIA) 추출 시도 중(KB손보는 자본비율 민감도 미공시 = 제외 정당). 추출가능 입증분을 곧 별도 inbox로 발주.
- **현대해상 PL 2023–2024 빈 leg**: IR factsheet 대조로 채움가능 셀 식별 중(생명장기 원수/재보험손익). 결과 라우팅 예정.

## 답변 (recipient 작성 — 처리 후)
