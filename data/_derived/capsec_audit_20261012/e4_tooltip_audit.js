/* e4: render and read the Chart.js tooltips of K-ICS.html for every company (donut tier1/tier2 and Forward Outlook points) at the current viewport.
 * The tooltips are triggered through the chart's own tooltip object (setActiveElements) so the page's callbacks run; a few companies were additionally
 * hovered with the real mouse (separate evidence).  Expected strings come from e2_expected_<rev>.json (independent of the page code).
 * Usage:  load e3_screen_audit.js first (defines window.__EXP loader) then
 *   const res = await TT(['KR0011', ...]);
 */
(function () {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const norm = (s) => String(s == null ? '' : s).replace(/ /g, ' ').replace(/\s+/g, ' ').trim();
  const f2 = (v) => Number(v).toFixed(2);
  const fmtSigned = (v) => (v < 0 ? '△' : '') + Math.abs(v).toFixed(2) + '%';

  async function expAll() {
    if (!window.__EXP) window.__EXP = await (await fetch('e2_expected_dbbffcb5.json')).json();
    return window.__EXP;
  }
  function trigger(chart, picks, at) {
    chart.tooltip.setActiveElements(picks, at);
    chart.setActiveElements(picks);
    chart.update();
    const tt = chart.tooltip;
    return {
      title: (tt.title || []).slice(),
      body: (tt.body || []).map((b) => ({ lines: (b.lines || []).slice(), after: (b.after || []).slice() })),
      x: Math.round(tt.x), y: Math.round(tt.y), w: Math.round(tt.width), h: Math.round(tt.height),
      canvasW: chart.canvas.clientWidth, canvasH: chart.canvas.clientHeight,
    };
  }
  function expectedDonut(pct, na, overNote, extra) {
    if (pct == null) return { use: [na || '데이터 없음'], rest: [na || '데이터 없음'] };
    const ex = extra ? [extra] : [];
    const use = ['사용: ' + (pct > 100 ? '100%+ (실제 ' + pct.toFixed(1) + '%' + (overNote ? ' · ' + overNote : '') + ')' : pct.toFixed(2) + '%')].concat(ex);
    const rest = ['잔여: ' + Math.max(0, 100 - pct).toFixed(2) + '%'].concat(ex);
    return { use, rest };
  }

  window.TT = async function (codes) {
    const EXP = await expAll();
    const sel = document.getElementById('company');
    const out = [];
    for (const code of codes) {
      const e = EXP[code];
      const r = { code, name: e.name, miss: [], shown: {} };
      sel.value = e.name;
      sel.dispatchEvent(new Event('change', { bubbles: true }));
      await sleep(600);
      // ---- donuts
      for (const [id, tier, over, extra] of [['donut-tier1', e.t1, '초과분은 보완자본으로 재분류', null], ['donut-tier2', e.t2, '초과분은 지급여력금액에서 불인정', null]]) {
        const ch = Chart.getChart(id);
        const cx = ch.chartArea.left + (ch.chartArea.right - ch.chartArea.left) / 2, cy = ch.chartArea.top + (ch.chartArea.bottom - ch.chartArea.top) / 2;
        const pct = tier.pct;
        const na = (id === 'donut-tier2' && tier.na) ? '경과조치 표 미공시' : '';
        // tier1 unconfirmed extra line (type_unconfirmed companies)
        let ex = null;
        if (id === 'donut-tier1' && tier.unconf) ex = '기본자본형/보완자본형 미확정 신종 포함' + (tier.unconf_pct != null ? ', 보완자본형이면 ' + Number(tier.unconf_pct).toFixed(1) + '%' : '');
        const want = expectedDonut(pct, na, over, ex);
        const t0 = trigger(ch, [{ datasetIndex: 0, index: 0 }], { x: cx, y: cy - 0.86 * (ch.outerRadius || 80) });
        const t1 = trigger(ch, [{ datasetIndex: 0, index: 1 }], { x: cx, y: cy + 0.86 * (ch.outerRadius || 80) });
        r.shown[id] = { use: t0.body.map((b) => b.lines.join(' / ')), rest: t1.body.map((b) => b.lines.join(' / ')), geom: { w: t0.w, canvasW: t0.canvasW, x: t0.x } };
        const got0 = t0.body.length ? t0.body[0].lines : [];
        const got1 = t1.body.length ? t1.body[0].lines : [];
        if (pct == null) {
          if (norm(got0[0]) !== norm(want.use[0])) r.miss.push(id + ' tooltip (no pct): shown ' + JSON.stringify(got0) + ' expected ' + JSON.stringify(want.use));
        } else {
          if (norm(got0[0]) !== norm(want.use[0])) r.miss.push(id + ' 사용: shown "' + got0[0] + '" expected "' + want.use[0] + '"');
          if (norm(got1[0]) !== norm(want.rest[0])) r.miss.push(id + ' 잔여: shown "' + got1[0] + '" expected "' + want.rest[0] + '"');
          if (tier.unconf && (got0.length < 2 || norm(got0[1]) !== norm(ex))) r.miss.push(id + ' unconfirmed extra line: shown ' + JSON.stringify(got0) + ' expected "' + ex + '"');
          if (!tier.unconf && got0.length > 1) r.miss.push(id + ' unexpected extra tooltip line ' + JSON.stringify(got0));
        }
        if (t0.x + t0.w > t0.canvasW + 1) r.miss.push(id + ' tooltip box wider than its canvas: x ' + t0.x + ' + w ' + t0.w + ' > ' + t0.canvasW);
        ch.tooltip.setActiveElements([], { x: 0, y: 0 }); ch.setActiveElements([]); ch.update();
      }
      // ---- forward points
      const fc = Chart.getChart('forward-chart');
      if (e.fwd && e.fwd.status === 'ok' && fc) {
        const years = e.fwd.years;
        r.shown.fwd = [];
        for (let i = 0; i < years.length; i++) {
          const m0 = fc.getDatasetMeta(0).data[i], m1 = fc.getDatasetMeta(1).data[i];
          const t = trigger(fc, [{ datasetIndex: 0, index: i }, { datasetIndex: 1, index: i }], { x: m0.x, y: m0.y });
          const lines = t.body.map((b) => b.lines.concat(b.after));
          r.shown.fwd.push({ year: t.title.join(''), lines, w: t.w, canvasW: t.canvasW, x: t.x });
          const wantR = '지급여력비율: ' + f2(e.fwd.ratio[i]) + '%';
          const wantB = '기본자본비율: ' + f2(e.fwd.basic[i]) + '%';
          const tails = [];
          if (e.fwd.flag && e.fwd.by_type[i] != null) tails.push('신종 분류 기준: ' + fmtSigned(e.fwd.by_type[i]));
          if (e.fwd.if_t2[i] != null) tails.push('미확정 신종이 보완자본형이면: ' + fmtSigned(e.fwd.if_t2[i]));
          if (t.title.join('') !== years[i]) r.miss.push('forward title ' + t.title.join('') + ' expected ' + years[i]);
          if (!t.body[0] || norm(t.body[0].lines[0]) !== wantR) r.miss.push('forward ' + years[i] + ' line1 shown ' + JSON.stringify(t.body[0] && t.body[0].lines) + ' expected "' + wantR + '"');
          if (!t.body[1] || norm(t.body[1].lines[0]) !== wantB) r.miss.push('forward ' + years[i] + ' line2 shown ' + JSON.stringify(t.body[1] && t.body[1].lines) + ' expected "' + wantB + '"');
          const gotTail = t.body[1] ? t.body[1].after : [];
          if (JSON.stringify(gotTail) !== JSON.stringify(tails)) r.miss.push('forward ' + years[i] + ' tail shown ' + JSON.stringify(gotTail) + ' expected ' + JSON.stringify(tails));
          if (t.x + t.w > t.canvasW + 1) r.miss.push('forward ' + years[i] + ' tooltip wider than canvas: x ' + t.x + ' + w ' + t.w + ' > ' + t.canvasW);
        }
        fc.tooltip.setActiveElements([], { x: 0, y: 0 }); fc.setActiveElements([]); fc.update();
      }
      out.push(r);
    }
    return out;
  };
  return 'TT ready';
})();
