#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""경영공시 PL 백필 후속 정정 (2026-10-09, parser/ifrs17 단일 병합자).

validation 결함 D1/D6/D8 처리. `merge_pl_backfill_disclosure_20261008.py` 의 후속이며 같은 규칙을 따른다
(루트 PL_breakdown.json + PL_breakdown_provenance.json 만 쓴다, build_root_masters 미호출, 허가 집합 밖
기존 행이 1칸이라도 바뀌면 abort).

1) KR0004 2025.3Q 채움 (D1 coverage_hole 예별 2025.3Q 통째).
   원문 별도 포괄손익계산서 제1(당)3분기 = 신설법인 제1기 2025-06-16~09-30. 그 법인의 회계기간 누계이므로
   연누계 열에 싣는다. 이전 칸(2Q = MG 1/1~6/30)과 같은 법인·같은 기간 축이 아니라서 값_당분기 = None
   (차분 금지). 1·22·23·24 만 싣고 17/20/21 은 §3d 때문에 보류 파일에 추가한다.
2) 보험손익(1) 보류 15칸 (D1 pl_bridge 신규 실패 15건).
   DART 2023 분기 행은 LOB 다리(2·3·8·12·13·14 등)가 부분 추출이거나 비어 있다. 경영공시 요약표의 보험손익을
   넣으면 검증 pl_bridge 가 "다리 합 != 보험손익" 으로 실패한다(15/15 가 이 유형 -- 값이 틀린 게 아니라
   다리가 없다: KB라이프·코리안리는 보험손익 = 다리합 - 기타사업비용 으로 반올림 폭 안에서 닫히지만 기타영업수익(15)
   이 None 이라 검증이 그 후보를 만들지 않는다). 다리를 잔차로 역산해 채우는 것은 검증을 무력화하므로 하지 않고,
   1 만 비운다. 22/23/24/16 은 그대로. 값은 보류 파일 `held_item1_bridge_20261009` 에 근거와 함께 남긴다.
3) 값_당분기 차분 (D6). 값이 있는데 값_당분기가 None 인 칸 중 같은 해 직전 분기 누계가 마스터에 있는 칸은
   차분으로 채운다(억원 반올림 소스와 DART 원값의 혼합이라 오차 +-50백만 이내). KR0071 은 직전(1Q DART)
   누계가 경영공시와 -73% 어긋나는 앵커 이상(D2)이라 None 유지.

실행:
    $py scripts/fix_pl_backfill_followup_20261009.py            # dry-run
    $py scripts/fix_pl_backfill_followup_20261009.py --apply
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import merge_pl_backfill_disclosure_20261008 as M  # noqa: E402  (chdir ROOT, utf-8 stdout)

ROOT = M.ROOT
BACKUP = ROOT / "data" / "_derived" / "bspl_backfill_backup_20261008"
OUT_MANIFEST = ROOT / "data" / "_derived" / "pl_followup_20261009.json"

HOLD_ITEM1 = [  # (원수사명, 분기)
    ("KB라이프생명", "2023.1Q"), ("KB라이프생명", "2023.2Q"), ("NH농협손해보험", "2023.2Q"),
    ("교보생명보험", "2023.1Q"), ("교보생명보험", "2023.2Q"), ("농협생명보험", "2023.1Q"),
    ("농협생명보험", "2023.2Q"), ("메트라이프생명보험", "2023.4Q"), ("비엔피파리바카디프생명보험", "2023.4Q"),
    ("삼성생명보험", "2023.1Q"), ("삼성생명보험", "2023.2Q"), ("예별손해보험", "2023.4Q"),
    ("코리안리재보험", "2023.1Q"), ("코리안리재보험", "2023.2Q"), ("흥국생명보험", "2023.2Q"),
]
HOLD_REASON = ("경영공시 요약표 보험손익. DART 2023 행의 LOB 다리가 부분/결측이라 pl_bridge(보험손익 = 다리합 + "
               "기타영업수익 - 기타사업비용)를 닫을 수 없어 보류. 값 자체는 같은 표의 22/23/24 와 항등식이 닫힌다. "
               "다리가 채워지면(또는 validation/owner 가 등재를 결정하면) 그대로 싣는다.")
DANGI_SKIP_CODES = {"KR0071"}   # D2 앵커 이상
K3Q = ("KR0004", "2025.3Q")
K3Q_ITEMS = (1, 22, 23, 24)


def qkey(q):
    return int(q[:4]), int(q[5])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    raw_m = M.MASTER.read_bytes()
    raw_s = M.SIDECAR.read_bytes()
    raw_t = M.STAGED_OUT.read_bytes()
    rows = json.loads(raw_m.decode("utf-8"))
    side = json.loads(raw_s.decode("utf-8"))
    staged = json.loads(raw_t.decode("utf-8"))
    for name, raw, obj in (("master", raw_m, rows), ("sidecar", raw_s, side), ("staged", raw_t, staged)):
        if json.dumps(obj, ensure_ascii=False, indent=1).replace(chr(10), chr(13) + chr(10)).encode("utf-8") != raw:
            M.fail(f"{name} 가 indent=1 왕복과 바이트 불일치 -- 쓰면 공백 diff 가 생긴다")
    mtimes = {p: p.stat().st_mtime_ns for p in (M.MASTER, M.SIDECAR, M.STAGED_OUT)}

    by_key = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in rows}
    name2code = {r["원수사명"]: r["원보험사코드"] for r in rows}
    meta = {}
    for r in rows:
        meta.setdefault(r["원보험사코드"], {k: r[k] for k in ("원수사명", "티커", "생손보여부")})
    snapshot = {k: json.dumps(v, ensure_ascii=False, sort_keys=True) for k, v in by_key.items()}
    orig = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r
            for r in json.loads((BACKUP / "PL_breakdown.json").read_text(encoding="utf-8"))}
    side_idx = {(x["company_code"], x["quarter"], x["item_block"]): x for x in side["cells"]}
    parts = M.load_parts()

    allowed = set()      # 이번 실행이 바꿀 수 있는 칸
    new_rows = []
    log = {"fill_2025_3Q": [], "hold_item1": [], "dangi": [], "dangi_skipped": []}

    # ---- 1) KR0004 2025.3Q ----
    for it in K3Q_ITEMS:
        k = (K3Q[0], it, K3Q[1])
        spec = parts.get(k)
        if spec is None:
            M.fail(f"파트에 {k} 없음")
        r = by_key.get(k)
        if r is not None and r.get("값") is not None:
            M.fail(f"이미 값이 있다 {k}")
        if r is not None:
            if r.get("항목명") != M.MASTER_ITEM_NAME[it]:
                M.fail(f"항목명 불일치 {k}")
            r["값"], r["값_당분기"] = spec["값"], None
        else:
            m = meta[K3Q[0]]
            new_rows.append({"원보험사코드": K3Q[0], "원수사명": m["원수사명"], "티커": m["티커"],
                             "생손보여부": m["생손보여부"], "항목번호": it, "항목명": M.MASTER_ITEM_NAME[it],
                             "공시분기": K3Q[1], "값": spec["값"], "값_당분기": None})
        allowed.add(k)
        log["fill_2025_3Q"].append([it, spec["값"]])
    g = {it: parts[(K3Q[0], it, K3Q[1])]["값"] for it in K3Q_ITEMS}
    if abs(g[22] - g[23] - g[24]) > 0.01:
        M.fail("2025.3Q 24=22-23 불일치")
    pdf, page = parts[(K3Q[0], 1, K3Q[1])]["pdf"], parts[(K3Q[0], 1, K3Q[1])]["page"]
    if not (ROOT / pdf).exists():
        M.fail(f"pdf 없음 {pdf}")
    bucket = {"file": pdf, "how": "disclosure_summary_pl", "items": list(K3Q_ITEMS)}
    sk = (K3Q[0], K3Q[1], "income_statement")
    cell = side_idx.get(sk)
    if cell is None:
        side["cells"].append({
            "company_code": K3Q[0], "quarter": K3Q[1], "item_block": "income_statement",
            "source_id": "DISCLOSURE", "source_file": pdf, "source_files": [bucket],
            "resolution": "disclosure_summary_pl", "published_items": len(K3Q_ITEMS), "schema_items": 24})
    else:
        for b in cell.get("source_files") or []:
            if set(b["items"]) & set(K3Q_ITEMS):
                M.fail(f"사이드카 버킷 중복 {sk}")
        cell.setdefault("source_files", []).append(bucket)
        cell["published_items"] = cell.get("published_items", 0) + len(K3Q_ITEMS)
    # 보류(17/20/21) 추가
    for it in (17, 20, 21):
        sp = parts.get((K3Q[0], it, K3Q[1]))
        if sp is not None:
            staged["cells"][f"{K3Q[0]}|{it}|{K3Q[1]}"] = {
                "값": sp["값"], "pdf": sp["pdf"], "page": sp["page"], "scale": sp["scale"],
                "part_file": sp["file"]}

    # ---- 2) 보험손익(1) 보류 ----
    held = staged.setdefault("held_item1_bridge_20261009", {})
    for nm, q in HOLD_ITEM1:
        code = name2code[nm]
        k = (code, 1, q)
        r = by_key.get(k)
        if r is None or r.get("값") is None:
            M.fail(f"보류 대상 값 없음 {k}")
        if orig.get(k) is not None and orig[k].get("값") is not None:
            M.fail(f"원본(백업)에 값이 있는 칸은 보류 금지 {k}")
        held[f"{code}|1|{q}"] = {"값": r["값"], "원수사명": nm, "사유": HOLD_REASON}
        log["hold_item1"].append([code, q, r["값"]])
        r["값"], r["값_당분기"] = None, None
        allowed.add(k)
        cell = side_idx.get((code, q, "income_statement"))
        if cell is None:
            M.fail(f"사이드카 블록 없음 {code} {q}")
        hit = 0
        for b in cell["source_files"]:
            if str(b["file"]).startswith("data/disclosure/") and 1 in b["items"]:
                b["items"] = [x for x in b["items"] if x != 1]
                hit += 1
        if hit != 1:
            M.fail(f"사이드카 DISCLOSURE 버킷에서 item1 을 못 찾음 {code} {q} ({hit})")
        cell["published_items"] = cell.get("published_items", 1) - 1
    staged["_note_held_item1"] = ("2026-10-09: pl_bridge 신규 실패 15건 회피를 위해 보험손익(1) 15칸을 마스터에서 "
                                   "내리고 여기 보관한다(정정이 아니라 보류).")

    # ---- 3) 값_당분기 차분 ----
    cur = {k: r for k, r in by_key.items()}
    for r in new_rows:
        cur[(r["원보험사코드"], r["항목번호"], r["공시분기"])] = r
    pair_res = defaultdict(dict)
    for k, r in sorted(cur.items(), key=lambda x: (x[0][0], str(x[0][1]), qkey(x[0][2]))):
        c, it, q = k
        if r.get("값") is None or r.get("값_당분기") is not None or q.endswith("1Q"):
            continue
        # 이번 백필로 새로 채워진 칸만(원본에 값이 없던 칸)
        o = orig.get(k)
        if o is not None and o.get("값") is not None:
            continue
        if k == (K3Q[0], it, K3Q[1]):
            continue    # 의도적 None
        if c in DANGI_SKIP_CODES:
            log["dangi_skipped"].append([c, it, q, "D2 앵커 이상"])
            continue
        y, n = qkey(q)
        pv = cur.get((c, it, f"{y}.{n - 1}Q"))
        if pv is None or pv.get("값") is None:
            log["dangi_skipped"].append([c, it, q, "직전분기 누계 없음"])
            continue
        pair_res[(c, q)][it] = (r, round(r["값"] - pv["값"], 6))
    for (c, q), g2 in sorted(pair_res.items()):
        d = {it: v[1] for it, v in g2.items()}
        if all(i in d for i in (22, 23, 24)) and abs(d[22] - d[23] - d[24]) > 150.0:
            for it in g2:
                log["dangi_skipped"].append([c, it, q, f"당분기 항등식 불일치 {d[22] - d[23] - d[24]}"])
            continue
        for it, (r, val) in g2.items():
            r["값_당분기"] = val
            allowed.add((c, it, q))
            log["dangi"].append([c, it, q, r["값"], val])

    # ---- 검증 ----
    changed = [k for k, s in snapshot.items() if json.dumps(by_key[k], ensure_ascii=False, sort_keys=True) != s]
    if set(changed) - allowed:
        M.fail(f"허가 밖 기존 행이 바뀌었다: {sorted(set(changed) - allowed)[:10]}")
    out = rows + new_rows
    if len({(r["원보험사코드"], r["항목번호"], r["공시분기"]) for r in out}) != len(out):
        M.fail("키 중복")
    print("=" * 78)
    print(f"2025.3Q 채움 {len(log['fill_2025_3Q'])}칸(신규행 {len(new_rows)}) · 보험손익 보류 {len(log['hold_item1'])}칸 · "
          f"당분기 차분 {len(log['dangi'])}칸 · 당분기 스킵 {len(log['dangi_skipped'])}칸")
    for x in log["dangi_skipped"]:
        print("  skip", x)
    print(f"  기존 행 변경 {len(changed)} (허가 {len(allowed)}), 신규 행 {len(new_rows)}")
    print("=" * 78)
    if not args.apply:
        print("dry-run -- 아무것도 쓰지 않았다.")
        return
    for p, t in mtimes.items():
        if p.stat().st_mtime_ns != t:
            M.fail(f"읽은 뒤 {p.name} 이 바뀌었다 -- 동시 세션 의심")
    side["merge_note_20261009"] = ("PL 후속 정정(D1/D6): KR0004 2025.3Q 채움 · 보험손익 15칸 보류 · 값_당분기 차분. "
                                    "재현: scripts/fix_pl_backfill_followup_20261009.py --apply")
    M.MASTER.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    M.SIDECAR.write_text(json.dumps(side, ensure_ascii=False, indent=1), encoding="utf-8")
    M.STAGED_OUT.write_text(json.dumps(staged, ensure_ascii=False, indent=1), encoding="utf-8")
    OUT_MANIFEST.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {M.MASTER.name} ({len(out)} rows), {M.SIDECAR.name}, {M.STAGED_OUT.name}, {OUT_MANIFEST.name}")


if __name__ == "__main__":
    main()
