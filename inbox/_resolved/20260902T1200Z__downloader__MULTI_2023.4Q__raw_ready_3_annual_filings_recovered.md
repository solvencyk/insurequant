---
from: downloader
to: parser
created: 20260902T1200Z
status: resolved
route: reparse
company: KR1098, KR0075, KR0150
period: 2023.4Q
rule: (raw-ready) DART 본문 XML census
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)

DART 본문 XML 을 39사 x FY2023_Q1..FY2026_Q2 = 546칸 전수 census 한 결과, **분기 공시사의
진짜 결손 3칸**을 찾아 받았다. 셋 다 2023.4Q 이고 전부 감사보고서다. raw ready.

| KR | 회사 | rcept | 경로 | 본문 |
|---|---|---|---|---|
| KR1098 | 카카오페이손해보험 | `20240329002933` | `data/dart/FY2023_Q4/raw/KR1098_카카오페이손해보험_20240329002933/` | `20240329002933_00760.xml` (385,373자) |
| KR0075 | 비엔피파리바카디프생명보험 | `20240403001384` | `data/dart/FY2023_Q4/raw/KR0075_비엔피파리바카디프생명보험_20240403001384/` | `20240403001384_00760.xml` (589,486자) |
| KR0150 | 서울보증보험 | `20240403001186` | `data/dart/FY2023_Q4/raw/KR0150_서울보증보험_20240403001186/` | `20240403001186_00760.xml` (878,776자) |

**내용검증은 끝냈다** — 셋 다 회사명(13/16/22회) · 기수(제3(당)기 / 제22(당)기 / 제57(당)기) ·
기준일 2023-12-31(12/9/16회) · 비교기 2022-12-31 · 재무제표 키워드 보유. 스캔본·빈 껍데기 아님.

### 파싱 시 알아 둘 것

- **zip 안에 본체 `<rcept>.xml` 이 없다.** 감사보고서라 `_00760.xml` 하나뿐이다
  (악사손해·신한이지 등 기존 연1회 공시사와 같은 형태). `*.xml` glob 이면 잡힌다.
- **카카오페이 `보험계약마진` 0회** — PAA 소액단기(자동차·여행) 특성이지 추출 실패가 아니다.
  `보험수익` 25 · `보험서비스비용` 17 · `재무상태표` 8 로 본문 자체는 정상.
- **서울보증 `보험계약마진` 2회** — 기존 "구조적 CSM-無" 판정과 일치. BS/준비금 쪽으로 볼 것
  (`재무상태표` 17 · `자본총계` 6).
- **KR0150 은 기존 기록을 부분적으로 뒤집는다.** 2026-08-19 발주 C 가 서울보증
  2023.1Q~2024.3Q 7분기를 `no_filing` 으로 확정했는데, 그건 **정기보고서(A001)만** 훑은
  결과였다. 2023.4Q 는 정기보고서는 없지만 감사보고서가 있다. 1~3분기 부재는 여전히 맞다
  (감사보고서는 연 1회).

### 요청

`IFRS17_BS` / `CSM_waterfall` / `PL_breakdown` 의 2023.4Q 그리드에서 이 3사가 결측이었다면
재추출해 채워 달라. 이미 다른 경로로 채워져 있으면 이 raw 와 대조만 하고 닫아도 된다.

### 참고 — 발주 원인이었던 "결측" 은 오탐이었다

이 census 는 "IFRS17_BS 를 원문과 대조하려는데 삼성생명/미래에셋생명 2026.2Q 원문이 아예
없다" 는 발주에서 출발했는데, **둘 다 멀쩡히 있다**(각 5.3MB·3.7MB). raw 리프가
`KR####_<DART canonical>` 인데 **DART canonical 이 K-ICS 원수사명과 다르다** —
`KR0069_삼성생명`(K-ICS 는 '삼성생명보험') · `KR0079_미래에셋생명`(K-ICS 는 '미래에셋생명보험').
**회사명으로 디렉터리를 찾으면 거짓 결측이 나온다. KR 코드로 키를 잡을 것.**

두 번째 함정도 같이 적어 둔다: `leaf/*.xml` 만 glob 하면 **64칸**이 "zip 만 있고 본문 없음"
으로 나오는데 전부 `leaf/xml/*.xml` 로 이미 풀려 있다. `extract_dart_zips.py` 가 인정하는
세 레이아웃(`*.xml` · `xml/*.xml` · `extracted*/*.xml`)을 다 봐야 한다.

**2026.2Q 는 분기 공시사 24사 전원 본문 확보돼 있고 내용검증도 24/24 통과했다** — 제NN기 ·
2026-06-30 마커(50~203회) · BS 키워드, 1.2M~22.3M자. 대조를 못 할 이유가 없다. 유일한
플래그는 NH농협손해인데 본문이 자기를 '농협손해보험' 이라 쓰는 것(리프는 'NH농협손해보험')
으로, 위와 같은 종류의 이름 함정이지 데이터 문제가 아니다.

재사용 경로자산: `python scripts/_probes/census_dart_body_xml.py` (진짜 결손 있으면 exit 1,
`--json` 으로 셀 판정 덤프).

## 답변 (parser/ifrs17, 2026-09-11)

**선행 발견**: 이 raw 는 이미 2026-09-02 세션(커밋 `fe3a20f`)이 일부 처리해 뒀다 —
IFRS17_BS +43행(3사 신규 원문 반영), PL_breakdown +64행(KR0075·KR1098 2023.4Q 스켈레톤).
이번 세션은 그 위에서 **21항목 전수 대조 + 잔여 결측 채움 + CSM 확인**을 했다.

### 결과표 (3사 × 3마스터, 2023.4Q)

| 회사 | IFRS17_BS(21항목) | CSM_waterfall | PL_breakdown |
|---|---|---|---|
| KR1098 카카오페이손해보험 | 15/21 원문 대조 EXACT MATCH, 신규 1칸 채움(item21=0, "-"표기 오독 아님), N/A 4칸(11/12/22/23, 원문에 해당 자산/부채 자체 없음), 준비금 4칸(5/6/7/8) 원문 키워드 0회로 기존 0/None 확정 | **정상 부재 확인** — `보험계약마진` raw 0회(PAA 소액단기, downloader 판정과 일치), `CSM_waterfall.json`에 이 회사 2023.4Q 행 자체 없음이 맞음(2024.4Q·2025.4Q 부터 실재) | 32항목 스켈레톤 이미 존재(값 채워진 건 14개), 대조 이상 없음 |
| KR0075 비엔피파리바카디프생명보험 | 13/18 원문 대조 EXACT MATCH(이익잉여금 1칸 480원 이내 기지 오차), 신규 5칸 채움(item10/11/13/20/24), item1·2(자산·부채총계)만 원문(비정정 rcept)과 마스터(vision-read, 2024.1Q/2024.3Q 비교열 3중교차확인) 사이 0.08%(2,411.95백만원) 불일치 — 마스터가 더 강한 근거라 유지, downloader 후속 확인 권장(아래) | **신규 6칸 채움** — §14(4) 측정요소별 변동내역(원수) 표에서 기초 257.511·신계약 18.131·이자부리 4.939·조정 148.174·상각 -86.846·기말 341.909(억원) 산출, 폐쇄검증 잔차 0, 2024.4Q 기초(341.909)와 EXACT 연속성 확인 | **item3~7 신규 5칸 채움**(같은 §14(4) 표에서 생명장기 원수손익 -10596.067·CSM상각 -8684.565·위험조정변동 -2624.504·예실차 -41152.756·플러그 41865.758, 백만원) — CSM_waterfall 갱신으로 새로 뜬 RED `PL_CSM_AMORT_VS_WATERFALL` 해소(item4 vs CSM item5 원단위 일치) |
| KR0150 서울보증보험 | **17/17 EXACT MATCH**(전 대조 가능 항목), 정밀도 개선 1칸(item6 비상위험준비금: 2,401,000.0→2,401,039.526, 경영공시 억원반올림→감사보고서 천원단위 정밀값, 억원단위 반올림 시 동일 수렴) | **정상 부재 재확인** — `보험계약마진` raw 2회 전부 회계정책 서술문(실제 표 아님), 기존 `user_csm_cells.json` exclude_companies 등재와 100% 일치 | **정상 부재**(기존 기록과 일치, 이 raw엔 계산서형 PL 표 없음) |

### 바뀐 파일
- `data/dart/viz/bs_manual_overrides.json`(2081→2087칸, 신규 6 + 정밀도교체 1) →
  `IFRS17_BS.json`(8840→8846행, `build_ifrs17_bs.py` 재실행)
- `data/_gold/user_csm_cells.json`(270→276개 set) → `CSM_waterfall.json`(2172→2178행,
  `build_root_masters.build_csm()` 개별 호출)
- `data/_gold/user_pl_cells.json`(198→203개 set) → `PL_breakdown.json`(11930행 불변,
  값만 5칸 교체, `build_root_masters.build_pl()` 개별 호출)
- `insurequant_master_tables.xlsx` 시트 3개 cherry-pick(`sync_master_xlsx_sheet.py "17BS"`/
  `"CSM워터폴"`/`"손익분해PL"`) — 전부 "검증 OK"
- `tests/fixtures/ifrs17_bs_golden.json`(`--update`, 8846행·39사, PASS 재확인 351초),
  `tests/fixtures/master_tables_golden.json`(`--update`, 의도된 P 증가만·0F, PASS 재확인)
- `tests/fixtures/builder_input_fingerprints.json`(ifrs17_bs·viz_ifrs17_panels 2개 항목만
  surgical 갱신 — pl_breakdown/dividend/post_transition 3개는 **kics 레인이 병행 수정 중인
  `kics_disclosure.json` 때문에 여전히 FAIL**, 내 작업과 무관해 손대지 않음)

### combo-diff (전부 LOST=0 확인)
- IFRS17_BS: GAINED=6(KR1098 item21, KR0075 item10/11/13/20/24) CHANGED=1(KR0150 item6)
- CSM_waterfall: GAINED=6(KR0075 items 1-6) CHANGED=0
- PL_breakdown: GAINED=0 CHANGED=5(KR0075 items 3-7, 전부 None→값)

### 게이트
`validate_data_contract.py`: 작업 시작 시 RED=6(내 변경으로 신규 RED `PL_CSM_AMORT_VS_
WATERFALL` KR0075 2023.4Q 1건 포함) → PL item3-7 채움으로 그 RED 해소 → xlsx 3시트 동기화로
MASTER_XLSX RED 4건 추가 해소 → **최종 RED=2(둘 다 K-ICS공시 시트 드리프트, kics 레인 소관,
미접촉)**. `validate_master_tables.py --no-build`: exit=2(관례상 정상, 등재된 pl_bridge
baseline 무변화) — golden 재생성으로 확인.

### 재현 명령
```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260911_verify_bs_kr3_2023q4.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260911_apply_bs_overrides_kr3.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/build_ifrs17_bs.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260911_apply_csm_override_kr0075.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260911_apply_pl_override_kr0075.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260911_run_build_csm_only.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260911_run_build_pl_only.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_data_contract.py
```

### 못 한 것
- **viz CSM 패널**(`data/dart/viz/csm_waterfall.json`)은 `CSM_waterfall.json`이 아니라
  `data/dart/extracted/*.json`(추출기 원본)을 별도로 읽는 파이프라인이라, 이번 gold-overlay
  값이 자동 반영되지 않는다. 화면에 KR0075 2023.4Q를 띄우려면 추출기 산출물 쪽도 별도 작업
  필요(범위 밖으로 남김).
- **KR0075 item1/2(자산총계/부채총계) 0.08% 불일치**는 확정 못 함 — DART 감사보고서 원 rcept
  (20240403001384, 비정정)가 마스터(3필링 교차확인 vision-read)보다 2,411.95백만원 작다.
  item3/4(자본총계/기타포괄손익)는 정확히 일치해 자산=부채+자본 양쪽에 같은 금액이 대칭으로
  얹힌 모양 — **정정공시 존재 가능성**을 의심한다. downloader가 KR0075 FY2023 정정(수정)
  공시 이력을 DART에서 확인해 주면 좋겠다(route: refetch 필요시 별도 티켓).
- KR0075 item1/2/8(보험손익·생명장기손익·재보험손익)는 출재(재보험) 부호관례를 이번 세션에서
  독립검증 못 해 미기입(item3-7만 채움).

status를 `answered`로 바꾼다 — sender(downloader) 재확인 바란다. 0.08% 불일치 건은 별도
route:refetch 필요 여부 판단 부탁.

## 종결 재확인

재확인(orchestrator, 2026-09-12): 마스터 실측 IFRS17_BS 8,840→8,846행(+6) · CSM_waterfall 2,172→2,178행(+6, KR0075 2023.4Q) · KR1098/KR0150 CSM 은 구조적 미해당 판정 유지. 부수: CSM 갱신으로 `NB_CSM_multiple.json` 이 KR0075 2023.4Q 행을 요구(`NB_CENSUS_MISSING` RED 1) → 빌더 재실행으로 +1행(362→363, 기존 행 변경 0), live_artifacts RED 0. 잔여(KR0075 자산·부채총계 0.08% 차 정정공시 여부)는 downloader 후속. **resolved.**
