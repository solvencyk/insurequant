"""Read-only: build pl_plan.json (13 cells) + gold_notes.json from verify_xml.json (XML-derived, line-cited) and the live PL master (old values)."""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
HERE = Path(__file__).resolve().parent
V = json.loads((HERE / "verify_xml.json").read_text(encoding="utf-8"))
rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
live = {(r["공시분기"], r["항목번호"]): r for r in rows if r["원보험사코드"] == "KR0073"}
NAMES = {25: "기타포괄손익", 26: "FVOCI 채무증권 평가손익", 29: "FVOCI 지분증권 평가손익", 31: "총포괄손익", 32: "기타 포괄손익(미분류)"}
CELLS = {"2024.4Q": (25, 26, 31, 32), "2025.1Q": (25, 26, 31, 32), "2025.2Q": (25, 26, 29, 31, 32)}
FIL = {"2024.4Q": ("FY2025 사업보고서 rcept 20260331004015", "FY2024 사업보고서 rcept 20250331004015"),
       "2025.1Q": ("FY2026 1분기보고서 rcept 20260813001077", "FY2025 1분기보고서 rcept 20250515002967"),
       "2025.2Q": ("FY2026 반기보고서 rcept 20260814004024", "FY2025 반기보고서 rcept 20250814004112")}
NATURE = {
 ("2024.4Q", 25): "재작성(유배당보험계약 회계정책 변경 소급): 후속 사업보고서 주석 44-3 L71412 표 기타포괄손익 수정후 -3,856,081 / 수정전 -3,876,050 / 증감 19,969(백만원). 26+32 변동의 합",
 ("2024.4Q", 26): "재작성: 주석 변경내용 L71068 '10,932백만원 과소계상'; 원문 라벨 기타포괄손익-공정가치측정금융자산관련손익(원 공시) -> 기타포괄손익-공정가치측정채무증권평가손익(후속 공시)",
 ("2024.4Q", 31): "재작성: 총포괄손익 = 당기순이익(변동 없음) + 항목25. 24+25 로 닫힘",
 ("2024.4Q", 32): "재작성: 원 공시 자산재평가손익 -9,037.395 -> 후속 공시 유형자산재평가잉여금 0 ('9,037백만원 과소계상' L71068). 신용손실/손실충당금 -3,355.361 과 확정급여재측정 7,202.870 은 두 공시 같음. 계정 태그 이동 없음",
 ("2025.1Q", 25): "재작성(회계정책 변경 소급): 26(-1,856.00) + 32(-2,884.74)의 합",
 ("2025.1Q", 26): "재작성: 주석 변경내용 L54117 '1,856백만원 과대계상'",
 ("2025.1Q", 31): "재작성: 총포괄손익 = 당기순이익(변동 없음) + 항목25. 24+25 로 닫힘",
 ("2025.1Q", 32): "재작성: 원 공시 유형자산재평가잉여금 2,884.739 가 후속 공시 계산서에서 사라짐('2,885백만원 과대계상' L54117). 손실충당금 338.357 과 재측정 -216.375 는 같음. 계정 태그 이동 없음(항목29 7,425.340 은 두 공시 같음)",
 ("2025.2Q", 25): "재작성(회계정책 변경 소급): 26(-9,143.42) + 유형자산재평가잉여금 제거(-4,221.54, 항목32 안)의 합. 주석 43-2 표 기타포괄손익 수정후 (925,329) / 수정전 (911,964) / 증감 (13,365)",
 ("2025.2Q", 26): "재작성: 주석 변경내용 L49799 '9,143백만원 과대계상'",
 ("2025.2Q", 29): "재작성 아님(계정 태그 이동의 정상화): 원 공시 계산서도 같은 줄 '기타포괄손익-공정가치측정지정지분증권평가손익' 28,364,988,485원 을 인쇄(FY2025_Q2 xml L38058) — 마스터 29 가 비었던 것은 원 공시 시점 FS-API 태그가 이 줄을 항목32 로 보냈기 때문. 빈칸을 채움",
 ("2025.2Q", 31): "재작성: 총포괄손익 = 당기순이익(변동 없음) + 항목25. 24+25 로 닫힘",
 ("2025.2Q", 32): "합성 변동 -32,586.53 = 계정 태그 이동 -28,364.99(항목29 로 이동; 원 공시도 같은 줄 인쇄) + 재작성 -4,221.54(유형자산재평가잉여금 4,221.538 제거; '4,222백만원 과대계상' L49799). 남는 값 = 손실충당금 344.046 + 재측정 -316.424",
}
plan, notes = [], {}
for q, items in CELLS.items():
    v = V[q]
    later_file = v["later_file"]
    for it in items:
        new = round(v["later"][str(it)], 6)
        old = live[(q, it)].get("값")
        c = v["later_cites"][str(it)]
        cite = (f"L{c}" if it != 32 else "L" + "+L".join(str(x[2]) for x in c))
        oc = v["orig_cites"][str(it)]
        ocite = (f"L{oc}" if it != 32 else "L" + "+L".join(str(x[2]) for x in oc))
        if it == 29 and q == "2025.2Q":
            ocite = f"L{oc} (원 공시 별도 포괄손익계산서도 28,364.988485 인쇄)"
        plan.append({"quarter": q, "item": it, "name": NAMES[it], "old": old, "new": new, "cls": "FILL" if old is None else "CHANGED", "flags": []})
        notes[f"{q}|{it}"] = (f"2026-10-22 parser/ifrs17 (KR0073 OCI refresh, ticket 20261021T1556Z): latest-comparative, 별도 기준 누계. {FIL[q][0]} 별도 포괄손익계산서 "
                              f"전기(누적) 열 {later_file} {cite} = {new:,.6f} 백만원 (원 공시 {FIL[q][1]} 현재 마스터 기준값 {live[(q, it)].get('값')}, 원문 {ocite}). {NATURE[(q, it)]}. "
                              f"블록 닫힘: 25=26+27+28+29+30+32 잔차 0.000, 31=24+25. 근거 data/_derived/remaining_20261022/a_oci/verify_xml.txt")
        # check against the FS-API-derived number from the dry run
(HERE / "pl_plan.json").write_text(json.dumps({"plan": plan, "skipped": []}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
(HERE / "gold_notes.json").write_text(json.dumps(notes, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
alt = json.loads((ROOT / "data/_derived/kyobo_pl_restate_dryrun_20261021/restated_blocks_alt.json").read_text(encoding="utf-8"))
a26 = json.loads((ROOT / "data/_derived/kyobo_pl_restate_dryrun_20261021/restated_blocks_2026.json").read_text(encoding="utf-8"))
print(len(plan), "cells")
bad = 0
for c in plan:
    ref = (alt if c["quarter"] == "2024.4Q" else a26)[c["quarter"]]["restated_alt"][str(c["item"])]
    ok = abs(ref - c["new"]) < 5e-6
    bad += (not ok)
    print(f"{c['quarter']} item {c['item']:2d} {c['cls']:7s} old={c['old']} new={c['new']:,.6f}  fsapi={ref:,.6f} {'OK' if ok else 'MISMATCH'}")
print("xml vs FS-API mismatches:", bad)
