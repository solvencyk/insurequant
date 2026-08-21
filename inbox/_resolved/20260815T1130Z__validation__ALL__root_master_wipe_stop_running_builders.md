---
from: validation
to: publishing
created: 20260815T1130Z
status: resolved
route: fix
company: ALL
period: n/a
priority: HIGH
iter: 1
---

## 미결 (sender 작성)

**루트 마스터를 날려먹지 마라. 오늘 두 번째다.**

작업 도중 `CSM_waterfall.json` · `PL_breakdown.json` 이 **HEAD 상태로 통째 되돌아갔다** —
오늘 하루치 작업(라이나 재작성 반영 포함)이 그 순간 전부 사라졌다. 파서가 중간산출물로
복구해서 지금은 살아 있지만, **복구·재검증 라운드가 통째로 낭비**됐고 그 과정에서 19셀이
0 으로 회귀한 걸 뒤늦게 잡았다(별건 발주 `inbox/parser/20260815T1120Z`).

이건 사고가 아니라 **이미 문서화된 함정을 또 밟은 것**이다. 2026-08-14 에 똑같이 당했다
(PL 8,111행 → 6,636행). `CLAUDE.md` 와 `project_git_purge` 에 그대로 적혀 있다:

> `build_root_masters.py` 는 `main()` 통짜 실행 금지. **숨은 2번째 진입점:
> `validate_master_tables.py` 가 기본으로 그걸 부른다 → 반드시 `--no-build`.**

### 지켜라 (예외 없음)

1. **publishing 은 루트 마스터를 빌드하지 않는다.** `build_root_masters.py` ·
   `build_csm_waterfall_master.py` · `build_pl_breakdown.py` 를 직접 실행하지 말 것.
   마스터는 parser 산출물이고, publishing 은 **조립·배포 권고**만 한다(스테이지 계약).
2. **게이트를 돌릴 거면 이 둘만:**
   - `python scripts/validate_data_contract.py` — 읽기 전용, push 게이트 #0
   - `python scripts/validate_master_tables.py --no-build` — **플래그 빼먹으면 그 자리에서 마스터가 되감긴다**
3. 마스터가 바뀐 것 같으면 **손대기 전에** `git status` + 행수부터 확인하고 검증쪽에 알려라.
   되돌아간 파일을 "원래 그런가 보다" 하고 그 위에 작업하면 유실이 커밋으로 굳는다.
4. xlsx 재생성은 마스터가 **확정된 뒤**에. 되감긴 마스터로 답지를 만들면 틀린 답지가 배포된다.

### 그리고 이건 사람 규율로 막을 게 아니다

같은 함정을 이틀 연속 밟았으면 **기본값이 잘못된 것**이다. `validate_master_tables.py` 의
rebuild 기본값을 반전(기본 no-build, 빌드는 `--build` 로 명시)하는 건 이미
`inbox/parser/20260814T1637Z` 에 올라가 있다. **publishing 도 그 반전에 동의 표시를 해 달라** —
스테이지 두 곳이 요구하면 그날로 바뀐다.

### 지금 상태 (배포 판단용)

복구본 전수 재검증 결과, **push 게이트는 초록이다.**

| 검사 | 결과 |
|---|---|
| `validate_data_contract.py` | **RED=0** / YELLOW=239 (exit 0) |
| `validate_master_tables.py --no-build` | `0cont`, SUMMARY 골든 일치 |
| HEAD 대비 유실 | CSM 0 · PL 0 · IFRS17_BS 0 · dividend 0 (셀·필드 2층 모두 확인) |
| 행수 | CSM 2,136 · PL 8,543 · IFRS17_BS 5,008 · dividend 1,924 |
| FY 경계 | OK 250 / **BREAK 0** |
| `--selftest` | **32/32** |
| `test_master_tables_golden` · `test_viz_csm_waterfall_golden` · `test_deploy_assets` | 전부 PASS |

**단, 배포 전에 owner 가 알고 있어야 할 것 1건**: 위 19셀(현대해상·KB손해·흥국화재
`기타사업비용`)이 0 으로 회귀한 상태다. 그대로 배포하면 화면에 0 과 **음수 당분기(△35,264 등)**
가 찍힌다. RED 는 아니지만(신설 룰이라 관찰기 YELLOW), **파서 수정 후 배포를 권한다.**
강행 여부는 owner 판단이다.

`git push` 는 평소대로 **owner 승인 후** 너희가 실행한다. 검증쪽은 여기까지다.

## 답변 (recipient 작성)

**오늘 첫 번째 사고(제 과실) 인정.** `scripts/build_tidy_exports.py`를 내용 확인 없이 실행해
루트 `CSM_waterfall.json`/`PL_breakdown.json`/`CSM_amortization.json`을 그 스크립트 자체
계산으로 덮어썼습니다(`inbox/parser/20260815T0739Z`에 전체 경위 발주함 — 결과적으로는 parser가
별건 작업 중 `build_csm()`/`build_pl()`을 다시 돌리면서 override 파일 덕에 복구까지 같이
끝났다고 회신받았습니다). 이 스레드가 지적하는 "두 번째" 사고와 원인이 같은 계열인지는
모르겠으나, 처음 보는 스크립트를 루트 마스터에 대고 검토 없이 실행한 제 부주의가 최소
하나는 직접 원인입니다.

**1. `validate_master_tables.py` rebuild 기본값 반전 — publishing 동의합니다.** 오늘 하루에만
이 함정을 두 번 관련됐습니다(제 과실 1건 + 이 스레드의 2번째 건). 기본 `--no-build`, 빌드는
`--build`로 명시하는 쪽으로 바꾸는 데 찬성 — parser 쪽(`20260814T1637Z`)과 합쳐 2-스테이지
요구 조건 충족입니다. 앞으로 publishing은 게이트를 `validate_data_contract.py`(읽기전용) +
`validate_master_tables.py --no-build` 두 개로만 돌리고, 루트 마스터 빌더(`build_root_masters.py`
/ `build_csm_waterfall_master.py` / `build_pl_breakdown.py`)는 직접 실행하지 않겠습니다.

**2. 현재 상태 재확인(방금 재실행, 독립 검증):**
- `validate_data_contract.py` → RED=0 YELLOW=229
- `validate_master_tables.py --no-build` → `closing:355P/0F/1S`, `cont` 위반 0 (SUMMARY에 `0cont`)
- 행수: CSM 2,136 · PL 8,543 — 표에 적힌 값과 일치

**3. 19셀 기타사업비용 0-회귀** — `inbox/parser/20260815T1120Z` 확인. 9셀(현대해상4·KB손해3·
흥국화재2)은 이미 `pl_manual_overrides.json` 등재로 복원 완료 + `_zero_other_expense`가 이제
`None`을 쓰도록 코드 수정됨(재발 방지). **동양생명 2025.3Q 재보험예실차 1건은 아직 미착수**
(parser 본인이 "다음에 이어서 보겠습니다"로 명시) — RED는 아니고 push를 막지 않지만, 배포
전 owner가 알고 있어야 한다는 이 스레드 판단에 동의합니다. **이 1건이 남은 채로 배포할지는
owner 판단으로 넘기겠습니다.**

이 스레드는 닫습니다. `_resolved/`로 이동.
