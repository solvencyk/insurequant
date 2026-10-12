"""harness.py -- candidate builder + gate runner for the READ-ONLY latest-prior-column dry run.

A candidate master = LIVE master + the block-overlay plan (in memory), written under _tmp/ (never to the repo master).
The REAL gate (scripts/validate_kics_disclosure.py --master <candidate>) is run in a subprocess, one at a time.
The gate writes artifacts/kics_validation/report_<ts>.json + report_latest.json (gitignored); this harness copies what it needs and
deletes the new report files, and `restore_latest_pointer()` puts report_latest.json back at the end.
"""
import copy
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_precedence_dryrun_20261012")
from lib_dry import *  # noqa: F401,F403

ARTIFACTS = REPO / "artifacts" / "kics_validation"
LATEST = ARTIFACTS / "report_latest.json"

# report sections whose entries are RED-grade signals other than the rule-engine findings
EXTRA_RED_PATHS = [
    ("transition_mmult_after", "mismatch_red"), ("transition_identities_after", "red"), ("transition_irr_after", "red"),
    ("other_capital_children_sum", "red"), ("identity_tautology", "red"), ("identity_tautology", "spec_drift_red"),
    ("parent_present_child_incomplete", "partial_red"), ("parent_present_child_incomplete_after", None),
    ("parent_zero_child_nonzero", None), ("transition_ratio_after_capture", None), ("item12_equals_item1", None),
    ("ratio_series_spikes", None), ("diversification_negative", None), ("post_transition_parent_census", "red"),
    ("market_tooling_fail", None), ("axis_evaluation_census", "not_evaluated_red"), ("sidecar_coverage", "red"),
]
# exemption-machinery signals (pin drift, ledger disagreement, inert registration) -- NOT rule failures; reported as "registry action"
REGISTRY_RED_PATHS = [
    ("tier2_issuer_inconsistent_exception", "red"), ("ident_issuer_inconsistent_exception", "red"),
    ("life8_issuer_inconsistent_exception", "red"), ("exemption_provenance", "red"),
    ("restatement_cascade_exception", "residual_drift_red"), ("irr_derive_issuer_inconsistent_exception", "review"),
    ("tier2_issuer_inconsistent_exception", "review"), ("ident_issuer_inconsistent_exception", "review"),
    ("life8_issuer_inconsistent_exception", "review"),
]


def backup_latest_pointer():
    if LATEST.exists():
        return LATEST.read_bytes()
    return None


def restore_latest_pointer(blob):
    if blob is not None:
        LATEST.write_bytes(blob)


def fkey(f):
    return (f["원보험사코드"], f["공시분기"], str(f["rule"]))


def slim_report(rep: dict) -> dict:
    """Keep what the verdict logic needs (findings + RED-grade extra-axis lists + registry signals)."""
    s = {"findings": {"|".join(fkey(f)): [f["status"], f.get("expected"), f.get("actual"), f.get("diff")] for f in rep["findings"]}}
    s["summary"] = rep["summary"]["by_status"]
    ex = {}
    for sec, sub in EXTRA_RED_PATHS:
        v = rep.get(sec)
        if v is None:
            continue
        if sub:
            v = v.get(sub)
        if v:
            ex[f"{sec}.{sub}" if sub else sec] = v
    s["extra_red"] = ex
    rg = {}
    for sec, sub in REGISTRY_RED_PATHS:
        v = rep.get(sec)
        if v is None:
            continue
        v = v.get(sub) if sub else v
        if v:
            rg[f"{sec}.{sub}"] = v
    s["registry_red"] = rg
    cen = rep.get("coverage_census", {})
    s["census_blocking_missing"] = cen.get("blocking_missing_count")
    return s


def run_gate(master_path: Path, tag: str, timeout=900):
    """Run the real gate on master_path.  Returns (slim_report, stdout_lines_of_interest, returncode, seconds)."""
    before = set(ARTIFACTS.glob("*"))
    t0 = time.time()
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    proc = subprocess.Popen([PY, "scripts/validate_kics_disclosure.py", "--master", str(master_path)], cwd=str(REPO),
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        raise RuntimeError(f"gate for {tag} exceeded {timeout}s and was killed")
    text = out.decode("utf-8", errors="replace")
    first = text.splitlines()[0] if text else ""
    rp = first.split("report:", 1)[1].strip() if "report:" in first else None
    if not rp or not Path(rp).exists():
        raise RuntimeError(f"no report path for {tag}: {first!r} | {err.decode('utf-8', errors='replace')[-400:]}")
    rep = json.loads(Path(rp).read_text(encoding="utf-8"))
    slim = slim_report(rep)
    keep = [ln.strip()[:300] for ln in text.splitlines() if ln.startswith("Status counts") or "blocking RED" in ln]
    # delete ONLY the timestamped report this very run printed (other sessions may run the gate concurrently); the
    # report_latest.json pointer is refreshed by one real live-master gate run at the very end of the whole job
    try:
        Path(rp).unlink()
    except OSError:
        pass
    return slim, keep, proc.returncode, round(time.time() - t0, 1)


# ------------------------------------------------------------------ candidate building
def fmt_ratio(x):
    s = f"{x:.8f}".rstrip("0").rstrip(".")
    return s or "0"


def apply_plan(rows, plan, recompute_derived=True):
    """-> (candidate rows (deep copy), n_cell_edits, derived_edits[list])"""
    cand = copy.deepcopy(rows)
    idx = {}
    for i, r in enumerate(cand):
        idx[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = i
    n = 0
    touched = set()
    for e in plan["edits"]:
        k = (e["code"], e["q"], e["item"])
        if k not in idx:
            raise RuntimeError(f"edit target row missing: {k}")
        r = cand[idx[k]]
        cur = r.get(e["field"], "<nokey>")
        if cur != e["old"]:
            raise RuntimeError(f"GUARD FAIL {k} {e['field']}: current {cur!r} != planned old {e['old']!r}")
        r[e["field"]] = e["new"]
        touched.add((e["code"], e["q"]))
        n += 1
    derived = []
    if recompute_derived and plan["edits"]:
        for (code, q) in touched:
            def g(src, it, fld):
                j = idx.get((code, q, it))
                return num(src[j].get(fld)) if j is not None else None

            def put(it, fld, newv, why):
                j = idx.get((code, q, it))
                if j is None:
                    return
                old = cand[j].get(fld)
                if old != newv:
                    cand[j][fld] = newv
                    derived.append({"code": code, "q": q, "item": it, "field": fld, "old": old, "new": newv, "why": why})

            def ratio_inputs(src):
                i1, i2, i14 = g(src, 1, "값"), g(src, 2, "값"), g(src, 14, "값")
                p1, p2, p14 = g(src, 1, "값_적용후"), g(src, 2, "값_적용후"), g(src, 14, "값_적용후")
                p1 = i1 if p1 is None else p1
                p2 = i2 if p2 is None else p2
                den = p14 if p14 not in (None, 0) else i14
                return {"27": (i1, i14), "28": (i2, i14), "28p": (p2, den), "27p": (p1, den)}

            old_in, new_in = ratio_inputs(rows), ratio_inputs(cand)
            # a derived cell is recomputed ONLY when the master's current value is itself the derived value of the OLD inputs
            # (printed ratios such as 286.5 stay as printed)
            for tag, item, fld in (("27", 27, "값"), ("28", 28, "값"), ("28p", 28, "값_적용후"), ("27p", 27, "값_적용후")):
                (on, od), (nn, nd) = old_in[tag], new_in[tag]
                if None in (on, od, nn, nd) or not od or not nd or (on, od) == (nn, nd):
                    continue
                j = idx.get((code, q, item))
                if j is None:
                    continue
                have = num(rows[j].get(fld))
                if have is not None and abs(have - on / od * 100.0) < 0.011:
                    put(item, fld, fmt_ratio(nn / nd * 100.0), f"{tag} recomputed from the overlaid inputs")
    return cand, n, derived


# ------------------------------------------------------------------ signature comparison
def red_set(slim, code=None, quarter=None):
    out = {}
    for k, v in slim["findings"].items():
        c, q, rule = k.split("|", 2)
        if v[0] == "RED" and (code is None or c == code) and (quarter is None or q == quarter):
            out[k] = v
    return out


def entries_str(lst):
    return {json.dumps(x, ensure_ascii=False, sort_keys=True, default=str) for x in (lst if isinstance(lst, list) else [lst])}


def diff_extra(base, cand, section_key="extra_red"):
    """entries present in cand but not in base, per section"""
    new, gone = {}, {}
    keys = set(base[section_key]) | set(cand[section_key])
    for k in keys:
        b = entries_str(base[section_key].get(k, []))
        c = entries_str(cand[section_key].get(k, []))
        if c - b:
            new[k] = sorted(c - b)
        if b - c:
            gone[k] = sorted(b - c)
    return new, gone


def finding_changes(base, cand, only_buckets=None):
    """-> list of (key, base_tuple or None, cand_tuple or None) for findings whose status/diff changed."""
    out = []
    for k in set(base["findings"]) | set(cand["findings"]):
        b, c = base["findings"].get(k), cand["findings"].get(k)
        if b != c:
            cq = tuple(k.split("|", 2)[:2])
            if only_buckets is None or cq in only_buckets:
                # ignore pure float noise
                if b and c and b[0] == c[0] and all((x == y) or (isinstance(x, (int, float)) and isinstance(y, (int, float)) and abs(x - y) < 1e-6)
                                                   for x, y in zip(b[1:], c[1:])):
                    continue
                out.append((k, b, c))
    return sorted(out)
