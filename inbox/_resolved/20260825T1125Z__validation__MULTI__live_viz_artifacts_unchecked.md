---
from: validation
to: parser
created: 20260825T1125Z
status: resolved
route: reparse
company: MULTI
period: MULTI
rule: LIVE_ARTIFACT_GATE
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)

라이브 HTML 이 fetch 하는데 **어떤 검사기도 읽지 않던** viz 아티팩트 3개 + NB 마스터에
2026-08-25 에 처음으로 검사를 걸었다(`scripts/validate_live_artifacts.py`, prepush 1c 배선).
기지 결함 전건이 `data/_gold/live_artifact_baseline.json` 에 건별 등재돼 있다 —
고칠 때마다 그 줄을 지워 달라(게이트가 `BASELINE STALE` 로 알려준다). 재현:

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_live_artifacts.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_design_viz_checks.py
```

### A. `data/dart/viz/csm_waterfall_history.json` — 988건 (가장 큼)

**아무도 재생성하지 않는 정적 스냅샷이다.** 파일의 `source` 필드가 가리키는 빌더
`scripts/ifrs17_batch_historical.py` 는 2026-06 에 아카이브됐다. 그동안 마스터는 백필·정정을
계속 받았고 이 파일은 그 자리에 남았다. IFRS17.html 의 워터폴 이력 패널이 그 낡은 값을 그린다.

| 축 | 실측 |
|---|---|
| 마스터 대조 셀 | 1,581 (백만원→억원 /100 정규화 후) |
| **drift** | **933건 (59.0%)** — 최대 Δ 43,852억 (삼성화재 2023.3Q closing: 스냅샷 88,741 vs 마스터 132,593) |
| 스냅샷 자체 단계 항등식 파탄 | 41건 (마스터 쪽 동일 축은 358P/0F 로 닫힌다) |
| 마스터에 있는데 스냅샷에 없는 회사 | 14사 (패널에서 통째로 빠짐) |

**요청**: 처분을 정해 달라 — ① 빌더를 되살려 재생성하거나 ② **마스터에서 파생**으로 교체
(그러면 drift 가 구조적으로 0 이 되고 이 룰이 영구히 조용해진다). ②를 권한다.
그 전까지 등재는 "스냅샷이 낡았다"는 사실의 박제이지 값의 승인이 아니다.

### B. `data/dart/viz/csm_amort_schedule.json` — 53건

1. **장기 꼬리 버킷 누락 (22사 × 2룰 = 44건).** 원표 헤더에 `11년~15년 / 16년~20년 /
   21년~25년 / 26년~30년 / 30년 이후` 컬럼이 있는데 추출은 `y1~y10 + y10plus` 까지만 담는다.
   `y10plus` 가 11~15년 하나만 먹고 나머지 4개 컬럼이 버려진다 → Σ(연차)가 합계보다
   **35~44% 작다**. 예: DB생명 Σ=11,176.8 vs total=19,813.0 (Δ -8,636.2, -43.6%).
   화면 막대가 그만큼 짧게 그려진다.
2. **status != ok 5사** — empty 4(교보라이프플래닛·서울보증보험·악사손해보험·하나손해보험),
   partial 1(예별손해보험). 패널이 빈칸으로 그린다.
   ※ 서울보증보험은 validation 이 2026-08-25 에 **정당 미공시 확정**(주석14 컬럼이
   보험료배분접근법 하나뿐). 나머지 4사는 raw 확인 전이라 단정하지 않았다 —
   키워드 부재를 원문 부재로 읽지 말 것(스캔 PDF 전례).
3. **합계 / 기말CSM ratio 0.28~0.57 인 4사** — 처브(0.279)·AIA(0.377)·메트라이프(0.467)·
   라이나(0.574). 단위오류는 아니다(SCALE 룰 통과). PAA 적용분이 스케줄 표 밖일 가능성 —
   정당하면 legit 레지스트리로 올려 달라, 아니면 추출 범위 문제다.

### C. `data/dart/viz/insurance_pl_breakdown.json` — 9건

1. **한화손해보험 2024.4Q 행 파싱 사고.** 표의 `보험계약마진상각` 행 마지막 숫자가
   `-387,989,612` 로 PL 마스터(`원수CSM상각` 409,737)의 **947배**. 셀이 이어붙었다.
2. 코리안리재보험 2024.4Q ratio 2.841 — 재보험사 표 구조가 달라 원수/재보험 합산 행을
   집었을 가능성. 미확인.
3. PL 마스터 36사 중 29사만 있어 **7사가 패널에서 빠진다**.

참고: 이 대조는 신호가 있다 — 행이 잡히는 10사 중 8사가 ratio 0.87~1.04 로 붙는다.

### D. `NB_CSM_multiple.json` — 부호 반전 1건

예별손해보험 2023.4Q `신계약CSM_연누계` = **-509.7** 인데 `CSM_waterfall.json` 항목2 는
**+509.7**. index.html CSM 버블맵의 X축이 그 회사만 음수로 그려진다.
(같은 파일의 배수 항등식 `배수 = CSM / 월납월초보험료` 는 연누계 308P/0F · 당분기 286P/0F,
`당분기 = YTD 차` 도 299P/0F 로 깨끗하다 — 이 한 건만 부호가 틀렸다.)

## 답변 (recipient 작성 — 처리 후)

**요약: A는 처분만 판정(코드 미수정, 화면 영향 0 확인) · B 22개사 전원 닫힘 · C 947x 완전 정정 +
코리안리 1건은 raw로 원인 좁혔으나 미수정 · D 1셀 부호 정정. baseline 46건 삭제(1082→1036),
gate RED=0 STALE=0. prepush_check.py 재현 exit 0("PRE-PUSH VERDICT: ... → gate-clear").**

재현: `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_live_artifacts.py`

---

### A. `csm_waterfall_history.json` — 처분 판정: **화면 영향 0, 되살리지도 새로 만들지도 않았다**

`inbox` 발주문 자체의 전제("IFRS17.html 의 워터폴 이력 패널이 그 낡은 값을 그린다")를 raw
소스(HTML)로 반증했다. **로컬 브랜치가 아니라 `origin/main`(실제 라이브 배포본, rev
`fba59f0`)을 직접 대조**:

```
git show origin/main:IFRS17.html | grep -n "csm_waterfall_history\|ix\.hist\|payload\.hist\|charts\.hist"
```

- L260: `hist: dataPaths("../data/dart/viz/csm_waterfall_history.json", ...)` — **fetch 는 한다**
  (네트워크 요청 발생, 티켓의 "fetch 는 하는데" 부분은 맞음).
- L1525: `// 기존 csm_waterfall_history.json은 stale(2025.3Q·2026.1Q 결측, 초기 2023 미교정)
  이라 폐기.` — **소스 자체의 주석이 폐기를 명시.**
- L1526-1535 (Panel 6 렌더 블록): `wfHistName`·`wfVal`·`wfNbIncrement` 전부
  `ix.wfx`(=`CSM_waterfall.json`) 참조. `payload.hist`/`ix.hist` 를 읽는 코드는 **파일 전체에
  0곳**(L1670 대입 한 줄이 유일한 사용 — 채우기만 하고 아무도 안 읽음).

**결론: fetch 는 살아있지만 렌더는 100% `CSM_waterfall.json` 경유(Panel 1 과 동일 소스,
자동으로 항상 최신). `csm_waterfall_history.json` 의 933건 drift 는 화면에 단 한 셀도 안
나간다.** (34th pass, 2026-08-24 의 동일 결론을 오늘 `origin/main` 기준으로 재확인 — 로컬
브랜치가 하루 뒤처져 있어 로컬 `IFRS17.html` 만 봤으면 fetch 선언 자체가 없어서 오히려
false-negative 가 났을 것.)

**권고 — 셋 중 ③(화면에서 뗀다)이 유일하게 근거 있는 선택이지만 실행하지 않았다(HTML,
designer 소관):**
1. 빌더 되살리기(`ifrs17_batch_historical.py`, archive 아님·현존) 또는
   `archive/2026-06_csm_nb_reverse_engineering/viz_build_csm_waterfall_history.py` 복원 —
   **비권장.** 죽은 렌더 경로를 위해 재생성 파이프라인을 유지보수할 이유가 없다.
2. 마스터에서 파생하는 새 빌더 — **비권장.** validation 의 원래 제안이지만, 결과물을
   아무도 안 읽는 상태에서 새 코드를 투자하는 건 근거가 없다(CLAUDE.md 단순성 원칙).
3. **HTML 에서 fetch 자체를 떼기(`PATHS.hist`/`payload.hist`/`ix.hist`/`charts.hist` 잔재
   삭제) — 권고.** 매 페이지로드마다 낡은 47KB 짜리 죽은 JSON 을 받아오는 낭비만 남아있다.
   화면 구조 변경이라 designer/owner 승인 필요, 나는 실행하지 않았다.

**게이트는 그대로 둔다.** `validate_live_artifacts.py` 의 이 체크(HIST_MASTER_DRIFT 933 ·
HIST_STAGE_IDENTITY 41 · HIST_CENSUS_MISSING 14, 합 988건)는 baseline 에 그대로 남아있다 —
파일이 여전히 fetch 되는 한 "죽은 데이터가 더 썩어가는지" 감시할 이유는 있다. baseline
`_promote` 필드의 조항(4) "파일 자체의 처분이 승격 조건" 은 유지, 기한 2026-10-31 불변.

**owner/validation 에게 반증 보고**: 원 티켓의 "워터폴 이력 패널이 그 낡은 값을 그린다"는
현재 `origin/main` 기준 사실이 아니다. census 도구(정적 fetch 문자열 스캔)가 PM
`PM-2026-08-25_gate_read_the_wrong_file.md` §6 에서 이미 자인한 것과 **같은 종류의 오탐**
(fetch 선언 = 렌더 사용 으로 오인)이다 — 그 문서가 "동적 조립을 놓쳐 UNREAD 오탐"은 잡았지만
"fetch 는 하는데 렌더는 안 하는" 반대 방향 오탐은 못 잡았다. `UH-14`(런타임 추적이 매 push
묶음엔 안 돈다)와 같은 사각의 다른 사례로 보인다.

---

### B. `csm_amort_schedule.json` — 22개사 컬럼 누락, **전원 닫힘**

**원인.** `_year_bucket_cell`/`_classify_bucket_cell`(`scripts/viz_build_ifrs17_panels.py`)의
연차 버킷 정규식 4종 중 어느 것도 `"11년~15년"` 형태(둘째 뿐 아니라 **첫 숫자 뒤에도 "년"이
붙는** 꼴)를 못 잡았다. `_RANGE_TILDE_RE`는 `"5~10년"`(첫 숫자엔 "년" 없음)만 매치하고,
`_RANGE_CHOGWA_IHA_RE`는 `"1년초과2년이하"` 꼴만 매치한다. `_OVER_ONLY_RE`(`"30년 이후/초과/
이상"`)만 우연히 매치해 `y10plus` 를 채웠고, `"11년~15년"·"16년~20년"·"21년~25년"·
"26년~30년"` 4개 컬럼은 **매치되는 패턴이 아예 없어 통째로 버려졌다.** 39개사 중 22개사가
정확히 이 헤더 포맷을 쓴다(DB생명보험 raw 원문 헤더로 실측 확인: `['1년',...,'10년',
'11년~15년','16년~20년','21년~25년','26년~30년','30년 이후','합계']`, header-column 형과
row-키(전치) 형 둘 다 같은 두 함수를 거치므로 DB손해보험·케이비라이프생명보험(전치형)도
같이 낫는다).

**수정.** `_RANGE_YEAR_TILDE_YEAR_RE = r"^(\d{1,2})년~(\d{1,2})년$"` 신규 정규식 1개를 두
분류 함수에 순수 가산(다른 패턴 우선순위·기존 매치 결과 불변). y10plus/y5_plus 로 라우팅되는
로직은 그대로.

**Before/after (22개사 전원, 억원, `granularity=yearly` Σ vs 원표 합계):**

| 회사 | 원표 합계(불변) | Σ(수정 전) | gap 전 | Σ(수정 후) | gap 후 |
|---|---:|---:|---:|---:|---:|
| DB생명보험 | 19,813.0 | 11,176.8 | -43.6% | 19,813.0 | 0.00% |
| 교보생명보험 | 65,109.6 | 37,278.2 | -42.7% | 65,109.6 | 0.00% |
| 흥국화재 | 24,707.9 | 14,176.0 | -42.6% | 24,707.9 | 0.00% |
| 케이디비생명보험 | 8,650.4 | 4,986.7 | -42.4% | 8,650.4 | 0.00% |
| 하나생명보험 | 7,269.0 | 4,237.4 | -41.7% | 7,269.0 | 0.00% |
| 롯데손해보험 | 24,748.6 | 14,616.8 | -40.9% | 24,748.6 | 0.00% |
| 흥국생명보험 | 22,152.0 | 13,246.1 | -40.2% | 22,152.0 | 0.00% |
| 케이비라이프생명보험 | 32,637.8 | 19,674.5 | -39.7% | 32,637.8 | 0.00% |
| 농협생명보험 | 42,991.1 | 26,118.6 | -39.2% | 42,991.1 | 0.00% |
| NH농협손해보험 | 15,132.3 | 9,225.7 | -39.0% | 15,132.3 | 0.00% |
| 신한라이프생명보험 | 75,549.0 | 46,612.8 | -38.3% | 75,549.0 | 0.00% |
| 에이비엘생명보험 | 9,374.6 | 5,833.5 | -37.8% | 9,374.6 | 0.00% |
| DB손해보험 | 122,317.6 | 76,185.1 | -37.7% | 122,317.6 | 0.00% |
| 동양생명 | 26,710.9 | 16,700.2 | -37.5% | 26,710.9 | 0.00% |
| 아이엠라이프생명보험 | 7,060.5 | 4,422.6 | -37.4% | 7,060.5 | 0.00% |
| 삼성생명 | 130,806.9 | 82,289.3 | -37.1% | 130,806.9 | 0.00% |
| 한화손해보험 | 38,032.2 | 23,931.2 | -37.1% | 38,032.2 | 0.00% |
| 삼성화재해상보험 | 140,739.1 | 89,560.2 | -36.4% | 140,739.1 | 0.00% |
| KB손해보험 | 92,850.3 | 59,835.5 | -35.6% | 92,850.3 | 0.00% |
| 코리안리 | 9,046.7 | 5,863.3 | -35.2% | 9,046.7 | 0.00% |
| 미래에셋생명 | 20,584.2 | 13,615.8 | -33.9% | 20,584.2 | 0.00% |
| 에이아이지손해보험 | 922.7 | 696.3 | -24.5% | 922.7 | 0.00% |

`buckets`(4구간 요약) 필드도 같은 두 함수를 쓰므로 동시에 닫힘. `AMORT_YEARLY_SUM_NE_TOTAL`
22 + `AMORT_BUCKETS_SUM_NE_TOTAL` 22 = 44건 전부 baseline 에서 삭제.

**미해결로 남긴 것(범위 밖, ticket 은 손 안 댐):**
- `AMORT_STATUS_NOT_OK` 5건(empty 4 + partial 1) — raw 원문 미확인, 티켓 원문 그대로 두었다.
- `AMORT_TOTAL_VS_CLOSING_CSM_BAND` 4건(처브·AIA·메트라이프·라이나, ratio 0.28~0.57) — PAA
  제외 가설 미검증.

---

### C. `insurance_pl_breakdown.json` — 한화손해보험 947x **완전 정정**, 코리안리 **원인 좁힘(미수정)**

**한화손해보험 947x — 원인은 하나가 아니라 둘의 곱이었다.**

1. **기간 오선택(전기 vs 당기).** raw
   (`data/dart/FY2024_Q4/raw/KR0002_한화손해보험_20250311001216/20250311001216_00760.xml`)에
   같은 캡션 "(5) 당기와 전기 중 인식된 ... 변동내역은 다음과 같습니다."이 "(당기)" 표
   (L12520-, 보험계약마진 소계 -409,737,121천원)와 "(전기)" 표(L12770-, -387,989,612천원)
   두 개를 감싼다. 이 필링에서만 문서 안에 동일 표가 8번 중복 등장(본문+첨부 조합) 하는데
   `pick_best_block` 의 동점 tie-break(`score,rows` 동률 시 `line_no` **최댓값**)가 항상
   "마지막에 나오는 것"을 고른다 — (당기)가 먼저 인쇄되고 (전기)가 항상 뒤따르는 DART 관행상
   구조적으로 **전기가 이긴다.**
2. **단위 미정규화.** 이 표 캡션 바로 위 "(단위: 천원)" 은 `<TABLE>` 형제 텍스트 노드라 표
   블록에 안 담겨(docling 이 흔히 떨구는 패턴, `_AMORT_UNIT_OVERRIDE` 에 이미 5개사 기록된
   같은 함정), `extract_pl_breakdown` 은 애초에 단위 감지 자체가 없었다(원표 그대로 담는
   설계). 그래서 전기값(천원 단위 그대로)을 마스터(백만원)와 그대로 나누기 없이 대조 →
   *2요인이 곱해* 947배(=1000배 단위오차 × 0.947배 전기/당기 비율의 역수 근방)가 났다.

**수정.**
- `_dedupe_prefer_current_period()` 신규 — (caption, header, row-label 튜플) 이 완전히 같은
  후보군에서만 `line_no` 최솟값(당기)을 우선. **`_PL_PREFER_CURRENT_PERIOD = {"한화손해보험"}`
  로 게이팅**했다 — 처음엔 전 회사에 무조건 적용했더니 KB손해보험 등 15개사의 선택이
  바뀌었고(흥국생명보험은 아예 다른 노트("(7) 보험서비스결과의 상세내역"→"(7) 보험손익의
  상세내역")로 넘어감), 그중 KB손해보험은 **이미 완벽히 맞던 표(837,664, ratio 1.0000)가
  라벨 변형("보험계약마진 상각" vs "제공된 서비스의 보험계약마진", 같은 값의 문서 내
  재렌더링 잡음)에 걸려 체커가 못 찾는 None 으로 퇴행**하는 걸 실측으로 잡았다 — 전면
  적용을 되돌리고 한화손해보험 1개사만 허용리스트로 좁혔다(bs_snapshot.json·
  sensitivity_heatmap.json 바이트 무변동, PL 패널도 한화 외 28개사 전부 원본과 캡션까지
  바이트 동일 재확인).
- `_PL_UNIT_OVERRIDE = {"한화손해보험": "천원"}` 신규 (기존 `_AMORT_UNIT_OVERRIDE` 패턴을
  그대로 재사용, 별도 앵커/교차검증 자동화 대신 **raw 인용으로 못박음** — 이 회사는 FY2025
  상각스케줄 패널에서 이미 "천원" 으로 확정돼 있어 회사 단위 관행이 이중 확증됨). 감지되면
  표의 숫자칸만 ×0.001 재포맷(라벨·"-"칸·부호표기는 불변), `unit`/`unit_detected`/
  `unit_source` 메타 필드 추가.

**Before/after (한화손해보험 2024.4Q, 표 `보험계약마진상각` 소계, 원문 그대로 표시):**

| 단계 | 값(표시 그대로) | 실제 단위 | 마스터(원수CSM상각) | ratio |
|---|---:|---|---:|---:|
| 수정 전 | -387,989,612 | (미표시, 실제 천원) | 409,737.121 백만원 | 946.92 |
| 기간만 수정 | -409,737,121 | (미표시, 실제 천원) | 409,737.121 백만원 | 1000.00 |
| **최종(기간+단위)** | **-409,737.121** | **백만원(표시)** | 409,737.121 백만원 | **1.0000** |

**코리안리재보험 2024.4Q ratio 2.841 — raw로 파싱사고는 배제, 앵커 부적합으로 원인 좁힘(미수정).**
표시값 108,252(백만원)는
`data/dart/FY2024_Q4/raw/KR1000_코리안리_20250320001161/xml/20250320001161_00760.xml` L14365
에 리터럴로 존재 — **파싱 사고 아님.** 이 회사는 PL_breakdown.json 에 원수/재보험/수재/출재
4축 CSM상각 항목(item4=38,102·item9=11,236·item4-1=33,740·item9-1=-8,756)이 각각 있는
재보험사 특성상 다축 구조라, 체커가 대는 단일 앵커(item4 원수CSM상각)가 이 표의 "합계" 열
범위와 안 맞는다. 4항목의 여러 조합을 시도했으나 108,252 에 정확히 닫히는 조합을 못 찾았다
— **표시값을 바꾸지 않았다**(원문 그대로가 맞고, 비교 대상이 틀렸을 가능성). baseline 사유
갱신해 다음 세션이 재추적할 근거를 남겼다(`data/_gold/live_artifact_baseline.json` +
`scripts/validate_live_artifacts.py` RULE_REASON 둘 다 갱신, 회사 4축 CSM상각 항목 인용 포함).

**미해결로 남긴 것**: `INSPL_CENSUS_MISSING` 7건(원표 패널에 없는 회사) — 티켓 범위 밖,
안 건드림.

---

### D. `NB_CSM_multiple.json` — 예별손해보험(KR0004) 2023.4Q 부호 정정

**원인.** `NB_CSM_multiple.json` 의 `신계약CSM_연누계` 는 `build_nb_csm_multiple.py` 가
`CSM_waterfall.json` 항목2 를 그대로 복사만 하는 필드(변형 없음, 소스 자체 문서화됨) —
드리프트는 **파생 파일이 상류 정정을 못 받아 굳어 있던 stale copy** 였다.

**raw 로 상류(CSM_waterfall.json)쪽이 맞다는 것까지 재확인**(마스터 자체는 안 건드림, 대조만):
`data/dart/FY2023_Q4/raw/KR0004_엠지손해보험_20240408000665/20240408000665_00760.xml`
"(4) 당기 및 전기 중 인식된 ... 변동내역"(원수) 표 — 기초순장부금액 CSM소계 605,551,876천원
= 6,055.5억(마스터 item1 과 일치) · 당기말순장부금액 CSM소계 677,401,166천원 = 6,774.0억
(마스터 item6 과 일치). 표 내 "신계약인식효과"(=신규계약) 행 CSM소계는 raw 그대로는
-50,969,591천원 이지만, **표의 전체 변동 섹션(현행서비스+미래서비스+과거서비스+보험금융손익)
합계 -71,849,290천원 이 실제 (기말-기초)=+71,849,290천원 의 정확히 음수** — 즉 이 표의
변동행 전체가 부호 반전 관례로 인쇄된다(스크립트로 정밀 검산, 사람 눈대중 아님). 그 반전을
전 행에 균일 적용하면: 신계약=+509.7억(마스터 item2 일치) · 보험금융손익(이자부리)=
+203.1억(item3 일치) · 조정변동(154.6억)+손실부담계약(322.9억)=477.5억(item4 와 일치) ·
상각=-471.8억(item5 일치) — **6항목 중 검증 가능한 4개(2,3,4,5) 전부 소수 첫째자리까지
마스터와 닫힌다.** `CSM_waterfall.json` 은 건드리지 않았다(다른 세션 소관, +509.7 이 raw 로
독립 재확인됐다는 사실만 보고).

**Before/after:**

| 회사·분기 | 필드 | 수정 전 | 수정 후 | 근거 |
|---|---|---:|---:|---|
| 예별손해보험(KR0004) 2023.4Q | 신계약CSM_연누계 | -509.7 | 509.7 | raw 표 전체 부호반전 확인(위), CSM_waterfall 항목2=509.7 일치 |

수정은 **1셀뿐**(diff 로 확인, `월납월초보험료_*`/`신계약CSM배수_*` 등 나머지 필드는 이미
null 이라 무영향). `data/kidi/premium_summary.json` 이 디스크에 없어(gitignore, memory
`reference_kidi_premium_summary_gap`) **빌더 재실행은 하지 않았다** — 재실행하면 그 파일이
없어 전 행의 월납/배수 필드가 전부 null 로 wipe 된다(기존에 채워진 358행 규모의 값이 지워질
뻔했다). 대신 `NB_CSM_multiple.json` 을 손패치하고 `sync_master_xlsx_sheet.py 신계약CSM배수`
로 xlsx 시트만 cherry-pick 동기화(`검증 OK — 신계약CSM배수 327행 × 11열 마스터와 완전 일치,
나머지 시트 값 동일`).

---

### baseline 정리

`data/_gold/live_artifact_baseline.json`: 1082 → 1036건 (46건 삭제 — B 44 + C 1(한화) + D 1).
등재부 자체 정합성(`STALE_BASELINE`)을 매 삭제 후 재확인, 최종 `STALE_BASELINE=0`.
코리안리 잔여 1건은 사유만 갱신(값 불변). 남은 990건(A 988 + B 9(status/band) +
C 8(census+코리안리))은 전부 raw 미확인이거나 화면 영향이 없거나(A) 이번 티켓 범위 밖.

### 게이트

- `scripts/validate_live_artifacts.py` → **RED=0, YELLOW=1036, STALE_BASELINE=0**.
- `python -m pytest tests/test_viz_ifrs17_panels_golden.py tests/test_viz_csm_waterfall_golden.py`
  → csm_waterfall 골든 무변동 PASS, ifrs17_panels 골든은 의도된 변경(B+C) 감지 →
  `--update` 재생성 완료(`bs_snapshot.json`·`sensitivity_heatmap.json` 은 해시 불변 확인).
- `scripts/prepush_check.py` → **exit 0**("PRE-PUSH VERDICT: gate RED=0 · K-ICS rule
  gate=clear · domain gates=pass · DART raw 유실=0 · inbox 기계적위반=0 · offline tests=pass
  → gate-clear", offline tests 230 passed / 1 skipped, `validate_live_artifacts: exit=0`
  라인 포함). 재현: `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
  scripts/prepush_check.py`.

### 건드리지 않음

`CSM_waterfall.json`·`PL_breakdown.json`(루트 마스터, 다른 두 세션 병행 작업 확인 —
git status 에 잡히나 이 세션 미접촉) · `kics_tier{1,2}_utilization.json`·
`output/tier{1,2}_utilization/*`·`scripts/{compute_tier1_utilization,forward_capital_simulation,
wire_capital_securities_to_utilization}.py`(K-ICS 레인, git status 에 잡히나 미접촉) ·
`IFRS17.html`·기타 배포 HTML 4종(읽기만, designer 소관) · `bs_snapshot.json`·
`sensitivity_heatmap.json`(빌더 재실행했지만 바이트 무변동 확인) · `build_root_masters.py`
(미실행) · `git commit`/`git push`(미실행).

### 파일

`scripts/viz_build_ifrs17_panels.py`(정규식 1개 + PL 기간/단위 보정 2종, 둘 다 게이팅됨) ·
`data/dart/viz/csm_amort_schedule.json`(22개사 재생성) ·
`data/dart/viz/insurance_pl_breakdown.json`(한화손해보험만 재생성) ·
`NB_CSM_multiple.json`(1셀) · `data/_gold/live_artifact_baseline.json`(46건 삭제 + 코리안리
사유 갱신) · `scripts/validate_live_artifacts.py`(코리안리 RULE_REASON 갱신) ·
`tests/fixtures/viz_ifrs17_panels_golden.json`(`--update`) ·
`insurequant_master_tables.xlsx`("신계약CSM배수" 시트만 cherry-pick).

status: `resolved` (자기완결 — 게이트 수치·재현 명령으로 자기증명, A 는 반증 보고 포함해
원 sender 재확인 권장하되 이 세션 관점에서는 답 완료)
