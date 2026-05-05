"""
Builds tpv_enhanced.json with full dimension breakdowns:
  actual   → Jan-Apr 2026 (actual_raw.tsv)
  f48      → May-Dec 2026 forecast (tpv_combinado.tsv FORECAST 4+8)
             Jan-Apr 2026 actuals reused from actual_raw.tsv
  f39      → Apr-Dec 2026 forecast (forecast_39_raw.tsv)
             Jan-Mar 2026 actuals reused from actual_raw.tsv
  plano    → Jan-Dec 2026 product/canal/carteira (plano_raw.tsv)
             MOP from plano_mop_raw.tsv
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
print("Processing actual_raw.tsv...")
actual_detail = defaultdict(lambda: defaultdict(float))  # (product,mop,canal,cart) → {month: val}

with open('actual_raw.tsv', newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f, delimiter='\t'):
        mes = r['TIM_MONTH'].strip()
        if mes not in MIDX: continue
        idx = MIDX[mes]
        val = parse_num(r['SUM de TPV'])
        prod  = PROD_ACTUAL.get(r['PRODUTO'].strip(), 'OUTROS')
        mop   = r['METODO_PAGAMENTO'].strip() or 'OUTROS'
        canal = norm_canal(r['CANAL_AJUSTADO'])
        cart  = norm_cart(r['CARTEIRA'])
        bu_ac = BU_ACTUAL.get(r['PRODUTO'].strip(), '')
        seg   = r.get('CUST_SEGMENT_CROSS', '').strip()
        dims  = {'product':prod,'mop':mop,'canal':canal,'cart':cart,'bu':bu_ac,'seg':seg}
        # actual
        add(actual_s, dims, idx, val)
        # f39 gets Jan-Mar 2026 from actual (use QR SELLERS key for consistency)
        bu_fc = BU_PLANO.get(r['PRODUTO'].strip(), bu_ac)
        dims_fc = {**dims, 'bu': bu_fc}
        if mes in ('202601','202602','202603'):
            add(f39_s, dims_fc, idx, val)
        # f48 gets Jan-Apr 2026 from actual
        if mes in ('202601','202602','202603','202604'):
            add(f48_s, dims_fc, idx, val)

# ── 2. forecast_39_raw.tsv → f39 Apr-Dec 2026 ───────────────────────────────
print("Processing forecast_39_raw.tsv...")
with open('forecast_39_raw.tsv', newline='', encoding='utf-8') as f:
    rows = list(csv.DictReader(f, delimiter='\t'))

if rows:
    mon_cols = [k for k in rows[0].keys() if k.isdigit() and len(k)==6]
    for r in rows:
        prod  = PROD_FC.get(r['Produto'].strip(), 'OUTROS')
        mop   = r['MOP'].strip() or 'OUTROS'
        canal = norm_canal(r['CANAL'])
        cart  = norm_cart(r['CARTEIRA'])
        bu    = r.get('BU','').strip()
        seg   = r.get('SEGMENTO','').strip()
        dims  = {'product':prod,'mop':mop,'canal':canal,'cart':cart,'bu':bu,'seg':seg}
        for mc in mon_cols:
            if mc not in MIDX: continue
            val = parse_num(r[mc])
            add(f39_s, dims, MIDX[mc], val)

# ── 3. tpv_combinado.tsv → f48 May-Dec 2026 (FORECAST 4+8 rows) ─────────────
print("Processing tpv_combinado.tsv (FORECAST 4+8)...")
with open('tpv_combinado.tsv', newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f, delimiter='\t'):
        if r['CENARIO'].strip() != 'FORECAST 4+8': continue
        mes = r['MES'].strip()
        if mes not in MIDX or mes < '202605': continue  # only May-Dec 2026 (Apr covered by actual)
        val = parse_num(r['VALOR'])
        prod  = PROD_FC.get(r['PRODUTO'].strip(), r['PRODUTO'].strip() or 'OUTROS')
        mop   = r['MOP'].strip() or 'OUTROS'
        canal = norm_canal(r['CANAL'])
        cart  = norm_cart(r['CARTEIRA'])
        bu    = r.get('BU','').strip()
        seg   = r.get('SEGMENTO','').strip()
        dims  = {'product':prod,'mop':mop,'canal':canal,'cart':cart,'bu':bu,'seg':seg}
        add(f48_s, dims, MIDX[mes], val)

# ── 4. plano_raw.tsv → plano product/canal/carteira ─────────────────────────
print("Processing plano_raw.tsv...")
with open('plano_raw.tsv', newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f, delimiter='\t'):
        mes = r['MES'].strip()
        if mes not in MIDX: continue
        val  = parse_num(r['TPV_PLANO'])
        prod = PROD_ACTUAL.get(r['PRODUTO'].strip(), r['PRODUTO'].strip() or 'OUTROS')
        canal = norm_canal(r['CANAL'])
        cart  = norm_cart(r['CARTEIRA'])
        bu    = BU_PLANO.get(r['PRODUTO'].strip(), '')
        seg   = r.get('SEGMENTO','').strip()
        dims  = {'product':prod,'canal':canal,'cart':cart,'bu':bu,'seg':seg}
        add(plano_s, dims, MIDX[mes], val)

# ── 5. plano_mop_raw.tsv → plano MOP (2026 only) ────────────────────────────
print("Processing plano_mop_raw.tsv...")
with open('plano_mop_raw.tsv', newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f, delimiter='\t'):
        mes = r['MES'].strip()
        if mes not in MIDX or mes < '202601': continue
        val = parse_num(r['SUM de TPV'])
        mop = r['MOP'].strip() or 'OUTROS'
        if mop == 'PIX': mop = 'BANK_TRANSFER'
        bu  = BU_PLANO.get(r.get('PRODUTO','').strip(), '')
        if val:
            plano_s['by_mop'][mop][MIDX[mes]] += val
            if bu: plano_s['by_bu_by_mop'][bu][mop][MIDX[mes]] += val

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
