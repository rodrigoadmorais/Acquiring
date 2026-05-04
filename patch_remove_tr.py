"""
1. Remove entire Take Rate section (KPI cards, charts, editable table, all JS)
2. Add Volume / Share% toggle to MOP Trend chart
"""
import re

with open(r'C:\Users\rdmorais\Desktop\Teste\dashboard_tpv.html', 'r', encoding='utf-8') as f:
    h = f.read()

# ── 1. Remove HTML: gmr-kpi-row ──────────────────────────────────────────────
old = (
    '<div class="gmr-kpi-row" style="display:grid;grid-template-columns:repeat(3,1fr);'
    'gap:14px;padding:14px 24px 0">\n'
    '  <div class="card" style="text-align:center;padding:16px">\n'
    '    <div class="card-title" style="margin-bottom:6px">Take Rate Total FC 4+8 VF (Mai&ndash;Dez)</div>\n'
    '    <div id="kGMRfc" style="font-size:1.7rem;font-weight:800;color:rgba(124,58,237,1)">&#8212;</div>\n'
    '  </div>\n'
    '  <div class="card" style="text-align:center;padding:16px">\n'
    '    <div class="card-title" style="margin-bottom:6px">Take Rate Total Plano (Mai&ndash;Dez)</div>\n'
    '    <div id="kGMRpl" style="font-size:1.7rem;font-weight:800;color:rgba(22,163,74,1)">&#8212;</div>\n'
    '  </div>\n'
    '  <div class="card" style="text-align:center;padding:16px">\n'
    '    <div class="card-title" style="margin-bottom:6px">FC vs Plano &mdash; Take Rate YTG</div>\n'
    '    <div id="kGMRdelta" style="font-size:1.7rem;font-weight:800">&#8212;</div>\n'
    '    <div id="kGMRdeltaAbs" style="font-size:1rem;font-weight:600;color:var(--sub);margin-top:4px">&#8212;</div>\n'
    '  </div>\n'
    '</div>\n'
)
assert old in h, "gmr-kpi-row not found"
h = h.replace(old, '', 1); print("OK gmr-kpi-row removed")

# ── 2. Remove HTML: tr-row ───────────────────────────────────────────────────
old = (
    '<div class="tr-row" style="display:grid;grid-template-columns:1fr 1fr;gap:14px;padding:14px 24px 0">\n'
    '  <div class="card">\n'
    '    <div class="card-title">Take Rate M&#233;dio por Produto &mdash; FC vs Plano (Mai em diante)</div>\n'
    '    <canvas id="cTR" style="max-height:320px"></canvas>\n'
    '  </div>\n'
    '  <div class="card">\n'
    '    <div class="card-title">Take Rate Projetado por MOP &mdash; FC vs Plano (Mai em diante)</div>\n'
    '    <canvas id="cTRmop" style="max-height:320px"></canvas>\n'
    '  </div>\n'
    '</div>\n'
)
assert old in h, "tr-row not found"
h = h.replace(old, '', 1); print("OK tr-row removed")

# ── 3. Remove HTML: tbl-wrap ─────────────────────────────────────────────────
old = (
    '<div class="tbl-wrap">\n'
    '  <div style="display:flex;align-items:center;justify-content:space-between;padding:4px 0 14px;flex-wrap:wrap;gap:8px">\n'
    '    <span style="font-weight:700;font-size:14px">Take Rate por Produto / Segmento / MOP &mdash; edit&aacute;vel para simula&ccedil;&otilde;es</span>\n'
    '    <div style="display:flex;gap:8px">\n'
    '      <button id="btnBS" class="btn-tr-reset" onclick="toggleBigSellers()">Mostrar Big Sellers</button>\n'
    '      <button id="btnZ" class="btn-tr-reset" onclick="toggleZeroTR()">Incluir MOP zerados</button>\n'
    '      <button class="btn-tr-reset" onclick="resetTR()">Resetar TR</button>\n'
    '      <button class="btn-tr-export" onclick="exportData()">&#8595; Exportar dados</button>\n'
    '    </div>\n'
    '  </div>\n'
    '  <table id="trEditTable">\n'
    '    <thead><tr><th>Produto</th><th>Segmento</th><th>MOP</th><th style="text-align:right">Take Rate %</th></tr></thead>\n'
    '    <tbody id="trEditBody"></tbody>\n'
    '  </table>\n'
    '</div>'
)
assert old in h, "tbl-wrap not found"
h = h.replace(old, '', 1); print("OK tbl-wrap removed")

# ── 4. Remove CSS: #trEditTable + .btn-tr-* ──────────────────────────────────
css_to_remove = [
    '#trEditTable{width:100%;border-collapse:collapse;font-size:13px}\n',
    '#trEditTable thead th{background:var(--yellow);color:#000;padding:8px 14px;text-align:left;position:sticky;top:0;font-weight:700}\n',
    '#trEditTable td{padding:6px 14px;border-bottom:1px solid rgba(0,0,0,.05)}\n',
    '#trEditTable tr:hover td{background:rgba(0,0,0,.025)}\n',
    '#trEditTable input[type=number]{border:1px solid #ccc;border-radius:4px;padding:3px 7px;font-size:12px;width:80px;text-align:right}\n',
    '#trEditTable input[type=number]:focus{outline:none;border-color:var(--yellow);box-shadow:0 0 0 2px rgba(253,200,0,.3)}\n',
    '.btn-tr-reset{background:#f3f4f6;border:1px solid #ccc;border-radius:6px;padding:6px 14px;font-weight:600;font-size:12px;cursor:pointer}\n',
    '.btn-tr-export{background:var(--yellow);border:none;border-radius:6px;padding:6px 14px;font-weight:700;font-size:12px;cursor:pointer}\n',
    '.btn-tr-reset:hover{background:#e5e7eb}.btn-tr-export:hover{opacity:.85}\n',
    '.bvf{background:rgba(124,58,237,.15);color:rgb(109,40,217);}\n',
]
for css in css_to_remove:
    if css in h:
        h = h.replace(css, '', 1)
    else:
        print(f"  WARN CSS not found: {css[:50]}")
print("OK TR CSS removed")

# ── 5. Remove mobile CSS for tr-row / tbl-wrap ───────────────────────────────
h = h.replace(',.mobile-mode .tr-row', '', 1)
h = h.replace(',.mobile-mode .tbl-wrap', '', 1)
print("OK mobile CSS cleaned")

# ── 6. Remove JS: const TR={...} and TRcustom ────────────────────────────────
# TR is a very long line; find and remove it
tr_start = h.find('\nconst TR={')
tr_end   = h.find(';\n', tr_start) + 2      # ends with }; newline
assert tr_start != -1, "const TR not found"
h = h[:tr_start] + h[tr_end:]
print("OK const TR removed")

tcustom = 'const TRcustom=Object.assign({},TR);'
if '\n' + tcustom in h:
    h = h.replace('\n' + tcustom, '', 1)
elif tcustom in h:
    h = h.replace(tcustom, '', 1)
else:
    raise AssertionError("TRcustom not found")
print("OK TRcustom removed")

# ── 7. Remove JS functions: getTR, buildTRTable, toggleBigSellers, ───────────
#       toggleZeroTR, updateTR, resetTR, exportData
fn_blocks = [
    # getTR
    '\nfunction getTR(seg,prod,mop){\n'
    '  if(seg&&TRcustom[seg+"|"+prod+"|"+mop]) return TRcustom[seg+"|"+prod+"|"+mop];\n'
    '  if(seg&&TRcustom[seg+"||"+mop]) return TRcustom[seg+"||"+mop];\n'
    '  const segs=["SMB","BIG SELLERS","LONGTAIL"];\n'
    '  if(!seg&&prod&&mop){\n'
    '    const rates=segs.map(s=>TRcustom[s+"|"+prod+"|"+mop]).filter(v=>v>0);\n'
    '    if(rates.length) return rates.reduce((a,b)=>a+b,0)/rates.length;\n'
    '    const rates2=segs.map(s=>TRcustom[s+"||"+mop]).filter(v=>v>0);\n'
    '    if(rates2.length) return rates2.reduce((a,b)=>a+b,0)/rates2.length;\n'
    '  }\n'
    '  for(const s of segs){\n'
    '    if(TRcustom[s+"|"+prod+"|"+mop]) return TRcustom[s+"|"+prod+"|"+mop];\n'
    '    if(TRcustom[s+"||"+mop]) return TRcustom[s+"||"+mop];\n'
    '  }\n'
    '  return 0;\n'
    '}',
    # showBigSellers + showZeroTR vars (inline at start of buildTRTable section)
    '\nlet showBigSellers=false;\nlet showZeroTR=false;',
]
for block in fn_blocks:
    if block in h:
        h = h.replace(block, '', 1)
        print(f"OK removed block: {block[:40].strip()}")
    else:
        print(f"MISS block: {block[:40].strip()}")

# Remove buildTRTable function
bt_start = h.find('\nfunction buildTRTable(){')
bt_end   = h.find('\nfunction toggleBigSellers(){')
assert bt_start != -1, "buildTRTable not found"
h = h[:bt_start] + h[bt_end:]; print("OK buildTRTable removed")

# Remove toggleBigSellers
tbs_start = h.find('\nfunction toggleBigSellers(){')
tbs_end   = h.find('\nfunction toggleZeroTR(){')
h = h[:tbs_start] + h[tbs_end:]; print("OK toggleBigSellers removed")

# Remove toggleZeroTR
tz_start = h.find('\nfunction toggleZeroTR(){')
tz_end   = h.find('\nfunction updateTR(')
h = h[:tz_start] + h[tz_end:]; print("OK toggleZeroTR removed")

# Remove updateTR
utr_start = h.find('\nfunction updateTR(')
utr_end   = h.find('\nfunction resetTR(){')
h = h[:utr_start] + h[utr_end:]; print("OK updateTR removed")

# Remove resetTR
rtr_start = h.find('\nfunction resetTR(){')
rtr_end   = h.find('\nfunction exportData(){')
h = h[:rtr_start] + h[rtr_end:]; print("OK resetTR removed")

# Remove exportData
ed_start = h.find('\nfunction exportData(){')
ed_end   = h.find('\n}', h.find('a2.download="take_rates.csv";a2.click();', ed_start)) + 2
h = h[:ed_start] + h[ed_end:]; print("OK exportData removed")

# ── 8. Remove TR render() block (ytgFilter → mk cTRmop close) ────────────────
tr_render_start = h.find('  /* Take Rate Projection')
tr_render_end   = h.find('  mk("cTRmop",{')
# find the closing }}) of mk("cTRmop")
close_pos = h.find('})\n', tr_render_end) + 3  # skip past })  + newline
h = h[:tr_render_start] + h[close_pos:]; print("OK TR render block removed")

# ── 9. Remove buildTRTable() from init ───────────────────────────────────────
h = h.replace('\nbuildTRTable();', '', 1); print("OK buildTRTable() init removed")

# ── 10. MOP Trend card: add toggle buttons ───────────────────────────────────
old_card = (
    '  <div class="card">\n'
    '    <div class="card-title">MOP Trend &mdash; Actual + Forecast (AC sólido, FC tracejado)</div>\n'
    '    <canvas id="cMopTrend" style="max-height:300px"></canvas>\n'
    '  </div>'
)
new_card = (
    '  <div class="card">\n'
    '    <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:8px">\n'
    '      <div class="card-title" style="margin:0">MOP Trend &mdash; Actual + Forecast (AC sólido, FC tracejado)</div>\n'
    '      <div style="display:flex;gap:6px">\n'
    '        <button class="btn-trend active" id="btnMopAbs" onclick="setMopTrendMode(\'abs\',this)">Volume</button>\n'
    '        <button class="btn-trend" id="btnMopPct" onclick="setMopTrendMode(\'pct\',this)">Share %</button>\n'
    '      </div>\n'
    '    </div>\n'
    '    <canvas id="cMopTrend" style="max-height:300px"></canvas>\n'
    '  </div>'
)
assert old_card in h, "MOP Trend card not found"
h = h.replace(old_card, new_card, 1); print("OK MOP Trend toggle buttons added")

# ── 11. Add mopTrendMode state + setMopTrendMode before render() ─────────────
mop_mode_js = (
    "\nlet mopTrendMode='abs';\n"
    "function setMopTrendMode(v,btn){\n"
    "  mopTrendMode=v;\n"
    "  document.querySelectorAll('#btnMopAbs,#btnMopPct').forEach(b=>b.classList.remove('active'));\n"
    "  btn.classList.add('active');\n"
    "  render();\n"
    "}\n"
)
render_pos = h.find('\nfunction render(){')
assert render_pos != -1, "render() not found"
h = h[:render_pos] + mop_mode_js + h[render_pos:]; print("OK mopTrendMode state added")

# ── 12. Replace cMopTrend render code to support abs/pct ─────────────────────
old_trend_render = (
    '  const acCutoffIdx=acMesM.length-1;\n'
    '  const topMops=Object.entries(acMopBym).sort((a,b)=>Object.values(b[1]).reduce((x,y)=>x+y,0)-Object.values(a[1]).reduce((x,y)=>x+y,0)).slice(0,5).map(e=>e[0]);\n'
    '  const mopColors=["#2563EB","#F97316","#16A34A","#9333EA","#0891B2"];\n'
    '  const trendDs=topMops.map((mo,i)=>({\n'
    '    label:mo,\n'
    '    data:allTrendMes.map(m=>(acMopBym[mo]||{})[m]!==undefined?(acMopBym[mo]||{})[m]:(fcMopBym[mo]||{})[m]||null),\n'
    '    borderColor:mopColors[i],borderWidth:2.5,pointRadius:3,tension:.3,fill:false,spanGaps:false,\n'
    '    segment:{borderDash:ctx=>ctx.p1DataIndex>acCutoffIdx?[6,3]:[]}\n'
    '  }));\n'
    '  mk("cMopTrend",{type:"line",data:{labels:allTrendMes.map(mLbl),datasets:trendDs},options:{responsive:true,plugins:{legend:{position:"top"},datalabels:{display:false}},scales:{y:{ticks:{callback:v=>fmt(v)},grid:{color:"rgba(0,0,0,.06)"}}}}});'
)
new_trend_render = (
    '  const acCutoffIdx=acMesM.length-1;\n'
    '  const topMops=Object.entries(acMopBym).sort((a,b)=>Object.values(b[1]).reduce((x,y)=>x+y,0)-Object.values(a[1]).reduce((x,y)=>x+y,0)).slice(0,5).map(e=>e[0]);\n'
    '  const mopColors=["#2563EB","#F97316","#16A34A","#9333EA","#0891B2"];\n'
    '  /* totals per month for share % */\n'
    '  const acTotM={};const fcTotM={};\n'
    '  for(const m of allTrendMes){\n'
    '    acTotM[m]=Object.values(acMopBym).reduce((s,v)=>s+(v[m]||0),0);\n'
    '    fcTotM[m]=Object.values(fcMopBym).reduce((s,v)=>s+(v[m]||0),0);\n'
    '  }\n'
    '  function getMopVal(mo,m){\n'
    '    const isAc=(acMopBym[mo]||{})[m]!==undefined;\n'
    '    const raw=isAc?(acMopBym[mo]||{})[m]:(fcMopBym[mo]||{})[m];\n'
    '    if(raw===undefined||raw===null) return null;\n'
    '    if(mopTrendMode==="pct"){\n'
    '      const tot=isAc?(acTotM[m]||0):(fcTotM[m]||0);\n'
    '      return tot>0?Math.round(raw/tot*1000)/10:null;\n'
    '    }\n'
    '    return raw;\n'
    '  }\n'
    '  const trendDs=topMops.map((mo,i)=>({\n'
    '    label:mo,\n'
    '    data:allTrendMes.map(m=>getMopVal(mo,m)),\n'
    '    borderColor:mopColors[i],borderWidth:2.5,pointRadius:3,tension:.3,fill:false,spanGaps:false,\n'
    '    segment:{borderDash:ctx=>ctx.p1DataIndex>acCutoffIdx?[6,3]:[]}\n'
    '  }));\n'
    '  const mopYTick=mopTrendMode==="pct"?v=>v+"%":v=>fmt(v);\n'
    '  mk("cMopTrend",{type:"line",data:{labels:allTrendMes.map(mLbl),datasets:trendDs},options:{responsive:true,plugins:{legend:{position:"top"},datalabels:{display:false}},scales:{y:{ticks:{callback:mopYTick},grid:{color:"rgba(0,0,0,.06)"}}}}});'
)
assert old_trend_render in h, "cMopTrend render block not found"
h = h.replace(old_trend_render, new_trend_render, 1); print("OK cMopTrend abs/pct added")

# ── 13. Verify brace balance ──────────────────────────────────────────────────
sc = h[h.rfind('<script>')+8:h.rfind('</script>')]
depth = sum(1 if c=='{' else -1 if c=='}' else 0 for c in sc)
print(f'\nBrace balance: {depth}')

# Quick checks
checks = [
    ('no gmr-kpi-row',    'gmr-kpi-row' not in h),
    ('no tr-row div',     'class="tr-row"' not in h),
    ('no tbl-wrap',       'class="tbl-wrap"' not in h),
    ('no const TR',       '\nconst TR={' not in h),
    ('no TRcustom',       'TRcustom' not in h),
    ('no getTR',          'function getTR' not in h),
    ('no buildTRTable',   'function buildTRTable' not in h),
    ('no ytgFilter',      'ytgFilter' not in h),
    ('no mk cTR',         'mk("cTR"' not in h),
    ('no mk cTRmop',      'mk("cTRmop"' not in h),
    ('mopTrendMode',      'mopTrendMode' in h),
    ('setMopTrendMode',   'setMopTrendMode' in h),
    ('getMopVal',         'getMopVal' in h),
    ('Volume button',     'btnMopAbs' in h),
]
for name, ok in checks:
    print(f'  {"OK" if ok else "FAIL"} {name}')

with open(r'C:\Users\rdmorais\Desktop\Teste\dashboard_tpv.html', 'w', encoding='utf-8') as f:
    f.write(h)
print(f'\nSaved: {len(h):,} chars')
