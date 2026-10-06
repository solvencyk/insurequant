# -*- coding: utf-8 -*-
"""Bugfix (2026-09-20): drop the 55 wrong item13 `값_적용후` post-transition mirrors.

Background
----------
`scripts/backfill_post_transition_when_not_applied.py` (2026-07-11, commit e1aa8ae)
mirrored `값_적용후 = 값` for items 4/12/13 on the sole evidence that items 1/14/27
(총액·기준금액·비율) were 적용전 == 적용후. That is unsound: the 공통적용 경과조치 (TFI)
leaves 총액 alone and moves the **tier split** — it reclassifies already-issued capital
securities, i.e. it changes Ⅲ(보완자본 재분류, item13), not Ⅰ(순자산, item4) or
Ⅱ(불인정항목, item12).

Same treatment as the 2026-07-16 precedent
`scripts/fix_20260716_revert_wrong_item1213_mirror.py`: revert to missing (결측 =
"미공시"), because no issuer prints items 4/12/13 in the 적용후 column (0/251 buckets),
so there is no disclosed value to put back. `K-ICS.html` L304
`NO_POST_TRANSITION_DISCLOSURE = {4,12,13}` + L454 already render a missing cell as
"미공시".

Which cells, and why exactly 55
-------------------------------
    implied13  = item4_pre - item12_pre - item2_post        (true item13_post; item2_post
                                                             IS issuer-disclosed)
    resid_pre  = item4_pre - item12_pre - item13_pre - item2_pre
    Dtier      = item2_post - item2_pre
    over_by    = item13_pre - implied13 == Dtier - resid_pre

`over_by` mixes the TFI tier movement (Dtier — the contamination) with the 적용전
bridge's own pre-existing residual (resid_pre — NOT contamination; it sits in the
적용전 column too and deleting the 적용후 cell fixes nothing). A raw `over_by > tol`
sweep therefore over-fires. Gating on Dtier isolates the contamination:

    DELETE  <=>  item13 값_적용후 present AND == 값            (it is a mirror)
             AND item4_pre / item12_pre / item2_pre / item2_post all present
             AND |Dtier| > 2.0                                 (tier really moved)
             AND over_by > 2.0                                 (mirror really too high)

That yields **55 cells**, identical cell-for-cell to validation's CONTAMINATED-filtered
55. The orchestrator's 59 is this set plus exactly 4 cells whose Dtier == 0.0 and whose
over_by == -resid_pre exactly (KR0075 2024.3Q/2024.4Q, KR0087 2025.4Q/2026.1Q) — those
are 적용전-bridge residuals, not mirror contamination, and are kept.

NOT deleted, deliberately: item4 (58 cells) and item12 (56 cells) mirrors in the same
buckets. NOT deleted: 메리츠화재 2026.2Q item13 — that bucket's item2/item3 `값_적용후`
are a stale copy of 적용전 (raw `md_inbox/FY2026_Q2/KR0001_메리츠화재해상보험.md`:
기본자본 5,253,762 -> 5,432,957 백만원), so Dtier reads 0 and the cell is masked. It
becomes the 56th once that separate defect is fixed.

Probes: scripts/_probes/_probe_20260920_item13_{deletion_set,delta4,final_set,setdiff}.py
Reads the deletion list from data/_derived/_probe_20260920_item13_final_set.json.

Cell-level edit with guards; never a blind read-modify-write.
"""
from __future__ import annotations

import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER = os.path.join(REPO, "kics_disclosure.json")
DELSET = os.path.join(REPO, "data", "_derived", "_probe_20260920_item13_final_set.json")

ITEM = 13
EXPECTED_LABEL_PREFIX = "Ⅲ. 보완자본으로 재분류하는 항목"
EXPECTED_N = 55


def sig(row):
    return json.dumps(row, ensure_ascii=False, sort_keys=True)


def main():
    st0 = os.stat(MASTER)
    with io.open(MASTER, "r", encoding="utf-8", newline="") as f:
        raw_before = f.read()
    # the pipeline writes this file with Path.write_text(), i.e. os.linesep endings on
    # Windows -> CRLF on disk. Normalise for the round-trip check, restore on write, so a
    # 55-cell edit does not churn 275k line endings (and 277KB of golden fingerprint).
    nl = "\r\n" if "\r\n" in raw_before[:4096] else "\n"
    raw_before_lf = raw_before.replace("\r\n", "\n") if nl == "\r\n" else raw_before
    data = json.loads(raw_before_lf)

    # round-trip fidelity check: a no-op dump must reproduce the file byte for byte,
    # otherwise our write would silently reformat rows we never touched.
    noop = json.dumps(data, ensure_ascii=False, indent=2)
    if noop != raw_before_lf:
        if noop.rstrip("\n") == raw_before_lf.rstrip("\n"):
            print("note: only trailing-newline differs (before=%r after=%r)"
                  % (raw_before_lf[-1:], noop[-1:]))
        else:
            sys.exit("ABORT: no-op round-trip is not byte-identical "
                     "(%d -> %d chars); refusing to rewrite the master."
                     % (len(raw_before_lf), len(noop)))

    with io.open(DELSET, "r", encoding="utf-8") as f:
        payload = json.load(f)
    targets = {}
    for r in payload["delete"]:
        targets[(r["code"], r["q"])] = r
    if len(targets) != EXPECTED_N or len(payload["delete"]) != EXPECTED_N:
        sys.exit("ABORT: deletion list has %d entries (%d unique), expected %d"
                 % (len(payload["delete"]), len(targets), EXPECTED_N))

    before = [sig(r) for r in data]

    hit, changed_idx = set(), []
    for i, r in enumerate(data):
        if int(r.get("항목번호", -1)) != ITEM:
            continue
        key = (r.get("원보험사코드"), r.get("공시분기"))
        t = targets.get(key)
        if t is None:
            continue
        # --- guards -------------------------------------------------------
        if not str(r.get("항목명", "")).startswith(EXPECTED_LABEL_PREFIX):
            sys.exit("ABORT: %s %s item13 label mismatch: %r" % (key + (r.get("항목명"),)))
        if "값_적용후" not in r or r.get("값_적용후") is None:
            sys.exit("ABORT: %s %s item13 값_적용후 already missing" % key)
        pre, post = str(r.get("값")).strip(), str(r.get("값_적용후")).strip()
        if pre != post:
            sys.exit("ABORT: %s %s item13 is not a mirror (값=%r 값_적용후=%r)" % (key + (pre, post)))
        if abs(float(post.replace(",", "")) - float(t["item13_mirrored"])) > 1e-9:
            sys.exit("ABORT: %s %s item13 값_적용후=%r != probe value %r"
                     % (key + (post, t["item13_mirrored"])))
        if key in hit:
            sys.exit("ABORT: duplicate item13 row for %s %s" % key)
        hit.add(key)
        del r["값_적용후"]
        changed_idx.append(i)

    missing = sorted(set(targets) - hit)
    if missing:
        sys.exit("ABORT: %d target rows not found: %s" % (len(missing), missing))
    if len(changed_idx) != EXPECTED_N:
        sys.exit("ABORT: changed %d rows, expected %d" % (len(changed_idx), EXPECTED_N))

    # --- whole-file diff guard: nothing outside the target rows may move ---
    after = [sig(r) for r in data]
    if len(after) != len(before):
        sys.exit("ABORT: row count changed %d -> %d" % (len(before), len(after)))
    moved = [i for i in range(len(before)) if before[i] != after[i]]
    if moved != changed_idx:
        sys.exit("ABORT: rows changed outside the target set: %s"
                 % sorted(set(moved) ^ set(changed_idx))[:20])
    for i in changed_idx:
        b, a = json.loads(before[i]), json.loads(after[i])
        b.pop("값_적용후", None)
        if b != a:
            sys.exit("ABORT: row %d changed in a way other than dropping 값_적용후" % i)

    out = json.dumps(data, ensure_ascii=False, indent=2)
    if raw_before_lf.endswith("\n") and not out.endswith("\n"):
        out += "\n"
    if nl == "\r\n":
        out = out.replace("\n", "\r\n")

    # --- last-moment concurrency guard ------------------------------------
    st1 = os.stat(MASTER)
    if (st1.st_mtime_ns, st1.st_size) != (st0.st_mtime_ns, st0.st_size):
        sys.exit("ABORT: master changed under us (mtime/size moved) — another session is writing")

    with io.open(MASTER, "w", encoding="utf-8", newline="") as f:
        f.write(out)

    print("deleted item13 값_적용후 on %d cells" % len(changed_idx))
    for r in payload["delete"]:
        print("  %s %-14s %s  mirrored=%s -> true=%s (over %+.2f, Dtier %+.2f)"
              % (r["code"], r["name"], r["q"], r["item13_mirrored"],
                 r["item13_true_implied"], r["over_by"], r["Dtier_item2_post_minus_pre"]))
    print("line ending preserved: %r ; size %d -> %d chars"
          % (nl, len(raw_before), len(out)))


if __name__ == "__main__":
    main()
