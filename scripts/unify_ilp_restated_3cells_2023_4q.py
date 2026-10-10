# -*- coding: utf-8 -*-
"""
Ticket 20261011T0100Z: unify items 10-15 of KR0074/KR0079/KR0099 2023.4Q on the FY2024 filing's prior-year-end
(2023-12-31, restated) column, like items 1-8 already are.  Reads the same DART notes with the stage-1 engine, with
cur/prior swapped.  Dry run by default; --write replaces the existing items 10-15 cell by cell (old-value guard, backup
first), extends the provenance (original_basis_value) and writes the sidecar data/_derived/ilp_restated_comparative.json.
Never touches IFRS17_BS.json.

C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/unify_ilp_restated_3cells_2023_4q.py [--write] [--report out.json]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import extract_insurance_liability_lic as lic  # noqa: E402
import load_ilp_latest3_2023_4q as L3  # noqa: E402
import load_ilp_backfill_pre2025 as L  # noqa: E402

CODES = ["KR0074", "KR0079", "KR0099"]
Q = "2023.4Q"
BASIS = "latest_filing_comparative_restatable"
SIDECAR = REPO / "data" / "_derived" / "ilp_restated_comparative.json"
# reason lines read from the FY2024 filings (audit-report emphasis paragraphs / restatement notes)
REASONS = {
    "KR0074": ("FY2024 사업보고서 감사보고서 강조사항: 「기업회계기준서 제1008호 … 에 따라 갱신형 보험의 보험부채 평가 시 현금흐름 추정 대상기간을 수정하여 "
               "비교표시된 과거 재무제표를 소급재작성 하였습니다」(주석 34); 이익잉여금처분계산서 「비교표시 재무제표 재작성의 효과 1,595,957,634,143원」"),
    "KR0079": ("FY2024 감사보고서(20250318001228_00760.xml) 강조사항: 「주석 44에 기술하고 있는 바와 같이 회사는 현금흐름추정 로직 오류를 수정하여 "
               "비교표시된 과거 재무제표를 소급재작성 하였습니다」; 요약재무정보 「회계정책 변경 및 오류수정으로 제37(전)기 재무상태표 재작성」"),
    "KR0099": ("FY2024 사업보고서 주석 45 「재무제표 소급재작성 효과」(20250314000905_00760.xml): 「당기 중 보험금융손익의 체계적 배분 등과 관련된 "
               "회계정책을 변경하였으며, 비교표시된 전기 재무제표를 소급재작성하였습니다」"),
}

_orig_annotate = lic.annotate_tables


def swapped_annotate(tabs, repair=frozenset()):
    """same annotation, current <-> prior swapped (the FY2024 filing's prior-year-end tables become 'cur')"""
    out = _orig_annotate(tabs, repair)
    for t in out:
        if t.get("rows_p"):
            rp = t["rows_p"]
            t["rows_p"] = {"cur": rp.get("prior", {}), "prior": rp.get("cur", {})}
            t["rows"] = rp.get("prior", {})
        else:
            hdr = t.get("hdr", "")
            if hdr.startswith("구분당기"):          # explicit column header beats the caption heuristics (KB Life tables)
                true = "cur"
            elif hdr.startswith("구분전기"):
                true = "prior"
                # role_of() discards every column whose header mentions 전기; the whole table is the prior year, so strip the word
                nl = t.get("nl", 1)
                t["roles"] = [lic.role_of(p.replace("전기", "")) if k >= nl else None for k, p in enumerate(t["paths"])]
                t["kind"] = "ME" if "CSM" in t["roles"] else "RF"
            else:
                true = t["period"]
            t["period"] = {"cur": "prior", "prior": "cur"}.get(true, true)
    return out


def build(code):
    fy = "FY2024_Q4"
    files = []
    for e in lic.inventory([fy], [code]):
        for f in e["files"]:
            files.append((f.split("/raw/", 1)[-1], lic.harvest_file(f)))
    liab, asset, bsfile = L3.fs_bs_row(fy, code, 3)
    anchor_mm = liab * 100.0
    lic.annotate_tables = swapped_annotate
    try:
        rec = lic.assemble_cell(code, fy, files, anchor_mm, anchor_mm)
    finally:
        lic.annotate_tables = _orig_annotate
    return rec, liab, asset, bsfile


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--report")
    a = ap.parse_args()
    lic.QMAP.update({"FY2023_Q4": "2023.4Q", "FY2024_Q4": "2024.4Q"})
    ilp = L.load(L.ILP)
    cur = {(r["원보험사코드"], r["항목번호"]): r["값"] for r in ilp if r["공시분기"] == Q}
    result = {}
    for c in CODES:
        rec, liab, asset, bsfile = build(c)
        print(c, rec["status"], rec.get("reason"), rec.get("flags"), "class", rec.get("class"))
        if rec["status"] != "loaded":
            result[c] = {"status": rec["status"], "reason": rec.get("reason")}
            continue
        new = lic.cell_item_values(rec)
        old = {n: cur[(c, n)] for n in range(10, 16) if (c, n) in cur}
        i8 = cur[(c, 8)]
        bs_net = liab - asset
        result[c] = {
            "status": "loaded", "new": new, "old": old, "item8": i8, "bs_liab": round(liab, 2), "bs_asset": round(asset, 2),
            "bs_file": bsfile, "file": rec.get("file"), "class": rec["class"], "unit": rec.get("unit"), "unit_source": rec.get("unit_source"),
            "flags": rec["flags"], "tables": [(t["i"], bool(t["kept"]), round(t["tot_mm"] / 100, 2)) for t in rec["tables"]],
            "net_lrc": lic.eok(rec["net_lrc_mm"]),
            "chk_15_minus_10_14": round(new[15] - new[10] - new[14], 2),
            "chk_15_minus_bs_liab": round(new[15] - liab, 2),
            "chk_item8_minus_net_lrc": round(i8 - lic.eok(rec["net_lrc_mm"]), 2),
            "chk_item8_plus_10_minus_bs_net": round(i8 + new[10] - bs_net, 2),
        }
        print(json.dumps(result[c], ensure_ascii=False))
    if a.report:
        Path(a.report).write_text(json.dumps(result, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    if not a.write:
        print("dry run: nothing written")
        return 0
    if any(v["status"] != "loaded" for v in result.values()):
        raise SystemExit("abort: a cell did not load")
    reasons = REASONS

    raw0 = L.ILP.read_bytes()
    txt = raw0.decode("utf-8")
    crlf = "\r\n" in txt
    rows = json.loads(txt)
    if lic._dump_ilp(rows, crlf) != txt:
        raise SystemExit("abort: master does not round-trip")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    backup = lic.BACKUP_DIR / f"ilp_backup_{stamp}_pre_unify.json"
    pback = lic.BACKUP_DIR / f"ilp_provenance_backup_{stamp}_pre_unify.json"
    if backup.exists() or pback.exists():
        raise SystemExit("abort: backup already exists (already applied?)")
    shutil.copyfile(L.ILP, backup)
    shutil.copyfile(L.PROV, pback)
    idx = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r for r in rows}
    changed, kept_old = [], []
    for c in CODES:
        r_ = result[c]
        for n in range(10, 16):
            row = idx.get((c, Q, n))
            newv = r_["new"].get(n)
            if row is None:
                if newv is not None:
                    print("NOTE restated value exists but no row; not created:", c, n, newv)
                continue
            if abs(row["값"] - r_["old"][n]) > 1e-9:
                raise SystemExit(f"guard failed {c} {n}")
            if newv is None:
                kept_old.append((c, n, row["값"]))
                continue
            changed.append((c, n, row["값"], newv))
            row["값"] = newv
    out = lic._dump_ilp(rows, crlf)
    if L.ILP.read_bytes() != raw0:
        raise SystemExit("abort: master changed meanwhile")
    tmp = L.ILP.with_name(L.ILP.name + ".tmp")
    tmp.write_bytes(out.encode("utf-8"))
    os.replace(tmp, L.ILP)
    before = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r for r in json.loads(txt)}
    after = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r for r in json.loads(L.ILP.read_text(encoding="utf-8"))}
    diffs = {k for k in before if before[k] != after[k]}
    exp = {(c, Q, n) for c, n, o, v in changed if o != v}
    if set(before) != set(after) or diffs != exp:
        raise SystemExit("post-write verification FAILED; restore from " + str(backup))
    print(f"replaced cells with new value: {len(exp)} (of {len(changed)} targeted); backup {backup.name}")
    for k in kept_old:
        print("NOTE no restated source, kept:", k)

    ptxt = L.PROV.read_text(encoding="utf-8")
    p = json.loads(ptxt)
    if json.dumps(p, ensure_ascii=False, indent=1) + "\n" != ptxt:
        raise SystemExit("abort: provenance does not round-trip")
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ")
    for c in CODES:
        r_ = result[c]
        cell = next((x for x in p["cells"] if x["company_code"] == c and x["quarter"] == Q and x.get("item_block") == "lic_dart_note"), None)
        if cell is None:
            raise SystemExit(f"abort: provenance cell for {c} missing")
        cell["original_basis"] = {k: cell.get(k) for k in ("source_file", "basis", "unit", "unit_source", "items_eok", "checks", "net_lrc_eok")}
        cell["original_basis_value"] = {str(n): v for n, v in r_["old"].items()}
        cell["basis"] = BASIS
        cell["basis_note"] = ("items 10-15 unified on the FY2024 filing prior-year-end (2023-12-31, restated) column; original FY2023 values kept in "
                              "original_basis_value / original_basis (ticket 20261011T0100Z)")
        cell["source_file"] = r_["file"]
        cell["unit"], cell["unit_source"] = r_["unit"], r_["unit_source"]
        cell["items_eok"] = {str(n): v for n, v in r_["new"].items()}
        cell["restated_tables"] = r_["tables"]
        cell["flags"] = r_["flags"]
        cell["restated_bs_prior_col"] = {"liab_eok": r_["bs_liab"], "asset_eok": r_["bs_asset"], "source_file": r_["bs_file"]}
        cell["checks_restated"] = {k: r_[k] for k in r_ if k.startswith("chk_")}
        cell["unified_at"] = now
    p["backfills"] = p.get("backfills", []) + [{
        "stage": "2023.4Q-unify-restated", "at": now, "emitted_by": "scripts/unify_ilp_restated_3cells_2023_4q.py",
        "ticket": "inbox/parser/20261011T0100Z__orchestrator__KR0074-KR0079-KR0099_2023.4Q__ilp_unify_restated_basis.md",
        "note": "items 10-15 of the three 2023.4Q cells set to the FY2024 prior-year-end column; originals kept as original_basis_value"}]
    tmp = L.PROV.with_name(L.PROV.name + ".tmp")
    tmp.write_bytes((json.dumps(p, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    os.replace(tmp, L.PROV)

    side = {
        "purpose": ("Restated 2023-12-31 balances (FY2024 filing comparative column) of three 2023.4Q cells. For these cells use "
                    "restated_bs_insurance_contract_liability_eok as the balance-sheet total instead of IFRS17_BS item 20 (original FY2023 basis; master unchanged)."),
        "unit": "억원", "generated_at": now, "emitted_by": "scripts/unify_ilp_restated_3cells_2023_4q.py", "cells": []}
    bs20 = lic.load_bs20()
    for c in CODES:
        r_ = result[c]
        sub = [x for x in L.load(L.PROV)["lrc_model_cells"] if x["company_code"] == c and x["quarter"] == Q]
        i8_diff = sub[0]["vs_fy2023_original"]["item8_minus_orig"] if sub else None
        side["cells"].append({
            "company_code": c, "quarter": Q, "basis": BASIS, "restatement_reason": reasons[c],
            "item8_restated": r_["item8"], "item8_minus_fy2023_original": i8_diff,
            "restated_bs_insurance_contract_liability_eok": r_["bs_liab"],
            "restated_bs_insurance_contract_asset_eok": r_["bs_asset"],
            "restated_bs_net_eok": round(r_["bs_liab"] - r_["bs_asset"], 2),
            "bs_item20_fy2023_original_eok": round(bs20[(c, Q)] / 100.0, 2),
            "bs_source_file": r_["bs_file"],
            "items_10_15_restated": {str(n): v for n, v in r_["new"].items()},
            "items_10_15_fy2023_original": {str(n): v for n, v in r_["old"].items()},
        })
    SIDECAR.write_text(json.dumps(side, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("sidecar written", SIDECAR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
