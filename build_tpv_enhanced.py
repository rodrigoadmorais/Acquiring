"""
Builds tpv_enhanced.json with full dimension breakdowns:
  actual   → Jan-Apr 2026 (actual_raw.tsv)
  f39      → Apr-Dec 2026 forecast (unified_scenarios_raw.tsv FORECAST 3+9)
             Jan-Mar 2026 actuals reused from actual_raw.tsv
  f48      → May-Dec 2026 forecast (unified_scenarios_raw.tsv FORECAST 4+8)
             Jan-Apr 2026 actuals reused from actual_raw.tsv
  plano    → Jan-Dec 2026 (unified_scenarios_raw.tsv PLANO V5)
"""
import csv, json
from collections import defaultdict

# ── Normalisation maps ────────────────────────────────────────────────────────
PROD_ACTUAL = {
    'OP - CHECKOUT':'CHECKOUT','OP - LINK':'LINK','OP - OTHERS':'OTHERS',
    'POINT':'POINT','QR':'QR','QR FROM POINT':'QR','TAP':'TTP',
}
PROD_FC = {
    'CHECKOUT':'CHECKOUT','LINK':'LINK','POINT':'POINT',
    'QR SELLERS':'QR','TTP':'TTP','QR':'QR',
    'OP - CHECKOUT':'CHECKOUT','OP - LINK':'LINK','OP - OTHERS':'OTHERS',
}
CANAL_MAP = {
    'FDV PROPRIA':'FDVP','FDV-P':'FDVP',
    'FDV TERCEIRA':'FDVT','FDV-T':'FDVT',
    'CANAIS DIGITAIS':'DIGITAIS','LANDING':'DIGITAIS',
    'APP':'DIGITAIS','PAID':'DIGITAIS',
    'BIGSELLER FARMING':'ENGAGEMENT','ENGAGEMENT BIG SELLERS':'ENGAGEMENT',
    'ENGAGEMENT & VALUE PROP':'ENGAGEMENT',
    'TELESALES_FARMING':'TELESALES','TELEVENDAS':'TELESALES','TELESALES':'TELESALES',
    'HUNTING':'HUNTING','HUNTING LC':'HUNTING',
    'MGM':'MGM','MgM':'MGM',
    'RESELLERS':'RESELLERS',
    'CONSULTOR CERTIFICADO':'CONSULTOR',
    'PARTNERS INSTORE':'PARTNERS','PARTNERS ONLINE':'PARTNERS',
    'UNKNOWN':'OUTROS',
}
CART_MAP = {
    'ACQUISITION':'AQUISICAO','AQUISICAO':'AQUISICAO',
    'ENGAGEMENT':'ENGAJAMENTO','LEGADO':'ENGAJAMENTO',
}
BU_ACTUAL = {
    'OP - CHECKOUT':'OP','OP - LINK':'OP','OP - OTHERS':'OP',
    'POINT':'POINT','QR':'QR','QR FROM POINT':'QR','TAP':'QR',
}

def norm_canal(v):
    return CANAL_MAP.get(v.strip(), v.strip() or 'OUTROS')

def norm_cart(v):
    return CART_MAP.get(v.strip(), v.strip() or 'OUTROS')

def parse_num(s):
    s = str(s).strip()
    if not s: return 0.0
    try: return float(s.replace('.','').replace(',','.'))
    except: return 0.0

MONTHS = [f'{y}{m:02d}' for y in [2025,2026] for m in range(1,13)]
MIDX   = {m:i for i,m in enumerate(MONTHS)}

def zero24(): return [0.0]*24

BU_PLANO = {
    'OP - CHECKOUT':'OP','OP - LINK':'OP','OP - OTHERS':'OP',
    'POINT':'POINT','QR':'QR SELLERS','QR FROM POINT':'QR SELLERS','TAP':'QR SELLERS',
}

def new_scen(base_total, base_bu, base_seg):
    return {
        'total':         list(base_total),
        'by_bu':         {k:list(v) for k,v in base_bu.items()},
        'by_segment':    {k:list(v) for k,v in base_seg.items()},
        'by_product':    defaultdict(zero24),
        'by_mop':        defaultdict(zero24),
        'by_canal':      defaultdict(zero24),
        'by_carteira':   defaultdict(zero24),
        'by_bu_by_seg':  defaultdict(lambda: defaultdict(zero24)),
        'by_bu_by_mop':  defaultdict(lambda: defaultdict(zero24)),
        'by_seg_by_mop': defaultdict(lambda: defaultdict(zero24)),
    }

def add(scen, dims, idx, val):
    """dims = {'product':..., 'mop':..., 'canal':..., 'cart':..., 'bu':..., 'seg':...}"""
    if val == 0: return
    if dims.get('product'): scen['by_product'][dims['product']][idx] += val
    if dims.get('mop'):     scen['by_mop']    [dims['mop']]    [idx] += val
    if dims.get('canal'):   scen['by_canal']  [dims['canal']]  [idx] += val
    if dims.get('cart'):    scen['by_carteira'][dims['cart']]   [idx] += val
    bu, seg, mop = dims.get('bu',''), dims.get('seg',''), dims.get('mop','')
    if bu and seg:  scen['by_bu_by_seg'] [bu][seg][idx]  += val
    if bu and mop:  scen['by_bu_by_mop'] [bu][mop][idx]  += val
    if seg and mop: scen['by_seg_by_mop'][seg][mop][idx] += val

# ── Load base data ────────────────────────────────────────────────────────────
print("Loading base JSON...")
with open('tpv_data_processed.json') as f:
    base = json.load(f)

actual_s  = new_scen(base['actual']['total'],  base['actual']['by_bu'],  base['actual']['by_segment'])
f48_s     = new_scen(base['f48']['total'],     base['f48']['by_bu'],     base['f48']['by_segment'])
f39_s     = new_scen(base['f39']['total'],     base['f39']['by_bu'],     base['f39']['by_segment'])
plano_s   = new_scen(base['plano2026']['total'],base['plano2026']['by_bu'],base['plano2026']['by_segment'])

# ── Remove May 2026 actual (index 16, month 202605) ──────────────────────────
idx_may26 = MIDX['202605']
actual_s['total'][idx_may26] = 0
for v in actual_s['by_bu'].values():     v[idx_may26] = 0
for v in actual_s['by_segment'].values(): v[idx_may26] = 0

# ── 1. actual_raw.tsv → actual + f39 Jan-Mar + f48 Jan-Apr ──────────────────
# New format: wide/pivoted TSV — months are column headers (202.401 → 202401)
# Columns: PRODUTO_MACRO, CUST_SEGMENT_CROSS, CARTEIRA, PORTFOLIO_SELLER,
#          SUB_CANAL_AJUSTADO, SUB_CANAL, PRODUTO, METODO2, [month cols...]
print("Processing actual_raw.tsv (wide format)...")
NEW_MOP_MAP = {
    'BANK_TRANSFER':'BANK_TRANSFER','CREDIT_CARD':'CREDIT_CARD',
    'PARCELADO':'CREDIT_CARD',
    'DEBIT_CARD':'DEBIT_CARD','ACCOUNT_MONEY':'ACCOUNT_MONEY',
    'TICKET':'TICKET','DIGITAL_CURRENCY':'DIGITAL_CURRENCY',
    'PREPAID_CARD':'OUTROS','VOUCHER_CARD':'OUTROS','':'OUTROS',
}
# Month columns in TSV use dots as thousands sep (202.401 = 202401)
ACT_MON_COLS = [m for m in MONTHS if m <= '202604']  # 202501–202604 from this file
ACT_MON_MAP  = {f'{m[:3]}.{m[3:]}': m for m in ACT_MON_COLS}  # e.g. '202.501' → '202501'
# Also include 2024 months in case they appear (we won't add them to scenarios but must not crash)

with open('actual_raw.tsv', newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f, delimiter='\t'):
        prod  = PROD_ACTUAL.get(r['PRODUTO'].strip(), 'OUTROS')
        mop   = NEW_MOP_MAP.get(r['METODO2'].strip(), 'OUTROS')
        canal = norm_canal(r['SUB_CANAL_AJUSTADO'])
        cart  = norm_cart(r['CARTEIRA'])
        bu_ac = r['PRODUTO_MACRO'].strip() or BU_ACTUAL.get(r['PRODUTO'].strip(), '')
        seg   = r.get('CUST_SEGMENT_CROSS', '').strip()
        dims  = {'product':prod,'mop':mop,'canal':canal,'cart':cart,'bu':bu_ac,'seg':seg}
        for col, mes in ACT_MON_MAP.items():
            val = parse_num(r.get(col, ''))
            if not val: continue
            idx = MIDX[mes]
            add(actual_s, dims, idx, val)
            bu_fc = BU_PLANO.get(r['PRODUTO'].strip(), bu_ac)
            dims_fc = {**dims, 'bu': bu_fc}
            if mes in ('202601','202602','202603'):
                add(f39_s, dims_fc, idx, val)
            if mes in ('202601','202602','202603','202604'):
                add(f48_s, dims_fc, idx, val)

# ── 2+3+4+5. unified_scenarios_raw.tsv → f39 (Apr-Dec26), f48 (May-Dec26), plano (Jan-Dec26)
print("Processing unified_scenarios_raw.tsv...")

_U_BU   = {'ONLINE PAYMENTS':'OP','POINT':'POINT','QR':'QR SELLERS'}
_U_PROD = {'CHECKOUT':'CHECKOUT','LINK':'LINK','OTHERS':'OTHERS',
           'POINT':'POINT','QR SELLERS':'QR','TTP':'TTP','-':'OTHERS','':'OTHERS'}
_U_MOP  = {'account_money':'ACCOUNT_MONEY','bank_transfer':'BANK_TRANSFER',
           'credit_card':'CREDIT_CARD','debit_card':'DEBIT_CARD',
           'digital_currency':'DIGITAL_CURRENCY','ticket':'TICKET',
           'consumer_credits':'','others':'','prepaid_card':'OUTROS','voucher_card':'OUTROS'}
_U_CANAL = {'FDV-P':'FDVP','FDV-T':'FDVT','APP':'DIGITAIS','LANDING':'DIGITAIS',
            'MGM':'MGM','Others':'OUTROS','RESELLERS':'RESELLERS',
            'TELESALES':'TELESALES','TO':'CONSULTOR',
            'BIG SELLERS':'','BIGSELLER FARMING':'','-':'','':''}

def _u_cart(bs_port, port):
    bs = bs_port.strip(); po = port.strip()
    if bs and bs != '-':
        if bs == 'TTP': return 'TTP'
        if 'HUNT' in bs.upper(): return 'AQUISICAO'
        if bs.startswith('BS'): return 'ENGAJAMENTO'
    if po and po != '-':
        return 'AQUISICAO' if po == 'AQUISICAO' else 'ENGAJAMENTO'
    return ''

VER_MAP   = {'FORECAST 3+9':'f39','FORECAST 4+8':'f48','PLANO V5':'plano'}
VER_START = {'f39':'202604','f48':'202605','plano':'202601'}
VER_SCEN  = {'f39':f39_s,'f48':f48_s,'plano':plano_s}

# Zero out forecast months before rebuilding
for _i in range(15, 24):   # 202604-202612 for f39
    f39_s['total'][_i] = 0.0
    for _v in f39_s['by_bu'].values():      _v[_i] = 0.0
    for _v in f39_s['by_segment'].values(): _v[_i] = 0.0
for _i in range(16, 24):   # 202605-202612 for f48
    f48_s['total'][_i] = 0.0
    for _v in f48_s['by_bu'].values():      _v[_i] = 0.0
    for _v in f48_s['by_segment'].values(): _v[_i] = 0.0
for _i in range(12, 24):   # 202601-202612 for plano
    plano_s['total'][_i] = 0.0
    for _v in plano_s['by_bu'].values():      _v[_i] = 0.0
    for _v in plano_s['by_segment'].values(): _v[_i] = 0.0

with open('unified_scenarios_raw.tsv', newline='', encoding='utf-8') as f:
    reader = csv.reader(f, delimiter='\t')
    next(reader)  # skip "SUM de VALUE_AMOUNT" title row
    headers = next(reader)  # real column headers
    for row in reader:
        r = dict(zip(headers, row))
        ver_desc = r.get('VERSION_DESC','').strip()
        if ver_desc not in VER_MAP: continue  # skip ACTUAL and blank rows
        ver   = VER_MAP[ver_desc]
        scen  = VER_SCEN[ver]
        start = VER_START[ver]

        bu   = _U_BU.get(r.get('BU','').strip(), r.get('BU','').strip())
        seg  = r.get('SEGMENT_DESC','').strip()
        prod = _U_PROD.get(r.get('PRODUCT_DESC','').strip(), 'OTHERS')
        mop  = _U_MOP.get(r.get('PAYMENT_METHOD_DESC','').strip(), '')
        cart = _u_cart(r.get('BALANCE_SHEET_PORTFOLIO_DESC',''), r.get('PORTFOLIO_DESC',''))
        canal= _U_CANAL.get(r.get('CHANNEL_DESC','').strip(), '')

        dims = {'product':prod,'mop':mop,'canal':canal,'cart':cart,'bu':bu,'seg':seg}
        for mes in MONTHS:
            if mes < start: continue
            val = parse_num(r.get(mes,''))
            if not val: continue
            idx = MIDX[mes]
            scen['total'][idx] += val
            if bu:  scen['by_bu'].setdefault(bu,  zero24())[idx] += val
            if seg: scen['by_segment'].setdefault(seg, zero24())[idx] += val
            add(scen, dims, idx, val)

# ── Finalise (convert defaultdicts) ──────────────────────────────────────────
def finalise(s):
    for dim in ('by_product','by_mop','by_canal','by_carteira'):
        cleaned = {}
        for k,arr in s[dim].items():
            rounded = [round(v) for v in arr]
            if any(rounded): cleaned[k] = rounded
        s[dim] = cleaned
    s['total'] = [round(v) for v in s['total']]
    for sub in ('by_bu','by_segment'):
        s[sub] = {k:[round(x) for x in v] for k,v in s[sub].items()}
    for xdim in ('by_bu_by_seg','by_bu_by_mop','by_seg_by_mop'):
        outer = {}
        for k1, inner_d in s[xdim].items():
            inner = {}
            for k2, arr in inner_d.items():
                rounded = [round(v) for v in arr]
                if any(rounded): inner[k2] = rounded
            if inner: outer[k1] = inner
        s[xdim] = outer
    return s

for sc in (actual_s, f48_s, f39_s, plano_s):
    finalise(sc)

# ── Output ────────────────────────────────────────────────────────────────────
out = {
    'months': MONTHS,
    'labels': [f'{m[4:6]}/{m[2:4]}' for m in MONTHS],
    'scenarios': {
        'actual':    actual_s,
        'f48':       f48_s,
        'f39':       f39_s,
        'plano2026': plano_s,
    }
}

with open('tpv_enhanced.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False)

# ── Report ────────────────────────────────────────────────────────────────────
import os
size_kb = os.path.getsize('tpv_enhanced.json') // 1024
print(f"\nSaved tpv_enhanced.json ({size_kb} KB)")

for scen_name, sc in out['scenarios'].items():
    print(f"\n── {scen_name} ──")
    print(f"  Total Jan25: {sc['total'][0]:>15,.0f}  Dec26: {sc['total'][23]:>15,.0f}")
    print(f"  Products:  {sorted(sc['by_product'].keys())}")
    print(f"  MOPs:      {sorted(sc['by_mop'].keys())}")
    print(f"  Canais:    {sorted(sc['by_canal'].keys())}")
    print(f"  Carteiras: {sorted(sc['by_carteira'].keys())}")
