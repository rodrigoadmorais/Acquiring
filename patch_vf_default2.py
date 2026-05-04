import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\rdmorais\Desktop\Teste\dashboard_tpv.html', 'r', encoding='utf-8') as f:
    h = f.read()

patches = [
    # SCEN order: VF before original 4+8
    ('const SCEN=["ACTUAL","FORECAST 4+8","FORECAST 4+8 VF","PLANO"];',
     'const SCEN=["ACTUAL","FORECAST 4+8 VF","FORECAST 4+8","PLANO"];'),
    # Header subtitle
    ('Forecast 4+8 &middot; Plano &middot; Actual',
     'Forecast 4+8 VF &middot; Plano &middot; Actual'),
    # KPI card label
    ('Forecast 4+8 &mdash; Ano Completo',
     'Forecast 4+8 VF &mdash; Ano Completo'),
    # GMR KPI row label
    ('Take Rate Total FC 4+8 (Mai&ndash;Dez)',
     'Take Rate Total FC 4+8 VF (Mai&ndash;Dez)'),
    # GMR total KPI card label
    ('GMR Total Forecast 4+8 (Mai&ndash;Dez)',
     'GMR Total FC 4+8 VF (Mai&ndash;Dez)'),
    # sFcFull KPI: use VF
    ('const sFcFull=allM.reduce((a,m)=>a+(bsm["FORECAST 4+8"]||{})[m]||0,0);',
     'const sFcFull=allM.reduce((a,m)=>a+(bsm["FORECAST 4+8 VF"]||{})[m]||0,0);'),
    # trendScen FC toggle
    ('trendView==="fc"?["ACTUAL","FORECAST 4+8"]',
     'trendView==="fc"?["ACTUAL","FORECAST 4+8 VF"]'),
    # Trend button label
    ('>Actual + FC</button>',
     '>Actual + FC VF</button>'),
    # bPC product breakdown
    ('if(!bPC[k])bPC[k]={ACTUAL:0,"FORECAST 4+8":0,PLANO:0}',
     'if(!bPC[k])bPC[k]={ACTUAL:0,"FORECAST 4+8 VF":0,PLANO:0}'),
    # cMopTrend fcMopBym accumulation
    ('if(r.CENARIO==="FORECAST 4+8"){if(!fcMopBym',
     'if(r.CENARIO==="FORECAST 4+8 VF"){if(!fcMopBym'),
    # MOP evolution evoScens
    ('const evoScens=["FORECAST 4+8","PLANO"];',
     'const evoScens=["FORECAST 4+8 VF","PLANO"];'),
    # topEvoMops filter
    ('evoRaw.filter(r=>r.CENARIO==="FORECAST 4+8").map',
     'evoRaw.filter(r=>r.CENARIO==="FORECAST 4+8 VF").map'),
    # evoBySMop key
    ('evoBySMop["FORECAST 4+8|',
     'evoBySMop["FORECAST 4+8 VF|'),
    # evoDs label FC -> VF
    ('sc==="FORECAST 4+8"?"FC":"PL"',
     'sc==="FORECAST 4+8 VF"?"VF":"PL"'),
    # evoDs borderWidth
    ('sc==="FORECAST 4+8"?2.5:1.5',
     'sc==="FORECAST 4+8 VF"?2.5:1.5'),
    # evoDs pointRadius
    ('sc==="FORECAST 4+8"?3:2',
     'sc==="FORECAST 4+8 VF"?3:2'),
    # fcYTG TR section
    ('r.CENARIO==="FORECAST 4+8"&&ytgFilter',
     'r.CENARIO==="FORECAST 4+8 VF"&&ytgFilter'),
]

for old, new in patches:
    if old in h:
        h = h.replace(old, new, 1)
        print(f'OK  {old[:60]}')
    else:
        print(f'MISS {old[:60]}')

# Legend pill: add VF pill before existing 4+8 pill
old_pill = '  <div class="pill"><div class="dot" style="background:var(--fc)"></div>FORECAST 4+8</div>'
new_pill = (
    '  <div class="pill"><div class="dot" style="background:#7C3AED"></div>FORECAST 4+8 VF</div>\n'
    '  <div class="pill"><div class="dot" style="background:var(--fc)"></div>FORECAST 4+8</div>'
)
if old_pill in h:
    h = h.replace(old_pill, new_pill, 1)
    print('OK  legend pill')
else:
    print('MISS legend pill')

# Brace balance
sc = h[h.rfind('<script>')+8:h.rfind('</script>')]
depth = sum(1 if c == '{' else -1 if c == '}' else 0 for c in sc)
print(f'Brace balance: {depth}')

with open(r'C:\Users\rdmorais\Desktop\Teste\dashboard_tpv.html', 'w', encoding='utf-8') as f:
    f.write(h)
print(f'Saved: {len(h):,} chars')
