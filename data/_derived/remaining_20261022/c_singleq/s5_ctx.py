# -*- coding: utf-8 -*-
"""Print tag-stripped context of raw DART XML line ranges (independent reader, no scripts/ import).
usage: s5_ctx.py <xml path relative to repo> <start> <end> [<start> <end> ...]   -> appends to s5_ctx.txt"""
import re, sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
p = ROOT / sys.argv[1]
b = p.read_bytes()
for enc in ("utf-8", "cp949", "euc-kr"):
    try:
        t = b.decode(enc); break
    except UnicodeDecodeError:
        continue
lines = t.splitlines()
TAG = re.compile(r"<[^>]+>")
out = [f"#### {sys.argv[1]}"]
args = sys.argv[2:]
for s, e in zip(args[0::2], args[1::2]):
    out.append(f"--- L{s}-L{e}")
    buf = []
    for i in range(int(s), min(int(e), len(lines)) + 1):
        x = re.sub(r"\s+", " ", TAG.sub(" ", lines[i - 1])).strip()
        if x:
            buf.append(f"{i}:{x}")
    # compact: join cells of a row (rows end at </TR>) -- keep simple: one line per non-empty source line
    out.extend(buf)
with open(HERE / "s5_ctx.txt", "a", encoding="utf-8") as f:
    f.write("\n".join(out) + "\n")
print("\n".join(out))
