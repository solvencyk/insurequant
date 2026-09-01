---
from: orchestrator
to: parser
created: 20260901T1314Z
status: resolved
company: MULTI
period: MULTI (2023.1Q~2026.2Q)
rule: 19_market
lane: kics
---

## 미결 (sender 작성)

`status_report.py --fast` 가 시장위험 항목36-40 을 5개 항목 전부 "400/538 버킷"으로 찍는다
(138칸 결측, ×5항목=690셀). 오늘(2026-09-01) `scripts/fill_market_subitems_to_disclosure.py::
extract_mkt_subs()` 의 총계행 라벨 정규식(`_is_total_row_label`)을 고쳐 2026.2Q MD-마스터
재현율이 21→32/39사로 올랐다 — 그 개선이 과거 분기 138칸에도 적용되는지 재라. 138칸을
(a) MD 에 표는 있는데 추출 실패 / (b) MD 엔 없지만 raw PDF 엔 있음(윈도드롭) / (c) 원문에도
없음(간이공시 등, 정상부재) 로 기계 분류하고, (a)는 채우고 (b)는 원인규명, (c)는 분류만.
538 이라는 분모가 짝수/홀수분기 공시주기(cadence)를 반영한 것인지부터 확인.

## 답변 (recipient 작성 — 처리 후)

**분모(538)가 cadence 를 반영하지 않는 게 근본원인이었다 — 진짜 결측은 0칸이다.**

`status_report.py` 의 항목36-40 census 는 `len(idx)`(전체 (회사,분기) 버킷, 홀수분기 포함)를
분모로 썼다. 반면 바로 옆 항목41-46(금리시나리오)은 이미 `even`(짝수분기)만 분모로 쓴다
(`완비 270/273`). **같은 원본이 같은 코드 안에서 짝수분기만 재는 축과 전체를 재는 축으로
따로 존재**했던 것 — 41-46 기준을 그대로 36-40 에 적용하면 분모가 538 이 아니라 270 이어야
한다.

**census 실측** (`scripts/_probes/probe_20260901c_market_bucket_census.py`,
`probe_20260901c_market_bucket_census2.py`):
- 전체 538 버킷 = 짝수분기 270 + 홀수분기 268.
- **짝수분기 270/270 결측 0** (item36-40 다섯 항목 전부 100%). 138칸은 **전량 홀수분기**(1Q/3Q,
  간이공시)에서만 나온다.
- 홀수분기 268 버킷 중 **130개는 이미 채워져 있다**(25개사가 회사 재량으로 1Q/3Q 에도 세부표를
  공시 — 예: 롯데손해·하나손해·한화손해·교보생명 등). 138개만 결측.
- 138 결측을 회사별로 쪼개면: **11개사(72칸)는 그 회사의 홀수분기 이력 전체(全)에서 item36 이
  단 한 번도 없음**(삼성생명·삼성화재·한화생명·신한라이프·서울보증·DB생명·KB라이프·동양생명·
  라이나생명·미래에셋생명·AIG손해) — 처음부터 홀수분기 세부표를 안 하는 회사군. **14개사
  (66칸)는 일부 홀수분기엔 있고 특정 분기만 빔**(대부분 "2023.3Q만 있고 나머지 전부 없음" —
  K-ICS 1년차 특수공시로 보임) — 이쪽이 진짜 gap 후보.

**(a)/(b)/(c) 전수 판정** (`scripts/_probes/probe_20260901c_full_classify.py`, 138칸 전부
MD + raw PDF 양쪽 다 fitz 로 직접 열어 "OO위험액 현황" 헤딩 유무 검사 + 오늘 고친
`extract_mkt_subs()` 그대로 실행):

```
C_GENUINE_ABSENT              137   (MD 도 raw PDF 도 세부표 헤딩 0회 — 원문 자체에 없음)
A_MD_HAS_DATA_BUT_GATE_FAILS    1   (하나손해 KR0050 2026.1Q, 아래 참조)
A_EXTRACTABLE_NOW               0
B_PDF_HAS_HEADING_MD_DOESNT     0
```

독립검증으로 `fill_market_subitems_to_disclosure.py --dry-run --all-periods`(오늘 고친 정규식
그대로, 14개 분기 전체)를 돌렸더니 **TOTAL new rows: 0** — 두 방법이 같은 결론으로 수렴한다.
표본으로 삼성생명·한화생명·AIG손해·KB라이프 2024.1Q MD 를 열어보면 "금리위험액"/"주식위험액"
문자열은 있으나 전부 "④경과조치 종류 선택여부" 표의 행 라벨("금리위험액증가분점진적인식" 등)
이지 세부표가 아니다. 삼성생명 2024.1Q raw PDF(34p, 간이공시 분량)도 p15 에 "3.시장위험액
240,617"(=item19, 상위총계) 한 줄만 있고 36-40 분해표는 34페이지 전체에 없다 — 원문에 없는
게 맞다(직접 확인).

유일한 예외 하나손해보험(KR0050) 2026.1Q: `extract_mkt_subs()`가 item36=45,541백만(455.41억)을
주웠지만 19_market 게이트(item19 대비 rel<2%)가 이미 막았다(불일치라 저장 안 됨, 데이터 오염
없음). 원인은 MD "③주식위험 경과조치 또는 금리위험 경과조치" 표의 "금리위험" 행(다른 표, 경과
조치 시나리오 위험액)을 `_bare_subrisk_item`이 짧은 무헤더 라벨로 오매칭한 것 — 기존 게이트가
정확히 설계대로 걸러냈다. 실피해 0건이라 패치 불필요, 다만 `_bare_subrisk_item`을 "④/③경과
조치" 절 컨텍스트에서 제외하도록 강화하면 향후 유사 오탐을 원천봉쇄할 수 있음(낮은 우선순위로
남김, 코드 미수정).

**채운 칸: 0개. 패치 스크립트: 없음** — (a)/(b) 후보가 0개라 UPSERT할 값 자체가 없다("틀린
값을 싣느니 빈 칸" 원칙과 정확히 일치, 138칸은 실제로 원문에 없는 값이라 비워두는 게 맞다).

**실제로 고친 것은 데이터가 아니라 지표**: `scripts/status_report.py::axis_coverage()` 의
항목36-40 분모를 41-46 과 동일하게 짝수분기(`even`)로 맞추고, 홀수분기 자율공시 카운트를
참고용으로 병기했다. 이 화면 숫자는 화면 그래프가 아니라 진단 스크립트 출력이라 배포 게이트와
무관, kics_disclosure.json 은 건드리지 않음(동시세션 lost-update 리스크 없음).

**재현**:
```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/status_report.py --fast
  # 5. 축별 커버리지 → 시장위험 항목36-40 = "완비 270/270 (100.0%) [짝수분기만 공시;
  #    홀수분기 자율공시 130/268]"
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/fill_market_subitems_to_disclosure.py --dry-run --all-periods
  # TOTAL new rows: 0
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260901c_full_classify.py
  # C_GENUINE_ABSENT: 137 / A_MD_HAS_DATA_BUT_GATE_FAILS: 1 / 나머지 0
```

**게이트**: `kics_disclosure.json` 무변경이라 `validate_kics_disclosure.py` 재실행 불필요(이미
RED=0 인 상태 그대로). `status_report.py` 는 골든 테스트 대상 아님(`tests/`에 참조 0건),
ast.parse+BOM 확인 통과.

**결론**: 오늘 고친 정규식은 이 138칸엔 적용 대상이 없었다 — 그 개선(21→32/39사)은 순수
provenance(2026.2Q MD 가 기존 마스터값을 재현하는지) 문제였고, 이 138칸은 애초에 마스터에도
없고 원문에도 없는 진짜 정상 결측(간이공시 cadence)이었다. status: resolved(자기완결 —
재작업 대상 없음, 지표만 수정, 데이터 무변경).
