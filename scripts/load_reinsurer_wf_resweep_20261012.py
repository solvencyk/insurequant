# -*- coding: utf-8 -*-
"""Cell-level additive load of reinsurer CSM_waterfall rows read by eye from rendered audit-report tables.

Ticket: inbox/parser/20261012T0120Z__orchestrator__KR1101-KR1108_2023.1Q-2026.2Q__reinsurer_csm_ilp_sensitivity_resweep.md
Spec:   data/_derived/reinsurer_csm_resweep_20261012/spec_wf_vision.json  (integers exactly as printed)

Guards: master must round-trip through json.dumps(indent=2)+CRLF; staged key already present with different value -> abort
(nothing overwritten); opening must equal the master's prior-year closing (item 6 of the previous 4Q, 5 decimals);
open+new+interest+item4+amort == close exactly (item4 = integer residual) and item4 must equal the printed explicit rows
within 2 units; backup + sha256 first; afterwards old rows proven identical (list prefix) and the provenance sidecar gets one
cell per (company, quarter).

  default   dry run
  --apply   write (CSM_waterfall.json + CSM_waterfall_provenance.json)
  --revert --apply   remove exactly the rows/cells this script staged (only if still equal)

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/load_reinsurer_wf_resweep_20261012.py [--apply]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "data" / "_derived" / "reinsurer_csm_resweep_20261012"
SPEC = EV / "spec_wf_vision.json"
BACKUP = EV / "backup"
sys.stdout.reconfigure(encoding="utf-8")

FACTOR = {"원": 1e-8, "천원": 1e-5, "백만원": 1e-2}
NAMES = {1: "기초 CSM", 2: "신계약 CSM", 3: "이자 부리", 4: "가정 및 경험 조정", 5: "CSM 상각", 6: "기말 CSM"}


def dump(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, indent=2).replace("\n", "\r\n").encode("utf-8")


def read_guarded(path: Path):
    raw = path.read_bytes()
    obj = json.loads(raw.decode("utf-8"))
    if dump(obj) != raw:
        raise SystemExit(f"{path.name}: bytes do not round-trip -- refusing")
    return raw, obj


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def write_atomic(path: Path, data: bytes):
    tmp = path.with_suffix(path.suffix + ".tmp_resweep")
    tmp.write_bytes(data)
    tmp.replace(path)


def build_rows(spec, master_rows):
    out, prov, report = [], [], []
    for t in spec["tables"]:
        f = FACTOR[t["unit"]]
        code, q = t["code"], t["quarter"]
        item4 = t["close"] - t["open"] - t["new"] - t["interest"] - t["amort"]
        explicit = sum(t["item4_explicit_rows"].values())
        if abs(item4 - explicit) > 2:
            raise SystemExit(f"{code} {q}: item4 residual {item4} vs printed rows {explicit} differ by more than 2 units")
        vals = {1: t["open"], 2: t["new"], 3: t["interest"], 4: item4, 5: t["amort"], 6: t["close"]}
        eok = {i: round(v * f, 5) for i, v in vals.items()}
        # identity on the written (rounded) numbers
        resid = eok[6] - (eok[1] + eok[2] + eok[3] + eok[4] + eok[5])
        if abs(resid) > 2e-5:
            raise SystemExit(f"{code} {q}: written identity residual {resid}")
        prev_q = f"{int(q[:4]) - 1}.4Q"
        prior = [r for r in master_rows if r["원보험사코드"] == code and r["공시분기"] == prev_q and r["항목번호"] == 6]
        if t.get("start_up_year"):
            if t["open"] != 0 or prior:
                raise SystemExit(f"{code} {q}: start_up_year requires printed opening 0 and no prior closing in the master")
            prior = [{"값": 0.0}]
        elif not prior:
            raise SystemExit(f"{code} {q}: no prior closing in master ({prev_q})")
        if abs(prior[0]["값"] - eok[1]) > 1.1e-5:
            raise SystemExit(f"{code} {q}: opening {eok[1]} != master {prev_q} closing {prior[0]['값']}")
        tmpl = [r for r in master_rows if r["원보험사코드"] == code and r["항목번호"] == 6][0]
        for i in range(1, 7):
            out.append({"원보험사코드": code, "원수사명": tmpl["원수사명"], "티커": tmpl["티커"], "생손보여부": tmpl["생손보여부"],
                        "항목번호": i, "항목명": NAMES[i], "공시분기": q, "값": eok[i], "값_당분기": eok[6] if i == 6 else None})
        prov.append({"company_code": code, "quarter": q, "item_block": "csm_waterfall", "source_id": "DISCLOSURE",
                     "source_file": t["pdf"], "as_of_date": f"{q[:4]}-12-31"})
        report.append({"code": code, "quarter": q, "eok": eok, "identity_residual": resid, "item4_units": item4, "item4_printed_rows_units": explicit,
                       "opening_equals_prior_closing": prior[0]["값"]})
    return out, prov, report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    a = ap.parse_args()
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    path, side = ROOT / "CSM_waterfall.json", ROOT / "CSM_waterfall_provenance.json"
    raw, rows = read_guarded(path)
    sraw, sobj = read_guarded(side)
    new, prov, report = build_rows(spec, rows)
    key = lambda r: (r["원보험사코드"], r["공시분기"], r["항목번호"])
    ex = {key(r): r for r in rows}
    to_add = [r for r in new if key(r) not in ex]
    same = [r for r in new if key(r) in ex and ex[key(r)] == r]
    coll = [key(r) for r in new if key(r) in ex and ex[key(r)] != r]
    print(json.dumps(report, ensure_ascii=False, indent=1))
    print(f"existing {len(rows)} | staged {len(new)} | to add {len(to_add)} | already equal {len(same)} | collisions {len(coll)}")
    if coll:
        raise SystemExit(f"collisions with different values: {coll}")
    have = {(c["company_code"], c["quarter"], c["item_block"]) for c in sobj["cells"]}
    add_prov = [c for c in prov if (c["company_code"], c["quarter"], c["item_block"]) not in have]
    if a.revert:
        keys = {key(r): r for r in new}
        keep = [r for r in rows if not (key(r) in keys and keys[key(r)] == r)]
        pk = {(c["company_code"], c["quarter"], c["item_block"]): c for c in prov}
        keepc = [c for c in sobj["cells"] if pk.get((c["company_code"], c["quarter"], c["item_block"])) != c]
        print(f"revert would remove {len(rows) - len(keep)} rows, {len(sobj['cells']) - len(keepc)} sidecar cells")
        if a.apply:
            write_atomic(path, dump(keep))
            sobj["cells"] = keepc
            write_atomic(side, dump(sobj))
        return 0
    if not a.apply:
        print("(dry run)")
        return 0
    BACKUP.mkdir(parents=True, exist_ok=True)
    tag = hashlib.sha256((str(len(rows)) + sha(raw)).encode()).hexdigest()[:8]
    shutil.copyfile(path, BACKUP / f"CSM_waterfall.json.pre_wf_{tag}")
    shutil.copyfile(side, BACKUP / f"CSM_waterfall_provenance.json.pre_wf_{tag}")
    if sha(path.read_bytes()) != sha(raw) or sha(side.read_bytes()) != sha(sraw):
        raise SystemExit("master changed during planning -- rerun")
    write_atomic(path, dump(rows + to_add))
    sobj2 = dict(sobj)
    sobj2["cells"] = sobj["cells"] + add_prov
    write_atomic(side, dump(sobj2))
    raw2, rows2 = read_guarded(path)
    sraw2, sobj3 = read_guarded(side)
    assert rows2[: len(rows)] == rows and rows2[len(rows):] == to_add
    assert sobj3["cells"][: len(sobj["cells"])] == sobj["cells"] and sobj3["cells"][len(sobj["cells"]):] == add_prov
    print(f"WRITTEN CSM_waterfall.json {len(rows)} -> {len(rows2)} (+{len(to_add)}); sidecar {len(sobj['cells'])} -> {len(sobj3['cells'])} (+{len(add_prov)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
