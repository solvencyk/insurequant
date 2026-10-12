"""c3b_extract_terms.py (parser-kics, ticket 20261012T1230Z) -- READ ONLY on dart_sections/*.txt (written by c3_dart_sections.py).

Parses the per-bond key/value blocks of the 사업보고서 section "자본으로 인정되는 채무증권의 발행" into one row per (report, bond):
  발행일 | 발행금액 | 미상환잔액 | 발행금리 | 만기 및 조기상환 가능일 | 우선순위 | 회계처리 근거 | 기타 중요한 발행조건 (text) | step-up wording flag
The step-up flag is only a regex on the issuer's own words (스텝업|Step|금리상향|상향 조정|가산); the reading of each text is done by hand in c4.
Output: census_dart_terms.csv (utf-8-sig) + census_dart_terms.json.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_securities_classification_census_20261012/c3b_extract_terms.py
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
HERE = Path(__file__).resolve().parent
SEC = HERE / "dart_sections"

LABELS = {
    "발행일": "issue", "발행금액": "amount", "발행목적": "purpose", "발행방법": "method", "상장여부": "listed", "미상환잔액": "outstanding",
    "자본인정에관한사항": None, "회계처리근거": "accounting", "신용평가기관의자본인정비율등(주)": "rating_ratio", "신용평가기관의자본인정비율등": "rating_ratio",
    "미지급누적이자": "unpaid", "만기및조기상환가능일": "maturity_call", "발행금리": "coupon", "우선순위": "priority",
    "부채분류시재무구조에미치는영향": "debt_effect", "기타중요한발행조건등": "other_terms",
}
STEP = re.compile(r"스텝\s*업|step[\s-]*up|금리\s*상향|상향\s*조정|가산|조정됩니다|재산정|재설정|리셋", re.I)


def norm(s: str) -> str:
    return re.sub(r"\s+", "", s)


DATE_LINE = re.compile(r"^\d{4}\s*[년\.\-/]\s*\d{1,2}\s*[월\.\-/]\s*\d{1,2}")
rows = []
for fn in sorted(SEC.glob("*.txt")):
    code, period = fn.name.split("_")[0], "_".join(fn.name.split("_")[1:3])
    lines = []
    in_sec = False
    for ln in fn.read_text(encoding="utf-8").splitlines():
        if ln.startswith("## SECTION"):
            in_sec = True
            continue
        if ln.startswith("## NOTE HITS"):
            in_sec = False
        if in_sec and " | " in ln:
            no, txt = ln.split(" | ", 1)
            lines.append((int(no.strip()), txt.strip()))
    i = 0
    cur = None
    cur_key = None
    while i < len(lines):
        no, txt = lines[i]
        if norm(txt) == "발행일" and i + 1 < len(lines) and DATE_LINE.match(lines[i + 1][1]):
            if cur:
                rows.append(cur)
            cur = {"code": code, "period": period, "file": fn.name, "line_no": no, "issue": lines[i + 1][1], "fields": {}}
            cur_key = None
            i += 2
            continue
        if cur is not None:
            key = LABELS.get(norm(txt), "?")
            if key != "?":
                cur_key = key if key else cur_key
                if key:
                    cur["fields"].setdefault(key, [])
            elif cur_key:
                cur["fields"].setdefault(cur_key, []).append(txt)
        i += 1
    if cur:
        rows.append(cur)

out = []
for r in rows:
    f = {k: " ".join(v) for k, v in r["fields"].items()}
    other = f.get("other_terms", "")
    out.append({
        "code": r["code"], "period": r["period"], "file": r["file"], "line_no": r["line_no"], "issue_date": re.sub(r"\s+", "", r["issue"])[:12],
        "amount": f.get("amount"), "outstanding": f.get("outstanding"), "coupon": f.get("coupon"), "maturity_call": (f.get("maturity_call") or "")[:200],
        "priority": (f.get("priority") or "")[:80], "accounting": (f.get("accounting") or "")[:300], "other_terms": other[:700],
        "step_wording_in_other_terms": bool(STEP.search(other)),
    })
cols = ["code", "period", "issue_date", "amount", "outstanding", "coupon", "maturity_call", "priority", "step_wording_in_other_terms", "other_terms", "accounting", "file", "line_no"]
with open(HERE / "census_dart_terms.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(out)
(HERE / "census_dart_terms.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("blocks:", len(out), "| companies:", sorted({o["code"] for o in out}))
from collections import Counter  # noqa: E402

print("per company blocks:", dict(Counter(o["code"] for o in out)))
print("step wording flagged:", sum(1 for o in out if o["step_wording_in_other_terms"]))
