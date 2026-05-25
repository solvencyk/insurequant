"""Recalculate item 28 basic-capital ratio post-transition values."""
from __future__ import annotations
import argparse, io, json, shutil, sys
from collections import defaultdict
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
JSON_PATH = REPO / "kics_disclosure.json"
TEMPLATES_JSON = REPO / "templates" / "kics_disclosure.json"
VAL = "\uac12"
VAL_POST = "\uac12_\uc801\uc6a9\ud6c4"
CODE = "\uc6d0\ubcf4\ud5d8\uc0ac\ucf54\ub4dc"
QUARTER = "\uacf5\uc2dc\ubd84\uae30"
ITEM = "\ud56d\ubaa9\ubc88\ud638"
NAME = "\uc6d0\uc218\uc0ac\uba85"
def _to_float(raw):
    if raw is None: return None
    s = str(raw).strip().replace(",", "")
    if s in ("", "-"): return None
    s = s.replace("\u25b3", "-").replace("\u25b2", "-")
    if s.startswith("(") and s.endswith(")"): s = "-" + s[1:-1]
    try: return float(s)
    except ValueError: return None
def _format_ratio(x):
    s = f"{x:.8f}".rstrip("0").rstrip(".")
    return s or "0"
def _values_equal(a, b): return abs(a - b) < 1e-6
def _post_value(row):
    post = row.get(VAL_POST)
    if post is not None and post != "": return str(post)
    return str(row[VAL])
def recalc(rows):
    buckets = defaultdict(dict)
    for row in rows: buckets[(row[CODE], row[QUARTER])][row[ITEM]] = row
    updated = skipped_equal = 0
    samples = []
    for (code, quarter), items in sorted(buckets.items()):
        i2, i14, i28 = items.get(2), items.get(14), items.get(28)
        if not i2 or not i14 or not i28: continue
        basic_pre = _to_float(i2.get(VAL)); basic_post = _to_float(_post_value(i2))
        req_pre = _to_float(i14.get(VAL)); req_post = _to_float(_post_value(i14))
        ratio_pre = _to_float(i28.get(VAL))
        if None in (basic_pre, basic_post, req_pre, req_post, ratio_pre): continue
        if _values_equal(basic_pre, basic_post) and _values_equal(req_pre, req_post): continue
        if req_post <= 0: continue
        ratio_post = basic_post / req_post * 100.0
        if _values_equal(ratio_post, ratio_pre):
            skipped_equal += 1; continue
        formatted = _format_ratio(ratio_post)
        if i28.get(VAL_POST) == formatted: continue
        i28[VAL_POST] = formatted; updated += 1
        if len(samples) < 8: samples.append((code, quarter, i28.get(NAME, code), ratio_pre, ratio_post))
    return updated, skipped_equal, samples
def main(argv):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    p = argparse.ArgumentParser(); p.add_argument("--dry-run", action="store_true"); args = p.parse_args(argv)
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    print(f"loaded {len(rows)} rows from {JSON_PATH}")
    updated, skipped_equal, samples = recalc(rows)
    print(f"item28 post-transition rows set/updated: {updated}")
    print(f"skipped (ratio_post == ratio_pre): {skipped_equal}")
    if samples:
        print("\nSample ratio_pre -> ratio_post:")
        for code, quarter, name, r_pre, r_post in samples:
            print(f"  {code} {quarter} {name}: {r_pre:.4f}% -> {r_post:.4f}%")
    if args.dry_run:
        print("(dry-run; no write)"); return 0
    if updated:
        JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {len(rows)} rows to {JSON_PATH}")
    else: print("nothing to write")
    shutil.copy2(JSON_PATH, TEMPLATES_JSON); print(f"synced -> {TEMPLATES_JSON}"); return 0
if __name__ == "__main__": sys.exit(main(sys.argv[1:]))
