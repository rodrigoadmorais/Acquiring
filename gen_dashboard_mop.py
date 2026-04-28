"""Rebuild dashboard_tpv.html with MOP support, updated actual data, and SMB+LONGTAIL defaults."""
import json
import pandas as pd

# ── Load and prepare RAW data ──────────────────────────────────────────────────
df = pd.read_csv(r'C:\Users\rdmorais\Desktop\Teste\tpv_combinado.tsv', sep='\t', dtype=str, keep_default_na=False)
df['VALOR'] = pd.to_numeric(df['VALOR'], errors='coerce').fillna(0)
df = df[df['VALOR'] != 0]

raw_records = []
for _, r in df.iterrows():
    rec = {
        'CENARIO': r['CENARIO'],
        'MES': r['MES'],
        'PRODUTO': r['PRODUTO'],
        'CARTEIRA': r['CARTEIRA'],
        'CANAL': r['CANAL'],
        'SEGMENTO': r['SEGMENTO'],
        'VALOR': round(r['VALOR'], 2),
    }
    if r.get('MOP', ''):
        rec['MOP'] = r['MOP']
    raw_records.append(rec)

print(f"RAW records: {len(raw_records)}")

# ── Build RAW_MOP data ─────────────────────────────────────────────────────────
df_pl_mop = pd.read_csv(r'C:\Users\rdmorais\Desktop\Teste\plano_mop_raw.tsv', sep='\t', dtype=str, keep_default_na=False)

prod_map = {'CHECKOUT':'OP - CHECKOUT','OP - CHECKOUT':'OP - CHECKOUT','QR':'QR','QR FROM POINT':'QR',
            'QR SELLERS':'QR','LINK':'LINK','OP - LINK':'LINK','TAP':'TTP','TTP':'TTP'}
cart_map = {'AQUISICAO':'ACQUISITION','ACQUISITION':'ACQUISITION','LEGADO':'ENGAGEMENT','ENGAGEMENT':'ENGAGEMENT'}
df_pl_mop['PRODUTO'] = df_pl_mop['PRODUTO'].map(lambda x: prod_map.get(x, x))
df_pl_mop['CARTEIRA'] = df_pl_mop['CARTEIRA'].map(lambda x: cart_map.get(x, x))
df_pl_mop['CENARIO'] = 'PLANO'
df_pl_mop = df_pl_mop.rename(columns={'SUM de TPV': 'VALOR'})
df_pl_mop['VALOR'] = pd.to_numeric(
    df_pl_mop['VALOR'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False),
    errors='coerce').fillna(0)
df_pl_mop = df_pl_mop[df_pl_mop['VALOR'] != 0]
pl_mop_agg = df_pl_mop.groupby(['CENARIO','MES','PRODUTO','CARTEIRA','MOP'], as_index=False)['VALOR'].sum()

ac_fc = df[df['CENARIO'].isin(['ACTUAL','FORECAST 3+9'])].copy()
ac_fc = ac_fc[ac_fc['MOP'] != '']
ac_fc_mop = ac_fc.groupby(['CENARIO','MES','PRODUTO','CARTEIRA','MOP'], as_index=False)['VALOR'].sum()

raw_mop_df = pd.concat([ac_fc_mop, pl_mop_agg[['CENARIO','MES','PRODUTO','CARTEIRA','MOP','VALOR']]], ignore_index=True)
raw_mop_df = raw_mop_df[raw_mop_df['MOP'] != '']

raw_mop_records = []
for _, r in raw_mop_df.iterrows():
    raw_mop_records.append({
        'CENARIO': r['CENARIO'],
        'MES': r['MES'],
        'PRODUTO': r['PRODUTO'],
        'CARTEIRA': r['CARTEIRA'],
        'MOP': r['MOP'],
        'VALOR': round(r['VALOR'], 2),
    })

print(f"RAW_MOP records: {len(raw_mop_records)}")

RAW_JS     = 'const RAW='     + json.dumps(raw_records,     ensure_ascii=False, separators=(',',':')) + ';'
RAW_MOP_JS = 'const RAW_MOP=' + json.dumps(raw_mop_records, ensure_ascii=False, separators=(',',':')) + ';'

# ── Read existing dashboard ────────────────────────────────────────────────────
with open(r'C:\Users\rdmorais\Desktop\Teste\dashboard_tpv.html', 'r', encoding='utf-8') as f:
    old = f.read()

raw_start = old.index('const RAW=[')
raw_end   = old.index('];', raw_start) + 2
head_part = old[:raw_start]
tail_part = old[raw_end:]

# ── 1. Add MOP filter in filters bar HTML ─────────────────────────────────────
mop_filter_html = (
    '  <!-- MOP: multi-select -->\n'
    '  <div class="fgrp">\n'
    '    <label>MOP</label>\n'
    '    <div class="ms-wrap" id="msMop">\n'
    '      <button class="ms-btn" id="msMopBtn" onclick="toggleMs(\'msMop\')">Todos</button>\n'
    '      <div class="ms-dropdown" id="msMopDrop">\n'
    '        <label class="ms-item ms-all"><input type="checkbox" id="msAllMop" onchange="toggleAllMop(this)"> Todos</label>\n'
    '      </div>\n'
    '    </div>\n'
    '  </div>'
)

head_part = head_part.replace(
    '  <div class="fgrp"><label>Canal</label><select id="fCanal" onchange="render()"><option value="">Todos</option></select></div>',
    '  <div class="fgrp"><label>Canal</label><select id="fCanal" onchange="render()"><option value="">Todos</option></select></div>\n' + mop_filter_html
)

# ── 2. Add MOP chart section before the table ─────────────────────────────────
mop_section_html = (
    '<div class="mop-row" style="display:grid;grid-template-columns:1fr 1fr;gap:14px;padding:14px 24px 0">\n'
    '  <div class="card">\n'
    '    <div class="card-title">TPV por MOP &mdash; Actual vs Plano (m&ecirc;ses Actual)</div>\n'
    '    <canvas id="cMop" style="max-height:300px"></canvas>\n'
    '  </div>\n'
    '  <div class="card">\n'
    '    <div class="card-title">MOP Trend &mdash; Actual (mensalizado)</div>\n'
    '    <canvas id="cMopTrend" style="max-height:300px"></canvas>\n'
    '  </div>\n'
    '</div>\n'
)
head_part = head_part.replace('<div class="tbl-wrap">', mop_section_html + '<div class="tbl-wrap">')

# ── 3. Patch JavaScript ────────────────────────────────────────────────────────

# 3a. Close MOP dropdown on outside click
tail_part = tail_part.replace(
    '  if(!e.target.closest("#msSeg"))document.getElementById("msSegDrop").classList.remove("open");',
    ('  if(!e.target.closest("#msSeg"))document.getElementById("msSegDrop").classList.remove("open");\n'
     '  if(!e.target.closest("#msMop"))document.getElementById("msMopDrop").classList.remove("open");')
)

# 3b. Add MOP multi-select functions
mop_ms_functions = """
/* MOP multi-select */
function getSelMops(){
  return [...document.querySelectorAll("#msMopDrop input.mop-cb:checked")].map(c=>c.value);
}
function updateMopBtn(){
  const sel=getSelMops();
  const all=[...document.querySelectorAll("#msMopDrop input.mop-cb")];
  const btn=document.getElementById("msMopBtn");
  if(sel.length===0||sel.length===all.length){btn.textContent="Todos";}
  else if(sel.length===1){btn.textContent=sel[0];}
  else{btn.textContent=sel.length+" MOPs";}
  document.getElementById("msAllMop").checked=(sel.length===all.length);
  render();
}
function toggleAllMop(cb){
  document.querySelectorAll("#msMopDrop input.mop-cb").forEach(c=>c.checked=cb.checked);
  updateMopBtn();
}
function popMop(){
  const vals=[...new Set(RAW_MOP.map(r=>r.MOP).filter(Boolean))].sort();
  const drop=document.getElementById("msMopDrop");
  vals.forEach(v=>{
    const lbl=document.createElement("label");
    lbl.className="ms-item";
    lbl.innerHTML=`<input type="checkbox" class="mop-cb" value="${v}" checked onchange="updateMopBtn()"> ${v}`;
    drop.appendChild(lbl);
  });
  document.getElementById("msAllMop").checked=true;
}"""

tail_part = tail_part.replace('function pop(id,col){', mop_ms_functions + '\nfunction pop(id,col){')

# 3c. Default segments: SMB and LONGTAIL only
old_popSeg = ('function popSeg(){\n'
              '  const vals=[...new Set(RAW.map(r=>r.SEGMENTO).filter(Boolean))].sort();\n'
              '  const drop=document.getElementById("msSegDrop");\n'
              '  vals.forEach(v=>{\n'
              '    const lbl=document.createElement("label");\n'
              '    lbl.className="ms-item";\n'
              '    lbl.innerHTML=`<input type="checkbox" class="seg-cb" value="${v}" checked onchange="updateSegBtn()"> ${v}`;\n'
              '    drop.appendChild(lbl);\n'
              '  });\n'
              '  document.getElementById("msAllSeg").checked=true;\n'
              '}')
new_popSeg = ('function popSeg(){\n'
              '  const defaults=new Set(["SMB","LONGTAIL"]);\n'
              '  const vals=[...new Set(RAW.map(r=>r.SEGMENTO).filter(Boolean))].sort();\n'
              '  const drop=document.getElementById("msSegDrop");\n'
              '  vals.forEach(v=>{\n'
              '    const lbl=document.createElement("label");\n'
              '    lbl.className="ms-item";\n'
              '    const chk=defaults.has(v);\n'
              '    lbl.innerHTML=`<input type="checkbox" class="seg-cb" value="${v}" ${chk?"checked":""} onchange="updateSegBtn()"> ${v}`;\n'
              '    drop.appendChild(lbl);\n'
              '  });\n'
              '  document.getElementById("msAllSeg").checked=false;\n'
              '  updateSegBtn();\n'
              '}')
tail_part = tail_part.replace(old_popSeg, new_popSeg)

# 3d. Add MOP filtering to filt()
old_return = ('  return RAW.filter(r=>\n'
              '    (!useP||selP.includes(r.PRODUTO))&&\n'
              '    (!c||r.CARTEIRA===c)&&\n'
              '    (!cn||r.CANAL===cn)&&\n'
              '    (!useS||selS.includes(r.SEGMENTO))\n'
              '  );')
new_return = ('  const selM=getSelMops();\n'
              '  const allM=document.querySelectorAll("#msMopDrop input.mop-cb").length;\n'
              '  const useM=selM.length>0&&selM.length<allM;\n'
              '  return RAW.filter(r=>\n'
              '    (!useP||selP.includes(r.PRODUTO))&&\n'
              '    (!c||r.CARTEIRA===c)&&\n'
              '    (!cn||r.CANAL===cn)&&\n'
              '    (!useS||selS.includes(r.SEGMENTO))&&\n'
              '    (!useM||!r.MOP||selM.includes(r.MOP))\n'
              '  );')
tail_part = tail_part.replace(old_return, new_return)

# 3e. Add MOP reset to resetFilters
tail_part = tail_part.replace(
    ('  ["fCart","fCanal"].forEach(x=>document.getElementById(x).value="");\n'
     '  render();\n'
     '}'),
    ('  ["fCart","fCanal"].forEach(x=>document.getElementById(x).value="");\n'
     '  document.querySelectorAll("#msMopDrop input").forEach(c=>c.checked=true);\n'
     '  updateMopBtn();\n'
     '  render();\n'
     '}')
)

# 3f. Add MOP chart rendering inside render() before closing }
mop_render_js = (
    '  /* MOP Charts */\n'
    '  const selM2=getSelMops();\n'
    '  const allM2=document.querySelectorAll("#msMopDrop input.mop-cb").length;\n'
    '  const useM2=selM2.length>0&&selM2.length<allM2;\n'
    '  const fCart2=document.getElementById("fCart").value;\n'
    '  const mopD=RAW_MOP.filter(r=>(!useP||selP.includes(r.PRODUTO))&&(!fCart2||r.CARTEIRA===fCart2)&&(!useM2||selM2.includes(r.MOP)));\n'
    '  const acMesM=[...new Set(RAW_MOP.filter(r=>r.CENARIO==="ACTUAL").map(r=>r.MES))].sort();\n'
    '  const mops=[...new Set(mopD.map(r=>r.MOP))].sort();\n'
    '  const mopByCen={};for(const c of SCEN){mopByCen[c]={};for(const mo of mops)mopByCen[c][mo]=0;}\n'
    '  for(const r of mopD){if(acMesM.includes(r.MES)&&mopByCen[r.CENARIO])mopByCen[r.CENARIO][r.MOP]=(mopByCen[r.CENARIO][r.MOP]||0)+r.VALOR;}\n'
    '  mk("cMop",{type:"bar",data:{labels:mops,datasets:SCEN.map(c=>({label:c,data:mops.map(mo=>mopByCen[c][mo]||0),backgroundColor:CA[c].replace(".15",".8"),borderColor:CC[c],borderWidth:1,borderRadius:4}))},options:{responsive:true,plugins:{legend:{position:"top"},datalabels:{display:false}},scales:{y:{ticks:{callback:v=>fmt(v)},grid:{color:"rgba(0,0,0,.06)"}},x:{ticks:{font:{size:9}}}}}});\n'
    '  const acMopBym={};for(const r of mopD){if(r.CENARIO==="ACTUAL"){if(!acMopBym[r.MOP])acMopBym[r.MOP]={};acMopBym[r.MOP][r.MES]=(acMopBym[r.MOP][r.MES]||0)+r.VALOR;}}\n'
    '  const topMops=Object.entries(acMopBym).sort((a,b)=>Object.values(b[1]).reduce((x,y)=>x+y,0)-Object.values(a[1]).reduce((x,y)=>x+y,0)).slice(0,5).map(e=>e[0]);\n'
    '  const mopColors=["#2563EB","#F97316","#16A34A","#9333EA","#0891B2"];\n'
    '  mk("cMopTrend",{type:"line",data:{labels:acMesM.map(mLbl),datasets:topMops.map((mo,i)=>({label:mo,data:acMesM.map(m=>(acMopBym[mo]||{})[m]||null),borderColor:mopColors[i],borderWidth:2.5,pointRadius:4,tension:.3,fill:false,spanGaps:true}))},options:{responsive:true,plugins:{legend:{position:"top"},datalabels:{display:false}},scales:{y:{ticks:{callback:v=>fmt(v)},grid:{color:"rgba(0,0,0,.06)"}}}}}});\n'
)

tail_part = tail_part.replace(
    '  document.getElementById("tblBody").innerHTML=rows.join("");\n}',
    '  document.getElementById("tblBody").innerHTML=rows.join("");\n' + mop_render_js + '}'
)

# 3g. Add popMop() to init
tail_part = tail_part.replace(
    'pop("fCart","CARTEIRA");pop("fCanal","CANAL");\npopProd();popSeg();\nrender();',
    'pop("fCart","CARTEIRA");pop("fCanal","CANAL");\npopProd();popSeg();popMop();\nrender();'
)

# ── Assemble and write ─────────────────────────────────────────────────────────
new_html = head_part + RAW_JS + '\n' + RAW_MOP_JS + tail_part

with open(r'C:\Users\rdmorais\Desktop\Teste\dashboard_tpv.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f"Dashboard written: {len(new_html):,} chars")

# Verify patches were applied
checks = [
    ('MOP filter added',      'id="msMop"' in new_html),
    ('RAW_MOP added',         'const RAW_MOP=' in new_html),
    ('MOP canvas added',      'id="cMop"' in new_html),
    ('popSeg defaults',       'SMB","LONGTAIL' in new_html),
    ('popMop() called',       'popMop()' in new_html),
    ('MOP chart render',      'cMopTrend' in new_html),
]
for name, ok in checks:
    print(f"  {'OK' if ok else 'FAIL'} {name}")
