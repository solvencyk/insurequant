# -*- coding: utf-8 -*-
"""
P3 (ticket 20261010T1330Z / validation ticket 20261010T1100Z): KR0004 예별손해보험 PL_breakdown.json
LOB legs for 2024.4Q and 2025.4Q -- items 2 (생명장기 손익), 3 (원수), 8 (재보험) are blank (`MASTER_HOLE` 부분, the
validation 'single_leg_gap_생명장기' baseline lines) and items 13/14 (자동차/일반) hold the wrong convention.

Findings (DART 감사보고서, 별도, 단위 천원; every number below is printed in the filing's own tables):
  * Notes 26-29 (보험수익 / 보험서비스비용 / 재보험수익 / 재보험서비스비용) print a 장기|일반|자동차|합계 split.
    LOB 보험서비스결과 (P&L sign, net of 재보험) = (보험수익 - 보험서비스비용) + (재보험수익 - 재보험서비스비용), per LOB.
    This is the convention every other 손보 handler uses (extract_tier2_sonbo_component: item13/14 = (rev-cost)+(rerev-recost);
    item3 = 장기 rev - cost, item8 = 장기 rerev - recost, item2 = 3 + 8).
  * The master's KR0004 items 13/14 for 2024.4Q/2025.4Q came from `extract_tier2_yebyeol`, which reads the LAST column of
    the '보험서비스결과 소계' row of the PAA roll-forward note: that is (a) 원수 PAA only, no 재보험, and (b) printed in the
    LIABILITY sign in the FY2024/FY2025 filings (expense positive: 자동차 +7,179,117 / +1,133,870, 일반 -12,479,214 /
    -14,235,271), while the FY2023 filing prints the same line in P&L sign.  So the cells are sign-inverted and ex-재보험.
  * With the net P&L-sign legs the identity closes EXACTLY against two independent income-statement anchors:
        item1 = item2 + item13 + item14 + item15 - item16
        2025: -5,952.388 - 1,193.358 + 131.584 + 0 - 15,121.955 = -22,136.117  (IS 보험손익 -22,136,117,075 원)
        2024: -48,228.958 - 7,276.610 + 1,434.084 + 0 -  5,464.348 = -59,535.832  (IS 보험손익 -59,535,831,800 원)
    (item 1 and item 16 come from the income statement / FS-API, not from the notes.)

What this script changes (cell level, old-value guard, backup first, byte-exact round trip, nothing else is touched):
  PL_breakdown.json            2024.4Q + 2025.4Q: items 2, 3, 8 (None -> value), items 13, 14 (old -> corrected)
  PL_breakdown_provenance.json  the two DART income_statement blocks: items 2, 3, 8 added to the raw_filing bucket
Not touched: 2023.4Q (hidden, no 보험손익 to close against), the builder master data/dart/viz/pl_breakdown_master.json
(PL golden), data/_gold/*, build_pl_breakdown.py, validate_*.py.  The values are printed for the follow-up
(`_GOLD_CELL_OVERRIDE` / handler fix) that has to be paired with a PL-golden regeneration by validation.

Usage:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/fix_20261010_pl_kr0004_lob_legs.py [--write]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.stdout.reconfigure(encoding="utf-8")
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402

PL = REPO / "PL_breakdown.json"
SIDE = REPO / "PL_breakdown_provenance.json"
BACKUP_DIR = REPO / "data" / "_derived" / "pl_kr0004_lob_backup_20261010"
MANIFEST = REPO / "data" / "_derived" / "pl_kr0004_lob_legs_20261010.json"

CODE = "KR0004"
FILES = {
    "FY2024": REPO / "data/dart/FY2024_Q4/raw/KR0004_엠지손해보험_20250408000587/20250408000587_00760.xml",
    "FY2025": REPO / "data/dart/FY2025_Q4/raw/KR0004_엠지손해보험_20260406003175/20260406003175_00760.xml",
}
QUARTER_OF = {"FY2024": "2024.4Q", "FY2025": "2025.4Q"}
LOBS = ("장기", "일반", "자동차")
NOTES = {  # key -> (caption must contain any of, caption must not contain)
    "rev": (("보험수익의 내역", "보험계약수익의 내역"), "재보험"),
    "cost": (("보험서비스비용의 내역",), "재보험"),
    "rerev": (("재보험수익의 내역", "재보험계약수익의 내역"), None),
    "recost": (("재보험서비스비용의 내역",), None),
}
ITEM_NAME = {2: "생명장기 손익", 3: "생명장기 원수손익", 8: "생명장기 재보험손익", 13: "자동차손익", 14: "일반손익"}


def fail(msg: str):
    raise SystemExit(f"ABORT: {msg}")


def _ns(s: str) -> str:
    return re.sub(r"[\s\u3000\xa0]+", "", s or "")


def _num(cell: str) -> int:
    t = _ns(cell)
    if t in ("", "-"):
        return 0
    neg = t.startswith("(") and t.endswith(")")
    v = int(t.strip("()").replace(",", ""))
    return -v if neg else v


def read_notes(xml: Path) -> dict:
    """{note: {"cur": {lob: 천원, "합계": 천원}, "prev": {...}}} -- first match in document order = 당기, second = 전기."""
    tables = list(_iter_tables_with_context(xml))
    out = {}
    for key, (must, mustnot) in NOTES.items():
        hits = []
        for t in tables:
            cap = _ns(t.caption)
            if not any(_ns(m) in cap for m in must) or (mustnot and _ns(mustnot) in cap):
                continue
            hdr = next((r for r in t.rows if any(_ns(c).startswith("장기") for c in r)), None)
            if hdr is None:
                continue
            tot = next((r for r in t.rows if r and _ns(r[0]) == "합계"), None)
            if tot is None or len(tot) != len(hdr):
                fail(f"{xml.name} {key}: total row shape {len(tot) if tot else None} vs header {len(hdr)}")
            cols = {}
            for i, c in enumerate(hdr):
                n = re.sub(r"\(\*\d*\)", "", _ns(c))
                if n in LOBS or n == "합계":
                    cols[n] = i
            if set(cols) != set(LOBS) | {"합계"}:
                fail(f"{xml.name} {key}: header columns {cols}")
            vals = {k: _num(tot[i]) for k, i in cols.items()}
            if sum(vals[k] for k in LOBS) != vals["합계"]:
                fail(f"{xml.name} {key}: LOB columns do not add up to 합계 {vals}")
            hits.append(vals)
        if len(hits) != 2:
            fail(f"{xml.name} {key}: expected 2 tables (당기, 전기), found {len(hits)}")
        out[key] = {"cur": hits[0], "prev": hits[1]}
    return out


def read_is(xml: Path) -> dict:
    """Income-statement anchors (원): {label: (cur, prev)}."""
    want = {"보험손익": "Ⅰ.보험손익", "보험수익": "(1)보험수익", "재보험수익": "(2)재보험수익", "보험비용": "(1)보험비용",
            "재보험비용": "(2)재보험비용", "기타사업비용": "(3)기타사업비용"}
    for t in _iter_tables_with_context(xml):
        labs = [_ns(r[0]) for r in t.rows if r]
        if "Ⅰ.보험손익" not in labs or "(3)기타사업비용" not in labs:
            continue
        res = {}
        for k, lab in want.items():
            row = next((r for r in t.rows if r and _ns(r[0]) == lab), None)
            if row is None:
                fail(f"{xml.name}: income-statement row {lab} not found")
            # amounts only (>= one thousands group): note-number cells such as '26' or '9,31' are not amounts
            nums = [_num(c) for c in row[1:] if re.fullmatch(r"\(?\d{1,3}(,\d{3})+\)?", _ns(c))]
            if len(nums) != 2:
                fail(f"{xml.name}: income-statement row {lab}: expected 당기+전기 amounts, got {nums}")
            res[k] = (nums[0], nums[1])
        return res
    fail(f"{xml.name}: income statement not found")


def legs(cur: dict) -> dict:
    """All in 천원. cur = {rev, cost, rerev, recost} each {lob: v}."""
    r, c, rr, rc = cur["rev"], cur["cost"], cur["rerev"], cur["recost"]
    out = {"3": r["장기"] - c["장기"], "8": rr["장기"] - rc["장기"]}
    out["2"] = out["3"] + out["8"]
    out["13"] = (r["자동차"] - c["자동차"]) + (rr["자동차"] - rc["자동차"])
    out["14"] = (r["일반"] - c["일반"]) + (rr["일반"] - rc["일반"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    # ---- 1. read the filings -------------------------------------------------
    notes = {fy: read_notes(p) for fy, p in FILES.items()}
    isx = {fy: read_is(p) for fy, p in FILES.items()}
    plan_val = {}      # quarter -> {item: 백만원}
    manifest = {"_what": "KR0004 LOB legs from DART notes 26-29 (천원) and income-statement anchors (원); see the script docstring",
                "notes_천원": {}, "legs_백만원": {}, "closure": {}}
    # cross-year: FY2025's 전기 columns == FY2024's 당기 columns, all four notes x (3 LOB + 합계)
    for k in NOTES:
        if notes["FY2025"][k]["prev"] != notes["FY2024"][k]["cur"]:
            fail(f"FY2025 전기 != FY2024 당기 for {k}: {notes['FY2025'][k]['prev']} vs {notes['FY2024'][k]['cur']}")
    print("cross-year check: FY2025 전기 columns == FY2024 당기 columns (4 notes x 4 columns): OK")
    # income-statement prior column of FY2025 == current column of FY2024
    for k in isx["FY2024"]:
        if isx["FY2025"][k][1] != isx["FY2024"][k][0]:
            fail(f"IS 전기(FY2025) != IS 당기(FY2024) for {k}")
    print("cross-year check: IS 전기(FY2025) == IS 당기(FY2024): OK")

    for fy, q in QUARTER_OF.items():
        cur = {k: notes[fy][k]["cur"] for k in NOTES}
        manifest["notes_천원"][q] = cur
        # totals against the income statement (원): each note total (천원) vs IS line, +-2 천원 rounding
        for note, isk in (("rev", "보험수익"), ("rerev", "재보험수익"), ("cost", "보험비용"), ("recost", "재보험비용")):
            diff = cur[note]["합계"] * 1000 - isx[fy][isk][0]
            if abs(diff) > 2000:
                fail(f"{fy} {note} note total {cur[note]['합계']}천원 vs IS {isk} {isx[fy][isk][0]}원")
        lg = legs(cur)
        # 보험서비스결과 합 (천원) = rev+rerev-cost-recost, and 보험손익 = that - 기타사업비용
        svc = lg["2"] + lg["13"] + lg["14"]
        tot = (cur["rev"]["합계"] + cur["rerev"]["합계"] - cur["cost"]["합계"] - cur["recost"]["합계"])
        if svc != tot:
            fail(f"{fy}: LOB legs {svc} != total {tot}")
        other = isx[fy]["기타사업비용"][0]
        is_ins = isx[fy]["보험손익"][0]
        closure = svc * 1000 - other - is_ins            # 원
        manifest["closure"][q] = {"legs_sum_천원": svc, "기타사업비용_원": other, "IS_보험손익_원": is_ins, "residual_원": closure}
        if abs(closure) > 3000:
            fail(f"{fy}: legs - 기타사업비용 vs IS 보험손익 residual {closure} 원")
        plan_val[q] = {int(k): round(v / 1000.0, 3) for k, v in lg.items()}
        manifest["legs_백만원"][q] = plan_val[q]
        print(f"{q}: " + "  ".join(f"item{k}={plan_val[q][k]:,.3f}" for k in sorted(plan_val[q]))
              + f"   | closure vs IS 보험손익: residual {closure:,} 원")

    # ---- 2. read master + sidecar ------------------------------------------------
    raw_pl, raw_side = PL.read_bytes(), SIDE.read_bytes()
    rows = json.loads(raw_pl.decode("utf-8"))
    side = json.loads(raw_side.decode("utf-8"))
    fmt = lambda o: json.dumps(o, ensure_ascii=False, indent=1).replace("\n", "\r\n").encode("utf-8")
    if fmt(rows) != raw_pl:
        fail("PL_breakdown.json does not round-trip byte-for-byte (indent=1, CRLF)")
    if fmt(side) != raw_side:
        fail("PL_breakdown_provenance.json does not round-trip byte-for-byte (indent=1, CRLF)")
    mt = {PL: PL.stat().st_mtime_ns, SIDE: SIDE.stat().st_mtime_ns}
    by_key = {}
    for i, r in enumerate(rows):
        k = (r["원보험사코드"], r["항목번호"], r["공시분기"])
        if k in by_key:
            fail(f"duplicate master key {k}")
        by_key[k] = i

    # ---- 3. the plan with old-value guards -----------------------------------------
    OLD = {  # values found on 2026-10-10
        ("2024.4Q", 13): 7179.117, ("2024.4Q", 14): -12479.214,
        ("2025.4Q", 13): 1133.87, ("2025.4Q", 14): -14235.271,
    }
    plan = []   # (key, old, new)
    for q, vals in plan_val.items():
        for item, new in sorted(vals.items()):
            k = (CODE, item, q)
            if k not in by_key:
                fail(f"master row {k} does not exist")
            r = rows[by_key[k]]
            cur = r["값"]
            old = OLD.get((q, item))
            if old is None:
                if cur is not None and abs(cur - new) > 1e-9:
                    fail(f"old-value guard: {k} holds {cur}, expected a blank")
            else:
                if cur is not None and abs(cur - new) <= 1e-9:
                    print(f"already corrected: {k} = {cur}")
                    continue
                if cur is None or abs(cur - old) > 1e-9:
                    fail(f"old-value guard: {k} holds {cur}, expected {old}")
            if r.get("값_당분기") is not None:
                fail(f"{k} has a 값_당분기 {r.get('값_당분기')} (expected None for a Q4 leg)")
            if cur is not None and abs(cur - new) <= 1e-9:
                continue
            plan.append((k, cur, new))
    # items the gate / the closure also needs, read from the master (independent of the notes)
    for q in plan_val:
        g = lambda it: rows[by_key[(CODE, it, q)]]["값"]
        v = {it: (plan_val[q][it] if it in plan_val[q] else g(it)) for it in (2, 13, 14)}
        resid = v[2] + v[13] + v[14] + g(15) - g(16) - g(1)
        print(f"  master identity {q}: item2+13+14+15-16 - item1 = {resid:+.6f} 백만원 (item1={g(1)}, item15={g(15)}, item16={g(16)})")
        if abs(resid) > 0.01:
            fail(f"{q}: master identity does not close ({resid})")
        if abs(v[2] - (plan_val[q][3] + plan_val[q][8])) > 1e-9:
            fail(f"{q}: item2 != item3 + item8")
        # IS anchors vs the master's own items 1 and 16
        fy = [f for f, qq in QUARTER_OF.items() if qq == q][0]
        if abs(g(1) * 1e6 - isx[fy]["보험손익"][0]) > 1000 or abs(g(16) * 1e6 - isx[fy]["기타사업비용"][0]) > 1000:
            fail(f"{q}: master items 1/16 differ from the filing's income statement")

    print(f"\n{len(plan)} cell(s) to change in PL_breakdown.json:")
    for (c, it, q), old, new in plan:
        print(f"  {c} {q} item {it:>2} {ITEM_NAME[it]}: {old} -> {new}")

    # sidecar: income_statement block of the two DART quarters -> add items 2, 3, 8 to the raw_filing bucket
    side_plan = []
    for q in plan_val:
        for c in side["cells"]:
            if (c.get("company_code"), c.get("quarter"), c.get("item_block")) == (CODE, q, "income_statement"):
                buckets = [b for b in c["source_files"] if b.get("how") == "raw_filing" and "/dart/" in b["file"].replace("\\", "/")]
                if len(buckets) != 1 or c.get("source_id") != "DART":
                    fail(f"sidecar {q}: unexpected income_statement block {c}")
                add = [i for i in (2, 3, 8) if i not in buckets[0]["items"]]
                side_plan.append((c, buckets[0], add))
    for c, b, add in side_plan:
        print(f"  sidecar {c['quarter']} income_statement: raw_filing items {b['items']} + {add}; published_items {c['published_items']} -> {c['published_items'] + len(add)}")
    if not args.write:
        print("\ndry run -- nothing written.")
        return 0
    if not plan:
        print("nothing to do")
        return 0

    # ---- 4. write ------------------------------------------------------------------
    if BACKUP_DIR.exists():
        fail(f"backup dir {BACKUP_DIR} already exists")
    BACKUP_DIR.mkdir(parents=True)
    for p in (PL, SIDE):
        shutil.copyfile(p, BACKUP_DIR / p.name)
        if hashlib.sha256((BACKUP_DIR / p.name).read_bytes()).hexdigest() != hashlib.sha256(p.read_bytes()).hexdigest():
            fail("backup mismatch")
    new_rows = json.loads(raw_pl.decode("utf-8"))
    for (c, it, q), old, new in plan:
        new_rows[by_key[(c, it, q)]]["값"] = new
    new_side = json.loads(raw_side.decode("utf-8"))
    for c, b, add in side_plan:
        for cc in new_side["cells"]:
            if (cc.get("company_code"), cc.get("quarter"), cc.get("item_block")) == (c["company_code"], c["quarter"], c["item_block"]):
                for bb in cc["source_files"]:
                    if bb.get("how") == "raw_filing" and "/dart/" in bb["file"].replace("\\", "/"):
                        bb["items"] = sorted(set(bb["items"]) | set(add))
                cc["published_items"] = cc["published_items"] + len(add)
    new_side["merge_note_20261010"] = (
        "KR0004 2024.4Q/2025.4Q LOB 다리 정정(P3): 항목 2·3·8 채움(DART 주석 26-29 장기 열, 재보험 포함 순액) + 항목 13·14 부호·범위 정정"
        "(원수 PAA 만·부채부호 -> 재보험 포함 순액·손익부호). 재현: scripts/fix_20261010_pl_kr0004_lob_legs.py --write")
    for p, t in mt.items():
        if p.stat().st_mtime_ns != t:
            fail(f"{p.name} changed while preparing the fix -- concurrent session suspected")
    for p, obj in ((PL, new_rows), (SIDE, new_side)):
        tmp = p.with_name(p.name + ".tmp")
        tmp.write_bytes(fmt(obj))
        os.replace(tmp, p)
    # ---- 5. post-checks ------------------------------------------------------------
    after = json.loads(PL.read_bytes().decode("utf-8"))
    assert len(after) == len(rows)
    changed = [(a["원보험사코드"], a["항목번호"], a["공시분기"]) for a, b in zip(rows, after) if a != b]
    assert sorted(changed) == sorted(k for k, _o, _n in plan), (changed, plan)
    side_after = json.loads(SIDE.read_bytes().decode("utf-8"))
    n_side = sum(1 for a, b in zip(side["cells"], side_after["cells"]) if a != b)
    assert n_side == len(side_plan) and len(side["cells"]) == len(side_after["cells"]), (n_side, len(side_plan))
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nwrote {PL.name} ({len(changed)} cells changed, every other row identical), {SIDE.name} ({n_side} blocks changed), "
          f"backup {BACKUP_DIR.name}/, manifest {MANIFEST.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
