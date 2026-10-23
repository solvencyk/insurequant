import json, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
unchecked = [tuple(x) for x in json.load(open("unchecked_part2.json"))]
LIFE = {"KR0068", "KR0069", "KR0070", "KR0071", "KR0072", "KR0079", "KR0082", "KR0083", "KR0087", "KR0094", "KR0099", "KR0104"}
STMT = {str(i) for i in (1, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32)}
cat = collections.Counter()
detail = collections.defaultdict(collections.Counter)
for c, q, i in unchecked:
    if q == "2025.3Q": k = "A 2025.3Q (FY2026 3Q filing does not exist)"
    elif i in ("13", "14") and c in LIFE: k = "B life items 13/14 = 0 by construction (master==0 verified, not source-read)"
    elif i.startswith("CSM"): k = "C CSM roll-forward of companies outside the brief (reader not written)"
    elif i in STMT: k = "D statement item not readable"
    elif i in ("4", "5", "6", "9", "10", "11"): k = "E note item: layout without a calibrated reader"
    else: k = "F derived/LOB item (2,3,7,8,12,13,14) needing LOB notes or unread legs"
    cat[k] += 1
    detail[k][c] += 1
for k in sorted(cat):
    print(cat[k], k)
    print("     ", dict(sorted(detail[k].items())))
print("total unchecked", len(unchecked))
