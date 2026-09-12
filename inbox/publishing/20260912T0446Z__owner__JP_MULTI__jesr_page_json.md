---
from: owner
to: publishing
created: 20260912T0446Z
status: answered
route: assemble
company: JP_MULTI
period: FY2025
track: J-ESR
---

## 미결 (owner) — `/jp/` 일본 ESR 페이지용 데이터 JSON 조립 (`jp/jesr_esr.json`) [J-ESR 킥오프 2차 조각]

**배경.** owner 2026-09-12: `/jp/` 일본어 페이지 초안을 만든다(designer 티켓 `inbox/designer/20260912T0446Z`).
화면 규칙 "그래프 데이터는 HTML 인라인 금지, JSON fetch" 에 따라 페이지가 읽을 JSON 이 먼저 필요하다.
입력은 이미 있다: `J-ESR/fy2025_esr_census_20260912.csv`(79사 census, posted 15) + `J-ESR/jesr_sources_2026Q1.csv`
(6월 수집 11사, 총자산·목표비율 등 보조 열) + 기존 `J-ESR/jesr_master.json`(`build_jesr_master.py` 산출, 6월 스키마).

**할 일.**
1. `J-ESR/build_jesr_page_json.py` 신규(stdlib 만). 입력 = census csv 의 `fy2025_esr_status == posted` 15행 + sources csv 의
   보조 열(회사명 `company_jp` 로 조인; 없으면 null). 출력 두 곳에 **같은 내용**: `J-ESR/jesr_master.json`(기존 파일 교체 —
   `_meta` 에 `built_from` 두 입력 파일명·`census` 집계 포함) 과 배포용 `jp/jesr_esr.json`.
2. 스키마(designer 와 합의된 고정 계약 — 키 이름 바꾸지 말 것):
   ```json
   {
     "_meta": {"as_of": "2026-03-31", "as_of_label_ja": "2026年3月31日", "generated_at": "<UTC ISO>",
               "built_from": ["fy2025_esr_census_20260912.csv", "jesr_sources_2026Q1.csv"],
               "next_update": "2026-10-31",
               "census": {"total": 79, "posted": 15, "not_yet": 62, "not_found": 2}},
     "records": [
       {"company_jp": "...", "company_en": "...", "ticker": "8766" | null,
        "sector": "life" | "nonlife" | "reinsurance",
        "category": "<census category 원문>", "scope": "group" | "solo",
        "esr_pct": 238.0, "basis": "J-ICS", "as_of": "2026-03-31",
        "preliminary": false, "total_assets_bn_jpy": 319600 | null, "target_pct": "190%+" | null,
        "doc_type": "...", "doc_date": "2026-05-20" | null, "source_url": "https://...", "notes": "..."}
     ]
   }
   ```
   `sector` 는 census `sector` 열(생보/손보/재보험 한자 표기)을 위 세 값으로 매핑. `scope` 는 census `esr_scope`.
   `preliminary` 는 census notes/doc_type 에 속보·잠정·速報 류 표현이 있으면 true(어느 표현을 잡았는지 notes 에 남김).
   `esr_pct` 는 float. 정렬 = esr_pct 내림차순.
3. 검증(스크립트 안 self-check, 실패 시 exit 1): records 정확히 15 · esr_pct 전부 100~1000 · scope/sector 값 집합 검사 ·
   source_url 전부 https · as_of 전부 2026-03-31 · `_meta.census` 합 = total. 두 출력 파일 바이트 동일.
4. `jp/` 폴더는 배포 대상이 될 예정이다. 이번엔 **keep-list·xlsx 시트·public_exports 는 건드리지 말 것**(초안 단계, 라이브 반영은
   owner 승인 후 별도 티켓). 다만 답변란에 "라이브 반영 시 필요한 것" 을 목록으로 적어라(keep-list 추가 경로, master xlsx
   시트 추가 여부, status_report 4절 '화면 fetch ↔ 마스터 시트' 검사에 걸리는지).

**처리 규칙.** 마스터 JSON 통째 read-modify-write 금지 원칙은 루트 마스터 얘기이고 `jesr_master.json` 은 이 스크립트가
유일한 생산자라 교체 OK. python 은 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`. 멀티라인 `python -c` 금지.
파일 전부 UTF-8(BOM 없음). 끝나면 답변란에 15사 표(회사 영문명·sector·scope·esr·preliminary)와 위 4번 목록을 적고
`status: answered`.

## 답변 (publishing, 2026-09-12)

**실행.** `J-ESR/build_jesr_page_json.py` 신규 작성(stdlib만: csv/json/re/sys/datetime/pathlib), self-check 내장.
재현 명령:
```
cd C:/Users/sangwook.cho/Desktop/insurequant
PYTHONIOENCODING=utf-8 C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe J-ESR/build_jesr_page_json.py
```
실측 출력(exit 0):
```
wrote J-ESR/jesr_master.json and jp/jesr_esr.json  (15 records)
  census: {'total': 79, 'posted': 15, 'not_yet': 62, 'not_found': 2}
  preliminary=5: ['LifeNet Life Insurance', 'Asahi Life Insurance', 'Fukoku Life Insurance', 'Japan Post Insurance', 'Sumitomo Life Insurance']
```
`cmp J-ESR/jesr_master.json jp/jesr_esr.json` → 바이트 동일 확인. 두 파일·스크립트 모두 BOM 없는 UTF-8(`head -c3 | xxd -p` → `7b0d0a`/`23202d`, BOM 시그니처 `efbbbf` 아님). `ast.parse` 통과.
`git status --short J-ESR/ jp/` → `M J-ESR/jesr_master.json`, `?? J-ESR/build_jesr_page_json.py`, `?? jp/` 만 변경 — 루트 마스터·HTML·xlsx·public_exports·keep-list 무변경.

**join 규칙(티켓에 명시 안 된 부분, 판단 근거 기록).** `basis`/`total_assets_bn_jpy`/`target_pct`는 sources csv 행의 `as_of`가
census 행의 `as_of`(2026-03-31)와 **일치할 때만** 조인했다 — 미즈호 4개 상호회사(日本生命·住友生命·明治安田生命·富国生命)는
sources csv에 2025-03-31~2025-09-30 구치만 있어, 조인하면 새 posted 값에 옛 분기 총자산/목표비율/basis가 잘못 붙는다
("틀린 값을 싣느니 빈칸"). `ticker`는 시간불변이라 as_of 무관 조인. `basis`는 조인 실패 시 상수 기본값 `"J-ICS"`(SOMPO만
sources 원본이 `"J-ICS_VaR99.5"`라 그대로 반영). `preliminary`는 notes+doc_type 문자열에 속보/잠정/速報 있으면 true, 검출
키워드를 notes 끝에 괄호로 남겼다(티켓 지시대로).

**15사 표 (esr_pct 내림차순):**

| company_en | sector | scope | esr_pct | preliminary |
|---|---|---|---|---|
| au Non-Life | nonlife | solo | 791.7 | false |
| Meiji Yasuda Non-Life | nonlife | solo | 743.2 | false |
| LifeNet Life Insurance | life | solo | 333.0 | true |
| Sompo Holdings | nonlife | group | 270.0 | false |
| Asahi Life Insurance | life | group | 258.9 | true |
| Fukoku Life Insurance | life | solo | 248.5 | true |
| Tokio Marine Holdings | nonlife | group | 238.0 | false |
| T&D Holdings | life | group | 222.0 | false |
| Japan Post Insurance | life | solo | 220.0 | true |
| MS&AD Insurance Group Holdings | nonlife | group | 214.0 | false |
| Meiji Yasuda Life Insurance | life | group | 208.0 | false |
| Sumitomo Life Insurance | life | group | 197.0 | true |
| Nippon Life Insurance | life | group | 195.0 | false |
| Sony Financial Group | life | group | 177.0 | false |
| Sony Life Insurance | life | solo | 162.0 | false |

**라이브 반영 시 필요한 것 (이번엔 미실행, 목록만).**
1. **keep-list 추가**: `jp/jesr_esr.json` + designer가 만들 `jp/*.html`을 `docs/agents/claude-agent-publishing.md` §1 표·§9
   keep-list에 추가. **실측 함정**: 4-페이지 하드코딩 목록(`["index.html","K-ICS.html","IFRS17.html","공시보고서.html"]`)이
   `claude-agent-publishing.md` §1 grep 스니펫 · `tests/test_deploy_assets.py` L27 `PAGES` · `tests/test_push_gate_wiring.py`
   L378 `_HTML` 세 곳에 그대로 박혀 있어(grep으로 확인), `/jp/` 페이지 경로를 이 세 곳에 안 넣으면 그 페이지의 fetch가
   세 게이트 어디서도 "통과"가 아니라 **아예 안 보이게** 된다(invariant #1: 게이트가 보는 파일=사용자가 보는 파일).
2. **master xlsx 시트**: 없음, 필요 없음(확인). `scripts/build_master_xlsx.py`의 `MASTERS`·`scripts/sync_master_xlsx_sheet.py`
   둘 다 grep에 "jesr" 매치 0 — J-ESR은 K-ICS/IFRS17 xlsx 체계 밖 독립 트랙. 시트를 만들지는 owner 결정 사항.
3. **`status_report.py` §4 검사**: 위 1번의 `_HTML`을 갱신하기 전까지는 `jp/jesr_esr.json` fetch를 아예 못 봐서 gap 리스트에도
   안 뜬다(안전한 게 아니라 무검사). `_HTML`을 갱신하면 그 순간 `MASTERS`에 대응 시트가 없어 GAP으로 잡힐 것 — 그때
   `PANEL_DERIVED_FROM`류 면제 등록이나 신규 시트 중 하나가 필요(2번과 연결).
4. 그 밖: `jp/` 폴더는 현재 `.gitignore`/keep-list 어디에도 안 걸려 있음(신규, 무변경 확인) — 배포 시 신규 추가.
