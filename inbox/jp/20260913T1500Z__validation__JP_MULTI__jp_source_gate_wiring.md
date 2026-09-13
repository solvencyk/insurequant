---
from: validation
to: jp
created: 20260913T1500Z
status: open
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

<처리 결과 1~3줄. 못 했으면 왜 못 했는지.>
