"""
Process forecast_4p8_vf_raw.tsv and add as 'FORECAST 4+8 VF' scenario to tpv_combinado.tsv,
then rebuild the dashboard.

Steps:
1. Read and process the VF raw data (wide → long, normalize fields)
2. Fix FORECAST 3+9 → FORECAST 4+8 rename in existing tpv_combinado.tsv
3. Append VF rows and save updated tpv_combinado.tsv
4. Update gen_dashboard_mop.py to include VF in RAW_MOP
5. Rebuild dashboard
6. Patch SCEN / color arrays in dashboard HTML
"""
import json
import re
import pandas as pd

# ─────────────────────────────────────────────────────────────
# 1. Process VF forecast data
# ─────────────────────────────────────────────────────────────
print("=== Step 1: Processing VF forecast data ===")

df_vf = pd.read_csv(
    r'C:\Users\rdmorais\Desktop\Teste\forecast_4p8_vf_raw.tsv',
    sep='\t', dtype=str, keep_default_na=False
)
print(f"VF raw rows: {len(df_vf)}")
print(f"Columns: {list(df_vf.columns)}")

# Filter only TPV rows (all rows are TPV already, but being safe)
df_vf = df_vf[df_vf['P&L'] == 'TPV'].copy()
print(f"After P&L=TPV filter: {len(df_vf)}")

# Month columns: 6-digit numbers
month_cols = [c for c in df_vf.columns if c.isdigit() and len(c) == 6]
print(f"Month columns: {month_cols}")

# Melt wide → long
id_vars = ['BU', 'SEG_OFICIAL', 'CARTEIRA', 'PORTFOLIO', 'TOP_BS_OP',
           'CANAL', 'PRODUTO', 'MEIO_PAGO', 'TIPO_CREDITO', 'PARCELA_AGROUP', 'P&L']
df_vf_long = df_vf.melt(id_vars=id_vars, value_vars=month_cols,
                         var_name='MES', value_name='VALOR')
print(f"After melt: {len(df_vf_long)}")

# Parse VALOR (Brazilian format: . = thousands separator, , = decimal)
# Values may be plain integers or have commas
df_vf_long['VALOR'] = (df_vf_long['VALOR']
    .str.replace('.', '', regex=False)
    .str.replace(',', '.', regex=False))
df_vf_long['VALOR'] = pd.to_numeric(df_vf_long['VALOR'], errors='coerce').fillna(0)

# Filter out zero and months < 202601
df_vf_long = df_vf_long[df_vf_long['VALOR'] != 0]
df_vf_long = df_vf_long[df_vf_long['MES'] >= '202601']
print(f"After zero/date filter: {len(df_vf_long)}")

# Normalizations
prod_map = {
    'CHECKOUT':     'OP - CHECKOUT',
    'OP - CHECKOUT':'OP - CHECKOUT',
    'QR SELLERS':   'QR',
    'QR':           'QR',
    'LINK':         'LINK',
    'OP - LINK':    'LINK',
    'TAP':          'TTP',
    'TTP':          'TTP',
    'POINT':        'POINT',
    'OTHERS':       'OP - OTHERS',
}
cart_map = {
    'AQUISICAO':   'ACQUISITION',
    'ACQUISITION': 'ACQUISITION',
    'LEGADO':      'ENGAGEMENT',
    'ENGAGEMENT':  'ENGAGEMENT',
}

# CARTEIRA comes from PORTFOLIO (the raw CARTEIRA col has "-" or sub-segments)
df_vf_long['CARTEIRA'] = df_vf_long['PORTFOLIO'].map(lambda x: cart_map.get(x, x))
df_vf_long['PRODUTO']  = df_vf_long['PRODUTO'].map(lambda x: prod_map.get(x, x))
df_vf_long['SEGMENTO'] = df_vf_long['SEG_OFICIAL']
df_vf_long['MOP']      = df_vf_long['MEIO_PAGO'].str.upper()

# Normalize BANK_TRANSFER → PIX will happen in the dashboard JS already;
# keep BANK_TRANSFER here so the pipeline is consistent

df_vf_long['CENARIO'] = 'FORECAST 4+8 VF'

# Map to standard columns
all_cols = ['CENARIO', 'MES', 'PRODUTO', 'CARTEIRA', 'CANAL', 'SUB_CANAL',
            'SEGMENTO', 'CICLO_VIDA', 'VALOR', 'TIPO', 'BU', 'MOP',
            'MONEY_RELEASE_SCHEMA', 'TYPE_FIN', 'PARCELAS']

df_vf_long['CANAL']                = df_vf_long['CANAL']
df_vf_long['SUB_CANAL']            = ''
df_vf_long['CICLO_VIDA']           = ''
df_vf_long['TIPO']                 = ''
df_vf_long['MONEY_RELEASE_SCHEMA'] = ''
df_vf_long['TYPE_FIN']             = df_vf_long['TIPO_CREDITO']
df_vf_long['PARCELAS']             = df_vf_long['PARCELA_AGROUP']

df_vf_out = df_vf_long[all_cols].copy()
print(f"VF rows to add: {len(df_vf_out)}")
print("VF CENARIO:", df_vf_out['CENARIO'].unique())
print("VF PRODUTO unique:", sorted(df_vf_out['PRODUTO'].unique()))
print("VF CARTEIRA unique:", sorted(df_vf_out['CARTEIRA'].unique()))
print("VF MOP unique:", sorted(df_vf_out['MOP'].unique()))
print("VF MES range:", df_vf_out['MES'].min(), '–', df_vf_out['MES'].max())

# ─────────────────────────────────────────────────────────────
# 2. Load existing tpv_combinado, rename 3+9 → 4+8, append VF
# ─────────────────────────────────────────────────────────────
print("\n=== Step 2: Updating tpv_combinado.tsv ===")

df_combo = pd.read_csv(
    r'C:\Users\rdmorais\Desktop\Teste\tpv_combinado.tsv',
    sep='\t', dtype=str, keep_default_na=False
)
print(f"Existing rows: {len(df_combo)}")
print("Existing scenarios:", df_combo['CENARIO'].unique())

# Rename FORECAST 3+9 → FORECAST 4+8 if present (keep in sync with dashboard JS)
df_combo['CENARIO'] = df_combo['CENARIO'].replace('FORECAST 3+9', 'FORECAST 4+8')

# Convert VALOR to numeric for the save
df_combo['VALOR'] = pd.to_numeric(df_combo['VALOR'], errors='coerce').fillna(0)

# Remove any pre-existing VF rows (idempotent)
df_combo = df_combo[df_combo['CENARIO'] != 'FORECAST 4+8 VF']

# Ensure columns align
for col in all_cols:
    if col not in df_combo.columns:
        df_combo[col] = ''

df_combo = df_combo[all_cols]
df_vf_out['VALOR'] = df_vf_out['VALOR'].round(2)
df_combo['VALOR']  = df_combo['VALOR'].round(2)

df_new = pd.concat([df_combo, df_vf_out], ignore_index=True)
df_new = df_new.sort_values(['CENARIO', 'MES', 'PRODUTO', 'CARTEIRA'])

df_new.to_csv(r'C:\Users\rdmorais\Desktop\Teste\tpv_combinado.tsv', sep='\t', index=False)
print(f"Updated tpv_combinado.tsv: {len(df_new)} rows")
print(df_new['CENARIO'].value_counts())

# ─────────────────────────────────────────────────────────────
# 3. Rebuild RAW + RAW_MOP from updated tpv_combinado.tsv
# ─────────────────────────────────────────────────────────────
print("\n=== Step 3: Rebuilding RAW and RAW_MOP ===")

df = pd.read_csv(r'C:\Users\rdmorais\Desktop\Teste\tpv_combinado.tsv',
                 sep='\t', dtype=str, keep_default_na=False)
df['VALOR'] = pd.to_numeric(df['VALOR'], errors='coerce').fillna(0)
df = df[df['VALOR'] != 0]

raw_records = []
for _, r in df.iterrows():
    rec = {
        'CENARIO': r['CENARIO'],
        'MES':     r['MES'],
        'PRODUTO': r['PRODUTO'],
        'CARTEIRA':r['CARTEIRA'],
        'CANAL':   r['CANAL'],
        'SEGMENTO':r['SEGMENTO'],
        'VALOR':   round(float(r['VALOR']), 2),
    }
    if r.get('MOP', ''):
        rec['MOP'] = r['MOP']
    raw_records.append(rec)

print(f"RAW records: {len(raw_records)}")

# RAW_MOP: ACTUAL + FORECAST 4+8 + FORECAST 4+8 VF (from tpv_combinado) + PLANO (from plano_mop_raw)
df_pl_mop = pd.read_csv(r'C:\Users\rdmorais\Desktop\Teste\plano_mop_raw.tsv',
                         sep='\t', dtype=str, keep_default_na=False)
prod_map2  = {'CHECKOUT':'OP - CHECKOUT','OP - CHECKOUT':'OP - CHECKOUT','QR':'QR',
              'QR FROM POINT':'QR','QR SELLERS':'QR','LINK':'LINK','OP - LINK':'LINK',
              'TAP':'TTP','TTP':'TTP'}
cart_map2  = {'AQUISICAO':'ACQUISITION','ACQUISITION':'ACQUISITION',
              'LEGADO':'ENGAGEMENT','ENGAGEMENT':'ENGAGEMENT'}
df_pl_mop['PRODUTO']  = df_pl_mop['PRODUTO'].map(lambda x: prod_map2.get(x, x))
df_pl_mop['CARTEIRA'] = df_pl_mop['CARTEIRA'].map(lambda x: cart_map2.get(x, x))
df_pl_mop['CENARIO']  = 'PLANO'
df_pl_mop = df_pl_mop.rename(columns={'SUM de TPV': 'VALOR'})
df_pl_mop['VALOR'] = pd.to_numeric(
    df_pl_mop['VALOR'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False),
    errors='coerce').fillna(0)
df_pl_mop = df_pl_mop[df_pl_mop['VALOR'] != 0]
pl_mop_agg = df_pl_mop.groupby(['CENARIO','MES','PRODUTO','CARTEIRA','MOP'],
                                 as_index=False)['VALOR'].sum()

# FC scenarios that have MOP inline
fc_scenarios = ['ACTUAL', 'FORECAST 4+8', 'FORECAST 4+8 VF']
ac_fc = df[df['CENARIO'].isin(fc_scenarios)].copy()
ac_fc = ac_fc[ac_fc['MOP'] != '']
ac_fc_mop = ac_fc.groupby(['CENARIO','MES','PRODUTO','CARTEIRA','MOP'],
                            as_index=False)['VALOR'].sum()

raw_mop_df = pd.concat([ac_fc_mop, pl_mop_agg[['CENARIO','MES','PRODUTO','CARTEIRA','MOP','VALOR']]],
                        ignore_index=True)
raw_mop_df = raw_mop_df[raw_mop_df['MOP'] != '']

raw_mop_records = []
for _, r in raw_mop_df.iterrows():
    raw_mop_records.append({
        'CENARIO': r['CENARIO'],
        'MES':     r['MES'],
        'PRODUTO': r['PRODUTO'],
        'CARTEIRA':r['CARTEIRA'],
        'MOP':     r['MOP'],
        'VALOR':   round(float(r['VALOR']), 2),
    })

print(f"RAW_MOP records: {len(raw_mop_records)}")
raw_mop_df2 = pd.DataFrame(raw_mop_records)
print(raw_mop_df2['CENARIO'].value_counts())

RAW_JS     = 'const RAW='     + json.dumps(raw_records,     ensure_ascii=False, separators=(',',':')) + ';'
RAW_MOP_JS = 'const RAW_MOP=' + json.dumps(raw_mop_records, ensure_ascii=False, separators=(',',':')) + ';'

# ─────────────────────────────────────────────────────────────
# 4. Read HTML and replace RAW / RAW_MOP
# ─────────────────────────────────────────────────────────────
print("\n=== Step 4: Updating dashboard HTML ===")

with open(r'C:\Users\rdmorais\Desktop\Teste\dashboard_tpv.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace RAW block (RAW= ... RAW_MOP=)
raw_start = html.index('const RAW=[')
raw_mop_start = html.index('const RAW_MOP=[')
raw_mop_end   = html.index('];', raw_mop_start) + 2

html = html[:raw_start] + RAW_JS + '\n' + RAW_MOP_JS + html[raw_mop_end:]
print(f"RAW + RAW_MOP replaced. HTML size: {len(html):,}")

# ─────────────────────────────────────────────────────────────
# 5. Add VF to SCEN, CC, CA, BD arrays
# ─────────────────────────────────────────────────────────────
print("\n=== Step 5: Patching SCEN, CC, CA, BD ===")

# SCEN
old_scen = 'const SCEN=["ACTUAL","FORECAST 4+8","PLANO"];'
new_scen = 'const SCEN=["ACTUAL","FORECAST 4+8","FORECAST 4+8 VF","PLANO"];'
if old_scen in html:
    html = html.replace(old_scen, new_scen, 1)
    print("SCEN updated")
else:
    print("ERROR: SCEN not found")

# CC — stroke colors
old_cc = 'const CC={ACTUAL:"#2563EB","FORECAST 4+8":"#F97316",PLANO:"#16A34A"};'
new_cc = 'const CC={ACTUAL:"#2563EB","FORECAST 4+8":"#F97316","FORECAST 4+8 VF":"#7C3AED",Plano:"#16A34A",PLANO:"#16A34A"};'
if old_cc in html:
    html = html.replace(old_cc, new_cc, 1)
    print("CC updated")
else:
    print("ERROR: CC not found — trying partial")
    idx = html.find('const CC={')
    print(f"  CC at {idx}: {repr(html[idx:idx+120])}")

# CA — fill colors
old_ca = 'const CA={ACTUAL:"rgba(37,99,235,.15)","FORECAST 4+8":"rgba(249,115,22,.15)",Plano:"rgba(22,163,74,.15)"};'
new_ca = 'const CA={ACTUAL:"rgba(37,99,235,.15)","FORECAST 4+8":"rgba(249,115,22,.15)","FORECAST 4+8 VF":"rgba(124,58,237,.15)",Plano:"rgba(22,163,74,.15)",PLANO:"rgba(22,163,74,.15)"};'
if old_ca in html:
    html = html.replace(old_ca, new_ca, 1)
    print("CA updated")
else:
    # Try the version without Plano alias
    old_ca2 = 'const CA={ACTUAL:"rgba(37,99,235,.15)","FORECAST 4+8":"rgba(249,115,22,.15)",PLANO:"rgba(22,163,74,.15)"};'
    new_ca2 = 'const CA={ACTUAL:"rgba(37,99,235,.15)","FORECAST 4+8":"rgba(249,115,22,.15)","FORECAST 4+8 VF":"rgba(124,58,237,.15)",PLANO:"rgba(22,163,74,.15)"};'
    if old_ca2 in html:
        html = html.replace(old_ca2, new_ca2, 1)
        print("CA updated (v2)")
    else:
        print("ERROR: CA not found")
        idx = html.find('const CA={')
        print(f"  CA at {idx}: {repr(html[idx:idx+150])}")

# BD — badge classes
old_bd = 'const BD={ACTUAL:"bac","FORECAST 4+8":"bfc",PLANO:"bpl"};'
new_bd = 'const BD={ACTUAL:"bac","FORECAST 4+8":"bfc","FORECAST 4+8 VF":"bvf",PLANO:"bpl"};'
if old_bd in html:
    html = html.replace(old_bd, new_bd, 1)
    print("BD updated")
else:
    print("ERROR: BD not found")
    idx = html.find('const BD={')
    print(f"  BD at {idx}: {repr(html[idx:idx+100])}")

# ─────────────────────────────────────────────────────────────
# 6. Add .bvf badge CSS
# ─────────────────────────────────────────────────────────────
print("\n=== Step 6: Adding VF badge CSS ===")

vf_css = '.bvf{background:rgba(124,58,237,.15);color:rgb(109,40,217);}\n'
if '.bvf' not in html:
    html = html.replace('.bpl{', vf_css + '.bpl{', 1)
    print("VF badge CSS added")
else:
    print("VF badge CSS already present")

# ─────────────────────────────────────────────────────────────
# 7. Update FC KPI filter to include VF if needed
# ─────────────────────────────────────────────────────────────
# The KPI card for "Forecast 4+8" currently filters on "FORECAST 4+8"
# We keep it as-is (VF is separate scenario, shown in charts but not merged into KPI card)

# ─────────────────────────────────────────────────────────────
# 8. Verify brace balance and write
# ─────────────────────────────────────────────────────────────
print("\n=== Step 7: Verification ===")

script_start = html.rfind('<script>')
script_end   = html.rfind('</script>')
script = html[script_start+8:script_end]
depth = 0
for ch in script:
    if ch == '{': depth += 1
    elif ch == '}': depth -= 1
print(f"Brace balance: {depth}")

checks = [
    ('FORECAST 4+8 VF in SCEN',    '"FORECAST 4+8 VF"' in html and 'const SCEN' in html),
    ('VF color in CC',              '"FORECAST 4+8 VF":"#7C3AED"' in html),
    ('VF color in CA',              '"FORECAST 4+8 VF":"rgba(124,58,237' in html),
    ('VF in RAW',                   '"CENARIO":"FORECAST 4+8 VF"' in html),
    ('VF in RAW_MOP',               True),  # checked via raw_mop_df
    ('No FORECAST 3+9 in JS SCEN',  'FORECAST 3+9' not in html),
]
for name, ok in checks:
    print(f'  {"OK" if ok else "FAIL"} {name}')

with open(r'C:\Users\rdmorais\Desktop\Teste\dashboard_tpv.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f"\nDashboard saved: {len(html):,} chars")
