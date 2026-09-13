/* InsureQuant — theme.js (shared, all pages incl. jp/)
   다크 모드. 우선순위: 사용자가 토글로 고른 값(localStorage 'iq_theme') > OS 설정(prefers-color-scheme).
   <head> 에서 common.css 다음에 동기 로드한다 — body 가 그려지기 전에 <html data-theme> 을 박아야
   라이트→다크로 깜빡이지 않는다. 토큰 값 자체는 common.css(:root[data-theme]) 에 있고 여기는 스위치·
   차트 팔레트만 담당한다.

   페이지 쪽 계약:
     IQTheme.isDark()            현재 실효 테마
     IQTheme.chart()             차트용 색 묶음(계산된 CSS 변수) — 렌더 때마다 새로 읽을 것
     IQTheme.applyChartJs(Chart) Chart.defaults 의 색만 갱신(폰트는 페이지가 관리)
     IQTheme.echartsTooltip()    ECharts tooltip 색 옵션(formatter 와 Object.assign 해서 쓴다)
     window 'iq:themechange'     테마가 바뀌면 발생 — 페이지는 차트를 다시 그린다 */
(function(){
  var KEY='iq_theme';
  var root=document.documentElement;
  var mq=window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;

  function stored(){ try{ return localStorage.getItem(KEY); }catch(e){ return null; } }
  function store(v){ try{ v ? localStorage.setItem(KEY, v) : localStorage.removeItem(KEY); }catch(e){} }
  function systemDark(){ return !!(mq && mq.matches); }
  function effective(){ var s=stored(); return (s==='dark'||s==='light') ? s : (systemDark()?'dark':'light'); }
  function paint(){
    var s=stored();
    if(s==='dark'||s==='light') root.setAttribute('data-theme', s);
    else root.removeAttribute('data-theme');          /* 저장값 없음 = OS 를 따른다 */
    var b=document.getElementById('iqThemeToggle');
    if(b) decorate(b);
  }
  paint();

  function cssVar(name, fallback){
    var v=getComputedStyle(root).getPropertyValue(name).trim();
    return v || fallback;
  }
  function chart(){
    var dark=effective()==='dark';
    return {
      dark:dark,
      bg:cssVar('--bg','#ffffff'),
      card:cssVar('--card','#f8f9fa'),
      border:cssVar('--border','#e9ecef'),
      text:cssVar('--text','#212529'),
      muted:cssVar('--muted','#6a737a'),
      ink:cssVar('--ink-strong','#495057'),
      primary:cssVar('--primary','#0d6efd'),
      pos:cssVar('--pos','#16a34a'),
      neg:cssVar('--neg','#ef4444'),
      grid:cssVar('--border','#e9ecef'),
      tipBg:cssVar('--tip-bg','rgba(33,37,41,0.9)'),
      tipText:cssVar('--tip-text','#f8f9fa'),
      tipBorder:cssVar('--tip-border','rgba(33,37,41,0.9)')
    };
  }
  function applyChartJs(C){
    if(!C || !C.defaults) return;
    var t=chart();
    C.defaults.color=t.muted; C.defaults.borderColor=t.border;
    C.defaults.plugins.tooltip.backgroundColor=t.tipBg;
    C.defaults.plugins.tooltip.titleColor=t.tipText;
    C.defaults.plugins.tooltip.bodyColor=t.tipText;
    C.defaults.scale.grid.color=t.border; C.defaults.scale.ticks.color=t.muted;
  }
  function echartsTooltip(){
    var t=chart();
    return { backgroundColor:t.tipBg, borderColor:t.tipBorder, textStyle:{ color:t.tipText } };
  }

  var ja = (root.getAttribute('lang')||'').toLowerCase().indexOf('ja')===0;
  function decorate(b){
    var dark=effective()==='dark';
    b.textContent = dark ? '☀' : '☾';                 /* ☀ / ☾ */
    var label = ja ? (dark ? 'ライトモードに切替' : 'ダークモードに切替')
                   : (dark ? '라이트 모드로 전환' : '다크 모드로 전환');
    b.setAttribute('aria-label', label); b.title=label;
    b.setAttribute('aria-pressed', dark ? 'true' : 'false');
  }
  function fire(){
    paint();
    try{ window.dispatchEvent(new CustomEvent('iq:themechange', { detail:{ theme:effective() } })); }catch(e){}
  }
  function set(v){
    /* OS 설정과 같은 값을 고르면 저장값을 지워 계속 OS 를 따르게 한다 */
    store((v==='dark')===systemDark() ? null : v);
    fire();
  }
  function toggle(){ set(effective()==='dark' ? 'light' : 'dark'); }

  if(mq && mq.addEventListener) mq.addEventListener('change', function(){ if(!stored()) fire(); });

  function mount(){
    if(document.getElementById('iqThemeToggle')) return;
    var h=document.querySelector('header'); if(!h) return;
    var b=document.createElement('button');
    b.type='button'; b.id='iqThemeToggle'; b.className='theme-toggle';
    decorate(b);
    b.addEventListener('click', toggle);
    h.appendChild(b);
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', mount); else mount();

  window.IQTheme={ isDark:function(){ return effective()==='dark'; }, current:effective, set:set, toggle:toggle,
                   chart:chart, applyChartJs:applyChartJs, echartsTooltip:echartsTooltip };
})();
