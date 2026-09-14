# -*- coding: utf-8 -*-
"""A·B·C 3조의 손보 손해율 조사 결과를 **하나의 스키마**로 합친다.

왜 필요한가 (2026-09-14):
  3개 조를 병렬로 돌렸더니 연도 키를 제각각 썼다 — A·B 는 `"FY2025"`, C 는 `"2025"`,
  あいおい는 dict 가 아니라 float 하나, MS&AD 는 `"FY2025_jgaap"`/`"FY2025_ifrs_ref"`.
  그대로 두면 `row["loss_ratio_pct"]["FY2025"]` 로 읽는 다음 사람이 **10사를 조용히 놓친다**
  (실측: 정규화 전 19사만 잡혔고 정규화 후 29사). 발주 프롬프트에 키 형식을 안 박은 탓이다.

산출 `J-ESR/nonlife_ratio_census.json` 의 규칙:
  · 연도 키는 `FY20xx` 로 통일. dict 가 아닌 단일값은 FY2025 로 본다.
  · IFRS 참고치처럼 기준이 다른 값은 본값에서 빼고 `alt_values` 로 옮긴다.
  · `caveat` 는 **같은 열에 나란히 놓으면 안 되는 이유**를 적는다. 값을 고치지 않는다.
  · 검산 `合算率 == 損害率 + 事業費率`(±0.15) 을 전 연도에 돌려 결과를 박제한다.
"""
import io
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
GROUPS = ("A", "B", "C")
OUT = HERE / "nonlife_ratio_census.json"

#: 같은 열에 나란히 놓으면 안 되는 회사와 그 이유(원문 근거는 각 조 산출의 quote).
CAVEATS = {
    "トーア再保険": "正味損害率 산식이 正味支払保険金÷正味収入保険料 로 **損害調査費(LAE)를 분자에 안 더한다**. 다른 손보사는 전부 (正味支払保険金+損害調査費)÷正味収入保険料 라 이 회사만 과소 표시된다.",
    "ソニー損害保険": "**E.I.損害率**(경과보험료·발생손해액 기준)이지 正味損害率(수입보험료 기준)가 아니다. 범위도 地震保険・自賠責 제외.",
    "レスキュー損害保険": "이미지 스캔 PDF 라 자동 텍스트 추출이 실패했고(세로쓰기 표 헤더 파손) 렌더링 후 **육안 판독**한 값이다. 신뢰도가 다른 행과 같지 않다.",
    "MS&ADインシュアランスグループホールディングス": "「２社合計（単純合計）」 = 三井住友海上 + あいおいニッセイ同和 단순합산. 회사가 직접 공시한 표지만, 두 자회사를 따로 싣고 있으면 **중복 계상**이다.",
}


def norm_series(v):
    """연도 키가 제각각인 값을 {FY20xx: float} 로. 기준이 다른 값은 (본값, 대체값) 으로 가른다."""
    if v is None:
        return {}, {}
    if isinstance(v, (int, float)):
        return {"FY2025": float(v)}, {}
    if not isinstance(v, dict):
        return {}, {}
    main, alt = {}, {}
    for k, val in v.items():
        m = re.search(r"(20\d{2})", str(k))
        if not m:
            continue
        key = f"FY{m.group(1)}"
        try:
            f = float(val)
        except (TypeError, ValueError):
            continue
        # 기준이 다른 참고치(IFRS 등)는 본값 계열에 섞지 않는다.
        (alt if re.search(r"ifrs|ref|参考", str(k), re.I) else main)[key] = f
    return main, alt


def load_group(g):
    p = HERE / f"nonlife_ratio_census_{g}.json"
    d = json.load(io.open(p, encoding="utf-8"))
    return d.get("companies") or d.get("records") or []


def main():
    rows, checks, bad = [], 0, []
    for g in GROUPS:
        for c in load_group(g):
            nm = (c.get("company_jp") or "").strip()
            lr, lr_alt = norm_series(c.get("loss_ratio_pct"))
            er, er_alt = norm_series(c.get("expense_ratio_pct"))
            cr, cr_alt = norm_series(c.get("combined_ratio_pct"))
            for y in sorted(set(lr) & set(er) & set(cr)):
                checks += 1
                if abs(lr[y] + er[y] - cr[y]) > 0.15:
                    bad.append({"company_jp": nm, "fy": y,
                                "loss": lr[y], "expense": er[y], "combined": cr[y]})
            row = {
                "company_jp": nm,
                "company_en": c.get("company_en"),
                "group": g,
                "verdict": c.get("verdict"),
                "scope": c.get("scope"),
                "source_url": c.get("source_url"),
                "doc_type": c.get("doc_type"),
                "page": c.get("page"),
                "loss_ratio_pct": lr,
                "expense_ratio_pct": er,
                "combined_ratio_pct": cr,
                "combined_is_derived": c.get("combined_is_derived"),
                "quote": c.get("quote"),
            }
            alt = {k: v for k, v in (("loss_ratio_pct", lr_alt),
                                     ("expense_ratio_pct", er_alt),
                                     ("combined_ratio_pct", cr_alt)) if v}
            if alt:
                row["alt_values"] = alt
            if nm in CAVEATS:
                row["caveat"] = CAVEATS[nm]
            rows.append(row)

    from collections import Counter
    verdicts = dict(Counter(r["verdict"] for r in rows))
    fy25 = [r for r in rows if r["verdict"] == "found" and "FY2025" in r["loss_ratio_pct"]]
    out = {
        "_meta": {
            "purpose": "일본 손보사 正味損害率·正味事業費率·合算率 전수조사 (FY2025 우선, 없으면 FY2024)",
            "merged_from": [f"nonlife_ratio_census_{g}.json" for g in GROUPS],
            "year_key": "FY20xx 로 정규화됨 — 원본 3조는 키 형식이 서로 달랐다",
            "identity_check": {
                "rule": "合算率 == 正味損害率 + 正味事業費率 (±0.15)",
                "checked": checks,
                "mismatch": len(bad),
                "mismatches": bad,
            },
            "verdicts": verdicts,
            "fy2025_found": len(fy25),
            "caveat_companies": sorted(CAVEATS),
        },
        "rows": sorted(rows, key=lambda r: r["company_jp"]),
    }
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(f"wrote {OUT}")
    print(f"  verdicts: {verdicts}")
    print(f"  FY2025 found: {len(fy25)}사")
    print(f"  항등식 검산: {checks}건 중 불일치 {len(bad)}건")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
