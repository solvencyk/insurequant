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
    if(!nav){ _navPairs = []; syncSecFab(); clampHelpPops(); return; }
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
    syncSecFab();
    clampHelpPops();
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
  /* 모바일(<=640px)에서는 접고 펴는 동작을 하지 않는다(owner 2026-10-08: "자꾸 숨김처리 돼서
     찾기 힘듬"). 거기서는 우하단 햄버거 FAB 가 섹션 바로가기를 맡고, 상단 네비는 CSS 가 감춘다. */
  var mqMobile = window.matchMedia ? window.matchMedia('(max-width:640px)') : null;
  function isMobileW(){ return !!(mqMobile && mqMobile.matches); }
  function onNavScroll(){
    var nav = document.querySelector('.section-nav');
    if(nav){
      var y = window.scrollY, h = hdrH();
      if(isMobileW()) nav.classList.remove('is-tucked');
      else if(y > _lastY + 6 && y > h + 80) nav.classList.add('is-tucked');
      else if(y < _lastY - 6 || y <= h) nav.classList.remove('is-tucked');
      _lastY = y;
    }
    spySectionNav();
    if(_secOpen) markSecActive();
  }
  /* rAF 로 묶지 않는다 — 백그라운드 탭에서 rAF 가 멈추면 스파이가 조용히 죽는다(실측).
     대상이 10개 미만이라 매 스크롤에 rect 를 재도 비용이 없고, 활성이 바뀔 때만 DOM 을 건드린다. */
  window.addEventListener('scroll', onNavScroll, { passive:true });
  window.addEventListener('resize', function(){
    syncHdrVar(); _navActive = null; spySectionNav();
    clampHelpPops();
    if(_secOpen && !isMobileW()) closeSec(false);
  });

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
  /* ---- 도움말(?) 팝오버가 가로로 삐져나가 문서를 넓히는 문제 (owner 2026-10-08) -------
     .iq-help-pop 은 숨겨져 있어도(opacity:0) 레이아웃에는 남는다. 트리거가 화면 오른쪽에 있으면
     팝오버가 viewport 밖으로 나가고, 모바일 브라우저는 이걸 따라 레이아웃 viewport 자체를 넓힌다
     (375px 에서 문서 폭 662px 실측). 그러면 오른쪽 끝에 고정된 "오류 제보" 버튼과 모달이 화면
     밖으로 밀려 "오른쪽으로 넘겨야 튀어나오는" 증상이 된다. 열 때가 아니라 **항상** 화면 안으로
     밀어 둔다. 값이 안 바뀌면 쓰지 않는다 — 아래 MutationObserver 가 style 변경을 듣기 때문. */
  function clampHelpPops(){
    var pops = document.querySelectorAll('.iq-help-pop');
    if(!pops.length) return;
    var vw = document.documentElement.clientWidth, M = 8, i, r, cur, s, left, right, shifts = [];
    for(i = 0; i < pops.length; i++){
      r = pops[i].getBoundingClientRect(); cur = pops[i]._iqShift || 0; s = 0;
      if(r.width > 0){
        left = r.left - cur; right = r.right - cur;
        if(right > vw - M) s = vw - M - right;
        if(left + s < M) s = M - left;
        s = Math.round(s);
      }
      shifts.push(s);
    }
    for(i = 0; i < pops.length; i++){
      cur = pops[i]._iqShift || 0;
      if(shifts[i] !== cur){
        pops[i]._iqShift = shifts[i];
        pops[i].style.transform = shifts[i] ? 'translateX(' + shifts[i] + 'px)' : '';
      }
    }
  }
  document.addEventListener('pointerenter', function(e){ if(e.target && e.target.closest && e.target.closest('.iq-help')) clampHelpPops(); }, true);
  document.addEventListener('focusin', function(e){ if(e.target && e.target.closest && e.target.closest('.iq-help')) clampHelpPops(); });

  /* ---- 모바일 섹션 바로가기 FAB (owner 2026-10-08) --------------------------------
     우하단 햄버거 버튼 -> 위로 열리는 시트. 상단 가로 네비(.section-nav)는 스크롤하면 숨어
     찾기 어려워서 모바일에서는 CSS 가 감추고 이 버튼이 대신한다(폭 판정은 전부 CSS).
     항목의 출처(계약):
       (a) .section-nav a[href^="#"]  — is-na 는 흐리게 '미공시', 누를 수 없음
       (b) 그런 네비가 없는 페이지: id 와 data-section-label 이 둘 다 있는 요소(값=라벨).
           렌더되지 않은(높이 0) 요소는 목록에서 뺀다.
     항목이 2개 미만이거나 누를 수 있는 항목이 없으면 만들지도 보이지도 않는다. */
  var _secFab = null, _secSheet = null, _secSig = '', _secOpen = false, _secItems = [];
  function secItems(){
    var out = [], nav = document.querySelector('.section-nav');
    if(nav){
      [].slice.call(nav.querySelectorAll('a[href^="#"]')).forEach(function(a){
        var id = (a.getAttribute('href') || '').slice(1); if(!id) return;
        var label = (a.textContent || '').trim(); if(!label) return;
        out.push({ id:id, el:document.getElementById(id), label:label, na:a.classList.contains('is-na') });
      });
    } else {
      [].slice.call(document.querySelectorAll('[id][data-section-label]')).forEach(function(el){
        var label = (el.getAttribute('data-section-label') || '').trim(); if(!label) return;
        if(!(el.getBoundingClientRect().height > 0) || hasStub(el)) return;
        out.push({ id:el.id, el:el, label:label, na:false });
      });
    }
    return out;
  }
  function secEl(tag, cls){ var e = document.createElement(tag); if(cls) e.className = cls; return e; }
  function ensureSecFab(){
    if(_secFab || !document.body) return;
    _secFab = secEl('button', 'iq-secnav-fab');
    _secFab.type = 'button'; _secFab.id = 'iqSecFab';
    _secFab.setAttribute('aria-label', '섹션 바로가기');
    _secFab.setAttribute('aria-expanded', 'false');
    _secFab.setAttribute('aria-controls', 'iqSecSheet');
    _secFab.innerHTML = '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" focusable="false">'
      + '<path d="M4 7h16M4 12h16M4 17h16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>';
    _secSheet = secEl('nav', 'iq-secnav-sheet');
    _secSheet.id = 'iqSecSheet'; _secSheet.hidden = true;
    _secSheet.setAttribute('aria-label', '섹션 바로가기');
    _secFab.addEventListener('click', function(){ if(_secOpen) closeSec(true); else openSec(); });
    _secSheet.addEventListener('click', function(e){
      var a = e.target.closest ? e.target.closest('a[data-sec]') : null;
      if(!a) return;
      e.preventDefault();
      goSec(a.getAttribute('data-sec'));
    });
    document.body.appendChild(_secFab);
    document.body.appendChild(_secSheet);
    /* 바깥을 누르거나 Esc 로 닫는다 — capture 라 페이지가 이벤트를 삼켜도 닫힌다. */
    document.addEventListener('pointerdown', function(e){
      if(!_secOpen) return;
      if(_secSheet.contains(e.target) || _secFab.contains(e.target)) return;
      closeSec(false);
    }, { capture:true, passive:true });
    document.addEventListener('keydown', function(e){ if(_secOpen && e.key === 'Escape'){ e.preventDefault(); closeSec(true); } });
  }
  function renderSecSheet(items){
    _secSheet.textContent = '';
    var t = secEl('div', 'iq-secnav-title'); t.textContent = '섹션 바로가기'; t.setAttribute('aria-hidden', 'true');
    var ul = secEl('ul');
    items.forEach(function(it){
      var li = secEl('li'), n;
      if(it.na){
        n = secEl('span', 'iq-secnav-item is-na'); n.setAttribute('aria-disabled', 'true');
        n.textContent = it.label + ' ';
        var tag = secEl('small'); tag.textContent = '미공시'; n.appendChild(tag);
      } else {
        n = secEl('a', 'iq-secnav-item'); n.href = '#' + it.id; n.setAttribute('data-sec', it.id);
        n.textContent = it.label;
      }
      li.appendChild(n); ul.appendChild(li);
    });
    _secSheet.appendChild(t); _secSheet.appendChild(ul);
  }
  function syncSecFab(){
    var items = secItems(), live = items.filter(function(it){ return !it.na; });
    var show = items.length >= 2 && live.length >= 1;
    if(!show){
      if(_secFab){ _secFab.hidden = true; if(_secOpen) closeSec(false); }
      document.documentElement.classList.remove('iq-has-secfab');
      _secItems = [];
      return;
    }
    ensureSecFab();
    _secItems = items;
    _secFab.hidden = false;
    document.documentElement.classList.add('iq-has-secfab');
    var sig = items.map(function(it){ return it.id + '|' + it.label + '|' + (it.na ? 1 : 0); }).join('\n');
    if(sig !== _secSig){ _secSig = sig; renderSecSheet(items); if(_secOpen) markSecActive(); }
  }
  function markSecActive(){
    if(!_secSheet) return;
    var anchor = hdrH() + 20, active = null, i, it;
    for(i = 0; i < _secItems.length; i++){
      it = _secItems[i];
      if(it.na || !it.el) continue;
      if(!active) active = it;
      if(it.el.getBoundingClientRect().top <= anchor) active = it;
    }
    if(active && window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2){
      for(i = _secItems.length - 1; i >= 0; i--){ if(!_secItems[i].na && _secItems[i].el){ active = _secItems[i]; break; } }
    }
    var id = active ? active.id : null;
    [].slice.call(_secSheet.querySelectorAll('a[data-sec]')).forEach(function(a){
      var on = a.getAttribute('data-sec') === id;
      a.classList.toggle('is-current', on);
      if(on) a.setAttribute('aria-current', 'location'); else a.removeAttribute('aria-current');
    });
  }
  function openSec(){
    if(!_secFab || _secFab.hidden) return;
    _secOpen = true; _secSheet.hidden = false;
    _secFab.setAttribute('aria-expanded', 'true');
    markSecActive();
    var cur = _secSheet.querySelector('a.is-current') || _secSheet.querySelector('a[data-sec]');
    if(cur){
      try{ cur.focus({ preventScroll:true }); }catch(e){ cur.focus(); }
      if(cur.scrollIntoView) cur.scrollIntoView({ block:'nearest' });
    }
  }
  function closeSec(returnFocus){
    if(!_secSheet) return;
    _secOpen = false; _secSheet.hidden = true;
    _secFab.setAttribute('aria-expanded', 'false');
    if(returnFocus){ try{ _secFab.focus(); }catch(e){} }
  }
  function goSec(id){
    var t = id ? document.getElementById(id) : null;
    closeSec(false);
    if(!t) return;
    var reduce = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
    /* scrollIntoView 는 html 의 scroll-padding-top(헤더 높이+12px)을 반영한다. 해시는 건드리지 않는다
       (compare.html 처럼 주소를 상태로 쓰는 페이지가 있다). */
    t.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block:'start' });
    if(!t.hasAttribute('tabindex')) t.setAttribute('tabindex', '-1');
    try{ t.focus({ preventScroll:true }); }catch(e){}
  }

  /* ---- 차트 툴팁 바깥 탭으로 닫기 (owner 2026-10-08) ----------------------------------
     터치에는 mouseout 이 없어 한 번 탭해 뜬 툴팁이 영영 안 닫히고 차트를 가린다. 터치/펜으로
     차트 **바깥**을 누르면 그 차트의 활성 요소와 툴팁을 비운다. 마우스는 건드리지 않는다(hover 가
     이미 알아서 닫는다). Chart.js(전역 Chart.instances)와 ECharts(echarts.getInstanceByDom) 모두.
     차트 안을 탭하는 동작은 그대로 라이브러리가 처리한다.                                          */
  function hideChartTips(target){
    var k, c, act, tip;
    if(window.Chart && window.Chart.instances){
      for(k in window.Chart.instances){
        c = window.Chart.instances[k];
        if(!c || !c.canvas || !c.tooltip) continue;
        if(c.canvas === target || c.canvas.contains(target)) continue;
        try{
          act = c.getActiveElements ? c.getActiveElements() : [];
          tip = c.tooltip.getActiveElements ? c.tooltip.getActiveElements() : [];
          if((act && act.length) || (tip && tip.length)){
            c.setActiveElements([]);
            c.tooltip.setActiveElements([], { x:0, y:0 });
            c.update('none');
          }
        }catch(e){}
      }
    }
    if(window.echarts && window.echarts.getInstanceByDom){
      var boxes = document.querySelectorAll('.echarts, [_echarts_instance_]'), i, inst;
      for(i = 0; i < boxes.length; i++){
        if(boxes[i] === target || boxes[i].contains(target)) continue;
        try{
          inst = window.echarts.getInstanceByDom(boxes[i]);
          if(inst){ inst.dispatchAction({ type:'hideTip' }); inst.dispatchAction({ type:'downplay' }); }
        }catch(e){}
      }
    }
  }
  document.addEventListener('pointerdown', function(e){
    if(e.pointerType === 'mouse') return;
    hideChartTips(e.target);
  }, { capture:true, passive:true });

  /* ---- 공유 메뉴 (owner 2026-10-08): 링크 복사 · 현재 페이지 스크린샷 ----------------------
     헤더 우상단, 테마 토글 왼쪽. 사이트 전 페이지 공통(일본어 jp/ 페이지는 제외).
     html2canvas 는 스크린샷을 누를 때만 SRI 로 불러온다(평소 로딩 영향 없음). scripts/compute_sri.py 에 등재.
     페이지가 조정하고 싶으면 window.IQShareConfig = { container:'.container', ignore:['.add-wrap', ...] } 를
     (누르는 시점에 읽는다) 둔다. ignore 는 스크린샷에서 뺄 요소 선택자.                                  */
  var H2C_URL = 'https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js';
  var H2C_SRI = 'sha384-ZZ1pncU3bQe8y31yfZdMFdSpttDoPmOZg2wguVK9almUodir1PghgT0eY7Mrty8H';
  var _shToastTimer = null;
  function shToast(t){
    var el = document.getElementById('iqToast');
    if(!el){
      el = document.createElement('div'); el.id = 'iqToast'; el.className = 'iq-toast';
      el.setAttribute('role', 'status'); el.setAttribute('aria-live', 'polite'); el.hidden = true;
      document.body.appendChild(el);
    }
    el.textContent = t; el.hidden = false;
    clearTimeout(_shToastTimer); _shToastTimer = setTimeout(function(){ el.hidden = true; }, 2600);
  }
  function shCopyLink(){
    var u = new URL(location.href); u.searchParams.delete('iq_internal');
    var link = u.toString().replace(/%2C/gi, ',');
    var done = function(){ shToast('링크를 복사했습니다'); };
    if(navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(link).then(done, function(){ window.prompt('링크를 복사하세요', link); });
    else window.prompt('링크를 복사하세요', link);
  }
  function shLoadH2C(ok){
    if(window.html2canvas){ ok(); return; }
    var s = document.createElement('script'); s.src = H2C_URL; s.integrity = H2C_SRI; s.crossOrigin = 'anonymous';
    s.onload = ok; s.onerror = function(){ shToast('이미지 저장 도구를 불러오지 못했습니다'); };
    document.head.appendChild(s);
  }
  function shSave(blob){
    var name = 'insurequant-' + (location.pathname.split('/').pop().replace(/\.html$/, '') || 'index') + '-' + new Date().toISOString().slice(0, 10) + '.png';
    function download(){
      var a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name;
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(function(){ URL.revokeObjectURL(a.href); }, 4000); shToast('이미지를 저장했습니다');
    }
    var file = null; try{ file = new window.File([blob], name, { type:'image/png' }); }catch(e){}
    var touch = window.matchMedia && window.matchMedia('(pointer:coarse)').matches;
    if(touch && file && navigator.share && navigator.canShare && navigator.canShare({ files:[file] })){
      navigator.share({ files:[file], title:document.title }).then(function(){}, function(e){ if(!e || e.name !== 'AbortError') download(); });
    } else download();
  }
  function shShot(){
    var cfg = window.IQShareConfig || {};
    shToast('이미지를 만드는 중…');
    shLoadH2C(function(){
      var root = document.querySelector(cfg.container || '.container') || document.body;
      /* 짧은 페이지는 본문 전체, 아주 긴 페이지(표·차트 수십 장)는 캔버스 한도 때문에 지금 화면만 */
      var full = root !== document.body && root.scrollHeight <= 6000;
      var ign = ['.iq-report-fab', '.iq-secnav-fab', '.iq-secnav-sheet', '.iq-share', '.iq-toast', '.iq-modal-backdrop', '.theme-toggle', '.iq-help']
        .concat(cfg.ignore || []).join(',');
      var scale = Math.min(2, window.devicePixelRatio || 1), bg = getComputedStyle(document.body).backgroundColor;
      var opt = { backgroundColor:bg, scale:scale, useCORS:true, logging:false, windowWidth:document.documentElement.clientWidth,
        ignoreElements:function(el){ return !!(el.matches && el.matches(ign)); },
        /* 아직 화면에 안 들어와 투명(.will-reveal)이거나 나타나는 중인 패널도 또렷하게 찍는다 */
        onclone:function(doc){
          [].forEach.call(doc.querySelectorAll('.will-reveal, .revealed'), function(el){ el.style.opacity = '1'; el.style.transform = 'none'; el.style.animation = 'none'; });
          if(typeof cfg.onclone === 'function') cfg.onclone(doc);
        } };
      if(!full){ opt.x = window.scrollX; opt.y = window.scrollY; opt.width = window.innerWidth; opt.height = window.innerHeight; opt.windowHeight = window.innerHeight; }
      window.html2canvas(full ? root : document.body, opt).then(function(cv){
        /* 출처 한 줄을 아래에 붙인다 */
        var pad = Math.round(30 * scale), out = document.createElement('canvas');
        out.width = cv.width; out.height = cv.height + pad;
        var c = out.getContext('2d'); c.fillStyle = bg; c.fillRect(0, 0, out.width, out.height); c.drawImage(cv, 0, 0);
        c.fillStyle = chart().muted; c.font = Math.round(12 * scale) + 'px ' + getComputedStyle(document.body).fontFamily; c.textBaseline = 'middle';
        c.fillText('InsureQuant · www.insurequant.com' + location.pathname.replace(/\/index\.html$/, '/') + ' · ' + new Date().toISOString().slice(0, 10) + ' · 공시자료를 가공한 값이며 오류가 있을 수 있습니다', Math.round(14 * scale), cv.height + pad / 2);
        out.toBlob(function(b){ if(b) shSave(b); else shToast('이미지를 만들지 못했습니다'); }, 'image/png');
      }, function(){ shToast('이미지를 만들지 못했습니다'); });
    });
  }
  function mountShare(){
    if(ja) return;
    if(document.getElementById('iqShareBtn') || document.getElementById('share-btn')) return;   /* 페이지가 자체 메뉴를 이미 가진 경우 */
    var h = document.querySelector('header'); if(!h) return;
    var wrap = document.createElement('div'); wrap.className = 'iq-share'; wrap.id = 'iqShare';
    var btn = document.createElement('button');
    btn.type = 'button'; btn.id = 'iqShareBtn'; btn.className = 'iq-share-btn';
    btn.setAttribute('aria-haspopup', 'menu'); btn.setAttribute('aria-expanded', 'false'); btn.setAttribute('aria-controls', 'iqShareMenu');
    btn.setAttribute('aria-label', '공유'); btn.title = '공유';
    btn.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false"><path d="M8.4 10.9l7.2-4.1M8.4 13.1l7.2 4.1" stroke="currentColor" stroke-width="1.6" fill="none" stroke-linecap="round"/><g fill="currentColor"><circle cx="18" cy="5.5" r="2.7"/><circle cx="6" cy="12" r="2.7"/><circle cx="18" cy="18.5" r="2.7"/></g></svg>';
    var menu = document.createElement('ul');
    menu.className = 'iq-share-menu'; menu.id = 'iqShareMenu'; menu.setAttribute('role', 'menu'); menu.setAttribute('aria-label', '공유'); menu.hidden = true;
    [['링크 복사', shCopyLink], ['현재 페이지 스크린샷', shShot]].forEach(function(it){
      var li = document.createElement('li'); li.setAttribute('role', 'none');
      var b = document.createElement('button'); b.type = 'button'; b.setAttribute('role', 'menuitem'); b.textContent = it[0];
      b.addEventListener('click', function(){ close(); if(it[1] === shShot) btn.focus(); it[1](); });
      li.appendChild(b); menu.appendChild(li);
    });
    function items(){ return [].slice.call(menu.querySelectorAll('[role=menuitem]')); }
    function close(){ menu.hidden = true; btn.setAttribute('aria-expanded', 'false'); }
    function open(){ menu.hidden = false; btn.setAttribute('aria-expanded', 'true'); items()[0].focus(); }
    btn.addEventListener('click', function(e){ e.stopPropagation(); if(menu.hidden) open(); else close(); });
    document.addEventListener('click', function(e){ if(!menu.hidden && !wrap.contains(e.target)) close(); });
    document.addEventListener('keydown', function(e){ if(e.key === 'Escape' && !menu.hidden){ close(); btn.focus(); } });
    menu.addEventListener('keydown', function(e){
      if(e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
      e.preventDefault(); var it = items(), k = it.indexOf(document.activeElement);
      it[(k + (e.key === 'ArrowDown' ? 1 : it.length - 1)) % it.length].focus();
    });
    wrap.appendChild(btn); wrap.appendChild(menu); h.appendChild(wrap);
    h.classList.add('has-share');
  }

  function boot(){ mount(); mountShare(); syncSectionNav(); watchForRerender(); }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', boot); else boot();

  window.IQTheme={ isDark:function(){ return effective()==='dark'; }, current:effective, set:set, toggle:toggle,
                   chart:chart, applyChartJs:applyChartJs, echartsTooltip:echartsTooltip,
                   syncSectionNav:syncSectionNav };
})();
