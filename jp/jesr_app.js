/* jp/jesr_app.js — 회사별 상세 3페이지 공용 스크립트 (2026-09-13 분리, 종전 jesr.html 인라인).
   페이지는 <body data-page="esr|jgaap|disclosure"> 로 자기 정체를 알리고, 각 render 함수는 자기 컨테이너가 없는
   페이지에서는 그냥 돌아간다(byId 가드). 회사 선택·URL ?company=·탭 링크 동기화는 3페이지 공통.
   owner 2026-09-13: 所要資本 워터폴 폐지(분산효과 △만 보여주는 그래프), 규정 재현 배지는 適格資本・所要資本 표 제목으로 이동. */
(function(){
  'use strict';
  var PAGE = (document.body && document.body.dataset.page) || 'esr';
  var PAGE_TITLE = { esr:'ESR詳細', jgaap:'決算(J-GAAP)', disclosure:'その他開示' };
  var PAGE_FILE = { esr:'jesr.html', jgaap:'jgaap.html', disclosure:'disclosure.html' };
  function byId(id){ return document.getElementById(id); }
  function setHidden(id, v){ var el = byId(id); if(el) el.hidden = v; }
  var PRIMARY_URL = 'jesr_detail.json';
  var FIXTURE_URL = '_fixture_jesr_detail.json';

  var SCOPE_LABEL = {group:'連結', solo:'単体'};
  // jp/index.html と同じ算定基準ラベル(owner 2026-09-13、§5.2 관례대로 공유 모듈 없이 파일별 복사).
  // ESRページ(secHeadline)のみで使う — 決算・その他開示ページはESR算定基準と無関係なので出さない。
  var BASIS_LABEL = { regulatory_standard:'規制ベース', internal_model:'内部モデル', internal_management:'内部管理' };
  function basisLabel(basis){ return BASIS_LABEL[basis] || '未確認'; }

  // data_scope(publishing 계약, 2026-09-14): "ratio_only" 회사는 profit.ratios/history.series の
  // hist_*_ratio_pct 3종만 값이 있고 capital/items/sensitivity/risk/market_sub/bs/by_line は
  // 全部空(既存の"not_yet"部分会社と同じ表現)。既存10社は"full"(またはフィールドなし)。
  function isRatioOnly(c){ return !!c && c.data_scope === 'ratio_only'; }
  // ページごとに文言が違う一行案内 — 空パネルを黙って消すだけでなく「なぜ無いか」を必ず一言残す
  // (claude-agent-designer.md の反省: 空⇔壊れているは画面上で区別できないといけない)。__ID__は会社idに置換。
  var RATIO_ONLY_NOTE = {
    esr: 'このページ（ESR詳細）は損害率系の指標のみ収録しています。適格資本・所要資本・感応度は、規制様式(告示)に基づく本編開示の取得後に追加します。損害率・事業費率・合算率は<a href="jgaap.html?company=__ID__">「決算」タブ</a>でご覧いただけます。',
    jgaap: 'このページは損害率系の指標(損害率・事業費率・合算率)のみ収録しています。損益の内訳・貸借対照表・種目別は本編開示の取得後に追加します。下の「収益性指標」をご覧ください。',
    disclosure: 'この会社は損害率系の指標のみ収録しています。再保険の依存度等その他開示は本編開示の取得後に追加します。損害率は<a href="jgaap.html?company=__ID__">「決算」タブ</a>でご覧いただけます。'
  };
  function renderScopeNote(c, ratioOnly){
    var wrap = byId('scopeNoteWrap'); if(!wrap) return;
    if(!ratioOnly){ wrap.hidden = true; return; }
    wrap.hidden = false;
    var tpl = RATIO_ONLY_NOTE[PAGE] || '';
    byId('scopeNoteText').innerHTML = tpl.replace(/__ID__/g, encodeURIComponent(c.id || c.company_jp));
  }

  // ratio_caveat(4種、2026-09-14): 値そのものは他社と同じ列・同じ並びに置いたまま、脇に付ける表示専用の
  // 印。性格が違う3グループ(算式差=formula／画像判読の精度=read／重複計上=dup)ごとに枠線の形と頭字を変え、
  // 色だけに頼らない(a11y、jp.css の .caveat-badge*)。4コードを一括りにしない — 個々のラベル文言も違う。
  var CAVEAT_META = {
    lae_excluded: { cat:'formula', mark:'Δ', label:'算式差(損調費除く)' },
    ei_basis:     { cat:'formula', mark:'Δ', label:'E.I.基準' },
    ocr_read:     { cat:'read',    mark:'OCR', label:'画像判読' },
    simple_sum:   { cat:'dup',     mark:'Σ', label:'単純合算' }
  };
  function caveatBadgeHtml(caveat){
    if(!caveat || !caveat.code) return '';
    var m = CAVEAT_META[caveat.code] || { cat:'formula', mark:'△', label:'要確認' };
    return ' <span class="caveat-badge caveat-badge--'+m.cat+'" title="'+esc(caveat.text||m.label)+'">'+esc(m.mark)+' '+esc(m.label)+'</span>';
  }

  // value_verified(publishing 계약, 2026-09-14 신설 — PM-2026-09-13 T&D 222%/東京海上HD 238/MS&AD/
  // かんぽ 220 사고 후속, UH-25). "검증 못 함"과 "검증 통과"가 화면에서 같은 모양이면 안 된다.
  // caveat-badge 는 "값은 검증됐지만 다른 회사와 단순비교 주의"고, 이건 "값 자체를 그 출처 문서
  // 안에서 확인하지 못했다"로 성격이 다르다 — 그래서 같은 배지 "언어"(작은 표식+title 툴팁, 색만으로
  // 구분 안 함)는 쓰되 실루엣은 확실히 다르게 한다(둥근 pill 한 겹이 아니라 아이콘칩+굵은 테두리).
  // state: "verified"(정상, 배지 없음) | "unverified"(검증 못 함, 값이 틀렸다는 뜻 아님) |
  // "exempt"(owner 면제 등재, reason 에 등재 사유) | null/필드 없음(이 축 대상 아님, ratio_only의
  // ESR 등 — 역시 배지 없음). reason 은 publishing 이 게이트 정본에서 뽑아 넣은 문자열 그대로
  // title 에 노출한다 — designer 가 다시 쓰지 않는다.
  var VERIFY_META = {
    unverified: { cat:'unverified', mark:'?', label:'値 未検証' },
    exempt:     { cat:'exempt',     mark:'免', label:'確認対象外' }
  };
  function verifyBadgeHtml(vv){
    if(!vv || !vv.state || vv.state === 'verified') return '';
    var m = VERIFY_META[vv.state] || VERIFY_META.unverified;
    var tip = vv.reason ? (m.label+'：'+vv.reason) : m.label;
    return ' <span class="verify-badge verify-badge--'+m.cat+'" title="'+esc(tip)+'"><span class="vb-ic" aria-hidden="true">'+esc(m.mark)+'</span><span class="vb-tx">'+esc(m.label)+'</span></span>';
  }

  // jp/index.html 313~320행과 동일한 2단 버킷 정렬(inbox 20260912T1420Z, 공유 JS 파일 없음 —
  // §5.2 관례대로 각 파일에 복사). 드롭다운(ENTRIES) 정렬에 쓴다.
  function isBucketA(category){ return /^(HD上場|相互会社|上場)/.test(category||''); }
  function sortBucketed(list){
    return list.slice().sort(function(a,b){
      var ba = isBucketA(a.category) ? 0 : 1, bb = isBucketA(b.category) ? 0 : 1;
      if(ba !== bb) return ba - bb;
      return (b.esr_pct||0) - (a.esr_pct||0);
    });
  }

  // jp/index.html 217~235행과 동일한 발산색상 스케일(base=100 감독기준, strong=300).
  var RATIO_SCALE = { esr: { base: 100, strong: 300 } };
  function _ratioHsl(r){
    var ratio = (typeof r === 'number' && isFinite(r)) ? r : 0;
    var scale = RATIO_SCALE.esr, base = scale.base, strong = scale.strong;
    var up = ratio >= base;
    var span = up ? (strong - base) : base;
    var i = Math.min(Math.max(up ? (ratio - base) : (base - ratio), 0) / span, 1);
    return { h: up ? 130 : 0, s: 28 + 38 * i, l: 62 - 38 * i };
  }
  function colorForRatio(r){ var c=_ratioHsl(r); return 'hsl('+c.h+','+c.s+'%,'+c.l+'%)'; }

  function esc(s){
    return String(s==null?'':s).replace(/[&<>"']/g, function(c){
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
    });
  }
  // 억엔 환산(백만엔÷100) 1자리, 음수는 △(세모, 한국 회계 관례 — claude-agent-designer.md).
  function fmtEok(v){
    if(v==null || !isFinite(v)) return '—';
    var eok = v/100, sign = eok<0 ? '△' : '';
    return sign + Math.abs(eok).toLocaleString('ja-JP',{minimumFractionDigits:1,maximumFractionDigits:1});
  }
  // 損益内訳表の増減列(億円)用。fmtEokと違い正の増減にも+符号を付ける(pp用fmtPPと同じ発想)。
  function fmtEokDelta(cur, prev){
    if(cur==null || prev==null) return '—';
    var d = cur - prev;
    if(d===0) return '±0.0';
    var eok = d/100, sign = eok<0 ? '△' : '+';
    return sign + Math.abs(eok).toLocaleString('ja-JP',{minimumFractionDigits:1,maximumFractionDigits:1});
  }
  function fmtMillionTip(v){
    if(v==null) return '';
    return v.toLocaleString('ja-JP') + '百万円';
  }
  function fmtPct1(v){
    if(v==null || !isFinite(v)) return '—';
    var sign = v<0 ? '△' : '';
    return sign + Math.abs(v).toFixed(1) + '%';
  }
  function fmtPP(v){
    if(v==null || !isFinite(v)) return '—';
    if(v===0) return '±0.0pp';
    var sign = v<0 ? '△' : '+';
    return sign + Math.abs(v).toFixed(1) + 'pp';
  }
  function jaDate(iso){
    if(!iso) return '—';
    var p = String(iso).split('-');
    if(p.length>=3) return p[0]+'年'+parseInt(p[1],10)+'月'+parseInt(p[2],10)+'日';
    return String(iso);
  }
  // owner 2026-09-12 정정: 基準日(as_of)은 날짜 그대로 쓰면 한국식 "2026.1Q" 표기와 헷갈려
  // 일본 독자가 역월(4~6월)로 잘못 읽는다(일본 회계연도는 4월 시작) — jp/index.html 과 동일
  // 규칙으로 일본 회계연도 분기 표기로 바꾸고, 실제 날짜는 title 툴팁으로만 노출한다.
  function jaFiscalQuarter(iso){
    if(!iso) return null;
    var p = String(iso).split('-');
    var y = parseInt(p[0],10), m = parseInt(p[1],10);
    var fy, q;
    if(m>=1 && m<=3){ fy = y-1; q = 4; }
    else if(m<=6){ fy = y; q = 1; }
    else if(m<=9){ fy = y; q = 2; }
    else { fy = y; q = 3; }
    return fy + '年度 ' + q + 'Q';
  }
  function labelOf(meta, id, fallback){
    var l = meta.labels && meta.labels[id];
    return (l && l.ja) ? l.ja : (fallback || id);
  }
  // jp/index.html jaOnly() 그대로(244~254행) — publishing 파이프라인의 내부 한국어 메모가
  // doc_type 같은 자유텍스트 필드에 섞여 들어오는 사례가 실측됐다(au_nonlife doc_type:
  // "…, 업적데이터편, 2026-07-30 발행)" — 화면 표시 직전에만 한글 토큰을 제거, 원본 JSON은 안 건드림.
  function jaOnly(s){
    if(!s) return s;
    return String(s)
      .replace(/[가-힣]+/g, '')
      .replace(/,\s*,/g, ',')
      .replace(/\(\s*,/g, '(')
      .replace(/,\s*\)/g, ')')
      .replace(/\(\s*\)/g, '')
      .replace(/\s{2,}/g, ' ')
      .trim();
  }

  // ---- 데이터 로드: 계약 파일이 없으면(publishing 병행작업 중) 임시 fixture로 폴백.
  // 진짜 jesr_detail.json 이 생기면 이 fetch 가 그대로 성공해 fixture 는 자동으로 안 쓰인다
  // (inbox 20260912T1120Z 지시: fixture는 publishing 결과물 도착 후 삭제).
  function loadDetail(){
    return fetch(PRIMARY_URL, {cache:'no-store'})
      .then(function(r){ if(!r.ok) throw new Error('http '+r.status); return r.json(); })
      .catch(function(){
        return fetch(FIXTURE_URL, {cache:'no-store'})
          .then(function(r){ if(!r.ok) throw new Error('fixture http '+r.status); return r.json(); });
      });
  }
  // jp/index.html 이 쓰는 헤드라인 13사(jesr_esr.json) — 여기서는 드롭다운 확장(상세 없는
  // 회사의 기본 페이지)에 쓴다. publishing 산출물, 읽기 전용(inbox 20260912T1420Z).
  var ESR_URL = 'jesr_esr.json';
  function loadEsr(){
    return fetch(ESR_URL, {cache:'no-store'})
      .then(function(r){ if(!r.ok) throw new Error('http '+r.status); return r.json(); })
      .catch(function(err){ console.error('jesr_esr.json load failed', err); return {records:[]}; });
  }

  var DATA = null, META = null, ENTRIES = [], profitWaterfallChart = null;
  var CURRENT = null;   // 마지막으로 그린 entry — 테마 전환 시 그대로 다시 그린다
  var TH = window.IQTheme ? IQTheme.chart() : { text:'#212529', muted:'#6c757d', ink:'#495057', bg:'#fff', grid:'#e9ecef' };
  var TOGGLE_IDS = ['secCapitalWrap','secCapLimitsWrap','secSensWrap','secDurWrap','secBsWrap','secProfitWrap','secProfitabilityWrap','secReservesWrap','secReinsWrap','secAxesWrap'];

  Promise.all([loadDetail(), loadEsr()]).then(function(res){ boot(res[0], res[1]); }).catch(function(err){
    document.getElementById('mainRoot').innerHTML =
      '<div class="jp-err">データを読み込めませんでした。時間をおいて再度お試しください。</div>';
    console.error('jesr_detail.json load failed', err);
  });

  // ENTRIES = 드롭다운 14사(헤드라인13 + 상세만 있는 明治安田損保). key = 상세(jesr_detail.json)
  // 가 있으면 그 id, 없으면 company_jp 그대로(옵션 value 는 URLSearchParams 가 자동 인코딩/
  // 디코딩하므로 encodeURIComponent 를 여기서 또 하지 않는다 — jp/index.html 쪽 링크는 href
  // 문자열 조립이라 거기서만 encodeURIComponent 한다). 정렬 = jp/index.html 과 동일 2단 버킷 +
  // ESR desc, 상세만 있는 회사는 맨 뒤(inbox 20260912T1420Z).
  var ESR_META = null;
  function boot(detailData, esrData){
    DATA = detailData; META = detailData._meta || {}; ESR_META = (esrData && esrData._meta) || {};
    var detailCompanies = detailData.companies || [];
    var esrRecords = Array.isArray(esrData.records) ? esrData.records : [];
    var detailByEn = {};
    detailCompanies.forEach(function(d){ if(d.company_en) detailByEn[d.company_en] = d; });
    var usedIds = {};
    var entries = sortBucketed(esrRecords).map(function(r){
      var d = r.company_en ? detailByEn[r.company_en] : null;
      if(d) usedIds[d.id] = true;
      return { key: d ? d.id : r.company_jp, company_jp: r.company_jp, company_en: r.company_en,
        mode: d ? 'detail' : 'headline', detail: d || null, headlineRec: r };
    });
    detailCompanies.forEach(function(d){
      if(!usedIds[d.id]){
        entries.push({ key: d.id, company_jp: d.company_jp, company_en: d.company_en, mode: 'detail', detail: d, headlineRec: null });
      }
    });
    ENTRIES = entries;

    var sel = document.getElementById('companySelect');
    sel.disabled = false;
    sel.innerHTML = entries.map(function(e){
      return '<option value="'+esc(e.key)+'">'+esc(e.company_jp)+(e.company_en?'（'+esc(e.company_en)+'）':'')+'</option>';
    }).join('');
    sel.addEventListener('change', function(){
      var e = findEntry(sel.value);
      if(e) selectEntry(e, true); else showNotFound();
    });

    var params = new URLSearchParams(location.search);
    var wanted = params.get('company');
    if(wanted){
      var found = findEntry(wanted);
      if(found) selectEntry(found, false); else showNotFound();
    } else if(entries.length){
      selectEntry(entries[0], false);
    }

    window.addEventListener('resize', function(){
      if(profitWaterfallChart) profitWaterfallChart.resize();
    });
    // 다크/라이트 전환: 표·SVG 는 CSS 변수라 자동, ECharts 워터폴 2개의 잉크·격자 색만 다시 읽어 재렌더.
    window.addEventListener('iq:themechange', function(){
      if(window.IQTheme) TH = IQTheme.chart();
      if(window.IQTheme && window.Chart && IQTheme.applyChartJs) IQTheme.applyChartJs(window.Chart);   // 한국 K-ICS.html 과 같은 시점
      if(CURRENT) selectEntry(CURRENT, false);
    });
  }

  // id(상세) 또는 company_jp(URL 디코드) 둘 다 해석 — jp/index.html 이 회사에 따라 둘 중 하나로
  // 링크하므로, 어느 쪽이 와도 같은 회사를 찾아야 한다.
  function findEntry(wanted){
    if(!wanted) return null;
    return ENTRIES.filter(function(e){
      return e.key === wanted || e.company_jp === wanted || (e.detail && e.detail.company_jp === wanted);
    })[0] || null;
  }

  function showNotFound(){
    clDestroyCharts();
    setHidden('notFoundPanelWrap', false);
    setHidden('secHeadlineWrap', true);
    setHidden('noticePanelWrap', true);
    setHidden('scopeNoteWrap', true);
    TOGGLE_IDS.forEach(function(id){ setHidden(id, true); });
    document.title = '会社別' + PAGE_TITLE[PAGE] + ' | InsureQuant';
    syncTabLinks(null);
  }
  // 3페이지 탭·랭킹 복귀 링크에 현재 회사를 실어 페이지를 옮겨도 같은 회사가 열리게 한다.
  function syncTabLinks(key){
    document.querySelectorAll('.jp-tabs a[data-page]').forEach(function(a){
      var f = PAGE_FILE[a.dataset.page] || a.dataset.page;
      a.setAttribute('href', key ? f + '?company=' + encodeURIComponent(key) : f);
    });
  }

  function selectEntry(e, pushUrl){
    CURRENT = e;
    clDestroyCharts();   // 회사·테마를 바꿀 때마다 이전 도넛 인스턴스를 먼저 정리(누수 방지)
    ['capLimitsWrap', 'durApproxWrap'].forEach(function(id){ var h = byId(id); if(h) h.innerHTML = ''; });   // ESR 층이 없는 회사로 바꿔도 숨은 패널에 이전 회사의 캔버스가 남지 않게
    setHidden('notFoundPanelWrap', true);
    setHidden('secHeadlineWrap', false);
    var sel = document.getElementById('companySelect');
    sel.value = e.key;
    if(pushUrl && history.replaceState){
      var url = new URL(location.href);
      url.searchParams.set('company', e.key);
      history.replaceState(null, '', url);
    }
    document.title = e.company_jp + ' ' + PAGE_TITLE[PAGE] + ' | InsureQuant';
    syncTabLinks(e.key);

    if(e.mode === 'detail'){
      var c = e.detail;
      // jesr_detail.json 자체에는 basis 필드가 없다(publishing이 jesr_esr.json에만 채움) — 헤드라인
      // 레코드가 있으면 거기서 가져온다(없는 회사는 undefined로 두고 renderMeta가 세그먼트를 생략).
      c.basis = e.headlineRec ? e.headlineRec.basis : c.basis;
      // ratio_only(publishing 계약, 2026-09-14): capital_tree 등 資本層이 애초에 없는 회사 — hasEsr을
      // 무조건 false로 못박아 아래 "ESR 층이 아직 없는 회사"(대형 손보 3사 등)와 같은 코드경로를 타되,
      // 안내문은 별도(renderScopeNote)로 갈라 "곧 규제양식이 온다"가 아니라 "이번 라운드 수집범위가
      // 손해율뿐"이라고 정확히 말한다.
      var ratioOnly = isRatioOnly(c);
      // ESR 층이 아직 없는 회사(대형 손보 3사: 신기준 ESR 은 2026-10-31 이연)도 손익·収益性·準備金은 있다(owner 2026-09-13).
      // → ESR 관련 패널(適格資本・所要資本 표·워터폴·感応度)은 숨기고 안내 패널만, 나머지 패널은 그대로 렌더.
      var hasEsr = !ratioOnly && !!(c.headline && c.headline.esr_pct != null) && !!(c.capital_tree && c.capital_tree.length);
      // 안내 패널(規制様式 미공시)은 ESR 페이지에서만 의미가 있다 — 決算·その他開示 페이지는 ESR 유무와 무관.
      // ratio_only는 아래 scopeNoteWrap이 그 역할을 대신하므로 기존 noticePanelWrap은 끈다(문구 중복 방지).
      setHidden('noticePanelWrap', ratioOnly ? true : (PAGE === 'esr' ? hasEsr : true));
      setHidden('noDetailNote', true);
      renderScopeNote(c, ratioOnly);
      ['secCapitalWrap','secCapLimitsWrap','secSensWrap','secDurWrap'].forEach(function(id){ setHidden(id, !hasEsr); });
      // 損益の内訳: 2026-09-14 까지는 ratio_only 에 PL 이 아예 없어서 "ratio_only면 무조건 숨김"이
      // 맞았지만, 2026-09-15 에 법정 損益計算書를 실으면서 그 전제가 깨졌다(19사). 이제는 **실제로
      // PL 항목이 있는지**로 판정한다 — 아직 없는 회사(출처 교체 대기·스캔 PDF)는 종전대로 숨기고
      // scopeNoteWrap 한 줄이 이유를 남긴다(owner 지시: "빈 패널 20개"가 아니라 "왜 없는지 한 줄").
      var plItems = (c.profit && c.profit.items) || {};
      var hasPlItems = Object.keys(plItems).some(function(k){
        return k !== 'pl_net_premiums_written' && plItems[k] && plItems[k].cur != null;
      });
      setHidden('secProfitWrap', ratioOnly && !hasPlItems);
      // headline 이 없으면 랭킹 레코드(jesr_esr)의 값으로 카드만 채운다(상장 지주 연결값이 있는 경우 등).
      if(!hasEsr && e.headlineRec){
        c.headline = c.headline || {};
        if(c.headline.esr_pct == null) c.headline.esr_pct = e.headlineRec.esr_pct;
        if(c.headline.preliminary == null) c.headline.preliminary = e.headlineRec.preliminary;
      }
      renderMeta(c);
      renderHeadline(c);
      renderJgaapCards(c);
      if(hasEsr){
        renderCapital(c);
        renderCapReqTable(c);
        guarded(renderCapLimits, c);
        renderReproBadge(c);
        renderSensitivity(c);
        guarded(renderDuration, c);
        guarded(renderSensMatrix, c);
        // 새로 그린 「?」 팝오버는 오른쪽으로 넘쳐 있다가 theme.js 가 180ms 뒤에 눌러 준다 — 그 사이 모바일 레이아웃 뷰포트가 넓어진 채 남는다. 같은 태스크에서 바로 누른다.
        if(window.IQTheme && IQTheme.clampHelpPops){ try{ IQTheme.clampHelpPops(); }catch(ex){} }
      }
      renderBs(c);
      if(ratioOnly && !hasPlItems){
        // PL 이 정말 없는 회사(출처 교체 대기·스캔 PDF)만 여기로 온다 — 그릴 게 없으니
        // 이전에 그려둔 차트가 남아있으면 정리만 하고, 패널은 위에서 이미 숨겼다.
        if(profitWaterfallChart){ try{ profitWaterfallChart.dispose(); }catch(ex){} profitWaterfallChart = null; }
      } else {
        renderProfit(c);
      }
      renderProfitability(c);
      renderAxes(c);
      // その他開示 페이지: 재보험·その他 둘 다 비면 미수록 안내 — ratio_only는 scopeNoteWrap이 이미
      // 같은 설명(その他開示は本編開示後)을 하고 있어 disclosureEmpty를 더 띄우면 문장 두 개가
      // 겹쳐 보인다(2026-09-14 실측). ratio_only일 땐 이 안내를 끈다.
      if(PAGE === 'disclosure'){
        if(ratioOnly){
          setHidden('disclosureEmpty', true);
        } else {
          var anyDisc = ['secReinsWrap','secAxesWrap'].some(function(id){ var el = byId(id); return el && !el.hidden; });
          setHidden('disclosureEmpty', anyDisc);
        }
      }
    } else {
      setHidden('noticePanelWrap', PAGE !== 'esr');   // ESR 페이지: 規制様式 미공시 안내
      setHidden('noDetailNote', PAGE === 'esr');      // 決算·その他開示 페이지: 미수록 안내(+그룹 사업회사 링크)
      setHidden('scopeNoteWrap', true);               // 상세 자체가 없는 회사 — ratio_only 안내는 무관
      setHidden('disclosureEmpty', true);
      TOGGLE_IDS.forEach(function(id){ setHidden(id, true); });
      var r = e.headlineRec;
      var hc = {
        company_jp: r.company_jp, company_en: r.company_en, scope: r.scope, basis: r.basis,
        source_url: r.source_url, doc_date: r.doc_date, doc_type: r.doc_type, as_of: r.as_of,
        value_verified: r.value_verified,
        headline: { eligible_capital: null, required_capital: null, esr_pct: r.esr_pct, preliminary: r.preliminary }
      };
      renderMeta(hc);
      renderHeadline(hc);
      renderJgaapCards(null);
      // 지주(연결) 헤드라인 페이지: 그룹 사업회사(単体) 상세 링크(_meta.group_children, owner 2026-09-13)
      var gcl = document.getElementById('groupChildrenLine');
      var kids = (ESR_META && ESR_META.group_children && ESR_META.group_children[r.company_jp]) || [];
      if(gcl){
        if(kids.length){
          gcl.hidden = false;
          gcl.innerHTML = 'グループ会社（単体）の詳細: ' + kids.map(function(k){ return '<a href="'+PAGE_FILE[PAGE]+'?company='+esc(k.id)+'">'+esc(k.company_jp)+'</a>'; }).join('・');
        } else { gcl.hidden = true; }
      }
    }
  }

  function renderMeta(c){
    var scope = SCOPE_LABEL[c.scope] || c.scope || '—';
    // value_verified(2026-09-14): 「根拠資料 ↗」링크는 "여기서 값을 확인했다"는 약속이다
    // (PM-2026-09-13 T&D: 그 링크가 실은 목록 페이지였다). unverified/exempt 면 링크는 그대로
    // 두되(원문을 보는 건 여전히 유용하다) 그 약속이 아직 안 지켜졌다는 사실을 바로 옆에 붙인다.
    var vv = c.value_verified;
    var vBadge = verifyBadgeHtml(vv);
    var vNote = (vv && vv.state && vv.state !== 'verified') ? '（'+(VERIFY_META[vv.state]||VERIFY_META.unverified).label+'）' : '';
    var srcCell = c.source_url
      ? '<a href="'+esc(c.source_url)+'" target="_blank" rel="noopener noreferrer" aria-label="'+esc(c.company_jp)+'の根拠資料、別タブで開く'+esc(vNote)+'">'+esc(jaDate(c.doc_date))+(c.doc_type?'（'+esc(jaOnly(c.doc_type))+'）':'')+' &#8599;</a>' + vBadge
      : esc(jaDate(c.doc_date)) + vBadge;
    var fq = c.as_of ? jaFiscalQuarter(c.as_of) : '—';
    // 算定基準(owner 2026-09-13、ランキングのchipと同じ区分) — ESRページのみ、値がある会社のみ表示
    // (headline外の会社はbasisが無く、その場合"未確認"を出すとESR自体が無いのに紛らわしいので省略)。
    var basisSeg = (PAGE === 'esr' && c.basis) ? (' &nbsp;|&nbsp; 算定基準: <span title="'+esc(basisLabel(c.basis) === '未確認' ? '算定基準が未確認です' : basisLabel(c.basis)+'で算定。規制ベース(告示74号の標準式)以外の会社とは単純比較に適さない場合があります。')+'">'+esc(basisLabel(c.basis))+'</span>') : '';
    document.getElementById('metaLine').innerHTML =
      '<span title="'+esc(jaDate(c.as_of))+'">基準時点 '+esc(fq)+'</span> &nbsp;|&nbsp; 範囲: '+esc(scope)+basisSeg+' &nbsp;|&nbsp; 公表: '+srcCell;
  }

  function renderHeadline(c){
    if(!byId('cardEsr')) return;
    var h = c.headline || {};
    document.getElementById('cardEligible').textContent = fmtEok(h.eligible_capital);
    document.getElementById('cardEligible').title = fmtMillionTip(h.eligible_capital);
    document.getElementById('cardRequired').textContent = fmtEok(h.required_capital);
    document.getElementById('cardRequired').title = fmtMillionTip(h.required_capital);
    var esrEl = document.getElementById('cardEsr');
    esrEl.textContent = fmtPct1(h.esr_pct);
    esrEl.style.color = colorForRatio(h.esr_pct);
    // value_verified(2026-09-14): ESR 헤드라인 값 옆(値検証状態) — 速報 배지와 같은 자리에 병기.
    document.getElementById('cardPrelim').innerHTML = (h.preliminary ? '<span class="prelim-badge">速報</span>' : '') + verifyBadgeHtml(c.value_verified);
  }

  // 決算 페이지 상단 카드: 当期純利益 / 経常利益 / 保険引受利益(손보) 또는 基礎利益(생보) / 合算率(손보만)
  function renderJgaapCards(c){
    var host = byId('jgaapCards'); if(!host) return;
    var p = (c && c.profit && c.profit.status === 'extracted') ? c.profit : null;
    if(!p){
      // ratio_only(2026-09-14): items は無いが合算率(ratios)はある — "未取得"と書くと下の「収益性指標」
      // に実際にはデータがあるのに全く無いように読めるので、合算率カード1枚+誘導文に差し替える。
      var ro = c && c.profit && c.profit.ratios && c.profit.ratios.pl_combined_ratio_pct;
      if(isRatioOnly(c) && ro){
        host.innerHTML = '<div class="jcard"><div class="jcard-val">'+esc(fmtPct1(ro.cur))+'</div><div class="jcard-sub">&nbsp;</div><div class="jcard-lab">合算率'+caveatBadgeHtml(c.ratio_caveat)+verifyBadgeHtml(c.value_verified)+'</div></div>'
          + '<div class="empty-note" style="grid-column:span 3;align-self:center">当期純利益・経常利益・保険引受利益等は本編開示の取得後に追加します。損害率・事業費率は下の「収益性指標」をご覧ください。</div>';
        return;
      }
      host.innerHTML = '<div class="empty-note" style="grid-column:1/-1">損益データは未取得です。</div>';
      return;
    }
    var isLife = !!(p.core && Object.keys(p.core).length);
    var cards = [
      {lab:'当期純利益', v:plCur(p,'pl_net_income'), unit:'億円'},
      {lab:'経常利益', v:plCur(p,'pl_ordinary_profit'), unit:'億円'},
      isLife ? {lab:'基礎利益', v:plCur(p,'pl_core_profit'), unit:'億円'} : {lab:'保険引受利益', v:plCur(p,'pl_underwriting_profit'), unit:'億円'}
    ];
    if(!isLife){ var cr = p.ratios && p.ratios.pl_combined_ratio_pct; cards.push({lab:'合算率', v:cr ? cr.cur : null, unit:'%', pct:true}); }
    host.innerHTML = cards.map(function(k){
      var txt = k.pct ? fmtPct1(k.v) : fmtEok(k.v);
      return '<div class="jcard"><div class="jcard-val" title="'+esc(k.pct ? '' : fmtMillionTip(k.v))+'">'+esc(txt)+'</div><div class="jcard-sub">'+(k.pct?'&nbsp;':k.unit)+'</div><div class="jcard-lab">'+esc(k.lab)+'</div></div>';
    }).join('');
  }

  function renderCapital(c){
    if(!byId('stackBar')) return;
    var cap = c.capital || {};
    var h = c.headline || {};
    var t1 = cap.tier1_eligible, t2 = cap.tier2_eligible;
    var total = (t1||0) + (t2||0);
    var track = document.getElementById('stackBar');
    track.innerHTML = '';
    if(total>0){
      var segT1 = document.createElement('div');
      segT1.className = 'stackbar-seg t1';
      segT1.style.width = Math.max(0,(t1||0)/total*100) + '%';
      if((t1||0)/total > 0.12) segT1.textContent = 'Tier1 '+fmtPct1((t1||0)/total*100);
      var segT2 = document.createElement('div');
      segT2.className = 'stackbar-seg t2';
      segT2.style.width = Math.max(0,(t2||0)/total*100) + '%';
      if((t2||0)/total > 0.12) segT2.textContent = 'Tier2 '+fmtPct1((t2||0)/total*100);
      track.appendChild(segT1); track.appendChild(segT2);
    }
    track.setAttribute('aria-label',
      '適格資本構成。Tier1 '+fmtEok(t1)+'億円('+fmtPct1(total>0?(t1||0)/total*100:null)+')、'+
      'Tier2 '+fmtEok(t2)+'億円('+fmtPct1(total>0?(t2||0)/total*100:null)+')。');

  }

  // ── 適格資本・所要資本 한 표 (owner 2026-09-13, K-ICS.html 430~470행 subtoggle 방식) ───────────────
  // 입력: c.capital_tree / c.risk_tree — builder 가 스키마 parent/formula 로 만든 전위 순회 리스트
  //   [{id,label_ja,depth,sign:"="|"+"|"-",value,is_total,check?,aggregation?}]. 여기서는 산식을 해석하지 않는다.
  // 펼침 상태는 subOpen[nodeId] (기본: depth 0 노드만 열림 → depth 1 행 보임, depth ≥2 는 [+] 로).
  var subOpen = {};
  function treeRows(tree, blockLabel, blockId){
    if(!tree || !tree.length) return '';
    // 각 노드의 조상 id 목록(다단 접기: 조상 중 하나라도 닫히면 숨김)
    var stack = [], html = '';
    html += '<tr class="total-row block-head"><td colspan="4">'+esc(blockLabel)+'</td></tr>';
    for(var i=0;i<tree.length;i++){
      var n = tree[i];
      while(stack.length && stack[stack.length-1].depth >= n.depth) stack.pop();
      var ancestors = stack.map(function(a){ return a.id; });
      var hasChild = (i+1 < tree.length) && tree[i+1].depth > n.depth;
      if(subOpen[n.id] === undefined) subOpen[n.id] = (n.depth === 0);
      var hiddenByAncestor = ancestors.some(function(a){ return !subOpen[a]; });
      var cls = ancestors.map(function(a){ return 'subrow-'+a; }).join(' ');
      if(n.is_total) cls += ' total-row';
      var signTxt = n.sign === '=' ? '＝' : (n.sign === '-' ? '－' : '＋');
      var val = fmtEok(n.value);
      if(n.sign === '-' && n.value != null && n.value !== 0) val = '△' + val;
      var note = '';
      if(n.check && n.check.ok === true) note = '<span class="repro-badge ok" title="表示行の合計で再現">✓</span>';
      else if(n.check && n.check.ok === false) note = '<span class="repro-badge warn" title="表示行の合計との差">差 '+esc(fmtEok(Math.abs((n.check.lhs||0)-(n.check.rhs||0))))+'</span>';
      if(n.aggregation === 'correlated' && n.check && n.check.simple_sum != null)
        note = '<span class="small-muted">相関統合（単純合計 '+esc(fmtEok(n.check.simple_sum))+'）</span>';
      var toggle = hasChild
        ? ' <button type="button" class="subtoggle" data-group="'+esc(n.id)+'" aria-expanded="'+subOpen[n.id]+'" title="内訳を'+(subOpen[n.id]?'閉じる':'展開')+'">'+(subOpen[n.id]?'−':'+')+'</button>'
        : '';
      html += '<tr class="'+cls+'"'+(hiddenByAncestor?' style="display:none"':'')+' data-node="'+esc(n.id)+'" data-depth="'+n.depth+'">'
        + '<td style="padding-left:'+(8 + n.depth*16)+'px">'+esc(n.label_ja || labelOf(META, n.id, n.id))+toggle+'</td>'
        + '<td class="sign">'+signTxt+'</td>'
        + '<td class="num" title="'+esc(fmtMillionTip(n.value))+'">'+esc(val)+'</td>'
        + '<td>'+note+'</td></tr>';
      stack.push(n);
    }
    return html;
  }
  function renderCapReqTable(c){
    var body = document.getElementById('capReqBody'); if(!body) return;
    var html = treeRows(c.capital_tree, '適格資本', 'cap') + treeRows(c.risk_tree, '所要資本（税効果調整前）', 'req');
    // 税効果 → 所要資本 마무리 행 (risk_tree 뿌리는 rc_pre_tax)
    var r = c.risk || {};
    if(r.tax_effect != null) html += '<tr data-node="rc_tax_effect"><td style="padding-left:24px">'+esc(labelOf(META,'rc_tax_effect','税効果'))+'</td><td class="sign">－</td><td class="num" title="'+esc(fmtMillionTip(r.tax_effect))+'">△'+esc(fmtEok(r.tax_effect))+'</td><td></td></tr>';
    if(r.rc_post_tax != null) html += '<tr class="total-row" data-node="rc_post_tax"><td style="padding-left:8px">'+esc(labelOf(META,'rc_post_tax','所要資本の額'))+'</td><td class="sign">＝</td><td class="num" title="'+esc(fmtMillionTip(r.rc_post_tax))+'">'+esc(fmtEok(r.rc_post_tax))+'</td><td></td></tr>';
    body.innerHTML = html || '<tr><td colspan="4" class="small-muted">データがありません。</td></tr>';
    // 토글 바인딩 — 닫으면 자손 전부 숨김, 열면 "열린 조상만" 기준으로 자식 행을 다시 계산
    body.querySelectorAll('.subtoggle').forEach(function(btn){
      btn.addEventListener('click', function(){
        var g = btn.dataset.group;
        subOpen[g] = !subOpen[g];
        btn.textContent = subOpen[g] ? '−' : '+';
        btn.setAttribute('aria-expanded', String(subOpen[g]));
        btn.title = '内訳を' + (subOpen[g] ? '閉じる' : '展開');
        body.querySelectorAll('tr[class*="subrow-"]').forEach(function(tr){
          var anc = (tr.className.match(/subrow-([^\s]+)/g) || []).map(function(s){ return s.slice(7); });
          tr.style.display = anc.every(function(a){ return subOpen[a]; }) ? '' : 'none';
        });
      });
    });
  }

  // 告示 합성식 재현 배지 — 종전 所要資本 워터폴 제목에 있던 것을 표 제목으로 옮김(워터폴 폐지, owner 2026-09-13).
  function renderReproBadge(c){
    var agg = c.aggregation || {};
    var badge = byId('reproBadge'); if(!badge) return;
    var agg = c.aggregation || {};
    if(agg.reproduced===true){
      badge.style.display = 'inline-flex';
      badge.className = 'repro-badge ok';
      badge.textContent = '✓ 規定再現 '+(agg.checks_pass!=null?agg.checks_pass:'—')+'/'+(agg.checks_total!=null?agg.checks_total:'—');
      badge.title = '公表数値から告示の合成式を再現できました。';
    } else if(agg.reproduced===false){
      badge.style.display = 'inline-flex';
      badge.className = 'repro-badge warn';
      badge.textContent = '△ 規定再現 '+(agg.checks_pass!=null?agg.checks_pass:'—')+'/'+(agg.checks_total!=null?agg.checks_total:'—');
      var devs = (agg.deviations||[]).map(function(d){
        return d.id+': 公表'+d.lhs+' / 再現'+d.rhs+(d.note?' — '+d.note:'');
      }).join('\n');
      badge.title = devs || '一部の合成式で差異があります(告示の集計順序・地域集約の違い等)。';
    } else {
      badge.style.display = 'none';
    }

  }

  var MKT_SUB = [
    {key:'rc_mkt_interest', ja:'金利リスク'},
    {key:'rc_mkt_spread', ja:'スプレッドリスク'},
    {key:'rc_mkt_equity', ja:'株式リスク'},
    {key:'rc_mkt_property', ja:'不動産リスク'},
    {key:'rc_mkt_fx', ja:'為替リスク'},
    {key:'rc_mkt_concentration', ja:'資産集中リスク'},
  ];
  // 市場リスク 별도 패널은 2026-09-13 owner 지시로 폐지 — 하위 리스크는 適格資本・所要資本 표의 [+] 로 전개된다.

  function renderSensitivity(c){
    var body = document.getElementById('sensTableBody'); if(!body) return;
    var h = c.headline || {};
    var list = c.sensitivity || [];
    var rowsHtml = [];
    rowsHtml.push(
      '<tr class="sens-row base">'
      + '<td>基準(当期末)</td>'
      + '<td class="num">'+esc(fmtPct1(h.esr_pct))+'</td>'
      + '<td class="num">±0.0pp</td>'
      + '<td></td>'
      + '</tr>'
    );
    var maxAbs = Math.max.apply(null, list.map(function(s){ return Math.abs(s.delta_pp||0); }).concat([1]));
    list.forEach(function(s){
      var cls = (s.delta_pp||0) < 0 ? 'neg' : 'pos';
      var barPct = Math.min(100, Math.abs(s.delta_pp||0)/maxAbs*100);
      rowsHtml.push(
        '<tr class="sens-row">'
        + '<td>'+esc(s.label_ja||s.id)+'</td>'
        + '<td class="num">'+esc(fmtPct1(s.esr_pct))+'</td>'
        + '<td class="num sens-delta '+cls+'">'+esc(fmtPP(s.delta_pp))+'</td>'
        + '<td><div class="mini-track" style="width:60px;display:inline-block"><div class="mini-bar" style="width:'+Math.max(2,barPct)+'%;background:'+(cls==='neg'?'var(--neg)':'var(--pos)')+'"></div></div></td>'
        + '</tr>'
      );
    });
    body.innerHTML = rowsHtml.join('');
    var emptyNote = document.getElementById('sensEmptyNote');
    if(!list.length){
      if(!emptyNote){
        emptyNote = document.createElement('p');
        emptyNote.id = 'sensEmptyNote';
        emptyNote.className = 'empty-note';
        document.getElementById('sensWrap').appendChild(emptyNote);
      }
      emptyNote.textContent = '基準日以外のシナリオ別ESRは開示されていません(変動幅|Δ|が僅少で開示者が省略、等)。';
    } else if(emptyNote){
      emptyNote.remove();
    }
  }

  // ══ 算入上限に対する割合 / 略式実効デュレーション / 感応度の詳細 (2026-11-04, 티켓 20261103T1550Z) ══════════
  // 데이터: 회사 레코드의 형제 키 capital_limits · duration_approx · sensitivity_levels 와 _meta 의 같은 이름 블록.
  // 구판 JSON(키 없음)에서는 각 render 가 자기 컨테이너를 비우고 조용히 돌아간다. 기존 표(renderCapReqTable/renderSensitivity)는 건드리지 않는다.
  // owner 결정 기본값(오케스트레이터, 2026-11-04 위임)은 이 한 곳에 모은다: 대표 지표=Tier2 전체, Tier1 제한은 10%〜15% 범위+상태만,
  // 100% 초과는 값을 자르지 않고 「100%超」 칩(막대만 자른다), 바스켓 도달은 「上限に到達」 칩, 듀레이션은 면별 상승/하락/평균만(격차 행 없음).
  var UI_DEFAULTS = { tier1Range: '10%〜15%の範囲', overPct: 100, overChip: '100%超', atCapChip: '上限に到達' };
  var helpSeq = 0;
  function helpHtml(paras, label){
    var list = (paras || []).filter(function(p){ return !!p; });
    if(!list.length) return '';
    var id = 'iqhelp' + (++helpSeq);
    return '<span class="iq-help"><button type="button" class="iq-help-btn" aria-label="' + esc(label || '補足') + '" aria-describedby="' + id + '">?</button>'
      + '<span class="iq-help-pop" role="tooltip" id="' + id + '">' + list.map(function(p){ return '<span class="hp-line">' + esc(p) + '</span>'; }).join('') + '</span></span>';
  }
  function derivedBadge(){ return '<span class="derived-badge">算出値</span>'; }
  function chipHtml(t){ return '<span class="jp-chip">' + esc(t) + '</span>'; }
  function caveatJa(block, id){
    var m = META && META[block]; var t = m && m.caveats_ja && m.caveats_ja[id];
    return t || null;   // 문구가 아직 없으면 그 팝오버 항목만 조용히 생략
  }
  function guarded(fn, c){ try{ fn(c); }catch(ex){ console.error(fn.name + ' failed', ex); } }

  // 시나리오·표 상태 공통 일본어(티켓 지정 문구). duration 의 reason 파싱에도 쓴다.
  var SCEN_STATUS_JA = {
    omitted_below_1pp: '発行体が1%未満のため記載を省略',
    printed_dash: '開示表は―(記載なし)',
    not_in_source: '該当する表なし',
    not_extracted: '未収録'
  };
  var SCEN_TAG_JA = { omitted_below_1pp: '記載省略', printed_dash: '―(記載なし)', not_in_source: '表なし', not_extracted: '未収録' };
  // 閾値が1ppでない省略(status_notes[].threshold)は文言の「1%」を実際の閾値に差し替える。
  function omitText(sl){
    var th = null;
    (sl.status_notes || []).forEach(function(n){ if(n && n.status === 'omitted_below_1pp' && n.threshold && n.threshold !== '1pp') th = n.threshold; });
    var m = th && /^(\d+(?:\.\d+)?)pp$/.exec(th);
    return m ? '発行体が' + m[1] + '%未満のため記載を省略' : SCEN_STATUS_JA.omitted_below_1pp;
  }

  // ── P1. 자본성증권 인정한도 소진율 ──────────────────────────────────────────
  var CL_REC_JA = { not_extracted: '未収録', not_in_source: '開示表なし', not_computable: '算出不可' };
  var CL_LABEL = { tier1_restricted: 'tier1_instr_restricted', tier2_total: 'tier2_eligible', tier2_unpaid: 'tier2_instr_unpaid', tier2_basket: 'tier2_ni_basket' };
  var CL_ORDER = ['tier1_restricted', 'tier2_total', 'tier2_unpaid', 'tier2_basket'];
  var CL_STATE_JA = {
    tier1_restricted: { not_applicable_no_instrument: '該当なし(開示表は―)', ok_range: UI_DEFAULTS.tier1Range, needs_instrument_data: '証券条件の確認が必要', not_extracted: '未収録', inconsistent_print: '印字が不整合' },
    tier2_total: { identity_mismatch: '印字が不整合', not_extracted: '未収録', not_computable: '算出不可' },
    tier2_unpaid: { not_applicable_not_mutual: '該当なし(相互会社のみ)', not_applicable_no_instrument: '該当なし', not_extracted: '未収録', inconsistent_print: '印字が不整合' },
    tier2_basket: { no_amount: '該当なし', not_extracted: '未収録' }
  };
  // 수치를 그리는 상태(그 밖의 상태는 수치 없이 상태 문구만 — 대시는 0% 가 아니다).
  var CL_NUMERIC = {
    tier1_restricted: { ok: 1, ok_range: 1, needs_instrument_data: 1 },
    tier2_total: { ok: 1 },
    tier2_unpaid: { ok: 1 },
    tier2_basket: { ok_post_cap_only: 1 }
  };
  function articleJa(a){
    if(!a) return null;
    var m = /^(\d+)\s*(.*)$/.exec(String(a));
    return m ? '根拠条文: 告示74号 第' + m[1] + '条' + (m[2] ? ' ' + m[2] : '') : '根拠条文: 告示74号 ' + a;
  }
  function clHelpParas(lim){
    var out = [articleJa(lim && lim.article)];
    ((lim && lim.caveat_ids) || []).forEach(function(id){ out.push(caveatJa('capital_limits', id)); });
    return out;
  }
  // 한 한도 객체 → 표 한 줄에 쓸 값. pct 는 JSON 의 퍼센트 그대로(자르지 않는다), null 이면 수치 칸은 「―」.
  function clModel(key, lim, cl){
    var st = lim.status, numeric = !!(CL_NUMERIC[key] && CL_NUMERIC[key][st]);
    var m = { amount: null, capLo: null, capHi: null, pct: null, pctLo: null, pctHi: null, state: (CL_STATE_JA[key] && CL_STATE_JA[key][st]) || '', atCap: false };
    var rs = cl.row_states || {};
    if(key === 'tier1_restricted'){
      if(st === 'not_applicable_no_instrument'){
        if(rs.tier1_instr_restricted === 'printed_zero' || rs.tier2_instr_t1_excess === 'printed_zero'){ m.amount = lim.printed_restricted_post_limit; m.state = '該当なし(開示表は0)'; }
      } else if(numeric){
        m.amount = lim.printed_restricted_post_limit;
        m.capLo = lim.cap_low_amount; m.capHi = lim.cap_high_amount;
        m.pct = lim.utilization_pct; m.pctLo = lim.utilization_pct_min; m.pctHi = lim.utilization_pct_max;
      }
    } else if(key === 'tier2_total'){
      if(numeric){ m.amount = lim.numerator_E_minus_F; m.capHi = lim.cap_amount; m.pct = lim.utilization_pct; }
    } else if(key === 'tier2_unpaid'){
      if(numeric){ m.amount = lim.printed_unpaid_post_limit; m.capHi = lim.cap_amount; m.pct = lim.pct_of_cap; }
    } else if(key === 'tier2_basket'){
      if(numeric){ m.amount = lim.printed_basket_post_cap; m.capHi = lim.cap_amount; m.pct = lim.pct_of_cap; m.atCap = lim.at_cap === true; }
    }
    return m;
  }
  function clCapText(m){
    if(m.capHi == null) return '―';
    if(m.capLo != null && m.capLo !== m.capHi) return fmtEok(m.capLo) + '〜' + fmtEok(m.capHi);
    return fmtEok(m.capHi);
  }
  function clBasisJa(key, cl, m){
    if(key === 'tier2_total') return clBasisTier2Ja(cl);
    if(key === 'tier2_basket') return '所要資本×15%';
    if(key === 'tier2_unpaid') return '出資約定額と所要資本×10%の小さい方';
    if(key === 'tier1_restricted'){
      if(cl.mutual) return '所要資本×30%';
      return (m.capLo != null && m.capHi != null && m.capLo !== m.capHi) ? '所要資本×10%〜15%' : '';
    }
    return '';
  }
  function clBasisTier2Ja(cl){ return cl.mutual ? '所要資本×60%−Tier1制限額' : '所要資本×50%'; }
  function clIsNumeric(m){ return m.pct != null || (m.pctLo != null && m.pctHi != null); }
  function clFmt(v, n){ return (v < 0 ? '△' : '') + Math.abs(v).toFixed(n); }
  function clClamp(v){ return Math.min(Math.max(v, 0), 100); }

  // ── 도넛: 한국 K-ICS.html renderDonut 와 같은 모양 (Chart.js 4.4.0 doughnut, cutout 72%, 가운데 700 28px, 범례 없음) ──
  // 색: 0~70% 청록 · 70~100% 주황 · 100% 이상 빨강. 호는 100% 에서 자르고 숫자는 자르지 않는다(가운데 「100%超」, 툴팁에 실제 값).
  var CL_TITLE = '算入上限に対する割合';
  var clCharts = [];
  var clDefaultsSet = false;
  function clDestroyCharts(){
    clCharts.forEach(function(ch){ try{ ch.destroy(); }catch(ex){} });
    clCharts = [];
  }
  function clChartDefaults(){
    var C = window.Chart; if(!C) return false;
    if(!clDefaultsSet){
      clDefaultsSet = true;
      var font = "'Pretendard Variable',Pretendard,ui-sans-serif,system-ui,'Segoe UI',sans-serif";
      C.defaults.font.family = font; C.defaults.font.size = 12;
      C.defaults.plugins.tooltip.padding = 10; C.defaults.plugins.tooltip.cornerRadius = 6;
      C.defaults.plugins.tooltip.titleFont = { family: font, size: 12, weight: '600' };
      C.defaults.plugins.tooltip.bodyFont = { family: font, size: 12 };
    }
    if(window.IQTheme && IQTheme.applyChartJs) IQTheme.applyChartJs(C);   // 색은 theme.js 토큰, 테마가 바뀔 때마다 다시 읽는다
    return true;
  }
  function clFillColor(pct){
    if(pct >= 100) return 'rgba(220, 53, 69, 0.85)';
    if(pct >= 70) return 'rgba(255, 159, 64, 0.85)';
    return 'rgba(75, 192, 192, 0.85)';
  }
  // 가운데 글자: 단일 값은 소수 1자리(한국은 정수), 100% 초과는 「100%超」. 범위(10%〜15% 등)는 하한〜상한.
  function clCenterText(sp){
    if(sp.lo != null) return (sp.lo > UI_DEFAULTS.overPct ? UI_DEFAULTS.overChip : fmtPct1(sp.lo)) + '〜' + (sp.hi > UI_DEFAULTS.overPct ? UI_DEFAULTS.overChip : fmtPct1(sp.hi));
    return sp.pct > UI_DEFAULTS.overPct ? UI_DEFAULTS.overChip : fmtPct1(sp.pct);
  }
  function clDonut(cv, sp){
    var TH = window.IQTheme ? IQTheme.chart() : { text: '#212529', neg: '#dc3545', border: 'rgba(233, 236, 239, 0.6)' };
    var isRange = sp.lo != null;
    var refPct = isRange ? sp.lo : sp.pct;
    var main = clFillColor(refPct), data, colors;
    if(isRange){
      var lo = clClamp(sp.lo), hi = Math.max(lo, clClamp(sp.hi));
      data = [lo, hi - lo, 100 - hi];
      colors = [main, main.replace('0.85', '0.35'), TH.border];
    } else {
      var fill = clClamp(sp.pct);
      data = [fill, 100 - fill];
      colors = [main, TH.border];
    }
    var text = clCenterText(sp);
    var centerColor = refPct >= 100 ? TH.neg : TH.text;
    var centerPlugin = {
      id: 'centerText_' + sp.id,
      afterDraw: function(chart){
        if(!chart || !chart.chartArea) return;
        var a = chart.chartArea, ctx = chart.ctx;
        var cx = (a.left + a.right) / 2, cy = (a.top + a.bottom) / 2;
        ctx.save();
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillStyle = centerColor;
        // 한국과 같은 700 28px. 범위처럼 글자가 길어 안쪽 원(지름의 72%)을 넘을 때만 줄인다.
        var px = 28;
        ctx.font = '700 ' + px + 'px ui-sans-serif, system-ui';
        var inner = Math.min(a.right - a.left, a.bottom - a.top) * 0.72 * 0.88, w = ctx.measureText(text).width;
        if(w > inner){ px = Math.max(12, Math.floor(px * inner / w)); ctx.font = '700 ' + px + 'px ui-sans-serif, system-ui'; }
        ctx.fillText(text, cx, cy);
        ctx.restore();
      }
    };
    var rm = !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
    return new Chart(cv.getContext('2d'), {
      type: 'doughnut',
      data: { labels: isRange ? ['使用(下限)', '使用(上限)', '残余'] : ['使用', '残余'], datasets: [{ data: data, backgroundColor: colors, borderWidth: 0 }] },
      options: {
        responsive: true, maintainAspectRatio: false, cutout: '72%',
        animation: rm ? false : {},
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: function(c){
            if(isRange){
              if(c.dataIndex === 0) return ['使用(下限): ' + clFmt(sp.lo, 2) + '%'];
              if(c.dataIndex === 1) return ['使用(上限): ' + clFmt(sp.hi, 2) + '%'];
              return ['残余: ' + clFmt(Math.max(0, 100 - sp.hi), 2) + '%〜' + clFmt(Math.max(0, 100 - sp.lo), 2) + '%'];
            }
            // 모바일 폭에서 툴팁이 캔버스보다 넓어 잘리지 않게 긴 줄은 둘로 나눈다(한국 K-ICS.html 과 같은 처리).
            if(c.dataIndex === 0){
              return sp.pct > UI_DEFAULTS.overPct ? ['使用: ' + UI_DEFAULTS.overChip, '(実際 ' + clFmt(sp.pct, 2) + '%)'] : ['使用: ' + clFmt(sp.pct, 2) + '%'];
            }
            return ['残余: ' + clFmt(Math.max(0, 100 - sp.pct), 2) + '%'];
          } } }
        }
      },
      plugins: [centerPlugin]
    });
  }

  // 한 줄 노트(한국 donut-note 처럼 「 | 」 로 잇는다): 수치 있는 한도는 개시액·算入上限(근거), 없는 한도는 상태 문구만.
  function clNoteLine(k, m, cl){
    var name = labelOf(META, CL_LABEL[k], k);
    if(!clIsNumeric(m)){
      return esc(name) + ': ' + esc(m.state || '未収録') + (m.amount != null ? ' ／ 開示額 ' + esc(fmtEok(m.amount)) + '億円' : '');
    }
    var basis = clBasisJa(k, cl, m);
    return esc(name) + ' ' + esc(m.amount == null ? '―' : fmtEok(m.amount)) + '億円 ／ 算入上限 ' + esc(clCapText(m)) + '億円' + (basis ? '<span class="nw">(' + esc(basis) + ')</span>' : '');
  }

  function renderCapLimits(c){
    var panel = byId('secCapLimitsWrap'), host = byId('capLimitsWrap'); if(!host) return;
    clDestroyCharts();
    var cl = c.capital_limits;
    if(!cl || typeof cl !== 'object'){ host.innerHTML = ''; if(panel) panel.hidden = true; return; }   // 구판 JSON(키 없음): 패널째로 숨김
    var L = cl.limits || {};
    var fq = c.as_of ? jaFiscalQuarter(c.as_of) : null;
    var head = byId('secCapLimits');
    if(head) head.innerHTML = CL_TITLE + derivedBadge() + (fq ? ' <span class="h2-sub">基準時点 ' + esc(fq) + '</span>' : '');
    if(panel) panel.hidden = false;
    if((cl.status !== 'ok' && cl.status !== 'partial') || !Object.keys(L).length){
      host.innerHTML = '<div class="no-data">算入上限に対する割合: ' + esc(CL_REC_JA[cl.status] || '未収録') + '</div>';
      return;
    }
    var haveChart = clChartDefaults();
    var cells = [], notes = [], specs = [];
    CL_ORDER.forEach(function(k){
      var lim = L[k]; if(!lim) return;
      var m = clModel(k, lim, cl);
      notes.push(clNoteLine(k, m, cl));
      if(!clIsNumeric(m)) return;   // 수치가 없는 한도(대시·未収録·該当なし)는 도넛을 그리지 않는다 — 0% 가 아니다
      var name = labelOf(META, CL_LABEL[k], k);
      var sp = { id: 'clDonut' + cells.length, key: k };
      if(m.pct != null) sp.pct = m.pct; else { sp.lo = m.pctLo; sp.hi = m.pctHi; }
      var top = sp.lo != null ? sp.hi : sp.pct;
      var chipTxt = [];
      if(top > UI_DEFAULTS.overPct) chipTxt.push(UI_DEFAULTS.overChip);
      if(m.atCap) chipTxt.push(UI_DEFAULTS.atCapChip);
      var sub = (m.state ? esc(m.state) : '') + chipTxt.map(function(t, i){ return (m.state || i ? ' ' : '') + chipHtml(t); }).join('');
      var valTxt = clCenterText(sp);
      var aria = CL_TITLE + ': ' + name + ' ' + valTxt + (top > UI_DEFAULTS.overPct ? '(実際 ' + clFmt(top, 1) + '%)' : '') + (chipTxt.length ? '、' + chipTxt.join('、') : '');
      var body = haveChart
        ? '<canvas id="' + sp.id + '" role="img" aria-label="' + esc(aria) + '"></canvas>'
        : '<div class="cl-fallback" role="img" aria-label="' + esc(aria) + '">' + esc(valTxt) + '</div>';
      cells.push('<div class="donut-cell"><div class="donut-wrap">' + body + '</div>'
        + '<div class="donut-caption">' + esc(name) + helpHtml(clHelpParas(lim), name + 'の補足') + (sub ? '<span class="sub">' + sub + '</span>' : '') + '</div></div>');
      specs.push(sp);
    });
    var noteHtml = '<div class="donut-note">' + notes.join(' &nbsp;|&nbsp; ') + '</div>';
    if(!cells.length){
      var t2 = L.tier2_total || {};
      host.innerHTML = '<div class="no-data">算入上限に対する割合: ' + esc((CL_STATE_JA.tier2_total && CL_STATE_JA.tier2_total[t2.status]) || '未収録') + '</div>' + noteHtml;
      return;
    }
    host.innerHTML = '<div class="donut-row">' + cells.join('') + '</div>' + noteHtml;
    if(!haveChart) return;
    specs.forEach(function(sp){
      var cv = byId(sp.id); if(!cv) return;
      try{ clCharts.push(clDonut(cv, sp)); }catch(ex){
        console.error('donut failed', ex);
        var fb = document.createElement('div'); fb.className = 'cl-fallback'; fb.setAttribute('role', 'img');
        fb.setAttribute('aria-label', cv.getAttribute('aria-label') || ''); fb.textContent = clCenterText(sp);
        if(cv.parentNode) cv.parentNode.replaceChild(fb, cv);
      }
    });
  }

  // ── P2. 略式実効デュレーション ────────────────────────────────────────────
  var DUR_TOKEN_JA = {
    v0_nonpositive: '基準額が0以下のため算出せず',
    dash_in_jpy_up50: '円金利+50bpの列が開示されていないため算出せず',
    dash_in_jpy_down50: '円金利−50bpの列が開示されていないため算出せず'
  };
  var DUR_FLAG_JA = { negative_duration: 'マイナス値', low_precision: '低精度' };
  var DUR_SIDES = [
    { key: 'assets', name: '資産(総資産)', caveats: ['assets_total'] },
    { key: 'liabilities', name: '負債(保険負債、MOCEを除く)', caveats: ['liabilities_ex_moce', 'negative_base'] }
  ];
  var DUR_HEAD_CAVEATS = ['convexity', 'economic_value_not_cashflow', 'ufr_parallel'];
  function durReasonJa(code){
    if(!code) return '算出せず';
    var toks = String(code).split(/[,\s]+/).filter(Boolean), out = [];
    var up = toks.indexOf('dash_in_jpy_up50') >= 0, dn = toks.indexOf('dash_in_jpy_down50') >= 0;
    toks.forEach(function(t){
      if(t === 'dash_in_jpy_up50' || t === 'dash_in_jpy_down50') return;
      var s = DUR_TOKEN_JA[t] || '算出せず';
      if(out.indexOf(s) < 0) out.push(s);
    });
    if(up && dn) out.push('円金利±50bpの列が開示されていないため算出せず');
    else if(up) out.push(DUR_TOKEN_JA.dash_in_jpy_up50);
    else if(dn) out.push(DUR_TOKEN_JA.dash_in_jpy_down50);
    return out.join('／');
  }
  // 레코드 수준 reason: "yen +-50bp scenarios not disclosed (up: <상태>, down: <상태>)" 형식 → 일본어
  function durRecordReasonJa(reason){
    var m = /up:\s*([a-z0-9_]+)\s*,\s*down:\s*([a-z0-9_]+)/i.exec(String(reason || ''));
    if(!m) return '円金利±50bpのシナリオが開示されていないため算出せず';
    var a = SCEN_STATUS_JA[m[1]], b = SCEN_STATUS_JA[m[2]];
    var tail = (a && b) ? (m[1] === m[2] ? '(' + a + ')' : '(+50bp: ' + a + '／−50bp: ' + b + ')') : '';
    return '円金利±50bpのシナリオが開示されていないため算出せず' + tail;
  }
  // 소수 1자리, 음수는 △. 반올림은 100배 정수에서 하프업(데이터가 소수 2자리라 부동소수 오차를 피한다).
  function fmtYears(v){
    if(v == null || !isFinite(v)) return '―';
    var r = Math.floor((Math.round(Math.abs(v) * 100) + 5) / 10) / 10;
    return (v < 0 && r > 0 ? '△' : '') + r.toFixed(1);
  }
  // 한국 K-ICS.html 의 .dur-strip / .dur-card 와 같은 모양: 면(資産・負債)마다 제목 줄 + 카드 3장(金利上昇時・金利低下時・平均, 平均 이 .lead).
  var DUR_LABELS = ['金利上昇時', '金利低下時', '平均'];
  function renderDuration(c){
    var panel = byId('secDurWrap'), host = byId('durApproxWrap'); if(!host) return;
    var da = c.duration_approx;
    if(!da || typeof da !== 'object'){ host.innerHTML = ''; if(panel) panel.hidden = true; return; }   // 구판 JSON(키 없음): 패널째로 숨김
    if(panel) panel.hidden = false;
    var ids = da.caveat_ids || [];
    var title = '略式実効デュレーション';
    var headHelp = helpHtml(DUR_HEAD_CAVEATS.filter(function(id){ return ids.indexOf(id) >= 0; }).map(function(id){ return caveatJa('duration_approx', id); }), title + 'の補足');
    var head = byId('secDur');
    var fq = c.as_of ? jaFiscalQuarter(c.as_of) : null;   // 한국 패널과 같은 h2 뒤 기준 시점(없으면 만들지 않는다)
    if(head){
      head.innerHTML = esc(title) + derivedBadge() + (fq ? ' <span class="h2-sub">基準時点 ' + esc(fq) + '</span>' : '') + headHelp;
      head.setAttribute('aria-label', title);   // 접근 가능한 이름에 「?」 팝오버 문구가 섞이지 않게 제목만
    }
    if(da.status === 'not_computable'){
      host.innerHTML = '<div class="no-data">' + esc(durRecordReasonJa(da.reason)) + '</div>';
      return;
    }
    host.innerHTML = DUR_SIDES.map(function(s){
      var side = da[s.key];
      var helpIds = s.caveats.filter(function(id){ return ids.indexOf(id) >= 0; });
      var flags = (side && side.flags) || [];
      var chips = '', flagHelp = [];
      flags.forEach(function(f){
        if(!DUR_FLAG_JA[f]) return;
        chips += ' ' + chipHtml(DUR_FLAG_JA[f]);
        flagHelp.push(caveatJa('duration_approx', f));
      });
      var h3 = '<h3 class="dur-h3" aria-label="' + esc(s.name + flags.filter(function(f){ return !!DUR_FLAG_JA[f]; }).map(function(f){ return ' ' + DUR_FLAG_JA[f]; }).join('')) + '">' + esc(s.name) + chips
        + helpHtml(helpIds.map(function(id){ return caveatJa('duration_approx', id); }).concat(flagHelp), s.name + 'の補足') + '</h3>';
      var vals = side ? [side.d_up, side.d_down, side.d_avg] : [null, null, null];
      var allNull = vals.every(function(v){ return v == null; });
      var reason = durReasonJa(side ? side.reason : da.reason);
      var cards = vals.map(function(v, i){
        // 값이 없는 칸: 「―」 + 이유(.dur-sub). 세 칸 모두 없으면 같은 이유를 세 번 쓰지 않고 카드 아래 한 줄(.dur-note)로 둔다.
        var sub = (v == null && !allNull) ? '<div class="dur-sub">' + esc(reason) + '</div>' : '';
        return '<div class="dur-card' + (i === 2 ? ' lead' : '') + '">'
          + '<div class="dur-val' + (v == null ? ' is-none' : '') + '">' + esc(fmtYears(v)) + (v == null ? '' : '<span class="u">年</span>') + '</div>'
          + '<div class="dur-lab">' + DUR_LABELS[i] + '</div>' + sub + '</div>';
      }).join('');
      return h3 + '<div class="dur-strip" role="group" aria-label="' + esc(s.name + ' ' + title + '(単位: 年)') + '">' + cards + '</div>'
        + (allNull ? '<div class="dur-note">' + esc(reason) + '</div>' : '');
    }).join('');
  }

  // ── P3. T7 감응도 행렬 ───────────────────────────────────────────────────
  var smMode = 'delta';   // 'delta'(変化額, 기본) | 'level'(水準) — 회사를 바꿔도 유지
  var smOpen = false;     // <details> 열림 상태 — 테마 전환 등으로 다시 그려도 유지
  function smScenarioLabel(sid){ return labelOf(META, 'sens_' + sid + '_esr_pct', sid); }
  function smCell(rid, v, isDelta){
    if(v == null || !isFinite(v)) return '―';
    if(rid === 'esr_pct') return isDelta ? fmtPP(v) : fmtPct1(v);
    return isDelta ? fmtEokDelta(v, 0) : fmtEok(v);
  }
  function smTableHtml(sl){
    var mm = META && META.sensitivity_levels || {};
    var order = (mm.scenario_order && mm.scenario_order.length) ? mm.scenario_order : Object.keys(sl.scenarios || {});
    var rowIds = (mm.row_ids && mm.row_ids.length) ? mm.row_ids : Object.keys(sl.rows || {});
    rowIds = rowIds.filter(function(r){ return sl.rows && sl.rows[r]; });
    var isDelta = smMode === 'delta';
    var th = '<th scope="col" class="sm-row-h">項目</th><th scope="col" class="num">基準</th>';
    var groups = {};
    order.forEach(function(sid){
      var st = (sl.scenarios || {})[sid] || 'not_extracted';
      var dim = st !== 'disclosed';
      th += '<th scope="col" class="num' + (dim ? ' sm-dim' : '') + '">' + esc(smScenarioLabel(sid))
        + (dim ? '<span class="sm-tag">' + esc(SCEN_TAG_JA[st] || '未収録') + '</span>' : '') + '</th>';
      if(dim){ (groups[st] = groups[st] || []).push(smScenarioLabel(sid)); }
    });
    var body = rowIds.map(function(rid){
      var arr = sl.rows[rid];
      var tr = '<tr><th scope="row" class="sm-row">' + esc(labelOf(META, rid, rid)) + '</th>'
        + '<td class="num">' + esc(smCell(rid, arr[0], false)) + '</td>';
      order.forEach(function(sid, i){
        var dim = ((sl.scenarios || {})[sid] || 'not_extracted') !== 'disclosed';
        var v = arr[isDelta ? 2 + 2 * i : 1 + 2 * i];
        tr += '<td class="num' + (dim ? ' sm-dim' : '') + '">' + esc(dim ? '―' : smCell(rid, v, isDelta)) + '</td>';
      });
      return tr + '</tr>';
    }).join('');
    var notes = Object.keys(groups).map(function(st){
      var txt = st === 'omitted_below_1pp' ? omitText(sl) : (SCEN_STATUS_JA[st] || '未収録');
      return '<div class="donut-note sm-note">' + esc(groups[st].join('・')) + ': ' + esc(txt) + '</div>';
    }).join('');
    return notes
      + '<div class="table-container sm-scroll"><table class="esr-table sm-table" aria-label="資産・負債を含む感応度の詳細(' + (isDelta ? '変化額' : '水準') + ')">'
      + '<thead><tr>' + th + '</tr></thead><tbody>' + body + '</tbody></table></div>';
  }
  function renderSensMatrix(c){
    var host = byId('sensMatrixWrap'); if(!host) return;
    var sl = c.sensitivity_levels;
    if(!sl || typeof sl !== 'object'){ host.innerHTML = ''; return; }
    var title = '資産・負債を含む感応度の詳細';
    if(sl.status !== 'disclosed' || !sl.rows || !Object.keys(sl.rows).length){
      var why = sl.status === 'omitted_below_1pp' ? omitText(sl) : (SCEN_STATUS_JA[sl.status] || '未収録');
      host.innerHTML = '<p class="jp-dim sm-dim-line">' + esc(title) + ': ' + esc(why) + '</p>';
      return;
    }
    host.innerHTML = '<details class="sm-details jp-sub"' + (smOpen ? ' open' : '') + '><summary>' + esc(title) + '</summary>'
      + '<div class="sm-ctl"><div class="seg-toggle" role="group" aria-label="表示切替">'
      + '<button type="button" class="seg-btn" data-mode="delta" aria-pressed="false">変化額</button>'
      + '<button type="button" class="seg-btn" data-mode="level" aria-pressed="false">水準</button></div>'
      + '<span class="small-muted sm-unit">単位: 億円(ソルベンシー・マージン比率の行は%・pp)</span></div>'
      + '<div class="sm-body"></div></details>';
    var det = host.querySelector('details'), bodyEl = host.querySelector('.sm-body');
    function paint(){
      bodyEl.innerHTML = smTableHtml(sl);
      [].forEach.call(host.querySelectorAll('.seg-btn'), function(b){
        var on = b.getAttribute('data-mode') === smMode;
        b.classList.toggle('active', on); b.setAttribute('aria-pressed', String(on));
      });
    }
    [].forEach.call(host.querySelectorAll('.seg-btn'), function(b){
      b.addEventListener('click', function(){ smMode = b.getAttribute('data-mode'); paint(); });
    });
    det.addEventListener('toggle', function(){ smOpen = det.open; });
    paint();
  }

  // 그 밖의 공시항목(axes) 라우팅: 準備金(cat_reserve_*/…_reserve…) → 決算 페이지 '準備金', 再保険(reins_*) → その他開示 '再保険',
  // 旧基準 SMR(smr_*) → ESR 페이지 참고 줄, 나머지 숫자 항목 → その他開示 'その他'.
  var AXES_ROUTE = [
    {wrap:'secReservesWrap', body:'reservesTableBody', test:function(k){ return /reserve/.test(k); }},
    {wrap:'secReinsWrap', body:'reinsTableBody', test:function(k){ return /^reins_/.test(k); }},
    {wrap:'smrOldWrap', body:'smrOldTableBody', test:function(k){ return /^smr_/.test(k); }},
    {wrap:'secAxesWrap', body:'axesTableBody', test:function(){ return true; }}
  ];
  function renderAxes(c){
    var axes = c.axes || {};
    var allKeys = Object.keys(axes).filter(function(k){ return typeof axes[k] === 'number' && k.charAt(0) !== '_'; });
    var taken = {};
    AXES_ROUTE.forEach(function(r){
      var wrap = byId(r.wrap), body = byId(r.body);
      var keys = allKeys.filter(function(k){ return !taken[k] && r.test(k); });
      keys.forEach(function(k){ taken[k] = true; });
      if(!wrap || !body) return;
      renderAxesTable(axes, keys, wrap, body);
    });
  }
  function renderAxesTable(axes, keys, wrap, body){
    // axes 층에는 esr_status/air_used 같은 문자열 플래그, cat_reserve_by_line/_reins_rating_buckets
    // 같은 중첩 dict, esr_placeholder_locations 같은 배열도 섞여 온다(실측 jp/jesr_detail.json,
    // 2026-09-12). 이 표는 "값 표"(티켓 예시: 異常危険準備金 등 숫자 항목)이므로 숫자 항목만 남긴다
    // — 문자열/배열/객체는 자동으로 제외되어 별도 스킵리스트가 필요 없다.
    // '_' 로 시작하는 키는 추출기 내부 보조값(_reserve_total_all 등) — 화면 제외(2026-09-13).
    if(!keys.length){ wrap.hidden = true; return; }
    wrap.hidden = false;
    var unit = function(k){ var l=META.labels&&META.labels[k]; return l&&l.unit; };
    body.innerHTML = keys.map(function(k){
      var v = axes[k], u = unit(k);
      var disp = (typeof v === 'number') ? (u==='pct' ? fmtPct1(v) : (u==='JPY_million' ? fmtEok(v)+'億円' : v.toLocaleString('ja-JP'))) : esc(v);
      return '<tr><td>'+esc(labelOf(META, k, k))+'</td><td class="num">'+disp+'</td></tr>';
    }).join('');
  }

  // ── 貸借対照表 T자형 (jgaap.html, owner 2026-09-13; IFRS17.html Panel 1 미러) ────────────────────────
  // 입력: c.bs = {status, tree:[{id,label_ja,depth,sign,cur,prev,parent,derived}], checks} (bs 층 builder 계약).
  // 총계 3행(depth 0) = 資産/負債/純資産 존, depth 1 = 존 안의 행(막대 = 총계 대비 비중), depth 2 = 하위행(합계 미포함).
  var BS_ZONE = { bs_assets_total:'assets', bs_liabilities_total:'liabilities', bs_net_assets_total:'net_assets' };
  var BS_TOT_EL = { assets:'bsTotAssets', liabilities:'bsTotLiabilities', net_assets:'bsTotNetAssets' };
  var BS_DET_EL = { assets:'bsDetailAssets', liabilities:'bsDetailLiabilities', net_assets:'bsDetailNetAssets' };
  var bsOpen = { assets:false, liabilities:false, net_assets:false };
  function renderBs(c){
    var wrap = byId('secBsWrap'); if(!wrap) return;
    var bs = c.bs;
    if(!bs || bs.status !== 'extracted' || !bs.tree || !bs.tree.length){ wrap.hidden = true; return; }
    wrap.hidden = false;
    var tree = bs.tree, byZone = { assets:[], liabilities:[], net_assets:[] }, totals = {};
    var zone = null;
    tree.forEach(function(n){
      if(n.depth === 0){ zone = BS_ZONE[n.id] || null; if(zone) totals[zone] = n; return; }
      if(zone) byZone[zone].push(n);
    });
    Object.keys(BS_TOT_EL).forEach(function(z){
      var t = totals[z], el = byId(BS_TOT_EL[z]);
      if(el){ el.textContent = t ? fmtEok(t.cur) : '—'; el.title = t ? fmtMillionTip(t.cur) : ''; }
      var det = byId(BS_DET_EL[z]); if(!det) return;
      var tot = (t && t.cur) ? Math.abs(t.cur) : 0;
      det.innerHTML = byZone[z].map(function(n){
        var pct = (tot > 0 && n.cur != null) ? Math.max(0, Math.min(100, Math.abs(n.cur)/tot*100)) : 0;
        var cls = 'bs-l2-row' + (n.derived ? ' bs-l2-row-residual' : '') + (n.depth >= 2 ? ' bs-l2-row-sub' : '');
        return '<div class="'+cls+'"><span class="bs-l2-lab">'+esc(n.label_ja || labelOf(META, n.id, n.id))+'</span>'
          + '<span class="bs-l2-val" title="'+esc(fmtMillionTip(n.cur))+'">'+esc(fmtEok(n.cur))+'</span>'
          + (n.depth >= 2 ? '<span></span>' : '<span class="bs-l2-bar-track"><span class="bs-l2-bar" style="width:'+pct.toFixed(1)+'%"></span></span>')
          + '</div>';
      }).join('');
      det.hidden = !bsOpen[z];
    });
    // 負債:純資産 실제 비율로 우측 두 존 높이 배분(IFRS17.html 과 같은 시각 규칙)
    var L = totals.liabilities && totals.liabilities.cur, E = totals.net_assets && totals.net_assets.cur;
    var zl = byId('bsZoneLiab'), ze = byId('bsZoneEquity');
    if(zl && ze && L > 0 && E > 0){ zl.style.flexGrow = String(Math.max(1, L / (L + E) * 10)); ze.style.flexGrow = String(Math.max(1, E / (L + E) * 10)); }
    wrap.querySelectorAll('.subtoggle[data-zone]').forEach(function(btn){
      var z = btn.dataset.zone;
      btn.textContent = bsOpen[z] ? '−' : '+'; btn.setAttribute('aria-expanded', String(bsOpen[z]));
      btn.onclick = function(){
        bsOpen[z] = !bsOpen[z];
        var det = byId(BS_DET_EL[z]); if(det) det.hidden = !bsOpen[z];
        btn.textContent = bsOpen[z] ? '−' : '+'; btn.setAttribute('aria-expanded', String(bsOpen[z]));
        btn.title = '内訳を' + (bsOpen[z] ? '閉じる' : '展開');
      };
    });
    // 2기 비교표(当期末/前期末/増減) — 트리 전부, 들여쓰기
    var body = byId('bsTableBody');
    if(body){
      body.innerHTML = tree.map(function(n){
        var isTot = n.depth === 0;
        return '<tr'+(isTot ? ' class="total-row"' : '')+'><td style="padding-left:'+(8 + n.depth*16)+'px">'+esc(n.label_ja || labelOf(META, n.id, n.id))+(n.derived ? ' <span class="small-muted">(差引)</span>' : '')+'</td>'
          + '<td class="num" title="'+esc(fmtMillionTip(n.cur))+'">'+esc(fmtEok(n.cur))+'</td>'
          + '<td class="num" title="'+esc(fmtMillionTip(n.prev))+'">'+esc(fmtEok(n.prev))+'</td>'
          + '<td class="num">'+esc(fmtEokDelta(n.cur, n.prev))+'</td></tr>';
      }).join('');
    }
    var cap = byId('bsCap');
    if(cap) cap.textContent = '法定決算(J-GAAP)の貸借対照表。' + (bs.as_of ? '基準日 ' + jaDate(bs.as_of) + '。' : '') + (bs.source_doc ? ' 出所: ' + jaOnly(String(bs.source_doc)).split('/').pop() : '');
    var badge = byId('bsBadge');
    if(badge){
      var ch = bs.checks || {}, ok = ch.assets_eq_liab_plus_equity;
      if(ok === true || ok === false){
        badge.style.display = 'inline-flex'; badge.className = 'repro-badge ' + (ok ? 'ok' : 'warn');
        badge.textContent = (ok ? '✓' : '△') + ' 資産 = 負債 + 純資産';
      } else badge.style.display = 'none';
    }
  }

  // 損益の内訳(当期純利益ウォーターフォール + 当期/前期表)。inbox 20260912T1330Z。
  // データは c.profit(jp/jesr_detail.json)。IFRS17.html の PL ウォーターフォールと同じ
  // custom renderItem 方式(0線を跨ぐ棒も正しく描ける — reference_waterfall_zero_crossing)。
  var PL_ACCOUNTING_BASIS_JA = {
    jgaap: '日本基準(J-GAAP)', ifrs: 'IFRS', ifrs17: 'IFRS17', us_gaap: '米国会計基準(US-GAAP)'
  };
  var PL_RATIO_JA = {
    pl_loss_ratio_pct: '損害率', pl_expense_ratio_pct: '事業費率', pl_combined_ratio_pct: '合算率'
  };
  var PL_PCT_KEYS = {pl_loss_ratio_pct:1, pl_expense_ratio_pct:1, pl_combined_ratio_pct:1};

  // items と core(生保の基礎利益・三利源は core 専用)の両方から当期値を引く。
  function plEntry(p, id){
    var e = p.items && p.items[id]!=null ? p.items[id] : null;
    if(!e && p.core) e = p.core[id]!=null ? p.core[id] : null;
    return e;
  }
  function plCur(p, id){ var e=plEntry(p,id); return (e && e.cur!=null) ? e.cur : null; }

  function buildProfitWaterfallBars(p, isMobile){
    var isLife = !!(p.core && Object.keys(p.core).length);
    var bars = [], skipped = [];
    function xl(short, full){ return isMobile ? short : full; }
    function addFlow(ja, short, v){
      if(v==null){ skipped.push(ja); return; }
      bars.push({ja:ja, xLabel:xl(short, ja), cur:v, role:'flow'});
    }
    function addEnd(ja, short, v){
      if(v==null){ skipped.push(ja); return; }
      bars.push({ja:ja, xLabel:xl(short, ja), cur:v, role:'end'});
    }

    if(isLife){
      // 생보(10월 이후): 三利源 → 基礎利益 → キャピタル損益 → 臨時損益 → 経常利益。
      addFlow('利差損益', '利差', plCur(p, 'pl_interest_margin'));
      addFlow('危険差損益', '危険差', plCur(p, 'pl_mortality_margin'));
      addFlow('費差損益', '費差', plCur(p, 'pl_expense_margin'));
      addEnd('基礎利益', '基礎利益', plCur(p, 'pl_core_profit'));
      addFlow('キャピタル損益', 'キャピタル', plCur(p, 'pl_capital_gains'));
      addFlow('臨時損益', '臨時損益', plCur(p, 'pl_extraordinary_pl'));
    } else {
      // 손보: 保険引受利益 → 資産運用損益 → その他経常損益(差引) → 経常利益。
      var uw = plCur(p, 'pl_underwriting_profit');
      var inv = plCur(p, 'pl_investment_pl');
      var ord = plCur(p, 'pl_ordinary_profit');
      addFlow('保険引受利益', '引受利益', uw);
      addFlow('資産運用損益', '運用損益', inv);
      var other = (uw!=null && inv!=null && ord!=null) ? (ord - uw - inv) : null;
      addFlow('その他経常損益(差引)', 'その他(差引)', other);
    }

    addEnd('経常利益', '経常利益', plCur(p, 'pl_ordinary_profit'));

    // 特別損益 = 特別利益 − 特別損失。片方だけ非公表(欠測キー)なら0扱い、両方欠測ならスキップ。
    var gains = plCur(p, 'pl_extraordinary_gains');
    var losses = plCur(p, 'pl_extraordinary_losses');
    if(gains==null && losses==null){ skipped.push('特別損益'); }
    else { bars.push({ja:'特別損益', xLabel:'特別損益', cur:(gains||0)-(losses||0), role:'flow'}); }

    var tax = plCur(p, 'pl_income_taxes');
    addFlow('法人税等', '法人税等', tax!=null ? -Math.abs(tax) : null);

    addEnd('当期純利益', '当期純利益', plCur(p, 'pl_net_income'));

    return {bars:bars, skipped:skipped, isLife:isLife};
  }

  function drawProfitWaterfall(bars){
    var el = document.getElementById('chartProfitWaterfall');
    if(!el || typeof echarts === 'undefined') return;
    if(profitWaterfallChart){ try{ profitWaterfallChart.dispose(); }catch(e){} }
    profitWaterfallChart = echarts.init(el, null, {renderer:'canvas'});

    var isMobile = window.matchMedia('(max-width:640px)').matches;
    var xs = bars.map(function(b){ return b.xLabel; });
    var geo = []; var running = 0;
    bars.forEach(function(b){
      if(b.cur==null){ geo.push({missing:true, at:running}); return; }
      if(b.role==='end'){ geo.push({y0:0, y1:b.cur, color:'#0d6efd'}); running=b.cur; }
      else { var end=running+b.cur; geo.push({y0:running, y1:end, color: b.cur>=0 ? '#22c55e' : '#ef4444'}); running=end; }
    });

    var vals = [0]; geo.forEach(function(g){ if(!g.missing){ vals.push(g.y0, g.y1); } });
    var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals);
    var pad = Math.max((hi-lo)*0.12, 10);
    var yMin = lo < 0 ? Math.floor((lo-pad)/10)*10 : 0, yMax = Math.ceil((hi+pad)/10)*10;

    var ariaBits = bars.map(function(b){ return b.ja + ' ' + fmtEok(b.cur) + '億円'; }).join('、');
    el.setAttribute('aria-label', '当期純利益の内訳。' + ariaBits + '。');

    profitWaterfallChart.setOption({
      backgroundColor:'transparent',
      tooltip:Object.assign(window.IQTheme ? IQTheme.echartsTooltip() : {}, {
        trigger:'axis', axisPointer:{type:'shadow'},
        formatter: function(items){
          var i = items[0].dataIndex, b = bars[i];
          if(!b || b.cur==null) return '<b>'+(b?b.ja:'')+'</b><br/>データなし';
          var sign = b.cur<0 ? '△' : (b.role==='flow' ? '+' : '');
          return '<b>'+b.ja+'</b><br/>'+sign+Math.abs(b.cur/100).toLocaleString('ja-JP',{maximumFractionDigits:1})+'億円';
        }
      }),
      grid:{left:isMobile?36:48, right:isMobile?6:16, top:40, bottom: isMobile?84:64},
      xAxis:{
        type:'category', data:xs,
        axisLabel:{color:TH.ink, fontSize:isMobile?10:11, interval:0,
                   rotate:isMobile?45:30, margin:isMobile?6:8},
        axisLine:{lineStyle:{color:TH.grid}}, axisTick:{show:false},
      },
      yAxis:{
        type:'value', name:'(億円)', min:yMin, max:yMax,
        nameGap:12, nameTextStyle:{color:TH.muted, fontSize:11},
        axisLabel:{color:TH.muted, fontSize:11, formatter:function(v){ return (v/100).toLocaleString('ja-JP'); }},
        splitLine:{lineStyle:{color:TH.grid}},
      },
      series:[{
        type:'custom',
        renderItem: function(params, api){
          var idx = params.dataIndex, g = geo[idx], b = bars[idx];
          if(!g) return;
          var xPix = api.coord([idx,0])[0];
          var bw = Math.max(10, api.size([1,0])[0]*0.55);
          if(g.missing){
            var yc = api.coord([idx, g.at||0])[1];
            return {type:'group', children:[
              {type:'rect', shape:{x:xPix-bw/2, y:yc-4, width:bw, height:8}, style:{fill:'rgba(173,181,189,0.55)'}},
              {type:'text', style:{text:'非公表', x:xPix, y:yc-10, textAlign:'center', fill:TH.muted, fontSize:9}},
            ]};
          }
          var yHi = api.coord([idx, Math.max(g.y0,g.y1)])[1];
          var yLo = api.coord([idx, Math.min(g.y0,g.y1)])[1];
          var isTot = b.role!=='flow';
          var txt = (b.cur<0?'△':(b.role==='flow'?'+':'')) + Math.abs(b.cur/100).toLocaleString('ja-JP',{maximumFractionDigits:1});
          return {type:'group', children:[
            {type:'rect', shape:{x:xPix-bw/2, y:yHi, width:bw, height:Math.max(1,yLo-yHi)}, style:{fill:g.color}},
            {type:'text', style:{text:txt, x:xPix, y:yHi-4, textAlign:'center', textVerticalAlign:'bottom',
              fill:TH.text, fontSize:isTot?11:10, fontWeight:isTot?'bold':'normal'}},
          ]};
        },
        data: geo.map(function(g){ return (g && !g.missing) ? [g.y0, g.y1] : [0,0]; }),
        z:2,
      }],
    }, true);
    requestAnimationFrame(function(){ if(profitWaterfallChart){ try{ profitWaterfallChart.resize(); }catch(e){} } });
  }

  // 損益 표 = profit_flow 선별 흐름만(owner 2026-09-13). 상단은 상대방 기준 두 블록 元受収支 / 再保険収支
  // (owner 2026-09-13 (2): 受再는 사실상 出再 재원이라 한 블록, 出再保険手数料 포함). 각 블록은 [+] 로 구성항목(row.parts)
  // 전개. 구성항목·부호·값은 builder(build_profit_flow)가 넣어 준다 — 페이지는 계산하지 않는다. 전 항목은 details 표.
  var PROFIT_FOOT_2BLOCK = '再保険収支＝(受再正味保険料−受再正味保険金)−支払再保険料＋回収再保険金＋出再保険手数料。'
    + '自賠責・地震保険はプール経由で受再・出再の双方に計上されるため、商業再保険のコストとは一致しません。'
    + '出再保険手数料は損益計算書の注記(当期のみ)から取得しているため、前期欄が空欄の行があります。'
    + 'その他収支は保険引受利益から上の各行を差し引いた残差(積立保険料・満期返戻金・支払備金/責任準備金の繰入戻入等)です。';
  function flowCells(cur, prev, sign){
    var c = fmtEok(cur), p = fmtEok(prev);
    if(sign === '-'){ if(cur!=null && cur!==0) c = '△'+c; if(prev!=null && prev!==0) p = '△'+p; }
    return '<td class="num" title="'+esc(fmtMillionTip(cur))+'">'+esc(c)+'</td>'
         + '<td class="num" title="'+esc(fmtMillionTip(prev))+'">'+esc(p)+'</td>'
         + '<td class="num">'+esc(fmtEokDelta(cur, prev))+'</td>';
  }
  function renderProfitTable(p, pfBlock){
    var items = p.items || {};
    // profit_flow 는 회사 레벨 블록 {sector, rows[], missing[], checks} (builder 계약)
    var flow = (pfBlock && pfBlock.rows) || [];
    var rows = [];
    flow.forEach(function(f){
      var signTxt = f.sign === '=' ? '＝' : (f.sign === '-' ? '－' : (f.sign === '+' ? '＋' : '±'));
      var parts = f.parts || [];
      var has = parts.length > 0;
      if(has && subOpen['pf_'+f.id] === undefined) subOpen['pf_'+f.id] = false;
      var toggle = has ? ' <button type="button" class="subtoggle" data-group="pf_'+esc(f.id)+'" aria-expanded="'+subOpen['pf_'+f.id]+'" title="内訳">'+(subOpen['pf_'+f.id]?'−':'+')+'</button>' : '';
      // 라벨은 스키마(_meta.labels) 우선 — 추출 원문 라벨은 "合計" 같은 표 안 행 이름이 섞여 온다(pl_investment_pl).
      var lab = labelOf(META, f.id, null) || f.label_ja || f.id;
      rows.push('<tr'+(f.sign==='='?' class="total-row"':'')+'><td>'+esc(lab)+(f.derived?' <span class="small-muted">(差引)</span>':'')+toggle+'</td>'
        + '<td class="sign">'+signTxt+'</td>' + flowCells(f.cur, f.prev, f.sign) + '</tr>');
      parts.forEach(function(b){
        rows.push('<tr class="subrow-pf_'+esc(f.id)+'"'+(subOpen['pf_'+f.id]?'':' style="display:none"')+'><td class="subitem" style="padding-left:28px">'+esc(labelOf(META, b.id, null) || b.label_ja || b.id)+'</td>'
          + '<td class="sign">'+(b.sign==='-'?'－':'＋')+'</td>' + flowCells(b.cur, b.prev, b.sign) + '</tr>');
      });
    });
    var body = document.getElementById('profitTableBody');
    body.innerHTML = rows.join('') || '<tr><td colspan="5" class="small-muted">データがありません。</td></tr>';
    // 2026-09-15: profit_flow(元受収支→再保険収支→…의 단계표)는 本編까지 읽은 회사에만 있다.
    // 법정 損益計算書만 실은 회사(ratio_only 19사)는 flow 가 없어 이 표가 「データがありません。」
    // 한 줄로 남았다(실측) — 빈 표를 보이느니 접고, 대신 전 항목표를 펼쳐 그쪽을 본문으로 쓴다.
    // 3개 페이지가 같은 스크립트를 쓰므로 HTML 3벌을 고치지 않고 DOM 에서 찾아 처리한다.
    var hasFlow = rows.length > 0;
    var flowTbl = document.getElementById('profitTable');
    if(flowTbl && flowTbl.parentElement) flowTbl.parentElement.hidden = !hasFlow;
    var allTbl = document.getElementById('profitAllTable');
    var det = allTbl && allTbl.closest ? allTbl.closest('details') : null;
    if(det){
      det.open = !hasFlow;
      var sm = det.querySelector('summary');
      if(sm) sm.textContent = hasFlow ? '全項目を表示' : '損益計算書（全項目）';
    }
    var fn = document.getElementById('profitFlowNote');
    if(fn){ var twoBlock = flow.some(function(f){ return f.id === 'pf_reins_balance'; }); fn.hidden = !twoBlock; fn.textContent = twoBlock ? '※ ' + PROFIT_FOOT_2BLOCK : ''; }
    body.querySelectorAll('.subtoggle').forEach(function(btn){
      btn.addEventListener('click', function(){
        var g = btn.dataset.group; subOpen[g] = !subOpen[g];
        btn.textContent = subOpen[g] ? '−' : '+'; btn.setAttribute('aria-expanded', String(subOpen[g]));
        body.querySelectorAll('tr.subrow-'+g).forEach(function(tr){ tr.style.display = subOpen[g] ? '' : 'none'; });
      });
    });
    // 전 항목(접힘)
    var all = Object.keys(items).filter(function(k){ return !PL_PCT_KEYS[k]; }).map(function(k){
      var e = items[k];
      return '<tr><td>'+esc(labelOf(META, k, k))+'</td>' + flowCells(e.cur, e.prev, '+') + '</tr>';
    }).join('');
    document.getElementById('profitAllTableBody').innerHTML = all || '<tr><td colspan="4" class="small-muted">—</td></tr>';
  }

  // ── 収益性指標 패널 (owner 2026-09-13: 손해율은 손익표 밖 별도 패널, 5개년 시계열은 ECharts 없이 SVG) ───
  var HIST_RATIO = [
    {key:'hist_loss_ratio_pct', ja:'損害率', color:'#2f6fed'},
    {key:'hist_expense_ratio_pct', ja:'事業費率', color:'#f59e0b'},
    {key:'hist_combined_ratio_pct', ja:'合算率', color:'#1a7f37'}
  ];
  var HIST_TABLE = ['hist_net_premiums_written','hist_ordinary_profit','hist_net_income','hist_total_assets','hist_net_assets',
                    'hist_loss_ratio_pct','hist_expense_ratio_pct','hist_combined_ratio_pct','hist_smr_old_pct','hist_esr_pct'];
  function ratioCard(label, cur, prev, badgeHtml){
    var d = (cur!=null && prev!=null) ? (cur-prev) : null;
    return '<div class="jcard"><div class="jcard-val">'+esc(fmtPct1(cur))+'</div><div class="jcard-lab">'+esc(label)
      + (d!=null ? ' <span class="small-muted">(前期比 '+esc(fmtPP(d))+')</span>' : '') + (badgeHtml||'') + '</div></div>';
  }
  function svgLineChart(years, series){
    // series: [{ja,color,values[]}] — null 은 선을 끊는다. y 0~max(100, 최대값)+10.
    var W = 640, H = 220, L = 44, R = 16, T = 14, B = 30;
    var allv = []; series.forEach(function(s){ s.values.forEach(function(v){ if(v!=null) allv.push(v); }); });
    if(!allv.length) return '';
    var ymax = Math.max(100, Math.ceil(Math.max.apply(null, allv)/10)*10 + 10);
    var x = function(i){ return L + (W-L-R) * (years.length>1 ? i/(years.length-1) : 0.5); };
    var y = function(v){ return T + (H-T-B) * (1 - v/ymax); };
    var g = '';
    [0,25,50,75,100].concat(ymax>100?[ymax]:[]).forEach(function(t){ if(t<=ymax) g += '<line x1="'+L+'" y1="'+y(t)+'" x2="'+(W-R)+'" y2="'+y(t)+'" style="stroke:var(--border)" stroke-width="1"/><text x="'+(L-6)+'" y="'+(y(t)+4)+'" font-size="11" text-anchor="end" style="fill:var(--muted)">'+t+'%</text>'; });
    g += '<line x1="'+L+'" y1="'+y(100)+'" x2="'+(W-R)+'" y2="'+y(100)+'" style="stroke:var(--muted)" stroke-width="1" stroke-dasharray="4 3"/>';
    years.forEach(function(yr,i){ g += '<text x="'+x(i)+'" y="'+(H-8)+'" font-size="11" text-anchor="middle" style="fill:var(--muted)">'+esc(yr)+'</text>'; });
    series.forEach(function(s){
      var seg = [], pts = '';
      s.values.forEach(function(v,i){
        if(v==null){ if(seg.length){ pts += '<polyline fill="none" stroke="'+s.color+'" stroke-width="2" points="'+seg.join(' ')+'"/>'; seg=[]; } return; }
        seg.push(x(i)+','+y(v));
        pts += '<circle cx="'+x(i)+'" cy="'+y(v)+'" r="3" fill="'+s.color+'"/><text x="'+x(i)+'" y="'+(y(v)-7)+'" font-size="10" text-anchor="middle" fill="'+s.color+'">'+v.toFixed(1)+'</text>';
      });
      if(seg.length) pts += '<polyline fill="none" stroke="'+s.color+'" stroke-width="2" points="'+seg.join(' ')+'"/>';
      g += pts;
    });
    var legend = series.map(function(s){ return '<span><span class="sw" style="background:'+s.color+'"></span>'+esc(s.ja)+'</span>'; }).join('');
    var label = series.map(function(s){ return s.ja+' '+s.values.map(function(v,i){ return years[i]+' '+(v==null?'—':v.toFixed(1)+'%'); }).join('、'); }).join('。');
    return '<svg viewBox="0 0 '+W+' '+H+'" role="img" aria-label="'+esc(label)+'" style="width:100%;height:auto;max-width:760px">'+g+'</svg><div class="chart-legend">'+legend+'</div>';
  }
  // 손보 종목별 표(by_line: {lines, labels_ja, items{lob_id:{line:{cur,prev}}}}) — 당기 값, 전기는 툴팁.
  function renderLob(c){
    if(!byId('lobWrap')) return;
    var w = document.getElementById('lobWrap'); var bl = c.by_line;
    if(!bl || !bl.items || !bl.lines){ w.hidden = true; return; }
    var cols = [
      {id:'lob_net_premiums_written', ja:'正味収入保険料', pct:false},
      {id:'lob_net_claims_paid', ja:'正味支払保険金', pct:false},
      {id:'lob_loss_ratio_pct', ja:'損害率', pct:true},
      {id:'lob_expense_ratio_pct', ja:'事業費率', pct:true},
      {id:'lob_combined_ratio_pct', ja:'合算率', pct:true}
    ].filter(function(k){ return bl.items[k.id]; });
    if(!cols.length){ w.hidden = true; return; }
    w.hidden = false;
    document.getElementById('lobTableHead').innerHTML = '<tr><th scope="col">種目</th>' + cols.map(function(k){ return '<th scope="col" class="num">'+esc(k.ja)+(k.pct?'':'（億円）')+'</th>'; }).join('') + '</tr>';
    document.getElementById('lobTableBody').innerHTML = bl.lines.map(function(line){
      var isTotal = line === 'total';
      return '<tr'+(isTotal?' class="total-row"':'')+'><td>'+esc((bl.labels_ja||{})[line] || line)+'</td>' + cols.map(function(k){
        var e = (bl.items[k.id]||{})[line] || {};
        var cur = e.cur, prev = e.prev;
        var txt = cur==null ? '—' : (k.pct ? fmtPct1(cur) : fmtEok(cur));
        var tip = prev==null ? '' : ('前期 ' + (k.pct ? fmtPct1(prev) : fmtEok(prev)+'億円'));
        return '<td class="num" title="'+esc(tip)+'">'+esc(txt)+'</td>';
      }).join('') + '</tr>';
    }).join('');
    document.getElementById('lobNote').textContent = '出所: ディスクロージャー誌「保険引受の状況」（種目別）。合計行は損益の内訳と一致。金額は百万円を億円に換算、前期値はツールチップ。';
  }
  // 생보 基礎利益·三利源 추이(core_history: unit JPY_100million = 이미 억엔, labels_ja 동봉)
  function renderCoreHistory(c){
    if(!byId('coreWrap')) return;
    var w = document.getElementById('coreWrap'); var ch = c.core_history;
    if(!ch || !ch.series || !ch.fiscal_years){ w.hidden = true; return; }
    var keys = Object.keys(ch.series).filter(function(k){ return (ch.series[k]||[]).some(function(v){ return v!=null; }); });
    if(!keys.length){ w.hidden = true; return; }
    w.hidden = false;
    var years = ch.fiscal_years;
    document.getElementById('coreTableHead').innerHTML = '<tr><th scope="col">指標</th>' + years.map(function(y){ return '<th scope="col" class="num">'+esc(y)+'</th>'; }).join('') + '</tr>';
    document.getElementById('coreTableBody').innerHTML = keys.map(function(k){
      var lab = (ch.labels_ja||{})[k] || labelOf(META, k, k);
      var isTotal = /core_profit/.test(k);
      return '<tr'+(isTotal?' class="total-row"':'')+'><td>'+esc(lab)+'</td>' + ch.series[k].map(function(v){
        var txt = v==null ? '—' : (typeof v==='number' ? (v<0?'△':'')+Math.abs(v).toLocaleString('ja-JP',{maximumFractionDigits:1}) : String(v));
        return '<td class="num">'+esc(txt)+'</td>';
      }).join('') + '</tr>';
    }).join('');
    document.getElementById('coreNote').textContent = '出所: 各社決算説明資料・ディスクロージャー誌。三利源（利差・危険差・費差）の開示は任意のため、会社により保険関係差（危険差＋費差）のみの場合があります。';
  }
  function renderProfitability(c){
    if(!byId('secProfitabilityWrap')) return;
    var wrap = document.getElementById('secProfitabilityWrap');
    var p = c.profit || {}; var h = c.history || {}; var ratios = p.ratios || {}; var core = p.core || {};
    var hasRatio = !!(ratios.pl_combined_ratio_pct || ratios.pl_loss_ratio_pct);
    var hasCore = !!(core.pl_core_profit || core.pl_interest_margin);
    var hasHist = !!(h.fiscal_years && h.series);
    var hasLob = !!(c.by_line && c.by_line.items);
    var hasCoreHist = !!(c.core_history && c.core_history.series);
    renderLob(c); renderCoreHistory(c);
    if(!hasRatio && !hasCore && !hasHist && !hasLob && !hasCoreHist){ wrap.hidden = true; return; }
    wrap.hidden = false;
    var cards = '';
    if(hasRatio){
      // ratio_caveat(2026-09-14)이 있으면 合算率 카드에 배지 병기 — 값은 다른 회사와 같은 카드·
      // 같은 자리, 표식만 옆에 붙인다(owner: 별도 열로 빼지 말 것).
      cards += ratioCard('損害率', (ratios.pl_loss_ratio_pct||{}).cur, (ratios.pl_loss_ratio_pct||{}).prev)
            + ratioCard('事業費率', (ratios.pl_expense_ratio_pct||{}).cur, (ratios.pl_expense_ratio_pct||{}).prev)
            + ratioCard('合算率', (ratios.pl_combined_ratio_pct||{}).cur, (ratios.pl_combined_ratio_pct||{}).prev, caveatBadgeHtml(c.ratio_caveat)+verifyBadgeHtml(c.value_verified));
    } else if(hasCore){
      ['pl_interest_margin','pl_mortality_margin','pl_expense_margin'].forEach(function(k){
        var e = core[k] || {}; cards += '<div class="jcard"><div class="jcard-val">'+esc(fmtEok(e.cur))+'</div><div class="jcard-lab">'+esc(labelOf(META,k,k))+'（億円）</div></div>';
      });
    }
    document.getElementById('ratioCards').innerHTML = cards;
    renderCombinedRatioBadge(p, document.getElementById('combinedBadge'));
    var chartWrap = document.getElementById('historyChartWrap');
    var head = document.getElementById('historyTableHead'), body = document.getElementById('historyTableBody');
    if(!hasHist){ chartWrap.innerHTML = ''; head.innerHTML = ''; body.innerHTML = ''; document.getElementById('historyNote').textContent = '5事業年度の推移は本編開示後に追加します。'; return; }
    var years = h.fiscal_years, S = h.series;
    var series = HIST_RATIO.filter(function(r){ return S[r.key]; }).map(function(r){ return {ja:r.ja, color:r.color, values:S[r.key]}; });
    chartWrap.innerHTML = series.length ? svgLineChart(years, series) : '';
    head.innerHTML = '<tr><th scope="col">指標</th>' + years.map(function(yr){ return '<th scope="col" class="num">'+esc(yr)+'</th>'; }).join('') + '</tr>';
    body.innerHTML = HIST_TABLE.filter(function(k){ return S[k]; }).map(function(k){
      var isPct = /_pct$/.test(k);
      return '<tr><td>'+esc(labelOf(META, k, k))+(isPct?'':'（億円）')+'</td>' + S[k].map(function(v){
        return '<td class="num"'+(isPct||v==null?'':' title="'+esc(fmtMillionTip(v))+'"')+'>'+esc(v==null?'—':(isPct?fmtPct1(v):fmtEok(v)))+'</td>';
      }).join('') + '</tr>';
    }).join('');
    document.getElementById('historyNote').textContent = '出所: 各社ディスクロージャー誌「主要な経営指標等の推移」。比率は開示行がない年度を「—」で示します。';
  }

  // 合算率(損害率+事業費率)の自己検算バッジ。損保のみ(ratiosがある会社のみ)表示。
  function renderCombinedRatioBadge(p, badge){
    var ratios = p.ratios || {};
    var loss = ratios.pl_loss_ratio_pct, exp = ratios.pl_expense_ratio_pct, comb = ratios.pl_combined_ratio_pct;
    if(!loss || !exp || !comb){ badge.style.display = 'none'; return; }
    var checks = [];
    ['cur','prev'].forEach(function(period){
      if(loss[period]==null || exp[period]==null || comb[period]==null) return;
      var diff = comb[period] - (loss[period] + exp[period]);
      checks.push({period:period, diff:diff, pass: Math.abs(diff) <= 0.1});
    });
    if(!checks.length){ badge.style.display = 'none'; return; }
    var allPass = checks.every(function(x){ return x.pass; });
    badge.style.display = 'inline-flex';
    badge.className = 'repro-badge ' + (allPass ? 'ok' : 'warn');
    badge.textContent = (allPass ? '✓' : '△') + ' 合算率 = 損害率+事業費率';
    badge.title = checks.map(function(x){
      return (x.period==='cur'?'当期':'前期') + ': 差 ' + (x.diff>=0?'+':'△') + Math.abs(x.diff).toFixed(2) + 'pt';
    }).join(' / ');
  }

  function renderProfit(c){
    var p = c.profit;
    var notExtracted = document.getElementById('profitNotExtracted');
    var body = document.getElementById('profitBody');
    var badge = document.getElementById('combinedBadge');
    if(!body) return;

    if(!p || p.status !== 'extracted'){
      notExtracted.hidden = false;
      body.hidden = true;
      badge.style.display = 'none';
      return;
    }
    notExtracted.hidden = true;
    body.hidden = false;

    var basisText = PL_ACCOUNTING_BASIS_JA[p.accounting_basis] || (p.accounting_basis || '不明');
    var ifrs17Text = p.ifrs17_applied ? 'IFRS17適用' : 'IFRS17未適用';
    document.getElementById('profitBasisNote').textContent =
      '会計基準: ' + basisText + '（' + ifrs17Text + '）。金額は億円換算、百万円単位は数値にカーソルを合わせるとツールチップで確認できます。';

    var isMobile = window.matchMedia('(max-width:640px)').matches;
    var built = buildProfitWaterfallBars(p, isMobile);
    drawProfitWaterfall(built.bars);

    document.getElementById('profitFootnote').textContent = built.skipped.length
      ? ('※非公表のため次の区分は図から省略しています: ' + built.skipped.join('、'))
      : '';

    renderProfitTable(p, c.profit_flow);
  }
})();
