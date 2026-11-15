"""Stand-alone HTML dashboard (dashboard/casino_integrations.html): one file, Plotly embedded (works offline),
4 tabs, filters by state and provider. SIMULATED aggregates only (fictional providers and states).

Tabs: 1 Content performance · 2 Integration pipeline · 3 Game health · 4 Roadmap priorities (what-if sliders).
Run: python src/build_dashboard.py      open dashboard/casino_integrations.html (#1 ... #4 opens a tab)
"""
from __future__ import annotations

import json

import duckdb
import pandas as pd
from plotly.offline import get_plotlyjs

from config import DASH, FOOTER, OUT, SIM, STATUS


def q(con, sql):
    return con.execute(sql.replace("{SIM}", SIM.as_posix())).df()


def main():
    con = duckdb.connect()
    con.execute(f"CREATE VIEW gd AS SELECT d.*, g.game_type FROM read_parquet('{SIM.as_posix()}/game_daily.parquet') d "
                f"JOIN read_csv_auto('{SIM.as_posix()}/games.csv') g USING (game_id)")
    content = q(con, """SELECT strftime(date_trunc('month', CAST("date" AS DATE)), '%Y-%m') AS m, provider_id AS p, state AS s,
                        game_type AS t, ROUND(SUM(ggr)) AS ggr, SUM(players) AS pd, SUM(sessions) AS ses,
                        COUNT(DISTINCT game_id) AS games FROM gd GROUP BY ALL""")
    newg = q(con, """SELECT strftime(date_trunc('month', f), '%Y-%m') AS m, p, s, t, COUNT(*) AS n FROM (
                       SELECT game_id, provider_id AS p, state AS s, game_type AS t, MIN(CAST("date" AS DATE)) AS f
                       FROM gd WHERE game_id NOT LIKE 'HD-%' GROUP BY ALL) WHERE f > DATE '2025-10-01' GROUP BY ALL""")
    errs = q(con, """SELECT CAST("date" AS VARCHAR) AS d, provider_id AS p, state AS s, SUM(launch_attempts) AS a,
                     SUM(launch_errors) AS e, ROUND(AVG(avg_load_ms)) AS l FROM gd GROUP BY ALL ORDER BY d""")
    wal = pd.read_csv(OUT / "wallet_daily.csv")[["day", "provider_id", "route", "calls", "tech_errors", "rollbacks",
                                                  "rollback_failed", "debit_p95_ms"]]
    wal.columns = ["d", "p", "r", "c", "te", "rb", "rf", "p95"]
    rtp = pd.read_csv(OUT / "rtp_check.csv")[["game_id", "provider_id", "game_type", "volatility", "rounds", "rtp_theoretical",
                                               "rtp_realised", "z", "band_3sd", "naive_flag", "stat_flag"]]
    pipe = pd.read_csv(SIM / "integration_pipeline.csv").fillna("")
    stage = pd.read_csv(OUT / "stage_cycle_time.csv")
    alerts = pd.read_csv(STATUS / "compliance_alerts.csv")
    rk = pd.read_csv(OUT / "nb_roadmap.csv")
    mc = pd.read_csv(OUT / "nb_sensitivity_mc.csv")
    cand = pd.read_csv(SIM / "candidate_providers.csv")
    tg = pd.read_csv(OUT / "type_gap.csv")
    R = json.loads((OUT / "nb_results.json").read_text(encoding="utf-8"))
    st_share = q(con, "SELECT state AS s, SUM(players) AS v FROM gd GROUP BY 1")
    fc = pd.read_csv(OUT / "nb_forecast.csv")
    data = dict(content=content.to_dict("list"), newg=newg.to_dict("list"), errs=errs.to_dict("list"),
                wal=wal.to_dict("list"), rtp=rtp.round(5).to_dict("list"), pipe=pipe.to_dict("list"),
                stage=stage.to_dict("list"), alerts=alerts.to_dict("list"), rk=rk.to_dict("list"), mc=mc.to_dict("list"),
                cand=cand.to_dict("list"), tg=tg.to_dict("list"), st=st_share.to_dict("list"), fc=fc.to_dict("list"),
                ttl=dict(Aggregator=R["forecast"]["agg_ab_p50"], Direct=R["forecast"]["dir_ab_p50"]),
                providers=sorted(content.p.unique().tolist()))
    html = (TEMPLATE.replace("{{PLOTLY}}", get_plotlyjs()).replace("{{FOOTER}}", FOOTER)
            .replace("{{DATA}}", json.dumps(data, separators=(",", ":"), default=str)))
    DASH.parent.mkdir(parents=True, exist_ok=True)
    DASH.write_text(html, encoding="utf-8")
    print("dashboard:", DASH.relative_to(DASH.parents[1]), DASH.stat().st_size // 1024, "KB")


TEMPLATE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Casino Integrations Dashboard</title><style>
:root{--bg:#F4F4F2;--card:#FCFCFB;--ink:#0B0B0B;--ink2:#52514E;--line:#E1E0D9;--blue:#1C5CAB}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:'Segoe UI',system-ui,sans-serif}
.top{position:sticky;top:0;z-index:5;background:var(--card);border-bottom:1px solid var(--line);padding:10px 16px;display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.top b{font-size:15px;margin-right:8px}nav{display:flex;flex-wrap:wrap;gap:6px}
nav button{border:1px solid var(--line);background:var(--bg);padding:7px 12px;border-radius:6px;cursor:pointer;font:inherit;color:var(--ink2)}
nav button.on{background:var(--blue);color:#fff;border-color:var(--blue)}
.filters{margin-left:auto;display:flex;gap:12px;font-size:13px;color:var(--ink2)}select,input{font:inherit;padding:4px;margin-left:4px}
.page{display:none;max-width:1400px;margin:0 auto;padding:14px 16px}.page.on{display:block}
h1{font-size:20px;margin:4px 0 4px}.subt{color:var(--ink2);font-size:13px;margin:0 0 12px}
.tag{font-size:11px;font-weight:700;letter-spacing:.6px;color:#1C5CAB;border:1px solid #86B6EF;border-radius:4px;padding:3px 7px;margin-left:8px;vertical-align:middle}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-bottom:12px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:11px 14px}.kpi b{display:block;font-size:23px}.kpi span{font-size:12px;color:var(--ink2)}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(440px,1fr));gap:12px;margin-bottom:12px}
.box{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px 10px;min-height:120px;overflow:auto}
table{border-collapse:collapse;width:100%;font-size:12.5px}th,td{text-align:left;padding:5px 7px;border-bottom:1px solid var(--line)}th{color:var(--ink2)}
td.n{text-align:right;font-variant-numeric:tabular-nums}tr.hl td{background:#EEF5FD;font-weight:600}.p1{color:#B02E2E;font-weight:700}.p2{color:#9A6A00;font-weight:700}
.note{color:var(--ink2);font-size:12px}.sl{display:flex;flex-wrap:wrap;gap:18px;margin-bottom:10px;font-size:13px;color:var(--ink2)}
footer{text-align:center;color:#898781;font-size:12px;padding:16px}@media(max-width:600px){.two{grid-template-columns:1fr}.filters{margin-left:0}}
</style><script>{{PLOTLY}}</script></head><body>
<div class="top"><b>Casino integrations</b><nav>
<button data-p="1">1. Content performance</button><button data-p="2">2. Integration pipeline</button>
<button data-p="3">3. Game health</button><button data-p="4">4. Roadmap priorities</button></nav>
<div class="filters"><label>State <select id="fs"><option>All</option><option>State A</option><option>State B</option><option>State C</option></select></label>
<label>Provider <select id="fp"><option>All</option></select></label></div></div>

<section class="page" id="p1"><h1>Content performance <span class="tag">SIMULATED</span></h1>
<p class="subt">GGR, players and new games by provider and game type, Oct 2025 - Sep 2026. Filters apply.</p>
<div class="kpis" id="k1"></div><div class="two"><div class="box" id="c1a"></div><div class="box" id="c1b"></div></div>
<div class="two"><div class="box" id="c1c"></div><div class="box" id="c1d"></div></div></section>

<section class="page" id="p2"><h1>Integration pipeline <span class="tag">SIMULATED</span></h1>
<p class="subt">Stages from commercial agreement to launch for every provider project; open items as of 2026-11-13. Provider filter applies.</p>
<div class="kpis" id="k2"></div><div class="box" id="c2a" style="margin-bottom:12px"></div>
<div class="two"><div class="box" id="c2b"></div><div class="box" id="c2c"></div></div></section>

<section class="page" id="p3"><h1>Game health <span class="tag">SIMULATED</span></h1>
<p class="subt">Launch errors, wallet latency and rollbacks, RTP vs volatility-aware bounds, and this week's alerts. Filters apply.</p>
<div class="kpis" id="k3"></div><div class="two"><div class="box" id="c3a"></div><div class="box" id="c3b"></div></div>
<div class="two"><div class="box" id="c3c"></div><div class="box" id="c3d"></div></div></section>

<section class="page" id="p4"><h1>Roadmap priorities <span class="tag">SIMULATED</span></h1>
<p class="subt">Which provider to integrate next. Move the sliders to test the assumptions: the score is recomputed in the page.</p>
<div class="sl"><label>Elasticity factor <input type="range" id="se" min="0.05" max="0.3" step="0.01" value="0.15"> <span id="sev"></span></label>
<label>Direct-integration effort x <input type="range" id="sd" min="0.5" max="2" step="0.1" value="1"> <span id="sdv"></span></label>
<label>Extra days to launch <input type="range" id="st" min="0" max="120" step="10" value="0"> <span id="stv"></span></label>
<label><input type="checkbox" id="sc"> Ignore confidence</label></div>
<div class="two"><div class="box" id="c4a"></div><div class="box" id="c4b"></div></div>
<div class="two"><div class="box" id="c4c"></div><div class="box" id="c4d"></div></div></section>
<footer>{{FOOTER}} · all data on this page SIMULATED (fictional providers, aggregators and states)</footer>
<script>
const D={{DATA}};
const rows=o=>o[Object.keys(o)[0]].map((_,i)=>Object.fromEntries(Object.keys(o).map(k=>[k,o[k][i]])));
const CT=rows(D.content),NG=rows(D.newg),ER=rows(D.errs),WA=rows(D.wal),RT=rows(D.rtp),PI=rows(D.pipe),ST=rows(D.stage),
AL=rows(D.alerts),RK=rows(D.rk),MC=rows(D.mc),CA=rows(D.cand),TG=rows(D.tg),SS=rows(D.st),FC=rows(D.fc);
const TC={'Slot':'#2A78D6','Jackpot slot':'#EB6834','Table':'#1BAF7A','Live dealer':'#EDA100'};
const L=(t,h,x={})=>Object.assign({title:{text:t,font:{size:14}},height:h||330,font:{family:'Segoe UI, sans-serif',size:12,color:'#52514E'},
 paper_bgcolor:'#FCFCFB',plot_bgcolor:'#FCFCFB',margin:{l:55,r:15,t:40,b:40},legend:{orientation:'h',y:-0.18},hovermode:'closest'},x);
const CF={displayModeBar:false,responsive:true};
const $=id=>document.getElementById(id),fmt=(x,d=0)=>x.toLocaleString('en',{maximumFractionDigits:d,minimumFractionDigits:d});
const usd=x=>Math.abs(x)>=1e6?'$'+fmt(x/1e6,2)+'M':Math.abs(x)>=1e3?'$'+fmt(x/1e3,0)+'k':'$'+fmt(x,0);
const kpi=(v,t)=>`<div class="kpi"><b>${v}</b><span>${t}</span></div>`;
D.providers.forEach(p=>{const o=document.createElement('option');o.text=p;$('fp').add(o)});
const F=r=>($('fs').value=='All'||r.s==$('fs').value)&&($('fp').value=='All'||r.p==$('fp').value);
const FP=r=>($('fp').value=='All'||r.p==$('fp').value||r.provider_id==$('fp').value);
const sum=(a,k)=>a.reduce((s,x)=>s+(+x[k]||0),0),uniq=a=>[...new Set(a)].sort();
function grp(a,keys,val){const m={};a.forEach(r=>{const k=keys.map(x=>r[x]).join('|');m[k]=(m[k]||0)+(+r[val]||0)});return m}

function p1(){const c=CT.filter(F),months=uniq(CT.map(r=>r.m)),types=['Slot','Jackpot slot','Table','Live dealer'];
 const q3=c.filter(r=>r.m>='2026-07'),q2=c.filter(r=>r.m>='2026-04'&&r.m<'2026-07');
 $('k1').innerHTML=kpi(usd(sum(q3,'ggr')),'GGR Q3 2026 ('+(sum(q2,'ggr')?((sum(q3,'ggr')/sum(q2,'ggr')-1)*100).toFixed(1)+'% vs Q2':'')+')')+
  kpi(fmt(sum(q3,'pd')),'player-days Q3')+kpi(fmt(sum(q3,'ses')),'sessions Q3')+kpi(usd(sum(q3,'ggr')/Math.max(sum(q3,'ses'),1)),'GGR per session')+
  kpi(fmt(sum(NG.filter(F),'n')),'new game launches (game x state)');
 const g=grp(c,['m','t'],'ggr');
 Plotly.react('c1a',types.map(t=>({type:'bar',name:t,x:months,y:months.map(m=>g[m+'|'+t]||0),marker:{color:TC[t]},hovertemplate:'%{x} '+t+': $%{y:,.0f}<extra></extra>'})),
  L('GGR by month and game type (USD)',330,{barmode:'stack'}),CF);
 const gp=grp(c.filter(r=>r.m>='2026-07'),['p'],'ggr'),ps=Object.keys(gp).sort((a,b)=>gp[a]-gp[b]);
 Plotly.react('c1b',[{type:'bar',orientation:'h',y:ps.map(p=>'Provider '+p),x:ps.map(p=>gp[p]),marker:{color:'#2A78D6'},hovertemplate:'%{y}: $%{x:,.0f}<extra></extra>'}],
  L('GGR by provider, Q3 2026 (USD)',330,{margin:{l:90,r:15,t:40,b:30}}),CF);
 const ses=grp(c.filter(r=>r.m>='2026-07'),['t'],'ses');const gm=grp(c.filter(r=>r.m=='2026-09'),['t'],'games');
 const tot=Object.values(ses).reduce((a,b)=>a+b,0),totg=Object.values(gm).reduce((a,b)=>a+b,0);
 Plotly.react('c1c',[{type:'bar',name:'Share of sessions (Q3)',x:types,y:types.map(t=>(ses[t]||0)/tot),marker:{color:types.map(t=>TC[t])}},
  {type:'bar',name:'Share of live game-state entries (Sep)',x:types,y:types.map(t=>(gm[t]||0)/totg),marker:{color:'#C9C7BF'}}],
  L('Demand vs shelf by game type',330,{barmode:'group',yaxis:{tickformat:'.0%'}}),CF);
 const n=grp(NG.filter(F),['m','t'],'n');
 Plotly.react('c1d',types.map(t=>({type:'bar',name:t,x:months,y:months.map(m=>n[m+'|'+t]||0),marker:{color:TC[t]}})),L('New game launches per month (game x state)',330,{barmode:'stack'}),CF);}

function p2(){const pr=PI.filter(r=>FP(r)),open=pr.filter(r=>r.status!='done');
 $('k2').innerHTML=kpi(uniq(pr.map(r=>r.project_id)).length,'provider projects')+kpi(uniq(open.map(r=>r.project_id)).length,'projects open')+
  kpi(open.filter(r=>r.status=='blocked').length,'items blocked')+`<div class="kpi"><b style="font-size:16px">${FC.slice(0,2).map(r=>r.provider+', '+r.state.split(' (')[0]+': '+r.p80_date).join('<br>')}</b><span>forecast launch (P80)</span></div>`;
 const col={'Commercial agreement':'#86B6EF','Technical integration':'#2A78D6','QA & staging tests':'#1C5CAB','Lab certification':'#1BAF7A','State approval':'#EDA100','Launch':'#EB6834'};
 const lab=r=>r.project_id+(r.state?' · '+r.state:'');
 const order=[];uniq(pr.map(r=>r.project_id)).forEach(p=>{order.push(p);['State A','State B','State C'].forEach(s=>{if(pr.some(r=>r.project_id==p&&r.state==s))order.push(p+' · '+s)})});
 const tr=Object.keys(col).map(s=>{const x=pr.filter(r=>r.stage==s&&r.start_date&&r.status!='not_started');return {type:'bar',orientation:'h',name:s,marker:{color:col[s]},
  y:x.map(lab),base:x.map(r=>r.start_date),
  x:x.map(r=>{const e=r.end_date||'2026-11-13';return Math.max(new Date(e)-new Date(r.start_date),864e5)}),
  customdata:x.map(r=>[r.status,r.blocker||'-']),hovertemplate:'%{y} '+s+'<br>%{base|%d %b %Y}, status %{customdata[0]}<br>blocker: %{customdata[1]}<extra></extra>'}});
 const ny=order.length;
 Plotly.react('c2a',tr,L('Pipeline timeline (bars end at 2026-11-13 when the stage is still open)',Math.max(380,ny*13+120),
  {barmode:'overlay',xaxis:{type:'date'},yaxis:{autorange:'reversed',tickfont:{size:9},categoryorder:'array',categoryarray:order},margin:{l:110,r:15,t:40,b:40},
   shapes:[{type:'line',x0:'2026-11-13',x1:'2026-11-13',yref:'paper',y0:0,y1:1,line:{color:'#D03B3B',dash:'dot'}}]}),CF);
 const st=ST.filter(r=>r.stage!='Launch');const stg=uniq(st.map(r=>r.stage));
 Plotly.react('c2b',['Aggregator','Direct'].map(rt=>({type:'bar',name:rt,x:stg,y:stg.map(s=>{const a=st.filter(r=>r.stage==s&&r.route==rt);
  return a.length?a.reduce((t,r)=>t+r.median_days*r.n,0)/a.reduce((t,r)=>t+r.n,0):null}),marker:{color:rt=='Direct'?'#898781':'#2A78D6'}})),
  L('Median days per stage, by route',330,{barmode:'group'}),CF);
 $('c2c').innerHTML='<h3 style="font-size:14px;margin:4px 0">Open items</h3><table><thead><tr><th>Project</th><th>Stage</th><th>State</th><th>Status</th><th>Blocker</th></tr></thead><tbody>'+
  open.map(r=>`<tr><td>${r.project_id}</td><td>${r.stage}</td><td>${r.state||'-'}</td><td class="${r.status=='blocked'?'p1':''}">${r.status}</td><td>${r.blocker||''}</td></tr>`).join('')+'</tbody></table>';}

function p3(){const e=ER.filter(F),days=uniq(e.map(r=>r.d)),ga=grp(e,['d'],'a'),ge=grp(e,['d'],'e');
 const w=WA.filter(r=>FP(r)),rb=sum(w,'rb'),rf=sum(w,'rf');const rt=RT.filter(r=>FP(r));
 $('k3').innerHTML=kpi((100*sum(e,'e')/Math.max(sum(e,'a'),1)).toFixed(2)+'%','launch error rate')+kpi((100*sum(w,'te')/Math.max(sum(w,'c'),1)).toFixed(3)+'%','wallet technical errors')+
  kpi((100*rf/Math.max(rb,1)).toFixed(2)+'%','failed rollbacks')+kpi(rt.filter(r=>r.stat_flag=='escalate').length+' / '+rt.filter(r=>r.stat_flag=='watch').length,'RTP escalate / watch')+
  kpi(rt.filter(r=>r.naive_flag===true||r.naive_flag=='True').length,'naive RTP alarms (3 pts below)');
 Plotly.react('c3a',[{type:'scatter',mode:'lines',x:days,y:days.map(d=>ge[d]/ga[d]),line:{color:'#898781',width:1.5},hovertemplate:'%{x}: %{y:.2%}<extra></extra>'}],
  L('Daily game launch error rate (pick a provider to see its own rate)',320,{yaxis:{tickformat:'.1%'},shapes:[{type:'line',xref:'paper',x0:0,x1:1,y0:.03,y1:.03,line:{color:'#D03B3B',dash:'dot'}}]}),CF);
 const routes=uniq(w.map(r=>r.r));
 Plotly.react('c3b',routes.map(ro=>{const x=w.filter(r=>r.r==ro),dd=uniq(x.map(r=>r.d)),c=grp(x,['d'],'c'),p=grp(x.map(r=>({d:r.d,v:r.p95*r.c})),['d'],'v');
  return {type:'scatter',mode:'lines',name:ro,x:dd,y:dd.map(d=>p[d]/c[d]),line:{width:1.6,color:ro=='Direct'?'#1C5CAB':ro=='Aggregator X'?'#86B6EF':'#898781'}}}),
  L('Wallet debit p95 latency by route (ms)',320),CF);
 const col={ok:'#C9C7BF',watch:'#EB6834',escalate:'#D03B3B'};
 Plotly.react('c3c',['ok','watch','escalate'].map(f=>{const x=rt.filter(r=>r.stat_flag==f);return {type:'scatter',mode:'markers',name:f,x:x.map(r=>r.rounds),
  y:x.map(r=>100*(r.rtp_realised-r.rtp_theoretical)),text:x.map(r=>r.game_id+' · '+r.volatility+' · z='+(+r.z).toFixed(1)+' · band ±'+(100*r.band_3sd).toFixed(1)+' pts'),
  marker:{color:col[f],size:f=='ok'?6:11,line:{color:'#FCFCFB',width:1.5}},hovertemplate:'%{text}<br>gap %{y:.1f} pts<extra></extra>'}}),
  L('RTP gap (pts) vs rounds, last 90 days: statistical flags',320,{xaxis:{type:'log',title:'rounds'}}),CF);
 const al=AL.filter(r=>$('fp').value=='All'||r.entity.startsWith($('fp').value+'-')||r.entity=='Provider '+$('fp').value)
  .filter(r=>$('fs').value=='All'||r.state==$('fs').value);
 $('c3d').innerHTML='<h3 style="font-size:14px;margin:4px 0">Compliance alerts, week of 2026-11-13</h3><table><thead><tr><th>Sev.</th><th>Rule</th><th>Entity</th><th>State</th><th>Detail</th></tr></thead><tbody>'+
  (al.length?al.map(r=>`<tr><td class="${r.severity.toLowerCase()}">${r.severity}</td><td>${r.rule}</td><td>${r.entity}</td><td>${r.state}</td><td>${r.detail}</td></tr>`).join(''):'<tr><td colspan=5 class="note">No alert for this filter.</td></tr>')+'</tbody></table>';}

const TY={n_slot:'Slot',n_table:'Table',n_live:'Live dealer',n_jackpot:'Jackpot slot'};
function score(c,ek,dm,xd,noconf){const tg=Object.fromEntries(TG.map(r=>[r.game_type,r])),tot=SS.reduce((a,r)=>a+r.v,0);
 const states=c.licensed_states.split('').map(x=>'State '+x),reach=SS.filter(r=>states.includes(r.s)).reduce((a,r)=>a+r.v,0)/tot;
 let inc=0;Object.entries(TY).forEach(([k,t])=>{if(c[k]>0){const g=tg[t],e=Math.min(.5,Math.max(.05,ek*g.demand_supply_ratio));
  inc+=g.ggr*365/90*(Math.pow((g.live_games+c[k])/g.live_games,e)-1)}});
 const ttl=(c.route=='Direct'?D.ttl.Direct:D.ttl.Aggregator)+xd,impact=inc*reach*Math.max(0,1-ttl/365);
 const conf=noconf?1:0.5+0.2*(c.portfolio_certified_elsewhere===true||c.portfolio_certified_elsewhere=='True')+0.2*(c.known_partner===true||c.known_partner=='True')+0.1*(states.length==3);
 const games=Object.keys(TY).reduce((a,k)=>a+c[k],0),eff=(c.integration_effort_weeks+0.1*games*states.length)*(c.route=='Direct'?dm:1);
 return {p:c.provider_id,route:c.route=='Direct'?'Direct':c.aggregator,games,states:c.licensed_states,reach,impact,conf,eff,ttl,score:impact*conf/eff,note:c.note}}
function p4(){const ek=+$('se').value,dm=+$('sd').value,xd=+$('st').value,nc=$('sc').checked;$('sev').textContent=ek.toFixed(2);$('sdv').textContent=dm.toFixed(1);$('stv').textContent=xd+' d';
 const s=CA.map(c=>score(c,ek,dm,xd,nc)).sort((a,b)=>b.score-a.score);
 Plotly.react('c4a',[{type:'bar',orientation:'h',y:s.map(r=>'Provider '+r.p).reverse(),x:s.map(r=>r.score).reverse(),marker:{color:s.map((r,i)=>i==0?'#2A78D6':i==1?'#86B6EF':'#C9C7BF').reverse()},
  hovertemplate:'%{y}: $%{x:,.0f} incremental GGR per person-week<extra></extra>'}],L('Score with these assumptions ($ incremental GGR per person-week)',320,{margin:{l:90,r:15,t:40,b:30}}),CF);
 $('c4b').innerHTML='<table><thead><tr><th></th><th>Candidate</th><th>Route</th><th>Games</th><th>States</th><th class="n">Reach</th><th class="n">Impact yr 1</th><th class="n">Conf.</th><th class="n">Effort (pw)</th><th class="n">Launch P50</th></tr></thead><tbody>'+
  s.map((r,i)=>`<tr class="${i==0?'hl':''}"><td><b>${r.p}</b></td><td>${r.note}</td><td>${r.route}</td><td class="n">${r.games}</td><td>${r.states}</td><td class="n">${(100*r.reach).toFixed(0)}%</td><td class="n">${usd(r.impact)}</td><td class="n">${r.conf.toFixed(1)}</td><td class="n">${r.eff.toFixed(1)}</td><td class="n">${r.ttl.toFixed(0)} d</td></tr>`).join('')+
  '</tbody></table><p class="note">Impact = incremental first-year GGR from filling under-supplied game types (diminishing returns), x reach, x the share of the year left after launch. Score = Impact x Confidence / Effort.</p>';
 Plotly.react('c4c',[{type:'bar',x:MC.map(r=>'Provider '+r.provider_id),y:MC.map(r=>r.p_first),name:'first',marker:{color:'#2A78D6'}},
  {type:'bar',x:MC.map(r=>'Provider '+r.provider_id),y:MC.map(r=>r.p_top2),name:'top 2',marker:{color:'#C9C7BF'}}],
  L('Randomised sensitivity (5,000 runs): share of runs first / top 2',320,{barmode:'group',yaxis:{tickformat:'.0%'}}),CF);
 Plotly.react('c4d',[{type:'bar',x:TG.map(r=>r.game_type),y:TG.map(r=>r.demand_supply_ratio),marker:{color:TG.map(r=>TC[r.game_type])},
  text:TG.map(r=>'x'+(+r.demand_supply_ratio).toFixed(1)),textposition:'outside',hovertemplate:'%{x}: GGR share / catalogue share = %{y:.2f}<extra></extra>'}],
  L('Demand / supply ratio by game type (above 1 = under-supplied)',320,{shapes:[{type:'line',xref:'paper',x0:0,x1:1,y0:1,y1:1,line:{color:'#898781',dash:'dot'}}]}),CF);}

const R={1:p1,2:p2,3:p3,4:p4};let cur=1;
function show(n){cur=n;document.querySelectorAll('.page').forEach((s,i)=>s.classList.toggle('on',i==n-1));
 document.querySelectorAll('nav button').forEach((b,i)=>b.classList.toggle('on',i==n-1));R[n]();}
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{location.hash=b.dataset.p;show(+b.dataset.p)});
['fs','fp'].forEach(id=>$(id).onchange=()=>R[cur]());['se','sd','st','sc'].forEach(id=>$(id).oninput=p4);
show(+(location.hash.slice(1))||1);
</script></body></html>"""

if __name__ == "__main__":
    main()
