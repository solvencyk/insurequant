/* e3: browser-side screen audit of K-ICS.html (utilization donuts, number lines, Forward Outlook, issuance bars + 2 big cells).
 * Written independently of the page code.  The expected values come from e2_expected_<rev>.json (served from the same local site folder),
 * which e2_expected.py built from the pinned published JSON + my own recompute + the timeline JSON.
 * Usage in the browser pane (page opened with ?iq_internal=1):
 *     eval(await (await fetch('e3_screen_audit.js')).text());
 *     const res = await AUD(['KR0068','KR0001', ...]);        // returns [{code,name,miss:[...],shown:{...}}]
 * It selects each company through the page's own <select id="company"> change handler, then reads DOM/Chart values.
 */
(function () {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const norm = (s) => String(s == null ? '' : s).replace(/ /g, ' ').replace(/\s+/g, ' ').trim();
  const near = (a, b, tol) => (a == null && b == null) || (a != null && b != null && Math.abs(a - b) <= tol);
  const fmtSigned = (v) => (v < 0 ? '△' : '') + Math.abs(v).toFixed(2) + '%';

  async function loadExp() {
    if (!window.__EXP) {
      const names = ['e2_expected_dbbffcb5.json'];
      window.__EXP = await (await fetch(names[0])).json();
    }
    return window.__EXP;
  }

  async function auditOne(EXP, code) {
    const e = EXP[code];
    const r = { code, name: e.name, miss: [], shown: {} };
    const sel = document.getElementById('company');
    sel.value = e.name;
    if (sel.value !== e.name) { r.miss.push('company not selectable: ' + e.name); return r; }
    sel.dispatchEvent(new Event('change', { bubbles: true }));
    await sleep(750);
    const g = (id) => document.getElementById(id);

    // ---- donuts
    const a1 = g('donut-tier1').getAttribute('aria-label');
    const a2 = g('donut-tier2').getAttribute('aria-label');
    r.shown.aria1 = a1; r.shown.aria2 = a2;
    if (a1 !== e.t1.aria) r.miss.push('tier1 aria: shown "' + a1 + '" expected "' + e.t1.aria + '"');
    if (a2 !== e.t2.aria) r.miss.push('tier2 aria: shown "' + a2 + '" expected "' + e.t2.aria + '"');
    const c1 = Chart.getChart('donut-tier1'), c2 = Chart.getChart('donut-tier2');
    const d1 = c1 ? c1.data.datasets[0].data : null, d2 = c2 ? c2.data.datasets[0].data : null;
    r.shown.arc1 = d1; r.shown.arc2 = d2;
    const fill = (p) => (p == null ? 0 : Math.min(Math.max(p, 0), 100));
    if (!d1 || !near(d1[0], fill(e.t1.pct), 0.011)) r.miss.push('tier1 arc ' + JSON.stringify(d1) + ' expected fill ' + fill(e.t1.pct));
    if (!d2 || !near(d2[0], fill(e.t2.pct), 0.011)) r.miss.push('tier2 arc ' + JSON.stringify(d2) + ' expected fill ' + fill(e.t2.pct));
    // my independent recompute must equal the percentage the donut shows (tolerance 0.1%p)
    if (e.t1.pct_mine != null && !near(e.t1.pct_mine, e.t1.pct, 0.12)) r.miss.push('JSON tier1 ' + e.t1.pct + ' vs independent ' + e.t1.pct_mine);
    if (e.t2.pct_mine != null && e.t2.pct != null && !near(e.t2.pct_mine, e.t2.pct, 0.12)) r.miss.push('JSON tier2 ' + e.t2.pct + ' vs independent ' + e.t2.pct_mine + ' (documented override for KR0079/KR0082)');
    // centre text rule (28px canvas text, not in the DOM): derived from the aria percentage -> check the rule inputs
    const centre = (p, na) => (p == null ? (na ? '—' : '데이터 없음') : (p > 100 ? '100%+' : p.toFixed(0) + '%'));
    r.shown.centre1 = centre(e.t1.pct, false); r.shown.centre2 = centre(e.t2.pct, e.t2.na);
    // empty-issuance flag under the tier1 caption
    const emptyShown = !g('donut-t1-empty').hidden;
    r.shown.t1empty = emptyShown;
    if (emptyShown !== e.t1.nosec) r.miss.push('발행 없음 shown=' + emptyShown + ' expected=' + e.t1.nosec + ' (JSON flag ' + e.t1.nosec_json + ')');
    // number lines
    const note = norm(g('donut-note').innerText).replace(/ \| /g, ' | ');
    r.shown.note = note;
    if (note !== norm(e.note)) r.miss.push('number lines: shown "' + note + '" expected "' + norm(e.note) + '"');
    // ? popover tail for tier1
    const tail = norm(g('help-capsec-t1-unconf').innerText);
    r.shown.t1tail = tail;
    if (e.t1.excl_t2 > 0) {
      const want = '보완자본으로 인정된 신종자본증권 ' + Math.round(e.t1.excl_t2).toLocaleString('ko-KR') + '억원';
      if (tail.indexOf(want) < 0) r.miss.push('tier1 ? tail lacks "' + want + '" (shown "' + tail + '")');
    }

    // ---- forward
    const ph = g('forward-placeholder');
    const fc = Chart.getChart('forward-chart');
    if (e.fwd == null) {
      r.shown.fwd = 'none';
      if (ph.style.display === 'none') r.miss.push('forward: expected placeholder (no row) but chart shown');
    } else if (e.fwd.status !== 'ok') {
      r.shown.fwd = 'excluded: ' + norm(ph.innerText);
      if (ph.style.display === 'none') r.miss.push('forward: expected placeholder for excluded company');
      if (e.fwd.reason && norm(ph.innerText).indexOf(norm(e.fwd.reason)) < 0) r.miss.push('forward placeholder lacks exclusion reason');
    } else {
      if (!fc) { r.miss.push('forward chart missing'); }
      else {
        const lab = fc.data.labels.join(',');
        const ratio = fc.data.datasets[0].data;
        const basic = fc.data.datasets[1]._originalBasic || fc.data.datasets[1].data;
        r.shown.fwd = { labels: lab, ratio, basic };
        if (lab !== e.fwd.years.join(',')) r.miss.push('forward years ' + lab + ' expected ' + e.fwd.years.join(','));
        e.fwd.ratio.forEach((v, i) => { if (!near(ratio[i], v, 0.005)) r.miss.push('forward ratio ' + e.fwd.years[i] + ' shown ' + ratio[i] + ' expected ' + v); });
        e.fwd.basic.forEach((v, i) => { if (!near(basic[i], v, 0.005)) r.miss.push('forward basic ' + e.fwd.years[i] + ' shown ' + basic[i] + ' expected ' + v); });
        const fn = norm(g('forward-note').innerText);
        r.shown.fnote = fn;
        if (fn !== norm(e.fwd.note)) r.miss.push('forward note: shown "' + fn + '" expected "' + norm(e.fwd.note) + '"');
        // tooltip tail for the 기본자본비율 series (new fields)
        const cb = fc.options.plugins.tooltip.callbacks.afterLabel;
        const tails = e.fwd.years.map((y, i) => cb({ datasetIndex: 1, dataIndex: i }));
        r.shown.fwdTail = tails.map((t) => t.join(' / '));
        e.fwd.years.forEach((y, i) => {
          const want = [];
          if (e.fwd.flag && e.fwd.by_type[i] != null) want.push('신종 분류 기준: ' + fmtSigned(e.fwd.by_type[i]));
          if (e.fwd.if_t2[i] != null) want.push('미확정 신종이 보완자본형이면: ' + fmtSigned(e.fwd.if_t2[i]));
          if (want.join('|') !== tails[i].join('|')) r.miss.push('forward tooltip tail ' + y + ': shown ' + JSON.stringify(tails[i]) + ' expected ' + JSON.stringify(want));
        });
      }
    }

    // ---- issuance bars + big cells
    const wrap = g('capsec-chart-wrap'), cells = g('capsec-cells');
    const cc = Chart.getChart('capsec-chart');
    const readCell = (id) => {
      const el = g(id);
      const rate = el.querySelector('.capsec-rate');
      const lines = Array.from(el.querySelectorAll('.capsec-line')).map((x) => norm(x.textContent));
      return { rate: rate ? norm(rate.textContent) : null, lines };
    };
    if (e.cap == null) {
      r.shown.cap = 'none';
      if (wrap.style.display !== 'none') r.miss.push('issuance chart wrapper visible although the company has no timeline rows');
      // by design (designer ticket): the two cells stay with a centred dash when the tier has no securities
      if (!cells.hidden) {
        const h0 = readCell('capsec-cell-hybrid'), s0 = readCell('capsec-cell-sub');
        r.shown.cells = { hybrid: h0, sub: s0 };
        if (h0.rate !== '—' || s0.rate !== '—' || h0.lines.length || s0.lines.length) r.miss.push('cells without timeline rows should show only a dash: ' + JSON.stringify([h0, s0]));
      }
    } else {
      if (!cc) { r.miss.push('issuance chart missing'); }
      else {
        const labels = cc.data.labels, hy = cc.data.datasets[0].data, sb = cc.data.datasets[1].data;
        r.shown.cap = { labels: labels.join(','), hy, sb };
        if (labels.join(',') !== e.cap.years.join(',')) r.miss.push('bar years ' + labels.join(',') + ' expected ' + e.cap.years.join(','));
        e.cap.hybrid.forEach((v, i) => { if (!near(hy[i], v, 0.011)) r.miss.push('bar hybrid ' + e.cap.years[i] + ' shown ' + hy[i] + ' expected ' + v); });
        e.cap.sub.forEach((v, i) => { if (!near(sb[i], v, 0.011)) r.miss.push('bar sub ' + e.cap.years[i] + ' shown ' + sb[i] + ' expected ' + v); });
      }
      const ch = readCell('capsec-cell-hybrid'), cs = readCell('capsec-cell-sub');
      r.shown.cells = { hybrid: ch, sub: cs };
      const chk = (nm, shown, want) => {
        if (want == null) { if (shown.rate !== '—' || shown.lines.length) r.miss.push(nm + ' cell: expected none/— shown ' + JSON.stringify(shown)); return; }
        if (shown.rate !== want.rate) r.miss.push(nm + ' rate shown ' + shown.rate + ' expected ' + want.rate);
        if (shown.lines[0] !== '총발행액 : ' + want.issued) r.miss.push(nm + ' issued shown "' + shown.lines[0] + '" expected "총발행액 : ' + want.issued + '"');
        if (shown.lines[1] !== '콜 상환 도래일 : ' + want.call) r.miss.push(nm + ' call shown "' + shown.lines[1] + '" expected "콜 상환 도래일 : ' + want.call + '"');
      };
      chk('신종자본증권', ch, e.cap.hybrid_cell);
      chk('후순위채', cs, e.cap.sub_cell);
    }
    // layout: no horizontal page scroll
    r.shown.scrollW = document.documentElement.scrollWidth; r.shown.innerW = window.innerWidth;
    if (document.documentElement.scrollWidth > window.innerWidth + 1) r.miss.push('horizontal overflow ' + document.documentElement.scrollWidth + ' > ' + window.innerWidth);
    return r;
  }

  window.AUD = async function (codes) {
    const EXP = await loadExp();
    const out = [];
    for (const c of codes) { out.push(await auditOne(EXP, c)); }
    return out;
  };
  window.AUD_LABELS = function () {
    const q = (s) => Array.from(document.querySelectorAll(s)).map((x) => norm(x.textContent));
    return {
      subtitle: q('#donut-section-panel .subtitle li'),
      captions: q('#donut-section-panel .donut-caption').map((t) => t),
      help1: norm(document.getElementById('help-capsec-t1').childNodes[0].textContent),
      help2: norm(document.getElementById('help-capsec-t2').textContent),
      headings: q('h2'),
      shareSections: Array.from(document.querySelectorAll('[data-share-section]')).map((x) => x.getAttribute('data-share-section')),
    };
  };
  return 'AUD ready';
})();
