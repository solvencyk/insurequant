#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cell-level applier (parser/ifrs17, validation ticket 20261021T1655Z, coordinator decision 2026-10-22 "option B-lite"):
KR0073 2023.3Q single quarter (PL 값_당분기) = the restated THREE-MONTH value PRINTED in the FY2024 Q3 report wherever it is printed and the 10 PL identities close;
blank (null) only where nothing is printed.  Supersedes the first step (apply_seam_blank.py: 28 cells blanked).

Source of the values: seam_3m_plan.json (extract_3m.py: raw XML cells with line numbers, cross-checked against the production FS-API/Tier-2 harness; 29 SET, 1 NULL (item 15: no printed
row), 2 KEEP (13/14: builder 0.0)).  Cumulative 값 is not touched; every other quarter is not touched.

Mechanism (extends the hook of the first step): gold overlay data/_gold/user_pl_cells.json
    null_dangi.cells : [[code, quarter, item], ...]                      -> 값_당분기 forced to null   (now only item 15)
    set_dangi.cells  : [[code, quarter, item, value, source], ...]       -> 값_당분기 forced to the printed 3-month value
read by build_root_masters._pl_null_dangi_keys / _pl_set_dangi_values in build_pl() (a key in both lists is refused).

Writes (guarded + backed up): scripts/build_root_masters.py, data/_gold/user_pl_cells.json, PL_breakdown.json (KR0073 2023.3Q 값_당분기 only), tests/test_gold_overlay_survives_rebuild.py.
  --check | --apply | --revert --apply | --verify
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
EV = ROOT / "data" / "_derived" / "kyobo_seam_blank_20261022"
sys.stdout.reconfigure(encoding="utf-8")


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


asb = _load(EV / "apply_seam_blank.py", "asb_helpers")       # ak (JsonFile/write_atomic/sha), git_json, rkey, text_edit, patched_module, run_build_pl, splice, F, BRM_REL, TEST_REL
ak = asb.ak
CODE, QTR = asb.CODE, asb.QTR
F, BRM_REL, TEST_REL = asb.F, asb.BRM_REL, asb.TEST_REL

SET_HELPER = '''def _pl_set_dangi_values(path):
    """{(코드, 분기, 항목번호): 값} — PL gold 파일(PL_OVR)의 `set_dangi.cells` = [코드, 분기, 항목, 값, 출처]. 그 분기의 3개월 열이 공시에 인쇄돼 있고 누계 차분이 그 값과 어긋나는 칸
    (재작성 전 상반기 누계 + 재작성 후 9개월 누계의 차)에 차분 대신 인쇄값을 값_당분기로 쓴다. 값(연누계)은 그대로. 파일이나 키가 없으면 빈 dict(구 동작 그대로)."""
    if not path.exists():
        return {}
    doc = json.loads(path.read_text(encoding="utf-8"))
    cells = (doc.get("set_dangi") or {}).get("cells", [])
    return {(c[0], c[1], int(c[2])): float(c[3]) for c in cells}


'''
BRM_EDITS = [
    ("    return {(c, q, int(i)) for c, q, i in cells}\n\n\ndef build_pl():\n",
     "    return {(c, q, int(i)) for c, q, i in cells}\n\n\n" + SET_HELPER + "def build_pl():\n"),
    ('    print(f"  pl 값_당분기 의도적 null (누계 유지): {len(null_dangi)} cells")\n',
     '    print(f"  pl 값_당분기 의도적 null (누계 유지): {len(null_dangi)} cells")\n'
     '    set_dangi = _pl_set_dangi_values(PL_OVR)\n'
     '    print(f"  pl 값_당분기 공시 3개월 인쇄값 고정 (누계 유지): {len(set_dangi)} cells")\n'
     '    both = null_dangi & set(set_dangi)\n'
     '    if both:\n'
     '        raise ValueError(f"null_dangi 와 set_dangi 에 같은 칸이 있다: {sorted(both)[:3]}")\n'),
    ('        if (r["원보험사코드"], r["공시분기"], r["항목번호"]) in null_dangi:\n'
     '            dangi = None             # 두 누계의 공시 기준이 달라 차분이 틀린 단일분기 — 값(누계)은 유지\n',
     '        k3 = (r["원보험사코드"], r["공시분기"], r["항목번호"])\n'
     '        if k3 in null_dangi:\n'
     '            dangi = None             # 인쇄된 3개월 값이 없고 차분은 틀린 단일분기 — 값(누계)은 유지\n'
     '        elif v is not None and k3 in set_dangi:\n'
     '            dangi = set_dangi[k3]    # 두 누계의 공시 기준이 달라 차분이 틀린 단일분기 — 공시 3개월 열 인쇄값 사용, 값(누계)은 유지\n'),
]
DOC_SENTENCE = (" set_dangi.cells: [code, quarter, item, value, source] -- the single-quarter 값_당분기 is forced to the THREE-MONTH value printed in the filing (kept: 값 YTD), for single quarters "
                "whose two cumulatives come from different disclosure vintages (build_root_masters._pl_set_dangi_values; a key in null_dangi and set_dangi is refused).")
NULL_DOC = ("KR0073 2023.3Q item 15 (기타영업수익): the separate statement of the FY2024 Q3 report prints no 기타영업수익 row, so there is no printed 3-month value (the cumulative 0.0 is an "
            "assemble() default for 생보); the single quarter stays blank, as it was before commit 3e53aef8. Ticket inbox/parser/20261021T1655Z__validation__KR0073_2023.3Q__single_quarter_vintage_seam.md")
SET_DOC = ("KR0073 2023.3Q single quarter = the restated THREE-MONTH value printed in the FY2024 Q3 report (data/dart/FY2024_Q3/raw/KR0073_교보생명보험/20241114003039.xml, separate basis, prior-year "
           "3-month column of the income statement / OCI and of the 보험수익 / 보험서비스비용 / 재보험 notes; the cell line is the 5th element). Derived items (2, 3, 7, 8, 12, 18, 19, 32) apply the "
           "production assemble() definitions to printed 3-month cells. All 10 PL identities close on this vector (residual <= 1e-6 백만원) and an independent read (FS-API frmtrm_q_amount + the "
           "production Tier-2 handler) agrees for every cell. The cumulative 값 is not touched, so the four 2023 single quarters do not add up to the full-year value: the difference is the "
           "restated first-half correction that was never published (the FY2024 Q1/Q2 comparatives are pre-correction), e.g. 원수 CSM상각 105,255 + 106,779 + 150,548 + 163,380 = 525,962 vs "
           "627,701 (difference 101,739). Items not printed stay null (null_dangi). Ticket inbox/parser/20261021T1655Z__validation__KR0073_2023.3Q__single_quarter_vintage_seam.md; "
           "evidence data/_derived/kyobo_seam_blank_20261022/ (seam_3m_extract.txt, seam_3m_vector.csv)")
NEW_TESTS = '''

def test_pl_set_dangi_uses_the_printed_single_quarter(tmp_path, monkeypatch):
    """gold `set_dangi.cells` forces 값_당분기 to the printed value for exactly the listed cell (값 stays; neighbours keep their derived single quarter; a cell listed in null_dangi stays
    blank; the result survives a second rebuild)."""
    src = tmp_path / "pl_breakdown_master.json"
    out = tmp_path / "PL_breakdown.json"
    ovr = tmp_path / "user_pl_cells.json"

    def row(item, q, v):
        return {"원보험사코드": "KR9999", "원수사명": "테스트생명", "티커": None, "생손보여부": "생명보험", "항목번호": item,
                "항목명": f"항목{item}", "공시분기": q, "값": v}

    _write(src, [row(1, "2023.1Q", 100), row(1, "2023.2Q", 250), row(1, "2023.3Q", 600),
                 row(20, "2023.1Q", 10), row(20, "2023.2Q", 30), row(20, "2023.3Q", 70),
                 row(21, "2023.1Q", 1), row(21, "2023.2Q", 2), row(21, "2023.3Q", 3)])
    _write(ovr, {"set": [], "set_dangi": {"cells": [["KR9999", "2023.3Q", 1, 123.5, "test"]]}, "null_dangi": {"cells": [["KR9999", "2023.3Q", 21]]}})
    monkeypatch.setattr(brm, "PL_SRC", src)
    monkeypatch.setattr(brm, "PL_OUT", out)
    monkeypatch.setattr(brm, "PL_OVR", ovr)

    def check():
        rows = {(r["항목번호"], r["공시분기"]): r for r in json.loads(out.read_text(encoding="utf-8"))}
        assert rows[(1, "2023.3Q")]["값"] == 600, "the cumulative 값 must stay"
        assert rows[(1, "2023.3Q")]["값_당분기"] == 123.5, "listed cell must carry the printed value"
        assert rows[(1, "2023.2Q")]["값_당분기"] == 150, "same item, other quarter must keep its derived value"
        assert rows[(20, "2023.3Q")]["값_당분기"] == 40, "other item, same quarter must keep its derived value"
        assert rows[(21, "2023.3Q")]["값_당분기"] is None, "a null_dangi cell must stay blank"
        assert rows[(21, "2023.3Q")]["값"] == 3

    brm.build_pl()
    check()
    brm.build_pl()
    check()


def test_pl_null_dangi_and_set_dangi_overlap_is_refused(tmp_path, monkeypatch):
    """the same cell in null_dangi and set_dangi is a contradiction -> the build refuses instead of picking one silently."""
    import pytest

    src = tmp_path / "pl_breakdown_master.json"
    out = tmp_path / "PL_breakdown.json"
    ovr = tmp_path / "user_pl_cells.json"
    _write(src, [{"원보험사코드": "KR9999", "원수사명": "테스트생명", "티커": None, "생손보여부": "생명보험", "항목번호": 1,
                  "항목명": "항목1", "공시분기": q, "값": v} for q, v in (("2023.1Q", 100), ("2023.2Q", 250), ("2023.3Q", 600))])
    _write(ovr, {"set": [], "set_dangi": {"cells": [["KR9999", "2023.3Q", 1, 123.5, "test"]]}, "null_dangi": {"cells": [["KR9999", "2023.3Q", 1]]}})
    monkeypatch.setattr(brm, "PL_SRC", src)
    monkeypatch.setattr(brm, "PL_OUT", out)
    monkeypatch.setattr(brm, "PL_OVR", ovr)
    with pytest.raises(ValueError):
        brm.build_pl()
'''


def plan():
    pl3 = json.loads((EV / "seam_3m_plan.json").read_text(encoding="utf-8"))
    SET = pl3["set"]
    NULL = pl3["null"]
    KEEP = pl3["keep"]
    if pl3["quarter"] != QTR or len(SET) != 29 or [c[2] for c in NULL] != [15] or KEEP != [13, 14]:
        raise SystemExit(f"ABORT: seam_3m_plan.json moved: set {len(SET)}, null {[c[2] for c in NULL]}, keep {KEEP}")
    live = {k: ak.JsonFile(rel) for k, rel in F.items()}
    brm_raw = (ROOT / BRM_REL).read_text(encoding="utf-8")
    test_raw = (ROOT / TEST_REL).read_text(encoding="utf-8")
    for label, t in ((BRM_REL, brm_raw), (TEST_REL, test_raw)):
        if "\r" in t:
            raise SystemExit(f"ABORT: {label} has CR characters")
    if "_pl_null_dangi_keys" not in brm_raw:
        raise SystemExit("ABORT: the first-step hook (_pl_null_dangi_keys) is not in the builder")
    new_brm = asb.text_edit(brm_raw, BRM_EDITS, BRM_REL) if "_pl_set_dangi_values" not in brm_raw else brm_raw
    new_test = test_raw if "test_pl_set_dangi_uses_the_printed_single_quarter" in test_raw else test_raw.rstrip("\n") + "\n" + NEW_TESTS

    gold = copy.deepcopy(live["GOLD"].obj)
    doc = gold.get("_doc", "")
    if DOC_SENTENCE.strip() not in doc:
        gold["_doc"] = doc + DOC_SENTENCE
    gold["null_dangi"] = {"_doc": NULL_DOC, "cells": [list(c) for c in NULL]}
    gold["set_dangi"] = {"_doc": SET_DOC, "cells": SET}

    mod = asb.patched_module(new_brm)
    sim = asb.run_build_pl(mod, gold, "plan2")
    new_rows, val_changed, dangi_changed, other_drift = asb.splice(live["PL"].obj, sim)

    # ---- expectations
    errs = []
    head = {asb.rkey(r): r for r in asb.git_json("HEAD", F["PL"]) if r["원보험사코드"] == CODE}
    cur = {asb.rkey(r): r for r in live["PL"].obj if r["원보험사코드"] == CODE}
    nb = {asb.rkey(r): r for r in new_rows if r["원보험사코드"] == CODE}
    exp = {}
    for c in SET:
        exp[(CODE, c[2], QTR)] = round(c[3], 6)
    for c in NULL:
        exp[(CODE, c[2], QTR)] = None
    for i in KEEP:
        exp[(CODE, i, QTR)] = cur[(CODE, i, QTR)].get("값_당분기")
    for k, v in exp.items():
        got = nb[k].get("값_당분기")
        same = (got is None and v is None) or (got is not None and v is not None and abs(got - v) <= 1e-9)
        if not same:
            errs.append(f"{k}: built {got} != expected {v}")
    if val_changed:
        errs.append(f"cumulative 값 changed: {val_changed[:5]}")
    stray = [k for k in dangi_changed if k not in exp]
    if stray:
        errs.append(f"값_당분기 changed outside the 2023.3Q targets: {stray[:5]}")
    snap = EV / "pl_drift_before_seam.json"
    before = {tuple(x) for x in json.loads(snap.read_text(encoding="utf-8"))["non_kr0073_drift"]}
    if before != set(other_drift):
        errs.append(f"non-KR0073 drift changed vs snapshot: {len(before)} -> {len(other_drift)}")
    # identities on the resulting single-quarter vector (15 := 0 only for the closure test)
    v = {k[1]: nb[k].get("값_당분기") for k in nb if k[2] == QTR}
    z = lambda i: 0.0 if v.get(i) is None and i == 15 else v.get(i)
    ident = {"20=1+17": (20, [1, 17]), "22=20+21": (22, [20, 21]), "17=18+19": (17, [18, 19]), "25=26..30+32": (25, [26, 27, 28, 29, 30, 32]),
             "1=2+15-16": None, "2=3+8": (2, [3, 8]), "3=4+5+6+7": (3, [4, 5, 6, 7]), "8=9+10+11+12": (8, [9, 10, 11, 12])}
    res = {}
    for name, spec in ident.items():
        if spec is None:
            res[name] = z(1) - (z(2) + z(15) - z(16))
        else:
            res[name] = z(spec[0]) - sum(z(i) for i in spec[1])
    res["24=22-23"] = z(24) - (z(22) - z(23))
    res["31=24+25"] = z(31) - (z(24) + z(25))
    bad = {k: r for k, r in res.items() if abs(r) > 0.01}
    if bad:
        errs.append(f"single-quarter identities do not close: {bad}")
    # what changes against git HEAD (the committed state) and against the live (first-step) state
    vs_head = sorted(k[1] for k in nb if k[2] == QTR and not ((nb[k].get("값_당분기") is None and head[k].get("값_당분기") is None) or
                                                               (nb[k].get("값_당분기") is not None and head[k].get("값_당분기") is not None and abs(nb[k]["값_당분기"] - head[k]["값_당분기"]) <= 5e-4)))
    return dict(live=live, gold=gold, new_rows=new_rows, new_brm=new_brm, brm_raw=brm_raw, new_test=new_test, test_raw=test_raw, dangi_changed=dangi_changed,
                other_drift=other_drift, errs=errs, res=res, vs_head=vs_head, exp=exp, SET=SET, NULL=NULL)


def outputs(P):
    L = P["live"]
    return {F["GOLD"]: ak.JsonFile._dump(P["gold"], *L["GOLD"].fmt), F["PL"]: ak.JsonFile._dump(P["new_rows"], *L["PL"].fmt),
            BRM_REL: P["new_brm"].encode("utf-8"), TEST_REL: P["new_test"].encode("utf-8")}


def report(P):
    print(f"SET {len(P['SET'])}: {[c[2] for c in P['SET']]}")
    print(f"NULL {len(P['NULL'])}: {[c[2] for c in P['NULL']]}")
    print(f"master KR0073 2023.3Q 값_당분기 cells changed vs the live (first-step) state: {len(P['dangi_changed'])}")
    print(f"cells of 2023.3Q that differ from git HEAD (committed) after this step: {len(P['vs_head'])} items {P['vs_head']}")
    print("single-quarter identity residuals:", {k: round(r, 6) for k, r in P["res"].items()})
    print("errors:", P["errs"] or "none")


def verify():
    live_rows = json.loads((ROOT / F["PL"]).read_text(encoding="utf-8"))
    gold = json.loads((ROOT / F["GOLD"]).read_text(encoding="utf-8"))
    mod = asb._load(ROOT / BRM_REL, "brm_live_verify2")
    sim = asb.run_build_pl(mod, gold, "verify2")
    _rows, vc, dc, other = asb.splice(live_rows, sim)
    snap = {tuple(x) for x in json.loads((EV / "pl_drift_before_seam.json").read_text(encoding="utf-8"))["non_kr0073_drift"]}
    kr = sum(1 for r in live_rows if r["원보험사코드"] == CODE)
    ok1 = not vc and not dc
    ok2 = set(other) == snap
    print(f"verify: KR0073 rows {kr}; fresh real build_pl() (live builder + live gold) differs from live in {len(set(vc) | set(dc))} KR0073 cells -> {'OK' if ok1 else 'FAIL'}")
    print(f"verify: non-KR0073 drift now {len(other)} vs snapshot {len(snap)} -> {'OK (identical set)' if ok2 else 'FAIL'}")
    pl3 = json.loads((EV / "seam_3m_plan.json").read_text(encoding="utf-8"))
    head = {asb.rkey(r): r for r in asb.git_json("HEAD", F["PL"]) if r["원보험사코드"] == CODE}
    now = {asb.rkey(r): r for r in live_rows if r["원보험사코드"] == CODE}
    exp = {(CODE, c[2], QTR): round(c[3], 6) for c in pl3["set"]}
    exp.update({(CODE, c[2], QTR): None for c in pl3["null"]})
    bad = []
    for k in now:
        if k in exp:
            want = exp[k]
        elif k[2] == QTR:
            want = head[k].get("값_당분기")            # items 13/14: untouched
        else:
            want = head[k].get("값_당분기")            # every other quarter: identical to HEAD
        got = now[k].get("값_당분기")
        if not ((got is None and want is None) or (got is not None and want is not None and abs(got - want) <= 1e-6)):
            bad.append((k, got, want))
        if now[k]["값"] != head[k]["값"]:
            bad.append((k, "cumulative 값 differs from HEAD", now[k]["값"], head[k]["값"]))
    chg = [k for k in now if (now[k].get("값_당분기") is None) != (head[k].get("값_당분기") is None) or
           (now[k].get("값_당분기") is not None and head[k].get("값_당분기") is not None and abs(now[k]["값_당분기"] - head[k]["값_당분기"]) > 5e-4)]
    print(f"verify: live KR0073 vs expectation (SET/NULL from seam_3m_plan.json, everything else == git HEAD, 값 == HEAD): {len(bad)} deviations -> {'OK' if not bad else 'FAIL ' + str(bad[:4])}")
    print(f"verify: cells that differ from git HEAD (값_당분기 only): {len(chg)}; quarters {sorted({k[2] for k in chg})}; items {sorted(k[1] for k in chg)}")
    return ok1 and ok2 and not bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    backup = EV / "backup_before_apply_SEAM2"
    manifest_path = EV / "apply_manifest_SEAM2.json"
    if a.verify:
        raise SystemExit(0 if verify() else 2)
    if a.revert:
        if not a.apply:
            raise SystemExit("--revert needs --apply")
        man = json.loads(manifest_path.read_text(encoding="utf-8"))
        for rel, h in man["after_sha256"].items():
            if ak.sha((ROOT / rel).read_bytes()) != h:
                raise SystemExit(f"ABORT revert: {rel} changed since apply (post-apply hash mismatch)")
        for rel in man["before_sha256"]:
            ak.write_atomic(ROOT / rel, (backup / rel).read_bytes())
        print("reverted", list(man["before_sha256"]))
        return
    P = plan()
    report(P)
    if P["errs"]:
        raise SystemExit("ABORT: " + " | ".join(P["errs"]))
    outs = outputs(P)
    if not a.apply:
        print("(--check only; nothing written)")
        return
    before = {rel: ak.sha((ROOT / rel).read_bytes()) for rel in outs}
    expect = {F["GOLD"]: P["live"]["GOLD"].sha0, F["PL"]: P["live"]["PL"].sha0, BRM_REL: ak.sha(P["brm_raw"].encode("utf-8")), TEST_REL: ak.sha(P["test_raw"].encode("utf-8"))}
    for rel, h in before.items():
        if expect[rel] != h:
            raise SystemExit(f"ABORT: {rel} changed between read and write (concurrent session?)")
    backup.mkdir(parents=True, exist_ok=True)
    for rel in outs:
        dst = backup / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, dst)
    written = []
    try:
        for rel, b in outs.items():
            ak.write_atomic(ROOT / rel, b)
            written.append(rel)
    except BaseException:
        for rel in written:
            ak.write_atomic(ROOT / rel, (backup / rel).read_bytes())
        raise
    after = {rel: ak.sha((ROOT / rel).read_bytes()) for rel in outs}
    manifest_path.write_text(json.dumps({"before_sha256": before, "after_sha256": after, "applied_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                         "set_items": [c[2] for c in P["SET"]], "null_items": [c[2] for c in P["NULL"]]}, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print("APPLIED:", list(outs))


if __name__ == "__main__":
    main()
