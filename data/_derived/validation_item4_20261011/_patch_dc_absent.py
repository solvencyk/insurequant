p = "scripts/validate_data_contract.py"
raw = open(p, "rb").read()
nl = "\r\n" if b"\r\n" in raw else "\n"
s = raw.decode("utf-8").replace("\r\n", "\n")
print("newline", repr(nl))
def rep(old, new):
    global s
    assert s.count(old) == 1, old
    s = s.replace(old, new)

rep("    pl_key_items_for,\n)\nfrom solvency.validation.kics_json_rules import",
    "    pl_key_items_for,\n    pl_source_absent_for_coverage,\n)\nfrom solvency.validation.kics_json_rules import")

# Env: after the sensitivity-quarter block add source absent
rep('''        self.latest_kics_quarter = self._latest_quarter(self.kics_records)
        # sensitivity heatmap target''', '''        # PL 원천부재 등재(owner 2026-10-11, 하노버 2025.3Q): 재검산 결과를 한 번만 만든다. selftest(inject)는
        # 합성데이터 격리 -- 라이브 등재가 새지 않게 빈 결과가 기본이고, 주입하려면
        # inject["pl_source_absent"] = ({(원수사명, 분기): (kind, approved)}, [red dict]) 를 넣는다.
        if "pl_source_absent" in self.inject:
            self.pl_source_absent_names, self.pl_source_absent_red = self.inject["pl_source_absent"]
        elif self.inject:
            self.pl_source_absent_names, self.pl_source_absent_red = {}, []
        else:
            _nm, _ok, _red = pl_source_absent_for_coverage()
            self.pl_source_absent_names, self.pl_source_absent_red = _nm, _red
        self.latest_kics_quarter = self._latest_quarter(self.kics_records)
        # sensitivity heatmap target''')

old_1c = '''        real, _known, _struct = coverage_holes(idx, key_items, na_registry=na_reg,
                                               key_items_for=kif)
        for co, q, kind in real:
            if not _emit(q):
                continue
            res.add(check="census", severity="RED", master=master, company=co, quarter=q,
                    rule="MASTER_HOLE",
                    message=f"real hole (2024+): {kind} missing for active filer {co}")
'''
new_1c = '''        # PL 만 원천부재 등재(`_PL_SOURCE_ABSENT`)를 읽는다 -- 읽는 쪽(lookup 분기)이 이 호출이다. 재검산을 통과한
        # 「통째」 hole 만 빠지고 YELLOW 로 매 실행 인쇄된다. 깨진 등재는 hole 이 그대로 RED 이고 장치 RED 가 더해진다.
        absent_hit: list = []
        absent_kw = ({"source_absent": env.pl_source_absent_names, "absent_out": absent_hit}
                     if master == "PL_breakdown" else {})
        real, _known, _struct = coverage_holes(idx, key_items, na_registry=na_reg,
                                               key_items_for=kif, **absent_kw)
        for co, q, kind in real:
            if not _emit(q):
                continue
            res.add(check="census", severity="RED", master=master, company=co, quarter=q,
                    rule="MASTER_HOLE",
                    message=f"real hole (2024+): {kind} missing for active filer {co}")
        for co, q in absent_hit:
            kind_a, appr_a = env.pl_source_absent_names[(co, q)]
            res.add(check="census", severity="YELLOW", master=master, company=co, quarter=q,
                    rule="MASTER_HOLE_SOURCE_ABSENT",
                    message=f"원천부재 면제 [{kind_a}] ({appr_a}) -- {co} {q} PL 버킷 없음. 사이트 미게시 -- 마스터 버킷 부재 · "
                            f"raw 폴더 · 매니페스트 · 원장 마커 재검산 통과(통째 skip 아님, 매 실행 인쇄)")
        if master == "PL_breakdown":
            for f in env.pl_source_absent_red:
                res.add(check="census", severity="RED", master=master,
                        company=env.code_name.get(f["code"], f["code"]), quarter=f["quarter"],
                        rule=f["rule"],
                        message=f"PL 원천부재 면제 재검산 실패: {f['detail']}")
'''
rep(old_1c, new_1c)
if nl == "\r\n":
    s = s.replace("\n", "\r\n")
open(p, "wb").write(s.encode("utf-8"))
print("ok")
