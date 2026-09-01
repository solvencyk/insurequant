# -*- coding: utf-8 -*-
"""2026.2Q TFI(공통적용 경과조치) 표 결측 3사 — 삼성생명·현대해상·서울보증.

## 왜 지금 나왔나
`kics_transition_applicability.json` 사이드카가 `data/disclosure/FY*/raw/` 만 보고
`pdf/` 를 안 봐서 2026.2Q 적용여부를 UNKNOWN 으로 두고 있었다(이 저장소에서 최소 세 번째
같은 raw/pdf 축 버그). 사이드카가 되살아나자 `47_tier2_census` 가 즉시 세 회사를 잡았다 —
`TIER2_TABLE_ABSENT_BUT_TFI_APPLIED: 47/48/49 가 한 칸도 없다`.

**게이트가 옳았다.** 세 회사 다 MD 에 공통적용 경과조치 표가 멀쩡히 있는데 마스터에만
없었다. 삼성생명은 이번 라운드의 MD 재변환(`docling_parser` 키워드 누락 수정)으로 그 절이
비로소 MD 에 들어왔다 — 재변환 전 MD 에는 '경과조치' 가 2회(요약행)뿐이었고 지금은 17회다.

## 원문 (단위 백만원 → 억원 = /100)
  KR0069 삼성생명   parsed MD L437-455  47=11,852,822 48=31,117,555 49=7,440,493
  KR0009 현대해상   parsed MD (공통적용) 47=2,585,236  48=3,666,753  49=6,597,410
  KR0150 서울보증   parsed MD (공통적용) 47=4,315      48=717,249    49=0
세 회사 다 경과조치 전·후 컬럼이 **문자 그대로 동일**하다(적용 효과 0) → 값_적용후 미러링.
(기발행 신종자본증권)/(기발행 후순위채무) 는 적용전 0(또는 대시), 적용후 칸은 비어 있다.

## 검산 (셋 다 닫힌다)
  min(47,48) + 49 == item51(보완자본, TFI표) == item3(보완자본)
  item50 + item51 == item52 == item1(지급여력금액)
  item48 == item14 × 50%

실행:
    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/fix_20260901_tfi_table_2026q2_three.py [--apply]
"""
from __future__ import annotations
import json, sys, shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
MASTER = ROOT / "kics_disclosure.json"
Q = "2026.2Q"

LABELS = {
    47: "보완자본 한도 적용 전",
    48: "보완자본 한도",
    49: "해약환급금 부족분 상당액 중 해약환급금 상당액 초과분",
    50: "기본자본(TFI표, 공통적용경과조치)",
    51: "보완자본(TFI표, 공통적용경과조치)",
    52: "지급여력금액(TFI표, 공통적용경과조치)",
    53: "(기발행 신종자본증권)(TFI표, 공통적용경과조치)",
    54: "(기발행 후순위채무)(TFI표, 공통적용경과조치)",
}
# code -> {item: (값, 값_적용후)}   억원. 적용후 None = 원문 칸이 비어 있음.
DATA = {
    "KR0069": {47: (118528.22, 118528.22), 48: (311175.55, 311175.55),
               49: (74404.93, 74404.93), 50: (1102591.88, 1102591.88),
               51: (192933.15, 192933.15), 52: (1295525.03, 1295525.03),
               53: (0.0, None), 54: (0.0, None)},
    "KR0009": {47: (25852.36, 25852.36), 48: (36667.53, 36667.53),
               49: (65974.10, 65974.10), 50: (61458.05, 61458.05),
               51: (91826.46, 91826.46), 52: (153284.51, 153284.51),
               53: (0.0, None), 54: (0.0, None)},
    "KR0150": {47: (43.15, 43.15), 48: (7172.49, 7172.49),
               49: (0.0, 0.0), 50: (56245.00, 56245.00),
               51: (43.15, 43.15), 52: (56288.15, 56288.15),
               53: (0.0, None), 54: (0.0, None)},
}


def census(rows):
    combos = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])) for r in rows}
    filled = sum(1 for r in rows for f in ("값", "값_적용후") if r.get(f) is not None)
    return len(rows), len(combos), filled


def main() -> int:
    apply = "--apply" in sys.argv
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    b = census(rows)
    print(f"before: rows={b[0]} combos={b[1]} filled={b[2]}")
    idx = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])): r for r in rows}
    meta = {}
    for r in rows:
        meta.setdefault(r["원보험사코드"], (r["원수사명"], r.get("티커"), r["생손보여부"]))

    n_ins = n_upd = 0
    for code, items in DATA.items():
        nm = meta.get(code, (code,))[0]
        for it in sorted(items):
            cur = idx.get((code, Q, str(it)))
            if cur is None:
                n_ins += 1
                continue
            # 이미 있는 칸은 **헤드라인에서 온 정수 근사**일 수 있다(item52). TFI 표의
            # 소수 값으로 갱신하되, 1억을 넘게 벌어지면 다른 사고이므로 멈춘다.
            cv = cur.get("값")
            if cv is None or abs(float(cv) - items[it][0]) > 1.0:
                print(f"  ABORT {nm} item{it}: 기존값 {cv!r} 이 TFI 표값 {items[it][0]} 과 "
                      f"1억 넘게 다르다 — 손대지 않는다"); return 2
            print(f"  UPDATE {nm} item{it}: {cv} -> {items[it][0]} (TFI 표 정밀값)")
            n_upd += 1
        # 검산 (원문 값끼리)
        g = lambda i: items[i][0]
        chk = [("min(47,48)+49 == 51", min(g(47), g(48)) + g(49), g(51)),
               ("50+51 == 52", g(50) + g(51), g(52))]
        m14 = idx.get((code, Q, "14"))
        m3 = idx.get((code, Q, "3"))
        m1 = idx.get((code, Q, "1"))
        if m14 is not None:
            chk.append(("48 == item14x50%", g(48), float(m14["값"]) * 0.5))
        if m3 is not None:
            chk.append(("51 == item3(보완자본)", g(51), float(m3["값"])))
        if m1 is not None:
            chk.append(("52 == item1(지급여력금액)", g(52), float(m1["값"])))
        print(f"\n  {nm} ({code})")
        for lab, a, bb in chk:
            ok = "OK" if abs(a - bb) <= 1.0 else "*** 안 닫힘 ***"
            print(f"    {lab:<26} {a:>14,.2f} vs {bb:>14,.2f}  Δ{a-bb:>+8,.2f}  {ok}")
            if abs(a - bb) > 1.0:
                print("    ABORT: 검산 실패"); return 2

    print(f"\nINSERT {n_ins}칸")
    if not apply:
        print("(dry-run) 반영하려면 --apply"); return 0

    for code, items in DATA.items():
        nm, tk, seg = meta.get(code, (code, None, None))
        anchor = idx.get((code, Q, "46")) or idx.get((code, Q, "28"))
        pos = rows.index(anchor) + 1 if anchor is not None else len(rows)
        for it in sorted(items):
            pre, post = items[it]
            cur = idx.get((code, Q, str(it)))
            if cur is not None:
                cur["값"] = pre
                if post is not None:
                    cur["값_적용후"] = post
                continue
            row = {"원보험사코드": code, "원수사명": nm, "티커": tk, "생손보여부": seg,
                   "항목번호": it, "항목명": LABELS[it], "공시분기": Q,
                   "값": pre, "값_적용후": post}
            rows.insert(pos, row); pos += 1
            idx[(code, Q, str(it))] = row

    a = census(rows)
    print(f"after : rows={a[0]} combos={a[1]} filled={a[2]}  (+{a[0]-b[0]}행 +{a[2]-b[2]}셀)")
    if a[0] - b[0] != n_ins or a[1] - b[1] != n_ins:
        print("  ABORT: 행/콤보 증가가 예상과 다르다"); return 2

    bak = MASTER.with_suffix(f".json.bak_{datetime.now():%Y%m%d_%H%M%S}_tfi3")
    shutil.copy2(MASTER, bak)
    MASTER.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n저장 완료. 백업: {bak.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
