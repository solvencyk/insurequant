# -*- coding: utf-8 -*-
"""pass3 s05 (read-only): exact set of xlsx '손익분해PL' drift cells before (backup master) vs after (live master) and whether the added drift cells are exactly the changed cells of this batch."""
import json
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/scripts")
sys.stdout.reconfigure(encoding="utf-8")
import check_master_xlsx_drift as MX
import sync_master_xlsx_sheet as S
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
BK = ROOT / "data/_derived/remaining_20261022/e25_followups/pass3/backup_before_apply"
sheets, f0 = MX.read_workbook()
assert not f0, f0
header, cur = sheets["손익분해PL"]


def drift_cells(repo):
    S.REPO = repo
    MX.target_rows.__globals__["REPO"] = repo
    cols, tgt = S.target_rows("PL_breakdown.json")
    assert list(header) == list(cols)
    key_idx = [i for i, c in enumerate(cols) if c in MX.TEXT_COLS or c == "항목번호"]
    val_idx = [i for i in range(len(cols)) if i not in key_idx]
    cmap = {}
    for r in cur:
        cmap.setdefault(MX.key_of(r, cols, key_idx), r)
    out = set()
    for r in tgt:
        k = MX.key_of(r, cols, key_idx)
        c = cmap.get(k)
        if c is None:
            continue
        for i in val_idx:
            if MX.norm(c[i]) != MX.norm(r[i]):
                out.add((k, cols[i]))
    return out, cols


b, cols = drift_cells(BK)
a, _ = drift_cells(ROOT)
print("drift cells before", len(b), "after", len(a), "added", len(a - b), "resolved", len(b - a))
live_new = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.load(open(ROOT / "PL_breakdown.json", encoding="utf-8"))}
live_old = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.load(open(BK / "PL_breakdown.json", encoding="utf-8"))}
changed = set()
for k, r in live_new.items():
    o = live_old[k]
    for f in ("값", "값_당분기"):
        if r.get(f) != o.get(f):
            changed.add((k, f))
print("changed master fields", len(changed))
added = a - b
# map drift keys back to (code, item, quarter): key_of returns a tuple of the text/key columns; find the code/item/quarter positions
print("sample key", next(iter(added)))
kidx = {c: i for i, c in enumerate([c for c in cols if c in MX.TEXT_COLS or c == "항목번호"])}
print("key columns", list(kidx))
def to_ck(k):
    t = k[0]
    return (t[kidx["원보험사코드"]], int(t[kidx["항목번호"]]), t[kidx["공시분기"]]), k[1]
added_ck = {to_ck(x) for x in added}
resolved_ck = {to_ck(x) for x in (b - a)}
print("added drift == changed fields?", added_ck == changed, "| only in added:", sorted(added_ck - changed)[:8], "| only in changed:", sorted(changed - added_ck)[:8])
print("resolved cells:", sorted(resolved_ck)[:10])
# the changed fields that do NOT drift after: the sheet already carries the new value
print("changed fields whose sheet value already equals the new master:", sorted(changed - added_ck)[:12])
