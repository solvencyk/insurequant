# -*- coding: utf-8 -*-
"""축 G(`53_tfi_memo_rows`) + 축 E 등식 승격 변이시험.

**갈래를 나눈 것이 검사가 아니라 면제가 되지 않았음을 실데이터로 증명한다.** 이 저장소가
두 달을 날린 false-green 의 정확한 형태가 "갈래를 늘려서 통과시키기" 였고,
`48_tier2_limit`(로더가 그 식으로 배율을 골라서 통과가 증거가 아니게 된 축)에서 한 번 더 봤다.

여기서 흔드는 것은 **합성 데이터가 아니라 라이브 마스터**다. 합성이면 "코드가 돈다" 만 보이고
"이 축이 실제 데이터에서 무언가를 잡는다" 는 안 보인다.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
MASTER = ROOT / "kics_disclosure.json"

PRE, POST = "값", "값_적용후"


@pytest.fixture(scope="module")
def rows():
    if not MASTER.exists():
        pytest.skip(f"master 없음: {MASTER}")
    return json.loads(MASTER.read_text(encoding="utf-8"))


def _findings(rows):
    from solvency.validation.kics_json_rules import run_validation
    from validate_kics_disclosure import _load_tfi_applicability
    return run_validation(rows, tfi_applicability=_load_tfi_applicability())["findings"]


def _status(findings, code, quarter, rule):
    for f in findings:
        if (f["원보험사코드"], f["공시분기"], f["rule"]) == (code, quarter, rule):
            return f["status"], f.get("detail", "")
    return None, ""


def _cell(rows, code, quarter, item, col):
    for r in rows:
        if (r.get("원보험사코드") == code and r.get("공시분기") == quarter
                and str(r.get("항목번호")) == str(item)):
            return r
    return None


def _mutate(rows, code, quarter, item, col, new):
    out = copy.deepcopy(rows)
    hit = 0
    for r in out:
        if (r.get("원보험사코드") == code and r.get("공시분기") == quarter
                and str(r.get("항목번호")) == str(item)):
            if new is None:
                r.pop(col, None)
            else:
                r[col] = new
            hit += 1
    assert hit, f"{code} {quarter} item{item}[{col}] 셀을 못 찾았다"
    return out


@pytest.fixture(scope="module")
def base(rows):
    return _findings(rows)


# ---------------------------------------------------------------------------
# 축 G — 세 검사가 각각 실제로 발화하나
# ---------------------------------------------------------------------------

def _a_green_memo_bucket(base, rows, col):
    """53/54 가 둘 다 실값(>0)이고 축 G 가 GREEN 인 대표 버킷 하나."""
    rule = "53_tfi_memo_rows" + ("_post" if col == POST else "")
    for f in base:
        if f["rule"] != rule or f["status"] != "GREEN":
            continue
        c, q = f["원보험사코드"], f["공시분기"]
        v53, v54 = _cell(rows, c, q, 53, col), _cell(rows, c, q, 54, col)
        if not v53 or not v54:
            continue
        try:
            if float(str(v53[col]).replace(",", "")) > 1 and float(str(v54[col]).replace(",", "")) > 1:
                return c, q, rule
        except (KeyError, ValueError, TypeError):
            continue
    pytest.skip(f"[{col}] 53/54 가 둘 다 실값인 GREEN 버킷이 없다")


def test_census_fires_when_a_memo_row_disappears(rows, base):
    """행이 사라지면 RED — 결측을 SKIP 으로 내리면 검증 무력화다."""
    c, q, rule = _a_green_memo_bucket(base, rows, PRE)
    after = _findings(_mutate(rows, c, q, 54, PRE, None))
    st, detail = _status(after, c, q, rule)
    assert st == "RED", f"{c} {q}: item54[{PRE}] 를 지웠는데 {st} 다 (detail={detail!r})"
    assert "TFI_MEMO_ROW_MISSING" in detail


def test_sign_check_fires(rows, base):
    """발행잔액이 음수가 되면 RED."""
    c, q, rule = _a_green_memo_bucket(base, rows, PRE)
    after = _findings(_mutate(rows, c, q, 53, PRE, "-1000.0"))
    st, detail = _status(after, c, q, rule)
    assert st == "RED", f"{c} {q}: item53 을 음수로 만들었는데 {st} 다"
    assert "TFI_MEMO_NEGATIVE" in detail


def test_containment_fires_in_both_columns(rows, base):
    """`53+54 ≤ item51` 이 **적용전·적용후 둘 다**에서 발화한다.

    적용후 census 를 안 걸었으므로, 적용후 미러가 실제로 도는지는 여기서 증명해야 한다 —
    안 그러면 '적용후도 본다' 는 선언이 말뿐이 된다."""
    for col in (PRE, POST):
        c, q, rule = _a_green_memo_bucket(base, rows, col)
        i51 = _cell(rows, c, q, 51, col)
        assert i51 is not None, f"{c} {q} item51[{col}] 이 없다"
        big = float(str(i51[col]).replace(",", "")) * 3 + 10_000.0
        after = _findings(_mutate(rows, c, q, 53, col, str(big)))
        st, detail = _status(after, c, q, rule)
        assert st == "RED", f"[{col}] {c} {q}: item53 을 item51 의 3배로 키웠는데 {st} 다"
        assert "TFI_MEMO_EXCEEDS_TIER2" in detail


def test_green_is_not_automatic(rows, base):
    """부모(item51)를 줄여도 GREEN 이면 그 통과는 검사가 아니라 자동통과다."""
    c, q, rule = _a_green_memo_bucket(base, rows, PRE)
    after = _findings(_mutate(rows, c, q, 51, PRE, "0.0"))
    st, _ = _status(after, c, q, rule)
    assert st == "RED", f"{c} {q}: item51 을 0 으로 만들었는데도 {st} 다 — 포함관계가 무검사다"


# ---------------------------------------------------------------------------
# 축 G — 두 SKIP 레지스트리가 **좁은가** (면제가 되지 않았나)
# ---------------------------------------------------------------------------

def test_blank_registry_only_covers_actually_missing_cells(rows):
    """`_TFI_MEMO_ISSUER_BLANK` 에 등재된 칸은 마스터에서 실제로 결측이어야 한다.

    값이 있는 칸을 등재해 두면 그 칸은 앞으로 어떤 검사도 안 받는다 — 등재가 곧 면제가 된다."""
    from solvency.validation import kics_json_rules as K
    filled = []
    for code, quarter, item in sorted(K._TFI_MEMO_ISSUER_BLANK):
        r = _cell(rows, code, quarter, item, PRE)
        if r is not None and r.get(PRE) not in (None, ""):
            filled.append((code, quarter, item, r.get(PRE)))
    assert not filled, (
        f"발행사 공란으로 등재됐는데 마스터에 값이 있다: {filled}. 등재는 '확인했다' 는 "
        "뜻이라 값이 있으면 등재가 거짓이고, 그 칸은 조용히 무검사가 된다.")


def test_not_scanned_registry_does_not_hide_readable_buckets(rows, base):
    """`_TFI_MEMO_TABLE_NOT_SCANNED` 등재분은 실제로 53/54 가 둘 다 없어야 한다."""
    from solvency.validation import kics_json_rules as K
    bad = []
    for code, quarter in sorted(K._TFI_MEMO_TABLE_NOT_SCANNED):
        have = [i for i in (53, 54)
                if (_cell(rows, code, quarter, i, PRE) or {}).get(PRE) not in (None, "")]
        if have:
            bad.append((code, quarter, have))
    assert not bad, (
        f"'스캐너가 못 읽었다' 로 등재됐는데 메모행이 실려 있다: {bad}. 백필이 끝났으면 "
        "레지스트리에서 지워라 — 안 지우면 그 버킷의 census 가 영구히 SKIP 이다.")


def test_both_skip_reasons_are_actually_used(base):
    """두 사유가 실데이터에서 실제로 발동하나 — 죽은 분기는 선언만 남은 것이다."""
    tags = [f.get("detail", "").split(":")[0] for f in base
            if f["rule"] == "53_tfi_memo_rows"]
    for tag in ("TFI_MEMO_ISSUER_BLANK", "TFI_MEMO_TABLE_NOT_SCANNED"):
        assert tag in tags, f"{tag} 분기가 실데이터에서 한 번도 안 쓰인다"


# ---------------------------------------------------------------------------
# 축 E — item52 등식 승격이 실제로 검사인가
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("col", [PRE, POST])
def test_axis_e_equation_uses_item52_in_both_columns(rows, base, col):
    """item52 를 흔들면 `50_tfi_tier_split{,_post}` 가 **양 컬럼 모두**에서 뒤집힌다.

    승격 전 적용후는 범위검사였고, item1 전==후 인 362칸에서는 범위가 한 점으로 붕괴해
    '등식과 같은 강도' 였지만 **나머지 69칸은 느슨했다.** 그 69칸이 등식이 됐는지 확인한다."""
    rule = "50_tfi_tier_split" + ("_post" if col == POST else "")
    target = None
    for f in base:
        if f["rule"] == rule and f["status"] == "GREEN" and "item52" in f.get("detail", ""):
            target = (f["원보험사코드"], f["공시분기"])
            break
    assert target, f"{rule} 이 item52 등식으로 통과하는 버킷이 없다 — 승격이 안 걸렸다"
    c, q = target
    r52 = _cell(rows, c, q, 52, col)
    assert r52 is not None and r52.get(col) not in (None, "")
    shaken = float(str(r52[col]).replace(",", "")) + 9_999.0
    after = _findings(_mutate(rows, c, q, 52, col, str(shaken)))
    st, _ = _status(after, c, q, rule)
    assert st == "RED", f"[{col}] {c} {q}: item52 를 9,999 흔들어도 {st} 다"


def test_axis_e_fallback_still_exists_for_missing_item52(rows, base):
    """item52 결측 버킷에서 폴백(적용전=item1 / 적용후=범위)이 살아 있고, **사유가 찍힌다.**

    폴백이 조용하면 item52 백필 발주가 사라진다.

    2026-08-25: 원래 이 테스트는 **라이브 마스터를 그대로** 스캔해서 폴백 사유가 자연히
    발생하는 버킷을 찾았다. parser 가 item52 를 30버킷 더 적재(428→458)하자 item50/51 이
    둘 다 있는 450버킷 **전부**가 item52 도 갖게 됐다 — 폴백에 도달하는 라이브 버킷이 0 이
    됐다(정상: 커버리지가 늘어난 결과이지 결함이 아니다). 그래서 자연발생 스캔은 이제 항상
    빈손이라 이 테스트가 늘 실패한다. **메커니즘 자체**(item52 가 미래에 다시 결측되는 회사가
    생기면 폴백이 조용하지 않다는 것)는 여전히 지켜야 하므로, 대표 버킷 하나의 item52 를
    **인위적으로 지워서** 폴백이 그 즉시 사유를 찍는지 직접 증명한다(다른 테스트들과 같은
    라이브-데이터 변이 관행, `_mutate(..., new=None)`)."""
    target = None
    for f in base:
        if f["rule"] == "50_tfi_tier_split" and "item52" in f.get("detail", ""):
            c, q = f["원보험사코드"], f["공시분기"]
            if (_cell(rows, c, q, 52, PRE) or {}).get(PRE) not in (None, "") and \
               (_cell(rows, c, q, 52, POST) or {}).get(POST) not in (None, ""):
                target = (c, q)
                break
    assert target, "item50+51 이 있고 item52 등식으로 검사되는 라이브 버킷이 없다 — 축 E 승격이 살아있는지부터 확인할 것"
    c, q = target
    mutated = _mutate(rows, c, q, 52, PRE, None)
    mutated = _mutate(mutated, c, q, 52, POST, None)
    after = _findings(mutated)
    for rule in ("50_tfi_tier_split", "50_tfi_tier_split_post"):
        st, detail = _status(after, c, q, rule)
        assert "TFI_TOTAL_ROW_ABSENT" in detail, (
            f"{rule} {c} {q}: item52 를 지웠는데 폴백 사유가 안 찍힌다(status={st}, "
            f"detail={detail!r}) — 어느 버킷이 약한 검사만 받았는지 게이트 출력만 보고 "
            "알 수 없게 된다")
