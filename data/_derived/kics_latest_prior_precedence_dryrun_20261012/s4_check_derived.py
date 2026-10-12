"""s4_check_derived.py -- READ-ONLY sanity check: does the harness's derived-item recompute reproduce what the master already holds?
(items 27 / 28 / 28후 / 27후 on every bucket)."""
import sys
from collections import Counter

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_precedence_dryrun_20261012")
from lib_dry import *  # noqa: F401,F403,E402
from harness import fmt_ratio  # noqa: E402

utf8_stdout()
rows = read_rows()
idx, names = master_index(rows)
cnt = Counter()
bad = []
for (c, q), m in idx.items():
    def g(it, f):
        if it not in m:
            return None
        return num(m[it][0 if f == "값" else 1])
    i1, i2, i14 = g(1, "값"), g(2, "값"), g(14, "값")
    if i1 is not None and i14:
        want = fmt_ratio(i1 / i14 * 100.0)
        have = m.get(27, (None,))[0]
        k = "27:same-string" if str(have) == want else ("27:close(<0.01)" if have is not None and abs(num(have) - i1 / i14 * 100) < 0.01 else "27:differs")
        cnt[k] += 1
        if k == "27:differs":
            bad.append((c, q, 27, have, want))
    if i2 is not None and i14:
        want = fmt_ratio(i2 / i14 * 100.0)
        have = m.get(28, (None,))[0]
        k = "28:same-string" if str(have) == want else ("28:close(<0.01)" if have is not None and abs(num(have) - i2 / i14 * 100) < 0.01 else "28:differs")
        cnt[k] += 1
        if k == "28:differs":
            bad.append((c, q, 28, have, want))
    p2 = g(2, "값_적용후") if g(2, "값_적용후") is not None else i2
    p14 = g(14, "값_적용후")
    den = p14 if p14 not in (None, 0) else i14
    if 28 in m and p2 is not None and den:
        want = fmt_ratio(p2 / den * 100.0)
        have = m[28][1]
        k = "28post:same-string" if str(have) == want else ("28post:close(<0.01)" if have is not None and abs(num(have) - p2 / den * 100) < 0.01 else "28post:differs")
        cnt[k] += 1
        if k == "28post:differs":
            bad.append((c, q, "28post", have, want))
    p1 = g(1, "값_적용후") if g(1, "값_적용후") is not None else i1
    if 27 in m and m[27][1] is not None and p1 is not None and den:
        want = fmt_ratio(p1 / den * 100.0)
        have = m[27][1]
        k = "27post:same-string" if str(have) == want else ("27post:close(<0.01)" if have is not None and abs(num(have) - p1 / den * 100) < 0.01 else "27post:differs")
        cnt[k] += 1
        if k == "27post:differs":
            bad.append((c, q, "27post", have, want))
for k in sorted(cnt):
    print(f"{k:24s} {cnt[k]}")
print("sample differs:", bad[:12])
