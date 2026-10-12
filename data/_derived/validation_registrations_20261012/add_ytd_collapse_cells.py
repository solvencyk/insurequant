# -*- coding: utf-8 -*-
"""owner 승인 2026-10-12: 재보사 인쇄된 0 7칸을 data/_gold/user_pl_confirmed_cells.json 에 등재(rule=PL_YTD_COLLAPSE_TO_ZERO).
재현: python <이 파일>  (이미 등재돼 있으면 중단). CRLF·들여쓰기 보존 삽입, 마커는 게이트 함수로 먼저 재현해야 쓴다."""
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "scripts")
import validate_kics_disclosure as K

P = "data/_gold/user_pl_confirmed_cells.json"
APPROVED = ("owner 2026-10-12 (inbox/validation/20261012T1010Z 티켓에 인용된 채팅 승인 「나머지는 다 승인」, "
            "TODO.md 결정 ⑯ 재보사 인쇄된 0 7칸)")
TAIL = (" 등재는 이 셀만이다 -- 값이 바뀌거나 인용 문구가 사라지면 PL_YTD_COLLAPSE_TO_ZERO RED 가 돌아온다. "
        "근거: data/disclosure/_meta/reinsurer ... 재스윕 런로그 runlog_8th.md · 후보 data/_derived/reinsurer_resweep_20261012/"
        "proposed_owner_confirmed_cells_ytd_collapse_resweep_20261012.json · 상태 collapse7_state.json.")
TAIL = TAIL.replace("data/disclosure/_meta/reinsurer ... 재스윕 런로그 runlog_8th.md", "data/_derived/reinsurer_resweep_20261012/runlog_8th.md")

# (회사, 분기, 항목, 직전분기 누계(백만원), 원문 파일, 쪽, 열 설명, 인쇄값 설명, 마커)
CELLS = [
 ("뮌헨재보험", "2023.4Q", "투자손익", -1800.0, "data/disclosure/FY2023_Q4/raw/KR1101_뮌헨재보험.pdf", [9],
  "3-2-1) 감독회계 기준 총괄계정 요약 포괄손익계산서(억원) 2023년 열(해당 분기)",
  "투자손익 0 (투자수익 224 - 투자비용 224 = 0), 전년 열 -35, 증감 34; 보험손익 732 + 투자손익 0 vs 영업이익 731, 영업이익 731 + 영업외 2 = 세전 733",
  ["(2023년)(2022년)", "투자손익0-3534", "영업이익(또는영업손실)731508223", "법인세비용차감전순이익733508225"]),
 ("알지에이리인슈어런스", "2023.2Q", "영업외손익", -100.0, "data/disclosure/FY2024_Q2/raw/KR1105_알지에이리인슈어런스.pdf", [5],
  "2-1-1) 요약 포괄손익계산서(억원) 이듬해 같은 분기(2024.2Q) 공시의 전년 동기(23.2Q) 열",
  "영업외손익 해당분기 2 / 전년동기 0 / 증감 2 (영업외수익 1 - 영업외비용 1 = 0); 영업이익 45 + 0 vs 세전 46 (1억 반올림)",
  ["해당분기(24.2Q)전년동기(23.2Q)증감", "영업외손익202(영업외수익)", "영업이익(또는영업손실)16545119", "법인세비용차감전순이익(또는법인세비용차감전순손실)16646121"]),
 ("알지에이리인슈어런스", "2025.3Q", "영업외손익", 100.0, "data/disclosure/FY2025_Q3/raw/KR1105_알지에이리인슈어런스.pdf", [4],
  "2-1-1) 요약 포괄손익계산서(억원) 해당 분기(25.3Q) 열",
  "영업외손익 해당분기 0 / 전년동기 3 / 증감 -3 (영업외수익 3 - 영업외비용 3 = 0); 영업이익 251 + 0 vs 세전 252 (1억 반올림)",
  ["해당분기(25.3Q)전년동기(24.3Q)증감", "영업외손익03-3(영업외수익)", "영업이익(또는영업손실)251328-77", "법인세비용차감전순이익(또는법인세비용차감전순손실)252331-79"]),
 ("제네럴재보험", "2024.3Q", "영업외손익", 22.0, "data/disclosure/FY2025_Q3/raw/KR1103_제네럴재보험.pdf", [4],
  "2-1-1) 요약 포괄손익계산서(억원) 이듬해 같은 분기(2025.3Q) 공시의 전년 동기(24.3Q) 열 -- 최신 공시의 전기 칸 채택(owner 2026-10-09 R1 규칙)",
  "영업외손익 해당분기 0 / 전년동기 (0) / 증감 (0) -- 괄호는 음수로 인쇄돼 억원 단위에서 0 으로 반올림된 값이다(영업외수익 0 - 영업외비용 1); 영업이익 66 + 0 = 세전 66. 마스터 값 0.0 은 억원 해상도의 인쇄값이다",
  ["영업외손익0(0)(0)(영업외수익)", "영업이익(또는영업손실)(39)66(106)", "법인세비용차감전순이익(40)66(106)"]),
 ("제네럴재보험", "2025.3Q", "영업외손익", -34.0, "data/disclosure/FY2025_Q3/raw/KR1103_제네럴재보험.pdf", [4],
  "2-1-1) 요약 포괄손익계산서(억원) 해당 분기(25.3Q) 열",
  "영업외손익 해당분기 0 / 전년동기 (0) / 증감 (0) (영업외수익 0 - 영업외비용 0 = 0); 영업이익 (39) + 0 vs 세전 (40) (1억 반올림)",
  ["영업외손익0(0)(0)(영업외수익)", "영업이익(또는영업손실)(39)66(106)", "법인세비용차감전순이익(40)66(106)"]),
 ("퍼시픽라이프리", "2023.3Q", "영업외손익", 70.0, "data/disclosure/FY2024_Q3/raw/KR1107_퍼시픽라이프리.pdf", [4],
  "2-1-1) 요약 포괄손익계산서(억원) 이듬해 같은 분기(2024.3Q) 공시의 전년 동기(23.3Q) 열 (좌표 확인: 라벨 열의 '-' 는 별개, 해당분기 1 / 전년동기 0 / 증감 -1)",
  "영업외손익 전년동기 0 (영업외수익 0 - 영업외비용 0); 영업이익 -46 + 0 vs 세전 -45 (1억 반올림)",
  ["해당분기(24.3Q)", "전년동기(23.3Q)", "영업외손익1-0-1", "132-46178"]),
 ("퍼시픽라이프리", "2025.3Q", "영업외손익", 100.0, "data/disclosure/FY2025_Q3/raw/KR1107_퍼시픽라이프리.pdf", [4],
  "2-1-1) 요약 포괄손익계산서(억원) 해당 분기(25.3Q) 열",
  "영업외손익 해당분기 0 / 전년동기 -1 / 증감 1 (영업외수익 13, 영업외비용 12 와 소계 0 은 억원 반올림으로 1 어긋난다); 영업이익 -9 + 0 = 세전 -9",
  ["해당분기(25.3Q)전년동기(24.3Q)증감", "영업외손익0-11(영업외수익)", "영업이익(또는영업손실)-9132-142", "법인세비용차감전순이익(또는법인세비용차감전순손실)-9132-140"]),
]

def build():
    out = []
    for co, q, item, prev, f, pages, where, printed, markers in CELLS:
        v = {"file": f, "pages": pages, "present_markers": markers}
        bad, why = K._verify_absent_markers(v)
        assert K._verify_markers_ran(v) and not bad, (co, q, why)
        out.append({
            "master": "PL_breakdown", "company": co, "quarter": q, "item": item, "value": 0.0,
            "rule": "PL_YTD_COLLAPSE_TO_ZERO", "approved": APPROVED,
            "note": (f"원문 {f} p{pages[0]} {where}: {printed}. 직전분기 누계 {prev:,.1f}(백만원)이 이 분기 0.0 으로 보이는 것은 "
                     f"재빌드 결손이 아니라 원문이 0 을 인쇄했기 때문이다(owner 확정). 마커는 게이트가 매 실행 원문 쪽을 다시 열어 재확인한다 "
                     f"(validation 2026-10-12 재현)." + TAIL),
            "verify": v,
        })
    return out

if __name__ == "__main__":
    raw = open(P, "rb").read().decode("utf-8")
    d = json.loads(raw)
    have = {(c["company"], c["quarter"], c["item"]) for c in d["cells"]}
    cells = build()
    for c in cells:
        assert (c["company"], c["quarter"], c["item"]) not in have, c
    txt = ",\r\n".join("\r\n".join("    " + ln for ln in json.dumps(c, ensure_ascii=False, indent=2).split("\n")) for c in cells)
    anchor = "\r\n  ]\r\n}"
    assert raw.rstrip("\r\n").endswith(anchor) and raw.count(anchor) == 1
    new = raw.rstrip("\r\n")[: -len(anchor)] + ",\r\n" + txt + anchor + "\r\n"
    json.loads(new)
    open(P, "wb").write(new.encode("utf-8"))
    print("appended", len(cells))
