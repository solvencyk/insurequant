---
from: orchestrator
to: parser
created: 20260901T2000Z
status: open
route: reparse
company: KR0050,KR0076,KR1098
period: 2023.4Q-2025.4Q
rule: INSPL_CENSUS_MISSING (live_artifacts)
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)

owner 승인(2026-09-01)으로 **PL 마스터에 3사가 새로 들어왔다** — 하나손해보험(KR0050) ·
아이엠라이프생명보험(KR0076) · 카카오페이손해보험(KR1098). 회사수 36 → 39.

그런데 **보험손익 원표 패널(`data/dart/viz/insurance_pl_breakdown.json`)이 이 3사를 모른다.**

```
RED  insurance_pl_breakdown.json :: INSPL_CENSUS_MISSING  아이엠라이프생명보험
RED  insurance_pl_breakdown.json :: INSPL_CENSUS_MISSING  카카오페이손해보험
RED  insurance_pl_breakdown.json :: INSPL_CENSUS_MISSING  하나손해보험
```

### 왜 안 따라왔나

패널 빌더 `scripts/viz_build_ifrs17_panels.py` L1631 이 이 패널을 **PL 마스터가 아니라**
`data/dart/extracted/*_insurance_pl_mvp.json` 에서 만든다:

```python
"insurance_pl_breakdown.json": ("*_insurance_pl_mvp.json", extract_pl_breakdown),
```

그 mvp 파일은 `scripts/ifrs17_ingest_audit_annual.py` 가 만드는데, 현재 47개가 있고
**KR0050 · KR0076 · KR1098 것은 없다.** 즉 PL 마스터 경로와 패널 경로가 서로 다른
추출기를 쓰고 있고, 마스터에 회사를 추가해도 패널은 자동으로 안 따라온다.

**값이 틀린 것이 아니라 커버리지가 안 따라온 상태다.** 그래서 화면에서 이 3사는 PL 관련
어떤 자리에는 나오고 보험손익 원표에는 안 나온다.

### 지금 조치 (임시)

`data/_gold/live_artifact_baseline.json` 에 3줄 등재해 push 를 풀었다. 통째 skip 이 아니라
건별 등재이고, mvp 추출이 생기면 게이트가 `BASELINE STALE` 로 알려준다 — **그때 그 줄을
지워야 한다**(안 지우면 등재부가 거짓말을 시작한다).

### 부탁

1. 3사의 `*_insurance_pl_mvp.json` 을 만들어 달라(`ifrs17_ingest_audit_annual.py` 경로).
   회사마다 표 형태가 다르다는 것은 이미 확인됐다 — PL 마스터 쪽에 각각 독립 핸들러를 짰다
   (`_hana_sonbo_*` · `_imelife_*` · 카카오페이, `scripts/pl_breakdown/companies.py`). 그 로직이
   참고가 될 것이다.
2. 만든 뒤 `viz_build_ifrs17_panels.py` 재실행 → `validate_live_artifacts.py` 가
   `BASELINE STALE` 을 인쇄하면 등재부 3줄을 지워라.
3. 근본적으로 **PL 마스터 경로와 패널 mvp 경로가 갈라져 있는 것 자체**가 이 사고의 원인이다.
   회사를 추가할 때 둘이 같이 움직이도록 묶을 수 있는지 검토해 달라 — 지금은 한쪽만 늘려도
   게이트가 잡아 주긴 하지만, 잡히기 전까지는 화면이 불일치한다.

재현:
```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_live_artifacts.py
```

## 답변 (recipient 작성 — 처리 후)
