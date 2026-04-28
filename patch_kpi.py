with open('dashboard_tpv.html', 'r', encoding='utf-8') as f:
    html = f.read()

# ── 1. Replace KPI grid HTML (use exact encoded characters) ──────────────────
kg_start = html.find('class="kpi-grid">')
kg_end = html.find('</div>\n<div class="charts-row">', kg_start) + 6  # up to and including </div>
old_kpi_html = html[kg_start:kg_end]
print('KPI block found, length:', len(old_kpi_html))

new_kpi_html = (
    'class="kpi-grid">\n'
    '  <div class="kpi kfc"><div class="kpi-lbl">Forecast 4+8 &mdash; Ano Completo</div><div class="kpi-val" id="kFcFull">&#8212;</div><div class="kpi-delta" id="kFcFullM"></div></div>\n'
    '  <div class="kpi kpl"><div class="kpi-lbl">Plano &mdash; Ano Completo</div><div class="kpi-val" id="kPlFull">&#8212;</div><div class="kpi-delta" id="kPlFullD">vs Forecast</div></div>\n'
    '  <div class="kpi kvs"><div class="kpi-lbl">FC vs Plano</div><div class="kpi-val" id="kFCvsPL">&#8212;</div><div class="kpi-delta">desvio % (ano completo)</div></div>\n'
    '  <div class="kpi kac"><div class="kpi-lbl">Actual YTD</div><div class="kpi-val" id="kAc">&#8212;</div><div class="kpi-delta" id="kAcM"></div></div>\n'
    '  <div class="kpi kvs2"><div class="kpi-lbl">Actual vs Plano (mesmo per&iacute;odo)</div><div class="kpi-val" id="kVsPl">&#8212;</div><div class="kpi-delta">desvio %</div></div>\n'
    '</div>'
)
html = html[:kg_start] + new_kpi_html + html[kg_end:]

# ── 2. Replace KPI JS calculations ───────────────────────────────────────────
# Find by landmark: const acM=[...
pos = html.rfind("const acM=[...new Set(D.filter(r=>r.CENARIO===\"ACTUAL\")")
end_landmark = 'document.getElementById("kVsFc").innerHTML=pct(sAc,sFc);'
end_pos = html.find(end_landmark, pos)
if end_pos != -1:
    end_pos += len(end_landmark) + 1  # +1 for newline
    old_js = html[pos:end_pos]
    print('Old KPI JS found, length:', len(old_js))
    new_kpi_js = (
        'const acM=[...new Set(D.filter(r=>r.CENARIO==="ACTUAL").map(r=>r.MES))].sort();\n'
        '  const allM=[...new Set(D.map(r=>r.MES))].sort();\n'
        '  const sAc=Object.values(bsm["ACTUAL"]||{}).reduce((a,v)=>a+v,0);\n'
        '  const sFcFull=allM.reduce((a,m)=>a+(bsm["FORECAST 4+8"]||{})[m]||0,0);\n'
        '  const sPlFull=allM.reduce((a,m)=>a+(bsm["PLANO"]||{})[m]||0,0);\n'
        '  const sPlAcPer=acM.reduce((a,m)=>a+(bsm["PLANO"]||{})[m]||0,0);\n'
        '  document.getElementById("kFcFull").textContent=fmt(sFcFull);\n'
        '  document.getElementById("kFcFullM").textContent=allM.length+" meses";\n'
        '  document.getElementById("kPlFull").textContent=fmt(sPlFull);\n'
        '  document.getElementById("kPlFullD").innerHTML=pct(sPlFull,sFcFull)+" vs Forecast";\n'
        '  document.getElementById("kFCvsPL").innerHTML=pct(sFcFull,sPlFull);\n'
        '  document.getElementById("kAc").textContent=fmt(sAc);\n'
        '  document.getElementById("kAcM").textContent=acM.map(mLbl).join(", ")||"-";\n'
        '  document.getElementById("kVsPl").innerHTML=pct(sAc,sPlAcPer);\n'
    )
    html = html[:pos] + new_kpi_js + html[end_pos:]
    print('KPI JS replaced')
else:
    print('ERROR: end landmark not found')
    # Fallback: try to find kVsFc line
    kvsfc = html.find('kVsFc')
    print('kVsFc at:', kvsfc)
    print(repr(html[kvsfc-20:kvsfc+80]))

# Verify brace balance
script_start = html.rfind('<script>')
script_end = html.rfind('</script>')
script = html[script_start+8:script_end]
depth = 0
for ch in script:
    if ch == '{': depth += 1
    elif ch == '}': depth -= 1
print(f'Brace balance: {depth}')

for kid in ['kFcFull','kPlFull','kFCvsPL','kAc','kVsPl']:
    ok = ('id="'+kid+'"') in html
    print(f'  {kid}: {"OK" if ok else "MISSING"}')

with open('dashboard_tpv.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f'Saved: {len(html):,} chars')
