# -*- coding: utf-8 -*-
"""pv3 check 3b: public PL changed cells == master changed cells (HEAD~1 -> HEAD); manifest raw diff is only generated_at_utc + build_id."""
import json
import subprocess
import sys

REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
sys.stdout.reconfigure(encoding="utf-8")


def gb(rev, path):
    return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=REPO, capture_output=True, check=True).stdout


def n_(v):
    if v is None or v == "":
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return v
    return int(f) if f.is_integer() else f


mo = json.loads(gb("HEAD~1", "PL_breakdown.json").decode("utf-8"))
mn = json.loads(gb("HEAD", "PL_breakdown.json").decode("utf-8"))
ko = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r for r in mo}
kn = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r for r in mn}
mchg = {(k, c) for k in kn for c in ("값", "값_당분기") if n_(kn[k].get(c)) != n_(ko[k].get(c))}
old = json.loads(gb("HEAD", "public_exports/손익분해PL.json").decode("utf-8"))
new = json.load(open(REPO + "/public_exports/손익분해PL.json", encoding="utf-8"))
pchg = set()
for a, b, m in zip(old, new, mn):
    k = (m["원보험사코드"], str(m["항목번호"]), m["공시분기"])
    assert (a["항목번호"], a["공시분기"], a["원수사명"]) == (m["항목번호"], m["공시분기"], m["원수사명"]) == (b["항목번호"], b["공시분기"], b["원수사명"])
    for c in b:
        if a.get(c) != b.get(c):
            pchg.add((k, c))
print("public PL changed cells:", len(pchg), "| master changed cells:", len(mchg), "| equal:", pchg == mchg)
print("public PL columns:", list(new[0]))
# manifest line diff
hl = gb("HEAD", "public_exports/manifest.json").decode("utf-8").replace("\r\n", "\n").split("\n")
wl = open(REPO + "/public_exports/manifest.json", "rb").read().decode("utf-8").replace("\r\n", "\n").split("\n")
print("manifest line count HEAD/WORK:", len(hl), len(wl))
print("manifest differing lines:", [(a.strip(), b.strip()) for a, b in zip(hl, wl) if a != b])
print("HEAD manifest has CRLF:", b"\r\n" in gb("HEAD", "public_exports/manifest.json"), "| WORK has CRLF:", b"\r\n" in open(REPO + "/public_exports/manifest.json", "rb").read())
# other files in public_exports untouched
st = subprocess.run(["git", "status", "--short", "--", "public_exports"], cwd=REPO, capture_output=True, text=True, encoding="utf-8").stdout
print("git status public_exports:", st.replace("\n", " | "))
