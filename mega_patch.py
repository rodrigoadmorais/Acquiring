"""
Mega patch:
1. cMopPct data labels
2. MOP Trend FC version selector
3. Scenario visibility (hide FC 4+8 by default)
4. YoY chart (2025 vs 2026, same month axis)
5. Comparativo A vs B table
"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

HTML = r'C:\Users\rdmorais\Desktop\Teste\dashboard_tpv.html'
with open(HTML, 'r', encoding='utf-8') as f:
    h = f.read()

OK = []; MISS = []

def patch(old, new, name):
    global h
    if old in h:
        h = h.replace(old, new, 1)
        OK.append(name)
    else:
        MISS.append(name)

# ─────────────────────────────────────────────────────────────
# 1. cMopPct data labels (show % inside bars >= 4%)
# ─────────────────────────────────────────────────────────────
patch(
    'datalabels:{display:false}},scales:{x:{stacked:true},y:{stacked:true,max:100',
    'datalabels:{display:ctx=>ctx.dataset.data[ctx.dataIndex]>=4,formatter:v=>v.toFixed(0)+"%",color:"#fff",font:{size:10,weight:"bold"},anchor:"center",align:"center"}},scales:{x:{stacked:true},y:{stacked:true,max:100',
    'cMopPct labels'
)

# ─────────────────────────────────────────────────────────────
# 2. MOP Trend card header – add FC selector dropdown
# ─────────────────────────────────────────────────────────────
patch(
    '      <div class="card-title" style="margin:0">MOP Trend &mdash; Actual + Forecast (AC sólido, FC tracejado)</div>\n      <div style="display:flex;gap:6px">\n        <button class="btn-trend active" id="btnMopAbs" onclick="setMopTrendMode(\'abs\',this)">Volume</button>\n        <button class="btn-trend" id="btnMopPct" onclick="setMopTrendMode(\'pct\',this)">Share %</button>\n      </div>',
    '      <div class="card-title" style="margin:0">MOP Trend &mdash; Actual + <span id="mopFcLabel">FC VF</span></div>\n      <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap">\n        <select id="selMopFc" onchange="mopTrendFc=this.value;document.getElementById(\'mopFcLabel\').textContent=this.options[this.selectedIndex].text;render()" style="font-size:11px;padding:4px 8px;border-radius:6px;border:1px solid var(--border);background:var(--bg);color:var(--text)"></select>\n        <button class="btn-trend active" id="btnMopAbs" onclick="setMopTrendMode(\'abs\',this)">Volume</button>\n        <button class="btn-trend" id="btnMopPct" onclick="setMopTrendMode(\'pct\',this)">Share %</button>\n      </div>',
    'MOP Trend FC selector HTML'
)

# ─────────────────────────────────────────────────────────────
# 3. Add mopTrendFc state variable
# ─────────────────────────────────────────────────────────────
patch(
    "let mopTrendMode='abs';",
    "let mopTrendMode='abs';let mopTrendFc='FORECAST 4+8 VF';",
    'mopTrendFc state'
)

# ─────────────────────────────────────────────────────────────
# 4. fcMopBym loop – use mopTrendFc instead of hardcoded string
# ─────────────────────────────────────────────────────────────
patch(
    'if(r.CENARIO==="FORECAST 4+8 VF"){if(!fcMopBym[r.MOP])fcMopBym[r.MOP]={};fcMopBym[r.MOP][r.MES]=(fcMopBym[r.MOP][r.MES]||0)+r.VALOR;}',
    'if(r.CENARIO===mopTrendFc){if(!fcMopBym[r.MOP])fcMopBym[r.MOP]={};fcMopBym[r.MOP][r.MES]=(fcMopBym[r.MOP][r.MES]||0)+r.VALOR;}',
    'fcMopBym use mopTrendFc'
)

# ─────────────────────────────────────────────────────────────
# 5. visScens state + SC_LABELS + COMP_PERIODS after SCEN
# ─────────────────────────────────────────────────────────────
patch(
    'const SCEN=["ACTUAL","FORECAST 4+8 VF","FORECAST 4+8","FORECAST 3+9 FINAL","PLANO"];',
    '''const SCEN=["ACTUAL","FORECAST 4+8 VF","FORECAST 4+8","FORECAST 3+9 FINAL","PLANO"];
const SC_LABELS={"ACTUAL":"Actual","FORECAST 4+8 VF":"FC 4+8 VF","FORECAST 4+8":"FC 4+8","FORECAST 3+9 FINAL":"3+9 Final","PLANO":"Plano"};
const COMP_PERIODS=[{key:"ytd",label:"YTD"},{key:"ytg",label:"YTG"},{key:"2026",label:"2026 Ano"},{key:"2025",label:"2025 Ano"}];
let visScens=new Set(["ACTUAL","FORECAST 4+8 VF","FORECAST 3+9 FINAL","PLANO"]);
let acMonthsGlobal=[];
function toggleScen(sc,cb){if(cb.checked)visScens.add(sc);else visScens.delete(sc);updateScenBtn();render();}
function updateScenBtn(){const b=document.getElementById("msScenBtn");if(b)b.textContent=SCEN.filter(s=>visScens.has(s)).map(s=>SC_LABELS[s]).join(", ")||"Nenhum";}
const YOY_OPTS=[
  {key:"ACTUAL|2025",label:"Actual 2025",sc:"ACTUAL",yr:"2025",color:"#93C5FD",dash:[]},
  {key:"ACTUAL|2026",label:"Actual 2026",sc:"ACTUAL",yr:"2026",color:"#2563EB",dash:[]},
  {key:"FORECAST 4+8 VF|2026",label:"FC VF 2026",sc:"FORECAST 4+8 VF",yr:"2026",color:"#7C3AED",dash:[5,3]},
  {key:"FORECAST 3+9 FINAL|2025",label:"3+9 Final 2025",sc:"FORECAST 3+9 FINAL",yr:"2025",color:"#67E8F9",dash:[3,3]},
  {key:"FORECAST 3+9 FINAL|2026",label:"3+9 Final 2026",sc:"FORECAST 3+9 FINAL",yr:"2026",color:"#0891B2",dash:[5,3]},
  {key:"PLANO|2026",label:"Plano 2026",sc:"PLANO",yr:"2026",color:"#16A34A",dash:[5,3]},
];
let visYoy=new Set(["ACTUAL|2025","ACTUAL|2026","FORECAST 4+8 VF|2026"]);''',
    'visScens + SC_LABELS + YOY state'
)

# ─────────────────────────────────────────────────────────────
# 6. Add "Cenários" filter to filters bar (before Limpar button)
# ─────────────────────────────────────────────────────────────
patch(
    '<button class="rbtn" onclick="resetFilters()">&#8635; Limpar</button>',
    '''<div class="fgrp">
    <label>Cen&#225;rios</label>
    <div class="ms-wrap" id="msScen">
      <button class="ms-btn" id="msScenBtn" onclick="toggleMs(\'msScen\')" style="min-width:120px">Vis&#237;veis</button>
      <div class="ms-dropdown" id="msScenDrop"></div>
    </div>
  </div>
  <button class="rbtn" onclick="resetFilters()">&#8635; Limpar</button>''',
    'scenario filter in filters bar'
)

# ─────────────────────────────────────────────────────────────
# 7. filt() – add visScens check
# ─────────────────────────────────────────────────────────────
patch(
    '  return RAW.filter(r=>\n    (!useP||selP.includes(r.PRODUTO))&&\n    (!c||r.CARTEIRA===c)&&\n    (!cn||r.CANAL===cn)&&\n    (!useS||selS.includes(r.SEGMENTO))&&\n    (!useM||!r.MOP||selM.includes(r.MOP))&&\n    (!mIni||r.MES>=mIni)&&(!mFim||r.MES<=mFim)\n  );',
    '  return RAW.filter(r=>\n    visScens.has(r.CENARIO)&&\n    (!useP||selP.includes(r.PRODUTO))&&\n    (!c||r.CARTEIRA===c)&&\n    (!cn||r.CANAL===cn)&&\n    (!useS||selS.includes(r.SEGMENTO))&&\n    (!useM||!r.MOP||selM.includes(r.MOP))&&\n    (!mIni||r.MES>=mIni)&&(!mFim||r.MES<=mFim)\n  );',
    'filt() visScens'
)

# ─────────────────────────────────────────────────────────────
# 8. Add filtNoDate() helper after filt()
# ─────────────────────────────────────────────────────────────
patch(
    'function mk(id,cfg){if(CH[id])CH[id].destroy();CH[id]=new Chart(documen',
    '''function filtNoDate(){
  const selP=getSelProds();const allP=document.querySelectorAll("#msProdDrop input.prod-cb").length;const useP=selP.length>0&&selP.length<allP;
  const c=document.getElementById("fCart").value;const cn=document.getElementById("fCanal").value;
  const selS=getSelSegs();const allS=document.querySelectorAll("#msSegDrop input.seg-cb").length;const useS=selS.length>0&&selS.length<allS;
  return RAW.filter(r=>(!useP||selP.includes(r.PRODUTO))&&(!c||r.CARTEIRA===c)&&(!cn||r.CANAL===cn)&&(!useS||selS.includes(r.SEGMENTO)));
}
function mk(id,cfg){if(CH[id])CH[id].destroy();CH[id]=new Chart(documen''',
    'filtNoDate() helper'
)

# ─────────────────────────────────────────────────────────────
# 9. pctScenLabels – use activeScen (respects visScens)
# ─────────────────────────────────────────────────────────────
patch(
    'const pctScenLabels=SCEN.filter(c=>Object.values(pctByCenMop[c]).some(v=>v>0));',
    'const activeScen=SCEN.filter(c=>visScens.has(c));\n  const pctScenLabels=activeScen.filter(c=>Object.values(pctByCenMop[c]||{}).some(v=>v>0));',
    'pctScenLabels activeScen'
)

# ─────────────────────────────────────────────────────────────
# 10. YoY chart + renderComp() – add before closing </script>
#     Also add YoY chart render call inside render()
# ─────────────────────────────────────────────────────────────

# Add YoY render call at the END of render() function (just before closing brace of render)
patch(
    '  mk("cMopPct",{type:"bar",data:{labels:pctScenLabels,datasets:pctDs},options:{responsive:true,plugins:{legend:{position:"bottom",labels:{font:{size:9},boxWidth:12}},datalabels:{display:ctx=>ctx.dataset.data[ctx.dataIndex]>=4,formatter:v=>v.toFixed(0)+"%",color:"#fff",font:{size:10,weight:"bold"},anchor:"center",align:"center"}},scales:{x:{stacked:true},y:{stacked:true,max:100,ticks:{callback:v=>v+"%"},grid:{color:"rgba(0,0,0,.06)"}}}}})\n\n}',
    '''  mk("cMopPct",{type:"bar",data:{labels:pctScenLabels,datasets:pctDs},options:{responsive:true,plugins:{legend:{position:"bottom",labels:{font:{size:9},boxWidth:12}},datalabels:{display:ctx=>ctx.dataset.data[ctx.dataIndex]>=4,formatter:v=>v.toFixed(0)+"%",color:"#fff",font:{size:10,weight:"bold"},anchor:"center",align:"center"}},scales:{x:{stacked:true},y:{stacked:true,max:100,ticks:{callback:v=>v+"%"},grid:{color:"rgba(0,0,0,.06)"}}}}});

  /* ── YoY Chart ── */
  const YOY_MM=["01","02","03","04","05","06","07","08","09","10","11","12"];
  const YOY_LBL=["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"];
  const yoyBase=filtNoDate();
  const yoyDs=YOY_OPTS.filter(o=>visYoy.has(o.key)).map(o=>{
    const byMM={};
    for(const r of yoyBase){if(r.CENARIO===o.sc&&r.MES.startsWith(o.yr)){const mm=r.MES.slice(4);byMM[mm]=(byMM[mm]||0)+r.VALOR;}}
    return{label:o.label,data:YOY_MM.map(mm=>byMM[mm]||null),borderColor:o.color,borderDash:o.dash,borderWidth:2.5,pointRadius:4,tension:.3,fill:false,spanGaps:false};
  });
  mk("cYoY",{type:"line",data:{labels:YOY_LBL,datasets:yoyDs},options:{responsive:true,plugins:{legend:{position:"top"},datalabels:{display:false}},scales:{y:{ticks:{callback:v=>fmt(v)},grid:{color:"rgba(0,0,0,.06)"}},x:{grid:{color:"rgba(0,0,0,.04)"}}}}});

  /* ── Comparison Table ── */
  renderComp();

}''',
    'YoY + renderComp in render()'
)

# ─────────────────────────────────────────────────────────────
# 11. Add renderComp() function + init additions before </script>
# ─────────────────────────────────────────────────────────────
old_init = 'pop("fCart","CARTEIRA");pop("fCanal","CANAL");\npopProd();popSeg();popMop();popPeriod();\nrender();'
new_init = '''pop("fCart","CARTEIRA");pop("fCanal","CANAL");
popProd();popSeg();popMop();popPeriod();

/* Populate scenario visibility checkboxes */
(function(){
  const drop=document.getElementById("msScenDrop");
  if(!drop)return;
  SCEN.forEach(sc=>{
    const lbl=document.createElement("label");
    lbl.className="ms-item";
    const chk=document.createElement("input");
    chk.type="checkbox"; chk.checked=visScens.has(sc);
    chk.onchange=()=>toggleScen(sc,chk);
    lbl.appendChild(chk);
    lbl.appendChild(document.createTextNode(" "+(SC_LABELS[sc]||sc)));
    drop.appendChild(lbl);
  });
  updateScenBtn();
})();

/* Populate MOP Trend FC selector */
(function(){
  const sel=document.getElementById("selMopFc");
  if(!sel)return;
  SCEN.filter(s=>s!=="ACTUAL"&&s!=="PLANO").forEach(sc=>{
    const o=new Option(SC_LABELS[sc]||sc, sc);
    if(sc===mopTrendFc)o.selected=true;
    sel.add(o);
  });
})();

/* Populate comparison dropdowns */
(function(){
  acMonthsGlobal=[...new Set(RAW.filter(r=>r.CENARIO==="ACTUAL").map(r=>r.MES))].sort();
  function hasData(sc,pk){
    const r=getMesRange(pk);
    return RAW.some(x=>x.CENARIO===sc&&x.MES>=r[0]&&x.MES<=r[1]);
  }
  const opts=[];
  for(const sc of SCEN){
    for(const p of COMP_PERIODS){
      if(hasData(sc,p.key)) opts.push({v:sc+"|"+p.key,l:(SC_LABELS[sc]||sc)+" — "+p.label});
    }
  }
  ["selCompA","selCompB"].forEach(id=>{
    const sel=document.getElementById(id); if(!sel)return;
    opts.forEach(o=>sel.add(new Option(o.l,o.v)));
  });
  const sA=document.getElementById("selCompA");
  const sB=document.getElementById("selCompB");
  if(sA){sA.value="ACTUAL|ytd"; if(!sA.value)sA.selectedIndex=0;}
  if(sB){sB.value="PLANO|2026"; if(!sB.value)sB.selectedIndex=Math.min(1,sB.options.length-1);}
})();

/* YoY toggle buttons */
(function(){
  const wrap=document.getElementById("yoyToggles");
  if(!wrap)return;
  YOY_OPTS.forEach(o=>{
    const b=document.createElement("button");
    b.className="btn-trend"+(visYoy.has(o.key)?" active":"");
    b.textContent=o.label;
    b.style.cssText="border-left:3px solid "+o.color+";padding-left:8px";
    b.onclick=()=>{
      if(visYoy.has(o.key))visYoy.delete(o.key);else visYoy.add(o.key);
      b.classList.toggle("active",visYoy.has(o.key));
      render();
    };
    wrap.appendChild(b);
  });
})();

render();'''
patch(old_init, new_init, 'init additions')

# ─────────────────────────────────────────────────────────────
# 12. Add getMesRange() + renderComp() before toggleMobile()
# ─────────────────────────────────────────────────────────────
patch(
    'function toggleMobile(){',
    '''function getMesRange(pk){
  const acLast=acMonthsGlobal[acMonthsGlobal.length-1]||"202604";
  const y=parseInt(acLast.slice(0,4)), m=parseInt(acLast.slice(4));
  const nm=m===12?1:m+1, ny=m===12?y+1:y;
  const ytgFirst=String(ny*100+nm).padStart(6,"0");
  if(pk==="ytd")return["202601",acLast];
  if(pk==="ytg")return[ytgFirst,"202612"];
  if(pk==="2026")return["202601","202612"];
  if(pk==="2025")return["202501","202512"];
  return["202601","202612"];
}
function renderComp(){
  const selA=document.getElementById("selCompA");
  const selB=document.getElementById("selCompB");
  if(!selA||!selB||!selA.value||!selB.value)return;
  const [scA,pkA]=selA.value.split("|");
  const [scB,pkB]=selB.value.split("|");
  const pA=COMP_PERIODS.find(p=>p.key===pkA)||COMP_PERIODS[2];
  const pB=COMP_PERIODS.find(p=>p.key===pkB)||COMP_PERIODS[2];
  function compute(sc,p){
    const [mI,mF]=getMesRange(p.key);
    const base=filtNoDate().filter(r=>r.CENARIO===sc&&r.MES>=mI&&r.MES<=mF);
    const total=base.reduce((s,r)=>s+r.VALOR,0);
    const bu={OP:0,POINT:0,QR:0};
    for(const r of base){
      if(r.PRODUTO==="QR")bu.QR+=r.VALOR;
      else if(["POINT","TTP"].includes(r.PRODUTO))bu.POINT+=r.VALOR;
      else bu.OP+=r.VALOR;
    }
    const mopBase=RAW_MOP.filter(r=>r.CENARIO===sc&&r.MES>=mI&&r.MES<=mF);
    const mopTot=mopBase.reduce((s,r)=>s+r.VALOR,0);
    const mopMap={};
    for(const r of mopBase){const m=r.MOP==="BANK_TRANSFER"?"PIX":r.MOP;mopMap[m]=(mopMap[m]||0)+r.VALOR;}
    return{total,bu,mopMap,mopTot};
  }
  const dA=compute(scA,pA), dB=compute(scB,pB);
  const fv=v=>v>=1e12?(v/1e12).toFixed(1)+"T":v>=1e9?(v/1e9).toFixed(1)+"B":v>=1e6?(v/1e6).toFixed(1)+"M":v>=1e3?(v/1e3).toFixed(0)+"K":Math.round(v)+"";
  const dp=(a,b)=>{if(!b)return"";const p=((a/b-1)*100);return" <span class='"+(p>=0?"pos":"neg")+"'>("+(p>=0?"+":"")+p.toFixed(1)+"%)</span>"};
  const sh=(v,t)=>t>0?Math.round(v/t*100)+"%":"—";
  const MN={"CREDIT_CARD":"Cr\xe9dito","DEBIT_CARD":"D\xe9bito","PIX":"PIX","ACCOUNT_MONEY":"Conta MP","TICKET":"Boleto","DIGITAL_CURRENCY":"Digital","PREPAID_CARD":"Pr\xe9-pago","VOUCHER_CARD":"Vale"};
  const TOP_MOPS=["CREDIT_CARD","DEBIT_CARD","PIX","ACCOUNT_MONEY","TICKET"];
  const hA=(SC_LABELS[scA]||scA)+" "+pA.label;
  const hB=(SC_LABELS[scB]||scB)+" "+pB.label;
  let t=`<table style="width:100%;border-collapse:collapse;font-size:12px">
<thead><tr style="background:var(--yellow)"><th style="padding:6px 10px;text-align:left;font-size:10px;font-weight:700;text-transform:uppercase">M\xe9trica</th><th style="padding:6px 10px;text-align:right;font-size:10px;font-weight:700">A: ${hA.toUpperCase()}</th><th style="padding:6px 10px;text-align:right;font-size:10px;font-weight:700">B: ${hB.toUpperCase()}</th></tr></thead><tbody>`;
  const sec=(lbl)=>`<tr style="background:rgba(0,0,0,.04)"><td colspan="3" style="padding:4px 10px;font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.5px;color:var(--sub)">${lbl}</td></tr>`;
  const row=(lbl,vA,vB,pctA,totA,pctB,totB)=>`<tr><td style="padding:5px 10px">${lbl}</td><td style="padding:5px 10px;text-align:right">${fv(vA)}${dp(vA,vB)} <span style="color:var(--sub);font-size:10px">${pctA!==null?sh(vA,pctA):""}</span></td><td style="padding:5px 10px;text-align:right;color:var(--sub)">${fv(vB)} <span style="font-size:10px">${pctB!==null?sh(vB,pctB):""}</span></td></tr>`;
  t+=sec("Total");
  t+=row("TPV",dA.total,dB.total,null,null,null,null);
  t+=sec("Por BU");
  for(const bu of["OP","POINT","QR"])t+=row(bu,dA.bu[bu],dB.bu[bu],null,null,null,null);
  t+=sec("Share MOP");
  for(const mo of TOP_MOPS)t+=row(MN[mo]||mo,dA.mopMap[mo]||0,dB.mopMap[mo]||0,dA.mopTot,dA.mopTot,dB.mopTot,dB.mopTot);
  t+="</tbody></table>";
  const el=document.getElementById("compTable"); if(el)el.innerHTML=t;
}
function toggleMobile(){''',
    'getMesRange + renderComp()'
)

# ─────────────────────────────────────────────────────────────
# 13. Add HTML sections (YoY + Comparison table) before </body>
# ─────────────────────────────────────────────────────────────
patch(
    '</body>',
    '''<!-- ── YoY + Comparison Table ── -->
<div style="display:grid;grid-template-columns:1fr 340px;gap:14px;padding:14px 24px 24px;align-items:start">
  <div class="card">
    <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:10px">
      <div class="card-title" style="margin:0">&#128200; 2025 vs 2026 &mdash; mesmo eixo de meses</div>
      <div id="yoyToggles" style="display:flex;gap:6px;flex-wrap:wrap"></div>
    </div>
    <canvas id="cYoY" style="max-height:280px"></canvas>
  </div>
  <div class="card">
    <div style="font-size:13px;font-weight:800;margin-bottom:12px;text-transform:uppercase;letter-spacing:.5px">&#9878; Comparativo A vs B</div>
    <div style="display:flex;flex-direction:column;gap:8px;margin-bottom:12px">
      <div>
        <label style="font-size:10px;font-weight:700;color:var(--sub);text-transform:uppercase;display:block;margin-bottom:3px">Cen&#225;rio A</label>
        <select id="selCompA" onchange="renderComp()" style="width:100%;font-size:12px;padding:5px 8px;border-radius:6px;border:1px solid var(--border);background:var(--bg);color:var(--text)"></select>
      </div>
      <div>
        <label style="font-size:10px;font-weight:700;color:var(--sub);text-transform:uppercase;display:block;margin-bottom:3px">Cen&#225;rio B</label>
        <select id="selCompB" onchange="renderComp()" style="width:100%;font-size:12px;padding:5px 8px;border-radius:6px;border:1px solid var(--border);background:var(--bg);color:var(--text)"></select>
      </div>
    </div>
    <div id="compTable"></div>
  </div>
</div>
</body>''',
    'YoY + Comparison table HTML'
)

# ─────────────────────────────────────────────────────────────
# Report + verify
# ─────────────────────────────────────────────────────────────
print("OK:", OK)
print("MISS:", MISS)

sc = h[h.rfind('<script>')+8:h.rfind('</script>')]
depth = sum(1 if c=='{' else -1 if c=='}' else 0 for c in sc)
print(f'Brace balance: {depth}')

with open(HTML, 'w', encoding='utf-8') as f:
    f.write(h)
print(f'Saved: {len(h):,} chars')
