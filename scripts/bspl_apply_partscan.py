#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 3 (parser/ifrs17): where does a BS cell key live? master / overlay / sidecar / every part file (read-only).

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_partscan.py KR0068|10|2023.2Q KR1000|10|2024.4Q ...
Prints, per key, the master value, the overlay (bs_manual_overrides.json) value, the sidecar value and each part file holding the key with its value and
merge class (engine < other_agent < note < vision: the later class wins in scripts/merge_bs_disclosure_parts.py).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
PARTS = ROOT / "data" / "_derived" / "bs_from_disclosure_parts"


def klass(stem: str) -> str:
    if "_agent_" not in stem:
        return "engine"
    if stem.endswith("_agent_note"):
        return "note"
    if stem.endswith("_agent_vision"):
        return "vision"
    return "other_agent"


def main():
    keys = sys.argv[1:]
    bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
    mv = {f"{r['원보험사코드']}|{r['항목번호']}|{r['공시분기']}": r["값"] for r in bs}
    ov = json.loads((ROOT / "data/dart/viz/bs_manual_overrides.json").read_text(encoding="utf-8"))["cells"]
    sd = json.loads((ROOT / "data/_derived/bs_from_disclosure.json").read_text(encoding="utf-8"))["cells"]
    parts = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in sorted(PARTS.glob("*.json"))}
    for k in keys:
        print(f"{k}: master={mv.get(k)}  overlay={(ov.get(k) or {}).get('값')}  sidecar={(sd.get(k) or {}).get('값')}")
        for name, d in parts.items():
            c = (d.get("cells") or {}).get(k)
            if c is not None:
                print(f"    part {name:<34} [{klass(Path(name).stem)}] 값={c.get('값')}")
            s = (d.get("skips") or {}).get(k)
            if s is not None:
                print(f"    part {name:<34} [{klass(Path(name).stem)}] SKIP={str(s)[:100]}")


if __name__ == "__main__":
    main()
