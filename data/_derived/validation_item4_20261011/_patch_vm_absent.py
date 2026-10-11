p = "scripts/validate_master_tables.py"
raw = open(p, "rb").read()
nl = "\r\n" if b"\r\n" in raw else "\n"
s = raw.decode("utf-8").replace("\r\n", "\n")

# 1) coverage_holes signature + docs + skip
old_sig = "def coverage_holes(idx, key_items, active_min=7, na_registry=None, key_items_for=None):"
new_sig = "def coverage_holes(idx, key_items, active_min=7, na_registry=None, key_items_for=None,\n                   source_absent=None, absent_out=None):"
assert s.count(old_sig) == 1
s = s.replace(old_sig, new_sig)

old_doc_end = "'부분' hole 로 드러난 것이 계기 -- 등재 없이 default(None)면 기존 동작과 완전히 같다.\"\"\""
assert s.count(old_doc_end) == 1
new_doc_end = '''\'부분' hole 로 드러난 것이 계기 -- 등재 없이 default(None)면 기존 동작과 완전히 같다.

    `source_absent` -- optional {(원수사명, 분기), ...}: **원천 부재로 재검산을 통과한** 칸
    (`pl_source_absent_for_coverage()` 의 산출, owner 승인 2026-10-11). 그 칸이 「통째」 hole 일 때만
    real/known 에서 빼고 `absent_out` 에 `(co, q)` 로 쌓는다 -- **이것이 등재부의 읽는 쪽(lookup 분기)** 이다.
    「부분」 hole 은 안 뺀다(버킷이 생겼다는 뜻이라 등재가 무효 -- 장치가 INERT RED 를 낸다).
    None 이면 종전과 바이트 동일.\"\"\"'''
s = s.replace(old_doc_end, new_doc_end)

old_loop = '''            vals = [m.get(k) for k in ks]
            if all(v is None for v in vals):
                kind = "통째"
'''
new_loop = '''            vals = [m.get(k) for k in ks]
            if all(v is None for v in vals):
                if source_absent and (co, q) in source_absent:
                    if absent_out is not None:
                        absent_out.append((co, q))
                    continue
                kind = "통째"
'''
assert s.count(old_loop) == 1
s = s.replace(old_loop, new_loop)

# 2) helper: pl_source_absent_for_coverage placed before coverage_holes
anchor = "def pl_key_items_for(source_ids: dict, key_items):"
helper = '''def pl_source_absent_for_coverage(pl_path=PL_PATH, registry=None, ledger=None, root=None):
    """PL 원천부재 등재부(`validate_kics_disclosure._PL_SOURCE_ABSENT`)를 재검산해
    -> (source_absent {(원수사명, 분기)}, ok {(코드, 분기): (kind, approved)}, red [dict]).

    `coverage_holes(source_absent=)` 에 넘기는 입력을 만든다. 재검산은 K-ICS census 원천부재 장치와
    **같은 함수**(`_census_source_absent`)다: 버킷이 여전히 PL 마스터에 없는가 · raw 폴더 박제 · 다운로더
    매니페스트 사유 · 근거 원장(registry `_PL_SOURCE_ABSENT`) VERIFIED + 인용 원천 재오픈. 하나라도 깨지면
    그 칸은 ok 에 안 들어가고(hole 이 그대로 남는다) red 가 같이 나온다. 마스터를 못 읽으면 면제 없음."""
    here = str(Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.insert(0, here)
    import validate_kics_disclosure as K  # noqa: PLC0415 -- 지연 import(순환 방지)
    reg = K._PL_SOURCE_ABSENT if registry is None else registry
    if not reg:
        return set(), {}, []
    try:
        rows = json.loads((ROOT / pl_path).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 -- 마스터를 못 읽으면 면제를 줄 수 없다(fail-closed)
        return set(), {}, []
    code_name: dict = {}
    present: set = set()
    for r in rows:
        c, q = r.get("원보험사코드"), r.get("공시분기")
        if c and r.get("원수사명"):
            code_name.setdefault(c, r["원수사명"])
        if c and q and r.get("값") is not None:
            present.add((c, q))
    ok, red = K.pl_source_absent_exemptions(present, code_name, registry=reg, ledger=ledger, root=root)
    return {(code_name.get(c, c), q) for c, q in ok}, ok, red


'''
assert s.count(anchor) == 1
s = s.replace(anchor, helper + anchor)

# 3) _check_coverage: use it
old_cov = '''    pl_holes, pl_known, pl_struct = coverage_holes(
        pl, pl_keys, na_registry=LOB_LEG_NA,
        key_items_for=pl_key_items_for(pl_src, pl_keys))
'''
new_cov = '''    # 원천부재 등재(owner 2026-10-11): 재검산을 통과한 칸만 「통째」 hole 에서 빠진다. 깨진 등재는 hole 이
    # 그대로 남고 아래 `ABSENT-RED` 행이 같이 나간다(= pl_holes 에 들어가 exit code 에 반영).
    pl_absent_names, pl_absent_ok, pl_absent_red = pl_source_absent_for_coverage()
    pl_absent_hit: list = []
    pl_holes, pl_known, pl_struct = coverage_holes(
        pl, pl_keys, na_registry=LOB_LEG_NA,
        key_items_for=pl_key_items_for(pl_src, pl_keys),
        source_absent=pl_absent_names, absent_out=pl_absent_hit)
    name_of = {}
    for (co_n, q_n) in pl_absent_names:
        name_of[co_n] = True
    pl_holes = list(pl_holes) + [(r["code"], r["quarter"], f"원천부재 등재 무효 {r['rule']}") for r in pl_absent_red]
    if absent_out is not None:
        absent_out.update({"ok": len(pl_absent_hit), "red": len(pl_absent_red), "registered": len(pl_absent_ok) + len(pl_absent_red)})
'''
assert s.count(old_cov) == 1
s = s.replace(old_cov, new_cov)
s = s.replace("def _check_coverage(wf: dict, pl: dict) -> tuple[list, list]:", "def _check_coverage(wf: dict, pl: dict, absent_out: dict | None = None) -> tuple[list, list]:")
old_pr = '''    for co, q, kind in pl_holes:
        print(f"  HOLE-PL  {co:14s} {q} ({kind})")
    print()
    return wf_holes, pl_holes
'''
new_pr = '''    for co, q, kind in pl_holes:
        print(f"  HOLE-PL  {co:14s} {q} ({kind})")
    print(f"   PL 원천부재 면제(통째 hole 에서 제외, 재검산 통과) {len(pl_absent_hit)}칸 -- **통과가 아니라 '원천이 없다'** 이고 건별로 인쇄한다")
    for co, q in pl_absent_hit:
        kind, approved = next((v for (c2, q2), v in pl_absent_ok.items() if q2 == q and (co == dict.get(dict(), c2, co) or True)), ("?", "?"))
        print(f"  ABSENT-PL {co:14s} {q} [{kind}] ({approved})")
    print()
    return wf_holes, pl_holes
'''
assert s.count(old_pr) == 1
s = s.replace(old_pr, new_pr)
if nl == "\r\n":
    s = s.replace("\n", "\r\n")
open(p, "wb").write(s.encode("utf-8"))
print("ok")
