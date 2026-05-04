"""
Reads f48_raw_new.tsv, aggregates all dimensions, replaces the f48
scenario in tpv_enhanced.json, then re-embeds the JSON in the HTML.
"""
import csv, json, re, os
from collections import defaultdict

MONTHS = [f'{y}{m:02d}' for y in [2025, 2026] for m in range(1, 13)]
MIDX   = {m: i for i, m in enumerate(MONTHS)}

def parse_num(s):
    s = str(s).strip()
    if not s or s == '-': return 0.0
    try:
        return float(s.replace('.', '').replace(',', '.'))
    except:
        return 0.0

BU_MAP = {'POINT':'POINT','QR SELLERS':'QR SELLERS','OP':'OP'}

SEG_MAP = {'LONGTAIL':'LONGTAIL','SMB':'SMB','BIG SELLERS':'BIG SELLERS'}

PROD_MAP = {
    'POINT':'POINT','TTP':'TTP','QR SELLERS':'QR',
    'LINK':'LINK','CHECKOUT':'CHECKOUT',
    'OTHERS':'OUTROS','-':'OUTROS','':'OUTROS',
}

MOP_MAP = {
    'account_money':'ACCOUNT_MONEY','bank_transfer':'BANK_TRANSFER',
    'credit_card':'CREDIT_CARD','debit_card':'DEBIT_CARD',
    'ticket':'TICKET','digital_currency':'DIGITAL_CURRENCY',
    'others':'OUTROS','':'OUTROS',
}

CANAL_MAP = {
    'FDV-P':'FDVP','FDV-T':'FDVT',
    'APP':'DIGITAIS','LANDING':'DIGITAIS',
    'LEGADO':'ENGAGEMENT','BIG SELLERS':'ENGAGEMENT',
    'TTP':'OUTROS','TO':'TELESALES','TELESALES':'TELESALES',
    'MGM':'MGM','RESELLERS':'RESELLERS',
    'OTHERS':'OUTROS','-':'OUTROS','':'OUTROS',
}

CART_MAP = {
    'AQUISICAO':'AQUISICAO',
    'LEGADO':'ENGAJAMENTO',
    'BS HUNTING':'ENGAJAMENTO','BS FARMING':'ENGAJAMENTO',
    'BS SIN TAG':'ENGAJAMENTO','BS HUNTING LC':'ENGAJAMENTO',
    'TTP':'ENGAJAMENTO',
    '-':'OUTROS','':'OUTROS',
}

def mk():
    return [0.0] * 24

total     = mk()
by_bu     = defaultdict(mk)
by_seg    = defaultdict(mk)
by_prod   = defaultdict(mk)
by_mop    = defaultdict(mk)
by_canal  = defaultdict(mk)
by_cart   = defaultdict(mk)

print("Reading f48_raw_new.tsv...")
with open('f48_raw_new.tsv', newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        if row.get('P&L', '').strip() != 'TPV':
            continue
        bu    = BU_MAP.get(row['BU'].strip(), '')
        seg   = SEG_MAP.get(row['SEG_OFICIAL'].strip(), '')
        prod  = PROD_MAP.get(row['PRODUTO'].strip(), 'OUTROS')
        mop   = MOP_MAP.get(row['MEIO_PAGO'].strip().lower(), 'OUTROS')
        canal = CANAL_MAP.get(row['CANAL'].strip(), 'OUTROS')
        cart  = CART_MAP.get(row['CARTEIRA'].strip().upper(), 'OUTROS')

        for m in MONTHS:
            val = parse_num(row.get(m, ''))
            if val == 0: continue
            idx = MIDX[m]
            total[idx]        += val
            if bu:   by_bu[bu][idx]     += val
            if seg:  by_seg[seg][idx]   += val
            if prod != 'OUTROS': by_prod[prod][idx]  += val
            if mop  != 'OUTROS': by_mop[mop][idx]    += val
            if canal != 'OUTROS': by_canal[canal][idx] += val
            if cart  != 'OUTROS': by_cart[cart][idx]  += val

def clean(d):
    out = {}
    for k, arr in d.items():
        r = [round(v) for v in arr]
        if any(r): out[k] = r
    return out

f48_new = {
    'total':       [round(v) for v in total],
    'by_bu':       clean(by_bu),
    'by_segment':  clean(by_seg),
    'by_product':  clean(by_prod),
    'by_mop':      clean(by_mop),
    'by_canal':    clean(by_canal),
    'by_carteira': clean(by_cart),
}

print("\nF4+8 totals by month:")
for i, m in enumerate(MONTHS):
    v = total[i]
    if v: print(f"  {m}: {v/1e9:.2f}B")
print(f"\nBUs:      {sorted(f48_new['by_bu'].keys())}")
print(f"Segs:     {sorted(f48_new['by_segment'].keys())}")
print(f"Products: {sorted(f48_new['by_product'].keys())}")
print(f"MOPs:     {sorted(f48_new['by_mop'].keys())}")
print(f"Canais:   {sorted(f48_new['by_canal'].keys())}")
print(f"Carteiras:{sorted(f48_new['by_carteira'].keys())}")

# ── Update tpv_enhanced.json ──────────────────────────────────────────────────
print("\nLoading tpv_enhanced.json...")
with open('tpv_enhanced.json', encoding='utf-8') as f:
    data = json.load(f)

data['scenarios']['f48'] = f48_new
with open('tpv_enhanced.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)
print(f"tpv_enhanced.json saved ({os.path.getsize('tpv_enhanced.json')//1024} KB)")

# ── Re-embed in HTML ──────────────────────────────────────────────────────────
print("Re-embedding in tpv_vs_forecast.html...")
with open('tpv_vs_forecast.html', encoding='utf-8') as f:
    html = f.read()

json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
html_new = re.sub(r'const D=\{.*?\};', f'const D={json_str};', html, count=1, flags=re.DOTALL)
with open('tpv_vs_forecast.html', 'w', encoding='utf-8') as f:
    f.write(html_new)
print("HTML updated. Done!")
