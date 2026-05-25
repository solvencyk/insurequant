# Forward Confidence Troubleshooting (v3)

See scripts/forward_capital_simulation.py compute_confidence v3.

## v2 bug (fixed)
T2 used numerator_eok (limit residual) not subordinated_eok.

Meritz KR0001: bond 15910 vs numerator 99.8 = +15848% (false low).
After fix: bond 15910 vs subordinated 17989 = -11.6% (high).

## Real cases
KR0032 NH Sonhae: fsc_missing_t1, under_deduct.
KR0010 KB: FSC T2 8860 vs proxy BS 71809, under_deduct.
KR0003 Lotte: FSC T2 7200 vs sub 2137, over_deduct +237%.
