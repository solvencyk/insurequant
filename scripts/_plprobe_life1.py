# -*- coding: utf-8 -*-
"""Probe (COPY of _diag_pl_notes.py, broadened) for 생보 PL-analysis notes.

Dumps ALL tables whose rows mention either:
  - "서비스의 이전으로 당기손익에 인식한 보험계약마진"  (CSM amortization recognized in P&L)
  - "발행한 보험계약" + "보험수익"                       (issued-contract revenue analysis)
plus a few other analysis-note signature fragments, so we can locate the real
보험수익/보험서비스비용 분석 note even when captions are misleading or header rows split.

Read-only.  Usage: python scripts/_plprobe_life1.py KR0073 2025.4Q [--all]
"""
import glob
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.build_net_income_breakdown import to_num  # noqa: E402


def _norm(s):
    return (s or "").replace("　", "").replace("\xa0", " ").strip()


ROLLFWD = ("기초 순장부금액", "기말 순장부금액", "기초 보험계약", "기말 보험계약",
           "기초보험계약", "기말보험계약", "수취한 보험료", "총 현금흐름", "순장부금액",
           "보험계약부채(자산)")

# Broadened signature fragments for the P&L-analysis note (issued + reinsurance).
ANALYSIS_ROWS = (
    "서비스의 이전으로 당기손익에 인식한 보험계약마진",
    "제공된 서비스의 보험계약마진",
    "당기손익에 인식한 보험계약마진",
    "보험계약마진의 상각",
    "위험해제로 인한 비금융위험에 대한 위험조정의 변동",
    "비금융위험에 대한 위험조정의 변동",
    "위험조정의 변동",
    "보고기간에 발생한 보험서비스비용",
    "기초 예상 측정치",
    "발생한 보험금 및 그 밖의 발생한 보험서비스비용",
    "예상 발생보험금",
    "발생한 보험금",
    "회수",
)


def looks_like_note(t):
    rowblob = " ".join(_norm(r[0]) + " " + (_norm(r[1]) if len(r) > 1 else "") for r in t.rows)
    flat = rowblob.replace(" ", "")
    if any(k.replace(" ", "") in flat for k in ROLLFWD):
        return False
    has_csm = "서비스의이전으로당기손익에인식한보험계약마진" in flat or "당기손익에인식한보험계약마진" in flat
    has_issued_rev = ("발행한보험계약" in flat and "보험수익" in flat)
    hits = sum(1 for k in ANALYSIS_ROWS if k.replace(" ", "") in flat)
    return has_csm or has_issued_rev or (hits >= 2 and ("보험수익" in flat or "보험서비스비용" in flat
                                                        or "재보험" in flat))


def fmt_row(r):
    lab = _norm(r[0])
    lab1 = _norm(r[1]) if len(r) > 1 else ""
    nums = [to_num(c) for c in r]
    nums = [round(n, 1) for n in nums if n is not None]
    label = lab if not lab1 else f"{lab} | {lab1}"
    return f"    {label[:70]:<70}  nums={nums}"


def main():
    code, q = sys.argv[1], sys.argv[2]
    show_all = "--all" in sys.argv
    y, qq = re.match(r"(\d{4})\.(\d)Q", q).groups()
    base_glob = f"data/dart/FY{y}_Q{qq}/raw/{code}_*"
    dirs = glob.glob(base_glob)
    if not dirs:
        print("no raw dir for", code, q, "glob=", base_glob)
        return
    tables = []
    srcmap = []
    for d in dirs:
        xs = glob.glob(d + "/*.xml") + glob.glob(d + "/xml/*.xml") + glob.glob(d + "/extracted*/*.xml")
        for x in sorted(set(xs), key=os.path.getsize, reverse=True):
            try:
                tt = _iter_tables_with_context(Path(x))
                for t in tt:
                    srcmap.append(os.path.basename(x))
                tables.extend(tt)
            except Exception as e:
                print("  parse error", x, e)
    print(f"=== {code} {q} : {len(tables)} tables ===")
    n = 0
    for idx, t in enumerate(tables):
        if not show_all and not looks_like_note(t):
            continue
        n += 1
        src = srcmap[idx] if idx < len(srcmap) else "?"
        print(f"\n[table {n}] src={src} caption={t.caption!r}")
        for h in t.header:
            print("   H:", [_norm(c) for c in h])
        for r in t.rows[:30]:
            print(fmt_row(r))
    print(f"\n-> {n} candidate note tables shown")


if __name__ == "__main__":
    main()
