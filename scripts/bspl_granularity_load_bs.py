#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cell-level BS loader for the management-disclosure granularity backfill (2026-10-11, parser/ifrs17).

Writes ONLY new keys (company|item|quarter that are absent from IFRS17_BS.json):
  1. data/_derived/bs_from_disclosure_parts/<KR>_agent_gran.json   (part file with per-cell lineage, re-mergeable)
  2. data/_derived/bs_from_disclosure.json                          (lineage sidecar: new keys only)
  3. data/dart/viz/bs_manual_overrides.json                         (overlay the builder re-applies: new keys only)
  4. IFRS17_BS.json                                                 (rows appended in builder sort order)
Existing keys/rows are never modified; any difference between an existing master value and a candidate is only reported.
Never runs build_ifrs17_bs.py / build_root_masters.py.  Re-reads the files immediately before writing and aborts if they
changed since the first read (concurrent session).  Verifies after writing that every pre-existing row is unchanged.

Run (dry-run is the default):
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_granularity_load_bs.py --companies KR0050
  ... --apply [--status CAND,CAND_UNTESTED] [--items 11,12] [--manual path.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")

MASTER = ROOT / "IFRS17_BS.json"
OVERRIDES = ROOT / "data" / "dart" / "viz" / "bs_manual_overrides.json"
SIDECAR = ROOT / "data" / "_derived" / "bs_from_disclosure.json"
PARTS = ROOT / "data" / "_derived" / "bs_from_disclosure_parts"
CAND_DIR = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "candidates"
BACKUP = ROOT / "data" / "_derived" / "bspl_granularity_backup_20261011"
MANIFEST = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "load_manifest_bs.json"

SECTION = {1: "자산", 2: "부채", 3: "자본", 4: "자본", 5: "준비금", 6: "준비금", 7: "준비금", 8: "준비금",
           10: "자산", 11: "자산", 12: "자산", 13: "자산", 14: "자산", 15: "자산",
           20: "부채", 21: "부채", 22: "부채", 23: "부채", 24: "부채", 30: "자본", 31: "자본"}
LABELS = {1: "자산총계", 2: "부채총계", 3: "자본총계", 4: "기타포괄손익 누계액", 5: "해약환급금준비금 적립액",
          6: "비상위험준비금 적립액", 7: "대손준비금 적립액", 8: "보증준비금 적립액", 10: "현금및현금성자산",
          11: "당기손익-공정가치측정금융자산", 12: "기타포괄손익-공정가치측정금융자산", 13: "상각후원가측정금융자산",
          14: "재보험계약자산", 15: "유형자산", 20: "보험계약부채", 21: "재보험계약부채", 22: "투자계약부채",
          23: "차입부채", 24: "기타부채", 30: "자본금", 31: "이익잉여금"}
KIND_TITLE = {"sum_bs": "요약 재무상태표(총괄)", "equity": "B/S상 자기자본", "bs_full": "재무상태표(8-1)"}


def safe_write(path: Path, data: bytes, tries: int = 8):
    """atomic replace with retries (a transient Windows file lock raised OSError 22 once, mid-write, on 2026-10-11)"""
    last = None
    for i in range(tries):
        tmp = path.with_name(path.name + ".tmp_gran")
        try:
            tmp.write_bytes(data)
            os.replace(tmp, path)
            return
        except OSError as e:
            last = e
            time.sleep(0.75 * (i + 1))
    raise SystemExit(f"ABORT: could not write {path}: {last!r}")


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def dumps(obj, indent, nl):
    s = json.dumps(obj, ensure_ascii=False, indent=indent)
    return (s.replace("\n", "\r\n") if nl == "\r\n" else s).encode("utf-8")


def load_json_exact(path: Path, indent, nl):
    raw = path.read_bytes()
    obj = json.loads(raw.decode("utf-8"))
    if dumps(obj, indent, nl) != raw:
        raise SystemExit(f"ABORT: {path.name} does not round-trip byte-exactly (indent={indent}, nl={nl!r}); refusing to rewrite")
    return obj, raw


def meta_from_kics():
    meta = {}
    for r in json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8")):
        c = r.get("원보험사코드")
        if c and c not in meta:
            meta[c] = (r.get("원수사명"), r.get("티커"), r.get("생손보여부"))
    return meta


def make_basis(c: dict) -> str:
    kind = c.get("kind")
    unit = c.get("unit")
    tab = KIND_TITLE.get(kind, kind)
    calib = c.get("calib")
    cal_txt = {"accepted": "보정 통과(마스터 DART/owner 앵커와 동일 라벨→항목 매핑 재현)",
               "group_ok": "그룹 보정(책임준비금 = 항목 20+21+22 가 Q4 앵커에서 닫힘)",
               "untested_ok": "앵커 없음 -- 단일개념 라벨 미검증 통과(표 항등식 닫힘)",
               "audit_anchor": "감사보고서(연말 K-IFRS 재무제표)를 앵커로 한 보정 통과",
               "manual": "육안 판독(렌더링) + 표 항등식 닫힘"}.get(calib, str(calib))
    if c.get("basis"):
        return c["basis"]
    r1 = c.get("r1")
    r1_txt = ""
    if r1 and r1.get("own_value_mn") is None:
        r1_txt = (f" R1(owner 2026-10-09 재보사 최신 공시 전기·전년동기 칸 채택): 이 분기 자체 공시에서는 쓸 수 있는 값이 없거나 "
                  f"재작성돼, 최신 공시 {r1.get('from')} 의 전년동기 열 값을 채택.")
    elif r1:
        r1_txt = (f" R1(owner 2026-10-09 재보사 최신 공시 전기 칸 채택): 최신 공시 {r1.get('from')} 의 전기말 열 값을 채택"
                  f"(원 공시 {r1.get('own_pdf_quarter')} 당기 열 값 {r1.get('own_value_mn')} 백만원은 재작성으로 대체).")
    src = f"정기경영공시 {c['quarter']} {tab} p{c.get('page')}"
    pq = c.get("pdf_quarter")
    if pq and pq != c["quarter"] and not r1:
        # gap-fill read from the prior-quarter column of ANOTHER filing (the 4-1 table prints three quarter columns)
        src = (f"정기경영공시 {pq} 공시본 {tab} 표 p{c.get('page')} 의 전분기 열({c['quarter']} 값; 그 열의 자본총계 = 구성 항목 합이 "
               f"닫히는 것을 확인)")
    return (f"{src} 라벨「{c.get('rule')}」, 단위 {unit}"
            f"({c.get('unit_how')}), 정밀도 ±{c.get('prec_mn')}백만원. {cal_txt}.{r1_txt} "
            f"(inbox/parser/20261011T0310Z bspl granularity)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--companies", default="")
    ap.add_argument("--status", default="CAND,CAND_UNTESTED")
    ap.add_argument("--items", default="")
    ap.add_argument("--manual", default="", help="JSON with extra cells in the candidate schema (visual transcription)")
    ap.add_argument("--exclude", default="", help="comma list of company|item|quarter keys to skip")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--round", default="1")
    a = ap.parse_args()

    status = set(a.status.split(","))
    items = {int(x) for x in a.items.split(",") if x}
    codes = [c for c in a.companies.split(",") if c] or sorted(p.stem for p in CAND_DIR.glob("KR*.json"))
    exclude = {x for x in a.exclude.split(",") if x}

    rows, raw_master = load_json_exact(MASTER, 2, "\r\n")
    ov, raw_ov = load_json_exact(OVERRIDES, 2, "\n")
    side, raw_side = load_json_exact(SIDECAR, 2, "\r\n")
    by_key = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in rows}
    if len(by_key) != len(rows):
        raise SystemExit("ABORT: duplicate keys in master")
    meta = meta_from_kics()

    cands = []
    for code in codes:
        p = CAND_DIR / f"{code}.json"
        if not p.exists():
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        cands += [c for c in d["candidates"] if c["status"] in status]
    # --exclude and --items filter the AUTOMATIC candidates only; manual cells are explicit and always taken
    if items:
        cands = [c for c in cands if c["item"] in items]
    cands = [c for c in cands if f"{c['code']}|{c['item']}|{c['quarter']}" not in exclude]
    if a.manual:
        cands += json.loads(Path(a.manual).read_text(encoding="utf-8"))["cells"]

    new, conflicts, same, dup = [], [], 0, set()
    for c in sorted(cands, key=lambda c: (c["code"], c["item"], c["quarter"])):
        key = (c["code"], c["item"], c["quarter"])
        if key in dup:
            raise SystemExit(f"ABORT: duplicate candidate {key}")
        dup.add(key)
        if key in by_key:
            m = by_key[key]["값"]
            if abs(m - c["value_mn"]) > max(c.get("tol_mn", 1.0), 0.011):
                conflicts.append((key, m, c["value_mn"]))
            else:
                same += 1
            continue
        if c["code"] not in meta:
            raise SystemExit(f"ABORT: no META for {c['code']}")
        new.append(c)

    by_co = Counter(c["code"] for c in new)
    by_item = Counter(c["item"] for c in new)
    print(f"candidates considered {len(cands)}; NEW cells {len(new)}; already in master & equal {same}; conflicts {len(conflicts)}")
    print("by company:", dict(sorted(by_co.items())))
    print("by item:", dict(sorted(by_item.items())))
    for k, m, v in conflicts[:20]:
        print("  CONFLICT", k, "master", m, "disclosure", v)
    if not a.apply:
        print("dry-run -- nothing written")
        return

    # ---- apply ----
    rd = BACKUP / f"round{a.round}"
    rd.mkdir(parents=True, exist_ok=True)
    for p in (MASTER, OVERRIDES, SIDECAR):
        shutil.copy2(p, rd / p.name)
    for p in PARTS.glob("*_agent_gran.json"):
        shutil.copy2(p, rd / p.name)

    # parts (per company)
    stamp = time.strftime("%Y-%m-%d")
    part_cells = defaultdict(dict)
    for c in new:
        k = f"{c['code']}|{c['item']}|{c['quarter']}"
        part_cells[c["code"]][k] = {
            "값": round(c["value_mn"], 6), "pdf": c.get("pdf"), "page": c.get("page"), "sha256": c.get("sha256"),
            "축척": f"{c.get('unit')} -> 백만원", "앵커항목": None, "방법": f"granularity:{c.get('kind')}:{c.get('rule')}:{c.get('calib')}",
            "근거": make_basis(c)}
    for code, cells in part_cells.items():
        pp = PARTS / f"{code}_agent_gran.json"
        prev = json.loads(pp.read_text(encoding="utf-8")) if pp.exists() else {"cells": {}, "skips": {}}
        for k, v in cells.items():
            if k in prev["cells"] and prev["cells"][k]["값"] != v["값"]:
                raise SystemExit(f"ABORT: part file value differs for {k}")
            prev["cells"][k] = v
        pp.write_text(json.dumps(prev, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    # overrides + sidecar: new keys only
    n_ov = n_sd = 0
    for code, cells in part_cells.items():
        for k, v in cells.items():
            if k in ov["cells"]:
                if ov["cells"][k]["값"] != v["값"]:
                    raise SystemExit(f"ABORT: override exists with different value {k}")
            else:
                ov["cells"][k] = {"값": v["값"], "근거": v["근거"]}
                n_ov += 1
            if k in side["cells"]:
                if side["cells"][k]["값"] != v["값"]:
                    raise SystemExit(f"ABORT: sidecar exists with different value {k}")
            else:
                side["cells"][k] = v
                n_sd += 1
    ov["_readme"].append(f"[{stamp}] 경영공시 BS 세부(granularity) 백필(inbox/parser/20261011T0310Z) -- {n_ov}칸 신규(기존 키 변경 0), "
                          f"scripts/bspl_granularity_load_bs.py 로 셀단위 추가. 계보: data/_derived/bs_from_disclosure.json")

    # master rows
    added = []
    for c in new:
        nm, tk, sb = meta[c["code"]]
        it = c["item"]
        added.append({"원보험사코드": c["code"], "원수사명": nm, "티커": tk, "생손보여부": sb, "항목번호": it,
                      "항목명": LABELS[it], "섹션": SECTION[it], "레벨": 1 if it in (1, 2, 3) else 2,
                      "공시분기": c["quarter"], "값": round(c["value_mn"], 6)})
    snapshot = {k: json.dumps(v, ensure_ascii=False, sort_keys=True) for k, v in by_key.items()}
    out_rows = rows + added
    out_rows.sort(key=lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"]))

    # concurrency guard: nothing may have changed since the first read
    for p, raw in ((MASTER, raw_master), (OVERRIDES, raw_ov), (SIDECAR, raw_side)):
        if p.read_bytes() != raw:
            raise SystemExit(f"ABORT: {p.name} changed since it was read (concurrent session?) -- nothing written to it")
    # master LAST: a failure before it leaves the master untouched (overlay/sidecar extras are idempotent on re-run)
    safe_write(OVERRIDES, dumps(ov, 2, "\n"))
    safe_write(SIDECAR, dumps(side, 2, "\r\n"))
    safe_write(MASTER, dumps(out_rows, 2, "\r\n"))

    # verify: every pre-existing row unchanged, only additions
    chk = json.loads(MASTER.read_bytes().decode("utf-8"))
    chk_idx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in chk}
    bad = [k for k, s in snapshot.items() if json.dumps(chk_idx.get(k), ensure_ascii=False, sort_keys=True) != s]
    if bad or len(chk) != len(rows) + len(added) or len(chk_idx) != len(chk):
        raise SystemExit(f"VERIFY FAILED: changed/missing existing rows {bad[:5]} rows {len(chk)} expected {len(rows) + len(added)}")
    prev_m = []
    if MANIFEST.exists():
        prev_m = json.loads(MANIFEST.read_text(encoding="utf-8")).get("rounds", [])
    prev_m.append({"round": a.round, "stamp": stamp, "added": [f"{c['code']}|{c['item']}|{c['quarter']}" for c in new],
                   "master_rows_before": len(rows), "master_rows_after": len(chk),
                   "overrides_new": n_ov, "sidecar_new": n_sd,
                   "master_sha256_after": sha_bytes(MASTER.read_bytes())})
    MANIFEST.write_text(json.dumps({"rounds": prev_m}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"APPLIED: +{len(added)} master rows ({len(rows)} -> {len(chk)}), overrides +{n_ov}, sidecar +{n_sd}; all {len(snapshot)} pre-existing rows byte-identical")


if __name__ == "__main__":
    main()
