#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cell-level applier for ticket 20261021T1310Z (parser/ifrs17): KR0073 (Kyobo Life) CSM waterfall basis/vintage fix.

Scenarios
  E5  2026.1Q items 2-6 = SEPARATE-basis sum of the three sub-tables (유배당+무배당+변액); item 1 stays 65109.6; item 4 = residual.
      + release of the now-closed csm_amort_identity_ledger pin (교보생명보험|2026.1Q) + provenance owner_override flags for 2023.1Q/2Q.
      This is what was APPLIED on 2026-10-21 (gate dry-run: no new RED apart from MASTER_XLSX_DRIFT until publishing syncs the xlsx).
  R   E5 + the restated-vintage separate-basis blocks for 2023.1Q-2024.2Q (latest-filing prior-period columns).  NOT applied:
      it breaks CSM_AMORT_IDENTITY (PL item 4 '원수 CSM상각' is still the original vintage) for 2023.1Q/3Q/4Q and 2024.1Q/2Q
      unless the owner approves 5 RESTATEMENT_BASIS ledger pins (--with-amort-pins) or the PL block is restated first.

Writes (only these, each guarded and backed up):  CSM_waterfall.json (KR0073 cells: 값 + derived 값_당분기), data/_gold/user_csm_cells.json,
  data/_gold/gold_overlay_ledger.json (pins), data/_gold/csm_amort_identity_ledger.json, CSM_waterfall_provenance.json,
  tests/test_rule_coverage_manifest.py (GOLD_OVERLAY_CENSUS declaration, only when the census changes).
The master cells are produced by running the REAL builder logic (scripts/build_root_masters.py::build_csm) against the candidate gold in a temp
copy, so the written master is exactly what a later build reproduces (--verify proves it for ALL rows).  No builder / main() writes the repo.

  python apply_kr0073_fix.py --scenario E5 --check                 read-only plan + post-condition checks
  python apply_kr0073_fix.py --scenario E5 --out-dir DIR           write the post-apply files under DIR (repo untouched; for gate overlay runs)
  python apply_kr0073_fix.py --scenario E5 --apply                 write the repo files (backups in backup_before_apply_<scenario>/)
  python apply_kr0073_fix.py --scenario E5 --revert --apply        restore the backups (only if live files still have the post-apply hashes)
  python apply_kr0073_fix.py --verify                              read-only: a fresh builder run from the LIVE gold == the LIVE master (all rows)
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
EV = ROOT / "data" / "_derived" / "kyobo_csm_basis_fix_20261021"
CODE = "KR0073"
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

F = {
    "CSM": "CSM_waterfall.json",
    "GOLD": "data/_gold/user_csm_cells.json",
    "PIN": "data/_gold/gold_overlay_ledger.json",
    "AMORT": "data/_gold/csm_amort_identity_ledger.json",
    "PROV": "CSM_waterfall_provenance.json",
}
TEST_REL = "tests/test_rule_coverage_manifest.py"
DIAG_REL = "data/dart/viz/csm_waterfall_master_diag.json"
AMORT_KEY_2026_1Q = "교보생명보험|2026.1Q"

# ---- raw-verified vectors (억원, 별도 기준, CSM 소계열, 당기 누계 블록); see csm_vectors_raw.txt for the raw line citations ----
E5_SPEC_ID = "2026.1Q@FY2026_Q1sep_cur_3blk"
R_SPEC_IDS = {
    "2023.1Q": "2023.1Q@FY2024_Q1prior", "2023.2Q": "2023.2Q@FY2024_Q2prior", "2023.3Q": "2023.3Q@FY2024_Q3prior",
    "2023.4Q": "2023.4Q@FY2024_Q4prior", "2024.1Q": "2024.1Q@FY2025_Q1prior", "2024.2Q": "2024.2Q@FY2025_Q2prior",
}
E5_EXPECT = [65109.6, 4159.16, 487.2, -1349.13, -1537.33, 66869.5]
R_EXPECT = {
    "2023.1Q": [55337.66, 3652.77, 7223.17, -6179.53, -1052.55, 58981.52],
    "2023.2Q": [55337.66, 6597.27, 7495.04, -6428.69, -2120.34, 60880.94],
    "2023.3Q": [54377.63, 10255.1, 4298.52, -2011.29, -4643.21, 62276.75],
    "2023.4Q": [54377.63, 13728.88, 14526.0, -18106.27, -6277.01, 58249.23],
    "2024.1Q": [58249.23, 3933.86, 840.31, -2603.32, -1560.15, 58859.93],
    "2024.2Q": [58249.23, 7046.45, 3950.99, -8518.48, -3039.95, 57688.24],
}
# PL(원수 CSM상각) values currently in PL_breakdown.json for the quarters where R would break CSM_AMORT_IDENTITY (억원) -> proposed pins
AMORT_PIN_NOTE = ("R-scenario companion (owner approval required): the CSM waterfall carries the latest-filing (restated) CSM amortization while PL_breakdown item 4 "
                  "'원수 CSM상각' still holds the original-vintage value; release this line when the PL block of this quarter is restated "
                  "(ticket 20261021T1310Z, data/_derived/kyobo_csm_basis_fix_20261021/)")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class JsonFile:
    """exact-format JSON file: detects (indent, newline) by byte round-trip; refuses files that do not round-trip."""

    def __init__(self, rel: str):
        self.rel = rel
        self.path = ROOT / rel
        self.raw = self.path.read_bytes()
        self.obj = json.loads(self.raw.decode("utf-8"))
        self.fmt = None
        for indent in (2, 1, 4):
            for nl in ("\n", "\r\n"):
                if self._dump(self.obj, indent, nl) == self.raw:
                    self.fmt = (indent, nl)
                    break
            if self.fmt:
                break
        if self.fmt is None:
            raise SystemExit(f"ABORT: {rel} does not round-trip byte-exactly (indent 1/2/4, LF/CRLF) -- refusing to rewrite")
        self.sha0 = sha(self.raw)

    @staticmethod
    def _dump(obj, indent, nl):
        s = json.dumps(obj, ensure_ascii=False, indent=indent)
        return (s.replace("\n", "\r\n") if nl == "\r\n" else s).encode("utf-8")

    def dumps(self):
        return self._dump(self.obj, *self.fmt)


def write_atomic(path: Path, data: bytes, tries: int = 8):
    path.parent.mkdir(parents=True, exist_ok=True)
    last = None
    for i in range(tries):
        tmp = path.with_name(path.name + ".tmp_apply")
        try:
            tmp.write_bytes(data)
            os.replace(tmp, path)
            return
        except OSError as e:
            last = e
            time.sleep(0.75 * (i + 1))
    raise SystemExit(f"ABORT: could not write {path}: {last!r}")


def qkey(q):
    return (int(q[:4]), int(q[5]))


def load_vectors():
    vec = json.loads((EV / "csm_vectors_raw.json").read_text(encoding="utf-8"))
    return vec


def e5_vector(vec):
    v = vec[E5_SPEC_ID]["vec_eok"]
    out = [E5_EXPECT[0], v[1], v[2], None, v[4], v[5]]
    out[3] = round(out[5] - out[0] - out[1] - out[2] - out[4], 2)
    assert out == E5_EXPECT, f"E5 vector drifted from the audited literal: {out} != {E5_EXPECT}"
    return out


def r_vectors(vec):
    out = {q: vec[sid]["vec_eok"] for q, sid in R_SPEC_IDS.items()}
    assert out == R_EXPECT, f"R vectors drifted from the audited literals: {out} != {R_EXPECT}"
    return out


def load_brm():
    spec = importlib.util.spec_from_file_location("brm_apply", str(ROOT / "scripts" / "build_root_masters.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def simulate_build(gold_obj, master_raw: bytes, tag: str):
    """REAL build_csm() against a candidate gold + a temp copy of the master; returns the resulting row list. Repo untouched."""
    tmpdir = EV / "tmp"
    tmpdir.mkdir(exist_ok=True)
    gp, mp = tmpdir / f"gold_{tag}.json", tmpdir / f"master_{tag}.json"
    gp.write_text(json.dumps(gold_obj, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    mp.write_bytes(master_raw)
    brm = load_brm()
    brm.CSM_OVR, brm.CSM_OUT = gp, mp
    brm.build_csm()
    rows = json.loads(mp.read_text(encoding="utf-8"))
    for p in (gp, mp):
        try:
            p.unlink()
        except OSError:
            pass
    return rows


def rkey(r):
    return (r["원보험사코드"], r["항목번호"], r["공시분기"])


def gold_idx(gold):
    return {(e["원보험사코드"], e["항목번호"], e["공시분기"]): i for i, e in enumerate(gold["set"])}


def build_gold(live_gold, scenario, vec, with_log):
    """returns (new_gold, edits[list of dict]) -- edits: {key, old, new, op}."""
    g = copy.deepcopy(live_gold)
    idx = gold_idx(g)
    edits = []
    e5 = e5_vector(vec)
    why_e5 = ("2026-10-21 parser/ifrs17 ticket 20261021T1310Z E5: 2026.1Q items 2-6 = SEPARATE-basis (별도) sum of the three 17-4 sub-tables 유배당+무배당+변액 "
              "(FY2026_Q1 20260813001077.xml 별도 당분기 L43617/L43934/L44251; CSM 소계열 L43738+L44055+L44372 등), item 1 stays 65109.6 (= master 2025.4Q close), "
              "item 4 = residual (= printed 추정치 변동 -1,349.13 = 19,911-113,208-41,616 mn). The previous values were the CONSOLIDATED sums "
              "(L20779+L21095+L21411 ...) mixed under a separate-basis opening")
    why_r = ("2026-10-21 parser/ifrs17 ticket 20261021T1310Z E1-E4: restated-vintage SEPARATE-basis block = latest filing prior-period column "
             "(FY2024 Q1/Q2/Q3/annual prior tables for 2023.x; FY2025 Q1/Q2 prior tables for 2024.1Q/2Q); raw lines in data/_derived/kyobo_csm_basis_fix_20261021/csm_vectors_raw.txt; "
             "item 4 = residual (= printed 추정치 변동)")

    def upd(q, item, val, why):
        k = (CODE, item, q)
        if k in idx:
            e = g["set"][idx[k]]
            old = e["값"]
            if old == val:          # already at the target value (e.g. E5 cells when R is layered on the applied E5 state)
                return
            e["값"] = val
            e["why"] = f"{why} | prior gold value {old}"
            e.pop("note", None)
            edits.append({"key": k, "old": old, "new": val, "op": "update"})
        else:
            g["set"].append({"원보험사코드": CODE, "항목번호": item, "공시분기": q, "값": val, "why": why})
            idx[k] = len(g["set"]) - 1
            edits.append({"key": k, "old": None, "new": val, "op": "add"})

    # item 1 of 2026.1Q is not edited (value unchanged) -- items 2..6 only
    for item in range(2, 7):
        upd("2026.1Q", item, e5[item - 1], why_e5)
    if scenario == "R":
        rv = r_vectors(vec)
        for q, v in rv.items():
            for item, val in enumerate(v, start=1):
                upd(q, item, val, why_r)
    return g, edits


def pins_for(new_gold, live_pin, diag_by):
    """re-derive the KR0073 CSM pins: drop pins of cells that are no longer masked, add pins for masked unpinned cells."""
    out = copy.deepcopy(live_pin)
    gidx = gold_idx(new_gold)
    removed, added = [], []
    for k in list(out["entries"]):
        p = k.split("|")
        if p[0] != "CSM" or p[1] != CODE:
            continue
        g = new_gold["set"][gidx[(CODE, int(p[3]), p[2])]]["값"] if (CODE, int(p[3]), p[2]) in gidx else None
        s = diag_by.get((CODE, int(p[3]), p[2]))
        if not (g is not None and s is not None and round(abs(g - s), 9) <= 0.05):
            del out["entries"][k]
            removed.append(k)
    for e in new_gold["set"]:
        if e["원보험사코드"] != CODE:
            continue
        k = (CODE, e["항목번호"], e["공시분기"])
        key = f"CSM|{CODE}|{e['공시분기']}|{e['항목번호']}"
        s = diag_by.get(k)
        if s is None or key in out["entries"]:
            continue
        d = round(abs(e["값"] - s), 9)
        if d <= 0.05:
            out["entries"][key] = {
                "overlay": "CSM", "verdict": "SAME_EXACT" if d <= 0.005 else "SAME_AT_1DP", "gold": e["값"], "src": s,
                "source_file": DIAG_REL,
                "note": "2026-10-21 parser/ifrs17 ticket 20261021T1310Z (KR0073 CSM basis/vintage fix): masked gold cell pinned (gold equals the builder diag within 1dp; "
                        "gold carries the 2dp printed value). GOLD_OVERLAY_DRIFT RED if the builder source stops reproducing it.",
            }
            added.append(key)
    return out, removed, added


def census_of(gold, pin, diag_rows):
    import validate_data_contract as G  # same import the manifest test uses
    rows = G.gold_overlay_census("CSM", gold["set"], diag_rows)
    masked = [r for r in rows if r["verdict"] in G._GOLD_MASKED]
    pins = pin.get("entries", {})
    unpinned = [r["key"] for r in masked if r["key"] not in pins]
    drift = [r["key"] for r in rows if r["key"] in pins and r["verdict"] not in G._GOLD_MASKED]
    seen = {r["key"] for r in rows}
    stale = [k for k in pins if k.startswith("CSM|") and k not in seen]
    return (len(rows), len(masked)), unpinned, drift, stale


def plan(scenario, with_amort_pins):
    live = {k: JsonFile(rel) for k, rel in F.items()}
    vec = load_vectors()
    diag_rows = json.loads((ROOT / DIAG_REL).read_text(encoding="utf-8"))
    diag_by = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in diag_rows}

    new_gold, gold_edits = build_gold(live["GOLD"].obj, scenario, vec, True)
    new_pin, pins_removed, pins_added = pins_for(new_gold, live["PIN"].obj, diag_by)
    census_old, un0, dr0, st0 = census_of(live["GOLD"].obj, live["PIN"].obj, diag_rows)
    census_new, un1, dr1, st1 = census_of(new_gold, new_pin, diag_rows)

    # master via the real builder logic
    sim = simulate_build(new_gold, live["CSM"].raw, f"plan_{scenario}")
    live_rows = live["CSM"].obj
    sim_by = {rkey(r): r for r in sim}
    new_master = []
    other_diff = []
    for r in live_rows:
        s = sim_by.get(rkey(r))
        if s is None:
            raise SystemExit(f"ABORT: {rkey(r)} missing from the builder simulation")
        if r["원보험사코드"] == CODE:
            nr = dict(r)
            nr["값"], nr["값_당분기"] = s["값"], s["값_당분기"]
            new_master.append(nr)
        else:
            if (r["값"], r.get("값_당분기")) != (s["값"], s.get("값_당분기")):
                other_diff.append(rkey(r))
            new_master.append(r)
    if len(sim) != len(live_rows):
        raise SystemExit(f"ABORT: builder simulation row count {len(sim)} != live {len(live_rows)}")
    master_changes = []
    for r, n in zip(live_rows, new_master):
        if r["원보험사코드"] == CODE and (r["값"], r.get("값_당분기")) != (n["값"], n.get("값_당분기")):
            master_changes.append({"quarter": r["공시분기"], "item": r["항목번호"], "old": r["값"], "new": n["값"],
                                   "old_dangi": r.get("값_당분기"), "new_dangi": n.get("값_당분기")})

    # amort ledger
    new_amort = copy.deepcopy(live["AMORT"].obj)
    amort_removed, amort_added = [], []
    if AMORT_KEY_2026_1Q in new_amort["entries"]:
        ent = new_amort["entries"][AMORT_KEY_2026_1Q]
        if ent.get("residual_eok") != -4.36:
            raise SystemExit(f"ABORT: ledger entry {AMORT_KEY_2026_1Q} residual {ent.get('residual_eok')} != -4.36 (state moved)")
        del new_amort["entries"][AMORT_KEY_2026_1Q]
        amort_removed.append(AMORT_KEY_2026_1Q)
    if scenario == "R" and with_amort_pins:
        pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
        pl4 = {r["공시분기"]: r["값"] for r in pl if r["원보험사코드"] == CODE and r["항목번호"] == 4}
        rv = r_vectors(vec)
        for q in ("2023.1Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q"):
            pl_eok = round(abs(pl4[q]) / 100.0, 2)
            wf = round(abs(rv[q][4]), 2)
            key = f"교보생명보험|{q}"
            new_amort["entries"][key] = {
                "residual_eok": round(pl_eok - wf, 2), "pl_eok": pl_eok, "waterfall_eok": wf, "rel": round(abs(pl_eok - wf) / wf, 6),
                "cause": "RESTATEMENT_BASIS", "note": AMORT_PIN_NOTE,
                "routed": "inbox/parser/20261021T1310Z__orchestrator__KR0073_2023.1Q-2026.1Q__csm_basis_vintage_fix.md",
            }
            amort_added.append(key)
        new_amort["entries"] = dict(sorted(new_amort["entries"].items()))

    # provenance flags
    new_prov = copy.deepcopy(live["PROV"].obj)
    prov_flagged = []
    for c in new_prov["cells"]:
        if c["company_code"] == CODE and c["item_block"] == "csm_waterfall" and c["quarter"] in ("2023.1Q", "2023.2Q") and not c.get("owner_override"):
            c["owner_override"] = True
            prov_flagged.append(c["quarter"])
    new_prov["merge_note_20261021_kr0073_basis_fix"] = (
        "ticket 20261021T1310Z (KR0073 CSM basis/vintage fix): 2026.1Q items 2-6 re-set to the separate-basis sum of the three 17-4 sub-tables (data/_gold/user_csm_cells.json, owner_override); "
        "2023.1Q/2Q already carried 12 gold cells (raw re-confirmation 2026-08-25) -> owner_override flag added. Evidence data/_derived/kyobo_csm_basis_fix_20261021/")
    if scenario == "R":
        new_prov["merge_note_20261022_kr0073_csm_restated"] = (
            "ticket 20261021T1310Z E1-E4 (owner decision 2026-10-22: no RESTATEMENT_BASIS pins, the PL block is restated instead): KR0073 CSM 2023.1Q-2024.2Q set to the latest-filing "
            "(restated) separate-basis vintage via data/_gold/user_csm_cells.json (owner_override already flagged on these blocks); item 4 = printed 추정치 변동 residual. "
            "Companion PL refresh: data/_gold/user_pl_cells.json (+122 KR0073 cells, PL_breakdown_provenance.json merge_note_20261022_kr0073_pl_refresh). "
            "Evidence data/_derived/kyobo_csm_basis_fix_20261021/ and data/_derived/kyobo_pl_restate_dryrun_20261021/")

    # test manifest declaration
    test_raw = (ROOT / TEST_REL).read_text(encoding="utf-8")
    old_decl = 'GOLD_OVERLAY_CENSUS = {"CSM": (%d, %d), "PL": (360, 29)}' % census_old
    new_decl = 'GOLD_OVERLAY_CENSUS = {"CSM": (%d, %d), "PL": (360, 29)}' % census_new
    new_test = test_raw
    if census_new != census_old:
        if test_raw.count(old_decl) != 1:
            raise SystemExit(f"ABORT: declaration {old_decl!r} not found exactly once in {TEST_REL}")
        note = ("# %s ticket 20261021T1310Z (parser/ifrs17, KR0073 CSM %s): CSM gold %d->%d cells, masked %d->%d (pins re-derived).\n"
                % ("2026-10-22" if scenario == "R" else "2026-10-21",
                   "restated vintage E1-E4" if scenario == "R" else "basis/vintage fix",
                   census_old[0], census_new[0], census_old[1], census_new[1]))
        new_test = test_raw.replace(old_decl, note + new_decl)

    return dict(live=live, new_gold=new_gold, gold_edits=gold_edits, new_pin=new_pin, pins_removed=pins_removed, pins_added=pins_added,
                census_old=census_old, census_new=census_new, census_flags=(un1, dr1, st1), census_flags_old=(un0, dr0, st0),
                new_master=new_master, master_changes=master_changes, other_diff=other_diff, new_amort=new_amort,
                amort_removed=amort_removed, amort_added=amort_added, new_prov=new_prov, prov_flagged=prov_flagged,
                test_raw=test_raw, new_test=new_test, vec=vec, scenario=scenario)


def closure_ok(master_rows, quarters):
    by = {}
    for r in master_rows:
        if r["원보험사코드"] == CODE:
            by.setdefault(r["공시분기"], {})[r["항목번호"]] = r["값"]
    bad = []
    for q in quarters:
        d = by[q]
        gap = round(d[1] + d[2] + d[3] + d[4] + d[5] - d[6], 2)
        if abs(gap) > 0.011:
            bad.append((q, gap))
    return bad


def report(P, out_csv=None):
    s = P["scenario"]
    print(f"=== scenario {s}")
    print(f"gold edits: {len(P['gold_edits'])} ({sum(1 for e in P['gold_edits'] if e['op']=='update')} update, {sum(1 for e in P['gold_edits'] if e['op']=='add')} add)")
    for e in P["gold_edits"]:
        print(f"   gold {e['op']:6s} {e['key'][2]} item{e['key'][1]}: {e['old']} -> {e['new']}")
    print(f"pins removed {len(P['pins_removed'])}: {P['pins_removed']}")
    print(f"pins added   {len(P['pins_added'])}: {P['pins_added']}")
    print(f"census (gold cells, masked) {P['census_old']} -> {P['census_new']}; flags after: unpinned={P['census_flags'][0]} drift={P['census_flags'][1]} stale={P['census_flags'][2]}")
    print(f"amort ledger removed {P['amort_removed']} added {P['amort_added']}")
    print(f"provenance owner_override added for {P['prov_flagged']}")
    print(f"master KR0073 cells changed: {len(P['master_changes'])} (non-KR0073 differences vs fresh builder: {len(P['other_diff'])})")
    for c in P["master_changes"]:
        print(f"   master {c['quarter']} item{c['item']}: 값 {c['old']} -> {c['new']} | 값_당분기 {c['old_dangi']} -> {c['new_dangi']}")
    changed_q = sorted({c["quarter"] for c in P["master_changes"] if c["old"] != c["new"]}, key=qkey)
    print("YTD closure gaps of changed quarters:", closure_ok(P["new_master"], changed_q) or "all closed (<=0.011)")
    if out_csv:
        cites = {}
        for sid in ([E5_SPEC_ID] + (list(R_SPEC_IDS.values()) if s == "R" else [])):
            v = P["vec"][sid]
            cites[v["period"]] = (sid, v)
        key = {1: "open", 2: "new", 3: "fin", 5: "release", 6: "close"}
        with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["master", "company", "quarter", "item", "field", "old", "new", "kind", "raw_file", "raw_cite"])
            for c in P["master_changes"]:
                kind = "target" if c["old"] != c["new"] else "derived_dangi_followon"
                sid_v = cites.get(c["quarter"])
                cite, rawf = "", ""
                if sid_v:
                    sid, v = sid_v
                    rawf = v["file"]
                    if c["item"] in key:
                        cite = " + ".join(f"{cc[key[c['item']]]['txt']}@L{cc[key[c['item']]]['line']}" for cc in v["cells"] if key[c["item"]] in cc)
                    elif c["item"] == 4:
                        cite = "residual: " + " ; ".join(f"est {cc['est']['txt']}@L{cc['est']['line']}" for cc in v["cells"] if "est" in cc)
                if c["old"] != c["new"]:
                    w.writerow(["CSM_waterfall", CODE, c["quarter"], c["item"], "값", c["old"], c["new"], kind, rawf, cite])
                if c["old_dangi"] != c["new_dangi"]:
                    w.writerow(["CSM_waterfall", CODE, c["quarter"], c["item"], "값_당분기", c["old_dangi"], c["new_dangi"],
                                "derived" if c["old"] == c["new"] else "derived(builder rule)", rawf, ""])
        print("wrote", out_csv)


def outputs(P):
    L = P["live"]
    gold_bytes = JsonFile._dump(P["new_gold"], *L["GOLD"].fmt)
    pin_bytes = JsonFile._dump(P["new_pin"], *L["PIN"].fmt)
    amort_bytes = JsonFile._dump(P["new_amort"], *L["AMORT"].fmt)
    prov_bytes = JsonFile._dump(P["new_prov"], *L["PROV"].fmt)
    master_bytes = JsonFile._dump(P["new_master"], *L["CSM"].fmt)
    out = {F["GOLD"]: gold_bytes, F["CSM"]: master_bytes, F["AMORT"]: amort_bytes, F["PROV"]: prov_bytes}
    if P["pins_removed"] or P["pins_added"]:
        out[F["PIN"]] = pin_bytes
    if P["new_test"] != P["test_raw"]:
        out[TEST_REL] = P["new_test"].encode("utf-8")
    return out


def verify_reproducible():
    """fresh builder run from the LIVE gold + LIVE master must equal the live master in ALL rows."""
    gold = json.loads((ROOT / F["GOLD"]).read_text(encoding="utf-8"))
    raw = (ROOT / F["CSM"]).read_bytes()
    live = json.loads(raw.decode("utf-8"))
    sim = simulate_build(gold, raw, "verify")
    lb, sb = {rkey(r): r for r in live}, {rkey(r): r for r in sim}
    diffs = [k for k in lb if k not in sb or (lb[k]["값"], lb[k].get("값_당분기"), lb[k].get("항목명")) != (sb[k]["값"], sb[k].get("값_당분기"), sb[k].get("항목명"))]
    extra = [k for k in sb if k not in lb]
    print(f"verify: live rows {len(live)}, builder rows {len(sim)}, differing {len(diffs)}, only-in-builder {len(extra)}")
    for k in diffs[:20]:
        print("   DIFF", k, lb[k]["값"], lb[k].get("값_당분기"), "vs", sb.get(k, {}).get("값"), sb.get(k, {}).get("값_당분기"))
    return not diffs and not extra


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", choices=["E5", "R"])
    ap.add_argument("--with-amort-pins", action="store_true", help="R only: also write the 5 RESTATEMENT_BASIS ledger pins (REQUIRES OWNER APPROVAL)")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    ap.add_argument("--out-dir")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()

    if a.verify:
        raise SystemExit(0 if verify_reproducible() else 2)
    if not a.scenario:
        raise SystemExit("--scenario is required")
    backup = EV / f"backup_before_apply_{a.scenario}"
    manifest_path = EV / f"apply_manifest_{a.scenario}.json"

    if a.revert:
        if not a.apply:
            raise SystemExit("--revert needs --apply")
        man = json.loads(manifest_path.read_text(encoding="utf-8"))
        for rel, h in man["after_sha256"].items():
            if sha((ROOT / rel).read_bytes()) != h:
                raise SystemExit(f"ABORT revert: {rel} changed since apply (post-apply hash mismatch)")
        for rel in man["before_sha256"]:
            write_atomic(ROOT / rel, (backup / rel).read_bytes())
        print("reverted", list(man["before_sha256"]))
        return

    if a.scenario == "R" and not a.with_amort_pins:
        print("NOTE: scenario R without --with-amort-pins leaves 5 CSM_AMORT_IDENTITY_BREAK REDs until PL item 4 is restated too "
              "(owner 2026-10-22: pins rejected) -- apply it only together with data/_derived/kyobo_pl_restate_dryrun_20261021/apply_kr0073_pl_refresh.py in the same pass.")
    P = plan(a.scenario, a.with_amort_pins)
    csv_path = EV / f"cell_changes_{a.scenario}{'_with_pins' if a.with_amort_pins else ''}.csv"
    report(P, str(csv_path))
    outs = outputs(P)
    if P["other_diff"]:
        raise SystemExit(f"ABORT: fresh builder differs from the live master for non-{CODE} rows: {P['other_diff'][:5]} -- not applying")
    if P["census_flags"][0] or P["census_flags"][1]:
        raise SystemExit(f"ABORT: gold census flags unpinned={P['census_flags'][0]} drift={P['census_flags'][1]}")

    if a.out_dir:
        od = Path(a.out_dir)
        for rel, b in outs.items():
            write_atomic(od / rel, b)
        print("simulated post-apply files under", od)
        return
    if not a.apply:
        print("(--check only; nothing written)")
        return

    # --- apply: guards then write, with automatic restore on failure
    before = {rel: sha((ROOT / rel).read_bytes()) for rel in outs}
    expect = {F["GOLD"]: P["live"]["GOLD"].sha0, F["CSM"]: P["live"]["CSM"].sha0, F["AMORT"]: P["live"]["AMORT"].sha0, F["PROV"]: P["live"]["PROV"].sha0, F["PIN"]: P["live"]["PIN"].sha0}
    for rel, h in before.items():
        if rel in expect and expect[rel] != h:
            raise SystemExit(f"ABORT: {rel} changed between read and write (concurrent session?)")
    backup.mkdir(parents=True, exist_ok=True)
    for rel in outs:
        dst = backup / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, dst)
    written = []
    try:
        for rel, b in outs.items():
            write_atomic(ROOT / rel, b)
            written.append(rel)
    except BaseException:
        for rel in written:
            write_atomic(ROOT / rel, (backup / rel).read_bytes())
        raise
    after = {rel: sha((ROOT / rel).read_bytes()) for rel in outs}
    manifest_path.write_text(json.dumps({"scenario": a.scenario, "with_amort_pins": a.with_amort_pins, "before_sha256": before, "after_sha256": after,
                                         "applied_at": time.strftime("%Y-%m-%dT%H:%M:%S")}, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print("APPLIED:", list(outs))


if __name__ == "__main__":
    main()
