"""Read-only: for every bucket in the 40-bucket back-solve census, replay
fill_post_transition_to_disclosure.py's current extraction and compare its
item14 (지급여력기준금액) 값_적용후 against the master. This tells us whether
the current (already-imported, unmodified) generator would self-heal each
bucket on a plain rerun, or still reproduces the same back-solved decimal
(which would mean a live generator bug, not just a stale historical value).

No writes anywhere -- imports fill_post_transition_to_disclosure.py as a
module and calls its private extraction helpers directly, same technique as
_probe_20260921_kr0071_headline_recompute.py.
"""
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

spec = importlib.util.spec_from_file_location(
    "fill_post_transition_to_disclosure", REPO / "scripts" / "fill_post_transition_to_disclosure.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

MASTER = REPO / "kics_disclosure.json"
MD_INBOX = REPO / "md_inbox"
CENSUS = REPO / "data" / "_derived" / "_probe_20260921_item14_backsolve_census.json"

KEY_CODE = "원보험사코드"
KEY_ITEM = "항목번호"
KEY_Q = "공시분기"
KEY_VAL = "값"
KEY_POST = "값_적용후"


def quarter_to_period_label(quarter: str) -> str:
    # "2025.2Q" -> "FY2025_Q2"
    year, rest = quarter.split(".")
    q = rest.rstrip("Q")
    return f"FY{year}_Q{q}"


def main():
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    index = {}
    for r in rows:
        index[(r[KEY_CODE], r[KEY_Q], r[KEY_ITEM])] = r

    census = json.loads(CENSUS.read_text(encoding="utf-8"))

    results = []
    for bucket in census:
        code = bucket["code"]
        quarter = bucket["quarter"]
        period_label = quarter_to_period_label(quarter)
        md_dir = MD_INBOX / period_label
        matches = list(md_dir.glob(f"{code}_*.md")) if md_dir.is_dir() else []
        entry = {
            "code": code,
            "name": bucket["name"],
            "quarter": quarter,
            "master_item14_post": bucket["item14_post_master"],
            "md_found": bool(matches),
        }
        if not matches:
            entry["verdict"] = "NO_MD_INBOX_FILE"
            results.append(entry)
            continue

        md_path = matches[0]
        text = md_path.read_text(encoding="utf-8")
        tables = mod._scan_tables_with_context(text)
        existing_values = {
            item_no: row.get(KEY_VAL)
            for (c, q, item_no), row in index.items()
            if c == code and q == quarter
        }
        try:
            post_map, provenance, dbg, unit_fixed_items = mod._extract_post_values(
                tables, code, existing_values
            )
        except Exception as exc:  # noqa: BLE001 -- diagnostic probe
            entry["verdict"] = f"EXTRACT_ERROR: {exc!r}"
            results.append(entry)
            continue

        if 14 not in post_map:
            entry["verdict"] = "NO_ITEM14_RECOMPUTED"
            entry["headline_debug"] = [d for d in dbg if "총괄" in d]
            results.append(entry)
            continue

        recomputed_pre, recomputed_post = post_map[14]
        entry["recomputed_item14_post"] = recomputed_post
        entry["recomputed_item14_provenance"] = provenance.get(14)
        entry["headline_debug"] = [d for d in dbg if "총괄" in d]

        try:
            master_f = float(str(bucket["item14_post_master"]).replace(",", ""))
            recomputed_f = float(str(recomputed_post).replace(",", ""))
            same = abs(master_f - recomputed_f) < 0.005
        except (TypeError, ValueError):
            same = None

        if same is True:
            entry["verdict"] = "UNCHANGED_ON_RERUN"
        elif same is False:
            entry["verdict"] = "WOULD_CHANGE_ON_RERUN"
        else:
            entry["verdict"] = "COMPARE_ERROR"
        results.append(entry)

    tally = {}
    for e in results:
        tally[e["verdict"].split(":")[0]] = tally.get(e["verdict"].split(":")[0], 0) + 1

    print("tally:", tally)
    for e in results:
        print(
            e["code"], e["name"], e["quarter"], "->", e["verdict"],
            "master=", e.get("master_item14_post"),
            "recomputed=", e.get("recomputed_item14_post"),
            "prov=", e.get("recomputed_item14_provenance"),
        )

    out_path = REPO / "data" / "_derived" / "_probe_20260921_backsolve_recompute_all40.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
