# -*- coding: utf-8 -*-
import sys, json
from pathlib import Path
ROOT = Path('C:/Users/sangwook.cho/Desktop/insurequant'); V = Path(__file__).parent
sys.path.insert(0, str(ROOT/'scripts'))
import validate_data_contract as G
env = G.Env()
out = []
for oid, gold_doc, src_rows, p, err in env.gold_overlays:
    rows = G.gold_overlay_census(oid, gold_doc.get('set', []), src_rows)
    masked = [r for r in rows if r['verdict'] in G._GOLD_MASKED]
    out.append(f'{oid}: src={p} n={len(rows)} masked={len(masked)} err={err}')
    if oid == 'PL':
        for r in masked:
            if r['gold'] is None or r['src'] is None or True:
                pass
        nn = [r for r in masked if not isinstance(r['gold'], (int, float)) or not isinstance(r['src'], (int, float))]
        out.append('  masked with None: %s' % [(r['key'], r['gold'], r['src'], r['verdict']) for r in nn])
        pins = env.gold_overlay_ledger.get('entries', {})
        out.append('  masked unpinned: %s' % [r['key'] for r in masked if r['key'] not in pins])
        out.append('  PL pins n=%d' % len([k for k in pins if k.startswith('PL|')]))
(V/'v9b_gate_census.txt').write_text('\n'.join(out), encoding='utf-8')
print('\n'.join(out))
