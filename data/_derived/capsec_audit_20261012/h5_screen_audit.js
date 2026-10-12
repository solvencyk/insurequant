/* h5: browser-side screen audit of K-ICS.html at the NEW pin (re-measure 2026-10-13); successor of e3_screen_audit.js.
 * Expected values come from h4_expected_<rev>.json (served from the same local site folder), built independently of the page code.
 * Usage (page opened with ?iq_internal=1; scripts are injected with <script src> because the page CSP forbids eval):
 *     await H5LOAD('h4_expected_6fd00720.json');
 *     const res = await AUD(['KR0068', ...]);       // -> [{code, name, miss:[...], shown:{...}}]
 * Each company is selected through the page's own <select id="company"> change handler; DOM and Chart.js objects are read afterwards.
 * New in this version: forward series with null (자본잠식) points, the hidden 3rd series, triangle negatives in note and axis ticks, the clip notice line,
 * the 100%+ / unconfirmed tooltip lines (checked in h6), date-only call cell, estimated-bar footer.
 */
(function () {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const norm = (s) => String(s == null ? '' : s).replace(/ /g, ' ').replace(/\s+/g, ' ').trim();
  const near = (a, b, tol) => (a == null && b == null) || (a != null && b != null && Math.abs(a - b) <= tol);

  window.H5LOAD = async function (name) {
    window.__EXP = await (await fetch(name + '?v=' + Date.now())).json();
    return Object.keys(window.__EXP).length;
  };

  async function auditOne(EXP, code) {
    const e = EXP[code];
    const r = { code, name: e.name, miss: [], shown: {} };
    const sel = document.getElementById('company');
    sel.value = e.name;
    if (sel.value !== e.name) { r.miss.push('company not selectable: ' + e.name); return r; }
    sel.dispatchEvent(new Event('change', { bubbles: true }));
    await sleep(800);
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
    if (e.t1.pct_mine != null && !near(e.t1.pct_mine, e.t1.pct, 0.12)) r.miss.push('JSON tier1 ' + e.t1.pct + ' vs independent ' + e.t1.pct_mine);
    if (e.t2.pct_mine != null && e.t2.pct != null && !near(e.t2.pct_mine, e.t2.pct, 0.12)) r.miss.push('JSON tier2 ' + e.t2.pct + ' vs independent ' + e.t2.pct_mine);
    const emptyShown = !g('donut-t1-empty').hidden;
    r.shown.t1empty = emptyShown;
    if (emptyShown !== e.t1.nosec) r.miss.push('발행 없음 shown=' + emptyShown + ' expected=' + e.t1.nosec + ' (JSON flag ' + e.t1.nosec_json + ')');
    // number lines
    const note = norm(g('donut-note').innerText).replace(/ \| /g, ' | ');
    r.shown.note = note;
    if (note !== norm(e.note)) r.miss.push('number lines: shown "' + note + '" expected "' + norm(e.note) + '"');
    // ? popover tail for tier1: excluded tier2-type amount + (unconfirmed text when present)
    const tail = norm(g('help-capsec-t1-unconf').innerText);
    r.shown.t1tail = tail;
    if (e.t1.excl_t2 > 0) {
      const want = '보완자본으로 인정된 신종자본증권 ' + Math.round(e.t1.excl_t2).toLocaleString('ko-KR') + '억원';
      if (tail.indexOf(want) < 0) r.miss.push('tier1 ? tail lacks "' + want + '" (shown "' + tail + '")');
    }
    if (e.t1.unconf_text) {
      if (tail.indexOf(norm(e.t1.unconf_text)) < 0) r.miss.push('tier1 ? tail lacks "' + e.t1.unconf_text + '" (shown "' + tail + '")');
    } else if (tail.indexOf('미확정') >= 0) r.miss.push('tier1 ? tail shows an unconfirmed line although none is expected: "' + tail + '"');
    if (!(e.t1.excl_t2 > 0) && !e.t1.unconf_text && tail !== '') r.miss.push('tier1 ? tail should be empty: "' + tail + '"');

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
        const ds2 = fc.data.datasets[2];
        r.shown.fwd = { labels: lab, ratio, basic, ex: ds2 ? [ds2._exR, ds2._exB] : null };
        if (lab !== e.fwd.years.join(',')) r.miss.push('forward years ' + lab + ' expected ' + e.fwd.years.join(','));
        e.fwd.ratio.forEach((v, i) => { if (!near(ratio[i], v, 0.005)) r.miss.push('forward ratio ' + e.fwd.years[i] + ' shown ' + ratio[i] + ' expected ' + v); });
        e.fwd.basic.forEach((v, i) => { if (!near(basic[i], v, 0.005)) r.miss.push('forward basic ' + e.fwd.years[i] + ' shown ' + basic[i] + ' expected ' + v); });
        // clipped years must be null points (no drawn 0), and the hidden 3rd series must flag exactly those years
        e.fwd.exR.forEach((x, i) => { if (x && ratio[i] !== null) r.miss.push('forward ratio ' + e.fwd.years[i] + ' must be null (capital <= 0) but is ' + ratio[i]); });
        e.fwd.exB.forEach((x, i) => { if (x && basic[i] !== null) r.miss.push('forward basic ' + e.fwd.years[i] + ' must be null (basic capital <= 0) but is ' + basic[i]); });
        if (!ds2) { if (e.fwd.exR.some(Boolean) || e.fwd.exB.some(Boolean)) r.miss.push('forward: clipped years but no hidden tooltip series'); }
        else {
          if (JSON.stringify(ds2._exR) !== JSON.stringify(e.fwd.exR)) r.miss.push('forward _exR ' + JSON.stringify(ds2._exR) + ' expected ' + JSON.stringify(e.fwd.exR));
          if (JSON.stringify(ds2._exB) !== JSON.stringify(e.fwd.exB)) r.miss.push('forward _exB ' + JSON.stringify(ds2._exB) + ' expected ' + JSON.stringify(e.fwd.exB));
        }
        // note: baseline + 2030 change + balance, and the clip notice line
        const fn = norm(g('forward-note').innerText);
        r.shown.fnote = fn;
        const want = norm(e.fwd.note + (e.fwd.clip_note ? ' ' + e.fwd.clip_note : ''));
        if (fn !== want) r.miss.push('forward note: shown "' + fn + '" expected "' + want + '"');
        if (/-\s?\d/.test(g('forward-note').innerText)) r.miss.push('forward note contains an ASCII minus: "' + fn + '"');
        const clipEl = g('forward-clip-note');
        if (!!clipEl !== !!e.fwd.clip_note) r.miss.push('clip notice element present=' + !!clipEl + ' expected=' + !!e.fwd.clip_note);
        // axis ticks: no ASCII minus
        ['y', 'y1'].forEach((ax) => { const sc = fc.scales[ax]; if (sc) sc.ticks.forEach((t) => { if (typeof t.label === 'string' && /^-\d/.test(t.label)) r.miss.push('axis ' + ax + ' tick with ASCII minus: ' + t.label); }); });
        // legend must not list the hidden series
        try { const items = fc.legend.legendItems.map((x) => x.text); r.shown.legend = items; if (items.indexOf('자본잠식') >= 0) r.miss.push('legend lists the hidden 자본잠식 series'); } catch (x) { /* legend not ready */ }
        // tooltip tail callback (new fields) - generic
        const cb = fc.options.plugins.tooltip.callbacks.afterLabel;
        const tails = e.fwd.years.map((y, i) => cb({ datasetIndex: 1, dataIndex: i }));
        r.shown.fwdTail = tails.map((t) => t.join(' / '));
        e.fwd.years.forEach((y, i) => {
          const wantT = [];
          const tri = (v) => (v < 0 ? '△' : '') + Math.abs(v).toFixed(2) + '%';
          if (e.fwd.flag && e.fwd.by_type[i] != null) wantT.push('신종 분류 기준: ' + tri(e.fwd.by_type[i]));
          if (e.fwd.if_t2[i] != null) wantT.push('미확정 신종이 보완자본형이면: ' + tri(e.fwd.if_t2[i]));
          if (wantT.join('|') !== tails[i].join('|')) r.miss.push('forward tooltip tail ' + y + ': shown ' + JSON.stringify(tails[i]) + ' expected ' + JSON.stringify(wantT));
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
        // estimated-bar footer
        const ft = cc.options.plugins.tooltip.callbacks.footer;
        e.cap.est.forEach((x, i) => {
          const got = ft([{ dataIndex: i }]);
          const gs = Array.isArray(got) ? got.join('') : String(got);
          if (x && gs !== '추정(원장 미갱신)') r.miss.push('bar ' + e.cap.years[i] + ' footer should be 추정(원장 미갱신), shown "' + gs + '"');
          if (!x && gs !== '') r.miss.push('bar ' + e.cap.years[i] + ' footer should be empty, shown "' + gs + '"');
        });
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
    r.shown.scrollW = document.documentElement.scrollWidth; r.shown.innerW = window.innerWidth;
    if (document.documentElement.scrollWidth > window.innerWidth + 1) r.miss.push('horizontal overflow ' + document.documentElement.scrollWidth + ' > ' + window.innerWidth);
    return r;
  }

  window.AUD = async function (codes) {
    if (!window.__EXP) throw new Error('call H5LOAD(name) first');
    const out = [];
    for (const c of codes) { out.push(await auditOne(window.__EXP, c)); }
    return out;
  };
  window.AUD_LABELS = function () {
    const q = (s) => Array.from(document.querySelectorAll(s)).map((x) => norm(x.textContent));
    return {
      subtitle: q('#donut-section-panel .subtitle li'),
      captions: q('#donut-section-panel .donut-caption'),
      help1: norm(document.getElementById('help-capsec-t1').childNodes[0].textContent),
      help2: norm(document.getElementById('help-capsec-t2').textContent),
      headings: q('h2'),
      shareSections: Array.from(document.querySelectorAll('[data-share-section]')).map((x) => x.getAttribute('data-share-section')),
    };
  };
  return 'H5 ready';
})();
