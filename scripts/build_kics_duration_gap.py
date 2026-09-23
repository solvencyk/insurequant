# -*- coding: utf-8 -*-
"""kics_duration_gap.json 빌더 — K-ICS 금리위험 듀레이션 갭 마스터.

owner 지시 (2026-09-22): 듀레이션 갭의 분모는 '금리위험액 현황' 표의 자산총계다.
건전성감독기준 재무상태표의 자산총계(전체 자산)가 아니다. 분자인 순자산가치 변동이
금리위험 측정 대상(금리부자산·금리부부채)에서만 나오므로 분모도 같은 범위여야
갭 = 자산듀레이션 - 부채듀레이션 항등식이 닫힌다. 전체 자산을 쓰면 특별계정·주식·
부동산처럼 분자에 0을 기여하는 자산이 분모만 불려 갭이 회사마다 다른 배율로 희석된다.

산식 (단위 억원):
    A0 = 자산총계(충격전) · L0 = 부채총계(충격전)
    자산듀레이션  D_A = (자산_금리하락 - 자산_금리상승) / (2% x A0)
    부채듀레이션  D_L = (부채_금리하락 - 부채_금리상승) / (2% x L0)
    듀레이션갭    GAP = D_A - (L0/A0) x D_L
부채듀레이션은 부채로 나눠 D_L 에서 끝난다 — L/A 는 갭을 구할 때 곱한다(owner 2026-09-22).
(L0/A0) x D_L 은 전개하면 (부채_금리하락 - 부채_금리상승)/(2% x A0) 이므로 L0 가 음수인
회사(라이나생명·AIG손해: 책임준비금이 음수)에서도 갭은 정의된다. 그때 D_L 자체는 음수 부채로
나눈 값이라 의미가 없어 비우고 비고에 남긴다.
부호 규약: 양수 = 금리 상승 시 순자산 감소(자산이 부채보다 길다).

주의: K-ICS 의 금리상승/하락 충격은 평행이동이 아니라 만기별 크기가 다른 기간구조
충격이다. 2%로 나누는 것은 owner 가 정한 근사이며 순위·상대크기는 유효하지만 절대
연수는 참고치다. 이 단서는 마스터 설명(build_master_xlsx.py MASTERS)에도 적는다.

입력
  data/_derived/kics_irr_balance.json   scripts/extract_kics_irr_balance.py 자동 추출분
  data/_gold/kics_irr_balance_vision.json  표가 이미지라 사람이 눈으로 읽은 16칸
  kics_disclosure.json                  항목 41/43/44 (순자산가치) — 검산 앵커
출력
  kics_duration_gap.json                루트 마스터 (회사 x 분기 1행)
  data/_derived/kics_duration_gap_audit.json  마스터 항목41~46 역검산 불일치 목록

Usage:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/build_kics_duration_gap.py
  옵션 --check 는 파일을 쓰지 않고 검산 결과만 인쇄한다.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AUTO = REPO / "data" / "_derived" / "kics_irr_balance.json"
GOLD = REPO / "data" / "_gold" / "kics_irr_balance_vision.json"
DISCLOSURE = REPO / "kics_disclosure.json"
OUT = REPO / "kics_duration_gap.json"
AUDIT = REPO / "data" / "_derived" / "kics_duration_gap_audit.json"

QS = ["2023.2Q", "2023.4Q", "2024.2Q", "2024.4Q", "2025.2Q", "2025.4Q", "2026.2Q"]
SCEN = [(41, "충격전"), (42, "평균회귀"), (43, "금리상승"), (44, "금리하락"),
        (45, "금리평탄"), (46, "금리경사")]
SHOCK = 0.02


def _load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def _tol(x):
    return max(1.0, abs(x) * 6e-4)


def main(argv):
    check_only = "--check" in argv
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    auto = _load(AUTO)
    gold = _load(GOLD)["cells"]
    kd = _load(DISCLOSURE)

    meta, master = {}, {}
    for r in kd:
        meta[r["원보험사코드"]] = (r["원수사명"], r["티커"], r["생손보여부"])
        if r["항목번호"] in (41, 42, 43, 44, 45, 46):
            try:
                master.setdefault((r["공시분기"], r["원보험사코드"]), {})[r["항목번호"]] = \
                    float(str(r["값"]).replace(",", ""))
            except (TypeError, ValueError):
                pass

    # 1) 자동 추출 + 비전 gold 병합 (gold 가 우선 — 자동이 못 읽은 칸만 들어 있다)
    cells = {}
    for k, v in auto.items():
        cells[k] = {"asset": {int(i): x for i, x in v["asset"].items() if x is not None},
                    "liab": {int(i): x for i, x in v["liab"].items() if x is not None},
                    "출처": v.get("src", ""), "추출경로": v.get("how", "")}
    for k, v in gold.items():
        cells[k] = {"asset": {it: v["asset_백만원"][i] / 100.0 for i, (it, _n) in enumerate(SCEN)},
                    "liab": {it: v["liab_백만원"][i] / 100.0 for i, (it, _n) in enumerate(SCEN)},
                    "출처": "vision:" + v["출처"], "추출경로": "vision"}

    # 2) 커버리지 센서스 — 항목41 이 있는 (분기,회사) 는 전부 있어야 한다
    need = {(r["공시분기"], r["원보험사코드"]) for r in kd
            if r["항목번호"] == 41 and r.get("값") not in (None, "")}
    missing = sorted(k for k in need if (k[0] + "|" + k[1]) not in cells)
    if missing:
        for q, c in missing:
            print(f"  MISSING {q} {c} {meta[c][0]}")
        sys.exit(f"REFUSE: 금리위험액 현황 표 {len(missing)}칸 결측 (대상 {len(need)})")

    # 3) 역검산 — 자산-부채 가 마스터 항목41~46(순자산가치)과 맞아야 한다
    audit = []
    for key in sorted(cells):
        q, c = key.split("|")
        a, l = cells[key]["asset"], cells[key]["liab"]
        for it, name in SCEN:
            if it not in a or it not in l or master.get((q, c), {}).get(it) is None:
                continue
            got, exp = a[it] - l[it], master[(q, c)][it]
            if abs(got - exp) > _tol(exp):
                audit.append({"공시분기": q, "원보험사코드": c, "원수사명": meta[c][0],
                              "항목번호": it, "시나리오": name,
                              "표_자산빼기부채_억원": round(got, 2), "마스터_억원": exp,
                              "배율": round(exp / got, 4) if got else None})

    # 발행사 표가 스스로 안 맞는 칸(순자산가치 행 != 자산-부채) 은 비고에 박제한다.
    # 갭은 자산·부채 행으로 계산해 GAP = D_A - (L/A)xD_L 항등식을 닫아 둔다 — 공시된 순자산가치
    # 행을 쓰면 그 항등식이 깨진다. (owner 규칙: 발행사 불일치는 공시대로 두고 표시)
    inconsistent = {(x["공시분기"], x["원보험사코드"]) for x in audit
                    if abs(x["배율"] or 1) < 1.5}

    # 4) 듀레이션 산출
    rows = []
    for key in cells:
        q, c = key.split("|")
        a, l = cells[key]["asset"], cells[key]["liab"]
        row = {"원보험사코드": c, "원수사명": meta[c][0], "티커": meta[c][1],
               "생손보여부": meta[c][2], "공시분기": q}
        for it, name in SCEN:
            row["자산_" + name] = round(a[it], 2) if it in a else None
            row["부채_" + name] = round(l[it], 2) if it in l else None
        a0, l0 = a.get(41), l.get(41)
        up, dn = a.get(43), a.get(44)
        lup, ldn = l.get(43), l.get(44)
        note = ""
        if None in (a0, l0, up, dn, lup, ldn):
            d_a = d_l = gap = ratio = None
            note = "표 항목 결측"
        elif a0 <= 0:
            d_a = d_l = gap = ratio = None
            note = "금리부자산 충격전 ≤ 0 — 분모 불성립(듀레이션 정의 안 됨)"
        else:
            den = SHOCK * a0
            d_a = round((dn - up) / den, 4)
            gap = round(((dn - up) - (ldn - lup)) / den, 4)   # = D_A - (L/A) x D_L
            ratio = round(l0 / a0, 4)
            if l0 > 0:
                d_l = round((ldn - lup) / (SHOCK * l0), 4)
            else:
                d_l = None
                note = "금리부부채 충격전 ≤ 0 — 부채듀레이션 정의 안 됨(갭은 유효)"
        if (q, c) in inconsistent:
            flag = "발행사 표 불일치(순자산가치 행 ≠ 자산-부채) — 갭은 자산·부채 행 기준"
            note = (note + " / " + flag) if note else flag
        row.update({"자산듀레이션": d_a, "부채듀레이션": d_l,
                    "부채자산비율": ratio, "듀레이션갭": gap, "비고": note})
        rows.append(row)

    rows.sort(key=lambda r: (QS.index(r["공시분기"]) if r["공시분기"] in QS else 99,
                             r["원보험사코드"]))

    gaps = [r["듀레이션갭"] for r in rows if r["듀레이션갭"] is not None]
    print(f"셀 {len(rows)} (대상 {len(need)}) · 갭 산출 {len(gaps)} · "
          f"산출불가 {len(rows) - len(gaps)}")
    print(f"갭 범위 {min(gaps):.2f} ~ {max(gaps):.2f} 년")
    for r in rows:
        if r["듀레이션갭"] is None or r["비고"]:
            print(f"  NOTE {r['공시분기']} {r['원수사명']} — {r['비고']}")
    print(f"\n마스터 항목41~46 역검산 불일치 {len(audit)}건")
    for x in audit:
        print(f"  {x['공시분기']} {x['원수사명']} item{x['항목번호']}({x['시나리오']}) "
              f"표={x['표_자산빼기부채_억원']} 마스터={x['마스터_억원']} 배율={x['배율']}")

    if check_only:
        print("\n(--check: 파일 안 씀)")
        return 0
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nwrote {OUT.name} ({len(rows)} rows) · {AUDIT.relative_to(REPO)} ({len(audit)})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
