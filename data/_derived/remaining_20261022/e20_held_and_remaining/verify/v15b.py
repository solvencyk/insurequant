# -*- coding: utf-8 -*-
import json
from pathlib import Path
V = Path(__file__).parent
m = {(r['원보험사코드'], r['공시분기'], r['항목번호']): r for r in json.loads((V/'head_files'/'PL_breakdown.json').read_text(encoding='utf-8'))}
g = json.loads((V/'head_files'/'user_pl_cells.json').read_text(encoding='utf-8'))
bad = [(e['원보험사코드'], e['공시분기'], e['항목번호'], e['값'], m[(e['원보험사코드'], e['공시분기'], e['항목번호'])]['값']) for e in g['set'] if abs((m[(e['원보험사코드'], e['공시분기'], e['항목번호'])]['값'] or 0) - (e['값'] or 0)) > 1e-9]
print('HEAD: gold vs master mismatches', len(bad), bad)
