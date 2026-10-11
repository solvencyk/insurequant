# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/scripts"); sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/src")
import _data_contract_selftest as ST, validate_data_contract as g
res = g.run_gate(g.Env(inject=ST.f_pl_rein_published_block_missing_from_sidecar()))
for f in res.red: print(f.rule, f.company, f.quarter, f.message[:150])
