"""Recalculate derived K-ICS JSON fields from sibling items."""
from __future__ import annotations

import argparse
import io
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
JSON_PATH = REPO / "kics_disclosure.json"
TEMPLATES_JSON = REPO / "templates" / "kics_disclosure.json"

KEY_CODE = "\uc6d0\ubcf4\ud5d8\uc0ac\ucf54\ub4dc"
KEY_NAME = "\uc6d0\uc218\uc0ac\uba85"
KEY_TICKER = "\ud2f0\ucee4"
KEY_KIND = "\uc0dd\uc190\ubcf4\uc5ec\ubd80"
KEY_ITEM = "\ud56d\ubaa9\ubc88\ud638"
KEY_INAME = "\ud56d\ubaa9\uba85"
KEY_Q = "\uacf5\uc2dc\ubd84\uae30"
KEY_VAL = "\uac12"
KEY_POST = "\uac12_\uc801\uc6a9\ud6c4"

# item27/28 are ratios (%). Parsed PDFs sometimes store absolute eok-won by mistake.
RATIO_ABS_MAX = 1000.0


def _is_plausible_ratio(v: float | None) -> bool:
    if v is None:
        return False
    return 0.0 <= v <= RATIO_ABS_MAX


def _template_row(items: dict[int, dict]) -> dict:
    for n in (2, 14, 1, 27):
        if n in items:
            return items[n]
    return next(iter(items.values()))


def _ensure_item_row(
    rows: list[dict],
    items: dict[int, dict],
    *,
    code: str,
    quarter: str,
    item_no: int,
    item_name: str,
) -> dict:
    row = items.get(item_no)
    if row is not None:
        return row
    template = _template_row(items)
    row = {
        KEY_CODE: code,
        KEY_NAME: template[KEY_NAME],
        KEY_TICKER: template[KEY_TICKER],
        KEY_KIND: template[KEY_KIND],
        KEY_ITEM: item_no,
        KEY_INAME: item_name,
        KEY_Q: quarter,
        KEY_VAL: None,
    }
    rows.append(row)
    items[item_no] = row
    return row


def _to_float(raw) -> float | None:
    if raw is None:
        return None
    s = str(raw).strip().replace(",", "")
    if s in ("", "-"):
        return None
    s = s.replace("\u25b3", "-").replace("\u25b2", "-")
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    try:
        return float(s)
    except ValueError:
        return None


def _fmt_ratio(x: float) -> str:
    s = f"{x:.8f}".rstrip("0").rstrip(".")
    return s or "0"


def _fmt_amount(x: float) -> str:
    if abs(x - round(x)) < 1e-6:
        return str(int(round(x)))
    return f"{x:.2f}".rstrip("0").rstrip(".")


def recalc(rows: list[dict]) -> dict[str, int]:
    buckets: dict[tuple[str, str], dict[int, dict]] = defaultdict(dict)
    for row in rows:
        buckets[(row[KEY_CODE], row[KEY_Q])][row[KEY_ITEM]] = row

    stats = {
        "item3_added": 0,
        "item3_updated": 0,
        "item4_reconciled": 0,
        "item8_zeroed": 0,
        "item10_zeroed": 0,
        "item18_added": 0,
        "item18_zeroed": 0,
        "item22_zeroed": 0,
        "item22_added": 0,
        "item27_updated": 0,
        "item27_added": 0,
        "item28_updated": 0,
        "item28_added": 0,
        "item28_post_updated": 0,
    }

    for (code, quarter), items in buckets.items():
        i1 = _to_float(items.get(1, {}).get(KEY_VAL))
        i2 = _to_float(items.get(2, {}).get(KEY_VAL))
        i4 = _to_float(items.get(4, {}).get(KEY_VAL))
        i14 = _to_float(items.get(14, {}).get(KEY_VAL))
        i15 = _to_float(items.get(15, {}).get(KEY_VAL))
        post2 = _to_float(items.get(2, {}).get(KEY_POST))
        post14 = _to_float(items.get(14, {}).get(KEY_POST))

        if i4 is not None:
            comp = {
                n: _to_float(items.get(n, {}).get(KEY_VAL)) or 0.0
                for n in range(5, 12)
            }
            s_all = sum(comp.values())
            s_no10 = sum(v for n, v in comp.items() if n != 10)
            s_no8 = sum(v for n, v in comp.items() if n != 8)
            row10 = items.get(10)
            if row10 is not None and abs(s_no10 - i4) <= 2 and abs(s_all - i4) > 2:
                if row10.get(KEY_VAL) != "0":
                    row10[KEY_VAL] = "0"
                    stats["item10_zeroed"] += 1
            row8 = items.get(8)
            if row8 is not None and abs(s_no8 - i4) <= 2 and abs(s_all - i4) > 2:
                if row8.get(KEY_VAL) != "0":
                    row8[KEY_VAL] = "0"
                    stats["item8_zeroed"] += 1
            # NOTE: this used to also overwrite item4 itself with s_all (sum of
            # items 5-11) whenever they disagreed by >5%. Removed 2026-08-21
            # (inbox 20260821T1505Z / 20260821T1420Z) -- item4 is a disclosed
            # value; forcing it to equal the children sum makes rule 2
            # (item4 == sum(5..11)) structurally incapable of ever failing on
            # real data. 122 cells had already been silently overwritten this
            # way (see scripts/fix_20260821_item4_writepath_restore.py for the
            # raw-sourced restoration). item4 must come from extraction only.

        row22 = items.get(22)
        row23 = items.get(23)
        i23 = _to_float(row23.get(KEY_VAL)) if row23 is not None else None
        if i23 is None:
            i23 = 0.0
        if (
            row22 is None
            and i14 is not None
            and i15 is not None
            and abs(i14 - i15) < 0.01
            and i23 == 0.0
        ):
            row22 = _ensure_item_row(
                rows,
                items,
                code=code,
                quarter=quarter,
                item_no=22,
                item_name="\u2161. \ubc95\uc778\uc138\uc870\uc815\uc561",
            )
            row22[KEY_VAL] = "0"
            stats["item22_added"] += 1
        elif (
            row22 is not None
            and i14 is not None
            and i15 is not None
            and abs(i14 - i15) < 0.01
            and i23 == 0.0
        ):
            if row22.get(KEY_VAL) not in ("0", 0):
                row22[KEY_VAL] = "0"
                stats["item22_zeroed"] += 1

        if i1 is not None and i2 is not None:
            row3 = items.get(3)
            if row3 is None:
                # item3 (\ubcf4\uc644\uc790\ubcf8) genuinely missing -- backfill from the
                # disclosed identity item1 = item2 + item3. This branch only
                # ever CREATES a row; it never touches one that already
                # holds a disclosed value (see removed 'else' branch below).
                i3_val = i1 - i2
                template = items.get(2) or items.get(1) or next(iter(items.values()))
                new_row = {
                    KEY_CODE: code,
                    KEY_NAME: template[KEY_NAME],
                    KEY_TICKER: template[KEY_TICKER],
                    KEY_KIND: template[KEY_KIND],
                    KEY_ITEM: 3,
                    KEY_INAME: "\ubcf4\uc644\uc790\ubcf8",
                    KEY_Q: quarter,
                    KEY_VAL: _fmt_amount(i3_val),
                }
                rows.append(new_row)
                items[3] = new_row
                stats["item3_added"] += 1
            # NOTE: this used to also unconditionally overwrite an EXISTING
            # item3 with item1-item2 whenever they differed (no tolerance
            # gate at all). Removed 2026-08-21 (inbox 20260821T1505Z,
            # surfaced via validation's IDENTITY_TAUTOLOGY meta-rule --
            # R1_\uac00\uc6a9\uc790\ubcf8=\uae30\ubcf8+\ubcf4\uc644 \uc801\uc6a9\uc804 n=477, 97.7% exact-zero vs 75.0%
            # null). item3 is a disclosed value (\uac00.\uc9c0\uae09\uc5ec\ub825\uae08\uc561 = \uae30\ubcf8\uc790\ubcf8 +
            # \ubcf4\uc644\uc790\ubcf8 in the source table); forcing it to always equal
            # item1-item2 makes rule 1 structurally incapable of failing on
            # real data. 80 cells had already been silently overwritten this
            # way (see scripts/fix_20260821_item3_writepath_restore.py for
            # the raw-sourced restoration).

        if i1 is not None and i14 and i14 != 0:
            expected27 = i1 / i14 * 100.0
            if 27 not in items:
                row27 = _ensure_item_row(
                    rows,
                    items,
                    code=code,
                    quarter=quarter,
                    item_no=27,
                    item_name="\uc9c0\uae09\uc5ec\ub825\ube44\uc728",
                )
                row27[KEY_VAL] = _fmt_ratio(expected27)
                stats["item27_added"] += 1
            elif 27 in items:
                row27 = items[27]
                new_v = _fmt_ratio(expected27)
                cur27 = _to_float(row27.get(KEY_VAL))
                if (
                    not _is_plausible_ratio(cur27)
                    or cur27 is None
                    or abs(cur27 - expected27) > 0.5
                    or row27.get(KEY_VAL) != new_v
                ):
                    row27[KEY_VAL] = new_v
                    stats["item27_updated"] += 1

        if i2 is not None and i14 and i14 != 0:
            expected28 = i2 / i14 * 100.0
            if 28 not in items:
                row28 = _ensure_item_row(
                    rows,
                    items,
                    code=code,
                    quarter=quarter,
                    item_no=28,
                    item_name="\uae30\ubcf8\uc790\ubcf8\ube44\uc728",
                )
                row28[KEY_VAL] = _fmt_ratio(expected28)
                stats["item28_added"] += 1
            else:
                row28 = items[28]
                new_v = _fmt_ratio(expected28)
                cur = _to_float(row28.get(KEY_VAL))
                if not _is_plausible_ratio(cur) or cur is None or row28.get(KEY_VAL) != new_v:
                    row28[KEY_VAL] = new_v
                    stats["item28_updated"] += 1

        if post2 is None:
            post2 = i2
        # denominator: post-transition 기준금액 when disclosed (선택 경과조치 적용사 —
        # 농협생명/처브/교보플래닛 등), else pre. Mirrors kics_json_rules rule 8_post
        # (bucket.get(14, post=True) falls back to pre) — using i14 here while the
        # validator uses post14 manufactured RED for every post14-disclosing company.
        den14 = post14 if post14 not in (None, 0) else i14

        if post2 is not None and den14 and den14 != 0 and 28 in items:
            row28 = items[28]
            expected_post = post2 / den14 * 100.0
            cur_post = _to_float(row28.get(KEY_POST))
            new_post = _fmt_ratio(expected_post)
            if not _is_plausible_ratio(cur_post) or cur_post is None or row28.get(KEY_POST) != new_post:
                row28[KEY_POST] = new_post
                stats["item28_post_updated"] += 1

        row18 = items.get(18)
        if row18 is not None and row18.get(KEY_VAL) in (None, "", "-"):
            row18[KEY_VAL] = "0"
            stats["item18_zeroed"] += 1
        elif row18 is None and 17 in items:
            template = items[17]
            new_row = {
                KEY_CODE: code,
                KEY_NAME: template[KEY_NAME],
                KEY_TICKER: template[KEY_TICKER],
                KEY_KIND: template[KEY_KIND],
                KEY_ITEM: 18,
                KEY_INAME: "2. \uc77c\ubc18\uc190\ud574\ubcf4\ud5d8\uc704\ud5d8\uc561",
                KEY_Q: quarter,
                KEY_VAL: "0",
            }
            rows.append(new_row)
            items[18] = new_row
            stats["item18_added"] += 1

    return stats


def main(argv: list[str]) -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    print(f"loaded {len(rows)} rows")
    stats = recalc(rows)
    print("stats:", stats)
    if args.dry_run:
        print("(dry-run; no write)")
        return 0
    JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.copy2(JSON_PATH, TEMPLATES_JSON)
    print(f"wrote {len(rows)} rows; synced templates")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))