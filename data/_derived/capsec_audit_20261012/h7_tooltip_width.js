/* h7: does every Chart.js tooltip of K-ICS.html fit into its own canvas at the current viewport?  (successor of e5_tooltip_width.js, new pin)
 * Chart.js draws a tooltip on the chart canvas and limits the box x to [0, chartWidth - boxWidth], so a box wider than the canvas is cut off at the right edge.
 * Where the pane does not paint, chart.tooltip.width is NaN, therefore the width is computed with the formula of Chart.js (getTooltipSize):
 *     width = max(title widths, body widths + boxWidth + 2 + boxPadding, footer widths (footerFont)) + padding.left + padding.right
 * with the chart's own resolved tooltip options and the canvas context font (calibration: real hover on 하나생명 tier1 = 329 px at the old pin; formula 329).
 * Input: window.__TT (collected by h6 TT()).  Usage:  const rows = TTW();
 */
(function () {
  window.TTW = function () {
    const H = Chart.helpers;
    const rows = [];
    const all = window.__TT || {};
    function need(chart, titleText, bodyLines, footerLines) {
      const o = chart.tooltip.options;
      const bodyFont = H.toFont(o.bodyFont);
      const titleFont = H.toFont(o.titleFont);
      const footerFont = H.toFont(o.footerFont);
      const pad = H.toPadding(o.padding);
      const ctx = chart.ctx;
      ctx.save();
      let w = 0;
      if (titleText) { ctx.font = titleFont.string; w = Math.max(w, ctx.measureText(titleText).width); }
      ctx.font = bodyFont.string;
      const widthPadding = o.displayColors ? (o.boxWidth + 2 + o.boxPadding) : 0;
      (bodyLines || []).forEach((t) => { w = Math.max(w, ctx.measureText(t).width + widthPadding); });
      if (footerLines && footerLines.length) { ctx.font = footerFont.string; footerLines.forEach((t) => { w = Math.max(w, ctx.measureText(t).width); }); }
      ctx.restore();
      return Math.round(w + pad.width);
    }
    const longest = (a) => a.slice().sort((x, y) => y.length - x.length)[0];
    Object.values(all).forEach((r) => {
      ['donut-tier1', 'donut-tier2'].forEach((id) => {
        const ch = Chart.getChart(id);
        const s = r.shown[id];
        if (!ch || !s) return;
        const lines = [].concat(s.use || [], s.rest || []);
        const n = need(ch, '', lines, []);
        rows.push({ code: r.code, name: r.name, chart: id, need: n, canvasW: ch.canvas.clientWidth, clipped: n > ch.canvas.clientWidth, longest: longest(lines) });
      });
      const fc = Chart.getChart('forward-chart');
      if (fc && Array.isArray(r.shown.fwd)) {
        let worst = 0, wl = null;
        r.shown.fwd.forEach((p) => {
          const flat = (p.lines || []).reduce((a, b) => a.concat(b), []);
          const n = need(fc, p.year, flat, []);
          if (n > worst) { worst = n; wl = flat; }
        });
        rows.push({ code: r.code, name: r.name, chart: 'forward-chart', need: worst, canvasW: fc.canvas.clientWidth, clipped: worst > fc.canvas.clientWidth, longest: longest(wl || []) });
      }
      const cc = Chart.getChart('capsec-chart');
      if (cc && Array.isArray(r.shown.bars)) {
        let worst = 0, wl = null;
        r.shown.bars.forEach((p) => {
          const n = need(cc, p.year, p.lines || [], p.footer || []);
          if (n > worst) { worst = n; wl = (p.lines || []).concat(p.footer || []); }
        });
        rows.push({ code: r.code, name: r.name, chart: 'capsec-chart', need: worst, canvasW: cc.canvas.clientWidth, clipped: worst > cc.canvas.clientWidth, longest: longest(wl || []) });
      }
    });
    return rows;
  };
  return 'TTW ready';
})();
