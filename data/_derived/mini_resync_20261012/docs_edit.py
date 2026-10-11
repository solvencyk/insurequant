# -*- coding: utf-8 -*-
"""Insert the 2026-10-12 mini-resync-2 entries into TODO_publishing.md Status (top, keep latest 3) and docs/changelog_publishing.md."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

todo_p = ROOT / "TODO_publishing.md"
t = todo_p.read_text(encoding="utf-8")
marker = "## Status (최신 3개)\n\n"
assert marker in t
new_status = (
    "- **2026-10-12 미니 재동기화 2차(재보사 재스윕 반영, 커밋만 · push 보류)** — xlsx 7시트(`손익분해PL` +303행·25칸, `17BS` +49, `CSM워터폴` +18, `CSM상각` +15, `가정민감도` +6, `보험계약부채` +110, `신계약CSM배수` +3)·NB 마스터 +3행(재보사, 배수 null)·combo/compare 재빌드(재보사만)·`public_exports`(`b4b6a71`·`5079688`). 드리프트 0, data-contract RED 102(전부 `CONCEPT_MIXED_DISCLOSURE_INTO_DART`), live_artifacts RED 0.\n"
    "  남은 것: ① `CONCEPT_MIXED_DISCLOSURE_INTO_DART` 102 는 validation ② ifrs17 viz 4패널·csm_waterfall 은 바이트 동일(신규 재보사 행이 전부 최신 분기 아님) ③ compare 패널 손해율 항목은 직전 라운드(`66e6156`) 재보사 행을 이번에 처음 반영. 상세 `data/_derived/mini_resync_20261012/runlog.md`.\n\n"
)
todo_p.write_text(t.replace(marker, marker + new_status, 1), encoding="utf-8")
# keep only the latest 3 Status bullets: drop the 4th (oldest) if present, archive it verbatim
lines = todo_p.read_text(encoding="utf-8").split("\n")
starts = [i for i, l in enumerate(lines) if l.startswith("- **20")]
print("status bullets:", len(starts))
