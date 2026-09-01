"""Cell census: what does the re-converted MD make extractable that the old one did not?

Runs the same extractors the fill_* scripts use, against the BACKUP markdown
(pre re-conversion) and the CURRENT markdown, then compares both against the
master kics_disclosure.json.

    items 1-28   kics_disclosure_parser.extract_kics_detail_rows
    items 29-35  fill_subitems_to_disclosure._scan_subitem_rows
    items 36-40  fill_market_subitems_to_disclosure.extract_mkt_subs
    민감도        extract_kics_rate_sensitivity.find_section_table

Nothing is written to any master. Output: stdout table + JSON.
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PERIOD = "FY2026_Q2"
QUARTER = "2026.2Q"
NEW_DIR = REPO / "md_inbox" / PERIOD
OLD_DIR = REPO / "data" / "_derived" / "md_backup_20260901_windowfix" / "md_inbox"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return text
    _, _, rest = text.partition("---\n")
    _, _, body = rest.partition("\n---\n")
    return body


def _front(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    _, _, rest = text.partition("---\n")
    front, _, _ = rest.partition("\n---\n")
    meta = {}
    for line in front.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip().strip('"')
    return meta


def main() -> int:
    from solvency.parser.kics_disclosure_parser import extract_kics_detail_rows

    mkt = _load("_mkt", REPO / "scripts" / "fill_market_subitems_to_disclosure.py")
    sub = _load("_sub", REPO / "scripts" / "fill_subitems_to_disclosure.py")
    rs = _load("_rs", REPO / "scripts" / "extract_kics_rate_sensitivity.py")

    master = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
    keys = list(master[0].keys())
    F = {"code": keys[0], "item": keys[4], "name": keys[5], "quarter": keys[6], "val": keys[7]}
    master_cells: dict[tuple[str, int], str] = {}
    for r in master:
        if r.get(F["quarter"]) != QUARTER:
            continue
        try:
            item = int(r.get(F["item"]))
        except (TypeError, ValueError):
            continue
        master_cells[(r.get(F["code"]), item)] = str(r.get(F["val"]))

    rows = []
    print(f"\n=== re-conversion cell census ({PERIOD}) ===\n")
    print(
        f"{'code':<8}{'run':<18}{'ranges(new)':<26}"
        f"{'core':<12}{'29-35':<10}{'36-40':<12}{'민감도':<8}  gained"
    )
    print("-" * 140)
    for new_md in sorted(NEW_DIR.glob("*.md")):
        code = new_md.stem.split("_")[0]
        old_md = OLD_DIR / new_md.name
        if not old_md.exists():
            continue
        old_body, new_body = _body(old_md), _body(new_md)
        meta = _front(new_md)
        changed = old_body != new_body

        def sets(body: str):
            core = {name for name, _ in extract_kics_detail_rows(body, QUARTER)}
            s2935 = set(sub._scan_subitem_rows(body, QUARTER).keys())
            s3640 = set(mkt.extract_mkt_subs(body).keys())
            sens = rs.find_section_table(body) is not None
            return core, s2935, s3640, sens

        oc, o29, o36, osens = sets(old_body)
        nc, n29, n36, nsens = sets(new_body)
        gained = []
        if nc - oc:
            gained.append(f"core+{len(nc - oc)}")
        if n29 - o29:
            gained.append(f"29-35+{sorted(n29 - o29)}")
        if n36 - o36:
            gained.append(f"36-40+{sorted(n36 - o36)}")
        if nsens and not osens:
            gained.append("민감도+")
        lost = []
        if oc - nc:
            lost.append(f"core-{len(oc - nc)}")
        if o29 - n29:
            lost.append(f"29-35-{sorted(o29 - n29)}")
        if o36 - n36:
            lost.append(f"36-40-{sorted(o36 - n36)}")
        if osens and not nsens:
            lost.append("민감도-")

        if not changed:
            continue
        print(
            f"{code:<8}{meta.get('run_id',''):<18}{meta.get('source_page_ranges','')[:25]:<26}"
            f"{len(oc)}->{len(nc):<8}{len(o29)}->{len(n29):<6}"
            f"{len(o36)}->{len(n36):<8}{int(osens)}->{int(nsens):<5}  "
            + (" ".join(gained) if gained else "-")
            + (("   LOST: " + " ".join(lost)) if lost else "")
        )
        rows.append(
            {
                "company": code,
                "run_id": meta.get("run_id", ""),
                "source_page_ranges": meta.get("source_page_ranges", ""),
                "source_total_pages": meta.get("source_total_pages", ""),
                "docling_status": meta.get("docling_status", ""),
                "docling_dropped_pages": meta.get("docling_dropped_pages", ""),
                "docling_recovered_pages": meta.get("docling_recovered_pages", ""),
                "docling_unrecovered_pages": meta.get("docling_unrecovered_pages", ""),
                "core_old": sorted(oc),
                "core_new": sorted(nc),
                "sub2935_old": sorted(o29),
                "sub2935_new": sorted(n29),
                "mkt3640_old": {k: mkt.extract_mkt_subs(old_body)[k] for k in sorted(o36)},
                "mkt3640_new": {k: mkt.extract_mkt_subs(new_body)[k] for k in sorted(n36)},
                "sens_old": osens,
                "sens_new": nsens,
                "gained": gained,
                "lost": lost,
                "master_3640": {
                    str(i): master_cells.get((code, i)) for i in range(36, 41)
                },
            }
        )

    out = REPO / "data" / "_derived" / "_probe_reconvert_cell_census.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nchanged files: {len(rows)}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
