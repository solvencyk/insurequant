# -*- coding: utf-8 -*-
"""Reconcile durable gold (data/_gold/user_kics_cells.json) to the owner xlsx
(insurequant_master_tables.xlsx 'K-ICS공시' sheet = owner SOT) for cells already
in the gold. Owner edits the xlsx and syncs to JSON; the gold (re-applied by the
rebuild chain) can lag and would then OVERWRITE an owner correction on rebuild
(found: KR0068 2025.2Q it37 주식위험액 gold 45096.51 vs owner xlsx 58590.96).

Only UPDATES values of cells ALREADY in the gold (never adds/removes cells).
Aligns 값 and 값_적용후 to the xlsx where they diverge numerically (>0.01).

Default = DRY RUN. Pass --apply to write (with .bak).
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import openpyxl

sys.stdout.reconfigure(encoding="utf-8")
REPO = Path(__file__).resolve().parents[1]
GOLD = REPO / "data" / "_gold" / "user_kics_cells.json"
XLSX = REPO / "insurequant_master_tables.xlsx"


def _num(v):
    if v is None:
        return None
    s = str(v).strip()
    if s in ("", "-", "─", "–", "?") or s.startswith("="):
        return None
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return None


def _canon(n):
    if n is None:
        return None
    return int(round(n)) if abs(n - round(n)) < 1e-6 else round(n, 6)


def main(apply: bool) -> int:
    gold = json.loads(GOLD.read_text(encoding="utf-8"))
    cells = gold["cells"]

    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    ws = wb["K-ICS공시"]
    xl = {}
    for r in ws.iter_rows(min_row=2, values_only=True):
        if r[0] is None:
            continue
        try:
            key = (r[0], r[6], str(int(r[4])))
        except (TypeError, ValueError):
            continue
        xl[key] = (_num(r[7]), _num(r[8]) if len(r) > 8 else None)
    wb.close()

    changes = []
    for code, qs in cells.items():
        for q, items in qs.items():
            for it, cell in items.items():
                xv = xl.get((code, q, it))
                if xv is None:
                    continue
                xval, xpost = xv
                # 값
                if "값" in cell and xval is not None:
                    gv = _num(cell["값"])
                    if gv is not None and abs(gv - xval) > 0.01:
                        changes.append((code, q, it, "값", cell["값"], _canon(xval)))
                        if apply:
                            cell["값"] = _canon(xval)
                # 값_적용후
                if "값_적용후" in cell and xpost is not None:
                    gp = _num(cell["값_적용후"])
                    if gp is not None and abs(gp - xpost) > 0.01:
                        changes.append((code, q, it, "값_적용후", cell["값_적용후"], _canon(xpost)))
                        if apply:
                            cell["값_적용후"] = _canon(xpost)

    print(f"=== reconcile gold -> xlsx ({'APPLY' if apply else 'DRY-RUN'}) ===")
    for code, q, it, fld, old, new in changes:
        print(f"  {code} {q} it{it} {fld}: {old} -> {new}")
    print(f"\n  {len(changes)} cell-field(s) realigned to owner xlsx")
    if apply and changes:
        bak = GOLD.with_suffix(".json.pre_reconcile.bak")
        bak.write_text(GOLD.read_text(encoding="utf-8"), encoding="utf-8")
        GOLD.write_text(json.dumps(gold, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  wrote {GOLD} (backup {bak.name})")
    elif not changes:
        print("  gold already matches xlsx — nothing to do")
    else:
        print("  (dry run — pass --apply to write)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main("--apply" in sys.argv))
