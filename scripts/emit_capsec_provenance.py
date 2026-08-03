#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Emit the three ROOT capital-securities provenance sidecars from the artifacts' REAL lineage.

  kics_forward_capital_provenance.json
  kics_tier1_utilization_provenance.json
  kics_tier2_utilization_provenance.json

Why this script exists (owner inbox/validation/20260803T0056Z §2)
----------------------------------------------------------------
These three sidecars were **hand-written** (publishing `faa34cd`, generated_at 20260721T115831Z)
with `source_id: "FSC_BONDS"` on all three — because `validate_data_contract.py` hardcoded that
enum for capital-securities masters. But tier1/tier2 moved to DART on 2026-06-20
(`wire_capital_securities_to_utilization.py` reads `data/bonds/capital_securities_fy2025.json`,
a DART 사업보고서 extraction), so the label was a lie the gate then "verified" = false-green.

The gate now checks `source_id` against the actual lineage of `source_file`
(`SOURCE_ID_LINEAGE_MISMATCH`), so the sidecars must be **derived, not typed**. Without an
emitter the correction would be washed out by the next rebuild — hence this script.

`source_id` is never hardcoded here: it comes from `validate_data_contract.source_id_for_lineage`,
the same function the gate judges with. `source_file` is read out of each master's own
`definition.source` / manifest, so a source change upstream re-labels automatically.

Run:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/emit_capsec_provenance.py
      (--check = 발행하지 않고 현 사이드카가 최신 계보와 맞는지만 확인, drift면 exit 2)
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from validate_data_contract import source_id_for_lineage  # noqa: E402

STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

# master -> (published root artifact, root sidecar)
MASTERS = {
    "forward_capital": ("kics_forward_capital.json", "kics_forward_capital_provenance.json"),
    "tier1_utilization": ("kics_tier1_utilization.json", "kics_tier1_utilization_provenance.json"),
    "tier2_utilization": ("kics_tier2_utilization.json", "kics_tier2_utilization_provenance.json"),
}


def _quarter_to_as_of(q: str) -> str:
    """'2026.1Q' -> '2026-03-31' (the as-of the published figures represent)."""
    m = re.match(r"(\d{4})\.(\d)Q", q or "")
    if not m:
        raise SystemExit(f"ERROR: unparseable quarter {q!r}")
    y, qn = int(m.group(1)), int(m.group(2))
    return f"{y}-{qn * 3:02d}-{ {1: 31, 2: 30, 3: 30, 4: 31}[qn] }"


def _rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def _source_file_from_definition(doc: dict) -> str | None:
    """Pull the per-bond source path out of a tier master's own `definition.source` string,
    e.g. 'DART FY2025 annual per-bond (data/bonds/capital_securities_fy2025.json)'."""
    src = ((doc.get("definition") or {}).get("source") or "")
    m = re.search(r"\(([^()]*\.json)\)", src) or re.search(r"(data/[^\s()]+\.json)", src)
    return m.group(1) if m else None


def _forward_source_file() -> tuple[str | None, str | None]:
    """(source_file, baseline_quarter) for forward_capital, read from its own build manifest.

    2026-08-03 (inbox/parser/20260803T0055Z): bonds_source is now the repo-relative
    source path itself (e.g. 'data/bonds/capital_securities_fy2025.json'), not a bare
    FSC normalized-dir timestamp — forward_capital_simulation.py's load_outstanding_bonds()
    returns it directly, so no path reconstruction is needed here any more.
    """
    base = ROOT / "output" / "kics_forward_capital"
    if not base.exists():
        return None, None
    for d in sorted((x for x in base.iterdir() if x.is_dir()), reverse=True):
        man = d / "manifest.json"
        if not man.exists():
            continue
        m = json.loads(man.read_text(encoding="utf-8"))
        bq = m.get("baseline_quarter")
        sf = m.get("bonds_source")
        if sf and not (ROOT / sf).exists():
            sf = None
        return sf, bq
    return None, None


def build_cells() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for master, (artifact, _sidecar) in MASTERS.items():
        p = ROOT / artifact
        if not p.exists():
            print(f"  SKIP {master}: {artifact} 부재")
            continue
        doc = json.loads(p.read_text(encoding="utf-8"))
        if master == "forward_capital":
            source_file, quarter = _forward_source_file()
        else:
            source_file, quarter = _source_file_from_definition(doc), doc.get("quarter")
        if not quarter:
            print(f"  SKIP {master}: 발행 분기를 확정할 수 없음")
            continue
        if not source_file or not (ROOT / source_file).exists():
            print(f"  SKIP {master}: per-bond source_file 미확인 ({source_file!r}) — "
                  f"게이트가 MISSING_PROVENANCE로 잡는다")
            continue
        source_file = str(source_file).replace("\\", "/")   # 사이드카는 항상 posix 상대경로
        sid = source_id_for_lineage(source_file)
        if sid is None:
            print(f"  SKIP {master}: {source_file} 계보 미등록 — validate_data_contract."
                  f"_SOURCE_LINEAGE 에 먼저 등재할 것")
            continue
        out[master] = {
            "master": master,
            "generated_at": STAMP,
            "cells": [{
                "quarter": quarter,
                "item_block": master,
                "source_id": sid,               # ← 계보에서 도출, 하드코딩 금지
                "as_of_date": _quarter_to_as_of(quarter),
                "source_file": source_file,
                "effective_filtered": True,
                "_note": f"source_id derived from source_file lineage by "
                         f"emit_capsec_provenance.py ({STAMP}); as_of_date = 발행 분기말 "
                         f"(per-bond 스냅샷 자체의 as-of는 그보다 이를 수 있고, effective 필터는 "
                         f"게이트 CHECK2 2c가 계보별로 검사한다)",
            }],
        }
    return out


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    built = build_cells()
    drift = 0
    for master, doc in built.items():
        path = ROOT / MASTERS[master][1]
        old = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        same = bool(old) and [{k: v for k, v in c.items() if k not in ("_note",)}
                              for c in old.get("cells", [])] == \
            [{k: v for k, v in c.items() if k not in ("_note",)} for c in doc["cells"]]
        cell = doc["cells"][0]
        state = "unchanged" if same else "UPDATED"
        if not same:
            drift += 1
            oldsid = (old or {}).get("cells", [{}])[0].get("source_id") if old else None
            print(f"  {state:9} {MASTERS[master][1]}  source_id {oldsid} -> {cell['source_id']}"
                  f"  ({cell['source_file']})")
        else:
            print(f"  {state:9} {MASTERS[master][1]}  source_id={cell['source_id']}")
        if not check_only and not same:
            path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if check_only:
        print(f"\n--check: {drift} sidecar(s) out of sync with real lineage")
        return 2 if drift else 0
    print(f"\n[wrote] {drift} sidecar(s) rewritten from real lineage; {len(built) - drift} already correct")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
