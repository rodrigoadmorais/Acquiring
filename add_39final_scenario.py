"""
Process forecast_39_final_raw.tsv and add as 'FORECAST 3+9 FINAL' scenario.
Steps:
1. Read and process the raw data (wide->long, normalize fields)
2. Append to tpv_combinado.tsv
3. Rebuild RAW and RAW_MOP arrays in dashboard_tpv.html
4. Add FORECAST 3+9 FINAL to SCEN, CC, CA, BD arrays
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import json
import re
import pandas as pd

SCENARIO = 'FORECAST 3+9 FINAL'
COLOR    = '#0891B2'   # teal
COLOR_BG = 'rgba(8,145,178,.15)'
RAW_FILE = r'C:\Users\rdmorais\Desktop\Teste\forecast_39_final_raw.tsv'
COMBO    = r'C:\Users\rdmorais\Desktop\Teste\tpv_combinado.tsv'
HTML     = r'C:\Users\rdmorais\Desktop\Teste\dashboard_tpv.html'

# ─────────────────────────────────────────────────────────────
# 1. Process raw data
# ─────────────────────────────────────────────────────────────
print("=== Step 1: Processing 3+9 FINAL data ===")

df = pd.read_csv(RAW_FILE, sep='\t', dtype=str, keep_default_na=False)
print(f"Raw rows: {len(df)}")
print(f"Columns: {list(df.columns)}")

df = df[df['P&L'] == 'TPV'].copy()
print(f"After P&L=TPV filter: {len(df)}")

month_cols = [c for c in df.columns if c.isdigit() and len(c) == 6]
print(f"Month columns ({len(month_cols)}): {month_cols[0]}..{month_cols[-1]}")

id_vars = ['BU', 'SEG_OFICIAL', 'CARTEIRA', 'PORTFOLIO', 'TOP_BS_OP',
           'CANAL', 'PRODUTO', 'MEIO_PAGO', 'TIPO_CREDITO', 'PARCELA_AGROUP', 'P&L']
df_long = df.melt(id_vars=id_vars, value_vars=month_cols,
                  var_name='MES', value_name='VALOR')
print(f"After melt: {len(df_long)}")

# Parse VALOR (Brazilian format: . thousands, , decimal)
df_long['VALOR'] = (df_long['VALOR']
    .str.replace('.', '', regex=False)
    .str.replace(',', '.', regex=False))
df_long['VALOR'] = pd.to_numeric(df_long['VALOR'], errors='coerce').fillna(0)

# Keep all months (this is a 3+9 = starts May 2025, but keep what we have)
# Only filter out zero values
df_long = df_long[df_long['VALOR'] != 0]
print(f"After zero filter: {len(df_long)}")

# Normalizations
prod_map = {
    'CHECKOUT':      'OP - CHECKOUT',
    'OP - CHECKOUT': 'OP - CHECKOUT',
    'QR SELLERS':    'QR',
    'QR':            'QR',
    'LINK':          'LINK',
    'OP - LINK':     'LINK',
    'TAP':           'TTP',
    'TTP':           'TTP',
    'POINT':         'POINT',
    'OTHERS':        'OP - OTHERS',
    'OP - OTHERS':   'OP - OTHERS',
}
cart_map = {
    'AQUISICAO':   'ACQUISITION',
    'ACQUISITION': 'ACQUISITION',
    'LEGADO':      'ENGAGEMENT',
    'ENGAGEMENT':  'ENGAGEMENT',
}

# CARTEIRA comes from PORTFOLIO column
df_long['CARTEIRA'] = df_long['PORTFOLIO'].map(lambda x: cart_map.get(x, x))
df_long['PRODUTO']  = df_long['PRODUTO'].map(lambda x: prod_map.get(x, x))
df_long['SEGMENTO'] = df_long['SEG_OFICIAL']
df_long['MOP']      = df_long['MEIO_PAGO'].str.upper()
df_long['CENARIO']  = SCENARIO

# Fix '-' placeholder values -> ''
for col in ['CARTEIRA', 'CANAL', 'PRODUTO']:
    df_long[col] = df_long[col].replace('-', '')
df_long['CANAL'] = df_long['CANAL'].replace('-', '')

# Map to standard columns
df_long['SUB_CANAL']            = ''
df_long['CICLO_VIDA']           = ''
df_long['TIPO']                 = ''
df_long['MONEY_RELEASE_SCHEMA'] = ''
df_long['TYPE_FIN']             = df_long['TIPO_CREDITO']
df_long['PARCELAS']             = df_long['PARCELA_AGROUP']

all_cols = ['CENARIO', 'MES', 'PRODUTO', 'CARTEIRA', 'CANAL', 'SUB_CANAL',
            'SEGMENTO', 'CICLO_VIDA', 'VALOR', 'TIPO', 'BU', 'MOP',
            'MONEY_RELEASE_SCHEMA', 'TYPE_FIN', 'PARCELAS']

df_out = df_long[all_cols].copy()
print(f"Rows to add: {len(df_out)}")
print("CENARIO:", df_out['CENARIO'].unique())
print("PRODUTO unique:", sorted(df_out['PRODUTO'].unique()))
print("CARTEIRA unique:", sorted(df_out['CARTEIRA'].unique()))
print("MOP unique:", sorted(df_out['MOP'].unique()))
print("MES range:", df_out['MES'].min(), '--', df_out['MES'].max())

# ─────────────────────────────────────────────────────────────
# 2. Append to tpv_combinado.tsv
# ─────────────────────────────────────────────────────────────
print("\n=== Step 2: Updating tpv_combinado.tsv ===")

df_combo = pd.read_csv(COMBO, sep='\t', dtype=str, keep_default_na=False)
print(f"Existing rows: {len(df_combo)}")
print("Existing scenarios:", sorted(df_combo['CENARIO'].unique()))

# Remove any existing 3+9 FINAL rows (idempotent)
df_combo = df_combo[df_combo['CENARIO'] != SCENARIO]

# Ensure df_out VALOR is string for consistent TSV
df_out_str = df_out.copy()
df_out_str['VALOR'] = df_out_str['VALOR'].astype(str)

# Align columns
for col in df_combo.columns:
    if col not in df_out_str.columns:
        df_out_str[col] = ''

df_new = pd.concat([df_combo, df_out_str[df_combo.columns]], ignore_index=True)
print(f"After append: {len(df_new)}")
print("Scenarios:", sorted(df_new['CENARIO'].unique()))

df_new.to_csv(COMBO, sep='\t', index=False, encoding='utf-8')
print(f"Saved tpv_combinado.tsv: {len(df_new)} rows")

# ─────────────────────────────────────────────────────────────
# 3. Rebuild RAW and RAW_MOP in dashboard HTML
# ─────────────────────────────────────────────────────────────
print("\n=== Step 3: Rebuilding dashboard arrays ===")

with open(HTML, 'r', encoding='utf-8') as f:
    h = f.read()

# Build RAW array
df_raw_all = df_new.copy()
df_raw_all['VALOR'] = pd.to_numeric(df_raw_all['VALOR'], errors='coerce').fillna(0)
df_raw_nonzero = df_raw_all[df_raw_all['VALOR'] != 0]

raw_rows = []
for _, row in df_raw_nonzero.iterrows():
    obj = {
        'CENARIO':  row['CENARIO'],
        'MES':      row['MES'],
        'PRODUTO':  row['PRODUTO'],
        'CARTEIRA': row['CARTEIRA'],
        'CANAL':    row['CANAL'],
        'SEGMENTO': row['SEGMENTO'],
        'VALOR':    round(float(row['VALOR']), 2)
    }
    raw_rows.append(json.dumps(obj, ensure_ascii=False, separators=(',', ':')))

raw_js = 'const RAW=[\n' + ',\n'.join(raw_rows) + '\n];'
print(f"RAW rows: {len(raw_rows)}")

# Build RAW_MOP array
df_mop = df_raw_nonzero[
    df_raw_nonzero['MOP'].notna() & (df_raw_nonzero['MOP'] != '')
].copy()

mop_rows = []
for _, row in df_mop.iterrows():
    obj = {
        'CENARIO':  row['CENARIO'],
        'MES':      row['MES'],
        'PRODUTO':  row['PRODUTO'],
        'CARTEIRA': row['CARTEIRA'],
        'MOP':      row['MOP'],
        'VALOR':    round(float(row['VALOR']), 2)
    }
    mop_rows.append(json.dumps(obj, ensure_ascii=False, separators=(',', ':')))

raw_mop_js = 'const RAW_MOP=[\n' + ',\n'.join(mop_rows) + '\n];'
print(f"RAW_MOP rows: {len(mop_rows)}")

# Replace in HTML
old_raw = re.search(r'const RAW=\[[\s\S]*?\];', h).group(0)
h = h.replace(old_raw, raw_js, 1)
print("RAW replaced")

old_mop = re.search(r'const RAW_MOP=\[[\s\S]*?\];', h).group(0)
h = h.replace(old_mop, raw_mop_js, 1)
print("RAW_MOP replaced")

# ─────────────────────────────────────────────────────────────
# 4. Patch SCEN, CC, CA, BD arrays
# ─────────────────────────────────────────────────────────────
print("\n=== Step 4: Patching scenario arrays ===")

patches = [
    # SCEN: add 3+9 FINAL before PLANO
    ('const SCEN=["ACTUAL","FORECAST 4+8 VF","FORECAST 4+8","PLANO"];',
     'const SCEN=["ACTUAL","FORECAST 4+8 VF","FORECAST 4+8","FORECAST 3+9 FINAL","PLANO"];'),
    # CC colors
    ('const CC={ACTUAL:"#2563EB","FORECAST 4+8":"#F97316","FORECAST 4+8 VF":"#7C3AED",PLANO:"#16A34A"};',
     'const CC={ACTUAL:"#2563EB","FORECAST 4+8":"#F97316","FORECAST 4+8 VF":"#7C3AED","FORECAST 3+9 FINAL":"#0891B2",Plano:"#16A34A",PLANO:"#16A34A"};'),
]

# CA background colors
ca_old = re.search(r'const CA=\{[^}]+\};', h)
if ca_old:
    ca_str = ca_old.group(0)
    print(f"Found CA: {ca_str[:120]}")
    # Add 3+9 FINAL entry
    ca_new = ca_str.replace(
        'PLANO:"rgba(22,163,74,.15)"};',
        '"FORECAST 3+9 FINAL":"rgba(8,145,178,.15)",PLANO:"rgba(22,163,74,.15)"};'
    )
    if ca_new != ca_str:
        h = h.replace(ca_str, ca_new, 1)
        print("CA patched")
    else:
        print("WARN: CA patch not applied - check format")
else:
    print("WARN: CA not found")

# BD border colors
bd_old = re.search(r'const BD=\{[^}]+\};', h)
if bd_old:
    bd_str = bd_old.group(0)
    print(f"Found BD: {bd_str[:120]}")
    bd_new = bd_str.replace(
        'PLANO:"rgba(22,163,74,1)"};',
        '"FORECAST 3+9 FINAL":"rgba(8,145,178,1)",PLANO:"rgba(22,163,74,1)"};'
    )
    if bd_new != bd_str:
        h = h.replace(bd_str, bd_new, 1)
        print("BD patched")
    else:
        print("WARN: BD patch not applied - check format")
else:
    print("WARN: BD not found")

for old, new in patches:
    if old in h:
        h = h.replace(old, new, 1)
        print(f"OK  {old[:70]}")
    else:
        print(f"MISS {old[:70]}")

# Add legend pill for 3+9 FINAL (teal) before PLANO pill
old_plano_pill = '  <div class="pill"><div class="dot" style="background:var(--pl)"></div>PLANO</div>'
new_plano_pill = (
    '  <div class="pill"><div class="dot" style="background:#0891B2"></div>FORECAST 3+9 FINAL</div>\n'
    + old_plano_pill
)
if old_plano_pill in h:
    h = h.replace(old_plano_pill, new_plano_pill, 1)
    print("OK  legend pill 3+9 FINAL")
else:
    print("MISS legend pill (PLANO)")

# ─────────────────────────────────────────────────────────────
# 5. Verify and save
# ─────────────────────────────────────────────────────────────
sc = h[h.rfind('<script>')+8:h.rfind('</script>')]
depth = sum(1 if c=='{' else -1 if c=='}' else 0 for c in sc)
print(f'\nBrace balance: {depth}')

with open(HTML, 'w', encoding='utf-8') as f:
    f.write(h)
print(f'Saved dashboard: {len(h):,} chars')
