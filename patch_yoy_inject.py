import sys
sys.stdout.reconfigure(encoding='utf-8')

HTML = r'C:\Users\rdmorais\Desktop\Teste\dashboard_tpv.html'
with open(HTML, 'r', encoding='utf-8') as f:
    h = f.read()

# Find the exact closing of render() - it ends with }}}});\n\n}\n right before getMesRange
old = '}}}});\n\n}\nfunction getMesRange('

new = (
    '}}}});\n\n'
    '  /* YoY Chart */\n'
    '  const YOY_MM=["01","02","03","04","05","06","07","08","09","10","11","12"];\n'
    '  const YOY_LBL=["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"];\n'
    '  const yoyBase=filtNoDate();\n'
    '  const yoyDs=YOY_OPTS.filter(o=>visYoy.has(o.key)).map(o=>{\n'
    '    const byMM={};\n'
    '    for(const r of yoyBase){if(r.CENARIO===o.sc&&r.MES.startsWith(o.yr)){const mm=r.MES.slice(4);byMM[mm]=(byMM[mm]||0)+r.VALOR;}}\n'
    '    return{label:o.label,data:YOY_MM.map(mm=>byMM[mm]||null),borderColor:o.color,borderDash:o.dash,borderWidth:2.5,pointRadius:4,tension:.3,fill:false,spanGaps:false};\n'
    '  });\n'
    '  mk("cYoY",{type:"line",data:{labels:YOY_LBL,datasets:yoyDs},options:{responsive:true,plugins:{legend:{position:"top"},datalabels:{display:false}},scales:{y:{ticks:{callback:v=>fmt(v)},grid:{color:"rgba(0,0,0,.06)"}},x:{grid:{color:"rgba(0,0,0,.04)"}}}}});\n\n'
    '  /* Comparison Table */\n'
    '  renderComp();\n\n'
    '}\n'
    'function getMesRange('
)

if old in h:
    h = h.replace(old, new, 1)
    print('OK: YoY + renderComp injected into render()')
else:
    # debug: find the getMesRange location and look backwards
    idx = h.find('function getMesRange(')
    print('getMesRange at:', idx)
    print('Context before:', repr(h[max(0,idx-100):idx]))

sc = h[h.rfind('<script>')+8:h.rfind('</script>')]
depth = sum(1 if c=='{' else -1 if c=='}' else 0 for c in sc)
print('Brace balance:', depth)

with open(HTML, 'w', encoding='utf-8') as f:
    f.write(h)
print('Saved:', len(h))
