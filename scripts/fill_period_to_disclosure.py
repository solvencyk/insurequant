"""Fill or refresh kics_disclosure.json from md_inbox."""
from __future__ import annotations
import argparse, io, json, re, sys
from collections import defaultdict
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from solvency.parser.kics_baseline_match import match_baseline_value_or_zero
from solvency.parser.kics_disclosure_parser import build_label_lookups, extract_kics_detail_rows, normalise_item_value
JSON_PATH = REPO / "kics_disclosure.json"
MD_INBOX = REPO / "md_inbox"
_PERIOD_RE = re.compile(r"^FY(\d{4})_Q([1-4])$")
STALE_DELETES = [("KR0005", "2025.4Q", range(18, 27))]

def _fields():
    k = list(json.loads(JSON_PATH.read_text(encoding="utf-8"))[0].keys())
    return {"code": k[0], "cname": k[1], "ticker": k[2], "kind": k[3], "item": k[4], "name": k[5], "quarter": k[6], "val": k[7]}

def _md_period_to_quarter(period):
    m = _PERIOD_RE.match(period)
    return f"{m.group(1)}.{m.group(2)}Q"

def _quarter_prior(quarter):
    m = re.match(r"^(\d{4})\.([1-4])Q$", quarter)
    y, q = int(m.group(1)), int(m.group(2))
    return f"{y - 1}.4Q" if q == 1 else f"{y}.{q - 1}Q"


def _is_core_baseline(baseline: list, F: dict) -> bool:
    """Prior-quarter rows must include capital summary items 1-28, not sub-items only."""
    items = {
        int(r[F["item"]])
        for r in baseline
        if r.get(F["item"]) is not None and str(r[F["item"]]).isdigit()
    }
    core = {i for i in items if i <= 28}
    return (
        {1, 4, 14, 17, 22} <= core
        or (1 in core and 14 in core and len(core) >= 20)
    )


def _supplement_core_baseline(baseline: list, rows: list, code: str, F: dict) -> list:
    """Add missing item 1-28 name templates from other quarters (e.g. item10 비지배지분)."""
    have = {
        int(r[F["item"]])
        for r in baseline
        if r.get(F["item"]) is not None and str(r[F["item"]]).isdigit()
    }
    missing = {i for i in range(1, 29) if i not in have}
    if not missing:
        return baseline
    templates: dict[int, dict] = {}
    by_q: dict[str, list] = defaultdict(list)
    for r in rows:
        if r.get(F["code"]) != code:
            continue
        it = r.get(F["item"])
        if it is None or not str(it).isdigit():
            continue
        item_no = int(it)
        if item_no > 28:
            continue
        by_q[r.get(F["quarter"])].append(r)
    for q in sorted(by_q.keys(), key=lambda qq: len(by_q[qq]), reverse=True):
        for r in by_q[q]:
            item_no = int(r[F["item"]])
            if item_no in missing and item_no not in templates:
                templates[item_no] = r
    if missing - set(templates):
        global_templates: dict[int, dict] = {}
        for r in rows:
            it = r.get(F["item"])
            if it is None or not str(it).isdigit():
                continue
            item_no = int(it)
            if item_no > 28 or item_no in global_templates:
                continue
            global_templates[item_no] = r
        for item_no in sorted(missing - set(templates)):
            if item_no in global_templates:
                templates[item_no] = global_templates[item_no]
    if not templates:
        return baseline
    out = list(baseline)
    for item_no in sorted(templates):
        out.append(dict(templates[item_no]))
    return out


def _reconcile_item4_from_components(rows: list, F: dict) -> int:
    """Align item4 to sum(items 5-11) when all components exist (rule 2)."""
    buckets: dict[tuple[str, str], dict[int, dict]] = defaultdict(dict)
    for r in rows:
        it = r.get(F["item"])
        if it is None or not str(it).isdigit():
            continue
        item_no = int(it)
        if item_no > 11:
            continue
        buckets[(r.get(F["code"]), r.get(F["quarter"]))][item_no] = r
    updated = 0
    for items in buckets.values():
        if 4 not in items:
            continue
        component_vals: list[float] = []
        complete = True
        for i in range(5, 12):
            if i not in items:
                complete = False
                break
            raw = items[i].get(F["val"])
            if raw is None:
                complete = False
                break
            try:
                component_vals.append(float(raw))
            except (TypeError, ValueError):
                complete = False
                break
        if not complete or len(component_vals) != 7:
            continue
        total = sum(component_vals)
        row4 = items[4]
        try:
            current = float(row4[F["val"]])
        except (TypeError, ValueError):
            continue
        if abs(current - total) < 1e-6:
            continue
        if abs(current - total) > 10:
            continue
        rounded = int(round(total)) if abs(total - round(total)) < 1e-6 else total
        row4[F["val"]] = str(int(rounded)) if isinstance(rounded, int) else str(rounded)
        updated += 1
    return updated


def _baseline_for_company(rows, code, tq, bq, F):
    """Row templates for items 1-28 when prior-quarter baseline is missing."""
    baseline = [r for r in rows if r.get(F["code"]) == code and r.get(F["quarter"]) == bq]
    if baseline and _is_core_baseline(baseline, F):
        return _supplement_core_baseline(baseline, rows, code, F)
    partial = [
        r
        for r in rows
        if r.get(F["code"]) == code
        and r.get(F["quarter"]) == tq
        and int(r.get(F["item"], 99)) <= 28
    ]
    if partial:
        return _supplement_core_baseline(partial, rows, code, F)
    by_q = defaultdict(list)
    for r in rows:
        if r.get(F["code"]) == code and int(r.get(F["item"], 99)) <= 28:
            by_q[r.get(F["quarter"])].append(r)
    if not by_q:
        return []
    best_q = max(by_q.keys(), key=lambda q: len(by_q[q]))
    seen = {}
    for r in by_q[best_q]:
        seen[(r[F["item"]], r[F["name"]])] = r
    return _supplement_core_baseline(list(seen.values()), rows, code, F)


def _process(rows, periods, refresh, F, target_quarter=None):
    ins = upd = rem = 0
    for period in periods:
        tq = target_quarter or _md_period_to_quarter(period)
        bq = _quarter_prior(tq)
        md_dir = MD_INBOX / period
        if not md_dir.is_dir():
            continue
        for code, quarter, ir in STALE_DELETES:
            if quarter != tq:
                continue
            n0 = len(rows)
            rows[:] = [r for r in rows if not (r.get(F["code"]) == code and r.get(F["quarter"]) == quarter and r.get(F["item"]) in ir)]
            rem += n0 - len(rows)
        baselines = defaultdict(list)
        for r in rows:
            if r.get(F["quarter"]) == bq:
                baselines[r[F["code"]]].append(r)
        index = {}
        for r in rows:
            if r.get(F["quarter"]) == tq:
                index[(r[F["code"]], r[F["item"]], r[F["name"]])] = r
        for md_path in sorted(md_dir.glob("*.md")):
            code = md_path.stem.split("_", 1)[0]
            baseline = _baseline_for_company(rows, code, tq, bq, F)
            if not baseline:
                continue
            table = extract_kics_detail_rows(md_path.read_text(encoding="utf-8"), tq)
            if not table:
                continue
            lookup, core = build_label_lookups(table)
            anchor = next((b for b in baseline if b.get(F["code"]) == code), None)
            for base in baseline:
                value = match_baseline_value_or_zero(
                    base[F["name"]], lookup, core, table
                )
                if value is None:
                    continue
                value = normalise_item_value(int(base[F["item"]]), base[F["name"]], value)
                key = (code, base[F["item"]], base[F["name"]])
                ex = index.get(key)
                if ex is not None:
                    if refresh and ex.get(F["val"]) != value:
                        ex[F["val"]] = value
                        upd += 1
                else:
                    nr = dict(base)
                    if anchor is not None:
                        for field in ("code", "cname", "ticker", "kind"):
                            nr[F[field]] = anchor[F[field]]
                    nr[F["quarter"]] = tq
                    nr[F["val"]] = value
                    rows.append(nr)
                    index[key] = nr
                    ins += 1
    upd += _reconcile_item4_from_components(rows, F)
    return ins, upd, rem

def main(argv):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--refresh", action="store_true")
    p.add_argument("--period", action="append")
    p.add_argument("--all-periods", action="store_true")
    p.add_argument("--target-quarter", help="Override disclosure quarter (e.g. 2024.1Q) when MD holds lag columns")
    a = p.parse_args(argv)
    periods = sorted(x.name for x in MD_INBOX.glob("FY*_Q?") if x.is_dir()) if a.all_periods else (a.period or ["FY2025_Q4"])
    F = _fields()
    before = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    rows = list(before)
    ins, upd, rem = _process(rows, periods, a.refresh, F, target_quarter=a.target_quarter)
    print(f"loaded={len(before)} ins={ins} upd={upd} rem={rem} after={len(rows)}")
    if not a.dry_run:
        JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print("wrote", len(rows))
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))