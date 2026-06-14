---
from: validation
to: parser
created: 20260609T0100Z
status: resolved
route: reparse
company: KR0009
period: 2023.1Q
rule: WITHIN_FY_OPENING_DRIFT
iter: 1
---

## 미결 (sender 작성)
현대해상 (KR0009) WITHIN_FY_OPENING_DRIFT — FY2023 기초 CSM 변동 83515~88281 (>5%) — 분기 간 basis/period mis-pick 의심

### 마스터(CSM_waterfall.json)에서 본 값 + 내부 정합
FY2023 내 분기별 기초 CSM (YTD opening, 항등식상 연중 상수여야 함):
- 2023.1Q: 기초=88281.1
- 2023.2Q: 기초=88281.1
- 2023.3Q: 기초=83515.4
- 2023.4Q: 기초=83515.4

각 분기 내부 closing-identity (기초+신+이+가+상 vs 기말):
- 2023.1Q: OK (기초88281.1+신4946.7+이653.8+가-2509.5+상-2163.5=89208.6 vs 기말89208.6, Δ0.0)
- 2023.2Q: OK (기초88281.1+신9542.1+이1339.0+가-3391.1+상-4410.3=91360.8 vs 기말91360.8, Δ0.0)
- 2023.3Q: OK (기초83515.4+신13221.4+이1929.8+가-3226.2+상-6403.8=89036.6 vs 기말89036.6, Δ-0.0)
- 2023.4Q: OK (기초83515.4+신16792.4+이2636.3+가-2714.9+상-8805.5=91423.7 vs 기말91423.7, Δ0.0)

### 요청
1. extracted_history(또는 extracted)에서 현대해상 해당 분기 CSM raw를 glob/재독.
   - 힌트: `data/dart/extracted_history/*현대해상*csm.json` (이름 부분일치 허용)
2. 위 내부 closing-identity가 OK면 = 워터폴 내부정합 → break는 '오차'가 아니라
   불연속(연도경계/별도·연결/재진술 후보). raw에 기초행을 가진 **롤포워드(변동표)**가
   있으면 그 기초값으로 앵커 확인. 없으면 앵커 불가.
3. 분류해서 회신: real_error(앵커된 수정 가능) / justified_restatement(raw·주석상
   정당한 기초 재작성) / no_anchor(내부정합이나 롤포워드 부재로 판정불가→사람·2nd소스) /
   refetch(raw 누락).

## 답변 (recipient 작성 — 처리 후)

**verdict: justified_restatement**

**롤포워드 존재 여부: YES** — 단, `*_csm.json`이 아니라 `*_measurement.json`에 있음.
`현대해상__2023.NQ_csm.json` 4개 파일은 전부 **상각 스케줄(연차 버킷)** 표(caption
"보험계약마진 상각 스케줄", header "1년이하/1년초과2년이하/.../합계")만 담고 있어 기초행이
없다. 그러나 `현대해상__2023.NQ_measurement.json`에는 원수 보험계약 CSM **변동표(롤포워드)**
가 있고 `전기말 보험계약마진`(=기초) / `당기말 보험계약마진`(=기말) 행으로 기초값을 앵커할 수 있다.

**원수 gross 전기말(기초) CSM 합계 (measurement 롤포워드, 단위 KRW):**
- 2023.1Q: 8,828,108,048 → 마스터 기초 88281.1 ✓
- 2023.2Q: 8,828,108,048 → 마스터 기초 88281.1 ✓
- 2023.3Q: 8,351,539,177 → 마스터 기초 83515.4 ✓
- 2023.4Q: 8,351,539,177 → 마스터 기초 83515.4 ✓

(마스터 단위는 raw의 1/10 스케일이나 비율 정확 일치. 4개 분기 모두 해당 분기 공시 롤포워드의
`전기말 보험계약마진` 합계를 그대로 복사한 것 — mis-pick 아님.)

**근본원인 (root cause):** 마스터 오선택이 아니다. 현대해상이 **FY2022 기말 CSM를
1H2023 공시(8,828,108,048)에서 Q3 2023 공시 이후(8,351,539,177)로 재진술(restatement)**
했다. 이 재진술값 8,351,539,177은 3Q/4Q 상각스케줄의 `2022년 12월 31일` 비교열 합계로도
동일하게 등장 → 별도/연결 swap이나 연도경계 오프셋이 아니라 전년말 수치의 의도적 재작성 확정.
각 분기 내부 closing-identity(기초+신+이+가+상=기말)도 4개 분기 모두 OK → 워터폴 내부정합 정상.

**proposed corrected opening:** n/a (수정 대상 단일값 없음). 마스터는 공시대로 유지해야 함:
1H = confirmed 88281.1, 2H = confirmed 83515.4. WITHIN_FY_OPENING_DRIFT는 정당한 재진술로
인한 것이므로 이 회사/FY에 대해 **문서화된 예외(documented exception)** 로 처리 권고.

## 종결 (validation 2026-06-14)
현대 FY2023 = legit_restatement documented(WFY_EXCEPTIONS, parser raw확인) → resolved
