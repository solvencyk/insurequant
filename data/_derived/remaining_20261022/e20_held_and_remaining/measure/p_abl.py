"""p_abl: prototype of the PL4 (item 4/5/9/10) PRIOR-column reader for ABL (KR0070): production extract_tier2_abl reads nums[0] (당기) of the [구분|당기|전기] note;
the prior variant reads nums[1].  Compared with the CSM prior amortisation of the same filing.  READ-ONLY."""
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import prod as P  # noqa: E402
import mlib as M  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
C, T2 = P.C, P.T2
_norm, _row_nums, _label, _is_rollforward = T2._norm, T2._row_nums, T2._label, T2._is_rollforward


def abl_note(tables, idx):
    def find(cap_needs, cap_excl=()):
        needs = [c.replace(" ", "") for c in cap_needs]
        excl = [e.replace(" ", "") for e in cap_excl]
        for t in tables:
            if _is_rollforward(t):
                continue
            capf = _norm(t.caption or "").replace(" ", "")
            if all(n in capf for n in needs) and not any(e in capf for e in excl):
                return t
        return None

    def pick(t, *labels):
        if t is None:
            return None
        keys = [l.replace(" ", "") for l in labels]
        for r in t.rows:
            lab = _label(r).replace(" ", "")
            if any(k in lab for k in keys):
                nums = _row_nums(r)
                if len(nums) > idx:
                    return nums[idx]
        return None
    rev_t = find(["잔여보장", "회수", "보험수익"], cap_excl=("재보험",))
    re_t = find(["잔여보장", "회수", "재보험"])
    out = {}
    csm = pick(rev_t, "서비스의이전으로", "인식한 보험계약마진")
    ra = pick(rev_t, "비금융위험에 대한 위험조정")
    re_csm = pick(re_t, "서비스의이전으로", "인식한 보험계약마진")
    re_ra = pick(re_t, "비금융위험에 대한 위험조정")
    if csm is not None:
        out[4] = abs(csm)
    if ra is not None:
        out[5] = abs(ra)
    if re_csm is not None:
        out[9] = -abs(re_csm)
    if re_ra is not None:
        out[10] = -abs(re_ra)
    return out, (rev_t.line_no if rev_t is not None else None)


pl, names, inames = M.load_pl()
res, txt = {}, []
for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):
    tabs = P.tables_for("KR0070", M.later_fy(q))
    cur, lc = abl_note(tabs, 0)
    pri, lp = abl_note(tabs, 1)
    del tabs
    m = pl[("KR0070", q)]
    res[q] = {"later_current_col": cur, "later_prior_col": pri, "master": {str(k): m.get(k) for k in (4, 5, 9, 10)}, "note_table_line": lp}
    txt.append(f"{q}: later filing {M.later_fy(q)} note L{lp}: 당기col {cur} | 전기col {pri} | master 4/5/9/10 = {[m.get(k) for k in (4, 5, 9, 10)]}")
M.MEASURE.joinpath("p_abl.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
M.MEASURE.joinpath("p_abl.txt").write_text("\n".join(txt), encoding="utf-8")
print("\n".join(txt))
