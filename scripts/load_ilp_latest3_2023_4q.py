# -*- coding: utf-8 -*-
"""
Owner decision 2026-10-11 ("use the latest filing"): load items 1-8 of 2023.4Q for the three cells the backfill round withheld
(KR0074 Cigna/라이나, KR0079 Mirae Asset Life, KR0099 KB Life) from the COMPARATIVE <2023년> column of the FY2024 year-end
disclosure (4-6-2 / the DART FY2024 note table).  Append only; the basis is marked in the provenance file
('latest_filing_comparative_restatable') together with the difference against the FY2023 original.

Usage:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/load_ilp_latest3_2023_4q.py [--write] [--report out.json]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import load_ilp_backfill_pre2025 as L  # noqa: E402

lic = L.lic
CODES = ["KR0074", "KR0079", "KR0099"]
Q = "2023.4Q"
BASIS = "latest_filing_comparative_restatable"
# 재무상태표 unit of the FY2024 filing (header cue read by eye in p63_fy2024_bs_prior.py output): won / won / million won
BS_UNIT_TO_EOK = {"KR0074": 1e-8, "KR0079": 1e-8, "KR0099": 1e-2}


def fs_bs_row(fy: str, code: str, col: int):
    """(보험계약부채, 보험계약자산) of the 재무상태표 in the main _00760 file: column 2 = current, 3 = prior year end; 억원"""
    base = REPO / "data" / "dart" / fy / "raw"
    for d in sorted(os.listdir(base)):
        if d[:6] != code:
            continue
        files = sorted(glob.glob(str(base / d / "*.xml"))) + sorted(glob.glob(str(base / d / "xml" / "*.xml")))
        f = [x for x in files if x.endswith("_00760.xml")] or files[:1]
        t = lic.read_xml(f[0])
        for m in lic.TAB_RE.finditer(t):
            flat = lic.comp(lic.clean(m.group(0)))
            if "자산총계" not in flat or "부채총계" not in flat or "보험계약부채" not in flat:
                continue
            g, _ = lic.parse_table(m.group(0))
            liab = asset = None
            for r in g:
                lab = lic.comp(r[0]) if r else ""
                v = lic.parse_num(r[col]) if len(r) > col else None
                if "보험계약부채" in lab and "재보험" not in lab:
                    liab = v
                if "보험계약자산" in lab and "재보험" not in lab:
                    asset = v
            k = BS_UNIT_TO_EOK[code]
            return (None if liab is None else liab * k), (0.0 if asset is None else asset * k), os.path.relpath(f[0], REPO).replace("\\", "/")
    return None, None, None


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--report")
    args = ap.parse_args(argv)
    lic.QMAP.update({"FY2023_Q4": "2023.4Q", "FY2024_Q4": "2024.4Q"})

    ilp = L.load(L.ILP)
    reg = lic.ilp_registry(ilp)
    have = {(r["원보험사코드"], r["공시분기"], r["항목번호"]) for r in ilp}
    bs20 = lic.load_bs20()
    csmw = {(r["원보험사코드"], r["공시분기"]): r["값"] for r in L.load(L.CSMW) if r["항목번호"] == 6}
    prov = L.load(L.PROV)
    withheld = {e["company_code"]: e for e in prov["lrc_model_not_loaded"] if e["quarter"] == Q and e["company_code"] in CODES}
    recs = {r["code"]: r for r in lic.build_all(CODES, ["FY2023_Q4"], verbose=False)}

    new_rows, new_prov, report = [], [], {}
    for code in CODES:
        if (code, Q, 1) in have:
            raise SystemExit(f"abort: {code} {Q} item 1 already exists")
        rd = L.read_pdf(code)
        xc = L.xml_candidates(code)
        cell = L.lrc_cell(code, 2023, rd, xc)
        if cell["status"] != "loaded":
            raise SystemExit(f"abort: {code} comparative not readable: {cell}")
        items = {i: round(cell["items"].get(i, 0.0), 4) for i in range(1, 8)}
        items[8] = round(sum(items[i] for i in range(1, 8)), 4)
        wh = withheld[code]["detail"]["withheld_items_eok"]
        if any(abs(items[i] - wh[str(i)]) > 1e-6 for i in range(1, 9)):
            raise SystemExit(f"abort: {code} re-read differs from the withheld values in provenance")
        # ---- reconciliation against the FY2023 original basis -------------------------------------------------------------
        rec = recs[code]
        i15 = lic.cell_item_values(rec)
        net_orig = rec["net_lrc_mm"] / 100.0
        csm_cmp = items[3] + items[6]
        cs = csmw.get((code, Q))
        b20 = bs20.get((code, Q)) / 100.0
        liab_prior, asset_prior, bs_file = fs_bs_row("FY2024_Q4", code, 3)
        liab_cur_fy23, asset_cur_fy23, _ = fs_bs_row("FY2023_Q4", code, 2)
        lic_orig = i15.get(10, 0.0)                      # items 10 (LIC) of the master = FY2023 original basis
        bs_prior_net = liab_prior - asset_prior          # restated 2023-12-31 net insurance contract liability
        close_restated = items[8] + lic_orig - bs_prior_net
        diff = {
            "item8_comparative": items[8], "net_lrc_fy2023_dart": round(net_orig, 2), "item8_minus_orig": round(items[8] - net_orig, 2),
            "csm_3plus6_comparative": round(csm_cmp, 2), "csm_waterfall_2023_4Q": cs, "csm_minus_wf": None if cs is None else round(csm_cmp - cs, 2),
            "item15_fy2023": i15[15], "bs_item20_fy2023": round(b20, 2),
            "bs_fy2023_liab_asset": [None if liab_cur_fy23 is None else round(liab_cur_fy23, 2), round(asset_cur_fy23, 2)],
            "bs_fy2024_prior_col_liab_asset": [round(liab_prior, 2), round(asset_prior, 2)], "bs_fy2024_prior_file": bs_file,
            "bs_restated_net": round(bs_prior_net, 2), "bs_restatement_delta_liab": round(liab_prior - liab_cur_fy23, 2),
            "item8_plus_lic_fy2023_minus_bs_restated_net": round(close_restated, 2),
            "implied_restated_lic_eok": round(bs_prior_net - items[8], 2), "lic_item10_in_master_fy2023_basis": round(lic_orig, 2),
        }
        report[code] = {"items": items, "src": cell["src"], "flags": cell.get("flags"), "xml": cell.get("xml"), "diff": diff}
        for n in range(1, 9):
            name, level = L.MODEL_ITEMS[n]
            new_rows.append(L.row(reg, code, Q, n, name, L.SEC_MODEL, level, items[n]))
        new_prov.append({
            "company_code": code, "quarter": Q, "item_block": "lrc_model_table_4-6-2", "source_id": cell["src"],
            "as_of_date": lic.as_of_date(Q), "source_file": cell.get("file"), "page": cell.get("page"), "table": cell.get("table"),
            "table_year": 2023, "table_year_src": cell.get("table_year_src"), "unit_in_source": cell["unit_in_source"],
            "printed_run": cell.get("run"), "run_kind": cell.get("run_kind"), "text_source": cell.get("text_source"),
            "items_eok": {str(k): v for k, v in items.items()}, "item9": None, "item9_evidence": None,
            "dart_note_crosscheck": cell.get("xml"), "flags": cell.get("flags", []),
            "basis": BASIS,
            "basis_note": ("owner decision 2026-10-11: latest filing's comparative column (FY2024 year-end <2023년>), which RESTATES the 2023-12-31 balances; "
                           "differs from the FY2023 original -- the other items of this cell (10-15, BS item 20, and for KR0079/KR0099 the CSM_waterfall) are FY2023 original basis"),
            "vs_fy2023_original": diff,
            "previously_withheld_reason": withheld[code]["reason"],
            "published_in": "FY2024 year-end 경영공시 / 사업보고서 (comparative column, restated)",
        })
        print(code, "items", items, "src", cell["src"], cell.get("flags"))
        print("   ", json.dumps(diff, ensure_ascii=False))
    new_rows.sort(key=lambda r: (r["원보험사코드"], r["공시분기"], r["항목번호"]))
    clash = [(r["원보험사코드"], r["공시분기"], r["항목번호"]) for r in new_rows if (r["원보험사코드"], r["공시분기"], r["항목번호"]) in have]
    if clash:
        raise SystemExit(f"abort: keys exist {clash[:3]}")
    print(f"rows to add: {len(new_rows)}")
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=1, default=str)
    if not args.write:
        print("dry run: nothing written")
        return 0

    backup = lic.merge_into_ilp(new_rows, tag="pre_latest3")
    # provenance: additive, guarded; the three 'not loaded' records stay (audit trail) but get a `resolved` marker
    raw0 = L.PROV.read_bytes()
    txt = raw0.decode("utf-8")
    p = json.loads(txt)
    if json.dumps(p, ensure_ascii=False, indent=1) + "\n" != txt:
        raise SystemExit("abort: provenance does not round-trip; refusing to rewrite")
    if any(c["company_code"] in CODES and c["quarter"] == Q for c in p["lrc_model_cells"]):
        raise SystemExit("abort: lrc_model_cells already holds one of the three")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    pbackup = lic.BACKUP_DIR / f"ilp_provenance_backup_{stamp}_pre_latest3.json"
    shutil.copyfile(L.PROV, pbackup)
    p["lrc_model_cells"] = p["lrc_model_cells"] + new_prov
    for e in p["lrc_model_not_loaded"]:
        if e["quarter"] == Q and e["company_code"] in CODES:
            e["resolved"] = {"at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ"), "how": "loaded from the latest filing's comparative column (owner decision 2026-10-11)",
                             "see": "lrc_model_cells[basis=" + BASIS + "]", "emitted_by": "scripts/load_ilp_latest3_2023_4q.py"}
    p["backfills"] = p.get("backfills", []) + [{
        "stage": "2023.4Q-latest3", "at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ"), "emitted_by": "scripts/load_ilp_latest3_2023_4q.py",
        "ticket": "inbox/parser/20261011T0010Z__orchestrator__KR0074-KR0079-KR0099_2023.4Q__ilp_latest_filing_comparative.md",
        "note": "items 1-8 of KR0074/KR0079/KR0099 2023.4Q from the FY2024 comparative column (restated 2023-12-31 balances); basis=" + BASIS}]
    out = json.dumps(p, ensure_ascii=False, indent=1) + "\n"
    tmp = L.PROV.with_name(L.PROV.name + ".tmp")
    tmp.write_bytes(out.encode("utf-8"))
    os.replace(tmp, L.PROV)
    print(f"appended {len(new_rows)} rows; backup {backup.name}; provenance backup {pbackup.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
