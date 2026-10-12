/* h8: share image (theme.js shRender -> html2canvas) check for the three new/changed K-ICS sections at the current viewport (run at 375 px).
 * For each company the page's own section-share routine is called (IQTheme.share.render(section, IQTheme.share.secOpts(section))) and the returned canvas is
 * inspected by pixels: donut ring colours (tier1 / tier2), forward series colours, issuance bar colours; and the image header text from meta.head.
 * Chart.js animations are finished first with chart.update('none') (otherwise a just-created chart is copied half drawn - a harness matter, not a product defect).
 * Expected values come from window.__EXP (H5LOAD).   Usage:  const rows = await SHARECHECK(['KR0068', ...]);
 */
(function () {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  function count(cv, pred) {
    const d = cv.getContext('2d').getImageData(0, 0, cv.width, cv.height).data;
    let n = 0;
    for (let i = 0; i < d.length; i += 4) if (pred(d[i], d[i + 1], d[i + 2])) n++;
    return n;
  }
  const isRed = (r, g, b) => r > 150 && g < 90 && b < 90;                 // donut >= 100%
  const isOrange = (r, g, b) => r > 200 && g > 120 && g < 190 && b < 110;  // donut 70..100%
  const isTeal = (r, g, b) => r < 140 && g > 150 && b > 150;               // donut < 70% / ratio line
  const isPink = (r, g, b) => r > 200 && g > 70 && g < 130 && b > 100 && b < 170;   // basic ratio line
  const isGold = (r, g, b) => r > 170 && g > 130 && g < 200 && b < 110;    // subordinated bars
  function settleCharts() { ['donut-tier1', 'donut-tier2', 'forward-chart', 'capsec-chart'].forEach((id) => { const c = Chart.getChart(id); if (c) c.update('none'); }); }

  window.SHARECHECK = async function (codes) {
    const EXP = window.__EXP;
    const sel = document.getElementById('company');
    await new Promise((res, rej) => IQTheme.share.load(res, () => rej(new Error('html2canvas not loadable'))));
    const rows = [];
    for (const code of codes) {
      const e = EXP[code];
      const row = { code, name: e.name, miss: [], px: {} };
      sel.value = e.name;
      sel.dispatchEvent(new Event('change', { bubbles: true }));
      await sleep(900);
      settleCharts();
      await sleep(300);
      for (const [id, label] of [['donut-section-panel', 'donut'], ['sec-forward', 'forward'], ['sec-capsec', 'capsec']]) {
        const el = document.getElementById(id);
        if (!el || (id === 'sec-capsec' && !e.cap) || (id === 'sec-forward' && (!e.fwd || e.fwd.status !== 'ok'))) { row.px[label] = 'section not applicable'; continue; }
        el.scrollIntoView({ block: 'start' });
        await sleep(500);
        settleCharts();
        const r = await IQTheme.share.render(el, IQTheme.share.secOpts(el));
        const cv = r.canvas;
        const info = { size: cv.width + 'x' + cv.height, head: r.meta.head, truncated: r.meta.truncated };
        if (label === 'donut') {
          const t1 = e.t1.pct, t2 = e.t2.pct;
          const red = count(cv, isRed), orange = count(cv, isOrange), teal = count(cv, isTeal);
          Object.assign(info, { red, orange, teal });
          // the tier1 ring is red when >= 100, orange when 70..100, teal when < 70 (and > 0); tier2 likewise.  At least one ring pixel set per non-zero donut.
          const need = (p) => (p == null || p <= 0) ? null : (p >= 100 ? 'red' : (p >= 70 ? 'orange' : 'teal'));
          [need(t1), need(t2)].forEach((c) => { if (c && info[c] < 500) row.miss.push('donut share image lacks ' + c + ' ring pixels (' + info[c] + ')'); });
        } else if (label === 'forward') {
          const teal = count(cv, isTeal), pink = count(cv, isPink);
          Object.assign(info, { teal, pink });
          const anyR = e.fwd.ratio.some((v) => v != null), anyB = e.fwd.basic.some((v) => v != null);
          if (anyR && teal < 300) row.miss.push('forward share image lacks the ratio line (teal ' + teal + ')');
          if (anyB && pink < 150) row.miss.push('forward share image lacks the basic-ratio line (pink ' + pink + ')');
          if (!anyR && !anyB) {
            // clipped company: no series drawn; the image must still carry the chart frame (axis text/grid) - count non-background pixels in the chart area
            const d = cv.getContext('2d').getImageData(0, 0, cv.width, cv.height).data;
            const bg = [d[0], d[1], d[2]]; let nz = 0;
            for (let i = 0; i < d.length; i += 4) if (Math.abs(d[i] - bg[0]) + Math.abs(d[i + 1] - bg[1]) + Math.abs(d[i + 2] - bg[2]) > 30) nz++;
            info.nonBackground = nz;
            if (nz < 20000) row.miss.push('forward share image of a clipped company is nearly empty (' + nz + ')');
          }
        } else {
          const teal = count(cv, isTeal), gold = count(cv, isGold);
          Object.assign(info, { teal, gold });
          const anyH = e.cap.hybrid.some((v) => v > 0), anyS = e.cap.sub.some((v) => v > 0);
          if (anyH && teal < 500) row.miss.push('capsec share image lacks hybrid bars (teal ' + teal + ')');
          if (anyS && gold < 500) row.miss.push('capsec share image lacks subordinated bars (gold ' + gold + ')');
        }
        const shown = (sel.options[sel.selectedIndex] ? sel.options[sel.selectedIndex].text : e.name).trim();      // the page's display name (e.g. iM라이프)
        if (!/K-ICS/.test(info.head) || (info.head.indexOf(shown) < 0 && info.head.indexOf(e.name.slice(0, 2)) < 0)) row.miss.push('share header "' + info.head + '" does not name the company "' + shown + '"');
        row.px[label] = info;
      }
      rows.push(row);
    }
    return rows;
  };
  return 'SHARECHECK ready';
})();
