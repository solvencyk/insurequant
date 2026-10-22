# -*- coding: utf-8 -*-
import json
from pathlib import Path
ROOT = Path('C:/Users/sangwook.cho/Desktop/insurequant'); V = Path(__file__).parent
m = {(r['원보험사코드'], r['공시분기'], r['항목번호']): r for r in json.loads((ROOT/'PL_breakdown.json').read_text(encoding='utf-8'))}
g = json.loads((ROOT/'data/_gold/user_pl_cells.json').read_text(encoding='utf-8'))
out = []
bad = [c for c in g['null_dangi']['cells'] if m[(c[0], c[1], c[2])].get('값_당분기') is not None]
out.append(f'null_dangi cells {len(g["null_dangi"]["cells"])}; master 값_당분기 not null: {bad}')
bad2 = [c for c in g['set_dangi']['cells'] if m[(c[0], c[1], c[2])].get('값_당분기') is None or abs(m[(c[0], c[1], c[2])]['값_당분기'] - c[3]) > 1e-9]
out.append(f'set_dangi cells {len(g["set_dangi"]["cells"])}; master != registry value: {bad2}')
both = {tuple(c[:3]) for c in g['null_dangi']['cells']} & {tuple(c[:3]) for c in g['set_dangi']['cells']}
out.append(f'keys in both null_dangi and set_dangi (refused by builder): {both}')
# set cells (gold set): master 값 equals gold 값 for every entry
bad3 = [(e['원보험사코드'], e['공시분기'], e['항목번호'], e['값'], m[(e['원보험사코드'], e['공시분기'], e['항목번호'])]['값']) for e in g['set'] if m[(e['원보험사코드'], e['공시분기'], e['항목번호'])]['값'] != e['값'] and abs((m[(e['원보험사코드'], e['공시분기'], e['항목번호'])]['값'] or 0) - (e['값'] or 0)) > 1e-9]
out.append(f'gold set entries {len(g["set"])}; master 값 != gold 값: {len(bad3)} {bad3[:5]}')
(V/'v15_registry_effect.txt').write_text('\n'.join(out), encoding='utf-8'); print('\n'.join(out))
