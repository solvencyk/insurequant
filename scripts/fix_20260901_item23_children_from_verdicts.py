# -*- coding: utf-8 -*-
"""item23 자식(24/25/26) 추출갭 일괄 반영 — 3개 서브에이전트 판정 파일 기반.

## 배경
`item23`(Ⅲ. 기타 요구자본 = 1+2+3)의 자식 행이 없으면 합계 룰이 **SKIP** 되어 게이트가
아예 못 본다(SKIP 버킷 345건 = 이 저장소의 'SKIP-on-missing = 검증무력화' 사각).
2026-09-01 에 세 그룹으로 나눠 원문 전수 대조했다:

    data/_derived/item23_children_audit/verdict_group1.json  현대해상·KB손해·신한이지 (72)
    data/_derived/item23_children_audit/verdict_group2.json  한화손해 등 10사        (40)
    data/_derived/item23_children_audit/verdict_group3.json  적용후 자식 통째결측    (93)

판정 205건 = EXTRACTION_GAP 106 · SOURCE_ABSENT 42 · POST_EQUALS_PRE_LEGIT 54 · UNMEASURED 3.
**이 스크립트는 EXTRACTION_GAP 만 반영한다.** 나머지는 값을 채우는 건이 아니라 등재 대상이다.

## 근본원인 (원문 확인)
  · 라벨 변형 `대용치`(≠대응치) — 업계 다수 표기, md_inbox 86개 파일
  · 라벨 공백 `요구 자본` / Docling 이 단어 중간에 끼우는 `요 구자본`
  · 값 셀이 대시(`-`)도 아닌 **완전 공백** (현대해상 12분기)
  · 셀 줄바꿈이 markdown 표 행으로 오분리 (농협생명·서울보증·KB라이프)
  · **PDF 폰트 결함** — 롯데손해 원문 임베드폰트가 '종' 글리프를 누락해 `종속회사`가 깨짐
  · 스캔 PDF 육안 판독 (KB손해 — 240dpi 렌더)

## 곁들여 고치는 것: KB손해보험 항목 뒤바뀜 4분기
2023.4Q·2024.1Q·2024.3Q·2024.4Q 는 원문이 item24=대시(0) / item25=값 인데 마스터가
**그 값을 item24 자리에 담고 item25 행은 아예 없다.** item23 == item24 로 산수가 우연히
맞아 게이트가 못 잡았고, 값이 있으니 결측 census 에도 안 걸린다. verdict 가 item25 를
채워 주므로 item24 를 0 으로 같이 내리지 않으면 합계가 2배가 된다.

실행:
    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/fix_20260901_item23_children_from_verdicts.py [--apply]
"""
from __future__ import annotations
import json, sys, shutil
from pathlib import Path
from datetime import datetime
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
MASTER = ROOT / "kics_disclosure.json"
AUDIT = ROOT / "data" / "_derived" / "item23_children_audit"

LABELS = {
    24: "1. 업권별 자본규제를 활용한 종속회사의 요구자본 환산치",
    25: "2. 비례성원칙을 적용한 종속회사의 요구자본 대응치",
    26: "3. 업권별 자본규제를 활용한 관계회사의 요구자본 환산치",
}
# KB손해 항목 뒤바뀜: item24 에 잘못 들어간 item25 값을 0 으로 내린다(원문 = 대시).
KB_SWAP = [("KR0010", q, 24, 0.0) for q in ("2023.4Q", "2024.1Q", "2024.3Q", "2024.4Q")]


def census(rows):
    combos = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])) for r in rows}
    filled = sum(1 for r in rows for f in ("값", "값_적용후") if r.get(f) is not None)
    return len(rows), len(combos), filled


def main() -> int:
    apply = "--apply" in sys.argv
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    b = census(rows)
    print(f"before: rows={b[0]} combos={b[1]} filled={b[2]}")

    recs = []
    for f in sorted(AUDIT.glob("verdict_group*.json")):
        recs += json.loads(f.read_text(encoding="utf-8"))
    print("판정 분포:", dict(Counter(r.get("verdict") for r in recs)))
    gaps = [r for r in recs if r.get("verdict") == "EXTRACTION_GAP"]

    idx = {}
    for r in rows:
        idx[(r["원보험사코드"], r["공시분기"], str(r["항목번호"]))] = r
    meta = {}
    for r in rows:
        meta.setdefault(r["원보험사코드"], (r["원수사명"], r.get("티커"), r["생손보여부"]))

    ins = upd = skip = 0
    touched = set()
    plan = []
    for g in gaps:
        code, q, it = g["code"], g["quarter"], int(g["item"])
        pre, post = g.get("value_pre"), g.get("value_post")
        if pre is None:
            skip += 1
            continue
        touched.add((code, q))
        row = idx.get((code, q, str(it)))
        plan.append((code, q, it, pre, post, "UPDATE" if row else "INSERT",
                     None if row is None else row.get("값")))
    for code, q, it, val in KB_SWAP:
        row = idx.get((code, q, str(it)))
        if row is None:
            print(f"  ABORT KB swap {code} {q} item{it}: 행이 없다"); return 2
        touched.add((code, q))
        plan.append((code, q, it, val, val, "SWAPFIX", row.get("값")))

    for code, q, it, pre, post, kind, cur in sorted(plan, key=lambda x: (x[0], x[1], x[2])):
        if kind != "UPDATE" or str(cur) != str(pre):
            print(f"  {kind:<8} {meta.get(code,(code,))[0]:<14} {q} item{it:<3} "
                  f"{str(cur):>10} -> {pre}")
        (ins := ins) if kind == "INSERT" else None
    ins = sum(1 for p in plan if p[5] == "INSERT")
    upd = sum(1 for p in plan if p[5] == "UPDATE")
    swp = sum(1 for p in plan if p[5] == "SWAPFIX")
    print(f"\nINSERT {ins} · UPDATE {upd} · SWAPFIX {swp} · value_pre 없음 skip {skip}")
    if not apply:
        print("(dry-run) 반영하려면 --apply"); return 0

    for code, q, it, pre, post, kind, _cur in plan:
        key = (code, q, str(it))
        row = idx.get(key)
        if row is None:
            nm, tk, seg = meta.get(code, (code, None, None))
            anchor = idx.get((code, q, str(23))) or idx.get((code, q, str(it - 1)))
            row = {"원보험사코드": code, "원수사명": nm, "티커": tk, "생손보여부": seg,
                   "항목번호": it, "항목명": LABELS[it], "공시분기": q,
                   "값": None, "값_적용후": None}
            pos = rows.index(anchor) + 1 if anchor is not None else len(rows)
            rows.insert(pos, row)
            idx[key] = row
        row["값"] = float(pre)
        if post is not None:
            row["값_적용후"] = float(post)

    a = census(rows)
    print(f"after : rows={a[0]} combos={a[1]} filled={a[2]}  (+{a[0]-b[0]}행 +{a[1]-b[1]}콤보 +{a[2]-b[2]}셀)")
    if a[0] - b[0] != ins or a[1] - b[1] != ins:
        print("  ABORT: 행/콤보 증가가 INSERT 수와 다르다"); return 2

    # 항등식 재검산 — 손댄 버킷 전부
    bad = []
    for code, q in sorted(touched):
        for fld, lab in (("값", "전"), ("값_적용후", "후")):
            p = idx.get((code, q, "23"))
            if p is None or p.get(fld) is None:
                continue
            ch = [idx.get((code, q, str(i))) for i in (24, 25, 26)]
            vals = [c.get(fld) for c in ch if c is not None and c.get(fld) is not None]
            if len(vals) != 3:
                continue
            if abs(sum(float(v) for v in vals) - float(p[fld])) > 0.01:
                bad.append((code, q, lab, float(p[fld]), sum(float(v) for v in vals)))
    print(f"\n항등식 재검산: 손댄 버킷 {len(touched)}개 · 안 닫힘 {len(bad)}건")
    for code, q, lab, pv, sv in bad[:20]:
        print(f"  {meta.get(code,(code,))[0]:<14} {q} [{lab}] item23={pv:,.1f} vs 자식합={sv:,.1f}")
    if bad:
        print("  ABORT: 항등식이 안 닫힌다. 저장하지 않는다."); return 2

    bak = MASTER.with_suffix(f".json.bak_{datetime.now():%Y%m%d_%H%M%S}_item23verdicts")
    shutil.copy2(MASTER, bak)
    MASTER.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n저장 완료. 백업: {bak.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
