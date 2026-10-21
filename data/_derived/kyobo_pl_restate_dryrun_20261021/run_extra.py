"""Read-only: (1) restated 2024.4Q from the FY2025 annual (corp-code fix), (2) item 6/7 under the alternate row label
('발생한보험서비스수익' read as the same row as '…비용'), (3) original-vintage reproduction for 2023.3Q/2023.4Q (convention check).
Writes restated_blocks_alt.json.
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import plib  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ROOT = plib.ROOT
root = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
cur = {}
for r in root:
    if r["원보험사코드"] == "KR0073":
        cur.setdefault(r["공시분기"], {})[r["항목번호"]] = r.get("값")


def clean(d):
    return {str(k): (round(v, 6) if isinstance(v, float) else v) for k, v in d.items()}


def rows_of(t, labels):
    out = {}
    if t is None:
        return out
    for r in t.rows:
        lf = plib.C._life_label_flat(r)
        nums = plib.C._row_nums(r)
        for lab in labels:
            if lab in lf and nums:
                out.setdefault(lab, nums)
    return out


res = {}
t0 = time.time()
# --- later filings (restated, alt label on/off) ---
for later in ["2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q"]:
    tables = plib.parse_tables(plib.raw_dirs(later))
    q_prior = f"{int(later[:4]) - 1}{later[4:]}"
    v0, m0 = plib.block(later, True, tables, alt_label=False)
    v1, m1 = plib.block(later, True, tables, alt_label=True)
    picks = plib.kyobo_picks(tables)
    rev_rows = rows_of(picks["rev"], ["발생한보험서비스수익", "발생한보험서비스비용", "예상보험금", "예상유지비등", "손실요소배분액"])
    cost_rows = rows_of(picks["cost"], ["실제보험금", "실제계약유지비용", "실제투자관리비"])
    res[q_prior] = {"later": later, "restated": clean(v0), "restated_alt": clean(v1), "t1_src": m0["t1_src"],
                    "rev_rows": rev_rows, "cost_rows": cost_rows, "t2": clean(m0["t2"] or {}), "t2_alt": clean(m1["t2"] or {})}
    # production-mode block of the later filing itself (alt on) for item 6 convention comparison
    vc, _ = plib.block(later, False, tables, alt_label=True)
    res.setdefault("_prod_alt", {})[later] = clean(vc)
    print(f"[{time.strftime('%H:%M:%S')}] {later} done ({time.time() - t0:.0f}s)", flush=True)
    del tables
# --- original filings 2023.3Q / 2023.4Q (production mode, current column) ---
for q in ["2023.3Q", "2023.4Q"]:
    tables = plib.parse_tables(plib.raw_dirs(q))
    v0, m0 = plib.block(q, False, tables, alt_label=False)
    v1, m1 = plib.block(q, False, tables, alt_label=True)
    picks = plib.kyobo_picks(tables)
    res.setdefault("_orig", {})[q] = {"block": clean(v0), "block_alt": clean(v1),
                                      "rev_rows": rows_of(picks["rev"], ["발생한보험서비스수익", "발생한보험서비스비용", "예상보험금", "예상유지비등", "손실요소배분액"]),
                                      "cost_rows": rows_of(picks["cost"], ["실제보험금", "실제계약유지비용", "실제투자관리비"]),
                                      "t1_src": m0["t1_src"]}
    print(f"[{time.strftime('%H:%M:%S')}] original {q} done", flush=True)
    del tables
(HERE / "restated_blocks_alt.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print("DONE")
