#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-12 reinsurer PL/BS blank re-sweep (inbox/parser/20261012T0110Z), BS part: ADD the blank IFRS17_BS cells that the reinsurer 경영공시 prints and whose label->item
mapping is proven (anchors = the same label already equals the master in other quarters of the same company).  Add-only, guard = the key must be absent everywhere.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/reinsurer_resweep_bs_apply.py [--apply]

Writes (only these): IFRS17_BS.json (rows) · data/_derived/bs_from_disclosure.json (lineage sidecar) · data/_derived/bs_from_disclosure_parts/<KR>_agent_resweep.json (durable part file that
scripts/merge_bs_disclosure_parts.py folds into the sidecar/overlay).  data/dart/viz/bs_manual_overrides.json (the overlay the builder re-applies) is NOT written here (outside this
ticket's write set) -- run scripts/merge_bs_disclosure_parts.py to regenerate it from the parts.
Spec = data/_derived/reinsurer_resweep_20261012/bs_spec_resweep.json (s60_bs_spec.py: every cell re-read from its PDF page).
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
from bspl_granularity_load_bs import LABELS, SECTION, dumps, load_json_exact, meta_from_kics, safe_write  # noqa: E402

MASTER = ROOT / "IFRS17_BS.json"
SIDECAR = ROOT / "data/_derived/bs_from_disclosure.json"
PARTS = ROOT / "data/_derived/bs_from_disclosure_parts"
SPEC = ROOT / "data/_derived/reinsurer_resweep_20261012/bs_spec_resweep.json"
BACKUP = ROOT / "data/_derived/reinsurer_resweep_backup_20261012"
UNITTXT = {"천원": "천원 -> 백만원", "원": "원 -> 백만원", "백만원": "백만원 -> 백만원", "억원": "억원 -> 백만원"}
HOWTXT = {"A": "engine candidate (bspl_granularity) whose rule 기타부채 is anchored by EXISTS_SAME quarters",
          "B": "KR1103 8-1 재무상태표(천원) line; same label equals the master in other quarters",
          "C": "summary BS (감독회계 총괄 요약 재무상태표)"}


def main():
    apply = "--apply" in sys.argv
    cells = json.loads(SPEC.read_text(encoding="utf-8"))["cells"]
    bad = [c["key"] for c in cells if not c.get("reread_ok")]
    if bad:
        raise SystemExit(f"ABORT: cells that were not re-read from the page: {bad[:5]}")
    rows, raw_m = load_json_exact(MASTER, 2, "\r\n")
    side, raw_s = load_json_exact(SIDECAR, 2, "\r\n")
    by = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in rows}
    meta = meta_from_kics()
    stamp = time.strftime("%Y-%m-%d")
    for c in cells:
        code, it, q = c["co"], int(c["item"]), c["q"]
        if (code, it, q) in by or c["key"] in side["cells"]:
            raise SystemExit(f"ABORT: {c['key']} already present (master/sidecar)")
        if code not in meta:
            raise SystemExit(f"ABORT: no META for {code}")
    prior_parts = {p.name for p in PARTS.glob("*.json")}
    for c in cells:
        pn = f"{c['co']}_agent_resweep.json"
        if pn in prior_parts:
            raise SystemExit(f"ABORT: part file {pn} already exists")
    print(f"spec cells {len(cells)}: " + ", ".join(f"{k} x{v}" for k, v in sorted(defaultdict(int, {f'{c['co']} item {c['item']}': 0 for c in cells}).items())))
    cnt = defaultdict(int)
    for c in cells:
        cnt[(c["co"], c["item"])] += 1
    for k, v in sorted(cnt.items()):
        print("  ", k, v)
    if not apply:
        print("dry-run")
        return

    BACKUP.mkdir(parents=True, exist_ok=True)
    for p in (MASTER, SIDECAR):
        if (BACKUP / p.name).exists():
            raise SystemExit(f"ABORT: backup {BACKUP / p.name} already exists")
        shutil.copy2(p, BACKUP / p.name)
    snap = {k: json.dumps(v, ensure_ascii=False, sort_keys=True) for k, v in by.items()}
    side_before = {k: json.dumps(v, ensure_ascii=False, sort_keys=True) for k, v in side["cells"].items()}
    added, parts = [], defaultdict(dict)
    for c in sorted(cells, key=lambda c: (c["co"], int(c["item"]), c["q"])):
        code, it, q = c["co"], int(c["item"]), c["q"]
        nm, tk, sb = meta[code]
        added.append({"원보험사코드": code, "원수사명": nm, "티커": tk, "생손보여부": sb, "항목번호": it, "항목명": LABELS[it], "섹션": SECTION[it],
                      "레벨": 1 if it in (1, 2, 3) else 2, "공시분기": q, "값": c["new"]})
        basis = (f"재보사 PL/BS 공란 재스윕(inbox/parser/20261012T0110Z): {HOWTXT[c['how'][0]]}. 항목 {it} {LABELS[it]} = {c['new']:,} 백만원 "
                 f"(원문 {c['unit']}, {Path(c['pdf']).name} p{c['page']} 에서 쪽을 다시 열어 인쇄값 재현). 근거: " + " / ".join(c["evidence"]))
        rec = {"값": c["new"], "pdf": c["pdf"], "page": c["page"], "sha256": c["sha256"], "축척": UNITTXT[c["unit"]], "앵커항목": None, "방법": "resweep_20261012:" + c["how"], "근거": basis}
        side["cells"][c["key"]] = rec
        parts[code][c["key"]] = rec
    out_rows = rows + added
    out_rows.sort(key=lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"]))
    if [r for r in out_rows if (r["원보험사코드"], r["항목번호"], r["공시분기"]) in by] != rows:
        raise SystemExit("ABORT: master was not sorted (code,item,quarter) -- the insertion would reorder existing rows")
    for code, cs in parts.items():
        obj = {"_readme": [f"[{stamp}] 재보사 PL/BS 공란 재스윕(inbox/parser/20261012T0110Z) 의 {code} 신규 칸 계보 -- scripts/reinsurer_resweep_bs_apply.py 가 쓴다. "
                           "scripts/merge_bs_disclosure_parts.py 가 이 파일을 다른 파트와 같이 사이드카·오버레이로 합친다."],
               "cells": cs, "skips": {}}
        safe_write(PARTS / f"{code}_agent_resweep.json", dumps(obj, 2, "\n"))
    for p, raw in ((MASTER, raw_m), (SIDECAR, raw_s)):
        if p.read_bytes() != raw:
            raise SystemExit(f"ABORT: {p.name} changed since read -- nothing further written")
    safe_write(SIDECAR, dumps(side, 2, "\r\n"))
    safe_write(MASTER, dumps(out_rows, 2, "\r\n"))

    chk = json.loads(MASTER.read_bytes().decode("utf-8"))
    ci = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in chk}
    changed = [k for k, s in snap.items() if json.dumps(ci.get(k), ensure_ascii=False, sort_keys=True) != s]
    sd2 = json.loads(SIDECAR.read_bytes().decode("utf-8"))["cells"]
    sd_bad = [k for k, s in side_before.items() if json.dumps(sd2.get(k), ensure_ascii=False, sort_keys=True) != s]
    if changed or sd_bad or len(chk) != len(rows) + len(added) or len(ci) != len(chk) or len(sd2) != len(side_before) + len(cells):
        raise SystemExit(f"VERIFY FAILED changed={changed[:3]} sidecar_changed={sd_bad[:3]} rows {len(chk)}")
    print(f"APPLIED: +{len(added)} rows (rows {len(rows)} -> {len(chk)}); all {len(snap)} pre-existing rows identical; sidecar +{len(cells)} cells (other {len(side_before)} identical); "
          f"part files {sorted(parts)}")


if __name__ == "__main__":
    main()
