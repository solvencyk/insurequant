---
from: validation
to: jp
created: 20260913T1500Z
status: resolved
route: blind_spot
company: JP_MULTI
period: FY2025
rule: JP_SOURCE_URL_DEAD / JP_SOURCE_EXPIRING_HOST / JP_ESR_NOT_IN_SOURCE / JP_ESR_EDINET_MISMATCH
iter: 1
---

## 미결 (sender 작성)

포스트모템 `docs/postmortems/PM-2026-09-13_jp_secondary_source_and_dead_url.md` 의 **UH-18**.

2026-09-13 에 화면 15사 중 **3사에서 값·출처 오류**가 나왔는데(東京海上HD 238→268 · かんぽ 220→181 ·
明治安田生命 208.0→208.7, MS&AD 는 출처 문서 자체가 무관), jp 빌더 self-check 는 전부 통과했다.
self-check 가 census 안에서만 닫히는 자기참조라 **"출처가 살아 있나 / 그 문서에 그 숫자가 있나" 축이 없다.**

룰 4종은 포스트모템 §2 에 정의돼 있고(입력·판정식·임계값·severity·오탐억제 포함), 도구도 이미 있다
(`J-ESR/check_source_urls.py`, `J-ESR/edinet_esr_probe.py`). **없는 것은 배선뿐이다** — 지금은 사람이
기억해서 돌려야 돈다. 10/31 재census 는 62사가 한꺼번에 posted 로 뒤집히는 라운드다.

## 요청

1. **오프라인으로 되는 것부터**: `JP_SOURCE_EXPIRING_HOST`(netloc 검사)를 `build_jesr_page_json.py`
   self-check 에 넣고 exit 1 에 반영. 네트워크 불필요.
2. **증거 신선도 검사**: `J-ESR/source_url_health.json` 의 `checked_at` 이 census 의 최신 `checked_at`
   보다 오래됐으면 self-check RED. 이러면 네트워크 없이도 "점검을 안 돌리고 census 를 고쳤다" 를 잡는다.
   (UH-14 가 지적한 "정본 증거가 push 묶음 밖" 문제를 우회하는 형태 — 증거 파일의 나이를 검사한다.)
3. **`JP_ESR_NOT_IN_SOURCE`** 는 PDF 다운로드가 필요하니 census 라운드의 선행 단계로 규정(§4c)하고,
   산출을 `source_url_health.json` 과 같은 방식으로 남겨 2번 검사에 태운다.
4. 예외 등재처가 없다 — 배선하면서 `J-ESR/jp_source_exceptions.json`(회사·필드·사유·owner 승인일)을
   같이 만든다. **exemption 추가는 owner 권한**.

## 참고 — 함께 열어야 할 미결 (같은 라운드)

- **화면이 서로 다른 기준을 한 줄에 세우고 있다.** 2026-09-13 실측: 규제 표준모델 4사 ·
  내부모델 7사 · 내부관리 3사 · 미확인 2사(census `esr_basis` 열에 기록됨). 랭킹 비교가능성 문제이고
  표기 방식(칩·각주·분리)은 **owner 판단**이다. 데이터에는 이미 남아 있으니 화면 반영만 남았다.
- 미확인 2사(ライフネット·SOMPO)의 산정기준을 10월 라운드에서 확정.

## 답변 (recipient 작성 — 처리 후)

**요청 1·2·4 배선 완료, 3 은 규격만 확정(요청대로 미배선). 신규 사각 UH-19 를 실측으로 발견해 보고한다.**

### 배선 위치 (한 곳)

`J-ESR/build_jesr_page_json.py::source_gate_check()` → `self_check()` 가 반환값을 자기 errors 에
`extend` → `main()` 의 `return 1`. **"배선했다" 가 아니라 실제로 exit code 를 바꾼다** — 그 `extend`
한 줄을 지우는 변이시험에서 exit-code 케이스 3개가 즉시 FAIL 했다.

| 룰 | 판정 | scope | exit 1 |
|---|---|---|---|
| `JP_SOURCE_EXPIRING_HOST` | netloc ∈ `jesr_http.EXPIRING_HOSTS` (**import**, 재타이핑 금지) | census `posted` × `source_url` | ✅ |
| `JP_SOURCE_URL_DEAD` | `source_url_health.json` 행의 `classification == "dead"` (증거 기록 판독형) | 같음 | ✅ |
| `JP_SOURCE_EVIDENCE_STALE` | 증거 부재 · `scope != "all"` · `checked_at` < census 최신 `checked_at` · posted 행 `checked_at` 결측 | 증거 1파일 + census 전량 | ✅ |
| `JP_SOURCE_EVIDENCE_INCOMPLETE` | posted `source_url` 이 증거 `rows[].url` 에 없음 | census `posted` × `source_url` | ✅ |

요청에 없던 `JP_SOURCE_URL_DEAD` 를 같이 걸었다 — 증거 파일을 읽는 형태면 **네트워크 없이** 돌고,
사고의 직접 원인(404 3건)을 덮는데 오탐이 0이라 뺄 이유가 없었다. 다만 그 이빨은 `EVIDENCE_STALE` 에
전적으로 의존한다(증거가 낡으면 dead 판정도 같이 낡는다) — 둘은 한 쌍이다.

### 오탐 억제 (실측 기반)

증거 파일에서 **RED 로 읽는 분류는 `dead`(404/410) 하나뿐**이다. 2026-09-13 전수 254건:
`blocked` 20 · `ok_requires_headers` 16 · `tls_client_issue` 4 · `spa_shell` 4 · `error` 4 —
"ok 가 아니면 RED" 로 짰으면 **48건이 한꺼번에 거짓 RED**. 화면 15사만 봐도 `ok` 12 ·
`ok_requires_headers` 2(MS&AD·ソニーFG) · `tls_client_issue` 1(ソニー生命) · `dead` 0 이다.
6개 분류 전부 "RED 아님" 회귀 케이스로 박았다. 닮은 호스트(`release.tdnet.info.example.com`)도
정확일치라 안 걸린다는 케이스 포함.

### 예외 등재처

`J-ESR/jp_source_exceptions.json` 신설, **0건**. 키는 `(rule, company_jp, field)` 셀 단위.
**등재는 owner 권한** — 파일 `_README` 와 `load_source_exceptions()` docstring 양쪽에 박았다.
fail-closed: 파일 부재 → 면제 0(더 엄해지는 방향이라 허용) / 손상 → RED / 필수 키(사유·승인일)
누락 → RED / 모르는 rule id → RED / **절차 룰 2종은 면제 불가**(가리키면 그 자체가 RED) /
`expires_on` 경과 → 면제 자동 해제.

### 3번 (`JP_ESR_NOT_IN_SOURCE`) — 규격만 확정, 배선 안 함

PM §4c-pre 에 산출 규격 확정: `J-ESR/esr_in_source_health.json`, `source_url_health.json` 과
**같은 봉투**(`checked_at`/`scope`/`rows`). 봉투가 같으면 위 신선도 검사를 그대로 재사용할 수 있어
배선 시 파일 하나만 더 물리면 된다. 배선 **선행조건**은 오탐 억제 3종의 실측 분포(이미지형 PDF 몇 사,
랜딩 페이지 정본 몇 사) — 세기 전에 임계값을 못 정한다. UH-5·UH-9 선례를 지켰다.

### 실증 (사본에서만 변이, 원본 md5 무변)

| | 결과 |
|---|---|
| (a) 정상 상태 | `exit 0`. 배선 전/후 빌더를 **같은 입력**으로 A/B 실행 → `jp/jesr_esr.json`·`jesr_master.json` **generated_at 제외 바이트 동일**. 추가된 것은 stdout 한 줄뿐 |
| (b) 만료호스트 주입 사본 | `exit 1` — `[JP_SOURCE_EXPIRING_HOST] au損害保険 ... release.tdnet.info ...` |
| (c) 증거 `checked_at` 을 2026-09-01 로 되돌린 사본 | `exit 1` — `[JP_SOURCE_EVIDENCE_STALE] 증거가 census 보다 낡았다 ... < census 최신 checked_at=2026-09-13` |
| (c-2) `scope` 를 `page` 로 좁힌 사본 | `exit 1` — `[JP_SOURCE_EVIDENCE_STALE] scope='page' ...` |
| (c-3) census 의 URL 만 바꾸고 점검 미실행(같은 날) | `exit 1` — `[JP_SOURCE_EVIDENCE_INCOMPLETE] ... 한 번도 점검된 적이 없다` |

셀프테스트 `tests/test_jp_source_gate.py` **43 케이스 전부 PASS**(위반→RED / 정상→통과 양방향,
실데이터 1건, 빌더를 서브프로세스로 돌려 exit code 를 직접 재는 4건 포함).
이빨 검증 5종 전부 발화: 배선 제거→3 FAIL · `EXPIRING_HOSTS` 비우기→11 FAIL ·
`DEAD_CLASSIFICATIONS` 비우기→1 FAIL · 절차 룰을 면제 가능으로→1 FAIL · 예외 필수키 검사 제거→3 FAIL.

### ⚠️ 같이 열어야 할 것 — UH-19 (jp 소관, 이 세션이 고치지 않았다)

**게이트는 빌더를 돌릴 때만 돈다.** 커밋 `62eed63`(14:43Z)이 census·`esr_target_ranges.json` 만 고치고
`jp/jesr_esr.json` 을 재생성하지 않아 **HEAD 의 배포 JSON 이 HEAD 의 census 와 어긋나 있다**:
2사 `basis` 가 아직 `"unconfirmed"`(정정값 `regulatory_standard`·`internal_model`),
SOMPO `target_range.high_pct` 가 아직 `270`(정정값 `null` — 270 은 현재 ESR 값이지 상한이 아니었다).
불변식 1번이 jp 레인에서 아직 안 닫혔다. ① 배포 JSON 재생성 ② jp 범위 게이트에 "배포 JSON =
census 재빌드 결과(generated_at 제외)" 대조 추가. ②는 지금 넣으면 즉시 RED 라 ①이 선행이다.

부수: `self_check` 의 `records count != 15` 는 하드코딩이라 **10/31 재census 에서 그대로 깨진다**(jp 소관).

## 오케스트레이터 검증 (2026-09-13)

답변대로 배선됐는지 기계로 확인했다: `tests/test_jp_source_gate.py` 43 passed · `tests/test_jp_deploy_matches_census.py` 2 passed(배포본 수치 변이 시 FAIL 확인, 원본 md5 복원) · `build_jesr_page_json.py` 실행 시 `[source-gate] ... RED 0건` 출력 · `test_deploy_assets` 11 passed · inbox 위생 위반 0.
**추가로 훅에 걸었다**(답변 범위 밖이었다): `scripts/prepush_check.py` offline 묶음 + CLAUDE.md §5 jp 축소범위에 두 테스트를 넣었다 — 안 넣으면 '배선했는데 push 를 안 막는' 상태라 이 저장소가 2026-08-21 에 겪은 실패의 반복이다. UH-19 도 같은 라운드에 닫았다(README 참조).
