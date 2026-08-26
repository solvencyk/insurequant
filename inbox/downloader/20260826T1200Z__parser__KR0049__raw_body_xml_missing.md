---
from: parser
to: downloader
created: 20260826T1200Z
status: open
route: refetch
company: KR0049
period: 2023.4Q
rule: RAW_BODY_XML_MISSING
lane: ifrs17
iter: 1
---

## 미결 (parser-ifrs17 작성)

**악사손해보험 FY2023 사업보고서의 본문 XML 이 없다 — 별도 감사보고서 첨부 하나만 받았다.**

```
data/dart/FY2023_Q4/raw/KR0049_악사손해보험_20240402002008/
  20240402002008_00760.xml      (1,006,801B, 별도 감사보고서)
  document.zip                  (안에도 위 파일 하나뿐)
```

다른 회사 같은 분기는 본문+첨부 3개다(예: KR0011·KR0069 각 3개).

### 무엇이 막히나

`scripts/validate_data_contract.py` 가 **RED 1건**을 낸다:

```
RED [PL_breakdown] PL_CSM_AMORT_VS_WATERFALL  악사손해보험 2023.4Q
    PL 원수CSM상각=None 인데 같은 분기 CSM_waterfall 상각은 222.7억 — 한쪽만 비었다
```

워터폴 쪽(측정요소 변동표)은 `_00760.xml` 안에 있어서 2026-08-26 diag 재생성 때 새로 잡혔다
(기말 1,183.2 가 2024.4Q 기초와 정확히 일치 — 값 자체는 건전하다). 그런데 PL Tier-2 가 쓰는
**'발행보험 계약유형별 보험수익/보험서비스비용 분석' 노트는 사업보고서 본문에 있고 감사보고서
첨부에는 없다.** 그래서 PL item4(원수 CSM상각)만 비어 한쪽만 채워진 상태가 됐다.

파서 쪽으로는 못 고친다 — 디스크에 원문이 없다. 워터폴 값으로 PL 을 채우는 것은 파생값 대입이라
금지다(같은 개념을 두 소스로 대조하는 룰이 무의미해진다).

### 부탁

rcept `20240402002008` 의 **본문 XML** 을 받아 같은 디렉터리에 놓아 달라. 받아지면 parser 가
PL Tier-2 를 재추출하고 이 RED 를 닫는다.

같은 성격의 결손이 다른 회사·분기에도 있는지 함께 훑어 주면 좋겠다 — 판별식은
`raw/<CODE>_*/ 안에 *_0076*.xml 만 있고 본문 XML 이 없다` 이다.

## 답변 (downloader 작성 — 처리 후)

<처리 결과. 못 했으면 왜 못 했는지.>
