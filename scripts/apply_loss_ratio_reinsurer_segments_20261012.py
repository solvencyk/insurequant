#!/usr/bin/env python3
"""Ticket 20261012T0900Z (1): reinsurer (KR1101~KR1107) loss-ratio label standardization -- master `세그먼트`/`상품구분` only.

Dry run (default): rebuilds the master in memory with build_loss_ratio_master.REINSURER_SEG_RULES and proves
  * non-reinsurer rows identical to the committed master (list equality),
  * reinsurer rows identical on every field except 세그먼트/상품구분 (multiset), row count unchanged (no add / delete),
  * row-level old-value guard (old 세그먼트/상품구분 of every reinsurer row is one of the values the loader wrote),
  * build_loss_ratio_master.verify() passes.
With --apply it writes (atomic): master_loss_ratio.json / .csv (non-reinsurer bytes are an exact prefix of the committed bytes) and
portfolio_taxonomy.csv (committed rows kept byte for byte; the 19 reinsurer-only rows the loader appended are replaced by the regenerated ones).
period_adoption.csv / master_census.csv are regenerated in memory and compared (they must be unchanged; they are not written).
Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/apply_loss_ratio_reinsurer_segments_20261012.py [--apply]
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_loss_ratio_master as M  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
LR = ROOT / "data" / "loss_ratio"
WORK = ROOT / "data" / "_derived" / "loss_ratio_label_std_20261012"
NEW = [f"KR110{i}" for i in range(1, 8)]
SEGFIELDS = ("세그먼트", "상품구분")
ALLOWED_OLD_SEG = {"", "생명보험", "손해보험", "장기손해보험"}
ALLOWED_OLD_PV = {"", "무배당", "유배당", "변액", "생명", "장기"}
LOG: list[str] = []


def log(s: str = "") -> None:
    LOG.append(s)
    print(s)


def other_key(r: dict) -> tuple:
    return tuple((k, json.dumps(r[k], ensure_ascii=False)) for k in M.ALL_COLS if k not in SEGFIELDS)


def read_src() -> list[dict]:
    gz = LR / "risk_premium_vs_expected_claims.json.gz"
    return M.read_json(gz if gz.exists() else LR / "risk_premium_vs_expected_claims.json")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    src = read_src()
    census = M.read_csv(LR / "census.csv")
    reg = M.load_registry()
    old_text = (LR / "master_loss_ratio.json").read_text(encoding="utf-8")
    old = json.loads(old_text)
    old_csv = (LR / "master_loss_ratio.csv").read_bytes().decode("utf-8-sig")
    res = M.build_from(src, census, reg)
    pub = [M.public_row(r) for r in res["master"]]
    log(f"committed master {len(old)} rows; rebuilt master {len(pub)} rows")

    # ---- proofs
    old_non = [r for r in old if r["원보험사코드"] not in NEW]
    new_non = [r for r in pub if r["원보험사코드"] not in NEW]
    ok_non = old_non == new_non
    log(f"non-reinsurer rows {len(old_non)} -> {len(new_non)}; identical: {ok_non}")
    old_re = [r for r in old if r["원보험사코드"] in NEW]
    new_re = [r for r in pub if r["원보험사코드"] in NEW]
    c_old, c_new = Counter(other_key(r) for r in old_re), Counter(other_key(r) for r in new_re)
    ok_re = c_old == c_new and len(old_re) == len(new_re)
    log(f"reinsurer rows {len(old_re)} -> {len(new_re)}; identical on the other {len(M.ALL_COLS) - 2} fields (added {sum((c_new - c_old).values())} / removed {sum((c_old - c_new).values())}): {ok_re}")
    guard_bad = [r for r in old_re if r["세그먼트"] not in ALLOWED_OLD_SEG or r["상품구분"] not in ALLOWED_OLD_PV]
    log(f"old-value guard (unexpected committed 세그먼트/상품구분 on a reinsurer row): {len(guard_bad)}")
    by_old = {other_key(r): r for r in old_re}
    by_new = {other_key(r): r for r in new_re}
    changed = Counter()
    trans = Counter()
    for k, o in by_old.items():
        n = by_new[k]
        fs = tuple(f for f in SEGFIELDS if o[f] != n[f])
        changed[fs] += 1
        trans[(o["원보험사코드"], o["세그먼트"], o["상품구분"], n["세그먼트"], n["상품구분"])] += 1
    log("changed field sets (rows): " + json.dumps({"+".join(k) or "unchanged": v for k, v in changed.items()}, ensure_ascii=False))
    left_prefix = [r for r in new_re if r["상품구분"] in ("생명", "장기")]
    log(f"reinsurer rows still carrying 상품구분 생명/장기: {len(left_prefix)}")
    errs, warns, stats = M.verify(src, pub)
    log(f"verify(rebuilt): errs {len(errs)} warns {len(warns)} stats { {k: v for k, v in stats.items() if k != 'src_dups'} }")
    for e in errs[:10]:
        log("   ERR " + e[:240])
    # ---- text-level prefix proofs
    new_json = json.dumps(pub, ensure_ascii=False, indent=2)
    pre_json = json.dumps(old_non, ensure_ascii=False, indent=2)[:-2]            # strip "\n]"
    json_prefix_ok = new_json.startswith(pre_json) and old_text.startswith(pre_json)
    log(f"master JSON: non-reinsurer bytes are an exact prefix of both the committed and the new file: {json_prefix_ok}")
    new_csv = M.csv_text(M.ALL_COLS, pub, M.format_cell)
    pre_csv = M.csv_text(M.ALL_COLS, old_non, M.format_cell)
    csv_prefix_ok = new_csv.startswith(pre_csv) and old_csv.startswith(pre_csv)
    log(f"master CSV: non-reinsurer bytes are an exact prefix of both the committed and the new file: {csv_prefix_ok}")
    # ---- aux tables
    adopt_text = M.csv_text(M.ADOPT_COLS, M.adoption_rows(res))
    mc_text = M.csv_text(M.MC_COLS, M.census_grid(res))
    adopt_same = adopt_text == (LR / "period_adoption.csv").read_bytes().decode("utf-8-sig")
    mc_same = mc_text == (LR / "master_census.csv").read_bytes().decode("utf-8-sig")
    log(f"period_adoption.csv regenerated == committed: {adopt_same}; master_census.csv regenerated == committed: {mc_same}")

    # ---- taxonomy: committed rows kept, reinsurer-only rows replaced
    tax_bytes = (LR / "portfolio_taxonomy.csv").read_bytes().decode("utf-8-sig")
    tax_lines = tax_bytes.splitlines(keepends=True)
    tax_rows = list(csv.DictReader(io.StringIO(tax_bytes, newline="")))
    assert len(tax_lines) == len(tax_rows) + 1, "multi-line cell in taxonomy"
    is_re = [all(c in NEW for c in r["회사목록"].split(",")) for r in tax_rows]
    n_re_tail = 0
    for flag in reversed(is_re):
        if not flag:
            break
        n_re_tail += 1
    assert sum(is_re) == n_re_tail, "reinsurer-only taxonomy rows are not a contiguous tail"
    base_lines = tax_lines[: len(tax_lines) - n_re_tail]
    base_rows = tax_rows[: len(tax_rows) - n_re_tail]
    base_keys = {(r["원문구분"], r["원문포트폴리오"], r["세그먼트"]): r for r in base_rows}
    # regenerated reinsurer-only census: restrict the std tax to reinsurer codes
    tax_re = {}
    for tkey, t in res["tax"].items():
        by = {c: n for c, n in t["by_code"].items() if c in NEW}
        if by:
            tax_re[tkey] = {"codes": set(by), "n": sum(by.values()), "by_code": Counter(by)}
    res_re = dict(res, tax=tax_re)
    cand = M.taxonomy_rows(res_re)
    add_rows, covered, conflict = [], 0, []
    for r in cand:
        k3 = (r["원문구분"], r["원문포트폴리오"], r["세그먼트"])
        b = base_keys.get(k3)
        if b is None:
            add_rows.append(r)
        else:
            covered += 1
            if (b["표준_구분"], b["표준_상품구분"], b["표준_포트폴리오"]) != (r["표준_구분"], r["표준_상품구분"], r["표준_포트폴리오"]):
                conflict.append((k3, (b["표준_구분"], b["표준_상품구분"], b["표준_포트폴리오"]), (r["표준_구분"], r["표준_상품구분"], r["표준_포트폴리오"])))
    log(f"taxonomy: committed {len(tax_rows)} rows (reinsurer-only tail {n_re_tail}); regenerated reinsurer label rows {len(cand)} = {len(add_rows)} new key + {covered} already in the committed non-reinsurer rows; standard-triple conflicts {len(conflict)}")
    for c in conflict[:10]:
        log(f"   TAX CONFLICT {c}")
    tail_text = M.csv_text(M.TAX_COLS, add_rows).splitlines(keepends=True)[1:]          # drop header
    new_tax = "".join(base_lines) + "".join(tail_text)

    # ---- mapping evidence (per label x reinsurer)
    write_mapping(old_re, new_re, by_old, by_new)

    good = ok_non and ok_re and not guard_bad and not left_prefix and not errs and json_prefix_ok and csv_prefix_ok and adopt_same and mc_same and not conflict
    log(f"ALL PROOFS PASS: {good}")
    (WORK / "apply_log.txt").write_text("\n".join(LOG), encoding="utf-8")
    (WORK / "transitions.txt").write_text("\n".join(f"{'|'.join(map(str, k))}\t{v}" for k, v in sorted(trans.items())), encoding="utf-8")
    if not args.apply:
        log("dry run only (no data/loss_ratio writes)")
        (WORK / "apply_log.txt").write_text("\n".join(LOG), encoding="utf-8")
        return
    if not good:
        log("STOP: proofs failed - not applying")
        (WORK / "apply_log.txt").write_text("\n".join(LOG), encoding="utf-8")
        sys.exit(2)
    M.atomic_write(LR / "master_loss_ratio.json", new_json)
    M.atomic_write(LR / "master_loss_ratio.csv", new_csv, encoding="utf-8-sig")
    M.atomic_write(LR / "portfolio_taxonomy.csv", new_tax, encoding="utf-8-sig")
    log("WROTE master_loss_ratio.json / .csv, portfolio_taxonomy.csv")
    (WORK / "apply_log.txt").write_text("\n".join(LOG), encoding="utf-8")


EVIDENCE = {
    "KR1101": ("prefix", "원문 라벨이 `생명`/`장기` 접두어를 직접 인쇄(생명사망·생명건강·생명복합·장기복합). 같은 공시본 4-6-2 표(2025.4Q 공시 p17)의 상품유형 열이 건강·복합·사망 = `생명`, 복합 = `장기손해`로 일치. 합계는 생명+장기손해 혼합이라 세그먼트 공란."),
    "KR1103": ("prefix", "원문 라벨이 `생명`/`장기` 접두어를 직접 인쇄(생명사망·생명건강·장기질병; 4-6-2 표는 상품유형 `생명,장기손해` 한 칸에 무배당생명사망·무배당생명건강·무배당장기질병 라벨, 2025.4Q 공시 p9). 합계는 혼합이라 세그먼트 공란."),
    "KR1102": ("printed", "표 안 머리글 `[생명보험]` / `[손해보험]`(2025.4Q 공시 p23-26, 2024.4Q 공시 p20-21). `[손해보험]` 표의 포트폴리오는 무배당상해·무배당질병뿐이고 합계가 그 합으로 닫혀(일반·자동차 행 없음) 4-6-2 표(p17-18)의 상품유형 `장기손해` 행과 같다 -> `장기손해보험`. 각 합계는 자기 머리글의 세그먼트."),
    "KR1106": ("printed", "2024.4Q 공시 p15 표에 `생명보험`/`장기손해보험` 머리글이 이미 표준명. 단 마스터 채택 블록(2025.4Q 공시의 <2024>·<2025>)은 두 종목을 합산한 한 덩어리(합계 130,263 = 생명+장기손해 합, 포트폴리오 3개)라 세그먼트 분리 불가 -> 공란(추정 안 함)."),
    "KR1104": ("all", "표가 한 덩어리(세그먼트 머리글 없음). 같은 공시본 4-6-2 표(2025.4Q 공시 p16-17, 2024.4Q 공시 p16-17)의 상품유형 열이 전 행 `장기손해`(생명 행 없음) -> 전 행 `장기손해보험`, 합계도 같은 세그먼트."),
    "KR1105": ("all", "표가 한 덩어리(세그먼트 머리글 없음). 같은 공시본 4-6-2 표(2025.4Q 공시 p15-16, 2024.4Q 공시 p16-17)의 상품유형 열이 전 행 `장기손해`(무배당사망·무배당건강 포함) -> 전 행 `장기손해보험`, 합계도 같은 세그먼트. [owner 확인 요청] 사망·건강 포트폴리오도 원문이 장기손해로 인쇄."),
    "KR1107": ("table462", "표가 한 덩어리(세그먼트 머리글 없음). 같은 공시본 4-6-2 표(2025.4Q 공시 p16-18)의 상품유형 열: `생명` = Non-Par 무배당사망·무배당건강, `장기손해` = 나머지(상해·질병·재물·연금저축·자산연계형연금저축·기타; Non-Par·Direct-Par·Indirect-Par). 합계는 생명+장기손해 혼합이라 세그먼트 공란."),
}
KR1000_MAP = [
    ("생명/전통형재보험", "생명보험", "전통형(일반) 재보험", "코리안리 표기는 변경하지 않음. 새 표준 `생명보험` 과 같은 그룹(재보험 방식 접미 없음 = 전통형)"),
    ("장기손해/전통형재보험", "장기손해보험", "전통형(일반) 재보험", "코리안리 표기는 변경하지 않음. 새 표준 `장기손해보험` 과 같은 그룹"),
    ("생명/공동재보험", "생명보험/공동재보험", "공동재보험(금융재보험, 금재)", "코리안리 표기는 변경하지 않음. 새 표준 `생명보험/공동재보험` 에 대응"),
    ("장기손해/공동재보험", "장기손해보험/공동재보험", "공동재보험(금융재보험, 금재)", "코리안리 표기는 변경하지 않음. 새 표준 `장기손해보험/공동재보험` 에 대응"),
]
MAP_COLS = ["회사", "원문구분", "원문포트폴리오", "원문세그먼트", "표준화전_상품구분(마스터)", "표준_세그먼트", "표준_구분", "표준_상품구분", "표준_포트폴리오", "행수", "적용규칙", "판정근거(쪽=공시본 PDF 쪽)"]


def write_mapping(old_re, new_re, by_old, by_new) -> None:
    rows = Counter()
    for k, o in by_old.items():
        n = by_new[k]
        rows[(o["원보험사코드"], o["원문구분"], o["원문포트폴리오"], o["세그먼트"], o["상품구분"], n["세그먼트"], n["구분"], n["상품구분"], n["포트폴리오"])] += 1
    out = []
    for key, cnt in sorted(rows.items(), key=lambda kv: (kv[0][0], kv[0][5], kv[0][6], kv[0][8], kv[0][2])):
        code, gb_raw, pf_raw, seg_o, pv_o, seg_n, gb, pv_n, pf = key
        kind, why = EVIDENCE[code]
        rule = kind
        if code == "KR1106" and seg_n == "":
            rule = "none(합산 블록, 세그먼트 공란)"
        elif code in ("KR1101", "KR1103", "KR1107") and gb == "합계":
            rule = f"{kind}(혼합 합계 -> 공란)"
        out.append({"회사": code, "원문구분": gb_raw, "원문포트폴리오": pf_raw, "원문세그먼트": seg_o, "표준화전_상품구분(마스터)": pv_o, "표준_세그먼트": seg_n,
                    "표준_구분": gb, "표준_상품구분": pv_n, "표준_포트폴리오": pf, "행수": cnt, "적용규칙": rule, "판정근거(쪽=공시본 PDF 쪽)": why})
    for raw, std, how, why in KR1000_MAP:
        out.append({"회사": "KR1000", "원문구분": "", "원문포트폴리오": "", "원문세그먼트": raw, "표준화전_상품구분(마스터)": "", "표준_세그먼트": std, "표준_구분": "", "표준_상품구분": "",
                    "표준_포트폴리오": "", "행수": "", "적용규칙": f"대응표(코리안리 행은 그대로) / {how}", "판정근거(쪽=공시본 PDF 쪽)": why})
    text = M.csv_text(MAP_COLS, out)
    with open(WORK / "reinsurer_label_mapping.csv", "w", encoding="utf-8-sig", newline="") as fh:
        fh.write(text)


if __name__ == "__main__":
    main()
