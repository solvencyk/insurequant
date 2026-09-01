"""UPSERT 2026.2Q 생명장기 sub-risk cells (items 29-35) that the master never got.

DRY-RUN BY DEFAULT. Pass ``--apply`` to write. Written for the orchestrator to
apply serially alongside other agents' patches (concurrent whole-file
read-modify-write on kics_disclosure.json has silently dropped another
session's edits before).

WHY THESE CELLS EXIST
---------------------
Found while working inbox ``20260831T0700Z`` (docling window drops the market
section). The 2026.2Q master item census showed items 29-35 missing for 8
companies. Six of those are correctly empty or out of this lane's scope:

    KR0150 서울보증보험   item17(생명장기손해보험위험액)=0 -> children cannot exist
                          (보증보험, no life book). Correct as-is.
    KR0010 KB손해보험     raw PDF is an image-only scan (0 chars/page) -> OCR lane
    KR0087 동양생명       same, image-only scan -> OCR lane
    KR0029 AIG손해보험    only item35 missing; the MD's 대재해 table is the
                          general-insurance one, which fill_subitems
                          deliberately gates (_is_life_catastrophe_table).
                          Left alone - not this ticket.
    KR0051 신한이지손해    only item30 missing; the source row is a bare dash
                          ("| 위험액 | 장수위험 | - | - | |"), an extractor
                          zero-vs-missing question, not a page-selection one.

That leaves KR0009 현대해상, KR0094 신한라이프 and KR0099 케이비라이프, whose
values are present and unambiguous in the raw PDF and simply never reached the
master. KR0009's are also readable straight out of the markdown; KR0094's and
KR0099's are not, because those two filers print the row labels one character
per line ("사\\n망\\n위\\n험"), which Docling turns into a table whose label
column no longer matches any sub-risk name. That is a table-layout problem, not
a page-selection one - the pages were selected and converted - so the values
below are taken from the raw PDF text layer instead.

RAW-PDF VERIFICATION 1/3 (data/disclosure/FY2026_Q2/pdf/KR0009_현대해상.pdf)
---------------------------------------------------------------------------
p.22 "6-2-1) 개념 및 위험액 현황 / ② 생명·장기손해보험위험액 현황
      [생명·장기손해보험위험액-대재해위험 이외] (단위: 백만원, %)"
columns "Ⅰ. 생명보험 | Ⅱ. 장기손해보험 | Ⅲ. 총계", block "당기 (2026.2Q)"
(the "직전 반기 (2025.4Q)" block below it carries different numbers, so the
row block is unambiguous). 현대해상 leaves 생명보험 blank, so 장기 == 총계:

    사망위험          272,630 백만원 -> 2,726.30 억원   (item 29)
    장수위험            1,099 백만원 ->    10.99 억원   (item 30)
    장해·질병위험    4,877,916 백만원 -> 48,779.16 억원  (item 31)
    장기재물·기타위험  240,662 백만원 ->  2,406.62 억원  (item 32)
    해지위험        3,601,697 백만원 -> 36,016.97 억원  (item 33)
    사업비위험      1,456,363 백만원 -> 14,563.63 억원  (item 34)

p.23 "[생명·장기손해보험위험액-대재해위험] (단위: 백만원)", row "Ⅲ. 총계",
column "당기 (2026.2Q) 대재해위험액":

    대재해위험액      282,384 백만원 ->  2,823.84 억원  (item 35)

Reproduce:
    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe \
        scripts/_probes/probe_20260901_verify_cell_against_rawpdf.py KR0009 \
        2726.3 10.99 48779.16 2406.62 36016.97 14563.63 2823.84
    -> every value located on p.22 (29-34) / p.23 (35).

RAW-PDF VERIFICATION 2/3 (KR0094_신한라이프생명보험.pdf)
--------------------------------------------------------
p.25 "6-2. 생명•장기손해보험위험 관리 / ② 생명•장기손해보험위험액 현황
      [생명•장기손해보험위험액 - 대재해위험 이외] (단위 : 백만원)",
columns "I. 생명보험 | II. 장기손해보험 | III. 총계", block "당기 (26.2Q)"
(장기손해보험 is "-" throughout, so 생명보험 == 총계):

    사망위험          395,666 -> 3,956.66 억원   (item 29)
    장수위험           95,317 ->   953.17 억원   (item 30)
    장해•질병위험   1,771,412 -> 17,714.12 억원  (item 31)
    장기재물•기타위험        - ->        0       (item 32)
    해지위험        4,087,510 -> 40,875.10 억원  (item 33)
    사업비위험        860,969 ->  8,609.69 억원  (item 34)

p.26 "[생명•장기손해보험위험액 - 대재해위험]", "III. 총계" 당기 대재해위험액:

    대재해위험액      235,277 ->  2,352.77 억원  (item 35)

RAW-PDF VERIFICATION 3/3 (KR0099_케이비라이프생명보험.pdf)
----------------------------------------------------------
p.25 "② 생명·장기손해보험위험액 현황 [생명·장기손해보험위험액-대재해위험 이외]
      (단위: 백만원)", columns "1. 생명보험 | 2. 장기손해보험 | 3. 총계",
block "당기 (2026.2Q) / 위험액" (장기손해보험 "-", so 생명보험 == 총계):

    사망위험          336,659 -> 3,366.59 억원   (item 29)
    장수위험           43,987 ->   439.87 억원   (item 30)
    장해∙질병위험     386,077 -> 3,860.77 억원   (item 31)
    장기재물∙기타위험        - ->        0       (item 32)
    해지위험        2,356,799 -> 23,567.99 억원  (item 33)
    사업비위험        448,008 ->  4,480.08 억원  (item 34)

same page "[생명·장기손해보험위험액-대재해위험]", row "Ⅲ. 총계",
column "당기 (2026.2Q) 대재해위험액":

    대재해위험액      107,412 ->  1,074.12 억원  (item 35)

CROSS-CHECKS
------------
* item32 "-" is written as "0", the convention every other 생명보험 filer
  already follows in this quarter (18 of 19 life insurers carry item32 = 0;
  only 한화생명 has a non-zero 1384.37). A dash in a leaf sub-risk row means
  the filer discloses zero exposure to that risk, not "no data".
* 대재해 총계 is not the arithmetic sum of 전염병 + 대형사고: K-ICS combines
  them at correlation 0, i.e. sqrt(a^2 + b^2). Both filings reproduce:
      KR0094  sqrt(233,655^2 + 27,577^2) = 235,276.7  vs disclosed 235,277
      KR0099  sqrt(107,269^2 +  5,555^2) = 107,413.7  vs disclosed 107,412
  so the "총계" row really is the item35 value and not a mis-picked subtotal.
* Diversification sum(29..35) / item17, expected 1.2-1.6 for a diversified
  생명장기 book:
      KR0009  107,327.51 / 73,580 = 1.459
      KR0094   74,461.51 / 52,371 = 1.422
      KR0099   36,789.42 / 27,648 = 1.331
* Parent gate: item17 is non-zero for all three, so children are expected
  (the parent-zero/child-nonzero rule is not in play). Contrast KR0150
  서울보증, item17 = 0, which is why it is deliberately left empty above.
* 값_적용후 mirrors 값 for all three. Verified per filer, not assumed:
    KR0009 p.18 "4-2-2) 지급여력비율의 경과조치 적용에 관한 세부사항" - only
           공통적용 TFI(가용자본) and 보고기한 연장 are "O"; every 선택적용
           요구자본 measure (TAC/TIR/TER/TIRR/적기시정조치 유예) is "X".
           A 가용자본-only transition cannot move a 요구자본 sub-risk.
    KR0094 p.19 - every row including 공통적용 TFI is "X" (a full non-applier,
           same pattern as AIA). Recovered by word-bbox y-clustering because
           the table's read order is scrambled; see the run notes.
    KR0099 p.19 - TFI "O", 보고기한 연장 "O", all 선택적용 "X".
  This matches how the master already stores each company's parent item17
  (73580==73580 / 52371==52371 / 27648==27648) and item19.

WHAT THIS PATCH DELIBERATELY DOES NOT TOUCH
-------------------------------------------
Items 36-40. The 2026.2Q master already has all five for all 39 filers and they
reconcile (sqrt(V'·MARKET_M·V) ≈ item19). Re-extracting them from the markdown
would make things worse, not better:
``scripts/_probes/probe_20260901_md_vs_master_market_safety.py`` measured 128
agreements and **8 disagreements** where the markdown is the wrong one -
KR0009#37 is the clearest: the MD yields 2,317,766 but raw p.37 shows
당기(26.2Q) Ⅲ.합계 = 2,373,723 (= the master's 23,737.23억) and 2,317,766 is the
직전 반기 figure; Docling lost the "당기 / 직전 반기" block-label column and fused
the two period tables into one, so the extractor picks the last "Ⅲ. 합 계" row.
Do not re-run fill_market_subitems_to_disclosure.py over the re-converted MDs.

Idempotent: an existing non-empty value is never overwritten (use --force to
override, which this patch does not need).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TARGET = REPO / "kics_disclosure.json"
QUARTER = "2026.2Q"

ITEM_NAMES = {
    29: "1-1. 사망위험액",
    30: "1-2. 장수위험액",
    31: "1-3. 장해·질병위험액",
    32: "1-4. 장기재물·기타위험액",
    33: "1-5. 해지위험액",
    34: "1-6. 사업비위험액",
    35: "1-7. 대재해위험액",
}

# (company, item) -> 억원 value string, as it should appear in 값 and 값_적용후.
CELLS: dict[tuple[str, int], str] = {
    ("KR0009", 29): "2726.3",
    ("KR0009", 30): "10.99",
    ("KR0009", 31): "48779.16",
    ("KR0009", 32): "2406.62",
    ("KR0009", 33): "36016.97",
    ("KR0009", 34): "14563.63",
    ("KR0009", 35): "2823.84",
    ("KR0094", 29): "3956.66",
    ("KR0094", 30): "953.17",
    ("KR0094", 31): "17714.12",
    ("KR0094", 32): "0",
    ("KR0094", 33): "40875.1",
    ("KR0094", 34): "8609.69",
    ("KR0094", 35): "2352.77",
    ("KR0099", 29): "3366.59",
    ("KR0099", 30): "439.87",
    ("KR0099", 31): "3860.77",
    ("KR0099", 32): "0",
    ("KR0099", 33): "23567.99",
    ("KR0099", 34): "4480.08",
    ("KR0099", 35): "1074.12",
}


def _company_identity(rows: list[dict], code: str, fields: dict[str, str]) -> dict[str, str]:
    """Copy 원수사명 / 티커 / 생손보여부 from an existing row of the same company."""

    for row in rows:
        if row.get(fields["code"]) == code:
            return {
                fields["cname"]: row.get(fields["cname"]),
                fields["ticker"]: row.get(fields["ticker"]),
                fields["kind"]: row.get(fields["kind"]),
            }
    raise SystemExit(f"no existing row for {code}; refusing to invent company identity")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="write kics_disclosure.json (default: dry run)")
    ap.add_argument("--force", action="store_true", help="overwrite an existing non-empty value")
    args = ap.parse_args()

    data = json.loads(TARGET.read_text(encoding="utf-8"))
    keys = list(data[0].keys())
    F = {
        "code": keys[0],
        "cname": keys[1],
        "ticker": keys[2],
        "kind": keys[3],
        "item": keys[4],
        "name": keys[5],
        "quarter": keys[6],
        "val": keys[7],
        "after": keys[8],
    }

    index: dict[tuple[str, int], dict] = {}
    for row in data:
        if row.get(F["quarter"]) != QUARTER:
            continue
        try:
            index[(row.get(F["code"]), int(row.get(F["item"])))] = row
        except (TypeError, ValueError):
            continue

    before_rows = len(data)
    updated: list[str] = []
    inserted: list[str] = []
    skipped: list[str] = []

    for (code, item), value in sorted(CELLS.items()):
        row = index.get((code, item))
        if row is None:
            identity = _company_identity(data, code, F)
            data.append(
                {
                    F["code"]: code,
                    F["cname"]: identity[F["cname"]],
                    F["ticker"]: identity[F["ticker"]],
                    F["kind"]: identity[F["kind"]],
                    F["item"]: item,
                    F["name"]: ITEM_NAMES[item],
                    F["quarter"]: QUARTER,
                    F["val"]: value,
                    F["after"]: value,
                }
            )
            inserted.append(f"{code}#{item}={value}")
            continue
        current = row.get(F["val"])
        if current not in (None, "", "None") and not args.force:
            skipped.append(f"{code}#{item} already={current!r}")
            continue
        row[F["val"]] = value
        row[F["after"]] = value
        updated.append(f"{code}#{item}={value}")

    print(f"rows before={before_rows} after={len(data)}")
    print(f"inserted {len(inserted)}: {inserted}")
    print(f"updated  {len(updated)}: {updated}")
    print(f"skipped  {len(skipped)}: {skipped}")

    if not args.apply:
        print("\nDRY RUN - nothing written. Re-run with --apply to commit.")
        return 0

    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {TARGET}")
    print("NEXT: scripts/validate_kics_disclosure.py must stay exit 0, then sync the master xlsx")
    print("      sheet with scripts/sync_master_xlsx_sheet.py (never build_master_xlsx.py).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
