---
from: validation
to: parser
created: 20260609T0100Z
status: resolved
route: escalate
company: KR0099
period: 2024.1Q
rule: WITHIN_FY_OPENING_DRIFT
iter: 1
---

## 미결 (sender 작성)
KB라이프생명 (KR0099) WITHIN_FY_OPENING_DRIFT — FY2024 기초 CSM 변동 30176~31798 (>5%) — 분기 간 basis/period mis-pick 의심

### 마스터(CSM_waterfall.json)에서 본 값 + 내부 정합
FY2024 내 분기별 기초 CSM (YTD opening, 항등식상 연중 상수여야 함):
- 2024.1Q: 기초=30176.4
- 2024.2Q: 기초=30176.4
- 2024.3Q: 기초=30176.4
- 2024.4Q: 기초=31798.3

각 분기 내부 closing-identity (기초+신+이+가+상 vs 기말):
- 2024.1Q: OK (기초30176.4+신1313.6+이349.8+가-239.2+상-714.3=30886.3 vs 기말30886.4, Δ-0.1)
- 2024.2Q: OK (기초30176.4+신2273.9+이681.3+가-249.8+상-1435.8=31446.0 vs 기말31446.0, Δ0.0)
- 2024.3Q: OK (기초30176.4+신3729.8+이898.7+가-990.8+상-2161.5=31652.6 vs 기말31652.7, Δ-0.1)
- 2024.4Q: OK (기초31798.3+신5013.0+이1230.7+가-5006.1+상-2930.8=30105.1 vs 기말30105.1, Δ0.0)

### 요청
1. extracted_history(또는 extracted)에서 KB라이프생명 해당 분기 CSM raw를 glob/재독.
   - 힌트: `data/dart/extracted_history/*KB라이*csm.json` (이름 부분일치 허용)
2. 위 내부 closing-identity가 OK면 = 워터폴 내부정합 → break는 '오차'가 아니라
   불연속(연도경계/별도·연결/재진술 후보). raw에 기초행을 가진 **롤포워드(변동표)**가
   있으면 그 기초값으로 앵커 확인. 없으면 앵커 불가.
3. 분류해서 회신: real_error(앵커된 수정 가능) / justified_restatement(raw·주석상
   정당한 기초 재작성) / no_anchor(내부정합이나 롤포워드 부재로 판정불가→사람·2nd소스) /
   refetch(raw 누락).

## 답변 (recipient 작성 — 처리 후)

**verdict: justified_restatement** (route: escalate — 파서가 고칠 것 없음, 사람 큐에 문서화 권고)

**raw에 롤포워드(변동표) 있었나?** YES — `csm.json`이 아니라 `*_measurement.json`에 있음.
csm.json은 4개 분기 모두 '향후 기간별 예상상각금액'(연도-버킷 스케줄)만 있고 기초행 없음.
앵커는 measurement 파일의 측정요소별 변동내역(direct, whole_company_life)의
보험계약마진 컬럼 기초/기말 행에서 확보.

**근본 원인 (1-3줄):**
워터폴 내부정합(검증기 PRECOMPUTED)이 4개 분기 모두 OK이므로 break는 '오차'가 아니라
**기중 재진술(restatement)**임. KB라이프(케이비라이프생명보험)는 FY2023 기말 = FY2024 기초
발행 CSM를 분기보고서/연차보고서 간에 상향 재작성했고, 두 값 모두 별도 변동표로 앵커됨.
마스터의 1Q-3Q(30176.4)와 4Q(31798.3)는 **둘 다 옳음** — 각각 당시 공시 원본을 충실히 반영.

**raw 앵커 증거 (발행 보험계약, 보험계약마진 컬럼, 단위 백만원):**
- FY2023 연차(2023.4Q measurement): FY2023 기말 = **3,017,642** → 30,176.42 억 → 마스터 1Q-3Q 기초 30176.4 와 일치.
- FY2024 1Q measurement: 기초 순장부금액 = **3,017,642** (= 30,176.4), 분기말 = 3,088,637 (= 30,886.4). → 1Q 기초 앵커 확인.
- FY2024 연차(2024.4Q measurement): 당기 기초 순장부금액 = **3,179,826** → 31,798.26 억 → 마스터 4Q 기초 31798.3 과 일치.
  같은 표의 전기(FY2023) 기말 = **3,179,825** 로 재작성되어 4Q 기초와 내부 tie 성립.
- 재작성 금액: 3,179,826 − 3,017,642 = 162,184 백만 = **1,621.84 억** ≈ 마스터 drift (31798.3 − 30176.4 = 1621.9). 정확히 일치.

**제안 기초값 (proposed_opening):** confirmed — 변경 없음.
1Q-3Q 기초 = **30176.4** (confirmed, 원공시), 4Q 기초 = **31798.3** (confirmed, 재진술 후).
real_error 아님 (mis-pick·별도/연결 swap·off-by-year 없음). refetch 불필요 (raw 정상).

**사람 큐 권고:** TODO.md K-ICS/IFRS17 예외 목록에 (KR0099, FY2024, WITHIN_FY_OPENING_DRIFT,
"interim→annual CSM opening restatement +1621.9억, both values anchored by measurement 변동표")
로 documented exception 등록 → 게이트 통과 처리.

## 종결 (validation 2026-06-14)
KB라이프 FY2024 = 사업결합 재작성 documented → resolved
