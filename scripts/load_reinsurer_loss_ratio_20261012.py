#!/usr/bin/env python3
"""Stage 3 (ticket 20261012T0100Z): append reinsurer (KR1101~KR1107) + KR1108/KR1011 loss-ratio evidence to data/loss_ratio/ -- ADDITIONS ONLY.

Dry run (default): builds everything in memory, proves that the existing rows are untouched, writes the proof + the new rows to
data/_derived/reinsurer_loss_ratio_20261012/ and prints a summary. With --apply it backs the files up first, then appends:
  risk_premium_vs_expected_claims.json  (+ reinsurer table-B long rows, text append)
  claims_ae_ratio.json                  (+ reinsurer table-A rows, text append)
  census.csv                            (+ reinsurer / KR1011 / KR1108 census rows)
  master_loss_ratio.json / .csv         (+ reinsurer master rows, same layout)
  period_adoption.csv / master_census.csv / portfolio_taxonomy.csv (+ rows for the new codes / new labels only)
It never rewrites an existing row: the existing bytes are a verified prefix of the new bytes (the script checks that after writing).
Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/load_reinsurer_loss_ratio_20261012.py [--apply]
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_loss_ratio_master as M  # noqa: E402
import extract_loss_ratio as X  # noqa: E402

if sys.stdout.encoding is None or "utf" not in sys.stdout.encoding.lower():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

LR = ROOT / "data" / "loss_ratio"
WORK = ROOT / "data" / "_derived" / "reinsurer_loss_ratio_20261012"
BACKUP = WORK / "backup_before"
NEW_CODES = [f"KR110{i}" for i in range(1, 9)] + ["KR1011"]
ROW_ORDER = ["원보험사코드", "원수사명", "생손보여부", "공시분기", "기준연도", "구분", "구분_원문", "포트폴리오", "포트폴리오_원문", "경과기간", "지표",
             "값", "단위", "dash", "출처", "추출방식", "원천위치"]
FILES = ["risk_premium_vs_expected_claims.json", "claims_ae_ratio.json", "census.csv", "master_loss_ratio.json", "master_loss_ratio.csv",
         "period_adoption.csv", "master_census.csv", "portfolio_taxonomy.csv", "panel_loss_ratio.json", "source_errata.csv"]
LOGL: list[str] = []
ERRATA_COLS = ["원보험사코드", "공시분기", "기준연도", "사업구분", "부문", "구분", "포트폴리오", "경과기간", "지표", "인쇄값", "추정값", "근거"]
ERRATA_ADD = [
    {"원보험사코드": "KR1106", "공시분기": "2025.4Q", "기준연도": "2024", "사업구분": "", "부문": "", "구분": "Non-Par", "포트폴리오": "무배당질병", "경과기간": "현재가치",
     "지표": "비율", "인쇄값": "84", "추정값": "96.95",
     "근거": "2025.4Q PDF p20 렌더 PNG(130dpi)로 직접 확인: 현재가치 비율 84% 인쇄. 같은 칸 예상보험금 11,535·위험보험료 11,898 (A÷B=96.95%)이고 두 금액 모두 합계 현재가치(130,263·138,666) = Σ포트폴리오로 닫힘 -> 비율 칸만 틀린 인쇄로 판단, 값은 인쇄 그대로"},
    {"원보험사코드": "KR1106", "공시분기": "2025.4Q", "기준연도": "2024", "사업구분": "", "부문": "", "구분": "Non-Par", "포트폴리오": "무배당기타", "경과기간": "현재가치",
     "지표": "비율", "인쇄값": "86", "추정값": "93.66",
     "근거": "2025.4Q PDF p20 렌더 PNG(130dpi)로 직접 확인: 현재가치 비율 86% 인쇄. 같은 칸 예상보험금 118,725·위험보험료 126,764 (A÷B=93.66%)이고 두 금액 모두 합계 현재가치 = Σ포트폴리오로 닫힘 -> 비율 칸만 틀린 인쇄로 판단, 값은 인쇄 그대로"},
]


def log(s: str = "") -> None:
    LOGL.append(s)
    print(s)


def order_row(r: dict) -> dict:
    out = {k: r[k] for k in ROW_ORDER if k in r}
    for k, v in r.items():
        if k not in out:
            out[k] = v
    return out


# ------------------------------------------------------------------ source rows
def new_source_rows() -> list[dict]:
    rows = json.loads((WORK / "reinsurer_B_rows.json").read_text(encoding="utf-8"))
    out = []
    for r in rows:
        d = {k: v for k, v in r.items() if k in M.KNOWN_FIELDS}
        for f in r.get("플래그") or []:
            if f.startswith("라벨보정:"):
                d["라벨보정"] = f[len("라벨보정:"):]
        for k in ("부문", "사업구분"):
            if d.get(k) in (None, ""):
                d.pop(k, None)
        raw_pf = (d.get("포트폴리오_원문") or "").replace(" ", "")
        if raw_pf[:2] in M.LINE_PREFIXES and d.get("포트폴리오") == raw_pf[2:]:
            d["포트폴리오"] = raw_pf          # the generic extractor strips the 보험종목 prefix (`생명사망` -> `사망`); keep it (it is the standard 상품구분 here, and 생명복합/장기복합 must stay distinct)
        out.append(order_row(d))
    return apply_errata(out)


def errata_dict() -> dict:
    ed = X.load_errata()
    for r in ERRATA_ADD:
        yr = int(r["기준연도"]) if r["기준연도"] else None
        note = f"원문오기 인쇄 {r['인쇄값']} -> 추정 {r['추정값']}: {r['근거']}"
        ed.setdefault((r["원보험사코드"], r["공시분기"]), {})[(yr, r["사업구분"], r["부문"], r["구분"], r["포트폴리오"], r["경과기간"], r["지표"])] = note
    return ed


def apply_errata(rows: list[dict]) -> list[dict]:
    ed = errata_dict()
    for r in rows:
        e = ed.get((r["원보험사코드"], r["공시분기"]))
        if not e:
            continue
        seg = r.get("사업구분") or ""
        for k, note in e.items():
            if k[0] in (None, r["기준연도"]) and k[1] in ("", seg) and (k[2] or "") == (r.get("부문") or "") and k[3] == r["구분"]                     and k[4] == r["포트폴리오"] and k[5] == r["경과기간"] and k[6] == r["지표"]:
                r["원문오기"] = note
    return rows


def new_census_rows(src_new: list[dict], ext_census: list[dict], meta) -> list[dict]:
    blocks = defaultdict(list)
    for r in src_new:
        blocks[(r["원보험사코드"], r["공시분기"], r["기준연도"])].append(r)
    # blocks produced by the grid / forced-year readers (the generic extractor census row is replaced for these)
    replaced = {("KR1101", "2024.4Q"), ("KR1101", "2025.4Q"), ("KR1102", "2024.4Q"), ("KR1102", "2025.4Q"), ("KR1107", "2025.4Q"), ("KR1106", "2024.4Q"), ("KR1106", "2025.4Q")}
    out = []
    seen = set()
    for c in ext_census:
        k = (c["원보험사코드"], c["공시분기"], c["표"], str(c["기준연도"]))
        c = dict(c)
        if c["표"] == "B" and (c["원보험사코드"], c["공시분기"]) in replaced and c["기준연도"] != "":
            yr = int(c["기준연도"])
            blk = blocks.get((c["원보험사코드"], c["공시분기"], yr))
            if blk:
                pages = sorted({r["출처"]["page"] for r in blk})
                how = {"KR1101": "격자판독(표 테두리 셀)", "KR1102": "격자판독(표 테두리 셀)", "KR1107": "격자판독(표 테두리 셀)"}.get(c["원보험사코드"], "좌표판독(연도 강제)" if c["공시분기"] == "2024.4Q" else "일반 추출기")
                ey = {k[2:]: note for k, note in errata_dict().get((c["원보험사코드"], c["공시분기"]), {}).items() if k[0] in (None, yr)}
                st = X.check_B_rows([dict(r, 부문=r.get("사업구분"), _dec=_dec_of(r)) for r in blk], ey)
                n_ok_r = st["ratio_checked"] - st["ratio_fail"]
                n_ok_t = st["total_checked"] - st["total_fail"]
                why = (f"본문 쪽 {','.join(map(str, pages))}; {how}; 비율≈A÷B {n_ok_r}/{st['ratio_checked']} 통과, 합계=Σ포트폴리오 {n_ok_t}/{st['total_checked']} 통과")
                status = "FILLED"
                notes = []
                if any("year_from_disclosure" in " ".join(r.get("플래그") or []) for r in blk):
                    notes.append("연도 캡션 행이 없어 공시 당해연도로 둠(같은 회사 후속 공시의 전기 블록과 대조)")
                if any("year_forced" in " ".join(r.get("플래그") or []) for r in blk):
                    notes.append("연도 캡션 <2024년>(쪽 15)은 있으나 일반 추출기가 읽지 못해 연도를 직접 지정(좌표판독); 사업구분 생명보험/장기손해보험은 표 안 머리글 순서")
                if any("10억원" in " ".join(r.get("플래그") or []) for r in blk):
                    notes.append("전 칸 10억원 단위 반올림 인쇄(끝자리 0) -> 비율 재계산이 반올림 폭 안에서 어긋나는 칸이 있고 합계=Σ 는 ±(항목수x5억) 오차")
                    status = "FILLED_CHECK_FLAGS"
                if st["ratio_fail"] or st["total_fail"]:
                    notes.append(f"검산 불일치 비율 {st['ratio_fail']}·합계 {st['total_fail']}: " + " | ".join(st["fails"][:2]))
                    status = "FILLED_CHECK_FLAGS"
                if st["errata_hit"]:
                    why += f"; 원문오기 등재 {len(st['errata_hit'])}칸 플래그(해당 칸의 비율 {st['ratio_errata']}건·합계 {st['total_errata']}건 검산 제외; 렌더 확인)"
                if notes:
                    why += "; " + "; ".join(notes)
                c.update({"상태": status, "추출방식": "text", "원천위치": "본문", "쪽": ",".join(map(str, pages)), "셀수": len(blk),
                          "값있는셀수": sum(1 for r in blk if r.get("값") is not None), "근거": why})
        if c["표"] == "B" and c["원보험사코드"] == "KR1105" and c["공시분기"] == "2024.4Q" and c["기준연도"] == "2023" and c["상태"] == "FILLED_CHECK_FLAGS":
            c["상태"] = "FILLED"
            c["근거"] += " || 2026-10-12: 검산(비율 82/82·합계 32/32)은 통과, 라벨 `무배당복합` 만 비표준이었으나 표준 포트폴리오 `복합` 을 사전에 추가해 해소"
        if c["표"] == "A" and c["원보험사코드"] == "KR1105" and c["공시분기"] == "2023.4Q" and c["상태"] == "PARSE_FAILED":
            c["상태"] = "ABSENT_IN_SOURCE"
            c["근거"] = "쪽 10 의 예상손해율·실제손해율 단어는 이익수수료 서술문(요약 포괄손익계산서 주석)이며 표 ① 이 아니다; 2023.4Q 결산본에는 4-6-4 최적가정 절 자체가 없다(최적가정 키워드 0건)"
            c["쪽"] = ""
        out.append(c)
        seen.add(k)
    return out


def _dec_of(r: dict) -> int:
    v = r.get("값")
    if v is None:
        return 0
    fl = " ".join(r.get("플래그") or [])
    if "10억원" in fl and r["지표"] != "비율":
        return -1
    s = repr(float(v))
    return len(s.split(".")[1].rstrip("0")) if "." in s else 0


def new_a_rows() -> list[dict]:
    a = json.loads((WORK / "ext_A.json").read_text(encoding="utf-8"))
    out = []
    for r in a:
        if r["원보험사코드"] not in NEW_CODES:
            continue
        r = dict(r)
        if r["원보험사코드"] == "KR1107" and r["공시분기"] == "2025.4Q":
            # the body copy is p25; the extractor picked the audit-report copy p186 (same numbers). Use the body page, record the copy.
            assert (r["예상손해율"], r["실제손해율"], r["예실차비율"]) in ((90.8, 97.9, -7.1), (88.2, 88.2, 0.1))
            r["출처"] = {"file": r["출처"]["file"], "page": 25}
            r["원천위치"] = "본문"
            r["플래그"] = list(r.get("플래그") or []) + ["감사보고서 사본 p186 과 값 일치(대조 완료)"]
        out.append(r)
    return out


# ------------------------------------------------------------------ helpers
def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    meta = X.load_company_meta()
    reg = M.load_registry()
    old_src = json.loads(read_text(LR / "risk_premium_vs_expected_claims.json"))
    old_census = M.read_csv(LR / "census.csv")
    old_master = json.loads(read_text(LR / "master_loss_ratio.json"))
    src_new = new_source_rows()
    ext_census = [r for r in M.read_csv(WORK / "ext_census.csv")]
    raw_rows = json.loads((WORK / "reinsurer_B_rows.json").read_text(encoding="utf-8"))
    census_new = new_census_rows(raw_rows, ext_census, meta)
    a_new = new_a_rows()
    log(f"new source rows {len(src_new)} / new census rows {len(census_new)} / new A rows {len(a_new)}")

    # --- baseline reproducibility + addition-only proof
    base = M.build_from(old_src, old_census, reg)
    full = M.build_from(old_src + src_new, old_census + census_new, reg)
    old_pub = [M.public_row(r) for r in base["master"]]
    log(f"baseline master (existing inputs) {len(old_pub)} rows; committed master {len(old_master)} rows; identical to committed: {old_pub == old_master}")
    full_pub = [M.public_row(r) for r in full["master"]]
    existing_rows_full = [r for r in full_pub if r["원보험사코드"] not in NEW_CODES]
    new_rows = [r for r in full_pub if r["원보험사코드"] in NEW_CODES]
    log(f"full master {len(full_pub)} rows; existing-code rows {len(existing_rows_full)}; new rows {len(new_rows)}")
    same_existing = existing_rows_full == old_pub
    log(f"existing-code rows in the full build identical to baseline: {same_existing}")
    committed_vs_full = existing_rows_full == old_master
    log(f"existing-code rows in the full build identical to the committed master: {committed_vs_full}")
    if not same_existing:
        log("STOP: the extended build changes existing rows")
        (WORK / "run_load_log.txt").write_text("\n".join(LOGL), encoding="utf-8")
        sys.exit(2)

    errs, warns, stats = M.verify(old_src + src_new, full_pub)
    new_errs = [e for e in errs if any(f" {c} " in e or f"'{c}'" in e or f"({c}" in e or f" {c}," in e for c in NEW_CODES)]
    log(f"verify(full): errs {len(errs)} (touching new codes {len(new_errs)}), warns {len(warns)}, stats {stats}")
    for e in errs[:25]:
        log("   ERR " + e[:260])
    for w in warns[:10]:
        log("   WARN " + w[:200])

    # --- aux tables (new codes / new labels only)
    adopt_all = M.adoption_rows(full)
    adopt_new = [r for r in adopt_all if r["원보험사코드"] in NEW_CODES]
    mc_all = M.census_grid(full)
    mc_old_codes = {r["원보험사코드"] for r in M.read_csv(LR / "master_census.csv")}
    mc_new = [r for r in mc_all if r["원보험사코드"] in NEW_CODES and r["원보험사코드"] not in mc_old_codes]
    tax_old = M.read_csv(LR / "portfolio_taxonomy.csv")
    tax_keys = {(r["원문구분"], r["원문포트폴리오"], r["세그먼트"]) for r in tax_old}
    tax_all = M.taxonomy_rows(full)
    tax_new = [r for r in tax_all if (r["원문구분"], r["원문포트폴리오"], r["세그먼트"]) not in tax_keys]
    tax_touched = [r for r in tax_all if (r["원문구분"], r["원문포트폴리오"], r["세그먼트"]) in tax_keys and any(c in r["회사목록"] for c in NEW_CODES)]
    log(f"period_adoption new {len(adopt_new)} / master_census new {len(mc_new)} (codes {sorted({r['원보험사코드'] for r in mc_new})}) / taxonomy new label rows {len(tax_new)} / existing taxonomy rows that would gain a reinsurer in 회사목록 (NOT edited) {len(tax_touched)}")

    # --- mapping table for the report
    map_rows = []
    for (raw_gb, raw_pf, seg, gb, pv, pf, note, flags), t in full["tax"].items():
        codes = sorted(c for c in t["codes"] if c in NEW_CODES)
        if codes:
            map_rows.append({"회사": ",".join(codes), "원문구분": raw_gb, "원문포트폴리오": raw_pf, "세그먼트": seg, "표준_구분": gb, "표준_상품구분": pv,
                             "표준_포트폴리오": pf, "플래그": ";".join(flags), "비고": note[:200]})
    map_rows.sort(key=lambda r: (r["회사"], r["세그먼트"], r["표준_구분"], r["표준_상품구분"], r["표준_포트폴리오"], r["원문포트폴리오"]))
    with open(WORK / "reinsurer_label_mapping.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(map_rows[0].keys()))
        w.writeheader()
        w.writerows(map_rows)
    for k in ("reinsurer_master_rows.json",):
        (WORK / k).write_text(json.dumps(new_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    with open(WORK / "reinsurer_adoption_rows.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=M.ADOPT_COLS)
        w.writeheader()
        w.writerows(adopt_new)

    # summary by (code, quarter)
    cnt = Counter((r["원보험사코드"], r["공시분기"]) for r in new_rows)
    log("new master rows by (code, quarter): " + ", ".join(f"{c}/{q}:{n}" for (c, q), n in sorted(cnt.items())))
    flg = Counter()
    for r in new_rows:
        for tok in filter(None, (t.strip() for t in r["플래그"].split(";"))):
            flg[tok.split("(")[0].split(":")[0]] += 1
    log("new master flag tokens: " + str(dict(flg.most_common())))
    for r in adopt_new:
        log(f"   adoption {r['원보험사코드']} {r['공시분기']}: {r['채택원천'][-60:]} | {r['플래그'][:160]} | {r['정정판정']}")
    for g in [g for g in mc_all if g["원보험사코드"] in NEW_CODES and g["상태"] == "결측"]:
        log(f"   missing {g['원보험사코드']} {g['공시분기']}: {g['결측사유']}")

    (WORK / "run_load_log.txt").write_text("\n".join(LOGL), encoding="utf-8")
    if not args.apply:
        log("dry run only (no data/loss_ratio writes)")
        return
    if errs:
        log("STOP: verify errors present - not applying")
        (WORK / "run_load_log.txt").write_text("\n".join(LOGL), encoding="utf-8")
        sys.exit(3)

    # ------------------------------------------------------------- apply
    BACKUP.mkdir(parents=True, exist_ok=True)
    for fn in FILES:
        shutil.copy2(LR / fn, BACKUP / fn)
    before = {fn: (LR / fn).read_bytes() for fn in FILES}

    def append_compact_json(fn: str, rows: list[dict]) -> None:
        raw = before[fn].decode("utf-8")
        assert raw.endswith("]")
        add = ",".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in rows)
        new = raw[:-1] + ("," if len(raw) > 2 else "") + add + "]"
        M.atomic_write(LR / fn, new)

    append_compact_json("risk_premium_vs_expected_claims.json", src_new)
    append_compact_json("claims_ae_ratio.json", a_new)

    def append_csv(fn: str, cols: list[str], rows: list[dict], fmt=None) -> None:
        raw = before[fn].decode("utf-8-sig")
        buf = io.StringIO(newline="")
        w = csv.writer(buf)
        for r in rows:
            w.writerow([(fmt(c, r.get(c)) if fmt else ("" if r.get(c) is None else r.get(c))) for c in cols])
        add = buf.getvalue()
        assert raw.endswith("\r\n")
        M.atomic_write(LR / fn, raw + add, encoding="utf-8-sig")

    raw_er = before["source_errata.csv"].decode("utf-8")
    buf = io.StringIO(newline="")
    w = csv.writer(buf, lineterminator="\n")
    for r in ERRATA_ADD:
        w.writerow([r[c] for c in ERRATA_COLS])
    assert raw_er.endswith("\n")
    M.atomic_write(LR / "source_errata.csv", raw_er + buf.getvalue())
    append_csv("census.csv", X.CENSUS_FIELDS, census_new_only(census_new, old_census))
    append_csv("master_loss_ratio.csv", M.ALL_COLS, new_rows, M.format_cell)
    append_csv("period_adoption.csv", M.ADOPT_COLS, adopt_new)
    append_csv("master_census.csv", M.MC_COLS, mc_new)
    append_csv("portfolio_taxonomy.csv", M.TAX_COLS, tax_new)
    raw = before["master_loss_ratio.json"].decode("utf-8")
    assert raw.endswith("\n]") or raw.endswith("]")
    add = json.dumps(new_rows, ensure_ascii=False, indent=2)           # "[\n  {..},\n  {..}\n]"
    inner = add[1:-1].strip("\n")                                     # rows only, 2-space indent as in the file
    new_master = raw[:-2] + ",\n" + inner + "\n]" if raw.endswith("\n]") else None
    assert new_master is not None
    M.atomic_write(LR / "master_loss_ratio.json", new_master)

    # ---- post-write proofs
    for fn in FILES:
        after = (LR / fn).read_bytes()
        pre = before[fn]
        log(f"{fn}: bytes {len(pre)} -> {len(after)}; existing bytes are a prefix: {after[:len(pre) - (1 if fn.endswith('.json') else 0)] == pre[:len(pre) - (1 if fn.endswith('.json') else 0)] if fn.endswith('.json') else after.startswith(pre)}")
    mj = json.loads((LR / "master_loss_ratio.json").read_text(encoding="utf-8"))
    log(f"master json reload: {len(mj)} rows (expected {len(old_master) + len(new_rows)}); equals old+new: {mj == old_master + new_rows}")
    (WORK / "run_load_log.txt").write_text("\n".join(LOGL), encoding="utf-8")


def census_new_only(census_new: list[dict], old_census: list[dict]) -> list[dict]:
    old_keys = {(r["원보험사코드"], r["공시분기"], r["표"], str(r["기준연도"])) for r in old_census}
    out = [r for r in census_new if (r["원보험사코드"], r["공시분기"], r["표"], str(r["기준연도"])) not in old_keys]
    return out


if __name__ == "__main__":
    main()
