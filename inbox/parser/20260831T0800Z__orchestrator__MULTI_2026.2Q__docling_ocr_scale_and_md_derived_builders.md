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

## 검증 메모 (validation, 2026-09-01 10:16~10:26 KST — **티켓은 open 유지**)

**두 결함 다 코드 상태가 티켓 작성 시점 그대로다. 아무것도 바뀌지 않았다.**

### 1. OCR 배율 — 여전히 로컬 우회

`scripts/ocr_parse_scanned_disclosure.py` L37-66·L94-98 에 `--ocr-scale`(기본 2)과
`EasyOcrModel.__init__` 몽키패치가 그대로 있다. 이것은 티켓이 "이미 해뒀다"고 적은 완화책
자체이고, 파서에게 물은 판단(**정식 옵션으로 승격할지 / 스캔본을 다른 엔진으로 보낼지**)은
아직 답이 없다. `grep -rn "ocr_scale|EasyOcrModel" scripts/ src/` 결과가 이 파일 한 곳뿐 —
정규 파이프라인(`src/solvency/parser/docling_parser.py`)에는 손잡이가 없다.
144dpi 에서도 **5/9** 라는 티켓의 실측이 그대로 유효하다면, 스캔본 MD 는 여전히 거짓말을 한다.

### 2. tier2 빌더가 마스터 대신 MD 를 읽는 문제 — (a)·(b) 둘 다 미반영

`scripts/compute_tier2_utilization.py` 실측:

- L13 `MD_DIR = REPO / "md_inbox" / "FY2025_Q4"` — 기본 MD 디렉터리가 아직 **FY2025_Q4** 다.
- 값의 1차 소스는 여전히 MD 표(`_extract_common_table(md_path.read_text(...))`, L371).
- 마스터는 `proxy` 로만 쓰이는데 그것도 **item3·item14 뿐**이다(L373-376:
  `proxy_limit = proxy_item14 * 0.5`). 티켓이 지목한 **item47~54 를 읽는 코드가 없다**
  (`grep -n "'47'|\"47\"" scripts/compute_tier2_utilization.py` 무출력).
- 제안 (b)의 검산(MD 의 `보완자본 한도` vs `item14 x 50%` 대조 후 RED)도 없다 — `proxy_limit`
  은 MD 값과 대조되지 않고, MD 표가 있으면 MD 쪽이 그대로 쓰인다.

티켓이 지적한 대로 지금은 `wire_capital_securities_to_utilization.py` 가 뒤에서 분모·분자를
갈아끼워 화면 숫자는 안전하다(2026.2Q 산출 39행 모두 `numerator_as_of` 포함 정상). 그래서
**차단 사유는 아니지만**, wire 를 거치지 않는 경로가 생기면 바로 새는 구조가 그대로 남아 있다.

**남은 것 한 줄**: `--ocr-scale` 의 정식화 여부 판단이 미답이고,
`compute_tier2_utilization.py` 는 아직 마스터 item47~54 를 안 읽으며(제안 a) MD 한도와
`item14x50%` 대조 검산도 없다(제안 b). **담당: parser (kics lane).**
