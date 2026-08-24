"""KR0075(BNP카디프) 가 INCL 로 판정되는 근거가 **오염된 셀**에 기대고 있지 않은지 확인.

이 회사는 `item47 == item48` 이 전 분기 반복된다(게이트가 `TIER2_DUPLICATE_ROW` 로 이미
플래그한 상태). 만약 item48 이 `item14 × 50%` 와 맞고 item47 만 그 값을 베낀 것이라면,
스코프 투표의 입력 자체가 오염된 것이므로 INCL 판정을 근거로 쓸 수 없다.

여기서는 KR0075 전 분기에 대해 item14×50% · item47 · item48 · item49 · item3 · item51 을
나란히 찍고, 두 읽기의 재현 여부를 센다. INCL 로 갈린 버킷이 무엇인지도 같이 인쇄한다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.solvency.validation import kics_json_rules as R  # noqa: E402

OUT = ROOT / "artifacts" / "validation" / "probe_20260824_kr0075_scope_evidence.txt"
CODES = ("KR0075", "KR0004", "KR0068", "KR0079", "KR0080")


def main():
    rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    buckets = R._group_records(rows)
    lines = []
    for code in CODES:
        bs = sorted((b for b in buckets if b.code == code), key=lambda b: b.quarter)
        if not bs:
            continue
        lines.append(f"===== {code} {bs[0].name} =====")
        lines.append(f"{'분기':<9}{'col':<5}{'i14x50%':>11}{'i47':>11}{'i48':>11}{'i49':>11}"
                     f"{'i3':>11}{'i51':>11}{'EXCL기대':>11}{'INCL기대':>11}  판정")
        for b in bs:
            tol = (R.IMAGE_OCR_TOLERANCE if b.code in R.IMAGE_OCR_COMPANIES else 2.0)
            for post, col in ((False, "전"), (True, "후")):
                src = b.values_post if post else b.values
                i3, i47, i48, i49 = src.get(3), src.get(47), src.get(48), src.get(49)
                i51 = src.get(51)
                i14 = b.values.get(14)
                if None in (i3, i47, i48, i49):
                    continue
                e = min(i47, i48) + i49
                i = min(i47 - i49, i48) + i49
                eok, iok = abs(i3 - e) <= tol, abs(i3 - i) <= tol
                verdict = ("EXCL표" if eok and not iok else
                           "INCL표" if iok and not eok else
                           "모호(둘다)" if eok and iok else "둘다실패")
                lines.append(
                    f"{b.quarter:<9}{col:<5}"
                    f"{(i14 * 0.5 if i14 is not None else float('nan')):>11,.2f}"
                    f"{i47:>11,.2f}{i48:>11,.2f}{i49:>11,.2f}{i3:>11,.2f}"
                    f"{(i51 if i51 is not None else float('nan')):>11,.2f}"
                    f"{e:>11,.2f}{i:>11,.2f}  {verdict}")
        lines.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
