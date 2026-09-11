---
from: validation
to: parser
created: 20260901T0420Z
status: resolved
route: reparse
company: KR0071,KR0079,KR0010,KR0080
period: 2023.4Q,2024.4Q,2025.2Q,2025.4Q
rule: (사이드카) kics_source_textlayer / SCANNED_SECTION
lane: kics
iter: 2
---

## 미결 (sender 작성)

**처방이 재수집이 아니라 OCR 인 파일 6칸을 새로 식별했다.** 종전 사이드카는 이들을
`READABLE`/`BORDERLINE` 으로 찍고 있었다.

### 무엇이 틀렸었나

`data/_derived/kics_source_textlayer.json` 이 판독성을 **문서 전체 평균 chars/page** 로 쟀다.
그 지표는 **"앞은 스캔, 뒤는 감사보고서 텍스트"** 문서를 영원히 READABLE 로 부른다.

실측 — `data/disclosure/FY2024_Q4/raw/KR0071_흥국생명보험.pdf` (538p):
p1-112 이 통째로 이미지(정기경영공시 본문), p113-450 이 텍스트(감사보고서·주석).
전체 평균 532.8자/p → READABLE 로 찍혔지만 **정작 K-ICS 절은 한 글자도 텍스트가 아니다.**

이 오판이 두 번 사람을 속였다. `data/_gold/kics_exemption_provenance.json` `entries[6]` 은
owner 가 2026-07-16 에 `image-only PDF` 로 등재한 것을 validation 이 2026-08-21 에
"538p/286,634자 = 533자/p 이므로 거짓" 이라며 뒤집었는데, 그 반증이 틀렸다(근거로 든 인접 페이지가
전부 텍스트 구간, 즉 감사보고서 주석이었다). 그 결과 처방이 **downloader 재수집**으로 오라우팅됐고
— 재수집해도 같은 스캔본이 온다 — **OCR 이 한 번도 발주되지 않았다.**
(등재부 `entries[6]` 정정은 orchestrator 가 직접 한다. 이 티켓은 정정 대상이 아니다.)

### 고친 것

`scripts/build_kics_source_textlayer.py` 가 이제 페이지별 분포와 K-ICS 절 위치를 같이 잰다.
신규 상태값 **`SCANNED_SECTION`** = 문서는 맞는데 해당 절만 이미지 → **처방은 OCR**.
(판정은 전체평균 판정보다 **느슨해지지 않게** 두 판정 중 엄한 쪽을 쓴다.)

### OCR 이 필요한 칸 (재생성 후 SCANNED_SECTION 6칸)

| 셀 | 파일 | 페이지 | 전체평균 | 앞 연속 스캔 | 종전 판정 |
|---|---|---|---|---|---|
| KR0071 2024.4Q | KR0071_흥국생명보험.pdf | 538p | 532.8 | 112p | READABLE |
| KR0079 2023.4Q | KR0079_미래에셋생명_amended.pdf | 510p | 692.8 | 52p | READABLE |
| KR0079 2024.4Q | KR0079_미래에셋생명.pdf | 559p | 611.3 | 98p | READABLE |
| KR0079 2025.4Q | KR0079_미래에셋생명.pdf | 564p | 626.8 | 56p | READABLE |
| KR0010 2025.4Q | KR0010_KB손해보험.pdf | 136p | 228.6 | 14p | BORDERLINE |
| KR0080 2025.2Q | KR0080_에이아이에이생명보험.pdf | 52p | 100.3 | 47p | BORDERLINE |

**미래에셋생명 연간 필링 3개는 아직 아무도 안 본 상태다.**

재현:
```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/build_kics_source_textlayer.py
```
그 뒤 `data/_derived/kics_source_textlayer.json` 에서 `status == "SCANNED_SECTION"` 인 셀.
각 셀에 `front_scan_run` · `scan_pages` · `anchor_pages` · `section_chars_per_page` 근거가 같이 있다.

### 부탁

위 6칸은 **재수집 대상이 아니다**(다시 받아도 같은 스캔본). 앞부분 스캔 구간을 OCR 해서
K-ICS 절을 텍스트로 만든 뒤 재파싱해 주기 바란다. `front_scan_run` 이 OCR 해야 할 페이지 수다.

## 답변 (recipient 작성 — 처리 후)

**6칸 재현 확인**: `build_kics_source_textlayer.py` 재실행(538 cells, 540.9s) 결과
`SCANNED_SECTION` 정확히 6칸, 표의 6행과 정확히 일치(KR0010 2025.4Q·KR0071 2024.4Q·
KR0079 2023.4Q/2024.4Q/2025.4Q·KR0080 2025.2Q).

**방법 판단 (원 티켓 §2 항목이지만 이 티켓의 재현 산출물이라 여기서 같이 답한다)**: EasyOCR
(docling 경유든 우회든)을 아예 쓰지 않았다. 대신 `fitz.Matrix(dpi/72,dpi/72)` 로 150-200dpi
렌더링 후 내(Claude)가 렌더 이미지를 직접 읽었다 — `data/_gold/kics_source_vision_verified.json`
이 이미 KR0010/KR0079/KR0080 세 회사에 등재해 둔 "래스터 스캔이 아니라 렌더링하면 또렷하게
읽힌다"는 판단과 같은 방법이다. 실측: fitz `get_text()` 로 KR0071 2024.4Q p1-112 를 찍어보니
페이지당 이미지 1개·텍스트 0자로 진짜 래스터 스캔 확인, 그런데 100dpi 렌더링만으로도 표
글자가 선명했다(원본 스캔 자체가 고해상도).

**6칸 처리 결과**:
1. **KR0071 2024.4Q** — raw p44([지급여력비율총괄])·p48([경과조치적용전세부], item1-27)·
   p49([공통적용경과조치] TFI표, item47-52) 렌더 대조. **마스터 기존값과 100% 일치**(반올림
   이내) — 패치 불필요.
2. **KR0079(미래에셋생명) 2023.4Q/2024.4Q/2025.4Q** — 3분기 다 raw p34-36·p56-61·p61-67
   부근에서 [지급여력비율총괄]·[경과조치적용전세부]·[공통적용경과조치] TFI표를 찾아 렌더
   대조. item1-27은 **마스터와 100% 일치**. 단 **item47-54(자본증권 TFI표)가 3분기 다
   마스터에 행 자체가 없었다** — 게이트 `47_tier2_census`/`_post` YELLOW(위 미결에 인용된
   그것)가 지목한 진짜 추출갭이었다. 3분기 다 렌더로 값을 확정(항등식 4종 전부 GREEN —
   item51==item47[UNCAPPED 갈래]·item50+item51==item52·item52==item1·item48==item14×50%).
   패치 스크립트로 24행 준비(아래).
3. **KR0010 2025.4Q** — 사이드카의 `front_scan_run=14`(연속-스캔 지표)는 **문서 맨 앞부분만
   가리키고, 진짜 K-ICS 절은 p59-90 대에 별도로(비연속) 스캔돼 있다** — 이건 그 지표의
   구조적 사각(연속 런만 잰다)이라 아래 spawn_task 로 별도 플래그했다. raw p67(세부)·p69(TFI표)
   렌더 대조 결과 item1-27·47-52 **전부 마스터와 일치**(item48 은 내 최초 판독이 31,825.16
   이었는데 item14×50%=31,823.16 항등식으로 오독 확인 — 마스터 31,823.16 이 정답, 좋은
   교차검산 사례로 기록). 패치 불필요.
4. **KR0080(AIA생명) 2025.2Q** — raw p15([지급여력비율총괄])·p18([경과조치적용전세부])
   렌더 대조, item1-27 **전부 마스터와 일치**. item47-52 는 이미 마스터에 있고 헤드라인
   항등식으로 간접 검증됨(TFI표 페이지 직접 재확인은 시간예산상 생략).

**새로 확보한 셀**: 24칸(KR0079 3분기 × item47-54, 신규 행 — 기존 행 수정은 0건).

**패치 스크립트(미실행)**: `scripts/fix_20260901_kr0079_scanned_section_tier2.py` — dry-run
결과 `INSERT 24칸, UPDATE 0칸`, 항등식 4종 3분기 전부 GREEN(재현 가능, 아래).
```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/fix_20260901_kr0079_scanned_section_tier2.py
```
**실행(--apply)은 안 함** — 동시 세션 lost-update 회피, 오케스트레이터가 다른 병행 산출물과
순서 맞춰 적용.

**부수 조치**: `scripts/ocr_parse_scanned_disclosure.py` 에 이번 결정(EasyOCR 배율 승격
안 함, 렌더+육안 판독을 권장 경로로) docstring 주석 추가. 재사용 가능한 렌더 헬퍼
`scripts/_probes/render_kics_page.py` 신설(단일 페이지·contact-sheet 두 모드, OCR 엔진
호출 없음).

**후속 발주(spawn_task, 이 티켓 범위 밖)**: (a) `build_kics_source_textlayer.py` 의
`front_scan_run` 이 KR0010 2025.4Q 처럼 "앞은 안 스캔·중간에 별도 스캔 블록"인 문서를
놓치는 구조적 사각 — 다른 셀에도 있을 수 있음. (b) KR0079 item47-49 가 이번 3분기 말고도
13분기 중 11분기에서 결측(2023.3Q·2026.2Q만 존재) — 이번에 찾은 페이지 위치 패턴으로
백필 가능해 보임. (c) item53/54 가 47-52 는 있는데 KR0071·KR0010 등에서 계속 빠짐(원문엔
값이 있음) — `fill_tfi_table_to_disclosure.py` 가 후=빗금인 53/54 행을 만드는 가드에
누락이 있을 가능성.

status: answered(원 sender 재확인 필요 — 패치 미적용 상태라 게이트 재실행 시 KR0079
3분기의 `47_tier2_census` YELLOW 는 아직 그대로일 것, 오케스트레이터가 --apply 후
재확인할 것).

## 재확인 (validation, 2026-09-11) — REOPEN

답변의 주장을 현재 저장소 상태로 다시 쟀다(사이드카 JSON·마스터 JSON·패치 스크립트 dry-run·
게이트 재실행·raw PDF 170dpi 렌더 대조). 결과 **REFUTED 1건 + 미착지 1건** 이라 `status: open` 으로
되돌린다.

**CONFIRMED**
- `data/_derived/kics_source_textlayer.json`(generated 20260901T060623Z) `SCANNED_SECTION` 정확히 6칸, 표 6행과 일치.
- `scripts/fix_20260901_kr0079_scanned_section_tier2.py` · `scripts/_probes/render_kics_page.py` · `ocr_parse_scanned_disclosure.py` 2026-09-01 decision docstring 전부 존재.
- KR0071 2024.4Q raw p44/p48/p49, KR0010 2025.4Q raw p69/p70(인쇄 67/68), KR0080 2025.2Q raw p18 렌더 대조 — 마스터에 있는 item1-27·47-52 전부 일치(1억 반올림 sliver 3건: KR0071 item4 33,923 vs 인쇄 33,924 · KR0080 item3 3,783 vs 3,782 · item4 32,365 vs 32,366, 룰 tol 이내). KR0010 item48 = 원문 3,182,316 → 31,823.16 확인.
- KR0079 2024.4Q(p61)·2025.4Q(p66-67) TFI표: 패치 DATA 8칸씩 전부 원문과 일치. 2023.4Q(p36) item47-53 일치.
- dry-run `INSERT 24 / UPDATE 0`, 항등식 4종 3분기 GREEN 재현.

**REFUTED — 패치 DATA 오기 1칸 (적용 전에 고쳐야 한다)**
- **KR0079 2023.4Q item54(기발행 후순위채무) = 496.50 은 틀렸다.** raw p36 원문은 **300,359백만 → 3,003.59억**. 스크립트 docstring 도 `(후순위채무) 300,359` 라고 적어 놓고 DATA 에는 496.50 이 들어갔다. 496.50 = **KR0071(흥국생명) item53 신종자본증권 49,650백만**(같은 세션에서 p49 대조한 값, 마스터 KR0071 13분기 item53 전부 496.5)이 옆 회사 칸으로 새어 들어간 것. 스크립트 CHECKS 가 item53/54 를 안 덮어 못 잡았다. `DATA["2023.4Q"][54] = (3003.59, None)` 으로 정정 후 dry-run 재확인 필요.

**미착지 — 24칸이 아직 마스터에 없다**
- 답변 10일 후에도 `--apply` 가 안 돌았다: 마스터(2026-09-03 19:53 갱신본) KR0079 3분기 항목 46개뿐, 47-54 부재. 게이트 재실행(report_20260911T120403Z) 에서 `47_tier2_census`/`_post` YELLOW(TIER2_TABLE_ABSENT_APPLICABILITY_UNKNOWN) 3분기 그대로. 위 오기 정정 → `--apply` → 게이트 재실행 → 이 티켓 재확인 순서로 닫는다.

**부수 관찰 (이 티켓 차단 사유 아님, 별도 처리)**
- KR0080 2025.2Q item23-26: 원문 p18 은 0/0/0/0 인데 마스터에 행 자체가 없다(2023.2Q·2024.2Q·2024.4Q·2025.1Q~2026.1Q 도 동일 패턴). 답변의 "item1-27 전부 일치" 는 있는 행만 본 것. item23 자식 백필 레인으로.
- KR0010 2025.4Q item8(자본조정): 원문 "0", 마스터 값 "" (빈 문자열). 0-vs-결측 표기 불일치.
- KR0071 2024.4Q·KR0010 2025.4Q item53/54 는 원문에 값이 있는데(KR0071 49,650/123,407 · KR0010 -/672,249) 마스터 부재 — 답변의 spawn_task (c) 그대로 유효.

## 답변 (parser/kics, 2026-09-11, iter 2)

**(a) DATA 오기 정정 완료.** `scripts/fix_20260901_kr0079_scanned_section_tier2.py` 의
`DATA["2023.4Q"][54]` 를 496.50 → **3003.59** 로 정정(496.50 은 KR0071 item53 신종자본증권
49,650백만이 옆 회사 칸으로 새어든 값이었던 것으로 재확인). raw p36 을 fitz 190dpi 로
**독립 재렌더링**해 직접 읽었다 — "(기발행 후순위채무) 300,359" 확인(스크립트 docstring 은
이미 맞았고 DATA 리터럴만 틀렸었다는 재확인 판정과 일치). 같은 렌더에서 나머지 6개 항목
(47/48/49/50/51/52·53)도 DATA 와 전부 일치하는 것을 육안 재확인.

**(b) 적용 완료.** `--apply` 실행 → **INSERT 24칸 / UPDATE 0칸**, 항등식 4종(item51==item47
UNCAPPED · item50+item51==item52 · item48==item14×50% · item52==item1) 3분기 전부 GREEN.
게이트 재검증: KR0079 세 분기 `47_tier2_census`/`47_tier2_census_post`/`53_tfi_memo_rows`
전부 **GREEN**(`_post` 만 항목53/54 값_적용후가 원문 자체에 없어 정상 SKIP).

**(c) 부수 관찰 3건 — 2건 처리, 1건 재스코프 후 이번 라운드는 보류:**

1. **처리함 — KR0010 2025.4Q item8(자본조정) 0-vs-결측.** raw p68([경과조치 적용 전
   지급여력비율 세부], 190dpi 렌더 직접판독) "4. 자본조정" 행이 25.4Q/25.3Q/25.2Q **세
   분기 다 "0"** 으로 인쇄됨(이 표는 이 회사가 자본감소분(TAC) 미적용이라 적용후는 항상
   적용전과 동일 — 이웃 항목 7·9 가 이미 값=값_적용후 미러링돼 있는 것과 동일 패턴).
   값/값_적용후 둘 다 `"" → "0"` 정정.
2. **처리함 — item53/54 마스터 부재 4셀.** 둘 다 SCANNED_SECTION 이라 fitz get_text() 는
   0자를 반환(확인됨) — 190dpi 렌더 직접판독만이 경로다. KR0071 2024.4Q raw p49(0-idx 48):
   "(기발행 신종자본증권) 49,650" · "(기발행 후순위채무) 123,407" → 496.50 / 1234.07억.
   KR0010 2025.4Q raw p69: "(기발행 신종자본증권) -" · "(기발행 후순위채무) 672,249" →
   0.00(대시=0, 저장소 관례) / 6722.49억 — 같은 페이지의 47/48/49(14138.32/7415.83,
   31823.16/31823.16, 57670.39/57670.39)가 마스터 기존값과 소수점까지 일치해 판독법 자체가
   교차검증됨. 값_적용후는 두 표 다 해당 칸이 빗금 처리라 미기재(47-54 나머지 항목과 동일
   관례). 신규 4셀 전부 UPSERT.
3. **재스코프만 하고 이번 라운드는 미처리 — KR0080 item23-26.** 마스터 census로 정확히
   재봤다: 이 회사 13분기 중 **8분기**(2023.2Q·2024.2Q·2024.4Q·2025.1Q·2025.2Q·2025.3Q·
   2025.4Q·2026.1Q)가 전부 item23-26 행 자체가 없다 — 원 티켓이 예로 든 2025.2Q 하나가
   아니라 8분기×4항목=**32셀** 규모다. 각 분기 raw를 개별 렌더 확인해야(이 회사는
   BORDERLINE/스캔 혼재라 텍스트 신뢰 불가) 하는데 이번 라운드 시간예산 안에서 8분기를
   전부 못 돌았다 — 근거 없이 "0 disclosed" 로 일괄 UPSERT하면 "틀린 값을 싣느니 빈 칸"
   원칙 위반이라 손대지 않았다. `TODO_parser_kics.md` 에 정확한 스코프(8분기 목록)로
   다음 라운드 항목 등재.

**게이트**: `validate_kics_disclosure.py` RED=36(불변)·blocking RED=0.
`validate_data_contract.py` RED=0 YELLOW=88.

**변경 파일**: `kics_disclosure.json`(+24행 KR0079, +4행 KR0010/KR0071 item53/54, item8 1셀
정정) · `scripts/fix_20260901_kr0079_scanned_section_tier2.py`(DATA 오기 정정) · 신규
`scripts/fix_20260911_side_observations_tier2_item8.py`.

status: answered (원 sender 재확인 필요 — KR0080 item23-26 은 미처리, 다음 라운드용으로
TODO 에 스코프 등재함)

## 종결 재확인

재확인(orchestrator가 validation 대행, 2026-09-12): KR0079 2023.4Q item54 = 3003.59 마스터 실측 · TFI 24칸 적재(행수 25,458→25,486) · `47_tier2_census`/`_post` KR0079 YELLOW 소멸 · 차단 RED 0. 부수 KR0010·KR0071 5셀 처리, KR0080 item23-26(32셀)은 `TODO_parser_kics.md` KR0080-2326 으로 이월. **resolved.**
