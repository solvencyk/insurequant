# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("scripts/validate_master_tables.py")
s = p.read_text(encoding="utf-8")
assert not s.startswith("\ufeff")

# 1) header comment + prior-vintage helper
old1 = '''def _check_tax22_crosscheck(rows: list | None = None,
                            quiet: bool = False) -> tuple[int, list, dict]:
    """item22 vs (item24 + 원천 법인세). Returns (pass, fail_rows, skip_counts).
'''
new1 = '''def _tax22_prior_tier1(fdf, cc: str, quarter: str):
    """**최신 비교열 판**: 다음 해 같은 기간 FS-API 캐시의 전기 열(frmtrm_*)을 빌더와 **같은 함수**
    (`fetch_dart_fs._parse`)로 읽는다 (2026-10-22 신설).

    왜. 발행사가 이후 공시에서 전기 숫자를 소급재작성하면(교보생명 2023.3Q~2024.2Q 의 CSM 상각
    시간가치 오류 정정, 법인세 205,722 -> 255,935백만 등) 마스터가 최신 비교열 판으로 갱신되고,
    같은 분기 원공시 캐시(thstrm_*)와는 달라진다. 규칙은 원공시 판 **또는** 최신 비교열 판
    둘 중 하나와 일치하면 통과로 본다. 둘 다와 어긋나면 그대로 FAIL 이다.

    매핑은 `_parse` 가 읽는 칸(thstrm_amount · thstrm_add_amount)에 전기 칸을 얹는 것뿐이라 계정
    선택 로직을 재구현하지 않는다. 연차(4Q)는 frmtrm_amount, 분기는 누계 frmtrm_add_amount.
    """
    reprt = fdf.REPRT.get(quarter[5:])
    if not reprt:
        return None
    annual = quarter[5:] == "4Q"
    nxt = str(int(quarter[:4]) + 1)
    for fs_div in ("OFS", "CFS"):
        p = ROOT / TAX22_CACHE_DIR / f"{cc}_{nxt}_{reprt}_{fs_div}.json"
        if not p.exists():
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            for a in d.get("list", []) or []:
                if annual:
                    a["thstrm_amount"], a["thstrm_add_amount"] = a.get("frmtrm_amount"), ""
                else:
                    a["thstrm_amount"] = a.get("frmtrm_q_amount")
                    a["thstrm_add_amount"] = a.get("frmtrm_add_amount")
            t1 = fdf._parse(d, annual)
        except Exception:
            t1 = None
        if t1:
            return t1
    return None


def _check_tax22_crosscheck(rows: list | None = None,
                            quiet: bool = False) -> tuple[int, list, dict]:
    """item22 vs (item24 + 원천 법인세). Returns (pass, fail_rows, skip_counts).

    원천 법인세는 두 판 중 하나와 일치하면 통과다: 같은 분기 원공시 캐시 **또는** 다음 해 같은
    기간 캐시의 전기 열(최신 비교열, `_tax22_prior_tier1`). fail_rows 의 8번째 값은 최신 비교열 판
    |법인세|(없으면 None)다.
'''
assert s.count(old1) == 1
s = s.replace(old1, new1)

old2 = '''        if abs(rhs - lhs) > tol:
            fails.append((co, q, round(m22, 1), round(lhs, 1), round(rhs, 1),
                          round(rhs - lhs, 1), round(tol, 1)))
        else:
            n_pass += 1
'''
new2 = '''        if abs(rhs - lhs) <= tol:
            n_pass += 1
            continue
        rhs_prior = None
        t1p = _tax22_prior_tier1(fdf, cc, q)
        if t1p and t1p.get(23) is not None:
            rhs_prior = abs(t1p[23])
            if abs(rhs_prior - lhs) <= tol:
                n_pass += 1
                n_prior += 1
                continue
        fails.append((co, q, round(m22, 1), round(lhs, 1), round(rhs, 1),
                      round(rhs - lhs, 1), round(tol, 1),
                      None if rhs_prior is None else round(rhs_prior, 1)))
'''
assert s.count(old2) == 1
s = s.replace(old2, new2)

old3 = '''    n_pass = 0
    try:
        sys.path.insert(0, str(ROOT))
        import fetch_dart_fs as fdf'''
new3 = '''    n_pass = n_prior = 0
    try:
        sys.path.insert(0, str(ROOT))
        import fetch_dart_fs as fdf'''
assert s.count(old3) == 1
s = s.replace(old3, new3)

old4 = '''              f"pass={n_pass} fail={len(fails)} skip={sum(skips.values())}")
'''
new4 = '''              f"pass={n_pass}(그중 최신 비교열 판으로만 통과 {n_prior}) fail={len(fails)} "
              f"skip={sum(skips.values())}")
'''
assert s.count(old4) == 1
s = s.replace(old4, new4)

old5 = '''        for co, q, m22, lhs, rhs, d, tol in fails[:40]:
            print(f"  FAIL {co:14s} {q}  22={m22:>+14,.1f}  |22-24|={lhs:>13,.1f}  "
                  f"|원천세|={rhs:>13,.1f}  diff={d:>+12,.1f}  tol={tol:,.1f}")'''
new5 = '''        for co, q, m22, lhs, rhs, d, tol, rhs_p in fails[:40]:
            alt = "없음" if rhs_p is None else f"{rhs_p:,.1f}"
            print(f"  FAIL {co:14s} {q}  22={m22:>+14,.1f}  |22-24|={lhs:>13,.1f}  "
                  f"|원천세|={rhs:>13,.1f}  diff={d:>+12,.1f}  tol={tol:,.1f}  "
                  f"|최신 비교열 세|={alt}")'''
assert s.count(old5) == 1
s = s.replace(old5, new5)
p.write_text(s, encoding="utf-8", newline="")
print("ok")
