p = "scripts/_data_contract_selftest.py"
raw = open(p, "rb").read()
nl = "\r\n" if b"\r\n" in raw else "\n"
s = raw.decode("utf-8").replace("\r\n", "\n")
def rep(old, new):
    global s
    assert s.count(old) == 1, old
    s = s.replace(old, new)

anchor = "# --- R1~R2: 17BS ↔ K-ICS 교차대조(2026-09-20 신설)의 변이 케이스"
fx = '''# --- Q10: PL 원천부재 등재(`_PL_SOURCE_ABSENT`, owner 2026-10-11)의 **읽는 쪽** 변이 케이스 -----------------
# 등재부만 쓰고 gate 가 읽지 않으면 다음 라운드에 샌다(feedback_ledger_needs_a_gate_reader). 이 케이스들이
# `check_census` 1c 가 주입된 재검산 결과를 실제로 읽는지 고정한다 -- 읽는 분기를 지우면 Q10b 가 깨진다.
_ABSENT_Q = "2025.3Q"


def _pl_hole_index():
    """active(>=7분기) 1사에서 2025.3Q 버킷만 통째로 없다 -- 계보는 전부 경영공시라 §2-1 항목만 기대한다."""
    pl = _pl_active_index()
    pl.pop(("KR9001", _ABSENT_Q))
    return pl


def _pl_hole_inject(**extra):
    from validate_master_tables import QS as MQS
    return base_inject(pl=_pl_hole_index(),
                       pl_source_ids={("KR9001", q): "DISCLOSURE" for q in MQS if q != _ABSENT_Q}, **extra)


def f_pl_hole_whole_bucket_is_red():
    """대조군: 등재가 없으면 통째 hole 은 종전대로 MASTER_HOLE RED."""
    return _pl_hole_inject()


def f_pl_hole_exempted_when_absent_verified():
    """재검산을 통과한 원천부재 칸은 MASTER_HOLE RED 가 아니라 YELLOW(MASTER_HOLE_SOURCE_ABSENT) 로 인쇄된다."""
    return _pl_hole_inject(pl_source_absent=({("KR9001", _ABSENT_Q): ("NOT_POSTED", "owner 2026-10-11")}, []))


def f_pl_hole_exemption_for_other_cell_does_not_cover():
    """등재 키가 다른 (회사,분기) 면 이 hole 은 안 가려진다 -- 키 특이성."""
    return _pl_hole_inject(pl_source_absent=({("KR9001", "2025.2Q"): ("NOT_POSTED", "owner 2026-10-11")}, []))


def f_pl_hole_broken_exemption_stays_red():
    """재검산이 깨진 등재(names 비어 있음 + 장치 RED)는 hole RED 가 그대로고 장치 RED 가 같이 뜬다."""
    return _pl_hole_inject(pl_source_absent=({}, [
        {"rule": "PL_SOURCE_ABSENT_LEDGER_DISAGREE", "code": "KR9001", "quarter": _ABSENT_Q,
         "detail": "근거 원장에 registry _PL_SOURCE_ABSENT 기록이 없다"}]))


def f_pl_partial_hole_is_not_exempted():
    """부분 hole(버킷은 있고 일부 항목만 결측)은 등재 키가 있어도 안 빠진다 -- 통째 hole 에만 적용."""
    pl = _pl_active_index()
    from validate_master_tables import QS as MQS
    pl[("KR9001", _ABSENT_Q)] = {"보험손익": 1000.0}          # 당기순이익 결측 = 부분
    return base_inject(pl=pl, pl_source_ids={("KR9001", q): "DISCLOSURE" for q in MQS},
                       pl_source_absent=({("KR9001", _ABSENT_Q): ("NOT_POSTED", "owner 2026-10-11")}, []))


'''
rep(anchor, fx + anchor)

anchor_c = '''    # R: 17BS ↔ K-ICS 교차대조 — 2026-09-20 배선분의 미배선 잔여(TODO_validation.md 박제) 해소.'''
cs = '''    # Q10: PL 원천부재 등재의 읽는 쪽(owner 2026-10-11) -- 양방향.
    ("Q10  PL 통째 hole 은 등재가 없으면 MASTER_HOLE RED", f_pl_hole_whole_bucket_is_red, {"MASTER_HOLE"}),
    ("Q10b 재검산 통과한 원천부재 칸은 RED 아님 (YELLOW 로 인쇄)", f_pl_hole_exempted_when_absent_verified,
     set(), {"MASTER_HOLE_SOURCE_ABSENT"}),
    ("Q10c 다른 칸의 등재로는 이 hole 이 안 가려진다", f_pl_hole_exemption_for_other_cell_does_not_cover,
     {"MASTER_HOLE"}),
    ("Q10d 깨진 등재는 hole RED 유지 + 장치 RED", f_pl_hole_broken_exemption_stays_red,
     {"MASTER_HOLE", "PL_SOURCE_ABSENT_LEDGER_DISAGREE"}),
    ("Q10e 부분 hole 은 등재 키가 있어도 안 빠진다", f_pl_partial_hole_is_not_exempted, {"MASTER_HOLE"}),
'''
rep(anchor_c, cs + anchor_c)
if nl == "\r\n":
    s = s.replace("\n", "\r\n")
open(p, "wb").write(s.encode("utf-8"))
print("ok")
