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
      card:cssVar('--card','#f5f5f4'),
      border:cssVar('--border','#e4e4e2'),
      text:cssVar('--text','#18181b'),
      muted:cssVar('--muted','#63666b'),
      ink:cssVar('--ink-strong','#3f4347'),
      primary:cssVar('--primary','#0f6e68'),
      pos:cssVar('--pos','#4b7f2a'),
      neg:cssVar('--neg','#b4443a'),
      grid:cssVar('--border','#e4e4e2'),
      tipBg:cssVar('--tip-bg','rgba(24,24,27,0.92)'),
      tipText:cssVar('--tip-text','#f5f5f4'),
      tipBorder:cssVar('--tip-border','rgba(24,24,27,0.92)')
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

  /* ---- 섹션 네비 (KICS-SECTIONNAV, 2026-09-20 공통화) --------------------
     K-ICS 에만 있던 것을 IFRS17 과 공유하려고 여기로 올렸다. 세 가지를 한다:

     1) **헤더 높이를 실측해 `--iq-hdr-h` 로 내려 준다.** 종전에는 sticky top 을
        71px/88px 로 박아 뒀는데, 헤더가 줄바꿈되면(다운로드 버튼이 아래로 내려가는
        폭 구간) 네비가 그대로 헤더 뒤로 숨는다 — owner 가 본 "어떨 땐 되고 어떨 땐
        안 되는" 증상이 이것이다. 높이를 재서 쓰면 그 구간이 사라진다.
     2) **없는 섹션을 감추지 않고 "미공시" 로 남긴다**(owner 2026-09-20:
        "없는 사들은 없다고 띄우면 되지"). 항목이 사라지면 그 회사에 무엇이 없는지
        조차 알 수 없다.
     3) **내려갈 때 접고 올라갈 때 도로 꺼낸다**(좁은 화면 전용, 폭 판정은 CSS 가 한다).
        목록을 늘 띄워 두면 좁은 화면에서 본문을 계속 먹는다.                    */
  function hdrH(){
    var h=document.querySelector('header');
    return h ? Math.round(h.getBoundingClientRect().height) : 72;
  }
  function syncHdrVar(){
    document.documentElement.style.setProperty('--iq-hdr-h', hdrH() + 'px');
  }
  /* 패널이 **있는데 안이 비어 있는** 경우를 미공시로 본다. 그 회사에 데이터가 없으면 패널은
     그대로 복제되고 안에 "…미제공 보험사입니다" 안내(.stub-msg / .no-data)만 보인다 —
     높이만 재면 이걸 '있음' 으로 잘못 읽는다. 안내가 떠 있고 실제 표·차트가 없으면 미공시다. */
  function hasStub(el){
    var stubs = el.querySelectorAll('.stub-msg, .no-data, .placeholder-empty');
    for(var i = 0; i < stubs.length; i++){
      var s = stubs[i];
      if(s.getBoundingClientRect().height > 0 && (s.textContent || '').trim()) return true;
    }
    return false;
  }
  var _navPairs = [], _navActive = null, _lastY = 0;
  function syncSectionNav(){
    syncHdrVar();
    var nav = document.querySelector('.section-nav');
    if(!nav){ _navPairs = []; return; }
    _navPairs = [];
    [].slice.call(nav.querySelectorAll('a[href^="#"]')).forEach(function(a){
      var el = document.getElementById(a.getAttribute('href').slice(1));
      var live = !!(el && el.getBoundingClientRect().height > 0) && !hasStub(el);
      a.classList.toggle('is-na', !live);
      if(live){ a.removeAttribute('aria-disabled'); _navPairs.push({ a:a, el:el }); }
      else { a.setAttribute('aria-disabled', 'true'); a.classList.remove('is-current'); a.removeAttribute('aria-current'); }
    });
    _navActive = null;
    spySectionNav();
  }
  function spySectionNav(){
    if(!_navPairs.length) return;
    var anchor = hdrH() + 20, active = _navPairs[0];
    for(var i = 0; i < _navPairs.length; i++){
      if(_navPairs[i].el.getBoundingClientRect().top <= anchor) active = _navPairs[i];
    }
    // 문서 끝에 닿으면 마지막 섹션 — 마지막 패널이 짧아 앵커선을 못 넘는 경우가 있다.
    if(window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2){
      active = _navPairs[_navPairs.length - 1];
    }
    if(active === _navActive) return;   // 바뀔 때만 DOM 을 건드린다
    _navActive = active;
    _navPairs.forEach(function(p){
      var on = (p === active);
      p.a.classList.toggle('is-current', on);
      if(on) p.a.setAttribute('aria-current', 'true'); else p.a.removeAttribute('aria-current');
    });
  }
  function onNavScroll(){
    var nav = document.querySelector('.section-nav');
    if(nav){
      var y = window.scrollY, h = hdrH();
      if(y > _lastY + 6 && y > h + 80) nav.classList.add('is-tucked');
      else if(y < _lastY - 6 || y <= h) nav.classList.remove('is-tucked');
      _lastY = y;
    }
    spySectionNav();
  }
  /* rAF 로 묶지 않는다 — 백그라운드 탭에서 rAF 가 멈추면 스파이가 조용히 죽는다(실측).
     대상이 10개 미만이라 매 스크롤에 rect 를 재도 비용이 없고, 활성이 바뀔 때만 DOM 을 건드린다. */
  window.addEventListener('scroll', onNavScroll, { passive:true });
  window.addEventListener('resize', function(){ syncHdrVar(); _navActive = null; spySectionNav(); });

  /* **페이지마다 re-sync 를 배선하지 않는다.** 처음엔 IFRS17 에만 렌더 후 호출을 넣었는데,
     K-ICS 는 부팅 시점(보험사 미선택)에 안내문이 떠 있어 3개 섹션이 "미공시" 로 찍히고
     회사를 골라도 다시 재지 않아 그대로 남았다 — 라이브에서 owner 가 잡았다.
     어느 페이지든 본문이 바뀌면 다시 재도록 관찰자를 건다(디바운스 180ms). */
  var _navTimer = null;
  function watchForRerender(){
    var host = document.querySelector('.container') || document.body;
    if(!host || !window.MutationObserver) return;
    new MutationObserver(function(){
      clearTimeout(_navTimer);
      _navTimer = setTimeout(syncSectionNav, 180);
    }).observe(host, { childList:true, subtree:true, attributes:true,
                       attributeFilter:['style','class','hidden'] });
  }
  function boot(){ mount(); syncSectionNav(); watchForRerender(); }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', boot); else boot();

  window.IQTheme={ isDark:function(){ return effective()==='dark'; }, current:effective, set:set, toggle:toggle,
                   chart:chart, applyChartJs:applyChartJs, echartsTooltip:echartsTooltip,
                   syncSectionNav:syncSectionNav };
})();
