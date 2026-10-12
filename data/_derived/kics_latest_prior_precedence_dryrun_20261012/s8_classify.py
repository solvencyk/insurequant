"""s8_classify.py -- step 8 (READ-ONLY).  Final classification of every registered exception (the ticket's FIRST deliverable) =
registry-declared type (s3) + the MEASURED cross-filing test (is the latest disclosure's printed column different from the master on the cells
the exception is about?).

declared type  A cross-filing conflict | B issuer self-inconsistency (one filing) | C source absent | D parser/tooling error or false positive | E other
measured       CONFLICT_INVOLVED   latest column (F(Q+2) 전전분기 열, else F(Q+1) 직전분기 열) differs from the master on an item the exception is about
               CONFLICT_OTHER      the block has a cross-filing difference, but not on the exception's own items
               CLEAN               latest column == master on all compared core items
               SUBITEM_*           exception is about sub-items (29..46): PDF prior-half presence/equality test (s7b)
               TFI_CURRENT_ONLY    exception is about TFI-table cells 47..54: a filing prints them for its own quarter only -> no later column exists
               UNCOVERED / NA_LATEST_FILING / OUT_OF_SCOPE
final type     A when the measurement shows a conflict on the exception's own cells (the registry text said B/C/E/D), else the declared type.
"""
import csv
import sys
from collections import Counter, defaultdict

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_precedence_dryrun_20261012")
from lib_dry import *  # noqa: F401,F403,E402

utf8_stdout()
inv = read_json(OUT / "exceptions_inventory_base.json")
blocks = {(b["code"], b["quarter"]): b for b in read_json(OUT / "conflict_blocks.json")}
verd = {(v["code"], v["quarter"]): v for v in read_json(OUT / "block_verdicts.json")}
sub = {(r["code"], r["quarter"]): r for r in read_json(OUT / "subitem_match_pdf.json")}
rows = read_rows()
midx, names = master_index(rows)

RULE_ITEMS = {
    "2_tier1_bridge": {2, 4, 12, 13}, "3_tier2_composition": {3, 13}, "47_tier2_census": {47, 48, 49}, "50_tfi_tier_split": {50, 51, 52},
    "51_tfi_tier2_composition": {51, 47, 48, 49}, "룰2": {4, 5, 6, 7, 8, 9, 10, 11}, "룰4": {15, 17, 18, 19, 20, 21}, "룰5": {14, 15, 22, 23},
    "룰6": {16, 15, 17, 18, 19, 20, 21}, "8_life": {17, 29, 30, 31, 32, 33, 34, 35}, "19_market": {19, 36, 37, 38, 39, 40},
    "36_irr": {36, 41, 42, 43, 44, 45, 46},
}
TFI = set(range(47, 55))
SUBI = set(range(29, 47))
CORE = set(range(1, 27))


def involved(row):
    s = {int(x) for x in str(row.get("items_involved", "")).split(";") if x.strip().isdigit()}
    for rule in str(row.get("rules", "")).split(";"):
        base = rule.replace("_post", "").strip()
        for k, v in RULE_ITEMS.items():
            if base.startswith(k):
                s |= v
    return s


def later_print_of_missing_bucket(code, q):
    """for census-absent buckets: does a LATER filing print the quarter's core block? (gap-fill candidate, not a conflict)"""
    out = []
    for qq, col, lab in ((qadd(q, 1), "prev", "F(Q+1) 직전분기"), (qadd(q, 2), "prev2", "F(Q+2) 전전분기")):
        if not qq:
            continue
        f = CACHE / f"core_{period_of(qq)}_{code}.json"
        if not f.exists():
            continue
        d = read_json(f)
        if d["status"] == "OK":
            n = sum(1 for v in d["cols"].get(col, {}).values() if v[0] is not None)
            out.append(f"{lab}: {n}칸 인쇄({d['pdf']} p{'+'.join(map(str, d['pages'] or []))})")
        else:
            out.append(f"{lab}: {d['status']}")
    return " | ".join(out)


# exceptions about the 적용후 column only: the later filing prints no 후 detail for a past quarter, so a 전(값) column comparison says nothing about them
POST_ONLY = {"_AFTER_SUBRISK_NOT_DISCLOSED", "kics_item23_children_post_absent.json"}
# hand adjudication (PDF page text read directly) overriding the automatic sub-item test; every entry names its evidence
MANUAL = {
    ("_LIFE8_ISSUER_INCONSISTENT", "KR1103", "2025.2Q"): (
        "CLEAN",
        "수기 판독: FY2025_Q4 KR1103 PDF p19 핵심표 당분기-2분기 열(2025년 6월) 14=341 · 15=431 · 16=41 · 17=392 · 18=13 · 19=41 · 21=26 · 22=89 와 p22 생명·장기손해보험위험액 "
        "직전 반기 열(47 / - / 214 / 5 / 115 / 130, 대재해 98)이 마스터(14=341.44 · 17=391.87 · 29~35=46.85/0.49/213.56/4.78/115.33/129.57/97.7)와 억원 정수 인쇄 정밀도에서 일치 - "
        "열 간 충돌 아님(발행사 표 내부 불일치 -12.73 은 그대로)"),
}

res = []
for r in inv:
    r = dict(r)
    code, q = r["code"], r["quarter"]
    inv_items = involved(r)
    r["involved_items_resolved"] = ";".join(str(i) for i in sorted(inv_items))
    r["measured"], r["measured_detail"], r["block_outcome"], r["block_category"] = "", "", "", ""
    man = MANUAL.get((r["registry"], code, q))
    if r["registry"] in POST_ONLY:
        r["measured"] = "POST_COLUMN_ONLY"
        r["measured_detail"] = "적용후 열 전용 예외 - 후속 공시는 지난 분기의 적용후 세부를 인쇄하지 않아 열 간 비교 불가(총괄표의 1후·14후·27후만 인쇄)"
    elif man:
        r["measured"], r["measured_detail"] = man
        v0 = verd.get((code, q))
        if v0:
            r["block_outcome"], r["block_category"] = v0["decision_table_outcome"], v0["ticket_category"]
    elif r["domain"] != "K-ICS":
        r["measured"] = "OUT_OF_SCOPE"
        r["measured_detail"] = "다른 마스터(" + r["domain"] + ") - 이 원칙의 K-ICS 헤드라인 열 비교 대상이 아님"
    elif not q.startswith("20"):
        r["measured"] = "N/A"
        r["measured_detail"] = "전 분기 적용 메타/허용오차 등재 - 특정 (회사,분기) 열 비교 대상 아님"
    elif q == "2026.2Q":
        r["measured"] = "NA_LATEST_FILING"
        r["measured_detail"] = "이 분기가 가장 최근 공시 - 후속 공시 없음 (2026.3Q 공시 뒤 재측정)"
    else:
        blk = blocks.get((code, q))
        if blk is None:
            r["measured"] = "NO_MASTER_BUCKET"
            r["measured_detail"] = "마스터에 이 (회사,분기) 버킷이 없음. 후속 공시의 전기 칸: " + later_print_of_missing_bucket(code, q)
        elif blk["status"] == "UNCOVERED":
            r["measured"] = "UNCOVERED"
            r["measured_detail"] = f"후속 공시 판독 불가 (own={blk['own_status']}, F+1={blk['q1_status']}, F+2={blk['q2_status']})"
        else:
            core_inv = inv_items & CORE
            diffs = {d["item"]: d for d in blk["diffs"]}
            hit = sorted(core_inv & set(diffs))
            sub_inv = inv_items & SUBI
            tfi_inv = inv_items & TFI
            parts = []
            if hit:
                r["measured"] = "CONFLICT_INVOLVED"
                parts.append("핵심표 최신 열이 현행과 다름: " + "; ".join(f"item{i} {diffs[i]['master']:g}->{diffs[i]['latest']:g}" for i in hit))
            elif blk["status"] == "CONFLICT":
                r["measured"] = "CONFLICT_OTHER"
                parts.append("블록에 열 간 차이가 있으나 이 예외의 항목 밖: " + "; ".join(f"item{d['item']}" for d in blk["diffs"]))
            else:
                r["measured"] = "CLEAN"
                parts.append(f"핵심표 최신 열({blk['latest_label']}) == 현행 (비교 {blk['compared']}칸)")
            if sub_inv:
                sm = sub.get((code, q))
                if sm is None:
                    parts.append("세부 위험액: 홀수분기라 직전 칸에 세부 표 없음(간이공시)" if not blk["even"] else "세부 위험액: 점검 기록 없음")
                else:
                    un = [u for u in sm["unmatched"] if u["item"] in sub_inv]
                    parts.append(f"세부 위험액 직전 반기 열 점검={sm['status']}" + (f" 미발견 {[u['item'] for u in un]}" if un else ""))
                    if un and r["measured"] in ("CLEAN", "CONFLICT_OTHER"):
                        r["measured"] = "SUBITEM_UNMATCHED"
                    elif not un and r["measured"] == "CLEAN" and sm["status"] in ("ALL_MATCH",):
                        r["measured"] = "CLEAN"
            if tfi_inv and not hit:
                parts.append("TFI 표(47~54)는 공시본마다 당분기 열만 인쇄 - 직전 칸 없음")
            r["measured_detail"] = " / ".join(parts)
            v = verd.get((code, q))
            if v:
                r["block_outcome"], r["block_category"] = v["decision_table_outcome"], v["ticket_category"]
    # final type
    declared = r["declared_type"]
    if r["measured"] == "CONFLICT_INVOLVED":
        r["final_type"], r["type_basis"] = "A", "측정(열 간 차이)"
    elif r["measured"] == "SUBITEM_UNMATCHED":
        r["final_type"], r["type_basis"] = declared + "?A", "세부 위험액 불일치 후보(재작성인지 판독 공백인지 미판정)"
    else:
        r["final_type"], r["type_basis"] = declared, "등재부 선언" + ("" if r["measured"] in ("CLEAN", "CONFLICT_OTHER") else f" ({r['measured']})")
    res.append(r)

# distinct registrations: the TFI-memo registry lists one row per item (53 / 54) of the same bucket
_seen = set()
for r in res:
    k = (r["registry"], r["code"], r["quarter"])
    r["distinct_registration"] = k not in _seen
    _seen.add(k)

cols = ["seq", "registry", "domain", "code", "company", "quarter", "distinct_registration", "rules", "items_involved", "pinned_residual",
        "n_raw_red_in_bucket", "raw_red_rules_in_bucket", "claim_kind", "declared_type", "measured", "final_type", "type_basis", "measured_detail",
        "block_outcome", "block_category", "reason", "approved_or_registered_by", "ledger_status", "citation"]
with open(OUT / "exceptions_classification.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for r in res:
        w.writerow(r)
write_json_lf(OUT / "exceptions_classification.json", res)

dist = [r for r in res if r["distinct_registration"]]
print("rows:", len(res), "| distinct (registry, company, quarter) registrations:", len(dist))
print("declared (rows)    :", dict(Counter(r["declared_type"] for r in res)))
print("declared (distinct):", dict(Counter(r["declared_type"] for r in dist)))
print("measured (distinct):", dict(Counter(r["measured"] for r in dist)))
print("final    (distinct):", dict(Counter(r["final_type"] for r in dist)))
print("final    (rows)    :", dict(Counter(r["final_type"] for r in res)))
print("--- final type A (measured cross-filing conflict on the exception's own cells):")
for r in res:
    if r["final_type"] == "A":
        print(f"  {r['registry']:30s} {r['code']} {r['quarter']} rules={r['rules'][:50]} | {r['measured_detail'][:120]} | {r['block_outcome']} / {r['block_category']}")
