export const meta = {
  name: 'recover-market-subrisks-v2',
  description: 'Extract K-ICS 시장위험 sub-risks 36-40 + IRR 41-46 from an explicit per-cell source (localized page OR full parsed MD), sqrt-reconcile gate, adversarial re-read on miss',
  phases: [
    { title: 'Extract', detail: 'one agent per (co,quarter) reads its resolved source file' },
    { title: 'Verify', detail: 'reconcile vs item19; re-read on near-miss' },
  ],
}

// --- reconcile (JS port of fill_market_subitems_to_disclosure.mkt_est / derive_irr)
const M = [[1,.25,.25,.25,0],[.25,1,.25,-.25,0],[.25,.25,1,.25,0],[.25,-.25,.25,1,0],[0,0,0,0,1]]
function mktEst(v) { let q = 0; for (let a=0;a<5;a++) for (let b=0;b<5;b++) q += v[a]*M[a][b]*v[b]; return q>0?Math.sqrt(q):0 }
function deriveIrr(b,mr,up,dn,fl,st) {
  const Rmr=b-mr, Rup=Math.max(b-up,0), Rdn=Math.max(b-dn,0), Rfl=Math.max(b-fl,0), Rst=Math.max(b-st,0)
  return Math.sqrt(Math.max(Rup,Rdn)**2 + Math.max(Rfl,Rst)**2) + Rmr
}
const num = (x) => (typeof x === 'number' && isFinite(x)) ? x : null

const SUB_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    found: {
      type: 'object', additionalProperties: false,
      description: '시장위험 sub-risk amounts in 백만원 (million KRW) as printed; null if not found',
      properties: {
        '36': { type: ['number','null'], description: '금리위험액 (interest-rate risk)' },
        '37': { type: ['number','null'], description: '주식위험액 (equity)' },
        '38': { type: ['number','null'], description: '부동산위험액 (property)' },
        '39': { type: ['number','null'], description: '외환위험액 (FX)' },
        '40': { type: ['number','null'], description: '자산집중위험액 (asset concentration)' },
      },
      required: ['36','37','38','39','40'],
    },
    irr: {
      type: 'object', additionalProperties: false,
      description: '금리위험액 현황 순자산가치 6 scenarios 백만원; null each if no IRR table',
      properties: {
        '41': { type: ['number','null'], description: '충격전 base' },
        '42': { type: ['number','null'], description: '평균회귀' },
        '43': { type: ['number','null'], description: '금리상승' },
        '44': { type: ['number','null'], description: '금리하락' },
        '45': { type: ['number','null'], description: '금리평탄' },
        '46': { type: ['number','null'], description: '금리경사' },
      },
      required: ['41','42','43','44','45','46'],
    },
    evidence: { type: 'string', description: 'exact source line quoted for each non-null value' },
    period_basis: { type: 'string', description: 'which column/period used (e.g. 당기 2025.4Q 적용후)' },
    notes: { type: 'string' },
  },
  required: ['found','irr','evidence','period_basis','notes'],
}

function extractPrompt(it, feedback) {
  return [
    `You are extracting K-ICS 시장위험액 (market risk) sub-risk amounts for ${it.name} (${it.code}) ${it.quarter}.`,
    `Read this file with the Read tool. It is EITHER a localized market-risk page bundle OR the FULL parsed disclosure MD (which may show several comparison periods side by side):`,
    `  ${it.file}`,
    ``,
    `If the file covers multiple periods/columns, FIND AND USE THE COLUMN FOR ${it.quarter} (당기/most-recent of the filing). If 경과조치 적용전/적용후 both appear use 적용후. If 표준모형 vs 내부모형(internal model) both appear use 표준(standard) K-ICS.`,
    `All values are in 백만원 (million KRW) EXACTLY AS PRINTED — do not rescale, do not strip digits:`,
    `  36 금리위험액   37 주식위험액   38 부동산위험액   39 외환위험액   40 자산집중위험액`,
    ``,
    `Each sub-risk usually has its OWN '현황' section (②금리위험액 현황, ③주식위험액 현황, …). The 위험액 is the RISK AMOUNT — NOT 익스포져(exposure), NOT 충격전 공정가치/평가금액/측정대상자산(pre-shock value), NOT a 위험계수(coefficient). It is the labeled '○○위험액' figure.`,
    `Smaller P&C filings instead have ONE table with rows 금리위험/주식위험/부동산위험/외환위험/자산집중위험 — use those. A sub-risk that is genuinely 0 / '-' / absent for a small insurer is null.`,
    ``,
    `Also, IF a 금리위험액 현황 table shows a 순자산가치 (net asset value) row of 6 scenario figures, return them in order: 41 충격전(base) 42 평균회귀 43 금리상승 44 금리하락 45 금리평탄 46 금리경사. Else all null.`,
    ``,
    `RULES: return null for anything you cannot find with confidence — NEVER guess or fabricate. '-'/'해당없음'/absent → null. Quote each value's source line in evidence.`,
    ``,
    `Sanity check (do NOT back-solve): item19 시장위험액 (parent) for this cell = ${it.item19_eok} 억원 ≈ ${Math.round(it.item19_eok*100)} 백만원. Your 5 sub-risks combine by a correlation formula to roughly this. Report PRINTED values only.`,
    feedback ? `\n⚠️ RE-READ: ${feedback}` : '',
  ].join('\n')
}

function reconcile(found, item19_eok) {
  const v = [36,37,38,39,40].map(i => num(found[String(i)]))
  const nonNull = v.filter(x => x !== null).length
  const v5 = v.map(x => x === null ? 0 : x)
  const est = mktEst(v5)            // 백만원
  const target = item19_eok * 100   // 억원 -> 백만원
  const rel = target > 0 ? Math.abs(est - target) / target * 100 : 999
  return { nonNull, est, target, rel, v }
}

// args = [[code, quarter, item19_eok, name, file], ...]
const rawArgs = typeof args === 'string' ? JSON.parse(args) : (args || [])
const items = rawArgs.map(([code, quarter, item19_eok, name, file]) => ({
  code, quarter, item19_eok, name,
  file: file || `artifacts/kics_validation/market_pages/${code}_${quarter}.md`,
  even: quarter.endsWith('2Q') || quarter.endsWith('4Q'),
}))
phase('Extract')

const results = await pipeline(items,
  (it) => agent(extractPrompt(it), { label: `mkt:${it.code}_${it.quarter}`, phase: 'Extract', schema: SUB_SCHEMA })
            .then(r => ({ it, r })),
  async ({ it, r }) => {
    if (!r) return { ...it, status: 'NULL' }
    let rc = reconcile(r.found, it.item19_eok)
    let used = r
    if (!(rc.nonNull >= 4 && rc.rel < 2) && rc.nonNull >= 2) {
      const fb = `Your values ${JSON.stringify(used.found)} give 시장위험액 ≈ ${Math.round(rc.est)} 백만원 but the disclosed parent is ${Math.round(rc.target)} 백만원 (off ${rc.rel.toFixed(1)}%). Likely one number is an 익스포져/충격전/coefficient instead of the 위험액, or a wrong period/적용전. Re-read ${it.file} and correct ALL five; keep ones you are sure of.`
      const r2 = await agent(extractPrompt(it, fb), { label: `mkt2:${it.code}_${it.quarter}`, phase: 'Verify', schema: SUB_SCHEMA })
      if (r2) {
        const rc2 = reconcile(r2.found, it.item19_eok)
        if ((rc2.nonNull >= 4 && rc2.rel < 2) || (rc2.nonNull > rc.nonNull)) { used = r2; rc = rc2 }
      }
    }
    let irrStatus = 'none', irrVals = null
    const iv = [41,42,43,44,45,46].map(i => num(used.irr[String(i)]))
    if (iv.every(x => x !== null)) {
      const der = deriveIrr(iv[0],iv[1],iv[2],iv[3],iv[4],iv[5])
      const i36 = num(used.found['36'])
      const relIrr = i36 ? Math.abs(der - i36) / i36 * 100 : 999
      if (relIrr < 5) { irrStatus = 'ok'; irrVals = iv }
      else irrStatus = `norc(${relIrr.toFixed(0)}%)`
    }
    let status
    if (rc.nonNull >= 4 && rc.rel < 2) status = 'RECOVERED'
    else if (rc.nonNull === 0) status = 'AGGREGATE'
    else if (rc.nonNull === 1 && used.found['36'] != null) status = 'G36_ONLY'
    else status = `PARTIAL(${rc.nonNull},${rc.rel.toFixed(0)}%)`
    return {
      code: it.code, quarter: it.quarter, name: it.name, status,
      item19_eok: it.item19_eok, rel: Number(rc.rel.toFixed(2)), nonNull: rc.nonNull,
      found: used.found, irrStatus, irr: irrVals,
      evidence: used.evidence, period_basis: used.period_basis,
    }
  }
)

const ok = results.filter(Boolean)
const by = {}
for (const r of ok) { const k = (r.status||'NULL').split('(')[0]; by[k] = (by[k]||0)+1 }
log(`done: ${ok.length} cells — ${Object.entries(by).map(([k,v])=>`${k}:${v}`).join(' ')}`)
return ok
