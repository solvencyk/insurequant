# -*- coding: utf-8 -*-
"""prod: READ-ONLY access to the production Tier-2 machinery (import only; nothing is written).
tables_for(code, fy) -> list of ExtractedTable with ._basis tagged exactly as scripts/build_pl_breakdown.parse_filing does."""
from __future__ import annotations

import glob
import os
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _iter_tables_by_basis, _tag_basis  # noqa: E402
from scripts.pl_breakdown import companies as C  # noqa: E402
from scripts.pl_breakdown import tier2 as T2  # noqa: E402
from scripts.pl_breakdown.tier1 import extract_tier1  # noqa: E402


def xmls_in(d):
    xs = glob.glob(str(d) + "/*.xml") + glob.glob(str(d) + "/xml/*.xml") + glob.glob(str(d) + "/extracted*/*.xml")
    return sorted(set(xs), key=os.path.getsize, reverse=True)


def raw_dirs(code, fy):
    return sorted(glob.glob(str(ROOT / "data/dart" / fy / "raw" / f"{code}_*")))


def tables_for(code, fy, only_main=False):
    tables = []
    for d in raw_dirs(code, fy):
        for x in xmls_in(d):
            if only_main and (x.endswith("_00760.xml") or x.endswith("_00761.xml")):
                continue
            try:
                tables.extend(_tag_basis(list(_iter_tables_by_basis(Path(x), _iter_tables_with_context)), x))
            except Exception as e:  # noqa: BLE001
                print("table parse failed", x, e)
    return tables
