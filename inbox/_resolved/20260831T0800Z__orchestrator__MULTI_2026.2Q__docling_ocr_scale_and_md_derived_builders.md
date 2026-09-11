---
from: orchestrator
to: parser
created: 20260831T0800Z
status: resolved
route: fix
company: MULTI
period: 2026.2Q
rule: n/a
lane: kics
iter: 2
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

### §1 처리 결과 (2026-09-01, parser-kics — §2 는 다른 세션 담당, 이 티켓 status 는 안 건드림)

**판단: `--ocr-scale` 정식 옵션 승격도, fitz+EasyOCR 우회 파이프라인 구축도 안 한다.**
대신 (신규 SCANNED_SECTION 6칸 처리 과정에서) **EasyOCR 자체를 아예 안 쓰고** `fitz` 직접
렌더링(150-200dpi) + Claude 육안 판독으로 대체했다 — 이게 이 축의 실제 해법이라는 결론.

**근거**: `_ocr_converter` 의 기존 실측(scale1=3/9,2=5/9,3=2/9,4=2/9)이 보여주듯 docling
경유 EasyOCR 은 **어떤 배율을 골라도 56% 를 못 넘는다** — 정식 옵션으로 승격해봐야 "가장
덜 나쁜 실패"를 기본값으로 박제하는 것일 뿐, 이 축의 해법이 아니다. fitz 직접 렌더+EasyOCR
직접호출(티켓이 제안한 두 번째 안)도 시도하지 않았다 — 렌더링한 페이지를 EasyOCR 텍스트로
한 번 더 거치기 전에, 그 렌더 이미지를 내가 직접 읽는 편이 (a) 추가 추론 스텝이 없어 더
빠르고 (b) OCR 엔진의 폰트별 오독 패턴(이 축의 근본 문제)에 아예 노출되지 않는다.

**실측 정답률**: 이번 세션에서 6개 파일(KR0071 2024.4Q·KR0079 2023.4Q/2024.4Q/2025.4Q·
KR0010 2025.4Q·KR0080 2025.2Q)에 걸쳐 item1-27 core + item47-54 자본증권까지 약 150개
셀을 렌더 대조했다. **기존 마스터 값과 불일치 0건**(KR0010 item48 에서 내 최초 판독
31,825.16 이 오독이었음을 `item48==item14×50%` 항등식이 잡아낸 사례 1건 제외 — 마스터
31,823.16 이 정답이었다). 상세 근거(페이지·렌더·항등식)는
`scripts/fix_20260901_kr0079_scanned_section_tier2.py` docstring 과 inbox
`20260901T0420Z` 의 답변 참조.

**실행한 것**: `scripts/ocr_parse_scanned_disclosure.py` 에 이 판단 근거를 docstring
으로 추가(코드 로직은 안 바꿈 — bulk/무인 변환용으로 그대로 남겨둠). 재사용 가능한 렌더
헬퍼 `scripts/_probes/render_kics_page.py` 신설(단일 페이지/contact-sheet, OCR 엔진 호출
없음 — 다음에 SCANNED_SECTION 셀이 나오면 이걸로 렌더링 후 직접 읽으라는 뜻).
`src/solvency/parser/docling_parser.py` 는 남의 담당이라 손 안 댐 — `--ocr-scale` 손잡이
자체는 그대로 있으니, 정말 무인 대량변환이 필요해지면 그때 다시 판단할 것.

**§2(tier2 유틸 빌더 MD-vs-마스터 이중경로)는 손 안 댐** — 다른 담당.

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

## §2 처리 (parser/kics, 2026-09-01)

**§2 처리 완료. §1(docling OCR 배율)은 다른 에이전트가 별도 진행 중, 이 세션은 손대지 않음.**

`compute_tier2_utilization.py`에 제안 (a)+(b) 둘 다 반영:

- **(a)** `_load_json_proxy`가 item3/14 외에 item47-54(같은 TFI/공통적용경과조치 표, 게이트의
  `47_tier2_census`/`48_tier2_limit`이 이미 검사하는 값)를 같이 읽도록 확장. 새 함수
  `_tv_from_master_proxy()`가 47/48/49(적용후 컬럼, 억원→백만원 ×100 변환)가 **셋 다** 있을 때만
  `TableValues`를 만들어 반환 — 하나라도 없으면 `None`을 돌려줘 기존 MD 파싱 경로로 폴백. `compute_one()`은
  이 마스터 경로를 MD보다 먼저 시도한다. 어느 경로를 썼는지 신규 필드 `UtilizationResult.table_source`
  (`"master_items_47_54" | "md_table" | "none"`)로 산출에 남김.
- **(b)** 새 함수 `_check_md_limit_vs_scr()` — **MD 폴백 경로로 떨어졌을 때만**, MD에서 읽은 한도를
  `item14_적용전 x TIER2_LIMIT_RATIO`(게이트 `48_tier2_limit`과 동일 상수, `kics_json_rules`에서
  import — 재타이핑 안 함)와 대조, 게이트 기본 tolerance(2.0억원)를 넘으면
  `quality_flag="tier2_limit_md_mismatch"`로 표시(다른 quality_flag보다 우선). 마스터 경로를 탄
  버킷은 게이트 자신의 `48_tier2_limit`이 이미 같은 식을 검사하므로 이 체크를 스킵.

**검증(전부 실측, 재현 명령 포함)**:

1. **KR0079 2026.2Q 단독**: `table_source`가 `md_table`→`master_items_47_54`로 바뀌면서
   `tier2_limit_eok` 77987.02(오염된 MD, OCR "1→7" 오독 지문 `7,347,253`/`7,798,702`와 정확히
   일치 — §1 티켓이 지목한 그 오염) → **11981.02**(item48과 정확히 일치)로 정정.
   `numerator_eok` -6.01 → **-0.01**로 600배 축소. `quality_flag`는 여전히 `util_negative`인데
   원인이 다르다 — 이제는 데이터 오염이 아니라 **공시된 47/49/53/54(2자리 반올림) 자체가 갖는
   벤치마크 반올림 잔차**(13472.53-10541.60-0-2930.94=-0.01, 4개 반올림값을 더한 정상적 오차
   범위)다. **`util_negative`가 완전히 사라지지는 않았다** — 정직하게 보고한다. candidate(b)를
   KR0079의 실제 오염 MD에 격리 테스트하면(마스터 우회, 스크립트 함수 직접 호출)
   `"MD tier2-limit 77987.02eok vs item14x0.5=11981.00eok (diff +66006.02eok, tol 2eok)"`로
   정확히 잡아낸다 — (b) 자체는 정상 동작, 다만 실제 파이프라인에서는 (a)가 먼저 걸려 KR0079가
   (b) 분기까지 가지 않는다.
2. **전사 재실행(FY2026_Q2, 39개사)**: git HEAD 버전(수정 전)과 현재 버전을 각각 돌려 전체 대조.
   39개사 중 **36개사가 master_items_47_54 경로로 전환**, 나머지 3개사(KR0094 신한라이프·KR1010
   교보라이프플래닛·KR0004 MG_예별손해)는 여전히 MD/proxy 경로(마스터에 47/48/49 미비). 산출이
   달라진 건 **8개사** — 전부 "이전엔 MD 파싱 실패(`data_source=proxy`, KR0001·KR0032·KR0080)나
   스케일 오류(KR0051, 2.62↔262.0·2.71↔271.0 100배 격차 두 분기 다 재현)나 발산
   (`table_proxy_diverge`, KR0087)이던 것이 마스터로 정정"류로 설명 가능, 나머지는 `quality_flag`
   라벨만 바뀌고 수치는 불변(KR0003·KR0010·KR0082) 또는 보조 표시필드 하나만 null로 바뀜(KR1011의
   `tier2_eok`, 실제 utilization_pct/numerator_eok는 불변). `tier2_limit_md_mismatch`는 이번
   실행에서 0건 발동(MD 폴백 3개사 중 진짜 어긋난 사례가 없었다 — (b)는 위 격리 테스트로 별도 확인).
   **DB생명(KR0082)류의 라벨만 바뀐 경우 포함 크래시·예외 0건.**
3. 같은 절차로 **2025.4Q(스크립트 기본 분기, 39개사)**도 재실행 — 37개사 master 전환, 4개사
   변화(KR0010·KR0080: proxy→table 정정 / KR0051: 동일 100배 스케일 정정 / KR0082: 라벨만).
   패턴이 2026.2Q와 일관됨.

**재현**:
```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/compute_tier2_utilization.py --quarter 2026.2Q --md-dir md_inbox/FY2026_Q2 --out-dir <dir>
```
`<dir>/tier2_utilization_20262Q.json`에서 `code=="KR0079"` 레코드 확인.

**수정 파일**: `scripts/compute_tier2_utilization.py`만(+137줄, 다른 담당 파일 미접촉).
`kics_disclosure.json`은 읽기 전용, 쓰지 않음.

**미처리(범위 밖, 후속 후보로만 남김)**: 티켓의 validation 후속메모가 지적한 `MD_DIR` 기본값
(`FY2025_Q4` 고정)은 후보 (a)/(b)와 무관하고 CLI `--quarter`/`--md-dir`로 항상 override되는 값이라
손대지 않았다 — 이 스크립트를 참조하는 다른 5개 스크립트(`validate_data_contract.py` 등, 전부
`output/tier2_utilization/*.json` 경로로만 소비, import 없음)의 default 분기 가정을 내가
단독으로 바꾸는 게 부담스러워서다. 필요하면 별도 검토 요청.

## 답변 (parser/kics, 2026-09-11, iter 2 — §1 판단 실행 + `MD_DIR` 부수지적 처리)

### §1 — 2026-09-01 판단을 재검증 후 유지, 문서화 갭을 메웠다

**판단은 바꾸지 않는다: `--ocr-scale`을 `docling_parser.py`/`run_harness.py --stage parse`
정규 옵션으로 승격하지 않고, fitz+EasyOCR 우회 파이프라인도 만들지 않는다.** 09-01 세션이 이미
이 판단을 실행까지 마쳤고(`scripts/ocr_parse_scanned_disclosure.py`의 `[!decision]` 독스트링에
근거·수치와 함께 명문화, `scripts/_probes/render_kics_page.py` 헬퍼 신설), 이번 세션은 그
판단이 여전히 맞는지 재검증만 했다 — 바뀐 사실이 없다:

- 스케일 1~4 실측(미래에셋 KR0079 2026.2Q p19, 9개 판독)은 `_ocr_converter()` 독스트링에
  그대로 남아 있다: 1=3/9, **2=5/9(최선)**, 3(docling 기본)=2/9, 4=2/9. 216dpi에서 선두
  '1'을 '7'로 읽는 지문(`155.3→755.3`, `13,473→73,473`)도 재현 코드 변경 없음.
  `PdfPipelineOptions.images_scale`이 OCR 경로에 안 닿는다는 확인(1.0/2.0/3.0 바이트 동일
  출력)도 유효.
  - **정식화하지 않는 이유를 다시 명시적으로 계산했다**: 최선의 스케일도 5/9=56% — 절반을
    겨우 넘는 수준이라, 이걸 "정식 옵션"으로 승격해 무인 실행 기본값으로 쓰면 44%가 틀린
    산출을 공식 경로로 만드는 셈이다. 게다가 오독이 '1→7'처럼 **그럴듯하게 틀린** 값이라
    "숫자가 나왔으니 맞겠지"로 새는 위험이 랜덤 노이즈보다 크다. 반대로 fitz 렌더+직독
    방식은 실측 ~150셀에서 **0건 불일치**(유일한 예외 1건도 렌더 문제가 아니라 판독자
    본인의 오독이었고, `item48==item14×50%` 항등식이 즉시 잡아냈다). "정식 옵션 승격"이
    실제로 더 나은 결과를 주지 못하는데 파이프라인 복잡도만 늘리므로 기각을 유지한다.

**실제로 실행한 것 — 이번 세션이 추가한 부분**: 이 판단이 왜 두 번(검증메모, 이번 티켓)
재론됐는지 원인을 짚었다 — **판단은 스크립트 독스트링에만 있었고, 세션이 항상 먼저 읽는
운영 정본(SKILL)에는 한 줄도 없었다.** `.claude/skills/kics-parser/references/
quirks-and-traps.md`에 "Scanned PDFs: OCR is a lead, not a source" 절을 신설해 위 표·근거·
`render_kics_page.py` 안내·"MD 텍스트만으로 마스터에 쓰지 말고 반드시 렌더 검증"규칙을
한 곳에 정리했다. `data/_derived/kics_source_textlayer.json`의 실제 상태값(`SCANNED_SECTION`
= 절만 이미지, `UNREADABLE` = 문서 전체 스캔 — 티켓의 "IMAGE_ONLY"는 이 파일의 실제 enum이
아니라 둘을 아우르는 구어적 표현이었음을 문서에 명시)과 연결했다. 같은 파일의 "Docling loses
pages" 가드 절이 2026-09-01 리라이트 이전 설계(`page_selection_flags()` 함수 +
`SECTION_LOST_*` 등 6종 enum 플래그)를 그대로 서술하고 있던 것도 정정(실제로는
`quality_check.score()`가 `QualityReport.page_flags`에 `missing_window=`/`ratio_critical=`
문자열로 채운다 — 상세는 inbox `20260831T0700Z` 답변 참조). 이 드리프트가 그 티켓의
`AttributeError` 10일 방치를 아무도 못 알아챈 배경 중 하나로 보여 근거를 남겼다.

`docs/domains/claude-agent-kics.md`가 아니라 SKILL 쪽에 적었다 — 그 도메인 문서 자체가
머리말에 "2026-05 설계 stub(부분 stale, owner 결정으로 동결)... durable한 건 [4개 항목]뿐"
이라 못박혀 있고 이 내용은 그 4개 항목에 안 든다. `docs/agents/claude-agent-parser.md`도
"운영 정본(자동로드 트리거)은 `.claude/skills/{kics,ifrs17}-parser/` SKILL"이라 명시한다.
단, `.claude/`는 `.gitignore`(L91)로 전체 제외라 이 문서는 **이 머신에만** 있다 — 다른
머신/워크트리에서 여는 세션은 이 절을 못 본다(SKILL 설계상 원래 그런 것이지, 이번에 새로
생긴 제약은 아니다).

### `MD_DIR` 부수지적 — 실측 후 latest-quarter 자동탐지로 교체했다

09-01 §2 답변이 "손대지 않음"으로 남긴 항목을 이번 티켓이 다시 판단하라고 해서 처리했다.
**실측**: `grep -rn "compute_tier2_utilization" --include=*.py scripts/ src/ tests/ docs/
.githooks/` (자기 파일 제외) = **무출력** — import도 subprocess 호출도 0건, 09-01 답변의
"5개 스크립트는 output JSON만 소비"라는 주장이 맞았다(오히려 5개보다 많은 12개 스크립트/
테스트가 참조하지만 전부 산출 파일 경로 상수일 뿐 이 모듈을 부르지 않는다). 즉 하드코딩된
기본값은 "바로 실행하면 항상 `--quarter`/`--md-dir` 를 넘긴다"는 문서화된 재현 경로 밖에서,
사람이 인자 없이 맨으로 돌릴 때만 조용히 FY2025_Q4를 주는 함정이었다 — 죽은 경로는 아니지만
위험은 낮은 채로 방치돼 있었다.

`_latest_md_period()`를 신설해 `md_inbox/FY*_Q?` 중 최댓값(다른 스크립트들과 동일한
`sorted(glob)[-1]` 관용구)을 골라 `MD_DIR`/`DEFAULT_QUARTER`를 자동 유도하도록 바꿨다:

```
MD_DIR (bare 실행)        FY2025_Q4  ->  FY2026_Q2
DEFAULT_QUARTER (bare)    2025.4Q    ->  2026.2Q
```

**회귀 확인**: git stash로 이 파일만 원복한 뒤 `--quarter 2026.2Q --md-dir md_inbox/FY2026_Q2
--out-dir <A>`를 실행, stash pop 후 같은 인자로 `--out-dir <B>` 재실행 — `diff -rq <A> <B>`
무출력(산출 JSON 바이트 동일). 명시 인자 경로(=문서화된 유일한 재현 경로)는 이번 변경으로
전혀 영향받지 않는다.

수정 파일: `scripts/compute_tier2_utilization.py`(+18줄, MD_DIR/DEFAULT_QUARTER 유도부만).
`kics_disclosure.json`은 이 섹션에서도 건드리지 않음.

### 이번 라운드 판정

§1 판단은 유지(2026-09-01과 동일 결론, 근거 재검증 완료) + 문서화 갭 해소. `MD_DIR` 부수지적은
해소. `route: fix`가 요구한 실행 가능한 항목은 이걸로 소진됐다고 본다 — 다만 §1의 "판단해달라"
요청에 대한 최종 승인은 orchestrator 몫으로 보고 `status: answered`로 둔다.

## 종결 재확인

재확인(orchestrator, 2026-09-12): §2 는 09-01 반영분 그대로, §1 은 '정식화 안 함 + fitz 렌더 직독 유지' 판단을 kics SKILL quirks 문서에 정본화 · `compute_tier2_utilization.py` MD_DIR 최신분기 자동탐지로 교체, `--quarter 2026.2Q` 실행 정상. **resolved.**
