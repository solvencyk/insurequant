# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

rep = json.load(open('artifacts/kics_validation/report_latest.json', encoding='utf-8'))
findings = rep['findings']

sel = [f for f in findings if f.get('원보험사코드') == 'KR0029' and f.get('공시분기') == '2025.3Q']
print('KR0029 2025.3Q findings count:', len(sel))
for f in sel:
    if f.get('status') in ('GREEN',) and f['rule'] not in ('2_tier1_bridge','2_tier1_bridge_post','3_tier2_composition','3_tier2_composition_post','47_tier2_census','47_tier2_census_post','48_tier2_limit','48_tier2_limit_post','50_tfi_tier_split','50_tfi_tier_split_post','51_tfi_tier2_composition','51_tfi_tier2_composition_post'):
        continue
    print('---')
    print(' rule   :', f['rule'])
    print(' status :', f['status'])
    print(' expected:', f.get('expected'))
    print(' actual  :', f.get('actual'))
    print(' diff    :', f.get('diff'))
    print(' detail  :', f.get('detail'))
