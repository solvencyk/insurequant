---
from: owner
to: publishing
created: 20260912T0530Z
status: resolved
route: assemble
company: JP_MULTI
period: FY2025
track: J-ESR
supersedes: 20260912T0446Z
---

## 미결 (owner) — `jp/jesr_esr.json` 부모-자식 중복 제거 (같은 자본을 두 단위로 두 번 표시하지 않기)

**배경.** owner 2026-09-12 실측 지적: 현재 15사 중 2곳이 **부모-자식 중복**이다 — 소니생명保険(solo 162%)의 parent가
소니FG(group 177%, 이미 posted), 明治安田損害保険(solo 743.2%)의 parent가 明治安田生命保険(group 208%, 이미 posted).
같은 회사그룹의 자본이 서로 다른 단위(개별법인 vs 그룹연결)로 두 번 랭킹에 올라가 있어 owner 가 "연결/별도 니가 정해서
통일하라"고 지시. 결론: **부모가 이미 posted 되어 있으면 자회사 solo 행은 페이지 JSON 에서 뺀다.** au損害保険 은
parent=KDDI(보험사 아님, posted 안 됨)라 중복이 아니므로 그대로 둔다.

**일반 규칙(회사명 하드코딩 금지 — 10월 말 재census 때 다른 회사 조합에도 자동 적용돼야 한다).**
`J-ESR/jp_insurers.csv` 의 `parent_group` 열을 조인 키로 쓴다: census 의 `posted` 레코드 중 `category` 가
`子会社`로 시작하는 행에 대해, 그 행의 `parent_group` 값이 **다른 posted 레코드의 `company_jp` 안에 포함되는 문자열인지**
확인한다(예: `parent_group="ソニーFG"` ⊂ `company_jp="ソニーフィナンシャルグループ"`). 포함되면 그 자회사 행을
`jp/jesr_esr.json` 의 `records` 에서 제외한다. `parent_group` 이 공란이거나 어떤 posted `company_jp` 에도
안 걸리면(= 부모가 보험사가 아니거나 미공시) 제외하지 않는다.

**할 일.**
1. `J-ESR/build_jesr_page_json.py` 에 이 dedup 을 self-check **이후, `jp/jesr_esr.json` 쓰기 직전**에 넣는다.
   `J-ESR/jesr_master.json` (원본, 15사 전부 유지)과 `jp/jesr_esr.json` (dedup 후, 화면용)이 **이제부터 다르다** —
   두 파일이 바이트 동일해야 한다는 기존 self-check 문구는 지우고, 대신 "jesr_master 레코드 수 - 제외된 자회사 수
   == jp/jesr_esr 레코드 수"를 검사하도록 self-check 을 바꾼다.
2. `_meta` 에 `excluded_subsidiaries`: 제외한 회사의 `company_en`·`parent`·자기 esr_pct 리스트를 추가한다
   (화면엔 안 쓰지만 티켓 답변·감사용). 이번 라운드 기대값: 정확히 2건(Sony Life Insurance, Meiji Yasuda Non-Life).
3. 재실행 후 `jp/jesr_esr.json` 이 13 레코드인지 확인. `git diff jp/jesr_esr.json` 로 au損害保険 이 그대로 남아있는지,
   소니생명·明治安田損害保険 이 빠졌는지 확인.

**규칙.** python 풀패스, 멀티라인 `python -c` 금지, UTF-8 BOM 없음. `J-ESR/jesr_master.json` 은 전체 15사 유지가
정본(제외는 화면용 파일에서만). 서브에이전트 생성 금지. 끝나면 답변란에 제외 2건 확인 로그와 최종 레코드 수를 적고
`status: answered`. `TODO_jp.md`·`docs/changelog_jp.md` 갱신.

## 답변 (publishing, 2026-09-12)

`J-ESR/build_jesr_page_json.py` 에 `apply_subsidiary_dedup()` 을 추가했다. 회사명 하드코딩 없이 일반 로직으로 짰다: census
`category` 가 `子会社` 로 시작하는 posted 레코드에 대해 `jp_insurers.csv` 의 `parent_group` 을 조인 키로 읽고, 그 값이
(직접 부분문자열, 또는 "HD"→"ホールディングス"/"FG"→"フィナンシャルグループ" 로 확장한 부분문자열) 다른 posted
`company_jp` 안에 들어가면 그 자회사 행을 `jp/jesr_esr.json` 에서만 제외한다(`J-ESR/jesr_master.json` 은 손대지 않음).
self-check 은 "두 파일 바이트 동일" 대신 "`jesr_master` 레코드 수 - 제외 수 == `jp/jesr_esr` 레코드 수" 로 교체했고,
`_meta.excluded_subsidiaries` 에 company_en·parent·esr_pct 를 남긴다.

**재현 명령:**
```
PYTHONIOENCODING=utf-8 C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe J-ESR/build_jesr_page_json.py
```

**실행 로그:**
```
wrote J-ESR/jesr_master.json  (15 records)
wrote jp/jesr_esr.json  (13 records, excluded=2)
census: {'total': 79, 'posted': 15, 'not_yet': 62, 'not_found': 2}
excluded_subsidiaries: [
  {'company_en': 'Meiji Yasuda Non-Life', 'parent': 'Meiji Yasuda Life Insurance', 'esr_pct': 743.2},
  {'company_en': 'Sony Life Insurance', 'parent': 'Sony Financial Group', 'esr_pct': 162.0}
]
```

**제외 2건 확인:**
- Sony Life Insurance (solo 162%) → parent Sony Financial Group (group 177%, posted) — 제외됨.
- Meiji Yasuda Non-Life (solo 743.2%) → parent Meiji Yasuda Life Insurance (group 208%, posted) — 제외됨.
- au Non-Life (parent KDDI, 보험사 아님·미posted) — `jp/jesr_esr.json` 에 그대로 남음(확인: `git diff jp/jesr_esr.json` 에 au 항목 무변화).

**최종 레코드 수:** `J-ESR/jesr_master.json` 15 (변경 없음, `generated_at` 타임스탬프만 갱신) / `jp/jesr_esr.json` 13 (요구값과 일치).

변경 파일: `J-ESR/build_jesr_page_json.py`, `J-ESR/jesr_master.json`, `jp/jesr_esr.json`. `TODO_jp.md`·`docs/changelog_jp.md`
갱신 완료. 라이브 반영(main push)은 아직 안 함 — `jp/` 는 이번 라운드 keep-list 에 없고(`docs/agents/claude-agent-publishing.md`
§12), 라이브 반영은 owner 가 `/jp/` 초안을 검토한 뒤 별도 승인 사항으로 남아 있다.
