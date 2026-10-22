"""Read-only: LIC / LRC / total (items 13-ish / 14 / 15, 억원) of KR0073 from every filing, current-period and prior-period (swapped) tables,
stage-1 engine WITHOUT anchor (status stays not_loaded by construction; items_mm is still computed)."""
import sys, json
from pathlib import Path
REPO = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.path.insert(0, str(REPO / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import extract_insurance_liability_lic as lic
import load_ilp_interim_2023_2024 as LI
code = "KR0073"
ALL = {"FY2023_Q1":"2023.1Q","FY2023_Q2":"2023.2Q","FY2023_Q3":"2023.3Q","FY2023_Q4":"2023.4Q","FY2024_Q1":"2024.1Q","FY2024_Q2":"2024.2Q","FY2024_Q3":"2024.3Q","FY2024_Q4":"2024.4Q",
       "FY2025_Q1":"2025.1Q","FY2025_Q2":"2025.2Q","FY2025_Q3":"2025.3Q","FY2025_Q4":"2025.4Q","FY2026_Q1":"2026.1Q","FY2026_Q2":"2026.2Q"}
lic.QMAP.update(ALL)
out = {}
for fy, q in ALL.items():
    for swap in (False, True):
        tag = "prior" if swap else "cur"
        try:
            rec, files, metas = LI.assemble_one(code, fy, q, None, None, swap=swap)
        except Exception as e:
            print(fy, tag, "ERR", repr(e)[:150]); continue
        im = rec.get("items_mm")
        if not im:
            print(fy, tag, rec["status"], rec.get("reason")); out[f"{fy}|{tag}"] = {"reason": rec.get("reason")}; continue
        e = lambda x: round(x / 100.0, 2)
        row = {"lic": e(im["lic_total"]), "lrc": e(im["lrc_total"]), "total": e(im["total"]), "bel": e(im["bel"]), "ra": e(im["ra"]), "single": e(im["single"]),
               "class": rec.get("class"), "unit": rec.get("unit"), "file": rec.get("file"), "flags": rec.get("flags"),
               "tables": [(t["i"], bool(t["kept"]), e(t["tot_mm"])) for t in rec.get("tables", [])]}
        out[f"{fy}|{tag}"] = row
        print(fy, tag, "LIC", row["lic"], "LRC", row["lrc"], "TOT", row["total"], "cls", row["class"], "tabs", row["tables"])
Path(REPO/"data/_derived/remaining_20261022/b_bs_ilp/s9_ilp_all.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
