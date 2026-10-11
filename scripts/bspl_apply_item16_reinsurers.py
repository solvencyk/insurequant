#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 5 (parser/ifrs17, inbox/parser/20261011T1730Z): load 7 PL item 16 (기타사업비용) cells that the reinsurer
경영공시 2-1 summary page prints but the master leaves blank.  Cell-level, old-value guard (old must be ABSENT), backup, sidecar update.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_item16_reinsurers.py [--apply]

Values are YTD in 백만원 (printed 억원 x 100; KR1103 2024.1Q is printed in 백만원).  Sign = as printed, which is the sign the bridge
`보험손익 = 보험수익 - 보험서비스비용 + 재보험수익 - 재보험서비스비용 - 기타사업비용` needs (proof in data/_derived/bspl_apply_20261011/item16/spec_item16.json).
값_당분기 of a new row = rule (Q1 = YTD, else YTD - previous quarter if present; a Q4 row = None like every sibling Q4 row of the DISCLOSURE lineage).
The next non-Q4 row of the same company whose previous quarter just became available gets its derived 값_당분기 (None -> value).
Never touches 값 of an existing row.
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import bspl_granularity_load_bs as L  # noqa: E402

MASTER = ROOT / "PL_breakdown.json"
SIDECAR = ROOT / "PL_breakdown_provenance.json"
SPEC = ROOT / "data/_derived/bspl_apply_20261011/item16/spec_item16.json"
BACKUP = ROOT / "data/_derived/bspl_apply_backup_20261011/item16"
ITEM = "16"


def prev_q(q):
    y, n = int(q[:4]), int(q[5])
    return None if n == 1 else f"{y}.{n - 1}Q"


def next_q(q):
    y, n = int(q[:4]), int(q[5])
    return None if n == 4 else f"{y}.{n + 1}Q"


def main():
    apply = "--apply" in sys.argv
    spec = json.loads(SPEC.read_text(encoding="utf-8"))["cells"]
    rows, raw_m = L.load_json_exact(MASTER, 1, "\r\n")
    side, raw_s = L.load_json_exact(SIDECAR, 1, "\r\n")
    by = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r for r in rows}
    ytd = {}
    for (c, it, q), r in by.items():
        if it == ITEM:
            ytd.setdefault(c, {})[q] = r.get("값")
    for s in spec:
        if (s["company"], ITEM, s["quarter"]) in by:
            raise SystemExit(f"ABORT: {s['company']} {s['quarter']} item 16 already in master")
    new_ytd = {c: dict(v) for c, v in ytd.items()}
    for s in spec:
        new_ytd.setdefault(s["company"], {})[s["quarter"]] = s["value"]

    def dangi(c, q):
        cur = new_ytd[c].get(q)
        if cur is None or q.endswith("4Q"):
            return None
        p = prev_q(q)
        if p is None:
            return cur
        pv = new_ytd[c].get(p)
        return None if pv is None else round(cur - pv, 6)

    dchg = {}
    for s in spec:
        c, q = s["company"], s["quarter"]
        nq = next_q(q)
        if nq and (c, ITEM, nq) in by and not nq.endswith("4Q"):
            r = by[(c, ITEM, nq)]
            if r.get("값_당분기") is not None:
                raise SystemExit(f"ABORT: {c} {nq} 값_당분기 {r.get('값_당분기')} is not None while the previous quarter was blank")
            dchg[(c, nq)] = (r.get("값_당분기"), dangi(c, nq))
    meta = {}
    for r in rows:
        meta.setdefault(r["원보험사코드"], r)
    print("NEW rows:")
    for s in spec:
        print(f"  {s['company']} {s['quarter']} 값 {s['value']:,.1f} 값_당분기 {dangi(s['company'], s['quarter'])}")
    print("derived 값_당분기 on existing rows:", {f"{k[0]} {k[1]}": v for k, v in dchg.items()})
    if not apply:
        print("dry-run")
        return

    BACKUP.mkdir(parents=True, exist_ok=True)
    shutil.copy2(MASTER, BACKUP / MASTER.name)
    shutil.copy2(SIDECAR, BACKUP / SIDECAR.name)
    snap = {k: json.dumps(v, ensure_ascii=False, sort_keys=True) for k, v in by.items()}
    added = []
    for s in spec:
        c, q = s["company"], s["quarter"]
        m = meta[c]
        added.append({"원보험사코드": c, "원수사명": m["원수사명"], "티커": m["티커"], "생손보여부": m["생손보여부"],
                      "항목번호": 16, "항목명": "기타사업비용", "공시분기": q, "값": s["value"], "값_당분기": dangi(c, q)})
    for (c, nq), (_o, nd) in dchg.items():
        by[(c, ITEM, nq)]["값_당분기"] = nd

    blocks = {(b["company_code"], b["quarter"], b["item_block"]): b for b in side["cells"]}
    for s in spec:
        b = blocks[(s["company"], s["quarter"], "income_statement")]
        if b.get("resolution") != "disclosure_summary_pl":
            raise SystemExit(f"ABORT: unexpected sidecar block {s['company']} {s['quarter']}")
        ent = next((e for e in b["source_files"] if e["file"] == s["source_file"]), None)
        if ent is None:
            b["source_files"].append({"file": s["source_file"], "how": "disclosure_summary_pl", "items": [16]})
        else:
            if 16 in ent["items"]:
                raise SystemExit("ABORT: sidecar already lists 16")
            ent["items"] = sorted(ent["items"] + [16])
        b["published_items"] = b["published_items"] + 1
    stamp = time.strftime("%Y-%m-%d %H:%M")
    side["merge_note_20261011_item16_reinsurers"] = (
        f"round-5 PL 항목 16 기타사업비용(inbox/parser/20261011T1730Z, {stamp}): 재보사 7칸 신규 적재"
        f"(KR1101 2023.1Q·2Q·3Q·2024.1Q, KR1103 2023.3Q·2024.1Q·2025.4Q) -- 경영공시 2-1 요약 포괄손익계산서의 (기타사업비용) 인쇄값, "
        f"보험손익 다리(보험수익-보험서비스비용+재보험수익-재보험서비스비용-기타사업비용)로 부호·단위 검산. "
        f"해당 7개 블록의 published_items +1 · source_files items 에 16 추가. "
        f"근거·재현 data/_derived/bspl_apply_20261011/item16/spec_item16.json · scripts/bspl_apply_item16_reinsurers.py")

    for p, raw in ((MASTER, raw_m), (SIDECAR, raw_s)):
        if p.read_bytes() != raw:
            raise SystemExit(f"ABORT: {p.name} changed since read -- nothing written")
    L.safe_write(SIDECAR, L.dumps(side, 1, "\r\n"))
    L.safe_write(MASTER, L.dumps(rows + added, 1, "\r\n"))

    chk = json.loads(MASTER.read_bytes().decode("utf-8"))
    ci = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r for r in chk}
    allowed = {(c, ITEM, q) for c, q in dchg}
    bad = [k for k, v in snap.items() if k not in allowed and json.dumps(ci.get(k), ensure_ascii=False, sort_keys=True) != v]
    if bad or len(chk) != len(rows) + len(added) or len(ci) != len(chk):
        raise SystemExit(f"VERIFY FAILED {bad[:5]} rows {len(chk)}")
    for k in allowed:
        o, n = json.loads(snap[k]), ci[k]
        for f in set(o) | set(n):
            if f != "값_당분기" and o.get(f) != n.get(f):
                raise SystemExit(f"VERIFY FAILED field {f} of {k}")
    print(f"APPLIED: +{len(added)} rows (rows {len(rows)} -> {len(chk)}); derived 값_당분기 on {len(dchg)} existing rows; "
          f"all other {len(snap) - len(dchg)} rows identical")


if __name__ == "__main__":
    main()
