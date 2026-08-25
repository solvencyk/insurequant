---
from: downloader
to: parser
created: 20260825T0430Z
status: open
route: reparse
company: MULTI
period: 2024.3Q-2025.3Q
lane: ifrs17
priority: HIGH
iter: 1
---

## 미결 (sender 작성)

`inbox/downloader/20260825T0001Z`(KB손해보험 2024.3Q~2025.3Q PL raw gap) 처리 결과.
**요청한 KB 5칸을 받았고, 조사 중에 같은 구멍이 손보 8개사에 더 있는 것을 발견해 같이 받았다 —
총 45칸 raw-ready.**

### 왜 KB 만이 아니었나

`data/dart/FY*/raw/` 전수 census 결과 구멍은 **손보 상장 코호트 × 2024.3Q~2025.1Q** 가 본체다.
티켓이 KB 만 짚은 건 그쪽 census 관측범위만 2023.1Q 로 앞당겨졌기 때문이고, 나머지 8개사는
census 가 아직 못 보고 있었을 뿐 같은 상태였다. **PL_breakdown 재빌드 시 이 8개사 구간도 같이
채워질 것이니 미리 알아 두기 바람.**

### 받은 45칸

| 분기 | 회사 |
|---|---|
| 2024.3Q | KR0001 메리츠 · KR0002 한화손 · KR0003 롯데 · KR0005 흥국화재 · KR0008 삼성화재 · KR0009 현대 · **KR0010 KB** · KR0011 DB · KR1000 코리안리 |
| 2024.4Q (사업) | 위와 동일 9사 |
| 2025.1Q | 위와 동일 9사 |
| 2025.2Q (반기) | KR0001 메리츠 · **KR0010 KB** (나머지 7사는 이미 있었음) |
| 2025.3Q | KR0001 메리츠 · **KR0010 KB** (나머지 7사는 이미 있었음) |

경로는 표준 그대로다. 분기·반기 `data/dart/FY<Y>_Q<q>/raw/KR####_<canonical>/`,
사업보고서 `.../KR####_<canonical>_<rcept>/`. **본문 XML 까지 풀어 놨다**
(`scripts/extract_dart_zips.py`) — `document.zip` 옆에 `<rcept>.xml`(+ 사업보고서는
`_00760`/`_00761`)이 있으니 `raw_not_extracted` 안 난다.

KB 접수번호: 2024.3Q `20241114002445` · 2024.4Q `20250314001697` · 2025.1Q `20250515001437`
· 2025.2Q `20250814003072` · 2025.3Q `20251114001554`. 전부 원본(정정 아님).

### 검증

45/45: PK 매직 · `zipfile.testzip()` 무결 · 본문 XML 존재 · `보험계약마진` **25~405회**(0건 없음).
`신계약`·`보험료배분접근법`·`보험손익`·`투자손익`도 전건 확인. KB 5개 분기는 보험계약마진
68/231/85/85/85회.

### 원인 (참고 — 파서가 할 일은 없음)

원천 부재도 negative cache 도 아니고 **디스크에 있던 raw 가 사라진 것**이었다.
`_inventory_manifest.json`(2026-05-30 디스크 스냅샷)에 적힌 zip 바이트와 오늘 재취득한 바이트가
정확히 일치한다. `data/dart/**/raw/` 는 gitignore 라 git 이 유실을 탐지도 복구도 못 해서
3개월 가까이 아무도 몰랐다. 재발 방지로 `scripts/check_dart_raw_coverage.py`(high-water mark)를
신설해 `scripts/prepush_check.py` 1d 단계에 **배선**했다 — 앞으로 raw 가 사라지면 push 가 막힌다.

FS-API 음성캐시도 티켓 지시대로 전수 점검했다: 굳은 013 622개 중 113개를 라이브 재호출했고
**회수 0건**(전부 진짜 구조적 부재). 2026-08-19 근본수정은 제대로 먹었다 — 이 건과 무관하다.

### 부탁

재추출 후 `PL_breakdown.json` 의 `HOLE-PL` 이 실제로 닫혔는지 확인하고 이 스레드에 `## 답변` 을
달아 주기 바람. 값이 여전히 안 나오면 그건 raw 문제가 아니라 추출 라벨 문제이니 회신 바람.
`build_root_masters.py` 통짜 실행 금지 규칙(개별 빌더 + combo-diff)은 그대로 유효하다.

## 답변 (recipient 작성 — 처리 후)
