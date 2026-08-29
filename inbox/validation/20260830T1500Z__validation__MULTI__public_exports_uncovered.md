---
from: validation
to: validation
created: 20260830T1500Z
status: open
route: blind_spot
company: MULTI
period: MULTI
rule: PUBLIC_EXPORTS_UNCOVERED
lane: ifrs17
iter: 1
---

## 미결 (validation 작성)

`inbox/_resolved/20260830T0710Z__validation__MULTI__gold_overlay_mask_undetected.md` §7(곁가지 2)
에서 분리한 잔여다. 그 티켓의 gold 오버레이 배선은 끝났고(`GOLD_OVERLAY_*` 7룰, RED=0), 이건
같이 발견했지만 **범위 밖이라 손대지 않은** 축이다.

### 실측한 사각

`public_exports/` 의 어떤 파일도 **읽는 검증기가 없다.**

```
grep -rn "public_exports" scripts/validate_*.py     -> 0건
```

특히 `scripts/validate_live_artifacts.py` — 2026-08-25 에 "라이브 HTML 이 fetch 하는 .json 중
6개를 어떤 검사기도 안 읽고 있었다" 를 고치려고 만든 그 게이트 — 가 `public_exports/` 를
한 번도 언급하지 않는다. 쓰는 쪽은 `scripts/export_public_sheets.py`, 읽는 쪽은
`download-survey.js` 다(= 사용자에게 내려가는 파일).

**이건 불변식 1번("게이트가 검사하는 파일 = 사용자가 보는 파일")의 미배선 구멍이다.**
원 티켓을 쓰던 시점에는 실제로 갭이 열려 있었다 — `CSM워터폴.json` 의 KR0079 2025.2Q 항목1
`값_당분기` 가 public 20840.7 / 루트 20847.3 이었다(`28ab7f8` "기타" 블록 수정 반영 전).

### 지금 상태 (2026-08-30 전수 재측정)

`public_exports/CSM워터폴.json` 대 루트 `CSM_waterfall.json`:

| 항목 | 값 |
|---|---:|
| 행 수 | 2,172 / 2,172 |
| 키 불일치 (public 결손 · 루트 결손) | 0 · 0 |
| 값 불일치 (`값` 또는 `값_당분기`) | **0** |

즉 **지금은 닫혀 있다**(그 사이 parser/publishing 라운드가 재생성했다). 고칠 데이터는 없다.
문제는 **그게 닫혀 있는지를 아무도 안 보고 있다**는 것이다 — 다음에 벌어져도 똑같이 조용하다.

### 요청 — 룰 배선 (제안)

`scripts/validate_live_artifacts.py` 에 `public_exports/` 축 신설:

1. `PUBLIC_EXPORT_DRIFT` (RED): `public_exports/<X>.json` 의 셀이 대응 루트 마스터와 다르다.
   키 스키마가 다르다는 점에 주의 — public 쪽은 `원보험사코드` 가 없고 `원수사명` 으로 조인한다
   (실측). 조인 키를 잘못 잡으면 전건 미스로 조용히 통과한다.
2. `PUBLIC_EXPORT_MISSING_CELL` (RED): 루트에 있는 (회사, 분기, 항목)이 public 에 없다.
   결측은 SKIP 이 아니라 RED — 기대 그리드는 루트 마스터다.
3. `PUBLIC_EXPORT_STALE` (YELLOW): public 파일 mtime 이 대응 루트 마스터보다 오래됐다
   (값이 우연히 같아도 재생성이 밀린 것은 사실이고, 다음 변경에서 갭이 된다).
4. 배선 후 `scripts/prepush_check.py` 1c 절이 `validate_live_artifacts` 를 이미 부르는지
   **그 자리에서 확인**할 것 — 부른다(L88-93). 즉 그 파일에 넣으면 강제된다.
5. `tests/test_push_gate_wiring.py` · `tests/test_rule_coverage_manifest.py` 등재 + 변이시험.

### 먼저 답해야 할 것 (배선 전)

`public_exports/` 에 파일이 몇 개이고 **각각 어느 루트 마스터의 파생인지**를 먼저 전수 열거해야
한다. 하나만 배선하고 나머지를 두면 이 저장소가 반복해 온 "빠진 게이트를 눈치챌 때마다 룰을
한 개씩 베껴 심는" 패턴이 된다(`CLAUDE.md` ①b 절).

### 재현

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -c "import json,pathlib;pub=json.loads(pathlib.Path('public_exports/CSM워터폴.json').read_text(encoding='utf-8'));root=json.loads(pathlib.Path('CSM_waterfall.json').read_text(encoding='utf-8'));pi={(x['원수사명'],x['항목번호'],x['공시분기']):x for x in pub};ri={(x['원수사명'],x['항목번호'],x['공시분기']):x for x in root};print(len(pi),len(ri),len(set(ri)-set(pi)),sum(1 for k in set(pi)&set(ri) if pi[k].get('값')!=ri[k].get('값') or pi[k].get('값_당분기')!=ri[k].get('값_당분기')))"
```

## 답변 (validation 작성 — 처리 후)

<축 전수 열거 + 배선 결과 + 변이시험 + 훅 경로 확인 + 커밋 해시.>
