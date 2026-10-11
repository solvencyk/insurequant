# -*- coding: utf-8 -*-
"""Move the oldest Status bullet (2026-10-11 마감 라운드) verbatim to the archive top; add the changelog entry."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
tp = ROOT / "TODO_publishing.md"
lines = tp.read_text(encoding="utf-8").split("\n")
i = next(k for k, l in enumerate(lines) if l.startswith("- **2026-10-11 마감 라운드"))
j = next(k for k in range(i + 1, len(lines)) if lines[k].startswith("## 열린 일"))
block = lines[i:j]          # bullet lines + trailing blank
del lines[i:j]
tp.write_text("\n".join(lines), encoding="utf-8")
ap = ROOT / "docs" / "todo_archive_publishing.md"
a = ap.read_text(encoding="utf-8").split("\n")
a[2:2] = block              # right below the title + blank line
ap.write_text("\n".join(a), encoding="utf-8")

cp = ROOT / "docs" / "changelog_publishing.md"
c = cp.read_text(encoding="utf-8")
marker = "---\n\n## 2026-10-12 — 재보사 손해율 패널"
assert marker in c
entry = """---

## 2026-10-12 — 미니 재동기화 2차 (재보사 PL·BS·CSM 재스윕 반영, 커밋만, push·배포 보류)

티켓 `inbox/publishing/20261012T0500Z__orchestrator__MULTI_2023.1Q-2026.2Q__mini_resync_2_reinsurer_resweep.md`. 마스터 JSON 은 읽기만 했다(3727438·57b7d78).
- xlsx 7시트를 시트별로 동기화(`sync_master_xlsx_sheet.py`, 기존 행 삭제 0): 손익분해PL 13,491→13,794(+303행, 값 변경 25칸 = 15행·KR1102/1103/1105 전부 값→값) · 17BS +49 · CSM워터폴 +18 · CSM상각 +15 · 가정민감도 +6 · 보험계약부채 +110 · 신계약CSM배수 +3. 마스터 diff 와 칸 단위로 일치, 다른 10시트 SHA 동일, 요약 시트는 행수 칸만 변경. 드리프트 RED 7→0.
- `NB_CSM_multiple.json` 390→393(재보사 KR1104 2025.4Q·KR1105 2025.4Q·KR1107 2023.4Q, 배수 null). 기존 390행 변경 0.
- 패널: ifrs17 viz 4패널·csm_waterfall 바이트 동일(재보사 상각·민감도는 최신 분기만 싣는데 신규 행이 모두 2023.4Q). csm_combo 52노드·compare 137리프 변경, 전부 재보사(다른 회사 0). compare 의 손해율 항목은 직전 라운드 재보사 행을 처음 반영한 것.
- `public_exports/` 7시트+manifest 재생성(build_id b4b6a71). 게이트: data-contract RED 102(전부 CONCEPT_MIXED_DISCLOSURE_INTO_DART, MASTER_XLSX_* 0), live_artifacts RED 0·YELLOW 25(baseline), 테스트 142 passed/1 skipped, viz 골든 2종 통과.
- 커밋 `b4b6a71`(xlsx·NB·패널·증거), `5079688`(public_exports). 상세 `data/_derived/mini_resync_20261012/runlog.md`.

"""
c = c.replace(marker, entry + marker[4:], 1)
cp.write_text(c, encoding="utf-8")
