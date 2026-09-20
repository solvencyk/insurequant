#!/usr/bin/env python3
"""경영공시 PL 백필 ⑤ 병합 (2026-09-20, parser/ifrs17).

승인 티켓: inbox/parser/20260920T1500Z__validation__ALL_2023.1Q-2026.2Q__disclosure_pl_merge_authorized.md
원 발주  : inbox/parser/20260918T0205Z__orchestrator__ALL_2023.1Q-2026.2Q__disclosure_pl_backfill.md

무엇을 하나
-----------
A) 스테이징 `data/_derived/pl_backfill_disclosure_20260918.json` 의 **merge_candidate 775칸**
   (15사 x 5항목 [1,16,22,23,24])을 루트 `PL_breakdown.json` 에 **새 행으로만** 추가한다.
   - 기존 셀은 한 칸도 안 덮는다(스테이징 155 (회사,분기) 는 마스터에 아예 없는 칸이다).
   - 항목번호 23 의 항목명은 스테이징이 `법인세비용` 이지만 마스터 정본은 `법인세` 다.
     `load_long()` 이 **항목명으로 색인**하므로 마스터 이름으로 정규화해 넣는다(티켓 §5-1).
   - `값_당분기` 는 **같은 소스(경영공시) 안에서만** 차분한다. 직전 분기가 경영공시 백필분이
     아니면(=DART 4Q 이거나 없음) None 으로 둔다 — 4Q 당분기 = DART 연간 - 경영공시 3Q 누계는
     소스 혼합이라 발주 §6 에서 범위 밖으로 못 박혔다.

B) 티켓 §5-2 의 진짜 결손 3건(경영공시 탓이 아닌 **DART 추출 갭**)을 raw 에서 재추출해 채운다.
   기존 행의 `값` 이 **None 인 칸만** 채우고, 값이 있는 칸은 절대 안 건드린다.

C) 사이드카 `PL_breakdown_provenance.json` 에 155 DISCLOSURE 셀을 append 하고, B 로 발행 항목이
   늘어난 5개 블록의 `source_files` / `published_items` 를 갱신한다.
   - `as_of_date` 는 **싣지 않는다**. 스테이징에는 분기말일이 들어 있으나 validation §1(c) 가
     "분기말일을 기계적으로 넣지 마라 — 항등식일 뿐 검증력이 0" 으로 별도 티켓으로 분리했다.

안 하는 것
----------
- `scripts/build_root_masters.py` 를 부르지 않는다(main() 통짜 실행 금지 이력).
- `data/dart/viz/pl_breakdown_master.json`(빌더 산출, PL 골든이 고정) 을 **안 건드린다**.
  루트가 누적 정본이고 viz 는 재생성 가능한 부분입력이다(validate_master_tables.py L40~ 주석).
  `build_pl()` 의 `_additive_merge` 가 다음 리빌드에서 이 행들을 보존한다.
- 사이드카를 재발행(emit_pl_provenance.py)하지 않는다 — 그 이미터는 DART 전용이라 경영공시 셀을
  `unresolved` 로 되돌린다. append/patch 만 한다.

실행
----
    $py scripts/merge_pl_backfill_disclosure_20260920.py            # dry-run (기본)
    $py scripts/merge_pl_backfill_disclosure_20260920.py --apply    # 실제 기록
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)

MASTER = ROOT / "PL_breakdown.json"
SIDECAR = ROOT / "PL_breakdown_provenance.json"
STAGING = ROOT / "data" / "_derived" / "pl_backfill_disclosure_20260918.json"

EXPECT_ROWS_BEFORE = 12122
EXPECT_CQ_BEFORE = 374
EXPECT_MERGE_VALUES = 775
EXPECT_PROV_ENTRIES = 155
BACKFILL_ITEMS = (1, 16, 22, 23, 24)

# 마스터 정본 항목명 (스테이징의 `법인세비용` 을 여기로 정규화 — 티켓 §5-1)
MASTER_ITEM_NAME = {1: "보험손익", 16: "기타사업비용", 22: "세전이익",
                    23: "법인세", 24: "당기순이익"}

# 사이드카 블록 분할 — validate_data_contract._PL_CONTRACT_NOTE_ITEMS 와 같아야 한다.
CONTRACT_NOTE_ITEMS = frozenset({4, 5, 6, 9, 10, 11, 13, 14})


def block_of(item_no: int) -> str:
    return "contract_notes" if item_no in CONTRACT_NOTE_ITEMS else "income_statement"


# --------------------------------------------------------------------------- #
# B) 티켓 §5-2 — DART 4Q 의 진짜 결손. 전부 raw 실측이며 근거는 아래 note 에 적는다.
#    단위: raw 는 천원, 마스터는 백만원(= 천원 / 1000).
# --------------------------------------------------------------------------- #
_KR0051_SRC = "data/dart/FY2024_Q4/raw/KR0051_신한이지손해보험_20250328002305"
_KR0029_SRC24 = "data/dart/FY2024_Q4/raw/KR0029_에이아이지손해보험_20250409001949"
_KR0029_SRC25 = "data/dart/FY2025_Q4/raw/KR0029_에이아이지손해보험_20260407002104"

LOB_FIX = {
    # 신한이지손해보험 2024.4Q — 주석 '22. 보험영업손익 (1) 1) 당기'(FY2024 filing, table#123).
    # 이 회사 주석은 LOB(장기/자동차/일반)가 아니라 **전환방법(수정소급법/공정가치법/기타)** 으로
    # 쪼개져 있다. owner 가 2025.4Q 를 xlsx 로 채울 때 쓴 규약 = 일반모형(GMM) -> 생명장기(2/3/8),
    # 보험료배분접근법(PAA) -> 일반손익(14). 그 규약을 2025.4Q 12칸 전부에 역산해 **천원 단위까지
    # 정확히 재현**한 뒤 같은 규약을 2024.4Q 에 적용했다. FY2025 filing table#167 의 '2) 제22(전)기'
    # 가 같은 숫자를 독립 확인한다.
    #   item3 = 보험수익 일반모형소계(1,151,056) - 보험서비스비용 일반모형소계(3,241,154)
    #   item8 = 재보험수익 일반모형소계(177,938) - 재보험비용 일반모형소계(-490,658)
    #   item14 = (보험수익 PAA 64,385,914 - 보험서비스비용 PAA 78,829,867)
    #          + (재보험수익 PAA 20,437,342 - 재보험비용 PAA 18,051,698)
    #   item6 = 예상보험금및기타(879,449) - [발생보험금및기타(1,305,551) + 발생사고이행현금흐름변동(375,569)]
    #   item11 = 발생재보험금(66,545) - 예상재보험금(68,567)
    #   item7 = item3 - (4+5+6),  item12 = item8 - (9+10+11),  item2 = 3 + 8
    #   검산: item2 + item14 = -13,479.811 vs 주석 '보험손익 합계' -13,479.812 (차 0.001)
    #         item2+item14+item15(0)-item16(1,654.120238) = -15,133.931238
    #         vs 마스터 item1 -15,133.931784 -> 잔차 0.000546 백만원
    ("KR0051", "2024.4Q"): {
        "source_file": _KR0051_SRC,
        "how": "raw_filing",
        "values": {2: -1421.502, 3: -2090.098, 4: 30.411, 5: 32.925, 6: -801.671,
                   7: -1351.763, 8: 668.596, 9: -30.597, 10: -3.806, 11: -2.022,
                   12: 705.021, 14: -12058.309},
    },
    # AIG손해보험 2024.4Q / 2025.4Q — 주석 6-1(보험수익) 6-2(보험비용) 6-3(재보험수익)
    # 6-4(재보험비용). 이 회사 주석은 **[장 기 | 일 반 | 합 계]** 컬럼으로 실제 LOB 분해가 있다
    # (= `LOB_LEG_NA` 등재 대상이 아니다). 자동차 컬럼은 filing 어디에도 없다 -> item13 은 공백.
    #   item3 = 6-1 장기합계 - 6-2 장기합계,  item8 = 6-3 장기합계 - 6-4 장기합계,  item2 = 3 + 8
    #   item14 = (6-1 일반 - 6-2 일반) + (6-3 일반 - 6-4 일반)
    # 5/6/7/10/11/12 는 이 표 형태에서 예실차 행 짝이 일의적이지 않아 **비워 둔다**(추측 금지).
    # 두 filing 교차확인: FY2025 <전기> == FY2024 <당기> 가 8개 합계 전부 일치.
    #   2024.4Q 검산: 14,582.532 + 58,505.173 - 18,836.138297 = 54,251.566703
    #                 vs 마스터 item1 54,251.566556 -> 잔차 0.000147 백만원
    #   2025.4Q 검산: 19,063.598 + 53,684.733 - 32,987.424721 = 39,760.906279
    #                 vs 마스터 item1 39,760.90519 -> 잔차 0.001089 백만원
    ("KR0029", "2024.4Q"): {
        "source_file": _KR0029_SRC24,
        "how": "raw_filing",
        "values": {2: 14582.532, 3: 18929.855, 8: -4347.323, 14: 58505.173},
    },
    ("KR0029", "2025.4Q"): {
        "source_file": _KR0029_SRC25,
        "how": "raw_filing",
        "values": {2: 19063.598, 3: 25975.584, 8: -6911.986, 14: 53684.733},
    },
}

ITEM_NAME_ALL = {
    2: "생명장기 손익", 3: "생명장기 원수손익", 4: "원수 CSM상각", 5: "원수 위험조정 변동",
    6: "원수 예실차", 7: "기타 생명장기 원수손익", 8: "생명장기 재보험손익", 9: "재보험 CSM상각",
    10: "재보험 위험조정 변동", 11: "재보험 예실차", 12: "기타 생명장기 재보험손익",
    13: "자동차손익", 14: "일반손익",
}


def _qkey(q):
    return (int(q[:4]), int(q[5]))


def _prev_q(q):
    y, n = _qkey(q)
    return None if n == 1 else f"{y}.{n - 1}Q"


def fail(msg):
    print("ABORT:", msg)
    sys.exit(2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="실제로 파일을 쓴다(기본은 dry-run)")
    args = ap.parse_args()

    # ---------------- load ------------------------------------------------- #
    st = json.loads(STAGING.read_text(encoding="utf-8"))
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    side = json.loads(SIDECAR.read_text(encoding="utf-8"))
    before_stat = MASTER.stat()

    # ---------------- preflight guards ------------------------------------- #
    if len(rows) != EXPECT_ROWS_BEFORE:
        fail(f"마스터 행수 {len(rows)} != 기대 {EXPECT_ROWS_BEFORE}")
    cq_before = {(r["원보험사코드"], r["공시분기"]) for r in rows}
    if len(cq_before) != EXPECT_CQ_BEFORE:
        fail(f"마스터 (회사,분기) {len(cq_before)} != 기대 {EXPECT_CQ_BEFORE}")
    if list(st.get("backfill_item_numbers") or []) != list(BACKFILL_ITEMS):
        fail(f"스테이징 backfill_item_numbers={st.get('backfill_item_numbers')} != {BACKFILL_ITEMS}")

    by_key = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in rows}
    if len(by_key) != len(rows):
        fail("마스터에 (코드,항목,분기) 중복 행이 있다")
    meta = {}
    for r in rows:
        meta.setdefault(r["원보험사코드"],
                        {k: r[k] for k in ("원수사명", "티커", "생손보여부")})

    # 병합 후보 수집 ------------------------------------------------------- #
    cand = []          # (code, quarter, {item: 값})
    for cell in st["cells"]:
        if cell.get("backfill_excluded"):
            continue
        got = {}
        for k, it in (cell.get("items") or {}).items():
            if it.get("merge_candidate") and it.get("값") is not None:
                got[int(k)] = float(it["값"])
        if got:
            if sorted(got) != list(BACKFILL_ITEMS):
                fail(f"{cell['원보험사코드']} {cell['공시분기']} 병합항목 {sorted(got)} != {list(BACKFILL_ITEMS)}")
            cand.append((cell["원보험사코드"], cell["공시분기"], got, cell.get("source_file")))
    n_vals = sum(len(g) for _, _, g, _ in cand)
    if n_vals != EXPECT_MERGE_VALUES:
        fail(f"병합후보 값 {n_vals} != 기대 {EXPECT_MERGE_VALUES}")

    # 덮어쓰기 0 검증 ------------------------------------------------------- #
    clash = [(c, q, i) for c, q, g, _ in cand for i in g if (c, i, q) in by_key]
    if clash:
        fail(f"기존 셀과 충돌 {len(clash)}건 — 빈 칸만 채워야 한다: {clash[:5]}")
    unknown = sorted({c for c, _, _, _ in cand if c not in meta})
    if unknown:
        fail(f"마스터에 없는 회사코드 {unknown} — 회사 메타(원수사명/티커/생손보)를 못 만든다")

    # 값_당분기: 같은 소스(경영공시) 안에서만 차분 --------------------------- #
    ytd = defaultdict(dict)
    for c, q, g, _ in cand:
        for i, v in g.items():
            ytd[(c, i)][q] = v
    disclosure_q = {(c, q) for c, q, _, _ in cand}

    new_rows = []
    dangi_stat = {"q1": 0, "diff": 0, "none_prev_not_disclosure": 0}
    for c, q, g, _ in sorted(cand, key=lambda x: (x[0], _qkey(x[1]))):
        for i in BACKFILL_ITEMS:
            v = g[i]
            p = _prev_q(q)
            if p is None:
                dangi = v
                dangi_stat["q1"] += 1
            elif (c, p) in disclosure_q and ytd[(c, i)].get(p) is not None:
                dangi = round(v - ytd[(c, i)][p], 6)
                dangi_stat["diff"] += 1
            else:
                dangi = None            # 직전 분기가 DART 이거나 없음 -> 소스 혼합 금지
                dangi_stat["none_prev_not_disclosure"] += 1
            new_rows.append({
                "원보험사코드": c, "원수사명": meta[c]["원수사명"], "티커": meta[c]["티커"],
                "생손보여부": meta[c]["생손보여부"], "항목번호": i,
                "항목명": MASTER_ITEM_NAME[i], "공시분기": q,
                "값": v, "값_당분기": dangi,
            })

    # ---------------- B) 5-2 결손 채움 ------------------------------------- #
    lob_filled, lob_missing_row, lob_would_overwrite = [], [], []
    for (c, q), spec in LOB_FIX.items():
        if not (ROOT / spec["source_file"]).exists():
            fail(f"5-2 source_file 부재: {spec['source_file']}")
        for i, v in spec["values"].items():
            r = by_key.get((c, i, q))
            if r is None:
                lob_missing_row.append((c, q, i))
                continue
            if r.get("값") is not None:
                lob_would_overwrite.append((c, q, i, r["값"]))
                continue
            if r.get("항목명") != ITEM_NAME_ALL[i]:
                fail(f"{c} {q} item{i} 항목명 {r.get('항목명')!r} != {ITEM_NAME_ALL[i]!r}")
            lob_filled.append((c, q, i, v, r))
    if lob_missing_row:
        fail(f"5-2 대상 행이 마스터에 없다: {lob_missing_row}")
    if lob_would_overwrite:
        fail(f"5-2 가 기존 값을 덮으려 한다(금지): {lob_would_overwrite}")

    # ---------------- 사이드카 -------------------------------------------- #
    pe = st["provenance_entries"]
    if len(pe) != EXPECT_PROV_ENTRIES:
        fail(f"provenance_entries {len(pe)} != {EXPECT_PROV_ENTRIES}")
    side_idx = {(x["company_code"], x["quarter"], x["item_block"]): x for x in side["cells"]}
    new_side = []
    for e in pe:
        key = (e["company_code"], e["quarter"], e["item_block"])
        if key in side_idx:
            fail(f"사이드카에 이미 있는 셀을 또 만들려 한다(티켓 §6.4 위반): {key}")
        if e["source_id"] != "DISCLOSURE":
            fail(f"source_id={e['source_id']} — DISCLOSURE 여야 한다: {key}")
        if not e["source_file"].startswith("data/disclosure/"):
            fail(f"source_file 계보 불일치: {e['source_file']}")
        if not (ROOT / e["source_file"]).exists():
            fail(f"source_file 디스크 부재: {e['source_file']}")
        new_side.append({
            "company_code": e["company_code"], "quarter": e["quarter"],
            "item_block": e["item_block"], "source_id": "DISCLOSURE",
            "source_file": e["source_file"],
            "source_files": [{"file": e["source_file"], "how": "disclosure_summary_pl",
                              "items": list(BACKFILL_ITEMS)}],
            "resolution": "disclosure_summary_pl",
            "published_items": len(BACKFILL_ITEMS), "schema_items": 24,
        })
        # as_of_date 는 의도적으로 뺀다 (validation §1(c): 분기말일 기계 삽입 금지)
    if {(e["company_code"], e["quarter"]) for e in pe} != {(c, q) for c, q, _, _ in cand}:
        fail("provenance_entries 키 집합 != 병합 셀 키 집합")

    # 5-2 로 발행 항목이 늘어난 블록 패치
    side_patch = []
    for (c, q), spec in LOB_FIX.items():
        per_block = defaultdict(list)
        for i in spec["values"]:
            per_block[block_of(i)].append(i)
        for blk, items in per_block.items():
            cell = side_idx.get((c, q, blk))
            if cell is None:
                fail(f"사이드카에 {c} {q} {blk} 셀이 없다")
            side_patch.append((cell, sorted(items), spec["source_file"], spec["how"]))

    # ---------------- 무결성: 기존 행은 값 채움 20칸 외에 한 글자도 안 바뀐다 -- #
    snapshot = {k: json.dumps(v, ensure_ascii=False, sort_keys=True) for k, v in by_key.items()}
    authorized = {(c, i, q) for (c, q), spec in LOB_FIX.items() for i in spec["values"]}

    # ---------------- apply ------------------------------------------------ #
    print("=" * 78)
    print(f"A) 병합 신규 행      : {len(new_rows)}  (기대 {EXPECT_MERGE_VALUES})")
    print(f"   (회사,분기) 셀     : {len(cand)}  합계 {sum(sum(g.values()) for _, _, g, _ in cand):,.0f} 백만원")
    print(f"   값_당분기          : Q1직접 {dangi_stat['q1']} · 동일소스차분 {dangi_stat['diff']} "
          f"· None(직전분기 비-경영공시) {dangi_stat['none_prev_not_disclosure']}")
    print(f"   덮어쓴 기존 셀      : 0 (충돌 검사 통과)")
    print(f"B) 5-2 채운 기존 칸  : {len(lob_filled)}  "
          f"({', '.join(f'{c} {q} item{i}' for c, q, i, _, _ in lob_filled[:3])} ...)")
    print(f"C) 사이드카 append   : {len(new_side)} 셀 · 패치 {len(side_patch)} 블록")
    print("=" * 78)
    if not args.apply:
        print("dry-run — 아무것도 쓰지 않았다. --apply 로 실행하라.")
        return

    # 쓰기 직전 파일이 그 사이 안 바뀌었는지 재확인
    now = MASTER.stat()
    if (now.st_mtime_ns, now.st_size) != (before_stat.st_mtime_ns, before_stat.st_size):
        fail("읽은 뒤 PL_breakdown.json 이 바뀌었다 — 동시 세션 의심. 중단")

    for c, q, i, v, r in lob_filled:
        r["값"] = v                       # 값_당분기 는 None 유지(4Q 는 소스 혼합이라 산출 불가)
    changed = [k for k, s in snapshot.items()
               if json.dumps(by_key[k], ensure_ascii=False, sort_keys=True) != s]
    if set(changed) - authorized:
        fail(f"허가 밖 기존 행이 바뀌었다: {sorted(set(changed) - authorized)[:10]}")
    if set(changed) != authorized:
        fail(f"허가된 칸 중 안 바뀐 게 있다: {sorted(authorized - set(changed))}")

    out = rows + new_rows
    if len(out) != EXPECT_ROWS_BEFORE + EXPECT_MERGE_VALUES:
        fail(f"결과 행수 {len(out)} != {EXPECT_ROWS_BEFORE + EXPECT_MERGE_VALUES}")
    if len({(r["원보험사코드"], r["항목번호"], r["공시분기"]) for r in out}) != len(out):
        fail("결과에 키 중복이 생겼다")

    for cell, items, sf, how in side_patch:
        bucket = None
        for b in cell.setdefault("source_files", []):
            if b.get("file") == sf and b.get("how") == how:
                bucket = b
                break
        if bucket is None:
            cell["source_files"].append({"file": sf, "how": how, "items": items})
        else:
            bucket["items"] = sorted(set(bucket["items"]) | set(items))
        cell["published_items"] = cell.get("published_items", 0) + len(items)
        # source_file/source_id/resolution = 가장 많은 항목을 설명하는 버킷 (emit_pl_provenance 규약)
        cell["source_files"].sort(key=lambda b: (-len(b["items"]),
                                                 0 if str(b["file"]).startswith("data/dart/") else 1,
                                                 str(b["file"])))
        top = cell["source_files"][0]
        cell["source_file"] = top["file"]
        cell["resolution"] = top["how"]
        cell["source_id"] = "DART" if str(top["file"]).startswith("data/dart/") else "OWNER_GOLD"
        cell.pop("unresolved_reason", None)

    side["cells"] = list(side["cells"]) + new_side
    side["merge_note_20260920"] = (
        "경영공시 §2-1 백필 155셀(DISCLOSURE) append + DART 4Q LOB 재추출 5블록 패치. "
        "as_of_date 는 싣지 않았다 — 분기말일 기계 삽입 금지(validation 20260920T1500Z §1c), "
        "downloader 가 필링 meta 에서 채울 별도 티켓이다. "
        "재현: scripts/merge_pl_backfill_disclosure_20260920.py --apply")

    MASTER.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    SIDECAR.write_text(json.dumps(side, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {MASTER}  ({len(out)} rows, +{len(new_rows)})")
    print(f"wrote {SIDECAR} ({len(side['cells'])} cells, +{len(new_side)})")


if __name__ == "__main__":
    main()
