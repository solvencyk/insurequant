---
from: owner
to: parser
created: 20260814T0232Z
status: resolved
route: backlog
company: MULTI
period: ALL
lane: ifrs17
priority: HIGH
iter: 1
---

## 미결 (sender 작성)

**owner 지시 (2026-08-14): `equity_composition.json`(항목 1-49)은 아카이브한다.**
*"내가 처음에 하려고 했던 항목 ㅈㄴ 많은 것들인데, 일단 archive에 넣어놓고 나중에 언젠가
필요해지면 그때 쓰지."*

**지우지 말고 옮겨라.** 앞으로 17BS 정본은 **`IFRS17_BS.json`**(항목 1-5) 한 벌이다.

### 옮길 것 → `archive/2026-08_equity_composition/`

기존 관례 그대로(`archive/2026-07_orphan_artifacts` 형식). **`git mv`** 로 이력 유지.

```
equity_composition.json
equity_composition_provenance.json
scripts/build_equity_composition.py
scripts/emit_equity_composition_provenance.py
scripts/fill_equity_item10_notes.py          ← 아래 단서 확인 후 판단
tests/test_equity_composition_golden.py
tests/fixtures/equity_composition_golden.json
```

한 줄짜리 `README.md` 를 같이 넣어라: 왜 아카이브했는지 + 되살리려면 뭘 되돌려야 하는지.

### 남길 것 (여기서 사고 난다)

1. **`scripts/build_equity_composition_tier2.py` 는 아카이브하지 말 것.**
   `build_ifrs17_bs.py:28` 이 `from scripts.build_equity_composition_tier2 import TIER2, parse_filing`
   로 물고 있다. 옮기면 새 마스터 빌드가 죽는다. 이름이 헷갈리면 **함수만 옮겨 이름을 바꾸든지**,
   아니면 그냥 그대로 둬라(둬도 무방 — 판단은 너에게 맡긴다).
2. `data/_gold/equity_census_exceptions.json` · `equity_value_overrides.json` 은 그대로 둔다
   (validation 이 쓰는지 그쪽에서 정리한다).
3. `data/dart/_fs_api_cache/` 는 절대 건드리지 말 것 — 새 마스터가 쓰는 소스다.

### 같이 줄어드는 것 — 직전 발주 `20260814T0216Z` 범위 축소

- **P-1(OFS 고정) · P-2(AOCI 태그 조건부 채택)는 `IFRS17_BS.json` 한 곳에만 적용하면 된다.**
  "두 빌더 모두에 적용"은 무효. P-6(마스터 두 벌 대조)도 무효 — 한 벌이 됐다.
- **P-3(항목 20-31) 전부 무효** — 아카이브와 함께 사라진다.
- **P-4(BS 세부 42항목) 취소는 그대로 유효.**
- **P-5(준비금 3종)는 유효하고, 이제 `IFRS17_BS.json` 에 붙인다.** 현재 항목 5(해약환급금준비금
  적립액) 102건만 있다. 비상위험준비금 기말 / 대손준비금 적립액을 **항목 6·7 로 추가하되
  "가능하면", 없으면 pass.** API 태그(`ifrs-full_ReserveForCatastrophe` /
  `dart_RegulatoryReserveForCreditLoss`)로 잡히는 것 우선.
- item10-notes 주석 스크래핑은 **해약환급금준비금 하나만** 계속 유효하다. `fill_equity_item10_notes.py`
  를 아카이브할지 `IFRS17_BS.json` 대상으로 고쳐 살릴지는 네가 판단해서 답신에 적어라
  (downloader 티켓 `20260814T0000Z` 으로 raw 24셀이 오는 중이다).

### 골든

`tests/test_equity_composition_golden.py` 를 아카이브하면 `CLAUDE.md` 골든표에서도 그 행을 지워야
한다 — `pytest tests/test_deploy_assets.py::test_golden_table_docs_agree_with_tests` 가 dangling 을
막는다(안 지우면 테스트가 FAIL). `IFRS17_BS.json` 골든을 새로 만들지 여부는 판단해서 답신에.

### 확인

- `pytest tests/test_deploy_assets.py` 통과
- `python -c "import scripts.build_ifrs17_bs"` 가 죽지 않는지(위 1번 함정)
- 남은 참조 0건: `grep -rn equity_composition --include=*.py --include=*.html .`
  (docs/TODO/changelog 의 **과거 이력 서술은 고치지 말 것** — 이력이다)

## 답변 (recipient 작성)

**아카이브 완료.** (파일이 전부 미커밋 상태라 `git mv`가 "not under version control"로 실패해서
그냥 `mv` — 애초에 커밋된 적이 없어 지킬 이력도 없다.)

### 옮긴 것
`equity_composition.json` · `equity_composition_provenance.json` ·
`scripts/build_equity_composition.py` · `scripts/emit_equity_composition_provenance.py` ·
`tests/test_equity_composition_golden.py` · `tests/fixtures/equity_composition_golden.json`
→ `archive/2026-08_equity_composition/`. **`scripts/fill_equity_item10_notes.py`도 같이
옮겼다** — 판단: `build_ifrs17_bs.py`가 이제 자체 롤포워드(아래)로 같은 역할을 대체하고,
이 스크립트는 archive되는 `build_equity_composition.py`의 `LABELS`를 import하므로 남겨두면
어차피 죽는다.

### 남긴 것
`scripts/build_equity_composition_tier2.py`는 그대로 (지시대로 — `build_ifrs17_bs.py`가
`TIER2`/`parse_filing` 을 계속 문다). `data/_gold/equity_census_exceptions.json` ·
`equity_value_overrides.json`은 이미 validation 쪽이 옮겨놓은 상태였다(내가 손 안 댐).
`data/dart/_fs_api_cache/`는 미접촉.

### CLAUDE.md 골든표
`test_equity_composition_golden.py` 행 삭제. **`IFRS17_BS.json` 골든은 이번엔 신설 보류** —
오늘 이 스레드 안에서 스키마가 두 번 바뀌었다(항목6·7 추가 + 롤포워드 로직 추가). 값이
가라앉은 다음 세션에 신설을 권한다.

### 확인
- `python -c "import scripts.build_ifrs17_bs"` — OK.
- `pytest tests/test_deploy_assets.py` — **9/10 pass, 1 fail (예상된 실패)**:
  `IFRS17.html`이 아직 `equity_composition.json`을 fetch하는데(Panel 7, 267행) 그 사실이
  `claude-agent-designer.md`에 없다는 문서 동기화 체크다. **designer의 `20260814T0232Z`
  스왑이 끝나야 사라진다** — 파서 쪽에서 고칠 항목 아님(HTML은 designer 소관).
- `grep -rn equity_composition --include=*.py --include=*.html .` 잔여 5건:
  `IFRS17.html`(위 — designer 대기) · `build_equity_composition_tier2.py`(지시대로 존치,
  자기 docstring/dead main()에서만 언급) · `build_ifrs17_bs.py`(아카이브 사유를 설명하는
  docstring, 기능 참조 아님) · `fetch_kr0150_2026q1.py`(발주 근거를 적은 주석 1줄) ·
  `validate_data_contract.py`(validation 소관, `check_ifrs17_bs`로 이관됐다는 주석) —
  전부 인지·의도된 것이라 추가 조치 없음.

### 같이 발견 — item10-notes 재실행보다 나은 대체 구현
`fill_equity_item10_notes.py`를 그대로 살리는 대신, **owner가 마스터xlsx에서 직접 손보정한
해약환급금준비금 기적립액 롤포워드 규칙**(동일회기 내 전분기 유지, 신규회기 1분기=전기말
기적립액+전입액)을 `build_ifrs17_bs.py`에 코드로 이식했다. 부수로 **흥국생명 전입액 부호
버그**(DART 조정이익 주석이 "당기순이익에서 차감 예정"으로 프레이밍해서 파서가 그대로
음수로 읽던 것 — 실제 준비금 증가 관점에선 양수여야 함, 같은 필링의 평문 문장
"적립예정액은 340,381백만원입니다"로 교차검증)도 `parse_filing()`에서 일반적으로(흥국생명
전용 패치 아님) 고쳤다. 재검증: 흥국생명 2025.1Q~4Q 기적립액=6,257 고정,
2026.1Q=346,638 — owner 수기값과 정확히 일치.

### AOCI(항목4) 마저 — validation의 `20260814T0500Z` B-2 잔여도 이 세션에서 해소
Tier-1(한화생명·흥국생명) 12셀은 기존 폴백으로 이미 해소돼 있었다. **AIA생명·아이엠라이프
2사 4셀**은 새 태그가 아니라 — ① AIA: `기타포괄손익누계액(주석29)`처럼 라벨에 괄호 각주가
붙어 정확일치가 깨짐 ② 아이엠라이프: `IV.` 같은 ASCII 로마숫자가 섹션헤더 정규식에만 있고
행단위 lstrip엔 없어서 prefix가 안 벗겨짐 — 두 라벨 정규화 버그였다. `parse_filing()`에
일반 수정(각주 suffix 스트립 + 행단위 로마숫자 정규식 통일), 3사·4분기 raw로 재확인.

### 잔여 — `IFRS17_BS.json` census RED 42건 (validation `20260814T0500Z` B-1 계열)
AIG손해보험·하나손해보험·신한이지손해보험(각 2025.4Q)·IBK연금보험·메트라이프생명보험
(각 3개년 4Q)·비엔피파리바카디프생명보험(2024·2025.4Q) = 6개사 11셀. **원인 3가지 확인,
전부 raw로 재현·특정 완료:**
1. AIG: BS 각주가 `<주석13,33,35>`(꺾쇠, 괄호 아님) + 총계행이 `[label,'','',값,'',값]`
   같은 빈칸-스페이서 컬럼구조라 `_bs_row_value`의 `row[-2]` 가정이 안 맞는다.
2. 하나손해: 같은 빈칸-스페이서 계열이지만 **행마다 오프셋이 다르다**(각주번호 셀이 끼는
   행과 안 끼는 행이 같은 표 안에 공존) — 표 전체에 균일한 컬럼 규칙이 없다.
3. 비엔피파리바카디프: "자산"으로 시작하는 첫 테이블을 고르는 현재 휴리스틱이, 본문 앞쪽의
   무관한 표(관계기업 투자 주석, 첫 행이 우연히 `['자산', '<유의적인 영향력을 행사하는
   기업>', ...]`)에 낚여 진짜 BS 표까지 못 간다.
메트라이프/IBK연금은 시간 관계상 개별 raw 확인은 안 했으나 셋 중 하나와 같은 계열로 추정된다.
**셋 다 서로 다른 표-구조 이슈라 단일 수정으로 안 묶인다 — 이번 라운드에서 고치지 않았다**
(validation이 "본문에 없다면 보고만 해도 된다"고 명시한 바 있어 그 기준을 씀). 폐쇄식이 이
스키마엔 없어 잘못 고치면 게이트가 못 잡는다는 점도 감안, 각각 별도로 좁게 고치는 편이 안전
하다고 판단 — 후속 세션 권장.

### 마스터 xlsx — 아직 재생성 안 함 (의도적)
`scripts/build_master_xlsx.py`의 "17BS" 시트 소스를 `equity_composition.json` →
`IFRS17_BS.json`로 갈아끼웠다(안 그러면 아카이브 이후 이 스크립트가 파일없음으로 죽는다).
**단, 실제로 xlsx를 재생성하진 않았다** — `insurequant_master_tables.xlsx`는
`ExcelWriter(mode="w")`라 실행할 때마다 파일 전체를 새로 쓰는데, owner가 손으로 만든
"17BS_PIVOT" 시트(이 빌더가 만드는 목록에 없음)와 "17BS" 시트의 수기 서식이 통째로 날아간다.
재생성 원하면 말해달라 — 대신 그 전에 새 7항목 스키마(1-7)로 피벗을 다시 짜야 할 수 있다는
점만 미리 알아두면 됨.
