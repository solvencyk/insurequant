#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Append the parser-ifrs17 answer to the two backfill tickets and flip status -> answered.
Content is built in full, then each file is written once (never open('w') first)."""
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
INBOX = ROOT / "inbox" / "parser"
AMEND = INBOX / "20260918T0700Z__validation__ALL_2023.1Q-2026.2Q__disclosure_pl_backfill_scope_amend.md"
ORDER = INBOX / "20260918T0205Z__orchestrator__ALL_2023.1Q-2026.2Q__disclosure_pl_backfill.md"

DASH_TABLE = """
| 회사 | 분기 | 항목 | 세전(억) | 순이익(억) | A 자기폐쇄 | B DART 연간 #23(백만원) | C 결손 | 판정 |
|---|---|---|---|---|---|---|---|---|
| KR0051 신한이지 | 2023.1Q | #23 법인세 | △9 | △9 | PASS | 2023.4Q=259.5 · 2024.4Q=0 | 예 | **0 승격** |
| KR0051 신한이지 | 2023.2Q | #23 법인세 | △13 | △13 | PASS | 2023.4Q=259.5 · 2024.4Q=0 | 예 | **0 승격** |
| KR0051 신한이지 | 2023.3Q | #23 법인세 | △52 | △52 | PASS | 2023.4Q=259.5 · 2024.4Q=0 | 예 | **0 승격** |
| KR0051 신한이지 | 2024.1Q | #23 법인세 | △9 | △9 | PASS | 2024.4Q=0 · 2025.4Q=0 | 예 | **0 승격** |
| KR0051 신한이지 | 2024.2Q | #23 법인세 | △60 | △60 | PASS | 2024.4Q=0 · 2025.4Q=0 | 예 | **0 승격** |
| KR0051 신한이지 | 2024.3Q | #23 법인세 | △140 | △140 | PASS | 2024.4Q=0 · 2025.4Q=0 | 예 | **0 승격** |
| KR0051 신한이지 | 2025.1Q | #23 법인세 | △46 | △46 | PASS | 2024.4Q=0 · 2025.4Q=0 | 예 | **0 승격** |
| KR0051 신한이지 | 2025.2Q | #23 법인세 | △157 | △157 | PASS | 2024.4Q=0 · 2025.4Q=0 | 예 | **0 승격** |
| KR0051 신한이지 | 2025.3Q | #23 법인세 | △272 | △272 | PASS | 2024.4Q=0 · 2025.4Q=0 | 예 | **0 승격** |
| KR0051 신한이지 | 2026.1Q | #23 법인세 | △97 | △97 | PASS | 2025.4Q=0 | 예 | **0 승격** |
| KR0051 신한이지 | 2026.2Q | #23 법인세 | △182 | △182 | PASS | 2025.4Q=0 | 예 | **0 승격** |
| KR1010 교보라플 | 2024.1Q | #23 법인세 | △34 | △34 | PASS | 2024.4Q=453.2 · 2025.4Q=0 | 예 | **0 승격** |
| KR1010 교보라플 | 2024.2Q | #23 법인세 | △76 | △76 | PASS | 2024.4Q=453.2 · 2025.4Q=0 | 예 | **0 승격** |
| KR1010 교보라플 | 2024.3Q | #23 법인세 | △119 | △119 | PASS | 2024.4Q=453.2 · 2025.4Q=0 | 예 | **0 승격** |
| KR1010 교보라플 | 2025.1Q | #23 법인세 | △78 | △78 | PASS | 2024.4Q=453.2 · 2025.4Q=0 | 예 | **0 승격** |
| KR1010 교보라플 | 2025.2Q | #23 법인세 | △79 | △79 | PASS | 2024.4Q=453.2 · 2025.4Q=0 | 예 | **0 승격** |
| KR1010 교보라플 | 2025.3Q | #23 법인세 | △86 | △86 | PASS | 2024.4Q=453.2 · 2025.4Q=0 | 예 | **0 승격** |
| KR1010 교보라플 | 2026.1Q | #23 법인세 | △49 | △49 | PASS | 2025.4Q=0 | 예 | **0 승격** |
| KR1010 교보라플 | 2026.2Q | #23 법인세 | △65 | △65 | PASS | 2025.4Q=0 | 예 | **0 승격** |
| KR1098 카카오페이 | 2023.2Q | #23 법인세 | △181 | △181 | PASS | 2023.4Q=0 · 2024.4Q=0 | 예 | **0 승격** |
| KR1098 카카오페이 | 2024.2Q | #23 법인세 | △218 | △218 | PASS | 2023~2025.4Q 전부 0 | 예 | **0 승격** |
| KR1098 카카오페이 | 2024.3Q | #23 법인세 | △349 | △349 | PASS | 2023~2025.4Q 전부 0 | 예 | **0 승격** |
| KR1098 카카오페이 | 2025.1Q | #23 법인세 | △137.15 | △137.15 | PASS | 2024.4Q=0 · 2025.4Q=0 | 예 | **0 승격** |
| KR1098 카카오페이 | 2025.2Q | #23 법인세 | △248 | △248 | PASS | 2024.4Q=0 · 2025.4Q=0 | 예 | **0 승격** |
| KR1098 카카오페이 | 2025.3Q | #23 법인세 | △352 | △352 | PASS | 2024.4Q=0 · 2025.4Q=0 | 예 | **0 승격** |
| KR1098 카카오페이 | 2026.1Q | #23 법인세 | △103 | △103 | PASS | 2025.4Q=0 | 예 | **0 승격** |
| KR1098 카카오페이 | 2026.2Q | #23 법인세 | △175 | △175 | PASS | 2025.4Q=0 | 예 | **0 승격** |
| (범위밖) KR0004 예별 | 2024.1Q | #23 법인세 | △37 | △37 | PASS | 2024.4Q=61,526.9 | 예 | 병합 안 함(§B 회사 보류) |
| (범위밖) KR0004 예별 | 2024.2Q | #23 법인세 | 88 | 88 | PASS | 2024.4Q=61,526.9 | 아니오 | 병합 안 함(§B 회사 보류) |
"""

ANSWER = """
처리자: parser-ifrs17 (2026-09-20). 범위 = 정정 티켓 §E(사이드카 재발행) + §D 의 PRINTED_DASH 판정.
**마스터 `PL_breakdown.json` 은 건드리지 않았다.** `kics_disclosure.json`·마스터 xlsx·`tests/fixtures/`·
다른 레인 파일도 열지 않았다.

### 1. `PL_breakdown_provenance.json` 재발행 — 완료 (병합 순서 ①)

| 축 | 재발행 전 | 재발행 후 |
|---|---|---|
| 셀 수 | 638 | **748** (마스터 실재 셀 전수와 1:1, 과부족 0) |
| 회사 · 최신분기 | 33사 · 2026.1Q | **39사 · 2026.2Q** |
| `source_file` 채움 | **0 / 638** | **730 / 748** (null 18, 전건 사유 기재) |
| `source_file` 디스크 존재 | — | **730 / 730** (부재 0) |
| `fields_pending_downloader` | as_of_date · source_file · effective_filtered | **as_of_date · effective_filtered** (source_file 제거) |
| `generated_at` | 20260620T0000Z | **20260920T0000Z** |

재생성·검증 명령(둘 다 오프라인, 결정론적):
```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/emit_pl_provenance.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/_20260920_pl_prov_audit.py   # FAILURES: 0 / exit 0
```

**역추적 방법 — 추측이 아니라 값 대조로 확정했다.** 빌더 코드를 읽어 published 값이 나올 수 있는
경로가 네 개뿐임을 먼저 확정하고(`build_pl_breakdown.assemble` → `_GOLD_CELL_OVERRIDE` →
`build_root_masters.build_pl` → `_apply_pl_overrides`), 각각을 이렇게 특정했다:

1. **FS-API Tier-1** — `fetch_dart_fs.tier1_for` 의 경로 결정(CORPCODE.xml → corp_code, `REPRT`,
   fs_div OFS→CFS)을 오프라인으로 복제해 `data/dart/_fs_api_cache/{cc}_{year}_{reprt}_{fs_div}.json`
   을 특정하고, **production `_parse()` 로 다시 파싱해 마스터 값과 대조**했다. 값이 안 맞으면 그 파일을
   원천으로 주장하지 않는다. 282셀 확정(항목 7개 중 7개 일치 257셀 · 5개 이상 일치 282/282).
2. **raw 필링 Tier-1(HTML fallback)** — FS-API 캐시가 없는 92셀(2023.1Q 23 · 2023.2Q 23 = FY2023
   최초도입 공백, 4Q 54 = 비상장·XBRL 미제출사)에 대해 **production `extract_tier1()` 을 실제로
   돌려** 값 대조했다. 44셀 확정, 48셀은 raw XML 에 손익계산서가 아예 없어 다른 원천으로 넘어갔다.
3. **raw 필링 Tier-2** — 항목 4·5·6·9·10·11·13·14 는 빌더에 raw XML 말고 다른 코드 경로가 없다.
   구조적 확정(위 1·2 에서 남은 것을 raw 로 밀어넣는 게 아니라, 코드 경로가 하나임을 근거로 한다).
4. **owner gold** — `data/_gold/user_pl_cells.json`(UPSERT, 최종 승자) 19셀 ·
   `scripts/build_pl_breakdown.py::_GOLD_CELL_OVERRIDE` 27셀. **이건 필링 경로를 달면 안 된다** —
   빌더가 raw 를 읽어서 만든 값이 아니라 파일 안의 리터럴이다.

복수 rcept 디렉터리 10셀(AIG·하나손보·라이나·AIA·메트라이프·하나생명·교보라플)은 값 일치 개수로
어느 필링인지 갈랐다. 예: `KR0029 2024.4Q` 는 `..._20250409001949`(7/7 일치)를 쓰고
`..._20250409001951`(0/7)은 쓰지 않는다.

**`source_file` 접두 분포(748)**: `data/dart/FY*/raw/` 402 · `data/dart/_fs_api_cache/` 282 ·
`scripts/build_pl_breakdown.py` 27 · `data/_gold/user_pl_cells.json` 19 · null 18.

셀 스키마에 **`source_files`** 를 같이 넣었다. 키가 (회사, 분기, item_block)이라 한 블록이 Tier-1
(FS-API)과 Tier-2(raw)를 섞는 게 정상이므로, 기여 파일마다 **그 파일이 설명하는 항목번호 목록**을
적었다. `source_file` 단일 값은 그중 **설명 항목이 가장 많은 파일**이다(동수면 `data/dart/` 우선).
감사 결과 **published 값 10,234개가 전부 정확히 한 버킷에 귀속**된다(누락·중복 0).

### 2. 🔴 빌더 파생 셀 — 412개 값 / 206셀. 필링 경로를 달지 않았다

이번 작업에서 나온 핵심 발견이다. `assemble()` 에 **`if is_life: v[13] = 0.0; v[14] = 0.0`** 이
무조건 실행된다. 생보사의 자동차손익(#13)·일반손익(#14) 0 은 **어느 필링에서도 읽은 값이 아니고**
빌더가 만들어 넣은 값이다. 여기에 `source_id: "DART"` + 필링 경로를 달면 거짓 계보다.

- **412개 값 / 206셀**에서 이 값들을 **모든 필링 버킷에서 제외**하고 셀에 `builder_derived_items`
  로 명시했다. 이 셀들의 `source_file` 은 나머지 실제 항목의 원천을 가리킨다.
- **published 값 전부가 이 파생값인 셀은 1칸**: `KR0080 AIA생명 2023.4Q contract_notes`
  (published=2, 둘 다 #13·#14 = 0.0). 이 셀은 **새 라벨 `source_id: "DERIVED"` + `source_file: null`
  + `unresolved_reason: "LIFE_LOB_ZERO_BUILDER_RULE_NOT_FROM_A_FILING"`** 로 남겼다.
- **새로 만든 라벨 2개**(둘 다 `_SOURCE_LINEAGE` 미등록 — 이 마스터에 `source_id_for_lineage()` 를
  배선하기 전에 validation 이 등재해야 한다. 사이드카 헤더 `source_id_values` 에 그렇게 적어 뒀다):
  - `DERIVED` — 블록의 published 값이 전부 빌더 산물. `source_file` 은 null.
  - `OWNER_GOLD` — owner 확정 리터럴(46셀). `source_file` 은 리터럴이 실제로 있는 파일
    (`data/_gold/user_pl_cells.json` 또는 `scripts/build_pl_breakdown.py`).
- **선 긋기(넘겨짚지 않은 부분)**: #6 예실차·#11 재보 예실차의 `0.0`(각 2셀·17셀)은 파생으로 **안**
  돌렸다. 2026-08-30 2-pass `zero_fill_ok` 때문에 그중 일부는 진짜 추출값이고, 둘을 가르려면 Tier-2
  를 다시 돌려야 한다. 지금은 필링 귀속으로 두고 이 잔여 모호성을 여기 적어 둔다 — 숨기지 않는다.

### 3. `source_file: null` 잔여 18칸 — 전건 사유

| 사유 | 칸 | 내용 |
|---|---|---|
| `NO_PUBLISHED_VALUE_IN_BLOCK` | **17** | 그 블록의 모든 항목이 `값: null`. 귀속할 값 자체가 없어 파일을 주장하지 않았다. KR0003 2023.1Q cn · KR0004 2023.4Q is · KR0051 2023.4Q·2024.4Q cn · KR0069 2023.1Q·2023.2Q is · KR0071 2023.2Q is · KR0073 2023.1Q·2023.2Q is · KR0074 2023.4Q is · KR0095 2023.4Q is · KR0104 2023.1Q·2023.2Q is · KR0150 2026.2Q cn · KR1098 2023.4Q·2024.4Q·2025.4Q cn |
| `LIFE_LOB_ZERO_BUILDER_RULE_NOT_FROM_A_FILING` | **1** | KR0080 2023.4Q cn (위 §2) |

**published 값이 있는데 원천을 못 찾은 셀은 0칸이다.** 17칸은 "못 찾은" 게 아니라 "찾을 값이 없는"
경우라, validation 의 `published_cells` 정의가 값 기준이면 애초에 검사 대상이 아니다. 값 없는 블록에
파일을 다는 건 근거 없는 주장이라 판단해 비웠다 — **이 17칸을 검사 대상으로 잡을 거면 알려 달라.**

### 4. 남아 있는 `fields_pending_downloader` 2개 — 왜 남는가

- **`as_of_date`** — 채울 수 있는 값이 둘인데 둘 다 틀린다. 필링일(`rcept` 날짜, 예: 2023.1Q →
  2023-05-15)을 넣으면 `_sidecar_quarter()` 가 **2023.2Q** 로 읽어 `STALE_AS_OF` RED 이 748건 난다.
  기간말일(2023-03-31)을 넣으면 분기에서 기계적으로 유도한 값이라 항등식일 뿐 검증력이 0이다.
  **downloader 가 필링 메타에서 보고기간 종료일을 실제로 읽어 채우는 게 맞다**(`meta.json` 이 각
  rcept 디렉터리에 있다). 이 판단은 파서가 단독으로 내릴 게 아니라 넘긴다.
- **`effective_filtered`** — 자본증권 전용 필드(상환·콜 도래분 필터링 증거)다. PL_breakdown 에는
  개념 자체가 없다. `_CAPITAL_SECURITIES_MASTERS` 에 PL 이 없으므로 게이트도 요구하지 않는다.
  **PL 에 한해 N/A 로 빼는 게 맞다고 본다** — validation 판정 바란다.

### 5. PRINTED_DASH 판정 — 27칸 전건 표

실측 결과 5항목 안의 `PRINTED_DASH` 는 **29칸**이고, 그중 **KR0004 예별 2칸은 §B 로 회사 단위
보류**라 병합대상은 정확히 **27칸**이다(티켓 숫자와 일치). **29칸 전부 #23 법인세**다.

기본값 null 을 깔고, 세 축을 각각 실측해 **A + 독립축 1개 이상**을 만족할 때만 0으로 승격했다:

- **A 자기폐쇄** — 같은 표에 인쇄된 세전이익과 당기순이익이 **정확히 같다**(E6 diff = 0.0억, 허용
  2.5억). 발행사 표 자체가 법인세 0 을 진술한다. 그 표의 **유일한 대시**다. → **29/29 PASS**
- **B 독립원천** — 같은 회사의 **DART 연간 마스터 #23**(경영공시와 완전히 다른 원천). KR1098 은
  2023~2025.4Q 전부 0, KR0051 은 2024.4Q·2025.4Q 가 0, KR1010 은 2025.4Q 가 0.
- **C 결손** — 병합대상 27칸 **전부 당기순손실**. 대시가 연속으로 이어진다(KR0051 11분기 ·
  KR1010 8분기 · KR1098 8분기).

{DASH_TABLE}

**B 의 정직한 단서**: KR0051 2023.4Q = 259.5백만원, KR1010 2023.4Q = △220.0 · 2024.4Q = 453.2백만원
으로 **연간은 0 이 아니다**. 결손사가 1~3Q 에는 인식액이 없다가 연말 일괄(이연법인세 재측정·정산)로
소액을 잡는 정상 패턴으로 읽었고, 그래서 B 를 단독 근거로 쓰지 않고 **A 를 필수 축**으로 뒀다.
27칸 모두 A 가 PASS 라 판정은 흔들리지 않는다. 이 해석에 이견 있으면 되돌리기는 한 줄이다
(`dash_promotion.promoted` → false, `값`/`값_억원` → null).

**값은 이번 판정으로 하나도 바뀌지 않았다.** 추출기가 이미 E6 단독 근거로 27칸을 0 승격해 둔
상태였고, 나는 그걸 3축으로 재검증해 **근거 문구를 교체**하고 KR0004 2칸을 `promoted: false` ·
`merged: false` 로 못 박았다. 스테이징 구조 무결성은 전수 대조로 확인했다
(`scripts/_probes/_20260920_dash_verify.py`: 평탄화 필드 15,164개 중 **변경 29개가 전부
`dash_promotion`**, 추가·삭제 0, 병합후보 **775칸 / 합 17,871,426백만원 불변**).

### 6. 백필분(DISCLOSURE)은 사이드카에 넣지 않았다

지시대로 `PL_breakdown_provenance.json` 에 `DISCLOSURE` 계보 셀을 **1건도 넣지 않았다**
(`grep -c "DISCLOSURE\\|data/disclosure" PL_breakdown_provenance.json` → **0**). 사이드카는 오늘
마스터에 실재하는 748셀만 담는다. 스테이징의 `provenance_entries` 가 ⑤ 병합 때 append 될 것이다.
`DART` 라벨을 경영공시 파일에 단 곳도 없다.

### 7. 병합 준비 완료 여부

**①(사이드카 실물 발행)은 끝났다. ⑤ 병합은 아직 못 한다 — validation 의 ②③④ 가 남아서다.**
내 쪽에서 validation 에 넘기는 것 3건: (a) 새 `source_id` 2개(`OWNER_GOLD`·`DERIVED`)의
`_SOURCE_LINEAGE`/게이트 등재, (b) `published_cells` 정의가 값 없는 17칸을 포함하는지, (c)
`effective_filtered` 를 PL 에 한해 N/A 처리해도 되는지.

### 8. 만진 파일

- `PL_breakdown_provenance.json` (재발행)
- `data/_derived/pl_backfill_disclosure_20260918.json` (dash_promotion 29건 + `dash_adjudication` 블록)
- `scripts/emit_pl_provenance.py` (**신규** — 사이드카를 재현 가능하게 만드는 데 필요. 기존
  `scripts/emit_ifrs17_provenance.py` 는 CSM 사이드카도 같이 덮어쓰므로 **건드리지 않았다.**
  주의: 그 스크립트를 다시 돌리면 `source_file` 이 통째로 날아간다 — PL 은 새 스크립트로 발행한다.)
- `scripts/_probes/_20260920_pl_prov_*.py` · `_20260920_dash_*.py` (프로브 9개)
- 프로브 산출: `data/_derived/_probe_20260920_pl_prov_{census,resolve,verify_raw}.json` ·
  `_probe_20260920_dash_adjudication.json`

모델 Opus 5 · 이 티켓 처리 약 2시간(중간에 API 한도로 1회 중단 후 재개). push 하지 않았다.
"""


def patch(path, body):
    t = path.read_text(encoding="utf-8")
    assert t.rstrip().endswith("## 답변 (recipient 작성 — 처리 후)"), path.name
    t = re.sub(r"^status: open$", "status: answered", t, count=1, flags=re.M)
    out = t.rstrip("\n") + "\n" + body.rstrip("\n") + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(out)
    print(f"patched {path.name}  ({len(out)} chars)")


body_amend = ANSWER.replace("{DASH_TABLE}", DASH_TABLE.strip())
patch(AMEND, body_amend)

body_order = """
처리자: parser-ifrs17 (2026-09-20). **정정 티켓
`inbox/parser/20260918T0700Z__validation__ALL_2023.1Q-2026.2Q__disclosure_pl_backfill_scope_amend.md`
§답변에 전문을 적었다 — 그쪽이 상위 티켓이라 여기서는 이 발주서 대비 달라진 점만 남긴다.**

- **§6 의 8항목 → 5항목**(#1 보험손익 · #16 기타사업비용 · #22 세전 · #23 법인세 · #24 순이익).
  #17 투자손익 · #20 영업이익 · #21 영업외손익은 감독회계 재분류로 **다른 개념**이라 빠졌다
  (정정 §A). 스테이징에는 검산용으로 남아 있으나 `merge_candidate: false` 다.
- **16사 → 15사**. KR0004 예별손해는 범위 불일치 규명까지 제외(정정 §B). 스테이징에서
  `backfill_excluded` 로 표시돼 있고, 이번에 판정한 대시 2칸도 `merged: false` 로 못 박았다.
- **§6 의 "먼저 스테이징한다" 는 그대로 유효하다.** 마스터 `PL_breakdown.json` 에 **병합하지
  않았다.** 병합은 validation 의 ②③④ 뒤 별도 라운드다.
- **§6 의 provenance 요구(`source_id: "DISCLOSURE"`)는 병합 시점에 적용된다.** 지금 재발행한
  `PL_breakdown_provenance.json` 에는 DISCLOSURE 셀이 **0건**이다(아직 마스터에 없는 값이라).
  스테이징의 `provenance_entries` 가 병합 때 append 된다. **`DART` 라벨을 경영공시 파일에 단
  곳은 없다.**
- **§3 의 `TABLE_NOT_FOUND` 14칸 · AIG 레이아웃 변형**은 재파싱으로 해소됐다(스테이징 status:
  OK 159 · OK_VISION_MANUAL 7 · NO_PDF 6). 남은 6칸은 KR0150 서울보증 **원천 부재 확정**이다.
- **§7 Phase 2(서술문 CSM 상각·위험조정·예실차)는 착수하지 않았다.** Phase 1 병합이 끝나기 전에는
  섞지 말라는 지시대로 남겨 둔다.

이번 라운드에서 실제로 끝낸 것은 **병합 순서 ①(`PL_breakdown_provenance.json` 셀 단위 `source_file`
재발행: 638 → 748셀 · 채움 730 · null 18 전건 사유 기재 · 디스크 부재 0)**과 **PRINTED_DASH 27칸
판정**이다. 수치·근거·판정표는 정정 티켓 §답변을 보라.

모델 Opus 5 · 약 2시간. push 하지 않았다.
"""
patch(ORDER, body_order)
