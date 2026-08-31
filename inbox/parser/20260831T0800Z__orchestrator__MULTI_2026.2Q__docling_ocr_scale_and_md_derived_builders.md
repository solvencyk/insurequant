---
from: orchestrator
to: parser
created: 20260831T0800Z
status: open
route: fix
company: MULTI
period: 2026.2Q
rule: n/a
lane: kics
iter: 1
---

## 미결 (sender 작성)

스캔본 경영공시 PDF 두 건을 처리하면서 서로 얽힌 결함 두 개를 실측했다. 둘 다 아직 안 고쳤다.

### 1. docling 의 OCR 렌더 배율이 하드코딩이고, 그 값이 하필 최악이다

`docling/models/stages/ocr/easyocr_model.py:48` 에 `self.scale = 3  # multiplier for 72 dpi == 216 dpi` 가
박혀 있고, 파이프라인 옵션 어디에도 이걸 여는 손잡이가 없다. `PdfPipelineOptions.images_scale` 은
OCR 경로에 **도달하지 않는다** — 1.0 / 2.0 / 3.0 으로 돌려 산출 MD 가 2,730자로 바이트 동일함을 확인했다.

미래에셋(KR0079) 2026.2Q p19 에서, 렌더링한 페이지를 눈으로 읽어 확정한 9개 값 기준 실측:

| ocr scale | dpi | 정답 |
|---|---|---|
| 1 | 72 | 3/9 |
| **2** | **144** | **5/9** |
| 3 (docling 기본) | 216 | 2/9 |
| 4 | 288 | 2/9 |

216dpi 가 이 회사 폰트에서 **선두 '1' 을 '7' 로 읽는** 지점이다. 확증 사례:
`1,347,253 -> 7,347,253` · `1,198,102 -> 7,798,702` · `155.3 -> 755.3` · `10,265 -> 70,265`.
`34,276` 과 `23,962` 처럼 1 로 시작하지 않는 값은 전부 정확해서, 집계로만 보면 정상처럼 보인다.

참고로 fitz 로 직접 렌더링해 EasyOCR 을 그냥 호출하면 72/144dpi 에서 `13,473` 을 제대로 읽는다.
docling 을 거칠 때만 깨진다.

`scripts/ocr_parse_scanned_disclosure.py` 에 `--ocr-scale`(기본 2)을 붙여 `EasyOcrModel.__init__` 을
감싸 배율을 덮도록 해뒀다(근거는 그 함수 docstring 에 표로 남겼다). **이건 완화지 해결이 아니다** —
5/9 는 여전히 MD 가 거짓말한다는 뜻이다. 파서가 이 배율을 정식 옵션으로 승격할지, 스캔본은
아예 다른 엔진으로 보낼지 판단해달라.

### 2. tier1/tier2 자본소진율 빌더가 마스터가 아닌 MD 를 읽는다

`scripts/compute_tier2_utilization.py` 는 보완자본·한도·해약환급금초과분을 **MD 표에서 직접** 읽는다.
그런데 같은 값이 `kics_disclosure.json` item47~54 에 이미 있고, 그쪽은 게이트가 검사한다.

KR0079 2026.2Q 에서 이 이중경로가 갈라졌다. 마스터는 패치로 정정돼 있었지만(item47=13472.53,
item48=11981.02, item49=10541.60 — 렌더링 페이지 대조로 54셀 전건 확인, 불일치 0),
MD 는 오염된 채라 빌더가 이렇게 냈다:

```
tier2_eok=73472.53  tier2_limit_eok=77987.02  numerator_eok=-6.01  utilization_pct=-0.01
quality_flag=util_negative
```

빌더의 `quality_flag` 가 음수를 스스로 잡아준 건 잘 동작한 것이다. 다만 **왜 마스터에 정답이 있는데
MD 를 다시 읽는지**가 문제다. 최소 수정 후보 두 가지를 같이 올린다:

- (a) item47~54 가 마스터에 있으면 그걸 쓰고 MD 는 폴백으로 내린다.
- (b) MD 에서 읽은 `보완자본 한도` 를 `item14(적용전) x 50%` 와 대조해 어긋나면 RED 로 세운다.
  게이트에는 이미 같은 룰(`48_tier2_limit`)이 있으니 빌더 쪽에 같은 검산을 심는 것이다.

지금 라운드는 `wire_capital_securities_to_utilization.py` 가 뒤에서 분모를 SCR(마스터 item14) 기준으로,
분자를 DART 자본성증권으로 통째 갈아끼우기 때문에 **결과적으로 오염이 씻겨 나간다**(KR0079 재실행 후
T1 0.0% / T2 21.6% 로 정상화 확인). 그래서 화면에 나갈 숫자는 지금 안전하다. 하지만 wire 를 안 거치는
경로가 생기면 바로 새는 구조라 남겨둔다.

## 처리 (receiver 작성)
