
(() => {
  const PATHS = {
    wf: "../data/ifrs17/viz/csm_waterfall.json",
    amort: "../data/ifrs17/viz/csm_amort_schedule.json",
    pl: "../data/ifrs17/viz/insurance_pl_breakdown.json",
    kpi: "../data/ifrs17/viz/downstream_kpis.json",
    bs: "../data/ifrs17/viz/bs_snapshot.json",
    sen: "../data/ifrs17/viz/sensitivity_heatmap.json",
    nb: "../data/ir/nb_csm_ratio.json",
  };

  const NB_LOOKUP = {
    삼성화재해상보험: { slug: "samsung_fire", bucket: "non_life" },
    현대해상: { slug: "hyundai_marine", bucket: "non_life" },
    DB손해보험: { slug: "db_insurance", bucket: "non_life" },
    KB손해보험: { slug: "kb_insurance", bucket: "non_life" },
    삼성생명: { slug: "samsung_life", bucket: "life" },
    한화생명: { slug: "hanwha_life", bucket: "life" },
  };

  const charts = { wf: null, amort: null, pl: null, nb: null };

  const payload = { wf:null, amort:null, pl:null, kpi:null, bs:null, sen:null, nb:null };
  const ix = {
    wf: new Map(),
    amort: new Map(),
    pl: new Map(),
    kpi: new Map(),
    bs: new Map(),
    sen: new Map(),
  };

  function parseKoNum(x){
    if (x == null) return null;
    if (x === "" || x === "-") return null;
    let s = String(x).trim();
    let neg = false;
    s = s.replace(/,/g, "");
    if (/^\(.+\)$/.test(s)) { neg=true; s=s.slice(1,-1); }
    const n = Number(String(s).replace(/[^0-9.+-]/g, ""));
    if (Number.isNaN(n)) return null;
    return neg ? -n : n;
  }

  function fmtNum(v, maxFrac){
    if (v == null || v === "") return "-";
    if (typeof v === "number"){
      if (!Number.isFinite(v)) return "-";
      const hasFrac = Math.abs(v % 1) > 1e-9;
      return v.toLocaleString("ko-KR", hasFrac ? { minimumFractionDigits:0, maximumFractionDigits:maxFrac||2 } : {});
    }
    const n = parseKoNum(v);
    return n == null ? String(v) : fmtNum(n, maxFrac);
  }

  function indexRows(rows){
    const m=new Map();
    for (const row of rows || []){
      if (!row || !row.company) continue;
      if (!m.has(row.company)) m.set(row.company, []);
      m.get(row.company).push(row);
    }
    return m;
  }

  function firstRow(m,name){
    const a=m.get(name);
    return (a&&a.length)? a[0] : null;
  }

  function destroyCharts(){
    for (const k of Object.keys(charts)){
      try{ charts[k] && charts[k].destroy(); }catch(e){}
      charts[k]=null;
    }
  }

  async function fetchJsonSafe(url){
    try{
      const r=await fetch(url);
      if (!r.ok) throw new Error(String(r.status));
      return await r.json();
    }catch(e){
      console.warn(e);
      return null;
    }
  }

  function waterfall(stageOrder, ko, en, stages){
    const labels = stageOrder.map((k)=>{
      const a=(ko&&ko[k])?String(ko[k]):String(k);
      const b=(en&&en[k])?String(en[k]):"";
      return (b?(a+"\n"+b):a).trim();
    });
    let running=0;
    const base=[], plus=[], minus=[], totals=[];
    for (let idx=0; idx<stageOrder.length; idx++){
      const key=stageOrder[idx];
      const st=stages&&stages[key];
      const raw=st && st.value_mn_krw!=null ? Number(st.value_mn_krw) : null;

      const edge = (idx===0) || (idx===stageOrder.length-1);
      if (edge){
        base.push(null); plus.push(null); minus.push(null); totals.push(raw);
        if (raw!=null && !Number.isNaN(raw)) running=raw;
        continue;
      }
      if (raw==null || Number.isNaN(raw)){
        base.push(null); plus.push(null); minus.push(null); totals.push(null);
        continue;
      }
      const v = raw;
      if (v>=0){
        base.push(running);
        plus.push(v);
        minus.push(null);
        totals.push(null);
        running += v;
      }else{
        base.push(running + v);
        plus.push(null);
        minus.push(-v);
        totals.push(null);
        running += v;
      }
    }
    return {
      labels,
      datasets:[
        { label:"__base", stack:"wf", backgroundColor:"rgba(0,0,0,0)", data: base },
        { label:"+", stack:"wf", backgroundColor:"rgba(34,197,94,0.75)", data: plus },
        { label:"-", stack:"wf", backgroundColor:"rgba(239,68,68,0.72)", data: minus },
        { label:"Total", stack:"wf", backgroundColor:"rgba(59,130,246,0.82)", data: totals },
      ],
    };
  }

  function renderMatrixTable(box, hdr, rows){
    box.innerHTML="";
    const widths=[]
    let maxCols=0
    for(const r of hdr||[]){ maxCols = Math.max(maxCols, Array.isArray(r)?r.length:0) }
    for(const r of rows||[]){ maxCols = Math.max(maxCols, Array.isArray(r)?r.length:0) }

    const table=document.createElement("table")
    const thead=document.createElement("thead")
    for(const row of hdr||[]){
      if(!Array.isArray(row)) continue
      const tr=document.createElement("tr")
      for(let i=0;i<maxCols;i++){
        const th=document.createElement("th")
        const c = i < row.length ? row[i] : ""
        th.textContent = (c==null)? "" : String(c)
        tr.appendChild(th)
      }
      thead.appendChild(tr)
    }

    const tbody=document.createElement("tbody")
    for(const r of rows||[]){
      if(!Array.isArray(r)) continue
      const tr=document.createElement("tr")
      for(let i=0;i<maxCols;i++){
        const td=document.createElement("td")
        const c=i< r.length ? r[i]:""
        const pn=parseKoNum(c)
        td.textContent = pn==null ? (c==null?"":String(c)) : fmtNum(pn, 0)
        if (i>=2) td.className="num"
        tr.appendChild(td)
      }
      tbody.appendChild(tr)
    }
    table.appendChild(thead); table.appendChild(tbody); box.appendChild(table)
  }

  function heatCss(v, absMax){
    const mx = Math.max(Math.abs(absMax||1), 1e-9)
    const t = Math.max(-1, Math.min(1, Number(v)/mx))
    if (t<=0){
      const u=-t;
      return "rgba(239,68,68,"+(0.10+0.55*u)+")"
    }
    const u=t;
    return "rgba(34,197,94,"+(0.11+0.58*u)+")"
  }

  const NB_LINE_COLORS = ["#0d6efd", "#198754", "#fd7e14", "#6f42c1", "#20c997", "#dc3545"];

  function nbChartData(nbJson, slug, bucket){
    if(!nbJson) return { periods: [], datasets: [] };
    const section = nbJson[bucket];
    if(!section||!section[slug]) return { periods: [], datasets: [] };
    const companySeries = section[slug].series;
    if(!companySeries || typeof companySeries!=="object" || Array.isArray(companySeries)){
      return { periods: [], datasets: [] };
    }

    const periodSet = new Set();
    const seriesList = [];
    for (const [key, sub] of Object.entries(companySeries)){
      if(!sub || !Array.isArray(sub.points) || !sub.points.length) continue;
      const byPeriod = new Map();
      for (const p of sub.points){
        if(!p || p.period==null) continue;
        const period = String(p.period);
        const value = Number(p.value);
        if(!Number.isFinite(value)) continue;
        periodSet.add(period);
        byPeriod.set(period, value);
      }
      if(!byPeriod.size) continue;
      seriesList.push({ key, label: sub.label || key, byPeriod });
    }

    const periods = [...periodSet].sort((a,b)=> String(a).localeCompare(String(b), "ko", {numeric:true}));
    const datasets = seriesList.map((s, idx)=>{
      const color = NB_LINE_COLORS[idx % NB_LINE_COLORS.length];
      const isTotal = s.key === "total";
      return {
        label: s.label,
        data: periods.map(p=> s.byPeriod.has(p) ? s.byPeriod.get(p) : null),
        borderColor: color,
        backgroundColor: color + "18",
        borderWidth: isTotal ? 2.5 : 1.5,
        borderDash: isTotal ? [] : [6, 4],
        pointRadius: isTotal ? 4 : 3,
        tension: 0.25,
        spanGaps: true,
        fill: false,
      };
    });

    return { periods, datasets };
  }

  function mountDash(){
    const host=document.getElementById("dashHost");
    host.innerHTML="";
    const tpl=document.getElementById("dashTpl");
    host.appendChild(tpl.content.cloneNode(true));
    return host;
  }

  function q(host, sel){
    return /** @type {HTMLElement|null}*/(host.querySelector(sel));
  }

  function canvasCtx(host,id){
    const c=/** @type {HTMLCanvasElement|null}*/(q(host,id));
    return c? c.getContext("2d"): null;
  }

  function stub(el, show, msg){
    if(!el) return;
    el.style.display = show?"block":"none";
    if (show && msg!=null) el.textContent = msg;
  }

  function renderCompany(company){
    destroyCharts();
    const host=mountDash();

    const wfPay=payload.wf;
    const wfRow= wfPay ? firstRow(ix.wf, company): null;

    stub(q(host,"#wfStub"), !(wfRow && wfRow.status==="ok" && wfRow.stages), wfRow?("status="+String(wfRow.status)): "워터폴 데이터 없음");
    q(host,"#wfMeta").textContent = wfRow? ("공시번호 "+String(wfRow.rcept_no||"-")+", 완결도 "+((wfRow.completeness==null)?"-":String(wfRow.completeness))+", 상태 "+String(wfRow.status)) : "";

    const okWf = !!(wfPay && wfRow && wfRow.status==="ok" && wfRow.stages);
    const ctxWf = canvasCtx(host,"#canvasWf");

    if (okWf && ctxWf){
      const spec = waterfall(wfPay.stage_order||[], wfPay.stage_labels_ko||{}, wfPay.stage_labels_en||{}, wfRow.stages);
      charts.wf=new Chart(ctxWf,{
        type:"bar",
        data:{ labels: spec.labels, datasets: spec.datasets },
        options:{
          responsive:true,maintainAspectRatio:false,
          plugins:{
            legend:{ labels:{ filter:(it)=> it.text !== "__base" } },
            title:{ display:true, text:"CSM 이동(백만원)" },
          },
          scales:{
            x:{ stacked:true, ticks:{ maxRotation:35, minRotation:35, font:{ size:10 } } },
            y:{ stacked:true, ticks:{ callback:(vv)=>{ const x=Number(vv)/1000; return x.toLocaleString("ko-KR",{maximumFractionDigits:1})+"k"; } }, title:{display:true,text:"mn KRW"} },
          },
        },
      })
    }

    const amortPay=payload.amort;
    const amRow= amortPay ? firstRow(ix.amort, company):null;
    const amortOk = !!(amRow && amRow.status==="ok" && amRow.buckets);
    stub(q(host,"#amortStub"), !amortOk, amRow?("status="+String(amRow.status)):"상각 버킷 없음");
    q(host,"#amortCap").textContent = amortOk && amRow.caption ? String(amRow.caption):"";

    if (amortOk){
      const ord=[["y1","1년이내"],["y1_y3","1–3년"],["y3_y5","3–5년"],["y5_plus","5년 초과"],["total","합계"]]
      charts.amort=new Chart(canvasCtx(host,"#canvasAmort"),{
        type:"bar",
        data:{ labels: ord.map(x=>x[1]), datasets:[{ label:String(amRow.row_label||"CSM amort"), backgroundColor:"rgba(99,102,241,0.65)", data: ord.map(([k])=>{const v=amRow.buckets[k]; const n=v==null?NaN:Number(v); return Number.isFinite(n)?n:null}) }]},
        options:{responsive:true,maintainAspectRatio:false, plugins:{legend:{display:false}, title:{display:true,text:"버킷별 상각 규모"}}, scales:{y:{beginAtZero:true, ticks:{ callback:(vv)=> vv.toLocaleString("ko-KR") }}}}
      })
    }

    const plPay=payload.pl;
    const plRow= plPay? firstRow(ix.pl,company):null;
    const plOk = !!(plRow && plRow.status==="ok" && Array.isArray(plRow.table))
    stub(q(host,"#plStub"), !plOk, plRow?("status="+String(plRow.status)):"PL 분해 테이블 없음")
    q(host,"#plCap").textContent = plOk && plRow.caption ? String(plRow.caption):""

    if (plOk){
      const lbls=[]; const vals=[];
      for (const rr of plRow.table||[]){
        if(!Array.isArray(rr) || rr.length<2) continue;
        lbls.push(String(rr[0]||"").trim()||"(기타)")
        const lastCell = rr[rr.length-1];
        const lastV = parseKoNum(lastCell);
        vals.push(lastV == null ? 0 : lastV);
      }
      charts.pl=new Chart(canvasCtx(host,"#canvasPl"),{
        type:"bar",
        data:{ labels: lbls, datasets:[{label:"합계열(표의 마지막 열)", data: vals, backgroundColor:"rgba(14,165,233,0.65)"}] },
        options:{ indexAxis:"y", responsive:true, maintainAspectRatio:false, plugins:{legend:{display:false}, title:{display:true, text:"PL 항목(현재표 합계열)" }}, scales:{x:{ticks:{ callback:(vv)=> vv.toLocaleString("ko-KR") }}}}
      })
    }

    const nbSpec = NB_LOOKUP[company] || null;
    const nbJs = payload.nb;
    q(host,"#nbStub").style.display="none"; q(host,"#nbWrap").style.display="none"; q(host,"#nbStub").textContent="";

    if(!nbSpec){
      q(host,"#nbStub").style.display="block";
      q(host,"#nbStub").textContent = "해당 라인 차트 매핑이 없습니다.(삼성화재해상보험, 현대해상, DB손해보험, KB손해보험, 삼성생명, 한화생명)";
    } else if(!nbJs){
      q(host,"#nbStub").style.display="block";
      q(host,"#nbStub").textContent = "nb_csm_ratio.json 을 불러오지 못했습니다.";
    } else {
      const nbChart = nbChartData(nbJs, nbSpec.slug, nbSpec.bucket);
      if(!nbChart.periods.length || !nbChart.datasets.length){
        q(host,"#nbStub").style.display="block";
        q(host,"#nbStub").textContent = "시계열 포인트가 비어있습니다.";
      } else {
        q(host,"#nbWrap").style.display="block";
        charts.nb=new Chart(canvasCtx(host,"#canvasNb"),{
          type:"line",
          data:{
            labels: nbChart.periods,
            datasets: nbChart.datasets,
          },
          options:{
            responsive:true, maintainAspectRatio:false,
            plugins:{
              legend:{ display: nbChart.datasets.length > 1, position:"top" },
              title:{display:true,text:"NB CSM 비율 (신계약 CSM ÷ 월납월초, IR 공시)" },
              tooltip:{ callbacks:{ label:(ctx)=> `${ctx.dataset.label}: ${fmtNum(Number(ctx.parsed.y),1)}x` } },
            },
            scales:{ y:{ ticks:{ callback:(vv)=> fmtNum(Number(vv),1) + "x" } } }
          },
        })
      }
    }

    const kPick=firstRow(ix.kpi,company);
    const kOk=kPick && kPick.status==="ok"
    stub(q(host,"#kpiStub"), !kOk, kPick?("status="+String(kPick.status)):"KPI 레코드 없음")
    const kwrap=q(host,"#kpiWrap")
    kwrap.innerHTML="";
    if (kOk){
      const defs=[
        ["CSM 의존도(프록시)","csm_dependency",4],
        ["CSM 런웨이(년)","csm_runway_years",2],
        ["스케줄 소진 속도","schedule_run_rate",4],
        ["NB 교체 필요도(프록시)","nb_replacement",2],
      ];
      for (const [title,field,fd] of defs){
        const card=document.createElement("div"); card.className="kpi-card";
        const h=document.createElement("h3"); h.textContent=title;
        const vv=document.createElement("div"); vv.className="val";
        const raw=kPick[field];
        if (raw==null) vv.textContent="-";
        else if (typeof raw==="number") vv.textContent = raw.toLocaleString("ko-KR",{maximumFractionDigits:fd,minimumFractionDigits:0});
        else vv.textContent=String(raw);

        card.appendChild(h); card.appendChild(vv); kwrap.appendChild(card);
      }
    }

    const bPick=firstRow(ix.bs,company);
    const bOk=bPick && bPick.status==="ok"
    stub(q(host,"#bsStub"), !bOk, bPick?("status="+String(bPick.status)):"BS 스냅샷 없음")
    q(host,"#bsCap").textContent = bPick && bPick.caption? String(bPick.caption):""
    q(host,"#bsTable").innerHTML="";
    if (bOk) renderMatrixTable(q(host,"#bsTable"), bPick.header, bPick.table)

    const sPick=firstRow(ix.sen,company);
    const scen = (sPick && Array.isArray(sPick.scenarios)) ? sPick.scenarios : [];
    const sOk = !!(sPick && sPick.status==="ok" && scen.length);
    stub(q(host,"#senStub"), !sOk, sPick?("status="+String(sPick.status)+" / 시나리오 없음"):"민감도 데이터 없음");
    q(host,"#senCap").textContent = sPick && sPick.caption ? String(sPick.caption):""
    q(host,"#senTable").innerHTML="";
    if (sOk){
      const deltas = scen.map(z=> Number(z.csm_delta)).filter(Number.isFinite)
      const absMax = deltas.length? Math.max(...deltas.map(Math.abs)) : 1

      const tbl=document.createElement("table"); const thead=document.createElement("thead"); const tr=document.createElement("tr");
      for(const h of ["위험요인","충격","ΔCSM(백만)","손익영향"]) { const th=document.createElement("th"); th.textContent=h; tr.appendChild(th)}
      thead.appendChild(tr); tbl.appendChild(thead); const tbody=document.createElement("tbody")
      for (const row of scen){
        const rr=document.createElement("tr")
        const t1=document.createElement("td"); t1.textContent= row.risk!=null?String(row.risk):"-"
        const t2=document.createElement("td"); t2.textContent= row.shock!=null?String(row.shock):"-"
        const t3=document.createElement("td"); t3.className="num"; const cd = Number(row.csm_delta); t3.textContent=fmtNum(cd,0); t3.style.background=heatCss(cd, absMax)
        const t4=document.createElement("td"); t4.className="num"; t4.textContent=fmtNum(Number(row.pl_impact),0)
        rr.appendChild(t1); rr.appendChild(t2); rr.appendChild(t3); rr.appendChild(t4)
        tbody.appendChild(rr)
      }
      tbl.appendChild(tbody); q(host,"#senTable").appendChild(tbl)
    }
  }

  function onSelect(){
    const sel=document.getElementById("company");
    const v=sel&&sel.value;
    const dash=document.getElementById("dashHost");
    const hint=document.getElementById("emptyHint");
    if(!v){
      destroyCharts();
      dash.style.display="none"; hint.style.display="block"; dash.innerHTML=""; return;
    }
    dash.style.display="block"; hint.style.display="none";
    renderCompany(v);
  }

  async function boot(){
    const wf=await fetchJsonSafe(PATHS.wf);
    const amort=await fetchJsonSafe(PATHS.amort);
    const plx=await fetchJsonSafe(PATHS.pl);
    const kpix=await fetchJsonSafe(PATHS.kpi);
    const bsx=await fetchJsonSafe(PATHS.bs);
    const senx=await fetchJsonSafe(PATHS.sen);
    const nbx=await fetchJsonSafe(PATHS.nb);

    payload.wf=wf; payload.amort=amort; payload.pl=plx; payload.kpi=kpix; payload.bs=bsx; payload.sen=senx; payload.nb=nbx;

    ix.wf = indexRows(wf && wf.companies);
    ix.amort = indexRows(amort && amort.companies);
    ix.pl = indexRows(plx && plx.companies);
    ix.kpi = indexRows(kpix && kpix.companies);
    ix.bs = indexRows(bsx && bsx.companies);
    ix.sen = indexRows(senx && senx.companies);

    const per = wf && (wf.period || wf.unit || wf.source) ? String(wf.period || wf.source || ""):"";
    const line = document.getElementById("wfPeriodLine");
    if (line) line.textContent = per ? ("워터폴 패킷 컨텍스트: "+per) : ""

    const names = wf && Array.isArray(wf.companies)
      ? Array.from(new Set(wf.companies.map(c=>c.company).filter(Boolean))).sort((a,b)=>a.localeCompare(b,"ko"))
      : [];

    const sel=document.getElementById("company");
    for (let i=sel.options.length-1;i>=1;i--) sel.remove(i);
    for (const nm of names){
      const opt=document.createElement("option"); opt.value=nm; opt.textContent=nm; sel.appendChild(opt)
    }
    sel.addEventListener("change", onSelect);
  }

  boot().catch(()=>{
    const hint=document.getElementById("emptyHint");
    if (hint) hint.textContent="JSON 패치를 불러오지 못했습니다. http 로컬 서버로 파일을 여세요.";
  })
})();
