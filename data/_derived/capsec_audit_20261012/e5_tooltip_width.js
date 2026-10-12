/* e5: does every Chart.js tooltip of K-ICS.html fit into its own canvas at the current viewport?
 * Chart.js draws a tooltip on the chart canvas, so a box wider than the canvas is cut off.  In a pane that is not painting, chart.tooltip.width/x are NaN,
 * therefore the box width is computed with the same formula Chart.js (getTooltipSize) uses:
 *     width = max(title line widths, body line widths + boxWidth + 2 + boxPadding) + padding.left + padding.right
 * with the chart's own resolved tooltip options and the canvas context font.  Calibration: one real mouse hover on the 하나생명 tier1 donut gave 329 px;
 * the formula gives 329 for the same text.
 * Input: window.__TT (the result object collected by e4_tooltip_audit.js TT()).   Usage:  const rows = TTW();
 */
(function () {
  window.TTW = function () {
    const H = Chart.helpers;
    const rows = [];
    const all = window.__TT || {};
    function boxWidthOf(chart, text, titleText, titleOpt) {
      const o = chart.tooltip.options;
      const bodyFont = H.toFont(o.bodyFont);
      const titleFont = H.toFont(o.titleFont);
      const pad = H.toPadding(o.padding);
      const ctx = chart.ctx;
      ctx.save();
      let w = 0;
      if (titleText) { ctx.font = titleFont.string; w = Math.max(w, ctx.measureText(titleText).width); }
      ctx.font = bodyFont.string;
      const widthPadding = o.displayColors ? (o.boxWidth + 2 + o.boxPadding) : 0;
      (text || []).forEach((t) => { w = Math.max(w, ctx.measureText(t).width + widthPadding); });
      ctx.restore();
      return Math.round(w + pad.width);
    }
    Object.values(all).forEach((r) => {
      ['donut-tier1', 'donut-tier2'].forEach((id) => {
        const ch = Chart.getChart(id);
        const s = r.shown[id];
        if (!ch || !s) return;
        const lines = [].concat(s.use || [], s.rest || []).map((x) => String(x).split(' / ')).reduce((a, b) => a.concat(b), []);
        const need = boxWidthOf(ch, lines, '');
        rows.push({ code: r.code, name: r.name, chart: id, need, canvasW: ch.canvas.clientWidth, clipped: need > ch.canvas.clientWidth, longest: lines.sort((a, b) => b.length - a.length)[0] });
      });
      const fc = Chart.getChart('forward-chart');
      if (fc && Array.isArray(r.shown.fwd)) {
        let worst = 0, worstLines = null;
        r.shown.fwd.forEach((p) => {
          const flat = (p.lines || []).reduce((a, b) => a.concat(b), []);
          const n = boxWidthOf(fc, flat, p.year);
          if (n > worst) { worst = n; worstLines = flat; }
        });
        rows.push({ code: r.code, name: r.name, chart: 'forward-chart', need: worst, canvasW: fc.canvas.clientWidth, clipped: worst > fc.canvas.clientWidth, longest: (worstLines || []).sort((a, b) => b.length - a.length)[0] });
      }
    });
    return rows;
  };
  return 'TTW ready';
})();
