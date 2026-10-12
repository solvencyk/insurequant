# -*- coding: utf-8 -*-
"""Apply the Chubb (KR0100) D2 restatement to insurance_liability_portfolio.json items 14/15 (nine mid-quarters) and its provenance sidecar.

Ticket : inbox/parser/20261012T1020Z__orchestrator__MULTI_2023.4Q-2026.2Q__ifrs17_owner_followups_20261012.md item 4 (owner decision (7)).
Spec   : data/_derived/ifrs17_owner_followups_20261012/chubb_d2_spec_ilp.json  (staged by scripts/extract_chubb_d2_20261012.py from the disclosure PDFs)
What   : item 15 (보험계약부채_합계) := D1 + SA and item 14 (잔여보장요소_합계) := LRC(general account) + SA, with D1 = `1. 보험계약부채`, SA = `IV. 특별계정부채` of the same
         balance sheet.  Items 10~13 (incurred claims) do not change.  Provenance cell of each quarter: items_eok 14/15, checks (bs20_eok, filing_bs_eok,
         ratio_filing_bs), flags (+ `general_plus_special_account_basis`, `general_account_basis` removed), evidence/note, the replaced values
         (`general_account_values_eok`) and the components; top level: one `value_corrections` record per cell + one `backfills` record.

Guards : both files must round-trip byte-exactly (master: indent 2 + CRLF, no trailing newline; provenance: detected), every target value must still be the spec's
         `old`.  Backup first, atomic replace, re-read, row-by-row / cell-by-cell proof that nothing else moved.  The pre-state of every touched provenance field is
         kept in data/_derived/ifrs17_owner_followups_20261012/chubb_d2_ilp_manifest.json so that --revert is exact.

  default            dry run
  --apply            write
  --revert --apply   put the old values back (only cells that still hold the new values)

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/apply_chubb_ilp_d2_20261012.py [--apply] [--revert]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "data" / "_derived" / "ifrs17_owner_followups_20261012"
BACKUP = ROOT / "data" / "_derived" / "ifrs17_owner_followups_backup_20261012"
MASTER = ROOT / "insurance_liability_portfolio.json"
PROV = ROOT / "insurance_liability_portfolio_provenance.json"
SPEC = WORK / "chubb_d2_spec_ilp.json"
MANIFEST = WORK / "chubb_d2_ilp_manifest.json"
CODE = "KR0100"
TICKET = "inbox/parser/20261012T1020Z__orchestrator__MULTI_2023.4Q-2026.2Q__ifrs17_owner_followups_20261012.md"
EMITTER = "scripts/apply_chubb_ilp_d2_20261012.py"
NEW_FLAG, OLD_FLAG = "general_plus_special_account_basis", "general_account_basis"
# NOTE: the key `original_basis` must NOT be used here -- scripts/build_master_xlsx.py labels every provenance cell that has it a 소급재작성 (restated) cell
ADDED_KEYS = ("general_account_values_eok", "d2_note", "components_won", "d2_applied_at")
sys.stdout.reconfigure(encoding="utf-8")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def dump_master(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, indent=2).replace("\n", "\r\n").encode("utf-8")


def detect_prov(raw: bytes, obj):
    """the provenance sidecar's exact serialisation (indent 1 or 2, LF or CRLF, trailing newline or not)"""
    for indent in (1, 2):
        for nl in ("\n", "\r\n"):
            for tail in (b"", nl.encode()):
                if json.dumps(obj, ensure_ascii=False, indent=indent).replace("\n", nl).encode("utf-8") + tail == raw:
                    return indent, nl, tail
    raise SystemExit("ABORT: the provenance sidecar does not round-trip byte-exactly with indent 1/2, LF/CRLF")


def dump_prov(obj, fmt) -> bytes:
    indent, nl, tail = fmt
    return json.dumps(obj, ensure_ascii=False, indent=indent).replace("\n", nl).encode("utf-8") + tail


def replace_retry(tmp: Path, path: Path, tries: int = 40, wait: float = 3.0) -> None:
    """os.replace fails with WinError 5 while another process has the target open (a gate run reading it); wait and retry, never half-write"""
    for k in range(tries):
        try:
            tmp.replace(path)
            return
        except PermissionError:
            time.sleep(wait)
    raise SystemExit(f"ABORT: could not replace {path.name} after {tries} tries (file locked) -- the temp file {tmp.name} is left for inspection")


def same(a, b) -> bool:
    return a is not None and b is not None and abs(float(a) - float(b)) < 1e-9


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    a = ap.parse_args()
    spec = json.loads(SPEC.read_text(encoding="utf-8"))["cells"]
    ev = json.loads((WORK / "chubb_d2_evidence.json").read_text(encoding="utf-8"))["quarters"]
    if a.revert:
        if not MANIFEST.exists():
            raise SystemExit("ABORT: no manifest -- nothing to revert")
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    else:
        if MANIFEST.exists():
            raise SystemExit("ABORT: chubb_d2_ilp_manifest.json exists -- already applied (use --revert first)")
        manifest = {}

    raw_m = MASTER.read_bytes()
    rows = json.loads(raw_m.decode("utf-8"))
    if dump_master(rows) != raw_m:
        raise SystemExit("ABORT: insurance_liability_portfolio.json does not round-trip (indent 2, CRLF, no trailing newline)")
    raw_p = PROV.read_bytes()
    prov = json.loads(raw_p.decode("utf-8"))
    fmt = detect_prov(raw_p, prov)
    idx = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): i for i, r in enumerate(rows)}
    pidx = {(c["company_code"], c["quarter"]): i for i, c in enumerate(prov["cells"])}

    plan = []
    for c in spec:
        q = c["quarter"]
        for item, key in ((14, "item14"), (15, "item15")):
            i = idx[(CODE, q, item)]
            frm, to = (c[key]["new"], c[key]["old"]) if a.revert else (c[key]["old"], c[key]["new"])
            if not same(rows[i]["값"], frm):
                raise SystemExit(f"ABORT: master {CODE} {q} item {item} holds {rows[i]['값']}, expected {frm}")
            plan.append((i, frm, to))
        pc = prov["cells"][pidx[(CODE, q)]]
        for item, key in ((14, "item14"), (15, "item15")):
            frm = c[key]["new"] if a.revert else c[key]["old"]
            if not same(pc["items_eok"][str(item)], frm):
                raise SystemExit(f"ABORT: provenance {CODE} {q} items_eok[{item}] = {pc['items_eok'][str(item)]}, expected {frm}")
        print(f"{CODE} {q}: item14 {c['item14']['old']} -> {c['item14']['new']}   item15 {c['item15']['old']} -> {c['item15']['new']}   "
              f"(D1 {c['D1_won']:,} + SA {c['SA_won']:,} won; LRC {c['LRC_won']:,}; LIC {c['LIC_won']:,})")
    print(f"master rows {len(rows)}, provenance cells {len(prov['cells'])}: {len(plan)} master values in {len(spec)} cells{'  [REVERT]' if a.revert else ''}")
    if not a.apply:
        print("(dry run -- nothing written; add --apply)")
        return 0

    BACKUP.mkdir(parents=True, exist_ok=True)
    tag = "pre_revert_chubb_d2" if a.revert else "pre_chubb_d2"
    shutil.copyfile(MASTER, BACKUP / f"insurance_liability_portfolio.json.{tag}")
    shutil.copyfile(PROV, BACKUP / f"insurance_liability_portfolio_provenance.json.{tag}")
    before_rows = json.loads(json.dumps(rows))
    before_prov = json.loads(json.dumps(prov))
    for i, _, to in plan:
        rows[i]["값"] = to

    stamp = time.strftime("%Y%m%dT%H%MZ", time.gmtime())
    for c in spec:
        q = c["quarter"]
        e = ev[q]
        pc = prov["cells"][pidx[(CODE, q)]]
        d1, sa = c["D1_won"], c["SA_won"]
        if a.revert:
            m = manifest[q]
            pc["items_eok"]["14"], pc["items_eok"]["15"] = c["item14"]["old"], c["item15"]["old"]
            pc["flags"], pc["checks"] = m["flags"], m["checks"]
            for k in ("evidence", "note"):
                if m[k] is None and k in pc and m.get(k + "_absent"):
                    pc.pop(k)
                else:
                    pc[k] = m[k]
            for k in ADDED_KEYS:
                pc.pop(k, None)
            continue
        manifest[q] = {"flags": json.loads(json.dumps(pc["flags"])), "checks": json.loads(json.dumps(pc["checks"])),
                       "evidence": pc.get("evidence"), "evidence_absent": "evidence" not in pc, "note": pc.get("note"), "note_absent": "note" not in pc}
        pc["general_account_values_eok"] = {"14": c["item14"]["old"], "15": c["item15"]["old"]}
        pc["items_eok"]["14"], pc["items_eok"]["15"] = c["item14"]["new"], c["item15"]["new"]
        pc["flags"] = [f for f in pc["flags"] if f != OLD_FLAG] + [NEW_FLAG]
        pc["components_won"] = {"general_account_보험계약부채_D1": d1, "general_account_잔여보장요소": c["LRC_won"], "general_account_발생사고요소": c["LIC_won"],
                                "특별계정부채_SA": sa, "D2_D1_plus_SA": d1 + sa}
        chk = pc["checks"]
        if chk.get("bs20_eok") is not None:
            chk["bs20_eok"] = c["item15"]["new"]          # IFRS17_BS item 20 moves to D2 in the same round (scripts/apply_ifrs17_bs_fix_20261012.py)
        chk["filing_bs_eok"] = c["item15"]["new"]
        chk["ratio_filing_bs"] = 1.0
        chk["filing_bs_basis"] = "D2 = 일반계정 1.보험계약부채 + IV.특별계정부채 (K-IFRS 서식 「보험계약부채」와 같은 정의)"
        pc["d2_applied_at"] = stamp
        pc["evidence"] = (f"업무보고서식 재무상태표 PDF p{e['D1_pages'][0]} 1. 보험계약부채 {d1:,}원 (= 가. 잔여보장요소 {c['LRC_won']:,} + 나. 발생사고요소 {c['LIC_won']:,}) + "
                          f"PDF p{e['SA_pages'][0]} IV. 특별계정부채 {sa:,}원 = {d1 + sa:,}원 (D2)")
        pc["d2_note"] = ("owner 2026-10-12 결정 ⑦(정의 통일): 항목 14·15 를 특별계정 변액 보험계약부채를 포함한 기준(D2)으로 다시 계산했다. 연말 DART 셀(2023.4Q·2024.4Q·2025.4Q)과 "
                            "2026 K-IFRS 서식의 「보험계약부채」가 같은 정의다. 발생사고요소(항목 10~13)는 특별계정에 없다: 일반계정 LIC 가 연말 DART LIC 와 같다"
                            "(2023.12.31 222.82 대 222.83, 2024.12.31 250.05 대 250.05). D2 대 연말 K-IFRS 라인 차 -0.110 %(2023.4Q) · -0.074 %(2024.4Q). "
                            "정정 전(일반계정) 값은 general_account_values_eok.")
        pc["note"] = ("업무보고서식 재무상태표 「1. 보험계약부채(가. 잔여보장요소 · 나. 발생사고요소) + IV. 특별계정부채」(원): items 14 and 15 contain the special-account 변액 "
                      "liabilities like the DART year-end cells and the 2026 K-IFRS 서식; items 10-13 (LIC) are the general-account values, which equal the DART year-end LIC")
        prov["value_corrections"].append({
            "company_code": CODE, "quarter": q,
            "items": {"14": {"old": c["item14"]["old"], "new": c["item14"]["new"]}, "15": {"old": c["item15"]["old"], "new": c["item15"]["new"]}},
            "source_file": c["source_file"].replace("\\", "/"), "page": {"D1": e["D1_pages"], "SA": e["SA_pages"]},
            "printed_row": f"1. 보험계약부채 {d1:,} + IV. 특별계정부채 {sa:,}",
            "printed_numbers": [d1, sa, c["LRC_won"], c["LIC_won"]],
            "reason": "owner 2026-10-12 decision (7): unify the definition of items 14/15 with the year-end cells (special account included, D2 = D1 + SA); LIC items 10-13 unchanged",
            "ticket": TICKET, "at": stamp, "emitted_by": EMITTER})
    if not a.revert:
        prov["backfills"].append({"stage": "chubb_d2_20261012", "at": stamp, "emitted_by": EMITTER, "ticket": TICKET,
                                  "note": "Chubb (KR0100) items 14/15 of nine mid-quarters (2023.1Q~2025.3Q) restated from the general-account basis to D2 (= + 특별계정부채); "
                                          "spec data/_derived/ifrs17_owner_followups_20261012/chubb_d2_spec_ilp.json; the same round moves IFRS17_BS item 20 of the six quarters that have one"})
    else:
        prov["value_corrections"] = [r for r in prov["value_corrections"] if r.get("emitted_by") != EMITTER]
        prov["backfills"] = [r for r in prov["backfills"] if r.get("emitted_by") != EMITTER]

    new_m, new_p = dump_master(rows), dump_prov(prov, fmt)
    if MASTER.read_bytes() != raw_m or PROV.read_bytes() != raw_p:
        raise SystemExit("ABORT: a master changed while planning -- nothing written")
    for path, data in ((PROV, new_p), (MASTER, new_m)):
        tmp = path.with_suffix(".json.tmp_chubbd2")
        tmp.write_bytes(data)
        replace_retry(tmp, path)

    # ---- proof
    raw_m2, raw_p2 = MASTER.read_bytes(), PROV.read_bytes()
    rows2 = json.loads(raw_m2.decode("utf-8"))
    prov2 = json.loads(raw_p2.decode("utf-8"))
    assert dump_master(rows2) == raw_m2 and dump_prov(prov2, fmt) == raw_p2, "written files do not round-trip"
    assert len(rows2) == len(before_rows)
    target = {i for i, _, _ in plan}
    moved = 0
    for i, (b, r) in enumerate(zip(before_rows, rows2)):
        if i in target:
            assert {k: v for k, v in b.items() if k != "값"} == {k: v for k, v in r.items() if k != "값"}
            moved += 0 if same(b["값"], r["값"]) else 1
        else:
            assert b == r, f"non-target master row changed: {b}"
    assert moved == len(plan), (moved, len(plan))
    tq = {c["quarter"] for c in spec}
    assert len(prov2["cells"]) == len(before_prov["cells"])
    for b, c in zip(before_prov["cells"], prov2["cells"]):
        if b["company_code"] == CODE and b["quarter"] in tq:
            continue
        assert b == c, f"non-target provenance cell changed: {b['company_code']} {b['quarter']}"
    for k in before_prov:
        if k not in ("cells", "value_corrections", "backfills"):
            assert before_prov[k] == prov2[k], f"provenance top-level {k} changed"
    if a.revert:
        MANIFEST.rename(MANIFEST.with_name("chubb_d2_ilp_manifest.reverted.json"))
    else:
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"{'reverted' if a.revert else 'written'}: {moved} master values ({len(spec)} cells), provenance cells {len(spec)}; all other master rows and provenance cells identical; "
          f"sha256 master {sha(raw_m)[:12]} -> {sha(raw_m2)[:12]}, provenance {sha(raw_p)[:12]} -> {sha(raw_p2)[:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
