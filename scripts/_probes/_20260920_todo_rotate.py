#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prepend the 2026-09-20 pass to TODO_parser_ifrs17.md Status and rotate the oldest pass
block (86th) into docs/todo_archive_parser_ifrs17.md verbatim, keeping Status at 5 entries
(CLAUDE.md §2.3).  Content is assembled first and each file written exactly once."""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
TODO = ROOT / "TODO_parser_ifrs17.md"
ARCH = ROOT / "docs" / "todo_archive_parser_ifrs17.md"

NEW_STATUS_LINE = """> **Status (top, 2026-09-20 91st pass 직후): 경영공시 PL 백필 병합 순서 ① 완료 —
> `PL_breakdown_provenance.json` 을 셀 단위 `source_file` 포함해 재발행(638→748셀, 채움
> 730, null 18 전건 사유, 디스크 부재 0) + PRINTED_DASH 27칸 3축 판정.** 마스터
> `PL_breakdown.json` 은 미변경(⑤ 병합은 validation ②③④ 뒤 별도 라운드). push 안 함.
"""

NEW_BLOCK = """> **2026-09-20 (91st pass) — PL provenance 사이드카 실물 발행(계보 축) + 백필
> PRINTED_DASH 판정. 빌더 파생값 412개를 거짓 계보에서 분리.**
>
> 발주: `inbox/parser/20260918T0700Z`(validation 범위정정 §E) + `20260918T0205Z`(원 발주).
> 둘 다 `status: answered`.
>
> ### ① `PL_breakdown_provenance.json` 재발행 (`scripts/emit_pl_provenance.py` 신설)
>
> 기존 사이드카는 638셀 전부 `source_file` 부재(파일이 스스로 `fields_pending_downloader`
> 라고 적고 있었다) · 33사 · 최신 2026.1Q 로, 게이트가 읽기만 하고 아무도 안 쓰는 죽은
> 아티팩트였다. 마스터 실재 셀 **748개 전수**로 재발행하고 셀 단위 `source_file` 을 채웠다
> (39사 · 2026.2Q · 채움 **730/748** · 디스크 부재 **0**).
>
> **역추적은 값 대조로 확정했다(추측 금지).** 빌더 코드상 published 값이 나올 수 있는 경로가
> 4개뿐임을 먼저 확정하고, ① FS-API 캐시는 `fetch_dart_fs.tier1_for` 의 경로결정을 오프라인
> 복제 후 production `_parse()` 로 재파싱해 값 대조(282셀) ② 캐시 없는 92셀은 production
> `extract_tier1()` 을 실제로 돌려 값 대조(44셀 확정, 48셀은 raw 에 손익계산서 자체가 없어
> 다른 원천으로 이동) ③ Tier-2(4/5/6/9/10/11/13/14)는 raw XML 외 코드 경로가 없어 구조적
> 확정 ④ owner gold 는 리터럴이 있는 파일(`data/_gold/user_pl_cells.json` 19셀 ·
> `scripts/build_pl_breakdown.py::_GOLD_CELL_OVERRIDE` 27셀)을 가리킨다 — **필링 경로를 달면
> 거짓 계보**라 달지 않았다. 복수 rcept 10셀은 값 일치 개수로 갈랐다(KR0029 2024.4Q 는
> `..._001949`(7/7) 채택, `..._001951`(0/7) 기각).
>
> ### ② 🔴 빌더 파생값 412개 / 206셀을 필링 귀속에서 분리
>
> `assemble()` 의 `if is_life: v[13] = 0.0; v[14] = 0.0` 은 무조건 실행된다 — 생보 자동차/
> 일반손익 0 은 **어느 필링에서도 읽은 값이 아니다.** 412개 값(206셀)을 모든 필링 버킷에서
> 빼고 `builder_derived_items` 로 명시했다. published 값이 전부 파생인 셀 **1칸**
> (`KR0080 2023.4Q contract_notes`)은 **새 라벨 `source_id: "DERIVED"` + `source_file: null`**.
> owner gold 46셀은 **새 라벨 `source_id: "OWNER_GOLD"`**. 둘 다 `_SOURCE_LINEAGE` 미등록이라
> 사이드카 헤더에 "배선 전 등재 필요" 로 박제하고 validation 에 넘겼다.
> **선 긋기**: #6/#11 의 `0.0`(2셀·17셀)은 2026-08-30 2-pass `zero_fill_ok` 때문에 진짜
> 추출값과 섞여 있어 파생으로 돌리지 않고 잔여 모호성으로 회신에 적었다.
>
> ### ③ PRINTED_DASH 27칸 판정 (스테이징 `data/_derived/pl_backfill_disclosure_20260918.json`)
>
> 5항목 안의 `PRINTED_DASH` 는 **29칸, 전건 #23 법인세**. KR0004 2칸은 §B 회사 보류라 병합
> 대상은 **27칸**. 기본값 null 에서 **A(자기폐쇄: 같은 표의 세전=순이익, E6 diff 0.0억, 그
> 표의 유일한 대시) + 독립축 1개 이상**을 만족할 때만 0 승격 → **27/27 승격**(A 29/29 PASS ·
> C 결손 27/27 · B DART 연간 #23 은 KR1098 전부 0, KR0051·KR1010 은 일부 연도만 0 —
> 연말 일괄인식 패턴이라 B 를 단독 근거로 쓰지 않았다).
> **값은 하나도 안 바뀌었다** — 추출기가 이미 E6 단독 근거로 승격해 둔 것을 3축 재검증하고
> 근거 문구를 교체했다. 전수 대조로 확인: 평탄화 필드 15,164개 중 변경 29개가 **전부
> `dash_promotion`**, 추가·삭제 0, 병합후보 **775칸 / 합 17,871,426백만원 불변**
> (`scripts/_probes/_20260920_dash_verify.py`, exit 0).
>
> ### 재현
>
> ```
> C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/emit_pl_provenance.py
> C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/_20260920_pl_prov_audit.py
> ```
> 후자 `FAILURES: 0` / exit 0 — 748셀 마스터와 1:1, published 값 **10,234개 전부 정확히 한
> 버킷에 귀속**(누락·중복 0), 파생값이 필링에 귀속된 건 0.
>
> **안 한 것**: 마스터 병합(⑤ — validation ②③④ 뒤 별도 라운드), DISCLOSURE 셀의 사이드카
> 선적재(`grep -c DISCLOSURE PL_breakdown_provenance.json` → 0), Phase 2 서술문 추출.
> validation 에 넘긴 판정 3건: 새 `source_id` 2개 등재 · `published_cells` 가 값 없는 17칸을
> 포함하는지 · `effective_filtered` 를 PL 에 한해 N/A 처리해도 되는지. push 안 함.

"""


def main():
    lines = TODO.read_text(encoding="utf-8").split("\n")
    # 1-based 388..522 = the 86th-pass Status block + its trailing blank line
    lo, hi = 388, 522
    assert lines[lo - 1].startswith("> **2026-09-11 (86th pass)"), lines[lo - 1][:60]
    assert lines[hi - 1] == "", repr(lines[hi - 1])
    assert lines[hi].startswith("> 📦 **Status 이력"), lines[hi][:40]
    cut = lines[lo - 1:hi - 1]

    # replace the running Status line-block (lines 3..7 region) and prepend the new pass
    head = TODO.read_text(encoding="utf-8")
    old_status_start = head.index("> **Status (top,")
    old_status_end = head.index("\n\n", old_status_start) + 1
    new_head = head[:old_status_start] + NEW_STATUS_LINE + head[old_status_end:]

    nl = new_head.split("\n")
    # re-locate the cut in the rewritten text (the Status replacement shifted line numbers)
    i = next(k for k, s in enumerate(nl) if s.startswith("> **2026-09-11 (86th pass)"))
    j = next(k for k, s in enumerate(nl) if s.startswith("> 📦 **Status 이력"))
    assert nl[j - 1] == "" and nl[i:j - 1] == cut, "cut boundary moved"
    kept = nl[:i] + nl[j - 1:]

    # insert the new pass block right after the Status paragraph (before the 90th pass block)
    k90 = next(k for k, s in enumerate(kept) if s.startswith("> **2026-09-12 (90th pass)"))
    out = "\n".join(kept[:k90] + NEW_BLOCK.rstrip("\n").split("\n") + [""] + kept[k90:])

    arch = ARCH.read_text(encoding="utf-8")
    marker = "\n---\n"
    p = arch.index(marker) + len(marker)
    new_arch = arch[:p] + "\n" + "\n".join(cut).rstrip("\n") + "\n" + arch[p:]

    with open(TODO, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(out)
    with open(ARCH, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(new_arch)
    print(f"TODO passes now = {out.count('(9') and sum(1 for s in out.split(chr(10)) if s.startswith('> **20') and 'pass)' in s)}")
    print(f"archived block lines = {len(cut)}  archive bytes {len(arch)} -> {len(new_arch)}")


main()
