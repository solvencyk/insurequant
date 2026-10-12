# -*- coding: utf-8 -*-
"""Annotate the KR1107 (Pacific Life Re) 2023.4Q CSM waterfall provenance cell: item 4 keeps the PRINTED value, which contains the business-transfer CSM.

Ticket : inbox/parser/20261012T1020Z__orchestrator__MULTI_2023.4Q-2026.2Q__ifrs17_owner_approved_followups.md item 2 (owner decision (20), 2026-10-12:
         keep the printed value including the 1,069억 transfer-in, and leave a remark in the provenance sidecar).
Master : CSM_waterfall.json is NOT touched.  Only CSM_waterfall_provenance.json cell (KR1107, 2023.4Q, csm_waterfall) gets a free-text `note`.

Guards (abort before writing): the sidecar must round-trip byte-exactly through json.dumps(indent=2)+CRLF, the cell must exist exactly once and carry no
`note` yet, and the master's item 4 / item 6 values must still be the printed 950.76538 / 989.05884.  After writing, every other cell must be identical.

  default    dry run
  --apply    write (backup: data/_derived/ifrs17_owner_followups_backup_20261012/CSM_waterfall_provenance.json.pre_note)
  --revert --apply   remove the note again (only if it is the note written here)

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/annotate_csm_prov_kr1107_20261012.py [--apply]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIDECAR = ROOT / "CSM_waterfall_provenance.json"
MASTER = ROOT / "CSM_waterfall.json"
BACKUP = ROOT / "data" / "_derived" / "ifrs17_owner_followups_backup_20261012"
KEY = ("KR1107", "2023.4Q", "csm_waterfall")
NOTE = ("영업양수 1,069억 포함, 인쇄값. 항목 4(가정 및 경험 조정) 950.77억은 잔차 항목이라 인쇄 CSM 변동표의 「2. 자산양수도」 CSM 1,069.43억"
        "(공정가치법 179.80 + 완전소급법 889.63)과 「보험계약마진을 변경하는 추정치 변동」 -118.67억(공정가치법 10.43 + 완전소급법 -129.10)을 함께 담는다"
        "(인쇄 기초 0, 2023 = 영업양수도 개시연도). 순수 가정 변동이 아니며 인쇄값 그대로 유지한다(owner 2026-10-12 결정 ⑳). "
        "원천: FY2024 감사보고서 전기 표 인쇄 쪽 -49-(PDF 51쪽).")
sys.stdout.reconfigure(encoding="utf-8")


def dump(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, indent=2).replace("\n", "\r\n").encode("utf-8")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    a = ap.parse_args()

    raw = SIDECAR.read_bytes()
    side = json.loads(raw.decode("utf-8"))
    if dump(side) != raw:
        raise SystemExit("ABORT: CSM_waterfall_provenance.json does not round-trip through json.dumps(indent=2)+CRLF")
    hits = [c for c in side["cells"] if (c["company_code"], c["quarter"], c["item_block"]) == KEY]
    if len(hits) != 1:
        raise SystemExit(f"ABORT: expected exactly one sidecar cell for {KEY}, found {len(hits)}")
    cell = hits[0]

    wf = json.loads(MASTER.read_bytes().decode("utf-8"))
    v = {r["항목번호"]: r["값"] for r in wf if r["원보험사코드"] == KEY[0] and r["공시분기"] == KEY[1]}
    if abs(v.get(4, 0) - 950.76538) > 1e-9 or abs(v.get(6, 0) - 989.05884) > 1e-9:
        raise SystemExit(f"ABORT: master item 4/6 are {v.get(4)}/{v.get(6)}, expected the printed 950.76538/989.05884")
    print(f"master KR1107 2023.4Q: item 4 = {v[4]}, item 6 = {v[6]} (unchanged by this script)")

    if a.revert:
        if cell.get("note") != NOTE:
            raise SystemExit("ABORT: the cell does not carry the note written by this script")
        print("revert: would remove the note")
    else:
        if "note" in cell:
            raise SystemExit(f"ABORT: the cell already has a note: {cell['note'][:60]}")
        print("add note:", NOTE)
    if not a.apply:
        print("(dry run -- nothing written; add --apply)")
        return 0

    BACKUP.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SIDECAR, BACKUP / ("CSM_waterfall_provenance.json.pre_revert" if a.revert else "CSM_waterfall_provenance.json.pre_note"))
    before = json.loads(json.dumps(side))
    if a.revert:
        cell.pop("note")
    else:
        cell["note"] = NOTE
    data = dump(side)
    if SIDECAR.read_bytes() != raw:
        raise SystemExit("ABORT: sidecar changed while planning -- nothing written")
    tmp = SIDECAR.with_suffix(".json.tmp_note")
    tmp.write_bytes(data)
    tmp.replace(SIDECAR)

    raw2 = SIDECAR.read_bytes()
    after = json.loads(raw2.decode("utf-8"))
    assert dump(after) == raw2, "written file does not round-trip"
    assert len(after["cells"]) == len(before["cells"])
    moved = 0
    for b, c in zip(before["cells"], after["cells"]):
        if (b["company_code"], b["quarter"], b["item_block"]) == KEY:
            assert {k: x for k, x in b.items() if k != "note"} == {k: x for k, x in c.items() if k != "note"}
            moved += 1
        else:
            assert b == c
    assert {k: x for k, x in before.items() if k != "cells"} == {k: x for k, x in after.items() if k != "cells"}
    assert moved == 1
    print(f"{'reverted' if a.revert else 'written'}: 1 cell; every other cell and all top-level fields identical; sha256 {sha(raw)[:12]} -> {sha(raw2)[:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
