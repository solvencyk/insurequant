# -*- coding: utf-8 -*-
"""KR0073 (Kyobo Life) 2023.4Q balance-sheet / insurance-liability block on the restated 2023-12-31 separate column.

Context: the FY2024 and FY2025 annual reports print the 2023-12-31 separate balance sheet RESTATED (time-value error of the CSM
amortisation, FY2024 note 44).  The BS master still carries the original FY2023 filing values.  Ticket: orchestrator 2026-10-22
(parser ifrs17, evidence data/_derived/remaining_20261022/a2_bs_ilp/).

Nine cells (one atomic block, BS item 20 and ILP item 15 move together):
  IFRS17_BS KR0073 2023.4Q items 1, 2, 3, 20, 31 ; KR0073 2024.4Q item 1
  insurance_liability_portfolio KR0073 2023.4Q items 10, 14, 15

What this script writes (never IFRS17_BS.json itself -- that file is produced by build_ifrs17_bs.py, which re-applies the overlay last):
  data/dart/viz/bs_manual_overrides.json                 +6 cells (key KR0073|<item>|<quarter>, 값 + 근거)
  insurance_liability_portfolio.json                     3 cells, old-value guard, CRLF/indent preserved
  insurance_liability_portfolio_provenance.json          the KR0073 2023.4Q lic_dart_note cell + one backfills entry
  data/_derived/ilp_restated_comparative.json            +1 cell (KR0073 2023.4Q), so the section-3 screen marks the restated cell

Modes (dry run by default):
  --check                      re-read the 11 filing values and the ILP table by line number, guards, closure; nothing written
  --apply --backup-dir DIR     write the four files above (backups first, post-write cell-level verification)
  --revert --backup-dir DIR    restore the four files from the backups

C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/apply_kr0073_bs_ilp_restated_20261022.py --check
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
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")

CODE = "KR0073"
F25 = "data/dart/FY2025_Q4/raw/KR0073_교보생명보험_20260331004015/20260331004015.xml"
F24 = "data/dart/FY2024_Q4/raw/KR0073_교보생명보험_20250331004015/xml/20250331004015.xml"
PATHS = {
    "BS": "IFRS17_BS.json",
    "BS_OV": "data/dart/viz/bs_manual_overrides.json",
    "ILP": "insurance_liability_portfolio.json",
    "PROV": "insurance_liability_portfolio_provenance.json",
    "SIDE": "data/_derived/ilp_restated_comparative.json",
}
WRITE_KEYS = ("BS_OV", "ILP", "PROV", "SIDE")
STAMP = "2026-10-22"
TICKET = "orchestrator 2026-10-22 parser/ifrs17 KR0073 BS+ILP restated block (evidence data/_derived/remaining_20261022/a2_bs_ilp/)"
BASIS = "latest_filing_comparative_restatable"

# (item, quarter, old (백만원), new (백만원), FY2025 line, FY2024 line, ACODE)
BS_CELLS = [
    (1, "2023.4Q", 115079638.554295, 115002544.049863, 46627, 49707, "Assets"),
    (2, "2023.4Q", 105317246.584092, 105026788.690168, 46718, 49974, "Liabilities"),
    (3, "2023.4Q", 9762391.970203, 9975755.359695, 46774, 50117, "Equity"),
    (20, "2023.4Q", 87533336.488348, 87242878.594424, 46648, 49746, "InsuranceContractsIssuedThatAreLiabilities"),
    (31, "2023.4Q", 6213762.493004, 6427125.882496, 46767, 50098, "RetainedEarnings"),
]
BS_2024_4Q_ITEM1 = (1, "2024.4Q", 122408983.045999, 122408551.533388, 46626, None, "Assets")
ILP_CELLS = [(10, 26927.46, 26927.47), (14, 848405.9, 845501.32), (15, 875333.36, 872428.79)]
ILP_Q = "2023.4Q"
ILP_ORIG_ITEMS = {"10": 26927.46, "13": 26927.46, "14": 848405.9, "15": 875333.36}
ILP_NEW_ITEMS = {"10": 26927.47, "13": 26927.46, "14": 845501.32, "15": 872428.79}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class JsonFile:
    """exact-format JSON file: detects (indent, newline, trailing newline) by byte round-trip; refuses files that do not round-trip."""

    def __init__(self, rel: str):
        self.rel = rel
        self.path = ROOT / rel
        self.raw = self.path.read_bytes()
        self.obj = json.loads(self.raw.decode("utf-8"))
        self.fmt = None
        for indent in (2, 1, 4):
            for nl in ("\n", "\r\n"):
                for tail in ("", "\n"):
                    if self._dump(self.obj, indent, nl, tail) == self.raw:
                        self.fmt = (indent, nl, tail)
                        break
                if self.fmt:
                    break
            if self.fmt:
                break
        if self.fmt is None:
            raise SystemExit(f"ABORT: {rel} does not round-trip byte-exactly -- refusing to rewrite")
        self.sha0 = sha(self.raw)

    @staticmethod
    def _dump(obj, indent, nl, tail):
        s = json.dumps(obj, ensure_ascii=False, indent=indent)
        if nl == "\r\n":
            s = s.replace("\n", "\r\n")
        return (s + tail).encode("utf-8")

    def dumps(self) -> bytes:
        return self._dump(self.obj, *self.fmt)


def write_atomic(path: Path, data: bytes, tries: int = 8):
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


def _num(s: str) -> int:
    s = re.sub(r"<[^>]+>", "", s).strip().replace(",", "")
    neg = s.startswith("(")
    v = int(s.strip("()"))
    return -v if neg else v


def reread_filings() -> dict:
    """independent re-read of the printed values (won) with line numbers; asserts ACODE / context / separate scope"""
    L25 = (ROOT / F25).read_text(encoding="utf-8").split("\n")
    L24 = (ROOT / F24).read_text(encoding="utf-8").split("\n")
    out = {}
    for item, q, old, new, l25, l24, code in BS_CELLS + [BS_2024_4Q_ITEM1]:
        s = L25[l25 - 1]
        want_ctx = "PFY2024eFY_" if q == "2024.4Q" else "BPFY2023eFY_"
        assert f'ACODE="ifrs-full_{code}"' in s and want_ctx in s and "SeparateMember" in s, (item, q, s[:160])
        v25 = _num(s)
        if l24 is not None:
            te = L24[l24 - 2]
            assert f'ACODE="ifrs-full_{code}"' in te and "PFY2023eFY_" in te and "SeparateMember" in te, (item, q, te[:160])
            v24 = _num(L24[l24 - 1])
            assert v24 == v25, f"FY2024 prior column {v24} != FY2025 third column {v25} (item {item})"
        assert round(v25 / 1e6, 6) == new, (item, q, v25, new)
        out[(item, q)] = v25
    # ILP: FY2024 note 17-2 2) 전기 closing row (separate): LRC excl LC | LC | LIC | total, 백만원
    row = [_num(L24[i]) for i in (63748, 63749, 63750, 63751)]          # lines 63749-63752
    assert re.sub(r"<[^>]+>", "", L24[63747]).strip() == "8. 기말 보험계약자산 및 부채"
    lrc, lc, lic, tot = row
    assert (lrc, lc, lic, tot) == (83536489, 1013643, 2692746, 87242879), row
    assert round((lrc + lc) / 100.0, 2) == ILP_NEW_ITEMS["14"]
    out["ILP_row"] = (lrc, lc, lic, tot)
    return out


def check_closure(vals: dict):
    a, l, e = vals[(1, "2023.4Q")], vals[(2, "2023.4Q")], vals[(3, "2023.4Q")]
    assert a - l - e == 0, ("2023.4Q 1 != 2 + 3", a - l - e)
    a24 = vals[(1, "2024.4Q")]
    return a - l - e, a24


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    ap.add_argument("--backup-dir")
    a = ap.parse_args()
    if a.revert:
        return revert(a)
    if not (a.check or a.apply):
        print("dry run (no --apply): checking only")
        a.check = True
    files = {k: JsonFile(v) for k, v in PATHS.items()}

    vals = reread_filings()
    resid, a24 = check_closure(vals)
    print(f"filing re-read OK (11 values, FY2024 prior col == FY2025 3rd col); 2023.4Q 1 - 2 - 3 = {resid} won; ILP row {vals['ILP_row']}")

    # ---------------- guards on the live masters
    bs_idx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in files["BS"].obj}
    ov_cells = files["BS_OV"].obj["cells"]
    for item, q, old, new, *_ in BS_CELLS + [BS_2024_4Q_ITEM1]:
        row = bs_idx.get((CODE, item, q))
        assert row is not None and abs(row["값"] - old) < 1e-6, ("BS guard", item, q, None if row is None else row["값"], old)
        k = f"{CODE}|{item}|{q}"
        assert k not in ov_cells, f"{k} is already an overlay cell -- hold"
    # block closure on the new values (백만원)
    n = {(i, q): new for i, q, old, new, *_ in BS_CELLS + [BS_2024_4Q_ITEM1]}
    assert abs(n[(1, "2023.4Q")] - n[(2, "2023.4Q")] - n[(3, "2023.4Q")]) < 1e-6
    assert abs((n[(2, "2023.4Q")] - bs_idx[(CODE, 2, "2023.4Q")]["값"]) - (n[(20, "2023.4Q")] - bs_idx[(CODE, 20, "2023.4Q")]["값"])) < 1e-6   # d(2) == d(20)
    assert abs(n[(1, "2024.4Q")] - bs_idx[(CODE, 2, "2024.4Q")]["값"] - bs_idx[(CODE, 3, "2024.4Q")]["값"]) < 1e-3   # 2024.4Q: items 2,3 already on that column, so 1 = 2 + 3 closes
    # RE roll 2023: restated opening + net income - annual dividend - hybrid dividend (FY2024 SOCE) == item 31
    re_roll = 5920420191959 + 632200607207 - 51250000000 - 74244916670
    assert re_roll == 6427125882496 and round(re_roll / 1e6, 6) == n[(31, "2023.4Q")]
    ilp_idx = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r for r in files["ILP"].obj}
    for item, old, new in ILP_CELLS:
        row = ilp_idx.get((CODE, ILP_Q, item))
        assert row is not None and abs(row["값"] - old) < 1e-9, ("ILP guard", item, None if row is None else row["값"], old)
    new15, new10, new14 = ILP_NEW_ITEMS["15"], ILP_NEW_ITEMS["10"], ILP_NEW_ITEMS["14"]
    assert abs(new10 + new14 - new15) < 1e-9, "10 + 14 != 15"
    assert abs(new15 - round(n[(20, "2023.4Q")] / 100.0, 2)) < 1e-9, "ILP 15 != restated BS 20 / 100"
    assert not any(c["company_code"] == CODE and c["quarter"] == ILP_Q for c in files["SIDE"].obj["cells"]), "sidecar already has the cell"
    pcells = [c for c in files["PROV"].obj["cells"] if c["company_code"] == CODE and c["quarter"] == ILP_Q and c.get("item_block") == "lic_dart_note"]
    assert len(pcells) == 1 and pcells[0]["items_eok"] == ILP_ORIG_ITEMS and "original_basis_value" not in pcells[0], "provenance guard"
    print("guards OK: BS 6 cells at old values, overlay has none of the 6 keys, ILP 3 cells at old values, closure 1=2+3 (2023.4Q, 2024.4Q), d(2)=d(20), RE roll ties, 10+14=15, 15==BS20/100")
    if not a.apply:
        print("check only: nothing written")
        return 0
    if not a.backup_dir:
        raise SystemExit("--apply needs --backup-dir")
    bdir = Path(a.backup_dir)
    bdir.mkdir(parents=True, exist_ok=True)
    for k in WRITE_KEYS:
        dst = bdir / (Path(PATHS[k]).name + ".pre_kr0073_20261022")
        if dst.exists():
            raise SystemExit(f"ABORT: backup {dst} exists (already applied?)")
    for k in WRITE_KEYS:
        shutil.copyfile(files[k].path, bdir / (Path(PATHS[k]).name + ".pre_kr0073_20261022"))
    pre = {k: copy.deepcopy(files[k].obj) for k in WRITE_KEYS}
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ")

    # ---------------- overlay (IFRS17_BS goes through bs_manual_overrides.json; build_ifrs17_bs.py re-applies it last)
    for item, q, old, new, l25, l24, code in BS_CELLS + [BS_2024_4Q_ITEM1]:
        if q == "2023.4Q":
            src = (f"{F25}#L{l25} {code} 제67기 열 {vals[(item, q)]:,}원 (별도 재무상태표 3번째 열); 독립 재독 {F24}#L{l24} 제67기 열 같은 값 (FY2024 사업보고서 전기 열); "
                   f"소급재작성 효과표 {F24}#L75166-75301 전기말 수정후/수정전/증감 (재작성 사유 note 44: 보험계약마진 상각을 위한 시간가치 계산의 오류, L75082-75083)")
        else:
            src = (f"{F25}#L{l25} {code} 제68기 열 {vals[(item, q)]:,}원 (별도 재무상태표 2번째 열); 소급재작성 효과표(44-2 전기말) 자산총계 수정후 122,408,552 / 수정전 122,408,983 / 증감 (431) "
                   f"(FY2025 note, rcept 20260331004015); 2024.4Q 항목 2·3·4 는 2026-10-12 에 이미 이 열로 교체됨, 이 칸으로 1 = 2 + 3 이 닫힘")
        ov_cells[f"{CODE}|{item}|{q}"] = {
            "값": new,
            "근거": (f"[{STAMP} parser/ifrs17 {TICKET}] 최신 공시 전기말 열 채택(owner 2026-10-12 최신 비교열 우선, 검증 단위=회사×FY 블록 산술 폐합). "
                     f"옛 값(원 공시 연말) {old} -> {new}. {src}")}
    # ---------------- ILP master (cell-level, old-value guard, CRLF preserved by JsonFile)
    for item, old, new in ILP_CELLS:
        ilp_idx[(CODE, ILP_Q, item)]["값"] = new
    # ---------------- provenance cell
    pc = pcells[0]
    pc["original_basis"] = {k: copy.deepcopy(pc.get(k)) for k in ("source_file", "rcept_no", "report_kind", "basis", "unit", "unit_source", "items_eok", "checks", "net_lrc_eok")}
    pc["original_basis_value"] = dict(ILP_ORIG_ITEMS)
    pc["source_file"] = F24
    pc["rcept_no"] = "20250331004015"
    pc["report_kind"] = "사업보고서"
    pc["items_eok"] = dict(ILP_NEW_ITEMS)
    pc["net_lrc_eok"] = ILP_NEW_ITEMS["14"]
    pc["flags"] = ["restated_comparative_prior_period_tables"]
    pc["tables"] = [{"table": None, "note": "17-2) 2) 전기 기말 보험계약자산 및 부채 (별도 재무제표 주석)", "unit": "백만원", "unit_src": "cue", "period_src": "cue",
                     "row": "LIAB", "tot_eok": ILP_NEW_ITEMS["15"], "lines": "FY2024_Q4 xml L63748-L63775"}]
    pc["checks"] = {"r_lic1": "pass", "bs20_eok": ILP_NEW_ITEMS["15"], "ratio_bs20": 1.0, "filing_bs_eok": ILP_NEW_ITEMS["15"], "ratio_filing_bs": 1.0,
                    "r_lic3_gap_eok": round(ILP_NEW_ITEMS["10"] + ILP_NEW_ITEMS["14"] - ILP_NEW_ITEMS["15"], 2), "tag_tables": 0, "tag_cells": 0, "tag_mismatch": 0}
    pc["checks_restated"] = {"chk_15_minus_10_14": 0.0, "chk_15_minus_bs_liab": round(ILP_NEW_ITEMS["15"] - 87242878.594424 / 100.0, 3)}
    pc["restated_bs_prior_col"] = {"liab_eok": ILP_NEW_ITEMS["15"], "asset_eok": 0.0, "source_file": F24}
    pc["period_basis"] = BASIS
    pc["basis_note"] = ("items 10, 14, 15 set to the FY2024 annual report prior-year-end (2023-12-31, restated) separate note column (printed LRC 83,536,489 + loss component 1,013,643 = "
                        "84,550,132 mn; LIC 2,692,746 mn unchanged within rounding; total 87,242,879 mn = restated BS item 20); item 10 +0.01 is the rounding that closes 10 + 14 = 15 "
                        "against the unrounded BS 87,242,878.594 mn (item 13, the printed LIC, stays 26927.46); original FY2023 values kept in original_basis_value / original_basis")
    pc["unified_at"] = now
    pc["restatement_ticket"] = TICKET
    pb = files["PROV"].obj
    pb["backfills"] = pb.get("backfills", []) + [{
        "stage": "kr0073_2023.4Q_restated_block_20261022", "at": now, "emitted_by": "scripts/apply_kr0073_bs_ilp_restated_20261022.py", "ticket": TICKET,
        "note": "KR0073 2023.4Q items 10/14/15 set to the FY2024 prior-year-end (restated) column; IFRS17_BS item 20 of the same quarter moves with it (bs_manual_overrides); originals in original_basis_value"}]
    # ---------------- sidecar cell
    reason = ("FY2024 사업보고서 주석 44 「재무제표 소급재작성 효과」(20250331004015.xml L75082-75083): 「당사는 보험계약마진 상각을 위한 시간가치 계산의 오류로 당기순이익 과소계상 "
              "및 보험계약부채 과대계상을 발견하여, 비교표시된 과거 재무제표를 소급재작성하였습니다」 (비교대상 전기말 = 2023-12-31, 보험계약부채 수정전 87,533,336 -> 수정후 87,242,879 백만원)")
    files["SIDE"].obj["cells"].append({
        "company_code": CODE, "quarter": ILP_Q, "basis": BASIS, "restatement_reason": reason,
        "restated_bs_insurance_contract_liability_eok": ILP_NEW_ITEMS["15"],
        "restated_bs_insurance_contract_asset_eok": 0.0,
        "restated_bs_net_eok": ILP_NEW_ITEMS["15"],
        "restated_bs_source": "FY2024 and FY2025 annual reports, separate balance sheet 2023-12-31 column (identical); IFRS17_BS item 20 of this quarter was moved to the same value in the same change",
        "bs_item20_fy2023_original_eok": ILP_ORIG_ITEMS["15"],
        "bs_item20_original_eok": ILP_ORIG_ITEMS["15"],
        "bs_source_file": F24,
        "items_10_15_restated": dict(ILP_NEW_ITEMS),
        "items_10_15_original": dict(ILP_ORIG_ITEMS)})
    files["SIDE"].obj["extended_at"] = now
    prev_by = files["SIDE"].obj.get("extended_by", [])
    prev_by = [prev_by] if isinstance(prev_by, str) else list(prev_by)
    files["SIDE"].obj["extended_by"] = prev_by + ["scripts/apply_kr0073_bs_ilp_restated_20261022.py"]

    # ---------------- write (masters last), then verify cell-level against the pre-state
    for k in ("SIDE", "PROV", "BS_OV", "ILP"):
        write_atomic(files[k].path, files[k].dumps())
    ok = True
    ilp_after = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r for r in json.loads((ROOT / PATHS["ILP"]).read_text(encoding="utf-8"))}
    ilp_before = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r for r in pre["ILP"]}
    diffs = {k for k in ilp_before if ilp_before[k] != ilp_after.get(k)}
    exp = {(CODE, ILP_Q, i) for i, o, nw in ILP_CELLS}
    if set(ilp_before) != set(ilp_after) or diffs != exp:
        ok = False
        print("ILP post-write verification FAILED", sorted(diffs - exp)[:5])
    ov_after = json.loads((ROOT / PATHS["BS_OV"]).read_text(encoding="utf-8"))["cells"]
    ov_before = pre["BS_OV"]["cells"]
    new_keys = set(ov_after) - set(ov_before)
    if new_keys != {f"{CODE}|{i}|{q}" for i, q, *_ in BS_CELLS + [BS_2024_4Q_ITEM1]} or any(ov_after[k] != ov_before[k] for k in ov_before):
        ok = False
        print("overlay post-write verification FAILED")
    if not ok:
        revert(a)
        raise SystemExit("post-write verification failed; restored from " + str(bdir))
    print(f"applied: overlay +{len(new_keys)}, ILP cells {len(exp)}, provenance cell + backfills, sidecar +1; backups in {bdir}")
    print("NEXT: run scripts/build_ifrs17_bs.py (re-applies the overlay last) and diff IFRS17_BS.json against git HEAD (exactly 6 cells)")
    return 0


def revert(a):
    if not a.backup_dir:
        raise SystemExit("--revert needs --backup-dir")
    bdir = Path(a.backup_dir)
    for k in WRITE_KEYS:
        src = bdir / (Path(PATHS[k]).name + ".pre_kr0073_20261022")
        if not src.exists():
            raise SystemExit(f"ABORT: backup missing {src}")
    for k in WRITE_KEYS:
        write_atomic(ROOT / PATHS[k], (bdir / (Path(PATHS[k]).name + ".pre_kr0073_20261022")).read_bytes())
    print("reverted", ", ".join(Path(PATHS[k]).name for k in WRITE_KEYS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
