"""Patch dashboard_tpv.html: period filter + MOP share all scenarios + Take Rate projection."""
import json

# Load TR lookup
with open(r'C:\Users\rdmorais\Desktop\Teste\tr_lookup.json', 'r', encoding='utf-8') as f:
    tr = json.load(f)
TR_JS = 'const TR=' + json.dumps(tr, ensure_ascii=False, separators=(',',':')) + ';'

with open(r'C:\Users\rdmorais\Desktop\Teste\dashboard_tpv.html', 'r', encoding='utf-8') as f:
    html = f.read()

# ── 1. Inject TR constant after RAW_MOP ───────────────────────────────────────
mop_start = html.find('const RAW_MOP=[')
mop_end = html.find('];', mop_start) + 2
html = html[:mop_end] + '\n' + TR_JS + html[mop_end:]

# ── 2. Add period filter in .filters bar ──────────────────────────────────────
period_html = (
    '  <div class="fgrp">'
    '<label>Per&#237;odo</label>'
    '<select id="fMesIni" onchange="render()"><option value="">In&#237;cio</option></select>'
    '<span style="font-size:11px;color:var(--sub);padding:0 2px">&#8594;</span>'
    '<select id="fMesFim" onchange="render()"><option value="">Fim</option></select>'
    '</div>'
)
html = html.replace(
    '  <div class="fgrp"><label>Carteira</label>',
    period_html + '\n  <div class="fgrp"><label>Carteira</label>'
)

# ── 3. Widen mop-row to 3 columns + add MOP% canvas ──────────────────────────
html = html.replace(
    '<div class="mop-row" style="display:grid;grid-template-columns:1fr 1fr;gap:14px;padding:14px 24px 0">',
    '<div class="mop-row" style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;padding:14px 24px 0">'
)
html = html.replace(
    '  <div class="card">\n    <div class="card-title">MOP Trend &mdash; Actual (mensalizado)</div>\n    <canvas id="cMopTrend" style="max-height:300px"></canvas>\n  </div>\n</div>',
    '  <div class="card">\n    <div class="card-title">MOP Trend &mdash; Actual (mensalizado)</div>\n    <canvas id="cMopTrend" style="max-height:300px"></canvas>\n  </div>\n'
    '  <div class="card">\n    <div class="card-title">Mix % MOP &mdash; Ano Completo (3 cen&#225;rios)</div>\n    <canvas id="cMopPct" style="max-height:300px"></canvas>\n  </div>\n</div>'
)

# ── 4. Add Take Rate section before table ─────────────────────────────────────
tr_section_html = (
    '<div class="tr-row" style="display:grid;grid-template-columns:1fr 1fr;gap:14px;padding:14px 24px 0">\n'
    '  <div class="card">\n'
    '    <div class="card-title">Take Rate Projetado por Produto &amp; Segmento (Actual)</div>\n'
    '    <canvas id="cTR" style="max-height:320px"></canvas>\n'
    '  </div>\n'
    '  <div class="card">\n'
    '    <div class="card-title">GMR Projetado por MOP (Actual)</div>\n'
    '    <canvas id="cTRmop" style="max-height:320px"></canvas>\n'
    '  </div>\n'
    '</div>\n'
)
html = html.replace('<div class="tbl-wrap">', tr_section_html + '<div class="tbl-wrap">')

# ── 5. Add popPeriod JS function ──────────────────────────────────────────────
pop_period_fn = (
    '\nfunction popPeriod(){\n'
    '  const all=[...new Set(RAW.map(r=>r.MES))].sort();\n'
    '  const si=document.getElementById("fMesIni");\n'
    '  const sf=document.getElementById("fMesFim");\n'
    '  si.innerHTML=\'<option value="">In\\u00edcio</option>\'+all.map(m=>`<option value="${m}">${mLbl(m)}</option>`).join("");\n'
    '  sf.innerHTML=\'<option value="">Fim</option>\'+all.map(m=>`<option value="${m}">${mLbl(m)}</option>`).join("");\n'
    '}'
)
html = html.replace('\nfunction pop(id,col){', pop_period_fn + '\nfunction pop(id,col){')

# ── 6. Add period filter to filt() ────────────────────────────────────────────
html = html.replace(
    '  const selM=getSelMops();\n'
    '  const allM=document.querySelectorAll("#msMopDrop input.mop-cb").length;\n'
    '  const useM=selM.length>0&&selM.length<allM;\n'
    '  return RAW.filter(r=>',
    '  const selM=getSelMops();\n'
    '  const allM=document.querySelectorAll("#msMopDrop input.mop-cb").length;\n'
    '  const useM=selM.length>0&&selM.length<allM;\n'
    '  const mIni=document.getElementById("fMesIni").value;\n'
    '  const mFim=document.getElementById("fMesFim").value;\n'
    '  return RAW.filter(r=>'
)
html = html.replace(
    '    (!useM||!r.MOP||selM.includes(r.MOP))\n  );',
    '    (!useM||!r.MOP||selM.includes(r.MOP))&&\n    (!mIni||r.MES>=mIni)&&(!mFim||r.MES<=mFim)\n  );'
)

# ── 7. Update resetFilters ────────────────────────────────────────────────────
html = html.replace(
    '  ["fCart","fCanal"].forEach(x=>document.getElementById(x).value="");\n',
    '  ["fCart","fCanal","fMesIni","fMesFim"].forEach(x=>document.getElementById(x).value="");\n'
)

# ── 8. Add popPeriod() to init ────────────────────────────────────────────────
html = html.replace(
    'pop("fCart","CARTEIRA");pop("fCanal","CANAL");\npopProd();popSeg();popMop();\nrender();',
    'pop("fCart","CARTEIRA");pop("fCanal","CANAL");\npopProd();popSeg();popMop();popPeriod();\nrender();'
)

# ── 9. Add MOP% + TR render code inside render() ─────────────────────────────
mop_colors_obj = (
    '{"BANK_TRANSFER":"rgba(22,163,74,.8)","CREDIT_CARD":"rgba(249,115,22,.8)",'
    '"ACCOUNT_MONEY":"rgba(37,99,235,.8)","DEBIT_CARD":"rgba(147,51,234,.8)",'
    '"DIGITAL_CURRENCY":"rgba(8,145,178,.8)","PIX":"rgba(21,128,61,.8)",'
    '"TICKET":"rgba(220,38,38,.8)","PREPAID_CARD":"rgba(202,138,4,.8)",'
    '"VOUCHER_CARD":"rgba(20,184,166,.8)"}'
)

new_render_end = (
    '  mk("cMopTrend",{type:"line",data:{labels:acMesM.map(mLbl),datasets:topMops.map((mo,i)=>({label:mo,data:acMesM.map(m=>(acMopBym[mo]||{})[m]||null),borderColor:mopColors[i],borderWidth:2.5,pointRadius:4,tension:.3,fill:false,spanGaps:true}))},options:{responsive:true,plugins:{legend:{position:"top"},datalabels:{display:false}},scales:{y:{ticks:{callback:v=>fmt(v)},grid:{color:"rgba(0,0,0,.06)"}}}}}});\n'
    '  /* MOP% full year all scenarios */\n'
    '  const mopColors2=' + mop_colors_obj + ';\n'
    '  const mopPeriodMes=[...new Set(RAW_MOP.map(r=>r.MES))].sort();\n'
    '  const mopsAll=[...new Set(RAW_MOP.map(r=>r.MOP).filter(Boolean))].sort();\n'
    '  const mopPctD=RAW_MOP.filter(r=>(!useP2||selP2.includes(r.PRODUTO))&&(!fCart2||r.CARTEIRA===fCart2)&&(!useM2||selM2.includes(r.MOP))&&(!document.getElementById("fMesIni").value||r.MES>=document.getElementById("fMesIni").value)&&(!document.getElementById("fMesFim").value||r.MES<=document.getElementById("fMesFim").value));\n'
    '  const pctByCenMop={};for(const c of SCEN){pctByCenMop[c]={};for(const mo of mopsAll)pctByCenMop[c][mo]=0;}\n'
    '  for(const r of mopPctD){if(pctByCenMop[r.CENARIO])pctByCenMop[r.CENARIO][r.MOP]=(pctByCenMop[r.CENARIO][r.MOP]||0)+r.VALOR;}\n'
    '  const pctScenLabels=SCEN.filter(c=>Object.values(pctByCenMop[c]).some(v=>v>0));\n'
    '  const pctDs=mopsAll.map(mo=>({label:mo,data:pctScenLabels.map(c=>{const tot=Object.values(pctByCenMop[c]).reduce((a,b)=>a+b,0);return tot>0?Math.round(pctByCenMop[c][mo]/tot*1000)/10:0;}),backgroundColor:mopColors2[mo]||"#999",stack:"s"}));\n'
    '  mk("cMopPct",{type:"bar",data:{labels:pctScenLabels,datasets:pctDs},options:{responsive:true,plugins:{legend:{position:"bottom",labels:{font:{size:9},boxWidth:12}},datalabels:{display:false}},scales:{x:{stacked:true},y:{stacked:true,max:100,ticks:{callback:v=>v+"%"},grid:{color:"rgba(0,0,0,.06)"}}}}}}});\n'
    '  /* Take Rate Projection */\n'
    '  function getTR(seg,prod,mop){return TR[seg+"|"+prod+"|"+mop]||TR[seg+"||"+mop]||0;}\n'
    '  const acForTR=RAW_MOP.filter(r=>r.CENARIO==="ACTUAL"&&(!useP2||selP2.includes(r.PRODUTO))&&(!fCart2||r.CARTEIRA===fCart2)&&(!useM2||selM2.includes(r.MOP)));\n'
    '  const segForTR=["BIG SELLERS","SMB","LONGTAIL"];\n'
    '  const prodsForTR=[...new Set(acForTR.map(r=>r.PRODUTO))].sort();\n'
    '  const trByProd={};prodsForTR.forEach(p=>{trByProd[p]={};segForTR.forEach(s=>{trByProd[p][s]=acForTR.filter(r=>r.PRODUTO===p).reduce((a,r)=>{const seg=r.SEGMENTO||"";return a+r.VALOR*(getTR(seg,r.PRODUTO,r.MOP)||0);},0);});});\n'
    '  mk("cTR",{type:"bar",data:{labels:prodsForTR,datasets:segForTR.map((s,i)=>({label:s,data:prodsForTR.map(p=>trByProd[p][s]||0),backgroundColor:["rgba(37,99,235,.8)","rgba(249,115,22,.8)","rgba(22,163,74,.8)"][i],borderRadius:4}))},options:{responsive:true,plugins:{legend:{position:"top"},datalabels:{display:false}},scales:{x:{ticks:{font:{size:9}}},y:{ticks:{callback:v=>fmt(v)},grid:{color:"rgba(0,0,0,.06)"}}}}}}});\n'
    '  const mopsForTR=[...new Set(acForTR.map(r=>r.MOP))].sort();\n'
    '  const gmrByMop2={};mopsForTR.forEach(mo=>{gmrByMop2[mo]=acForTR.filter(r=>r.MOP===mo).reduce((a,r)=>{const seg=r.SEGMENTO||"";return a+r.VALOR*(getTR(seg,r.PRODUTO,mo)||0);},0);});\n'
    '  mk("cTRmop",{type:"bar",data:{labels:mopsForTR,datasets:[{label:"GMR Projetado",data:mopsForTR.map(m=>gmrByMop2[m]||0),backgroundColor:mopsForTR.map(m=>mopColors2[m]||"#999"),borderRadius:4}]},options:{responsive:true,plugins:{legend:{display:false},datalabels:{anchor:"end",align:"end",color:"#555",font:{size:9},formatter:v=>fmt(v)}},scales:{x:{ticks:{font:{size:9}}},y:{ticks:{callback:v=>fmt(v)},grid:{color:"rgba(0,0,0,.06)"}}}}}}});\n'
    '}\n'
)

# Replace the closing of the render function (after cMopTrend)
html = html.replace(
    'mk("cMopTrend",{type:"line",data:{labels:acMesM.map(mLbl),datasets:topMops.map((mo,i)=>({label:mo,data:acMesM.map(m=>(acMopBym[mo]||{})[m]||null),borderColor:mopColors[i],borderWidth:2.5,pointRadius:4,tension:.3,fill:false,spanGaps:true}))},options:{responsive:true,plugins:{legend:{position:"top"},datalabels:{display:false}},scales:{y:{ticks:{callback:v=>fmt(v)},grid:{color:"rgba(0,0,0,.06)"}}}}}});\n}',
    new_render_end
)

# ── Write ─────────────────────────────────────────────────────────────────────
with open(r'C:\Users\rdmorais\Desktop\Teste\dashboard_tpv.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f'Dashboard written: {len(html):,} chars')

checks = [
    ('TR const',        'const TR=' in html),
    ('Period filter',   'fMesIni' in html),
    ('popPeriod',       'function popPeriod()' in html),
    ('MOP% full year',  'pctByCenMop' in html),
    ('MOP% canvas',     'id="cMopPct"' in html),
    ('TR canvases',     'id="cTR"' in html and 'id="cTRmop"' in html),
    ('getTR fn',        'function getTR(' in html),
    ('period filt',     'fMesIni' in html and 'fMesFim' in html),
]
for name, ok in checks:
    print(f"  {'OK' if ok else 'FAIL'} {name}")
