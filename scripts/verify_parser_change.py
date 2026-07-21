#!/usr/bin/env python3
"""verify_parser_change.py — one-command harness around a parser/extractor change.

"손으로 짰던 절차의 스크립트화": snapshot the data artifacts the validators read,
make a parser/extractor change, then run this to get a **blast-radius** diff
(what cells/values moved) plus a **validator re-run** (RED/YELLOW deltas) — the manual
pre/post-change procedure, automated.

This script is validation TOOLING. It does NOT modify any validator, any parsed data,
or any parser/downloader code. It only reads, hashes, copies, diffs, and shells out to
the existing validators. It NEVER runs build_csm_waterfall_master.py.

Subcommands
-----------
  snapshot           hash + copy the key validator-input artifacts into
                     artifacts/verify_parser_change/baseline_<UTCstamp>/ + manifest.json
  diff [--baseline]  compare current artifacts vs latest (or given) baseline → blast radius
  validate           run every validator, capture exit code + summary line → combined table
  all (default)      no baseline yet → snapshot; else → diff vs latest baseline + validate

Examples
--------
  # before a parser change:
  python scripts/verify_parser_change.py snapshot
  # ... make the parser/extractor change, rebuild masters as usual ...
  # after:
  python scripts/verify_parser_change.py diff        # blast radius
  python scripts/verify_parser_change.py validate    # RED/YELLOW re-run
  python scripts/verify_parser_change.py all         # diff + validate in one shot

stdlib only. UTF-8 stdout (Windows console defaults to cp949).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows console defaults to cp949
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
SNAP_DIR = ROOT / "artifacts" / "verify_parser_change"
# Use this interpreter (the venv python the harness was launched with) for validators.
PYTHON = sys.executable

# ---------------------------------------------------------------------------
# Artifact inventory — every data file the validators read.
# diff_mode: "cells" = kics_disclosure cell-keyed list; "structural" = generic value diff.
# ---------------------------------------------------------------------------
ARTIFACTS = [
    {"path": "kics_disclosure.json", "diff_mode": "cells",
     "readers": ["validate_kics_disclosure.py", "validate_kics_rate_sensitivity.py"]},
    {"path": "kics_rate_sensitivity.json", "diff_mode": "structural",
     "readers": ["validate_kics_rate_sensitivity.py"]},
    {"path": "CSM_waterfall.json", "diff_mode": "structural",
     "readers": ["validate_master_tables.py", "validate_csm_continuity.py"]},
    {"path": "data/dart/viz/pl_breakdown_master.json", "diff_mode": "structural",
     "readers": ["validate_master_tables.py"]},
    {"path": "data/dart/viz/sensitivity_heatmap.json", "diff_mode": "structural",
     "readers": ["validate_master_tables.py"]},
    {"path": "data/dart/viz/csm_waterfall.json", "diff_mode": "structural",
     "readers": ["validate_nb_csm_multiple.py", "build_root_masters.py"]},
    {"path": "data/dart/viz/csm_waterfall_history.json", "diff_mode": "structural",
     "readers": ["check_nb_csm_history.py"]},
    {"path": "data/ir/nb_csm_ratio.json", "diff_mode": "structural",
     "readers": ["validate_nb_csm_multiple.py"]},
    {"path": "data/_derived/nb_premium_wolnap.json", "diff_mode": "structural",
     "readers": ["validate_nb_csm_multiple.py"]},
    {"path": "data/ir/meritz/extracted_202603.json", "diff_mode": "structural",
     "readers": ["validate_nb_csm_multiple.py"]},
    # IR series dir (NB CSM history + multiple). Snapshot each *.json individually.
    {"path": "data/ir/series", "diff_mode": "dir", "glob": "*.json",
     "readers": ["check_nb_csm_history.py"]},
]

# ---------------------------------------------------------------------------
# Validator registry — CLI, the input file(s) each reads, and exit-code meaning.
# (read-only; this harness shells out to each unchanged.)
# ---------------------------------------------------------------------------
VALIDATORS = [
    {"name": "validate_kics_disclosure.py",
     "cmd": ["scripts/validate_kics_disclosure.py"],
     "inputs": ["kics_disclosure.json"],
     "exit": "0 if RED=0 & census_red=0 & no parent-zero/child; else 2"},
    {"name": "validate_kics_rate_sensitivity.py",
     "cmd": ["scripts/validate_kics_rate_sensitivity.py"],
     "inputs": ["kics_rate_sensitivity.json", "kics_disclosure.json"],
     "exit": "0 if RS1+RS2 RED=0 (RS2 exceptions excluded); else 2"},
    {"name": "validate_master_tables.py",
     "cmd": ["scripts/validate_master_tables.py", "--no-build"],
     "inputs": ["CSM_waterfall.json", "data/dart/viz/pl_breakdown_master.json",
                "data/dart/viz/sensitivity_heatmap.json"],
     "exit": "0 if no closing/pl_bridge/crosscheck fail & no hole/dup/spike/cont/"
             "wfy/zamort/zleg/impossible0/sens_red; else 2 "
             "(--no-build: skip build_root_masters; YELLOW/QoQ do not affect exit)"},
    {"name": "validate_csm_continuity.py",
     "cmd": ["scripts/validate_csm_continuity.py"],
     "inputs": ["CSM_waterfall.json"],
     "exit": "0 if no within-FY-opening-drift & no FY-boundary-discontinuity; else 2"},
    {"name": "check_nb_csm_history.py",
     "cmd": ["scripts/check_nb_csm_history.py"],
     "inputs": ["data/dart/viz/csm_waterfall_history.json", "data/ir/series/*.json"],
     "exit": "0 if OVER+UNDER=0; else 2"},
    {"name": "validate_nb_csm_multiple.py",
     "cmd": ["scripts/validate_nb_csm_multiple.py"],
     "inputs": ["data/dart/viz/csm_waterfall.json", "data/_derived/nb_premium_wolnap.json",
                "data/ir/nb_csm_ratio.json", "data/ir/meritz/extracted_202603.json"],
     "exit": "1 if any cohort member fails after reconcile; else 0 (YELLOW reconcile only)"},
]

CELL_CAP = 50  # max cells printed per diff section


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _utcstamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_name(rel: str) -> str:
    """Flatten a repo-relative path into a single snapshot filename component."""
    return rel.replace("/", "__").replace("\\", "__")


def _expand_artifacts() -> list[dict]:
    """Resolve ARTIFACTS entries to concrete files. A 'dir' entry expands to its glob."""
    out: list[dict] = []
    for a in ARTIFACTS:
        src = ROOT / a["path"]
        if a.get("diff_mode") == "dir":
            if not src.is_dir():
                continue
            for f in sorted(src.glob(a.get("glob", "*"))):
                rel = f.relative_to(ROOT).as_posix()
                out.append({"path": rel, "diff_mode": "structural", "_abs": f,
                            "readers": a.get("readers", [])})
        else:
            out.append({"path": a["path"], "diff_mode": a.get("diff_mode", "structural"),
                        "_abs": src, "readers": a.get("readers", [])})
    return out


def _latest_baseline() -> Path | None:
    if not SNAP_DIR.is_dir():
        return None
    cands = sorted(d for d in SNAP_DIR.glob("baseline_*") if d.is_dir())
    return cands[-1] if cands else None


def _load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# snapshot
# ---------------------------------------------------------------------------
def cmd_snapshot(_args) -> int:
    stamp = _utcstamp()
    dest = SNAP_DIR / f"baseline_{stamp}"
    dest.mkdir(parents=True, exist_ok=True)
    manifest = {"created_at": stamp, "root": str(ROOT), "files": []}
    present = missing = 0
    for a in _expand_artifacts():
        abs_p = a["_abs"]
        rel = a["path"]
        entry = {"path": rel, "diff_mode": a["diff_mode"], "readers": a.get("readers", [])}
        if abs_p.is_file():
            digest = _sha256(abs_p)
            stored = _safe_name(rel)
            shutil.copy2(abs_p, dest / stored)
            entry.update({"present": True, "sha256": digest,
                          "size": abs_p.stat().st_size, "stored_as": stored})
            present += 1
        else:
            entry.update({"present": False, "sha256": None, "size": None, "stored_as": None})
            missing += 1
        manifest["files"].append(entry)
    (dest / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[snapshot] baseline written: {dest}")
    print(f"[snapshot] artifacts captured: present={present} missing={missing} "
          f"(total {present + missing})")
    for e in manifest["files"]:
        flag = "ok " if e["present"] else "MISS"
        sz = f"{e['size']:>10,}B" if e["present"] else " (absent)  "
        print(f"    [{flag}] {sz}  {e['path']}")
    return 0


# ---------------------------------------------------------------------------
# diff — blast radius
# ---------------------------------------------------------------------------
def _kics_cell_index(records: list) -> dict:
    """kics_disclosure.json list → {(code, quarter, item): value}. Last write wins
    (matches gate/validator semantics which index the same way)."""
    idx: dict = {}
    for r in records:
        if not isinstance(r, dict):
            continue
        c = r.get("원보험사코드")
        q = r.get("공시분기")
        it = r.get("항목번호")
        if c is None or q is None or it is None:
            continue
        idx[(c, q, it)] = r.get("값")
    return idx


def _diff_cells(old_p: Path, new_p: Path) -> dict:
    old_idx = _kics_cell_index(_load_json(old_p)) if old_p.is_file() else {}
    new_idx = _kics_cell_index(_load_json(new_p)) if new_p.is_file() else {}
    old_keys, new_keys = set(old_idx), set(new_idx)
    added = sorted(new_keys - old_keys)
    removed = sorted(old_keys - new_keys)
    changed = []
    for k in sorted(old_keys & new_keys):
        if old_idx[k] != new_idx[k]:
            changed.append((k, old_idx[k], new_idx[k]))
    return {"added": added, "removed": removed, "changed": changed,
            "old_idx": old_idx, "new_idx": new_idx}


def _print_cells(name: str, d: dict) -> bool:
    n_add, n_rem, n_chg = len(d["added"]), len(d["removed"]), len(d["changed"])
    total = n_add + n_rem + n_chg
    if total == 0:
        print(f"  [=] {name}: 0 cell changes "
              f"(old {len(d['old_idx'])} cells, new {len(d['new_idx'])} cells)")
        return False
    print(f"  [~] {name}: {total} cell changes "
          f"(added {n_add} / removed {n_rem} / changed {n_chg})  "
          f"[old {len(d['old_idx'])} → new {len(d['new_idx'])} cells]")
    shown = 0
    for (c, q, it), ov, nv in d["changed"]:
        if shown >= CELL_CAP:
            break
        print(f"        chg  {c} {q} item{it}: {ov!r} → {nv!r}")
        shown += 1
    for (c, q, it) in d["added"]:
        if shown >= CELL_CAP:
            break
        print(f"        add  {c} {q} item{it}: {d['new_idx'][(c, q, it)]!r}")
        shown += 1
    for (c, q, it) in d["removed"]:
        if shown >= CELL_CAP:
            break
        print(f"        del  {c} {q} item{it}: (was {d['old_idx'][(c, q, it)]!r})")
        shown += 1
    if total > CELL_CAP:
        print(f"        ... +{total - shown} more cell changes (capped at {CELL_CAP})")
    return True


def _flatten(obj, prefix="") -> dict:
    """Flatten nested JSON to {dotted.path: scalar}. Lists indexed by position."""
    out: dict = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(_flatten(v, f"{prefix}.{k}" if prefix else str(k)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.update(_flatten(v, f"{prefix}[{i}]"))
    else:
        out[prefix] = obj
    return out


def _diff_structural(old_p: Path, new_p: Path) -> dict:
    old = _flatten(_load_json(old_p)) if old_p.is_file() else {}
    new = _flatten(_load_json(new_p)) if new_p.is_file() else {}
    ok, nk = set(old), set(new)
    added = sorted(nk - ok)
    removed = sorted(ok - nk)
    changed = [(k, old[k], new[k]) for k in sorted(ok & nk) if old[k] != new[k]]
    return {"added": added, "removed": removed, "changed": changed,
            "n_old": len(old), "n_new": len(new)}


def _print_structural(name: str, d: dict) -> bool:
    n_add, n_rem, n_chg = len(d["added"]), len(d["removed"]), len(d["changed"])
    total = n_add + n_rem + n_chg
    if total == 0:
        print(f"  [=] {name}: 0 leaf changes ({d['n_old']} → {d['n_new']} leaves)")
        return False
    print(f"  [~] {name}: {total} leaf changes "
          f"(added {n_add} / removed {n_rem} / changed {n_chg})  "
          f"[{d['n_old']} → {d['n_new']} leaves]")
    shown = 0
    for k, ov, nv in d["changed"]:
        if shown >= CELL_CAP:
            break
        print(f"        chg  {k}: {ov!r} → {nv!r}")
        shown += 1
    for k in d["added"]:
        if shown >= CELL_CAP:
            break
        print(f"        add  {k}")
        shown += 1
    for k in d["removed"]:
        if shown >= CELL_CAP:
            break
        print(f"        del  {k}")
        shown += 1
    if total > CELL_CAP:
        print(f"        ... +{total - shown} more leaf changes (capped at {CELL_CAP})")
    return True


def cmd_diff(args) -> int:
    baseline = Path(args.baseline).resolve() if args.baseline else _latest_baseline()
    if baseline is None or not baseline.is_dir():
        print("[diff] no baseline found — run `snapshot` first "
              f"(looked under {SNAP_DIR}).")
        return 2
    man_p = baseline / "manifest.json"
    if not man_p.is_file():
        print(f"[diff] baseline manifest missing: {man_p}")
        return 2
    manifest = _load_json(man_p)
    print(f"[diff] baseline: {baseline}  (created {manifest.get('created_at')})")
    print(f"[diff] comparing current working-tree artifacts vs baseline copies")
    print("-" * 78)

    any_change = False
    n_files = len(manifest["files"])
    appeared = vanished = 0
    for e in manifest["files"]:
        rel = e["path"]
        new_p = ROOT / rel
        stored = e.get("stored_as") or _safe_name(rel)
        old_p = baseline / stored
        was_present = e.get("present", False)
        now_present = new_p.is_file()

        if not was_present and not now_present:
            continue
        if not was_present and now_present:
            print(f"  [+] {rel}: NEW (absent in baseline, present now)")
            appeared += 1
            any_change = True
            continue
        if was_present and not now_present:
            print(f"  [-] {rel}: REMOVED (present in baseline, absent now)")
            vanished += 1
            any_change = True
            continue

        # both present — fast path: identical hash → skip parse
        if _sha256(new_p) == e.get("sha256"):
            print(f"  [=] {rel}: unchanged (identical sha256)")
            continue

        if e.get("diff_mode") == "cells":
            d = _diff_cells(old_p, new_p)
            changed = _print_cells(rel, d)
        else:
            d = _diff_structural(old_p, new_p)
            changed = _print_structural(rel, d)
        any_change = any_change or changed

    print("-" * 78)
    print(f"[diff] files compared: {n_files}  | appeared: {appeared}  vanished: {vanished}")
    print(f"[diff] RESULT: {'CHANGES DETECTED' if any_change else 'NO CHANGES (clean)'}")
    return 0


# ---------------------------------------------------------------------------
# validate — run every validator, capture exit + summary line
# ---------------------------------------------------------------------------
def _summary_line(name: str, stdout: str) -> str:
    """Pull the most informative one-line summary from each validator's stdout."""
    lines = [l.rstrip() for l in stdout.splitlines() if l.strip()]
    if not lines:
        return "(no stdout)"
    # validator-specific anchors
    if name == "validate_kics_disclosure.py":
        for l in lines:
            if l.startswith("Status counts:"):
                return l
    if name == "validate_kics_rate_sensitivity.py":
        for l in lines:
            if l.startswith("SUMMARY "):
                return l
    if name == "validate_master_tables.py":
        for l in reversed(lines):
            if l.startswith("SUMMARY "):
                return l
    if name == "validate_csm_continuity.py":
        for l in lines:
            if l.startswith("[csm_continuity]"):
                return l
    if name == "check_nb_csm_history.py":
        for l in lines:
            if l.startswith("cohort="):
                return l
    if name == "validate_nb_csm_multiple.py":
        for l in lines:
            if l.strip().startswith("tested="):
                return l.strip()
    return lines[-1]


def cmd_validate(_args) -> int:
    print(f"[validate] running {len(VALIDATORS)} validators with {PYTHON}")
    print("=" * 78)
    rows = []
    worst = 0
    for v in VALIDATORS:
        cmd = [PYTHON] + [str(ROOT / c) if c.endswith(".py") else c for c in v["cmd"]]
        try:
            r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
            rc = r.returncode
            summary = _summary_line(v["name"], r.stdout or "")
            if rc not in (0,) and not summary.strip():
                tail = (r.stderr or "").strip().splitlines()[-1:] or ["(no stderr)"]
                summary = "ERR: " + tail[0][:120]
        except Exception as exc:  # harness must not crash on one validator
            rc = -1
            summary = f"HARNESS-ERROR: {exc!s}"[:160]
        rows.append((v["name"], rc, summary))
        worst = max(worst, abs(rc))

    print(f"{'validator':38s} {'exit':>4s}  summary")
    print("-" * 78)
    for name, rc, summary in rows:
        print(f"{name:38s} {rc:>4d}  {summary}")
    print("=" * 78)
    fails = [n for n, rc, _ in rows if rc != 0]
    if fails:
        print(f"[validate] {len(fails)}/{len(rows)} validators non-zero: {', '.join(fails)}")
    else:
        print(f"[validate] all {len(rows)} validators exit 0 (clean)")
    # exit 2 if any validator reported a failure (RED/data-error), else 0.
    return 2 if fails else 0


# ---------------------------------------------------------------------------
# all (default)
# ---------------------------------------------------------------------------
def cmd_all(args) -> int:
    if _latest_baseline() is None:
        print("[all] no baseline exists → taking snapshot (run a change, then "
              "`diff` + `validate`, or `all` again).")
        print("-" * 78)
        return cmd_snapshot(args)
    print("[all] baseline exists → diff vs latest baseline, then validate.")
    print("=" * 78)
    rc_diff = cmd_diff(args)
    print()
    rc_val = cmd_validate(args)
    return max(abs(rc_diff), abs(rc_val))


# ---------------------------------------------------------------------------
# cli
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(
        description="Blast-radius diff + validator re-run around a parser/extractor change.")
    sub = ap.add_subparsers(dest="command")

    sub.add_parser("snapshot", help="hash+copy validator-input artifacts into a baseline")

    p_diff = sub.add_parser("diff", help="diff current artifacts vs a baseline (blast radius)")
    p_diff.add_argument("--baseline", help="baseline dir (default: latest under "
                        "artifacts/verify_parser_change/)")

    sub.add_parser("validate", help="run every validator, print combined exit/summary table")

    p_all = sub.add_parser("all", help="snapshot if none exists, else diff+validate")
    p_all.add_argument("--baseline", help="baseline dir for the diff step")

    args = ap.parse_args()
    cmd = args.command or "all"
    if cmd in ("all", "diff") and not hasattr(args, "baseline"):
        args.baseline = None

    if cmd == "snapshot":
        return cmd_snapshot(args)
    if cmd == "diff":
        return cmd_diff(args)
    if cmd == "validate":
        return cmd_validate(args)
    return cmd_all(args)


if __name__ == "__main__":
    raise SystemExit(main())
