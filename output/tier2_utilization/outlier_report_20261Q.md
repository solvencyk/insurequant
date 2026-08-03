# Tier-2 utilization outlier report (2026.1Q)

## Summary

| Metric | Count |
|--------|------:|
| Total companies | 39 |
| In range 0-100% | 34 |
| Outliers (<0, >100, null) | 5 |
| Missing (null) | 0 |

Valid 0-100% distribution: min=0.00%, median=15.62%, max=93.25%

## Spot-check (formula fix before/after)

| Code | Company | Before | After | Notes |
|------|---------|-------:|------:|-------|
| KR0068 | Hanwha Life | 73.07% | 71.01% | Unchanged (gross pre_limit) |
| KR0008 | Samsung Fire | -169.59% | 1.76% | pre_limit already netted lapse |
| KR0001 | Meritz Fire | -321.70% | 0.28% | post-transition residual pre_limit |

## Outliers

### KR0087 동양생명

- **utilization_pct**: 240.23%
- **numerator_eok**: 27537.0
- **tier2_limit_eok**: 11463.0
- **data_source**: proxy
- **quality_flag**: util_over_100
- **lapse_excess_eok**: None
- **hybrid_eok**: None
- **subordinated_eok**: None
- **tier2_eok / pre_limit_eok**: 27537.0 / None
- **proxy_utilization_pct**: 240.23
- **Interpretation**: Numerator exceeds SCRx50% limit — may reflect pre-clamp disclosure or proxy without exemption rows.

### KR0050 하나손해보험

- **utilization_pct**: 234.91%
- **numerator_eok**: 5434.06
- **tier2_limit_eok**: 2313.23
- **data_source**: table
- **quality_flag**: util_over_100
- **lapse_excess_eok**: None
- **hybrid_eok**: 0.0
- **subordinated_eok**: 0.0
- **tier2_eok / pre_limit_eok**: 5434.06 / None
- **proxy_utilization_pct**: 234.94
- **Interpretation**: Numerator exceeds SCRx50% limit — may reflect pre-clamp disclosure or proxy without exemption rows.

### KR0010 KB손해보험

- **utilization_pct**: 218.42%
- **numerator_eok**: 72777.0
- **tier2_limit_eok**: 33319.0
- **data_source**: proxy
- **quality_flag**: util_over_100
- **lapse_excess_eok**: None
- **hybrid_eok**: None
- **subordinated_eok**: None
- **tier2_eok / pre_limit_eok**: 72777.0 / None
- **proxy_utilization_pct**: 218.42
- **Interpretation**: Numerator exceeds SCRx50% limit — may reflect pre-clamp disclosure or proxy without exemption rows.

### KR0049 악사손해보험

- **utilization_pct**: 196.78%
- **numerator_eok**: 2633.88
- **tier2_limit_eok**: 1338.51
- **data_source**: table
- **quality_flag**: util_over_100
- **lapse_excess_eok**: None
- **hybrid_eok**: None
- **subordinated_eok**: None
- **tier2_eok / pre_limit_eok**: 2633.88 / None
- **proxy_utilization_pct**: 196.78
- **Interpretation**: Numerator exceeds SCRx50% limit — may reflect pre-clamp disclosure or proxy without exemption rows.

### KR0079 미래에셋생명보험

- **utilization_pct**: 126.45%
- **numerator_eok**: 14028.0
- **tier2_limit_eok**: 11093.5
- **data_source**: proxy
- **quality_flag**: util_over_100
- **lapse_excess_eok**: None
- **hybrid_eok**: None
- **subordinated_eok**: None
- **tier2_eok / pre_limit_eok**: 14028.0 / None
- **proxy_utilization_pct**: 126.45
- **Interpretation**: Numerator exceeds SCRx50% limit — may reflect pre-clamp disclosure or proxy without exemption rows.
