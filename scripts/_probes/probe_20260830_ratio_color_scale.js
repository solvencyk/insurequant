// 새 색 스케일 검증 — index.html 의 실제 함수를 꺼내 실데이터 39사에 돌린다.
// ① 초록 구간이 실제로 갈라지는가(옛것 대비) ② 모든 칸의 글자 대비가 WCAG AA(4.5:1) 이상인가
const fs = require('fs');
const ROOT = process.argv[2];
const out = require(ROOT + '/colorfns.js');

// 옛 스케일 재현 (커밋 전 정의)
function oldColor(ratio) {
  const REC = 130, STRONG = 200;
  if (ratio >= REC) {
    const i = Math.min((ratio - REC) / (STRONG - REC), 1) * 0.7 + 0.15;
    return { h: 130, s: 30 + 50 * i, l: 42 - 15 * i };
  }
  const i = Math.min((REC - ratio) / 60, 1);
  return { h: 0, s: 35 + 45 * i, l: 42 - 15 * i };
}

function lum(h, s, l) {
  s /= 100; l /= 100;
  const c = (1 - Math.abs(2 * l - 1)) * s, x = c * (1 - Math.abs(((h / 60) % 2) - 1)), m = l - c / 2;
  const [r, g, b] = h < 60 ? [c, x, 0] : h < 120 ? [x, c, 0] : h < 180 ? [0, c, x]
                  : h < 240 ? [0, x, c] : h < 300 ? [x, 0, c] : [c, 0, x];
  const f = v => { const u = v + m; return u <= 0.03928 ? u / 12.92 : Math.pow((u + 0.055) / 1.055, 2.4); };
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
}
const contrast = (Y, ink) => ink === '#ffffff' ? 1.05 / (Y + 0.05) : (Y + 0.05) / 0.05;

const rows = JSON.parse(fs.readFileSync(ROOT + '/kics_disclosure.json', 'utf8'));
const qs = [...new Set(rows.map(r => r['공시분기']))].sort();
const q = qs[qs.length - 1];
const num = v => { const n = parseFloat(String(v).replace(/,/g, '')); return isFinite(n) ? n : null; };
const data = rows.filter(r => r['항목번호'] === 27 && r['공시분기'] === q)
  .map(r => ({ n: r['원수사명'], v: num(r['값_적용후'] != null ? r['값_적용후'] : r['값']) }))
  .filter(d => d.v != null).sort((a, b) => a.v - b.v);

console.log(`분기 ${q} · ${data.length}사\n`);
console.log('회사'.padEnd(20) + '비율'.padStart(8) + '  옛 L'.padStart(8) + '  새 L'.padStart(8) + '  글자'.padStart(9) + '  대비');
const oldL = new Set(), newL = new Set();
let worst = 99, worstName = '';
for (const d of data) {
  const o = oldColor(d.v), nn = out._ratioHsl(d.v, 'kics');
  const ink = out.textOnRatio(d.v, 'kics');
  const cr = contrast(lum(nn.h, nn.s, nn.l), ink);
  if (cr < worst) { worst = cr; worstName = d.n; }
  oldL.add(o.l.toFixed(1)); newL.add(nn.l.toFixed(1));
  console.log(d.n.padEnd(20) + d.v.toFixed(0).padStart(8) + o.l.toFixed(1).padStart(8)
    + nn.l.toFixed(1).padStart(8) + (ink === '#ffffff' ? '흰' : '검').padStart(9) + '  ' + cr.toFixed(2) + ':1');
}
console.log(`\n서로 다른 밝기 값: 옛 ${oldL.size}개 -> 새 ${newL.size}개`);
const oldClamp = data.filter(d => d.v >= 200).length, newClamp = data.filter(d => d.v >= 300).length;
console.log(`최진한 색으로 뭉친 회사(clamp): 옛 ${oldClamp}사 -> 새 ${newClamp}사`);
console.log(`최소 대비: ${worst.toFixed(2)}:1 (${worstName})  — WCAG AA 기준 4.5:1 ${worst >= 4.5 ? '통과' : '**미달**'}`);
