"""READ-ONLY. KR1000 면제 재감사 — 판정 근거 산수 한 장.

세 가지를 한 화면에서 대조한다. 마스터·PDF 는 읽기만 한다.

  (A) 축 B(`3_tier2_composition`) 잔차가 단조 증가하는 이유 — TFI(공통적용 경과조치)
      재분류액이 매 분기 `지급여력기준금액 × 5%` 로 커지기 때문임을 실측으로 보인다.
      즉 잔차를 만드는 "빠진 항" 은 경과조치 자체이고, 그건 **적용전 컬럼에 들어가면
      안 되는 항**이다.
  (B) 2024.4Q 필링(FY2024_Q4 p24)이 2024.2Q·2024.3Q 비교컬럼을 **재작성**했고,
      재작성값이 우리 룰의 기대식 `min(47,48)+49` 와 일치한다 — 발행사 스스로
      원래 인쇄값이 적용전이 아니었음을 인정한 셈이다.
  (C) 마스터 item2/item3 의 적용전 값이 적용후 값에서 미러링된 게 아님을
      **정밀도 지문**(적용전=억원 정수 / 적용후=백만원÷100)으로 보인다.

사용: probe_20260824_reaudit_kr1000_verdict.py --out <utf8 파일>
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "kics_disclosure.json"

K_CODE, K_ITEM, K_Q, K_PRE, K_POST = ("원보험사코드", "항목번호", "공시분기", "값", "값_적용후")
CODE = "KR1000"
QS = ["2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q"]

# FY2024_Q4 raw p24 `[경과조치 적용 전 지급여력비율 세부]` 3개 비교컬럼 (억원), fitz 판독.
RESTATED_2024Q4_FILING = {          # quarter -> (기본자본, 보완자본, 순자산, 불인정, 재분류)
    "2024.4Q": (32860, 8953, 42723, 910, 7863),
    "2024.3Q": (33420, 7077, 40497, 0, 5996),
    "2024.2Q": (32931, 6504, 39435, 0, 5444),
}
# 각 분기 자기 필링의 헤드라인표 (억원), fitz 판독.
AS_ORIGINALLY_FILED = {
    "2024.3Q": (34501, 5996, 40497, 0, 5996),
    "2024.2Q": (33991, 5444, 39435, 0, 5444),
}


def num(v):
    if v is None:
        return None
    s = str(v).replace(",", "").replace("△", "-").strip()
    try:
        return float(s) if s else None
    except ValueError:
        return None


def main() -> None:
    out_path = sys.argv[sys.argv.index("--out") + 1]
    recs = json.load(io.open(MASTER, encoding="utf-8"))
    rows = [r for r in recs if r.get(K_CODE) == CODE]
    g: dict[str, dict[int, dict]] = {}
    for r in rows:
        g.setdefault(r.get(K_Q), {})[r.get(K_ITEM)] = r

    def v(q, n, post=False):
        return num((g.get(q, {}).get(n) or {}).get(K_POST if post else K_PRE))

    b: list[str] = []
    b.append("(A) 축 B 잔차의 정체 — TFI 재분류액 = 지급여력기준금액(item14) x 5%")
    b.append("%-9s %10s %10s %10s %10s %10s %10s %10s" % (
        "분기", "item3", "min(47,48)+49", "잔차", "i51_pre", "i51_post", "i50후-i50전", "i14x5%"))
    for q in QS:
        i3, i47, i48, i49 = v(q, 3), v(q, 47), v(q, 48), v(q, 49)
        i50p, i50q = v(q, 50), v(q, 50, True)
        i51p, i51q = v(q, 51), v(q, 51, True)
        i14 = v(q, 14)
        exp = min(i47, i48) + i49
        b.append("%-9s %10.2f %13.2f %10.2f %10s %10s %10s %10.2f" % (
            q, i3, exp, i3 - exp,
            "%.2f" % i51p if i51p is not None else "-",
            "%.2f" % i51q if i51q is not None else "-",
            "%.2f" % (i50q - i50p) if None not in (i50p, i50q) else "-",
            i14 * 0.05))

    b.append("")
    b.append("(B) FY2024_Q4 p24 가 2024.2Q/2024.3Q 비교컬럼을 재작성했다 "
             "— 재작성값 vs 우리 룰 기대식")
    b.append("%-9s %-24s %10s %10s %10s" % (
        "분기", "무엇", "그때 필링", "24.4Q 필링", "룰 기대식"))
    for q in ("2024.3Q", "2024.2Q"):
        i47, i48, i49 = v(q, 47), v(q, 48), v(q, 49)
        exp_t2 = min(i47, i48) + i49
        i50p = v(q, 50)
        orig, rest = AS_ORIGINALLY_FILED[q], RESTATED_2024Q4_FILING[q]
        b.append("%-9s %-24s %10d %10d %10.2f" % (q, "보완자본", orig[1], rest[1], exp_t2))
        b.append("%-9s %-24s %10d %10d %10.2f" % (q, "기본자본", orig[0], rest[0], i50p))
        b.append("%-9s %-24s %10d %10d %10s" % (q, "III.재분류(재작성 안 함)",
                                                orig[4], rest[4], "-"))
    b.append("")
    b.append("(B2) FY2024_Q4 p24 세 컬럼 전부 자기 구성행과 안 닫힌다 "
             "(순자산 - 불인정 - 재분류 vs 인쇄 기본자본)")
    for q, (t1, t2, na, ni, rc) in RESTATED_2024Q4_FILING.items():
        b.append("  %-9s %d - %d - %d = %d  vs 인쇄 기본자본 %d  -> 잔차 %d   "
                 "(그 분기 item14x5%% = %.2f)"
                 % (q, na, ni, rc, na - ni - rc, t1, t1 - (na - ni - rc), v(q, 14) * 0.05))

    b.append("")
    b.append("(C) 정밀도 지문 — 적용전이 적용후에서 미러링된 게 아니다")
    b.append("%-9s %-16s %-16s %-16s %-16s" % ("분기", "item2 전", "item2 후", "item3 전", "item3 후"))
    for q in QS:
        b.append("%-9s %-16s %-16s %-16s %-16s" % (
            q, (g[q].get(2) or {}).get(K_PRE), (g[q].get(2) or {}).get(K_POST),
            (g[q].get(3) or {}).get(K_PRE), (g[q].get(3) or {}).get(K_POST)))
    b.append("  적용전은 억원 정수(헤드라인표 인쇄 그대로), 적용후는 백만원/100 의 소수 2자리")
    b.append("  (TFI 표에서 독립 추출). 미러링이면 적용전에도 소수가 남았을 것이다.")

    io.open(out_path, "w", encoding="utf-8").write("\n".join(b))
    print("written", out_path)


if __name__ == "__main__":
    main()
