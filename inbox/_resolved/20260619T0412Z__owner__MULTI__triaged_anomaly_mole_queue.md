---
from: owner
to: parser
created: 20260619T0412Z
status: resolved
route: backlog
company: MULTI
period: ALL
lane: ifrs17
iter: 1
---

## 미결 (owner) — triaged anomaly 모래 큐 (CSM_waterfall / PL_breakdown)

data-contract CHECK 5(generic 스캐너)가 192 후보 → `scripts/triage_anomaly_candidates.py`가 own-history+YTD 정규화로 **81개로 압축**(111 노이즈 자동 억제). 큐 = **`data/_derived/anomaly_triage.json`**.

**1순위 — COHORT_ZERO (명백한 추출누락, fix):** 0일 수 없는 항목이 특정 분기만 0(다른 분기는 nonzero):
- `교보생명 원수예실차 = 0` (2024.4Q·2025.1Q·2025.4Q·2026.1Q; 다른 5분기 nonzero, 자기 median ~25,905)
- `카카오 기초CSM = 0` (2024.4Q; 이미지사)
- 그 외 COHORT_ZERO=REAL 전부 (`verdict:"REAL", rule:"COHORT_ZERO"`) → 재추출/소스확인.

**2순위 — PEER_OUTLIER (verify, 78건):** 자기 같은-분기 median 대비 3× 이탈. **진짜 경제적 급변 vs 추출/단위 오류** 구분 필요(소스 대조). 예: NH농협 보험손익 2025.1Q −1833 (자기 1Q median 47052) — 단위 일관성도 의심. json의 `reason`·`own_qpos_median` 참조.

### 주의
- python 풀패스 `C:\Users\sangwook.cho\venvs\insurequant\Scripts\python.exe`. 인라인 멀티라인 `python -c` 금지. `build_csm_waterfall_master.py` 금지.

## ⚡ skeptic 정밀화 (2026-06-19) — 78+3 → **10 actionable만 처리**
LLM-skeptic이 81을 최종판단: 67 REAL_EVENT(통과)·4 NOISE·**9 EXTRACTION + 1 UNIT = 10건만 fix**. verdict 전문 `data/_derived/anomaly_skeptic_verdict.json`. **아래 10건만 처리하면 됨:**

**high (우선):**
- 교보생명 원수예실차 = 0 (2024.4Q·2025.1Q·2025.4Q·2026.1Q; 타분기 19,583/-25,905) — 행 미캡처 ×4
- 삼성화재 2026.1Q 자동차손익 = -40 (국내 최대인데 이력 ±120k~183k) — 셀/컬럼 미스파싱
- BNP파리바카디프 2025.4Q 원수위험조정변동 = 1,768,401백만(1.77조) — /100=17,684가 cohort 정합 → **단위오류**

**med/low:**
- 코리안리 2026.1Q 기타생명장기재보험손익·기타장기재보험출재손익 = 둘 다 43 (다른 항목 동일값 = 중복 추출) ×2
- 신한이지 2025.4Q · 교보라이프플래닛 2024.4Q 보험금융손익 = 0 (비교분기 1개뿐, low)

## 답변 (recipient 작성 — 처리 후)

부분처리 2026-06-20 (parser-ifrs17, open 유지): skeptic 10 actionable 중 — 교보 원수예실차·BNP 단위오류·코리안리 중복43 = **owner 직접정정분(0811Z)으로 durable override 반영 완료**(소실방지). 삼성화재 자동차손익 2026.1Q=-40 = **owner 확인결과 실제 작은값 정답=pass**(에러아님). 신한이지/교보라플 보험금융손익 0 = 교보라플(KR1010)은 owner fill로 -21,827 정정됨; 신한이지 item19는 raw 미보유(KR0051 FY2025_Q4 부재)→downloader. 흥국화재 기타사업비=item16=0 룰(noise). 잔여 PEER_OUTLIER 다수는 REAL_EVENT.

**후속 확인 2026-07-30 (parser-ifrs17)**: 신한이지(KR0051) raw 재확인 — 6주 전과 동일하게 여전히
`meta.json`만 존재(FY2025_Q4 디렉터리 자체 없음), downloader 발주가 실제로는 안 나가 있었음(의도만
기록되고 누락) → 이번에 실제 발주함(`inbox/downloader/20260730T0110Z__parser__KR0051_FY2025__shinhanez_raw_fetch.md`).
이 10건 큐는 이걸로 전부 disposition 완료(신한이지만 raw 대기, 나머지 9건 종결).

---

### 종결 (owner status-sweep, 2026-08-20)

skeptic 10건 큐 전부 disposition 완료. 마지막 잔여였던 신한이지 raw는 2026-07-30에 실제 발주(20260730T0110Z), 해당 티켓 _resolved 확인.
