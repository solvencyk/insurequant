# Tier-2 utilization outlier report (2025.4Q)

## Summary

| Metric | Count |
|--------|------:|
| Total companies | 38 |
| In range 0-100% | 34 |
| Outliers (<0, >100, null) | 4 |
| Missing (null) | 1 |

Valid 0-100% distribution: min=0.00%, median=24.38%, max=98.48%

## Spot-check (formula fix before/after)

| Code | Company | Before | After | Notes |
|------|---------|-------:|------:|-------|
| KR0068 | Hanwha Life | 73.07% | 73.07% | Unchanged (gross pre_limit) |
| KR0008 | Samsung Fire | -169.59% | 7.35% | pre_limit already netted lapse |
| KR0001 | Meritz Fire | -321.70% | 0.36% | post-transition residual pre_limit |

## Outliers

### KR0010 KB손해보험

- **utilization_pct**: 225.65%
- **numerator_eok**: 71809.0
- **tier2_limit_eok**: 31823.0
- **data_source**: proxy
- **quality_flag**: util_over_100
- **lapse_excess_eok**: None
- **hybrid_eok**: None
- **subordinated_eok**: None
- **tier2_eok / pre_limit_eok**: 71809.0 / None
- **proxy_utilization_pct**: 225.65
- **Interpretation**: Numerator exceeds SCRx50% limit — may reflect pre-clamp disclosure or proxy without exemption rows.

### KR0079 미래에셋생명

- **utilization_pct**: 124.77%
- **numerator_eok**: 13072.0
- **tier2_limit_eok**: 10477.0
- **data_source**: proxy
- **quality_flag**: util_over_100
- **lapse_excess_eok**: None
- **hybrid_eok**: None
- **subordinated_eok**: None
- **tier2_eok / pre_limit_eok**: 13072.0 / None
- **proxy_utilization_pct**: 124.77
- **Interpretation**: Numerator exceeds SCRx50% limit — may reflect pre-clamp disclosure or proxy without exemption rows.

### KR0087 동양생명

- **utilization_pct**: 108.30%
- **numerator_eok**: 12223.25
- **tier2_limit_eok**: 11286.49
- **data_source**: table
- **quality_flag**: util_over_100
- **lapse_excess_eok**: 15607.77
- **hybrid_eok**: 0.0
- **subordinated_eok**: 0.0
- **tier2_eok / pre_limit_eok**: 26894.26 / 12223.25
- **proxy_utilization_pct**: 100.0
- **Interpretation**: Numerator exceeds SCRx50% limit — may reflect pre-clamp disclosure or proxy without exemption rows.

### KR0080 에이아이에이생명보험

- **utilization_pct**: null
- **numerator_eok**: None
- **tier2_limit_eok**: None
- **data_source**: missing
- **quality_flag**: missing
- **lapse_excess_eok**: None
- **hybrid_eok**: None
- **subordinated_eok**: None
- **tier2_eok / pre_limit_eok**: None / None
- **proxy_utilization_pct**: None
- **Interpretation**: No MD table and no JSON proxy items 3/14.
