#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cell-level applier for ticket 20261012T2230Z (parser/ifrs17): latest-comparative values for the verified blocks + definite 3-month-as-cumulative fixes.

Plan   = data/_derived/ifrs17_latest_comparative_apply_20261012/plan_final.json  (cells: master, code, quarter, item, old, new, kind, evidence ...)
Writes (only the cells of the plan; everything else is verified byte-identical afterwards):
  PL_breakdown.json / CSM_waterfall.json / IFRS17_BS.json      masters: cell 값 + the derived 값_당분기 of the touched series (build_root_masters rules)
  data/_gold/user_pl_cells.json / user_csm_cells.json           durable gold overlay (build_root_masters._apply_*_overrides UPSERT it last, so a rebuild cannot revert)
  data/dart/viz/bs_manual_overrides.json                        BS overlay that build_ifrs17_bs.py re-applies last
  PL_breakdown_provenance.json / CSM_waterfall_provenance.json  sidecars: touched items move to the owner_gold_overlay entry (same convention as the existing gold cells)
  registry releases (only when listed in the plan): data/_gold/pl_bridge_baseline.json, data/_gold/csm_amort_identity_ledger.json, scripts/validate_master_tables.py WFY_EXCEPTIONS
Guards (abort before any write): the live value must equal the plan's old value (or already equal the new value = idempotent skip); an appended gold key must be absent;
every file must round-trip byte-exactly with its detected indent/newline; the files must not change between read and write.  Backups: data/_derived/ifrs17_latest_comparative_apply_backup_20261012/.
No builder, no build_root_masters.main(), no validate_master_tables without --no-build is run by this script.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/apply_latest_comparative_20261012.py --check
  ... --apply                       write the repo files
  ... --out-dir DIR                 simulate: write the same relative files under DIR (nothing in the repo changes) so gates can be served the candidate
  ... --revert --apply              restore the backups (only when the live files still have the post-apply hashes)
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "data" / "_derived" / "ifrs17_latest_comparative_apply_20261012"
PLAN = WORK / "plan_final.json"
BACKUP = ROOT / "data" / "_derived" / "ifrs17_latest_comparative_apply_backup_20261012"
MANIFEST = WORK / "apply_manifest.json"
sys.stdout.reconfigure(encoding="utf-8")

F = {
    "PL": "PL_breakdown.json", "CSM": "CSM_waterfall.json", "BS": "IFRS17_BS.json",
    "PL_PROV": "PL_breakdown_provenance.json", "CSM_PROV": "CSM_waterfall_provenance.json",
    "GOLD_PL": "data/_gold/user_pl_cells.json", "GOLD_CSM": "data/_gold/user_csm_cells.json",
    "BS_OV": "data/dart/viz/bs_manual_overrides.json",
    "BASE_PL": "data/_gold/pl_bridge_baseline.json", "LEDGER_CSM": "data/_gold/csm_amort_identity_ledger.json",
    "VMT": "scripts/validate_master_tables.py",
}
CONTRACT_NOTE_ITEMS = {4, 5, 6, 9, 10, 11, 13, 14}
GOLD_PL_PATH = F["GOLD_PL"]
EPS = 1e-9
CSM_OPEN, CSM_CLOSE = 1, 6


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def qkey(q):
    return (int(q[:4]), int(q[5]))


def prev_q(q):
    y, n = qkey(q)
    return None if n == 1 else f"{y}.{n - 1}Q"


def next_q(q):
    y, n = qkey(q)
    return None if n == 4 else f"{y}.{n + 1}Q"


def same(a, b):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= EPS * max(1.0, abs(a), abs(b))


def flow_dangi(ytd_by_q, q):
    """build_root_masters._flow_dangi (copied verbatim): YTD(q) - YTD(prev); Q1 = YTD; None if a needed YTD is missing."""
    cur = ytd_by_q.get(q)
    if cur is None:
        return None
    p = prev_q(q)
    if p is None:
        return cur
    prev = ytd_by_q.get(p)
    return None if prev is None else round(cur - prev, 6)


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
        except OSError as e:  # transient Windows lock
            last = e
            time.sleep(0.75 * (i + 1))
    raise SystemExit(f"ABORT: could not write {path}: {last!r}")


def load_plan():
    d = json.loads(PLAN.read_text(encoding="utf-8"))
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    ap.add_argument("--out-dir")
    a = ap.parse_args()
    if a.revert:
        return revert(a)
    plan = load_plan()
    cells = plan["cells"]
    release = plan.get("release", {})
    outdir = Path(a.out_dir) if a.out_dir else None
    if not (a.check or a.apply or outdir):
        print("dry-run (no --apply / --out-dir): checking only")
        a.check = True

    files = {k: JsonFile(v) for k, v in F.items() if v.endswith(".json")}
    vmt_path = ROOT / F["VMT"]
    vmt_raw = vmt_path.read_bytes()
    pl, csm, bs = files["PL"], files["CSM"], files["BS"]
    pl_idx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in pl.obj}
    csm_idx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in csm.obj}
    bs_idx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in bs.obj}
    gold_pl = {(g["원보험사코드"], g["항목번호"], g["공시분기"]): g for g in files["GOLD_PL"].obj["set"]}
    gold_csm = {(g["원보험사코드"], g["항목번호"], g["공시분기"]): g for g in files["GOLD_CSM"].obj["set"]}
    ov_cells = files["BS_OV"].obj["cells"]

    # ---------------------------------------------------------------- guards
    todo = []          # cells that still need writing
    done = 0
    for c in cells:
        m, k = c["master"], (c["code"], c["item"], c["quarter"])
        idx = {"PL_breakdown": pl_idx, "CSM_waterfall": csm_idx, "IFRS17_BS": bs_idx}[m]
        if k not in idx:
            raise SystemExit(f"ABORT: {m} row {k} not in the master (the plan never adds rows)")
        cur = idx[k]["값"]
        if same(cur, c["new"]):
            done += 1
            continue
        if not same(cur, c["old"]):
            raise SystemExit(f"ABORT: {m} {k} live value {cur!r} != plan old {c['old']!r} (and != new {c['new']!r}) -- somebody changed it; re-plan")
        if m == "PL_breakdown" and k in gold_pl:
            raise SystemExit(f"ABORT: {k} already has a user_pl_cells gold entry -- would collide with an owner/parser overlay")
        if m == "CSM_waterfall" and k in gold_csm:
            raise SystemExit(f"ABORT: {k} already has a user_csm_cells gold entry")
        if m == "IFRS17_BS" and f"{k[0]}|{k[1]}|{k[2]}" in ov_cells:
            raise SystemExit(f"ABORT: {k} is already a bs_manual_overrides cell (owner/disclosure value) -- hold, do not overwrite")
        todo.append(c)
    print(f"plan cells {len(cells)}: already applied {done}, to write {len(todo)}")
    if a.check and not (a.apply or outdir):
        for c in todo[:10]:
            print("  would write", c["master"], c["code"], c["quarter"], c["item"], c["old"], "->", c["new"])
        print("check only -- nothing written")
        return 0

    # ---------------------------------------------------------------- apply to in-memory copies
    pre = {k: copy.deepcopy(files[k].obj) for k in ("PL", "CSM", "BS")}
    pre_gold = {k: copy.deepcopy(files[k].obj) for k in ("GOLD_PL", "GOLD_CSM", "BS_OV", "PL_PROV", "CSM_PROV", "BASE_PL", "LEDGER_CSM")}
    pl_touched, csm_touched = defaultdict(set), defaultdict(set)   # (code,item)->{q} / (code)->{(item,q)}
    stamp = "2026-10-12"
    for c in todo:
        k = (c["code"], c["item"], c["quarter"])
        if c["master"] == "PL_breakdown":
            pl_idx[k]["값"] = c["new"]
            pl_touched[(c["code"], c["item"])].add(c["quarter"])
            note = (f"{stamp} parser/ifrs17 ticket 20261012T2230Z: " +
                    ("원 공시 포괄손익계산서의 3개월 열이 누적으로 적재돼 있던 것을 누적 열로 정정. " if c["kind"] == "3m_as_cumulative"
                     else "후속 공시 요약 포괄손익계산서의 해당 분기(24.xQ) 열이 전년 동기(23.xQ) 칸에 적재돼 있던 것을 전년 동기 열로 정정. " if c["kind"] == "wrong_year_column"
                     else "최신 공시의 전기·전년동기 비교열 채택(owner 2026-10-12 「확실히 검산 닫히는 것만」). ") + c["source_ref"])
            files["GOLD_PL"].obj["set"].append({"원보험사코드": c["code"], "항목번호": c["item"], "공시분기": c["quarter"], "값": c["new"], "was": c["old"], "note": note})
        elif c["master"] == "CSM_waterfall":
            csm_idx[k]["값"] = c["new"]
            csm_touched[c["code"]].add((c["item"], c["quarter"]))
            note = f"{stamp} parser/ifrs17 ticket 20261012T2230Z: 최신 공시의 전기·전년동기 비교열 채택(owner 2026-10-12). " + c["source_ref"]
            files["GOLD_CSM"].obj["set"].append({"원보험사코드": c["code"], "항목번호": c["item"], "공시분기": c["quarter"], "값": c["new"], "was": c["old"], "note": note})
        else:
            bs_idx[k]["값"] = c["new"]
            ov_cells[f"{c['code']}|{c['item']}|{c['quarter']}"] = {
                "값": c["new"],
                "근거": (f"[{stamp} parser/ifrs17 20261012T2230Z] 최신 공시 전기말 열 채택(owner 2026-10-12 최신 비교열 우선). 옛 값(원 공시 연말) {c['old']} -> {c['new']}. "
                         f"{c['source_ref']}; {c['verified_ref']}")}

    # derived 값_당분기 (build_root_masters rules), only for the rows that depend on a changed value
    exp_pl_rows, exp_csm_rows = set(), set()
    pl_series = defaultdict(dict)
    for r in pl.obj:
        pl_series[(r["원보험사코드"], r["항목번호"])][r["공시분기"]] = r["값"]
    for (code, item), qs in pl_touched.items():
        for q in qs:
            for qq in (q, next_q(q)):
                if qq is None:
                    continue
                r = pl_idx.get((code, item, qq))
                if r is None:
                    continue
                v = r.get("값")
                new_d = flow_dangi(pl_series[(code, item)], qq) if v is not None else None
                if not same(r.get("값_당분기"), new_d):
                    r["값_당분기"] = new_d
                exp_pl_rows.add((code, item, qq))
    csm_series = defaultdict(dict)
    for r in csm.obj:
        csm_series[(r["원보험사코드"], r["항목번호"])][r["공시분기"]] = r["값"]
    for code, pairs in csm_touched.items():
        rows_to_fix = set()
        for (item, q) in pairs:
            rows_to_fix.add((item, q))
            nq = next_q(q)
            if nq:
                rows_to_fix.add((item, nq))                        # flow: next quarter's difference
                if item == CSM_CLOSE:
                    rows_to_fix.add((CSM_OPEN, nq))                # opening 당분기 = previous closing
        for (item, q) in rows_to_fix:
            r = csm_idx.get((code, item, q))
            if r is None:
                continue
            v = r.get("값")
            if v is None:
                d = None
            elif item == CSM_CLOSE:
                d = v
            elif item == CSM_OPEN:
                p = prev_q(q)
                d = v if p is None else csm_series[(code, CSM_CLOSE)].get(p)
            else:
                d = flow_dangi(csm_series[(code, item)], q)
            d = round(d, 6) if isinstance(d, (int, float)) else d
            if not same(r.get("값_당분기"), d):
                r["값_당분기"] = d
            exp_csm_rows.add((code, item, q))

    # ---------------------------------------------------------------- sidecars
    prov_pl = {(c["company_code"], c["quarter"], c["item_block"]): c for c in files["PL_PROV"].obj["cells"]}
    by_block = defaultdict(set)
    for c in todo:
        if c["master"] == "PL_breakdown":
            blk = "contract_notes" if c["item"] in CONTRACT_NOTE_ITEMS else "income_statement"
            by_block[(c["code"], c["quarter"], blk)].add(c["item"])
    nonnull = defaultdict(set)
    for r in pl.obj:
        if r["값"] is not None:
            nonnull[(r["원보험사코드"], r["공시분기"], "contract_notes" if r["항목번호"] in CONTRACT_NOTE_ITEMS else "income_statement")].add(r["항목번호"])
    for key, items in sorted(by_block.items()):
        rec = prov_pl.get(key)
        if rec is None:
            raise SystemExit(f"ABORT: PL provenance sidecar has no record for {key}")
        sfs = rec.setdefault("source_files", [])
        gold = next((e for e in sfs if e.get("file") == GOLD_PL_PATH and e.get("how") == "owner_gold_overlay"), None)
        if gold is None:
            gold = {"file": GOLD_PL_PATH, "how": "owner_gold_overlay", "items": []}
            sfs.append(gold)
        for e in list(sfs):
            if e is gold:
                continue
            e["items"] = [i for i in e.get("items", []) if i not in items]
            if not e["items"] and e.get("file") != rec.get("source_file"):
                sfs.remove(e)
        gold["items"] = sorted(set(gold.get("items", [])) | items, key=lambda x: (isinstance(x, str), x))
        rec["owner_override"] = True
        rec["published_items"] = len(nonnull.get(key, ()))
    side = files["PL_PROV"].obj
    side["merge_note_20261012_latest_comparative"] = (
        "ticket 20261012T2230Z (owner 2026-10-12 「확실히 검산 닫히는 것만 최신 공시로 덮어쓰기」): 검증된 7블록의 최신 공시 전기·전년동기 비교열 채택 + 원 공시 2Q 포괄손익계산서의 3개월 열이 "
        "누적으로 적재된 14칸 정정 + 한화손해보험 2023.1Q·2Q 기타사업비용의 후속 공시 해당 분기 열 오적재 2칸 정정. 값은 data/_gold/user_pl_cells.json 에 등재(빌드 마지막 UPSERT 라 재빌드가 되돌리지 못한다), 이 블록의 해당 항목은 owner_gold_overlay 항목으로 옮겼다. "
        "정정 전후 값·근거 쪽·인쇄값은 data/_derived/ifrs17_latest_comparative_apply_20261012/applied_cells.csv. 재현 scripts/apply_latest_comparative_20261012.py")
    csm_prov = {(c["company_code"], c["quarter"], c["item_block"]): c for c in files["CSM_PROV"].obj["cells"]}
    for c in todo:
        if c["master"] == "CSM_waterfall":
            rec = csm_prov.get((c["code"], c["quarter"], "csm_waterfall"))
            if rec is None:
                raise SystemExit(f"ABORT: CSM provenance sidecar has no record for {c['code']} {c['quarter']}")
            rec["owner_override"] = True
    files["CSM_PROV"].obj["merge_note_20261012_latest_comparative"] = (
        "ticket 20261012T2230Z: 검증된 CSM 8블록(최신 공시 전기·전년동기 비교열)은 data/_gold/user_csm_cells.json 에 등재(owner_override 표시). 근거 쪽·인쇄값 "
        "data/_derived/ifrs17_latest_comparative_apply_20261012/applied_cells.csv")

    # ---------------------------------------------------------------- registry releases
    rel = release or {}
    for key in rel.get("pl_bridge_baseline", []):
        if key not in files["BASE_PL"].obj["entries"]:
            raise SystemExit(f"ABORT: release key {key!r} not in pl_bridge_baseline entries")
        del files["BASE_PL"].obj["entries"][key]
    for key in rel.get("csm_amort_identity_ledger", []):
        if key not in files["LEDGER_CSM"].obj["entries"]:
            raise SystemExit(f"ABORT: release key {key!r} not in csm_amort_identity_ledger entries")
        del files["LEDGER_CSM"].obj["entries"][key]
    vmt_new = vmt_raw
    for name, fy in rel.get("wfy_exceptions", []):
        pat = f'("{name}", "{fy}"), '
        txt = vmt_new.decode("utf-8")
        if pat in txt:
            txt = txt.replace(pat, "", 1)
        elif f', ("{name}", "{fy}")' in txt:
            txt = txt.replace(f', ("{name}", "{fy}")', "", 1)
        else:
            raise SystemExit(f"ABORT: WFY exception ({name},{fy}) not found in validate_master_tables.py")
        vmt_new = txt.encode("utf-8")

    # ---------------------------------------------------------------- post-conditions on the in-memory result
    def diff_rows(before, after, allowed_keys, label):
        bi = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in before}
        n_val = n_d = 0
        for r in after:
            k = (r["원보험사코드"], r["항목번호"], r["공시분기"])
            b = bi[k]
            if r != b:
                ch = {f for f in set(r) | set(b) if r.get(f) != b.get(f)}
                if not ch <= {"값", "값_당분기"}:
                    raise SystemExit(f"ABORT({label}): unexpected field change {ch} at {k}")
                if "값" in ch:
                    n_val += 1
                    if k not in allowed_keys["val"]:
                        raise SystemExit(f"ABORT({label}): 값 changed outside the plan at {k}")
                if "값_당분기" in ch:
                    n_d += 1
                    if k not in allowed_keys["derived"]:
                        raise SystemExit(f"ABORT({label}): 값_당분기 changed outside the expected set at {k}")
        if len(before) != len(after):
            raise SystemExit(f"ABORT({label}): row count changed")
        return n_val, n_d

    plan_keys = {m: {(c["code"], c["item"], c["quarter"]) for c in todo if c["master"] == m} for m in ("PL_breakdown", "CSM_waterfall", "IFRS17_BS")}
    r_pl = diff_rows(pre["PL"], pl.obj, {"val": plan_keys["PL_breakdown"], "derived": exp_pl_rows}, "PL")
    r_csm = diff_rows(pre["CSM"], csm.obj, {"val": plan_keys["CSM_waterfall"], "derived": exp_csm_rows}, "CSM")
    r_bs = diff_rows(pre["BS"], bs.obj, {"val": plan_keys["IFRS17_BS"], "derived": set()}, "BS")
    print(f"in-memory result: PL 값 {r_pl[0]} / 당분기 {r_pl[1]} · CSM 값 {r_csm[0]} / 당분기 {r_csm[1]} · BS 값 {r_bs[0]}")
    n_gold_pl = len(files["GOLD_PL"].obj["set"]) - len(pre_gold["GOLD_PL"]["set"])
    n_gold_csm = len(files["GOLD_CSM"].obj["set"]) - len(pre_gold["GOLD_CSM"]["set"])
    print(f"gold appends: user_pl_cells +{n_gold_pl}, user_csm_cells +{n_gold_csm}; bs_manual_overrides +{len(ov_cells) - len(pre_gold['BS_OV']['cells'])}")

    # ---------------------------------------------------------------- write
    order = ["GOLD_PL", "GOLD_CSM", "BS_OV", "PL_PROV", "CSM_PROV", "BASE_PL", "LEDGER_CSM", "BS", "CSM", "PL"]     # masters last
    out = {k: files[k].dumps() for k in order}
    changed = {k: v for k, v in out.items() if v != files[k].raw}
    if vmt_new != vmt_raw:
        changed["VMT"] = vmt_new
    if outdir is not None:
        for k, data in changed.items():
            write_atomic(outdir / F[k], data)
        print(f"simulation written under {outdir}: {sorted(F[k] for k in changed)}")
        return 0
    # concurrency guard: nothing changed on disk since we read
    for k in changed:
        cur = (ROOT / F[k]).read_bytes()
        base = files[k].raw if k != "VMT" else vmt_raw
        if cur != base:
            raise SystemExit(f"ABORT: {F[k]} changed on disk while the plan was being applied")
    if BACKUP.exists() and any(BACKUP.iterdir()):
        raise SystemExit(f"ABORT: backup dir {BACKUP} already exists and is not empty (a previous apply?) -- use --revert or move it")
    BACKUP.mkdir(parents=True, exist_ok=True)
    for k in changed:
        dst = BACKUP / F[k]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / F[k], dst)
    for k in order:
        if k in changed:
            write_atomic(ROOT / F[k], changed[k])
    if "VMT" in changed:
        write_atomic(vmt_path, changed["VMT"])
    man = {"applied_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "files": {F[k]: {"sha_before": (files[k].sha0 if k != "VMT" else sha(vmt_raw)), "sha_after": sha(changed[k])} for k in changed}}
    MANIFEST.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("applied; backups in", BACKUP.relative_to(ROOT), "; manifest", MANIFEST.relative_to(ROOT))
    return 0


def revert(a):
    if not MANIFEST.exists():
        raise SystemExit("no apply_manifest.json -- nothing to revert")
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for rel, h in man["files"].items():
        cur = sha((ROOT / rel).read_bytes())
        if cur != h["sha_after"]:
            raise SystemExit(f"ABORT: {rel} changed since the apply (sha {cur[:12]} != {h['sha_after'][:12]}) -- revert that file by hand from {BACKUP}")
    if not a.apply:
        print("revert dry-run: all", len(man["files"]), "files still have the post-apply hashes; add --apply to restore the backups")
        return 0
    for rel in man["files"]:
        write_atomic(ROOT / rel, (BACKUP / rel).read_bytes())
    print("restored", len(man["files"]), "files from", BACKUP.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
