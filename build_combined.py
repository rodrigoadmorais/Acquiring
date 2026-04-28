import pandas as pd

# ── 1. FORECAST 3+9: read wide format, melt to long ──────────────────────────

df_fc = pd.read_csv(
    r'C:\Users\rdmorais\Desktop\Teste\forecast_39_raw.tsv',
    sep='\t',
    dtype=str,
    keep_default_na=False
)

id_vars = ['TIPO','CARTEIRA','CANAL','SUB_CANAL','SEGMENTO','CICLO_VIDA',
           'BU','Produto','MOP','MONEY_RELEASE_SCHEMA','TYPE_FIN','PARCELAS']

value_cols = [c for c in df_fc.columns if c.isdigit() and len(c) == 6]

df_fc_long = df_fc.melt(
    id_vars=id_vars,
    value_vars=value_cols,
    var_name='MES',
    value_name='VALOR'
)

df_fc_long = df_fc_long.rename(columns={'Produto': 'PRODUTO'})
df_fc_long['CENARIO'] = 'FORECAST 3+9'
df_fc_long['VALOR'] = (df_fc_long['VALOR']
    .str.replace('.', '', regex=False)
    .str.replace(',', '.', regex=False))

print(f"FORECAST 3+9 rows: {len(df_fc_long)}")

# ── 2. PLANO: already long format ─────────────────────────────────────────────

df_pl = pd.read_csv(
    r'C:\Users\rdmorais\Desktop\Teste\plano_raw.tsv',
    sep='\t',
    dtype=str,
    keep_default_na=False
)

df_pl = df_pl.rename(columns={'TPV_PLANO': 'VALOR'})
df_pl['CENARIO'] = 'PLANO'
df_pl['VALOR'] = (df_pl['VALOR']
    .str.replace('.', '', regex=False)
    .str.replace(',', '.', regex=False))

for col in ['TIPO','BU','MOP','MONEY_RELEASE_SCHEMA','TYPE_FIN','PARCELAS']:
    if col not in df_pl.columns:
        df_pl[col] = ''

print(f"PLANO rows: {len(df_pl)}")

# ── 3. ACTUAL ─────────────────────────────────────────────────────────────────

df_ac = pd.read_csv(
    r'C:\Users\rdmorais\Desktop\Teste\actual_raw.tsv',
    sep='\t',
    dtype=str,
    keep_default_na=False
)

df_ac = df_ac.rename(columns={
    'TIM_MONTH': 'MES',
    'CANAL_AJUSTADO': 'CANAL',
    'SUB_CANAL_AJUSTADO': 'SUB_CANAL',
    'CUST_SEGMENT_CROSS': 'SEGMENTO',
    'CICLO_VIDA_M0_TRIANGULO': 'CICLO_VIDA',
    'METODO_PAGAMENTO': 'MOP',
    'SUM de TPV': 'VALOR'
})
df_ac['CENARIO'] = 'ACTUAL'
df_ac['VALOR'] = (df_ac['VALOR']
    .str.replace('.', '', regex=False)
    .str.replace(',', '.', regex=False))

for col in ['TIPO','BU','MOP','MONEY_RELEASE_SCHEMA','TYPE_FIN','PARCELAS']:
    if col not in df_ac.columns:
        df_ac[col] = ''

print(f"ACTUAL rows: {len(df_ac)}")

# ── 4. Combine ─────────────────────────────────────────────────────────────────

all_cols = ['CENARIO','MES','PRODUTO','CARTEIRA','CANAL','SUB_CANAL',
            'SEGMENTO','CICLO_VIDA','VALOR',
            'TIPO','BU','MOP','MONEY_RELEASE_SCHEMA','TYPE_FIN','PARCELAS']

for col in all_cols:
    for df in [df_fc_long, df_pl, df_ac]:
        if col not in df.columns:
            df[col] = ''

df_combined = pd.concat(
    [df_fc_long[all_cols], df_pl[all_cols], df_ac[all_cols]],
    ignore_index=True
)

df_combined['MES'] = df_combined['MES'].astype(str).str.strip()
df_combined['VALOR'] = pd.to_numeric(df_combined['VALOR'], errors='coerce').fillna(0)

# ── 5. Normalize PRODUTO ──────────────────────────────────────────────────────
prod_map = {
    'CHECKOUT':      'OP - CHECKOUT',
    'OP - CHECKOUT': 'OP - CHECKOUT',
    'QR':            'QR',
    'QR FROM POINT': 'QR',
    'QR SELLERS':    'QR',
    'LINK':          'LINK',
    'OP - LINK':     'LINK',
    'TAP':           'TTP',
    'TTP':           'TTP',
}
df_combined['PRODUTO'] = df_combined['PRODUTO'].map(lambda x: prod_map.get(x, x))

# ── 6. Normalize CARTEIRA ─────────────────────────────────────────────────────
cart_map = {
    'AQUISICAO':  'ACQUISITION',
    'ACQUISITION': 'ACQUISITION',
    'LEGADO':     'ENGAGEMENT',
    'ENGAGEMENT': 'ENGAGEMENT',
}
df_combined['CARTEIRA'] = df_combined['CARTEIRA'].map(lambda x: cart_map.get(x, x))

df_combined = df_combined.sort_values(['CENARIO','MES','PRODUTO','CARTEIRA','CANAL'])

out_path = r'C:\Users\rdmorais\Desktop\Teste\tpv_combinado.tsv'
df_combined.to_csv(out_path, sep='\t', index=False)
print(f"\nSaved {len(df_combined)} rows to {out_path}")
print(df_combined['CENARIO'].value_counts())
print("\nMeses por cenário:")
print(df_combined.groupby('CENARIO')['MES'].unique())
