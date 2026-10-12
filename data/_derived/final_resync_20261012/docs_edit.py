# -*- coding: utf-8 -*-
"""Docs bookkeeping for the final resync: new TODO Status on top, oldest Status block moved verbatim to the archive,
changelog entry. Preserves each file's line terminators."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

NEW_STATUS = [
    "- **2026-10-12 최종 재동기화(push 직전 정합, 커밋만 · push 보류)** — xlsx 5시트(`17BS` 처브 6칸·`CSM상각` 18칸·`손익분해PL` +7행/1칸·`보험계약부채` 18칸·`K-ICS공시` +16행/4칸)·"
    "손해율 패널(재보사 세그먼트 표준화)·combo(처브)·compare(2칸) 재빌드·`public_exports`(`538cbe7`·`dee37c2`). 드리프트 0, data-contract RED 0, live_artifacts RED 0(baselined 25), 시험 142 passed.",
    "  남은 것: ① `downstream_kpis.json` 은 어느 HTML 도 안 읽고 이번 변경이 아닌 옛 `cf66dce`(상각 스케줄 정정) 미반영분(213칸) 때문에 어긋나 있어 재빌드본을 커밋하지 않음(`downstream_kpis.rebuilt_NOT_COMMITTED.json`) "
    "② `viz_build_nb_csm_ratio.py` 는 IR 원문 입력이라 이번 마스터와 무관해 생략 ③ 상세 `data/_derived/final_resync_20261012/runlog.md`.",
    "",
]

CHANGELOG = """## 2026-10-12 — 최종 재동기화 (push 직전 정합, 티켓 `20261012T1330Z`, 커밋만 · push 보류)

오늘 바뀐 마스터(재보사 손해율 세그먼트 `268002b`, 재보사 PL 7칸 복원·처브 BS 20/ILP 14-15·분할표 상각 `3bf1690`, K-ICS 퍼시픽 +16행·악사 4칸 `acd351a`)에 xlsx·공개본·패널을 맞췄다.

- **패널**: `viz_build_persistency_lossratio_panels.py` -> `panel_loss_ratio.json` 41노드(재보사 KR1101~1107 의 세그먼트가 `생명보험`/`장기손해보험` 으로 나뉘고 옛 `손해보험`·빈 구분 노드 삭제, `--check` OK), `viz_build_csm_combo_panel.py` 21노드(처브 KR0100 만, 포트폴리오 부채열), `viz_build_compare_panel.py` 2칸(악사 K-ICS 2024.3Q 286.4->286.5, KR1101 투자손익 null->0). ifrs17 viz 4패널·`csm_waterfall` 은 재빌드해도 바이트 동일. 증빙 `data/_derived/final_resync_20261012/panel_*.txt`.
- **xlsx**(`sync_master_xlsx_sheet.py` 시트별, 백업 `.bak_20261012_final_pre`): `17BS` 6칸(처브 보험계약부채 K-IFRS 기준 값->값), `CSM상각` 18칸(메트라이프·BNP·AIA·처브 2025.4Q 9·10년차 빈칸->값 8, 한화생명 분할표 정정 10), `손익분해PL` +7행·1칸(`값_당분기`), `보험계약부채` 18칸(처브 값->값), `K-ICS공시` +16행(퍼시픽 2025.3Q·2026.2Q 47~54)·4칸(악사 2024.3Q). 삭제 0, 나머지 12시트 값 SHA 동일(`xlsx_invariance.txt`), `요약` 은 행수 칸만 다름.
- **공개본** `export_public_sheets.py`: 5시트 + `manifest.json`(`build_id` `538cbe7`). 임시로 목록에서 내린 3시트 파일은 그대로 둠.
- **게이트**: `check_master_xlsx_drift` RED 7 -> 0, `validate_data_contract` RED 0(YELLOW 152), `validate_live_artifacts` RED 0(baselined 25), `validate_master_tables --no-build` 실행(exit 2 는 골든이 고정한 값), 골든 3종(master_tables·ifrs17 panels·csm_waterfall) passed, `test_deploy_assets`+`test_push_gate_wiring`+`test_prepush_scope` 142 passed.
- **미반영(의도)**: `downstream_kpis.json`(213칸 어긋남, 옛 `cf66dce` 미반영분이라 이번 범위 밖·HTML 무참조), `viz_build_nb_csm_ratio.py`(IR 원문 입력).

"""

RUNLOG = """# Final resync runlog (2026-10-12)

Ticket: `inbox/publishing/20261012T1330Z__orchestrator__MULTI_2023.1Q-2026.2Q__final_resync_before_push.md` (not edited). Branch fix/csm-product-segmented-columns. No push/subagents/docling/golden --update/exception registration. Masters were read-only.

## Result
- Commits: `538cbe7` (xlsx + 3 panels + evidence), `dee37c2` (public_exports, manifest build_id 538cbe7), docs commit separate.
- Preflight: parser-kics commit `acd351a` already landed (kics_disclosure.json clean) before the K-ICS sheet sync, which was done last.
- Drift before: RED 7 (17BS 6 cells, K-ICS ROW_MISSING 16 + DRIFT 4, CSM상각 18, PL ROW_MISSING 7 + DRIFT 1, 보험계약부채 18). After: RED 0, 120,692 rows, 0 cells.
- Gates: validate_data_contract RED=0 YELLOW=152; validate_live_artifacts RED=0, YELLOW baselined 25 (INSPL_CENSUS_MISSING 15), STALE_BASELINE 0; validate_master_tables --no-build exit 2 (pinned by test_master_tables_golden, which passes); golden master_tables + ifrs17 panels + csm_waterfall 3 passed; test_deploy_assets + test_push_gate_wiring + test_prepush_scope 142 passed, 1 skipped. Golden mismatches: none.

## Panels (before = git HEAD / saved copy; diffs in panel_*_diff.txt)
- `viz_build_persistency_lossratio_panels.py`: --check failed before (disk 206,065 vs rebuild 206,474 bytes); rebuilt, --check OK. 41 nodes, all companies KR1101-KR1107 (reinsurers): segment keys now life / long-term non-life, old `손해보험` and blank-segment nodes deleted, plus meta.source_sha12. panel_persistency unchanged.
- `viz_build_ifrs17_panels.py` (4 panels) and `viz_build_csm_waterfall.py`: byte-identical to HEAD.
- `viz_build_csm_combo_panel.py` (+--check OK): 21 nodes, Chubb KR0100 only (portfolio liability columns, 2023.1Q-2025.3Q); meta lic_recon: real 401 and sidecar 30 unchanged, estimated 83->85, none 52->50, est_unreliable updated; csm_recon unchanged.
- `viz_build_compare_panel.py` (+--check OK): 2 leaves: KR0049 K-ICS ratio 2024.3Q 286.4->286.5; KR1101 investment profit null->0 (restored printed-zero PL cell).
- `viz_build_ifrs17_kpis.py`: rebuilt 213 nodes across ~40 companies from the older amortization-schedule correction (cf66dce), not from this round; no HTML reads downstream_kpis.json. Reverted with git checkout; rebuilt copy kept as `downstream_kpis.rebuilt_NOT_COMMITTED.json`. Owner/designer may decide whether the file should be refreshed.
- `viz_build_nb_csm_ratio.py`: skipped. It reads IR text artifacts and also writes templates/ and embed.js; none of the masters changed today feed it.

## xlsx (backup insurequant_master_tables.xlsx.bak_20261012_final_pre, gitignored)
| sheet | rows | added | changed cells | removed |
|---|---|---|---|---|
| 17BS | 11,016 | 0 | 6 (KR0100 item 20, value->value) | 0 |
| CSM상각 | 635 | 0 | 18 (blank->value 8, value->value 10) | 0 |
| 손익분해PL | 13,794 -> 13,801 | 7 (KR1101 1, KR1103 2, KR1105 2, KR1107 2) | 1 (KR1105 2023.3Q item 21 값_당분기) | 0 |
| 보험계약부채 | 6,335 | 0 | 18 (KR0100 value->value) | 0 |
| K-ICS공시 | 29,992 -> 30,008 | 16 (KR1107 2025.3Q + 2026.2Q items 47-54) | 4 (KR0049 2024.3Q items 3, 4, 27) | 0 |
- Other 12 data sheets byte/sha identical; 요약 differs only in row-count cells (K-ICS공시, 손익분해PL, 합계). Note: the invariance script treats 보험계약부채 as removed 18/added 18 only because its key list spans the 값 column; the sync log shows 18 in-place cell edits and row count unchanged.

## public_exports
Changed: 17BS, CSM상각, K-ICS공시, 보험계약부채, 손익분해PL + manifest (build_id c3ebcc3 -> 538cbe7, K-ICS공시 rows 30008, 손익분해PL rows 13801). The 3 sheets taken off the download list were not touched.
"""


def read(p):
    return p.read_bytes().decode("utf-8")


def main():
    # TODO: move the oldest Status block to the archive, insert the new one on top
    tp = ROOT / "TODO_publishing.md"
    t = read(tp)
    nl = "\r\n" if "\r\n" in t else "\n"
    lines = t.split(nl)
    first = [i for i, l in enumerate(lines) if l.startswith("- **2026-10-12")]
    assert len(first) == 3, first
    old_start = first[2]
    # block = from old_start to the line before "## 열린 일"
    end = next(i for i, l in enumerate(lines) if l.startswith("## 열린 일"))
    block = lines[old_start:end]  # includes trailing blank line
    assert block[-1] == "", block
    new_lines = lines[:first[0]] + [s for s in NEW_STATUS] + lines[first[0]:old_start] + lines[end:]
    new_lines = [l for l in new_lines]
    tp.write_bytes(nl.join(new_lines).encode("utf-8"))
    # header date stays 2026-10-12
    ap = ROOT / "docs" / "todo_archive_publishing.md"
    a = read(ap)
    anl = "\r\n" if "\r\n" in a else "\n"
    alines = a.split(anl)
    assert alines[0].startswith("# TODO archive")
    alines = alines[:2] + block + alines[2:]
    ap.write_bytes(anl.join(alines).encode("utf-8"))
    # changelog: after the '---' that follows the header
    cp = ROOT / "docs" / "changelog_publishing.md"
    c = read(cp)
    cnl = "\r\n" if "\r\n" in c else "\n"
    marker = "---" + cnl + cnl + "## 2026-10-12"
    assert marker in c
    c = c.replace(marker, "---" + cnl + cnl + CHANGELOG.replace("\n", cnl) + "## 2026-10-12", 1)
    cp.write_bytes(c.encode("utf-8"))
    (ROOT / "data" / "_derived" / "final_resync_20261012" / "runlog.md").write_bytes(RUNLOG.encode("utf-8"))


main()
