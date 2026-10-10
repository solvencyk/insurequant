#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cell-level PL loader for the management-disclosure granularity backfill (2026-10-11, parser/ifrs17).

Loads ONLY items 1 (보험손익), 16 (기타사업비용), 22 (세전이익), 23 (법인세), 24 (당기순이익) -- the five items the
data-contract gate §3d lets the DISCLOSURE lineage carry -- from data/_derived/bspl_granularity_20261011/pl_candidates
(status CAND = blank master cell + all checks passed).  Fills `값` of an existing null row or appends a new row; a cell that
already has a value is never touched (conflicts are only reported).  `값_당분기` follows the 2026-10-08 convention: Q1 = the
YTD value, Q2/Q3 = difference to the previous quarter only when that quarter is in THIS load set (same source), Q4 = None.
Lineage is appended to PL_breakdown_provenance.json (DISCLOSURE bucket, mixed blocks keep the non-DISCLOSURE bucket first).

Skips: the 15 item-1 cells held on 2026-10-09 (pl_bridge cannot close them: DART legs partial), KR0004 2025.3Q (new-entity
period), and anything passed with --exclude.  Dry-run is the default.  Never runs build_root_masters / build_pl.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_granularity_load_pl.py [--companies ..] [--items ..]
        [--exclude code|item|quarter,..] [--apply] [--round N]
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

import bspl_granularity_load_bs as L  # noqa: E402  (exact round-trip loader, safe_write, meta_from_kics, BACKUP)

MASTER = ROOT / "PL_breakdown.json"
SIDECAR = ROOT / "PL_breakdown_provenance.json"
CAND_DIR = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "pl_candidates"
MANIFEST = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "load_manifest_pl.json"
PARTS = ROOT / "data" / "_derived" / "pl_from_disclosure_parts"
HOLD_FILE = ROOT / "data" / "_derived" / "pl_followup_20261009.json"
ALLOWED = {1: "보험손익", 16: "기타사업비용", 22: "세전이익", 23: "법인세", 24: "당기순이익"}
EXCLUDE_CQ = {("KR0004", "2025.3Q"): "신설법인 제1기(2025-06-16~09-30) 누계 -- 연누계 계열이 아니다"}
# item-1 cells that make validate_master_tables pl_bridge fail (tried 2026-10-11: NEW-FAIL 롯데손해보험 2023.1Q leg-coverage,
# 삼성화재해상보험 2023.2Q dual) -- same class as the 15 cells held on 2026-10-09: DART LOB legs partial
HOLD_ITEM1_BRIDGE_20261011 = {"KR0003|1|2023.1Q", "KR0008|1|2023.2Q"}


def qkey(q):
    return int(q[:4]), int(q[5])


def prev_q(q):
    y, n = qkey(q)
    return None if n == 1 else f"{y}.{n - 1}Q"


def make_basis(c):
    how = c.get("how")
    kind = {"sum_pl": "요약 포괄손익계산서(총괄) 2-1", "pl_full": "감사받은 재무제표 포괄손익계산서"}.get(c.get("kind"), c.get("kind"))
    extra = {"audit_exact": "연말 감사보고서의 원 단위 값(요약표와 1.5억 이내 일치)",
             "R1": "R1(owner 2026-10-09 재보사 최신 공시 전년동기 칸 채택): " + str((c.get("note") or "")),
             "R1_tiebreak": "R1: " + str((c.get("note") or "")),
             "later_comparative": "이 분기 자체 공시에서 쓸 값이 없어 다음 해 같은 분기 공시의 전년동기 열 값을 채택",
             "own_summary": "해당 분기 공시의 당기 열"}.get(how, how)
    return (f"정기경영공시 {c.get('pdf_quarter')} {kind} p{c.get('page')} 라벨「{c.get('label')}」 단위 {c.get('unit')}, "
            f"정밀도 ±{c.get('prec_mn')}백만원. {extra}. (inbox/parser/20261011T0310Z bspl granularity)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--companies", default="")
    ap.add_argument("--items", default="")
    ap.add_argument("--exclude", default="")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--round", default="1")
    a = ap.parse_args()
    items = {int(x) for x in a.items.split(",") if x} or set(ALLOWED)
    if not items <= set(ALLOWED):
        raise SystemExit(f"ABORT: items outside the gate allowlist {sorted(ALLOWED)}: {sorted(items - set(ALLOWED))}")
    codes = [c for c in a.companies.split(",") if c] or sorted(p.stem for p in CAND_DIR.glob("KR*.json"))
    exclude = {x for x in a.exclude.split(",") if x}
    exclude |= HOLD_ITEM1_BRIDGE_20261011
    if HOLD_FILE.exists():
        for code, q, _v in json.loads(HOLD_FILE.read_text(encoding="utf-8")).get("hold_item1", []):
            exclude.add(f"{code}|1|{q}")

    rows, raw_m = L.load_json_exact(MASTER, 1, "\r\n")
    side, raw_s = L.load_json_exact(SIDECAR, 1, "\r\n")
    by_key = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r for r in rows}
    if len(by_key) != len(rows):
        raise SystemExit("ABORT: duplicate keys in PL master")
    meta = {}
    for r in rows:
        meta.setdefault(r["원보험사코드"], {k: r[k] for k in ("원수사명", "티커", "생손보여부")})
    kmeta = L.meta_from_kics()

    cand, skipped, conflicts = {}, Counter(), []
    for code in codes:
        p = CAND_DIR / f"{code}.json"
        if not p.exists():
            continue
        for c in json.loads(p.read_text(encoding="utf-8"))["candidates"]:
            key = f"{c['code']}|{c['item']}|{c['quarter']}"
            if c["status"] != "CAND" or c["item"] not in items:
                continue
            if key in exclude:
                skipped["excluded/held"] += 1
                continue
            if (c["code"], c["quarter"]) in EXCLUDE_CQ:
                skipped["cq excluded"] += 1
                continue
            r = by_key.get((c["code"], str(c["item"]), c["quarter"]))
            if r is not None and r.get("값") is not None:
                conflicts.append((key, r["값"], c["value_mn"]))
                continue
            cand[(c["code"], c["item"], c["quarter"])] = c

    # 값_당분기: same-source rule inside this load set
    setv = defaultdict(dict)
    for (code, it, q), c in cand.items():
        setv[(code, it)][q] = c["value_mn"]
    dangi = {}
    for (code, it, q), c in cand.items():
        pq = prev_q(q)
        if q.endswith("4Q"):
            dangi[(code, it, q)] = None
        elif pq is None:
            dangi[(code, it, q)] = round(c["value_mn"], 6)
        elif pq in setv[(code, it)]:
            dangi[(code, it, q)] = round(c["value_mn"] - setv[(code, it)][pq], 6)
        else:
            dangi[(code, it, q)] = None

    n_fill = sum(1 for k in cand if (k[0], str(k[1]), k[2]) in by_key)
    by_co = Counter(k[0] for k in cand)
    by_item = Counter(k[1] for k in cand)
    print(f"PL candidates NEW cells {len(cand)} (fill existing null rows {n_fill}, new rows {len(cand) - n_fill}); "
          f"existing-value conflicts reported {len(conflicts)}; skipped {dict(skipped)}")
    print("by company:", dict(sorted(by_co.items())))
    print("by item:", dict(sorted(by_item.items())))
    for k, m, v in conflicts[:8]:
        print("  CONFLICT (not touched)", k, "master", m, "disclosure", v)
    # identity inside the load (reporting): 24 = 22 - 23
    grp = defaultdict(dict)
    for (code, it, q), c in cand.items():
        grp[(code, q)][it] = c["value_mn"]
    bad = [(k, g) for k, g in grp.items() if all(i in g for i in (22, 23, 24)) and abs(g[22] - g[23] - g[24]) > 150.0]
    print(f"identity 24 = 22 - 23 inside the set: {sum(1 for g in grp.values() if all(i in g for i in (22, 23, 24)))} groups, "
          f"{len(bad)} outside 1.5억")
    if not a.apply:
        print("dry-run -- nothing written")
        return
    if bad:
        raise SystemExit(f"ABORT: identity failures {bad[:3]}")

    rd = L.BACKUP / f"pl_round{a.round}"
    rd.mkdir(parents=True, exist_ok=True)
    shutil.copy2(MASTER, rd / MASTER.name)
    shutil.copy2(SIDECAR, rd / SIDECAR.name)
    snapshot = {k: json.dumps(v, ensure_ascii=False, sort_keys=True) for k, v in by_key.items()}
    authorized = set()
    new_rows = []
    for (code, it, q) in sorted(cand, key=lambda k: (k[0], qkey(k[2]), k[1])):
        c = cand[(code, it, q)]
        v = round(c["value_mn"], 6)
        r = by_key.get((code, str(it), q))
        if r is not None:
            r["값"], r["값_당분기"] = v, dangi[(code, it, q)]
            authorized.add((code, str(it), q))
        else:
            m = meta.get(code) or {"원수사명": kmeta[code][0], "티커": kmeta[code][1], "생손보여부": kmeta[code][2]}
            new_rows.append({"원보험사코드": code, "원수사명": m["원수사명"], "티커": m["티커"], "생손보여부": m["생손보여부"],
                             "항목번호": it, "항목명": ALLOWED[it], "공시분기": q, "값": v, "값_당분기": dangi[(code, it, q)]})
    changed = [k for k, s in snapshot.items() if json.dumps(by_key[k], ensure_ascii=False, sort_keys=True) != s]
    if set(changed) != authorized:
        raise SystemExit(f"ABORT: unauthorised/missing changes {sorted(set(changed) ^ authorized)[:5]}")
    out_rows = rows + new_rows
    if len({(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]) for r in out_rows}) != len(out_rows):
        raise SystemExit("ABORT: duplicate keys after append")

    # ---- sidecar: DISCLOSURE bucket per (company, quarter, file) ----
    side_idx = {(x["company_code"], x["quarter"], x["item_block"]): x for x in side["cells"]}
    pdf_items = defaultdict(lambda: defaultdict(list))        # (code, q) -> pdf -> items
    for (code, it, q), c in cand.items():
        pdf_items[(code, q)][c["pdf"]].append(it)
    n_new = n_patch = 0
    for (code, q), per_pdf in sorted(pdf_items.items(), key=lambda kv: (kv[0][0], qkey(kv[0][1]))):
        buckets = [{"file": f, "how": "disclosure_summary_pl", "items": sorted(its)} for f, its in sorted(per_pdf.items())]
        n_items = sum(len(b["items"]) for b in buckets)
        key = (code, q, "income_statement")
        cell = side_idx.get(key)
        if cell is None:
            top = max(buckets, key=lambda b: len(b["items"]))
            side["cells"].append({"company_code": code, "quarter": q, "item_block": "income_statement", "source_id": "DISCLOSURE",
                                  "source_file": top["file"], "published_items": n_items, "schema_items": 24,
                                  "source_files": sorted(buckets, key=lambda b: (-len(b["items"]), b["file"])),
                                  "resolution": "disclosure_summary_pl"})
            n_new += 1
            continue
        for b in buckets:
            for ob in cell.get("source_files") or []:
                if ob["file"] == b["file"] and ob.get("how") == b["how"]:
                    ob["items"] = sorted(set(ob["items"]) | set(b["items"]))
                    break
            else:
                cell.setdefault("source_files", []).append(b)
        cell["published_items"] = cell.get("published_items", 0) + n_items
        cell["source_files"].sort(key=lambda b: (1 if str(b["file"]).startswith("data/disclosure/") else 0, -len(b["items"]),
                                                  0 if str(b["file"]).startswith("data/dart/") else 1, str(b["file"])))
        top = cell["source_files"][0]
        cell["source_file"] = top["file"]
        cell["resolution"] = top["how"]
        f = str(top["file"])
        cell["source_id"] = "DART" if f.startswith("data/dart/") else "DISCLOSURE" if f.startswith("data/disclosure/") else "OWNER_GOLD"
        cell.pop("unresolved_reason", None)
        n_patch += 1
    side["merge_note_20261011"] = (f"경영공시 BS·PL 세부(granularity) 백필(inbox/parser/20261011T0310Z) PL 라운드 {a.round}: "
                                   f"{len(cand)}칸(허용 5항목 1·16·22·23·24) DISCLOSURE append/patch. as_of_date 는 싣지 않았다. "
                                   f"재현: scripts/bspl_granularity_pl_candidates.py + scripts/bspl_granularity_load_pl.py --apply")

    # parts (lineage per cell, re-mergeable)
    PARTS.mkdir(parents=True, exist_ok=True)
    part_cells = defaultdict(dict)
    for (code, it, q), c in cand.items():
        part_cells[code][f"{code}|{it}|{q}"] = {"값": round(c["value_mn"], 6), "pdf": c["pdf"], "page": c.get("page"),
                                                  "sha256": c.get("sha256"), "축척": f"{c.get('unit')} -> 백만원",
                                                  "방법": f"granularity:{c.get('kind')}:{c.get('how')}", "근거": make_basis(c)}
    for code, cells in part_cells.items():
        pp = PARTS / f"{code}_agent_gran.json"
        prev = json.loads(pp.read_text(encoding="utf-8")) if pp.exists() else {"cells": {}}
        prev["cells"].update(cells)
        pp.write_text(json.dumps(prev, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    for p, raw in ((MASTER, raw_m), (SIDECAR, raw_s)):
        if p.read_bytes() != raw:
            raise SystemExit(f"ABORT: {p.name} changed since it was read (concurrent session?) -- nothing written to it")
    L.safe_write(SIDECAR, L.dumps(side, 1, "\r\n"))
    L.safe_write(MASTER, L.dumps(out_rows, 1, "\r\n"))
    chk = json.loads(MASTER.read_bytes().decode("utf-8"))
    cidx = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r for r in chk}
    badx = [k for k, s in snapshot.items() if k not in authorized and json.dumps(cidx.get(k), ensure_ascii=False, sort_keys=True) != s]
    if badx or len(chk) != len(rows) + len(new_rows):
        raise SystemExit(f"VERIFY FAILED: {badx[:5]} rows {len(chk)} expected {len(rows) + len(new_rows)}")
    man = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {"rounds": []}
    man["rounds"].append({"round": a.round, "stamp": time.strftime("%Y-%m-%d %H:%M"),
                          "added": [f"{k[0]}|{k[1]}|{k[2]}" for k in cand], "filled_existing": [list(k) for k in sorted(authorized)],
                          "rows_before": len(rows), "rows_after": len(chk), "sidecar_new": n_new, "sidecar_patched": n_patch,
                          "master_sha256_after": L.sha_bytes(MASTER.read_bytes())})
    MANIFEST.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"APPLIED: {len(cand)} cells (+{len(new_rows)} rows, {len(authorized)} null rows filled); sidecar +{n_new} new blocks, "
          f"{n_patch} patched; all {len(snapshot)} pre-existing rows verified unchanged except the {len(authorized)} filled")


if __name__ == "__main__":
    main()
