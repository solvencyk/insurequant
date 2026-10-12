/* h6: render and read the Chart.js tooltips of K-ICS.html for every company at the NEW pin: donut tier1/tier2, Forward Outlook points (incl. 자본잠식 years)
 * and the issuance-bar tooltips (title / body / footer, 추정(원장 미갱신) footer).  Successor of e4_tooltip_audit.js.
 * The tooltip object of each chart is driven with setActiveElements; for the forward and bar charts the ACTIVE ELEMENTS ARE THE ONES A REAL HOVER WOULD PICK:
 * chart.getElementsAtEventForMode({type:'mousemove', x, y, native:true}, 'index', {intersect:false, axis:'x'}) at the pixel of the year (null points are skipped by Chart.js, so a
 * clipped year only activates the hidden 3rd series).  Expected strings come from h4_expected_<rev>.json (window.__EXP, loaded by H5LOAD).
 * Usage:  const res = await TT(['KR0011', ...]);  results are also kept in window.__TT[code].
 */
(function () {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const norm = (s) => String(s == null ? '' : s).replace(/ /g, ' ').replace(/\s+/g, ' ').trim();
  const f2 = (v) => Number(v).toFixed(2);
  const triPct = (v) => (v < 0 ? '△' : '') + Math.abs(v).toFixed(2) + '%';
  const fmtEok = (v) => Math.round(v).toLocaleString('ko-KR');

  function read(chart) {
    const tt = chart.tooltip;
    return {
      title: (tt.title || []).slice(),
      body: (tt.body || []).map((b) => ({ lines: (b.lines || []).slice(), after: (b.after || []).slice() })),
      footer: (tt.footer || []).slice(),
      canvasW: chart.canvas.clientWidth,
    };
  }
  function drive(chart, picks, at) {
    chart.tooltip.setActiveElements(picks, at);
    chart.setActiveElements(picks);
    chart.update();
    return read(chart);
  }
  function clear(chart) { chart.tooltip.setActiveElements([], { x: 0, y: 0 }); chart.setActiveElements([]); chart.update(); }
  // the elements a real mouse at (x, y) would activate (tooltip mode 'index', intersect false)
  function hoverPicks(chart, x, y, mode) {
    const els = chart.getElementsAtEventForMode({ type: 'mousemove', x, y, native: true }, mode || 'index', { intersect: false, axis: 'x' }, false);
    return els.map((el) => ({ datasetIndex: el.datasetIndex, index: el.index }));
  }
  function expectedDonut(pct, na, overNote, extra) {
    if (pct == null) return { use: [na || '데이터 없음'], rest: [na || '데이터 없음'] };
    const ex = extra ? [extra] : [];
    const use = (pct > 100 ? ['사용: 100%+ (실제 ' + pct.toFixed(1) + '%)'].concat(overNote ? [overNote] : []) : ['사용: ' + pct.toFixed(2) + '%']).concat(ex);
    const rest = ['잔여: ' + Math.max(0, 100 - pct).toFixed(2) + '%'].concat(ex);
    return { use, rest };
  }
  const same = (a, b) => JSON.stringify(a.map(norm)) === JSON.stringify(b.map(norm));

  window.TT = async function (codes) {
    const EXP = window.__EXP;
    if (!EXP) throw new Error('call H5LOAD(name) first');
    window.__TT = window.__TT || {};
    const sel = document.getElementById('company');
    const out = [];
    for (const code of codes) {
      const e = EXP[code];
      const r = { code, name: e.name, miss: [], shown: {} };
      sel.value = e.name;
      sel.dispatchEvent(new Event('change', { bubbles: true }));
      await sleep(700);
      // ---- donuts
      for (const [id, tier] of [['donut-tier1', e.t1], ['donut-tier2', e.t2]]) {
        const ch = Chart.getChart(id);
        const cx = ch.chartArea.left + (ch.chartArea.right - ch.chartArea.left) / 2, cy = ch.chartArea.top + (ch.chartArea.bottom - ch.chartArea.top) / 2;
        const pct = tier.pct;
        const na = (id === 'donut-tier2' && tier.na) ? '경과조치 표 미공시' : '';
        const ex = (id === 'donut-tier1' && tier.unconf_text) ? tier.unconf_text : null;
        const want = expectedDonut(pct, na, tier.over_note, ex);
        const t0 = drive(ch, [{ datasetIndex: 0, index: 0 }], { x: cx, y: cy - 0.86 * (ch.outerRadius || 80) });
        const t1 = drive(ch, [{ datasetIndex: 0, index: 1 }], { x: cx, y: cy + 0.86 * (ch.outerRadius || 80) });
        const got0 = t0.body.length ? t0.body[0].lines : [];
        const got1 = t1.body.length ? t1.body[0].lines : [];
        r.shown[id] = { use: got0.slice(), rest: got1.slice(), canvasW: t0.canvasW };
        if (!same(got0, want.use)) r.miss.push(id + ' 사용: shown ' + JSON.stringify(got0) + ' expected ' + JSON.stringify(want.use));
        if (!same(got1, want.rest)) r.miss.push(id + ' 잔여: shown ' + JSON.stringify(got1) + ' expected ' + JSON.stringify(want.rest));
        clear(ch);
      }
      // ---- forward points
      const fc = Chart.getChart('forward-chart');
      if (e.fwd && e.fwd.status === 'ok' && fc) {
        const years = e.fwd.years;
        r.shown.fwd = [];
        for (let i = 0; i < years.length; i++) {
          const x = fc.scales.x.getPixelForValue(i);
          const y = (fc.chartArea.top + fc.chartArea.bottom) / 2;
          const picks = hoverPicks(fc, x, y, 'index');
          const t = drive(fc, picks, { x, y });
          const lines = t.body.map((b) => b.lines.concat(b.after));
          r.shown.fwd.push({ year: t.title.join(''), lines, picked: picks.map((p) => p.datasetIndex) });
          // expected body items in dataset order
          const wantBody = [];
          if (!e.fwd.exR[i]) wantBody.push(['지급여력비율: ' + f2(e.fwd.ratio[i]) + '%']);
          if (!e.fwd.exB[i]) {
            const tails = [];
            if (e.fwd.flag && e.fwd.by_type[i] != null) tails.push('신종 분류 기준: ' + triPct(e.fwd.by_type[i]));
            if (e.fwd.if_t2[i] != null) tails.push('미확정 신종이 보완자본형이면: ' + triPct(e.fwd.if_t2[i]));
            wantBody.push(['기본자본비율: ' + f2(e.fwd.basic[i]) + '%'].concat(tails));
          }
          if (e.fwd.exR[i] || e.fwd.exB[i]) {
            const cl = [];
            if (e.fwd.exR[i]) cl.push('지급여력비율: 자본잠식');
            if (e.fwd.exB[i]) cl.push('기본자본비율: 자본잠식');
            wantBody.push(cl);
          }
          if (t.title.join('') !== years[i]) r.miss.push('forward title ' + t.title.join('') + ' expected ' + years[i]);
          if (lines.length !== wantBody.length || lines.some((l, k) => !same(l, wantBody[k]))) r.miss.push('forward ' + years[i] + ' body shown ' + JSON.stringify(lines) + ' expected ' + JSON.stringify(wantBody));
          if (/-\d/.test(lines.map((l) => l.join(' ')).join(' '))) r.miss.push('forward ' + years[i] + ' tooltip contains an ASCII minus');
        }
        clear(fc);
      }
      // ---- issuance bars
      const cc = Chart.getChart('capsec-chart');
      if (e.cap && cc) {
        r.shown.bars = [];
        for (let i = 0; i < e.cap.years.length; i++) {
          const x = cc.scales.x.getPixelForValue(i);
          const y = (cc.chartArea.top + cc.chartArea.bottom) / 2;
          const picks = hoverPicks(cc, x, y, 'index');
          const t = drive(cc, picks, { x, y });
          const lines = t.body.map((b) => b.lines.join(' '));
          r.shown.bars.push({ year: t.title.join(''), lines, footer: t.footer.slice() });
          const wantLines = ['신종자본증권: ' + fmtEok(e.cap.hybrid[i]) + '억', '후순위채: ' + fmtEok(e.cap.sub[i]) + '억'];
          if (t.title.join('') !== e.cap.years[i] + '년 발행') r.miss.push('bar title ' + t.title.join('') + ' expected ' + e.cap.years[i] + '년 발행');
          if (!same(lines, wantLines)) r.miss.push('bar ' + e.cap.years[i] + ' body shown ' + JSON.stringify(lines) + ' expected ' + JSON.stringify(wantLines));
          const wantFooter = e.cap.est[i] ? ['추정(원장 미갱신)'] : [];
          if (!same(t.footer, wantFooter)) r.miss.push('bar ' + e.cap.years[i] + ' footer shown ' + JSON.stringify(t.footer) + ' expected ' + JSON.stringify(wantFooter));
        }
        clear(cc);
      }
      window.__TT[code] = r;
      out.push(r);
    }
    return out;
  };
  return 'TT ready';
})();
