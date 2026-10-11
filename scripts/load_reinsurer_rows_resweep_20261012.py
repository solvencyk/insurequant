# -*- coding: utf-8 -*-
"""Cell-level additive load of reinsurer CSM_amortization / CSM_sensitivity rows found by the 2026-10-12 re-sweep.

Ticket: inbox/parser/20261012T0120Z__orchestrator__KR1101-KR1108_2023.1Q-2026.2Q__reinsurer_csm_ilp_sensitivity_resweep.md

Rows (printed numbers typed below with their source page):
  amort : 2023.4Q years 1-5 of KR1101 / KR1102 / KR1106 from the FY2023 audit-report note 'future amortization of CSM'
          (buckets 1년미만 .. 4~5년 are printed individually; 6~10 years exist only as ONE '5~10년' bucket -> years 6-10 are NOT
          written (no even split); the aggregate is kept in held_resweep.json).
  sens  : KR1104 2023.4Q (FY2024 disclosure 4-6-5 (1), 2023 column; page rendered and read, signs verified by eye).

Guards = same as load_reinsurer_csm_masters_20261011.py: byte round trip, no overwrite of existing keys, backup + sha256,
prefix proof afterwards.   default = dry run;  --apply writes;  --revert --apply removes exactly these rows.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/load_reinsurer_rows_resweep_20261012.py [--apply] [--revert]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "data" / "_derived" / "reinsurer_csm_resweep_20261012"
BACKUP = EV / "backup"
sys.stdout.reconfigure(encoding="utf-8")

# ---- printed amortization buckets (unit, [y1, y2, y3, y4, y5], bucket 5~10, total) per component row, issued/assumed business only
AMORT = {
    ("KR1101", "2023.4Q"): {
        "unit": 1e-8, "pdf": "FY2023_Q4/raw_aux/KR1101_뮌헨재보험__audit.pdf", "page": 72,
        "rows": {  # 발행한 보험계약: 생명보험 + 장기손해보험 (원); '보유하고 있는 재보험계약' rows are NOT read
            "생명보험": [9742034270, 2643088666, 2374737044, 2185882832, 1995558843, 8086943512, 39986324402],
            "장기손해보험": [7159412939, 610666146, 588174665, 566360723, 510161114, 820098298, 10254873885],
        },
        "closing": 502.41198,
    },
    ("KR1102", "2023.4Q"): {
        "unit": 1e-5, "pdf": "FY2023_Q4/raw_aux/KR1102_스위스리아시아__audit.pdf", "page": 75,
        "rows": {  # 16.9 ① 당기, 수재보험 합계 row (일반+장기+생명) (천원)
            "수재보험 합계": [65540644, 42250901, 34616145, 28239681, 21137664, 52045734, 255759060],
        },
        "closing": 2557.5906,
    },
    ("KR1106", "2023.4Q"): {
        "unit": 1e-5, "pdf": "FY2023_Q4/raw/KR1106_스코리재보험.pdf", "page": 112,
        "rows": {  # 12.6 <당기> 수재보험 장기 + 생명 (천원)
            "수재 장기": [22731919, 21550481, 20548551, 19432147, 18493202, 71654575, 389727848],
            "수재 생명": [6620466, 6369255, 5957567, 5555038, 5273767, 23863433, 210543953],
        },
        "closing": 6002.71804,
    },
}

# ---- Hannover 2023 sensitivity, printed in 백만원 on FY2024 filing p25 (<2023년>); (FCF, CSM, 당기손익, OCI) signed as printed
HANOVER_2023 = {
    "pdf": "FY2024_Q4/raw/KR1104_하노버재보험.pdf", "page": 25,
    "rows": [
        (1, "사망률", "3.27% 증가", [(435, -435, -2070, -569)]),
        (2, "장해질병(정액보상+실손보상)", "정액 3.40% & 실손 2.62% 증가", [(4900, -4900, -3235, -228)]),
        (3, "장기재물기타", "4.19% 증가", None),
        (4, "해지율(상승)", "9.16% 증가", [(2685, -2685, -1998, -276)]),
        (5, "해지율(하락)", "9.16% 감소", [(-2994, 2994, -2114, -998)]),
        (6, "사업비(수준+인플레이션)", "수준 2.62% 증가 / 인플레이션 0.26%p", [(498, -498, -928, -194), (639, -639, -1191, -248)]),
    ],
}


def dump(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, indent=2).replace("\n", "\r\n").encode("utf-8")


def read_guarded(path: Path):
    raw = path.read_bytes()
    obj = json.loads(raw.decode("utf-8"))
    if dump(obj) != raw:
        raise SystemExit(f"{path.name}: bytes do not round-trip -- refusing")
    return raw, obj


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def write_atomic(path: Path, data: bytes):
    tmp = path.with_suffix(path.suffix + ".tmp_resweep")
    tmp.write_bytes(data)
    tmp.replace(path)


def build_amort(master):
    rows, held, checks = [], [], []
    for (code, q), spec in AMORT.items():
        tmpl = next(r for r in master if r["원보험사코드"] == code)
        n = len(next(iter(spec["rows"].values())))
        tot = [sum(v[i] for v in spec["rows"].values()) for i in range(n)]
        # only buckets up to 5~10 and the printed total are typed above (10~20, 20~30, 30+ not needed): check the printed total vs closing CSM
        if abs(tot[6] * spec["unit"] - spec["closing"]) > 0.05:
            raise SystemExit(f"{code} {q}: printed total {tot[6] * spec['unit']} != waterfall closing {spec['closing']}")
        for y in range(5):
            rows.append({"원보험사코드": code, "원수사명": tmpl["원수사명"], "티커": tmpl["티커"], "생손보여부": tmpl["생손보여부"],
                         "공시분기": q, "경과차년": y + 1, "상각액": round(tot[y] * spec["unit"], 5)})
        held.append({"master": "CSM_amortization", "code": code, "quarter": q, "cells": "경과차년 6-10",
                     "reason": "원문은 '5~10년' 한 구간으로만 인쇄(연도별 값 없음); 균등 배분·추정 금지",
                     "printed_5_to_10_eok": round(tot[5] * spec["unit"], 5), "printed_total_eok": round(tot[6] * spec["unit"], 5),
                     "source": f"data/disclosure/{spec['pdf']} p{spec['page']}"})
        checks.append({"code": code, "quarter": q, "y1_5_eok": [round(tot[y] * spec["unit"], 5) for y in range(5)],
                       "printed_total_eok": round(tot[6] * spec["unit"], 5), "closing_csm_waterfall": spec["closing"]})
    return rows, held, checks


def build_sens(master):
    tmpl = next(r for r in master if r["원보험사코드"] == "KR1104")
    out = []
    for no, risk, shock, parts in HANOVER_2023["rows"]:
        base = {"원보험사코드": "KR1104", "원수사명": tmpl["원수사명"], "티커": tmpl["티커"], "생손보여부": tmpl["생손보여부"],
                "공시분기": "2023.4Q", "기준일": "2023-12-31", "순번": no, "위험구분": risk, "충격수준": shock}
        common = "재보사 경영공시 FY2024 4-6-5 ①(2023 열, 백만원→억원 소수 2자리); 자본영향=당기손익+기타포괄손익(세전); 당기손익 정의에 CSM 상각 변동 포함(원문 주2)"
        if parts is None:
            out.append({**base, "CSM변동": None, "당기손익영향": None, "자본영향": None, "비고": common + "; 원문 공란/'-' (값 없음)"})
            continue
        fcf = sum(p[0] for p in parts)
        csm = sum(p[1] for p in parts)
        pl = sum(p[2] for p in parts)
        oci = sum(p[3] for p in parts)
        note = common + f"; 원문 이행현금흐름 변동 {fcf / 100:g}; 렌더링으로 부호 확인(이행현금흐름 + 보험계약마진 = 0)"
        if len(parts) > 1:
            note += "; 병합셀: 수준·인플레이션 합산 1행"
        out.append({**base, "CSM변동": round(csm / 100, 2), "당기손익영향": round(pl / 100, 2), "자본영향": round((pl + oci) / 100, 2), "비고": note})
    return out


def process(fname, key, staged, apply, revert, tag, report):
    path = ROOT / fname
    raw, rows = read_guarded(path)
    ex = {key(r): r for r in rows}
    new = [r for r in staged if key(r) not in ex]
    same = [r for r in staged if key(r) in ex and ex[key(r)] == r]
    coll = [key(r) for r in staged if key(r) in ex and ex[key(r)] != r]
    print(f"[{tag}] {fname}: existing {len(rows)} | staged {len(staged)} | new {len(new)} | already equal {len(same)} | collisions {len(coll)}")
    if coll:
        raise SystemExit(f"collisions with different values: {coll[:10]}")
    if revert:
        kk = {key(r): r for r in staged}
        keep = [r for r in rows if not (key(r) in kk and kk[key(r)] == r)]
        print(f"[{tag}] revert removes {len(rows) - len(keep)}")
        if apply:
            write_atomic(path, dump(keep))
        return
    if not apply:
        return
    BACKUP.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, BACKUP / f"{fname}.pre_rows_{tag}")
    if sha(path.read_bytes()) != sha(raw):
        raise SystemExit("master changed during planning -- rerun")
    write_atomic(path, dump(rows + new))
    raw2, rows2 = read_guarded(path)
    assert rows2[: len(rows)] == rows and rows2[len(rows):] == new
    print(f"[{tag}] WRITTEN {fname}: {len(rows)} -> {len(rows2)} (+{len(new)})")
    report[tag] = {"before": len(rows), "after": len(rows2), "added": len(new)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    a = ap.parse_args()
    _, am = read_guarded(ROOT / "CSM_amortization.json")
    _, se = read_guarded(ROOT / "CSM_sensitivity.json")
    arows, held, checks = build_amort(am)
    srows = build_sens(se)
    EV.mkdir(parents=True, exist_ok=True)
    (EV / "staged_amort_resweep.json").write_text(json.dumps({"rows": arows, "checks": checks}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    (EV / "staged_sens_resweep.json").write_text(json.dumps(srows, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    (EV / "held_amort_resweep.json").write_text(json.dumps(held, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps(checks, ensure_ascii=False))
    report = {}
    process("CSM_amortization.json", lambda r: (r["원보험사코드"], r["공시분기"], r["경과차년"]), arows, a.apply, a.revert, "amort", report)
    process("CSM_sensitivity.json", lambda r: (r["원보험사코드"], r["공시분기"], r["순번"]), srows, a.apply, a.revert, "sens", report)
    print(json.dumps(report, ensure_ascii=False))
    if not a.apply:
        print("(dry run)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
