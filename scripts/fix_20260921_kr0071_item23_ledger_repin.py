"""Re-pin item23_post for KR0071's 5 buckets in data/_gold/kics_item23_children_post_absent.json.

Companion to scripts/fix_20260921_kr0071_item23_post_close_r5.py — the ledger pins item23 후 as a
drift guard (tol 0.5억). Verdict (SOURCE_ABSENT) and evidence are unchanged; only the pinned value
moves with the R5 re-closure. Byte-level string edit (CRLF/indent preserved), guarded on old value.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LEDGER = REPO / "data" / "_gold" / "kics_item23_children_post_absent.json"

REPINS = {
    "2023.2Q": ("5198.88", "5195.94"),
    "2023.3Q": ("4907.07", "4904.55"),
    "2025.2Q": ("5790.68", "5787.41"),
    "2025.4Q": ("6281.63", "6277.2"),
    "2026.1Q": ("6773.61", "6779.23"),
}
WHY = ("2026-09-21 repin {old}->{new}: item14후를 헤드라인 인쇄 정수로 정정(fix_20260921_item14_post_backsolve.py)"
       "하면서 R5(14=15-22+23) 잔차 셀인 item23후를 같은 식으로 재폐쇄(fix_20260921_kr0071_item23_post_close_r5.py). "
       "verdict·evidence 불변.")


def main() -> int:
    raw = LEDGER.read_bytes()
    text = raw.decode("utf-8")
    for q, (old, new) in REPINS.items():
        key = f'"KR0071|{q}"'
        i = text.find(key)
        if i < 0:
            print("ABORT key missing", key); return 1
        pat = re.compile(r'("item23_post":\s*)' + re.escape(old) + r'(,)')
        m = pat.search(text, i)
        if not m or m.start() - i > 400:
            print("ABORT old value not found near", key); return 1
        repl = f'{m.group(1)}{new},\r\n      "item23_post_repin": "{WHY.format(old=old, new=new)}"{m.group(2)}'
        # detect line ending style used in file
        if "\r\n" not in text:
            repl = repl.replace("\r\n", "\n")
        text = text[:m.start()] + repl + text[m.end():]
        print(f"  KR0071|{q}: item23_post {old} -> {new}")
    LEDGER.write_bytes(text.encode("utf-8"))
    import json
    json.loads(text)  # must still parse
    print("ok, still valid JSON")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
