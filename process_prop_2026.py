#!/usr/bin/env python3
"""Konfide Properties LLC — 2026 cash flow (Chase ...5899 + Properties Amex card ...51001).

Bank rules are reused from process_prop.py (process_5899) so 2025 and 2026 categorize identically;
2026-only additions are applied here. Amex rules extend process_prop_amex.py's 2025 rules.
Output: konfide_prop_cf_2026.csv (Label, Jan 2026 … Dec 2026) and konfide_prop_amex_2026_line_items.csv.
"""
import csv, os
from collections import defaultdict

here = os.path.dirname(os.path.abspath(__file__))
os.chdir(here)
YEAR = 2026
BANK_FILES = ['Chase5899_Activity_20261111.csv']
AMEX_FILE = 'activity:kprop.csv'
MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
LINES = ['Rental Income','Mortgage','Insurance','HOA','Utilities','Repair & Maintenance',
         'Professional Fees','Travel','Office Expenses']
cf = {l: [0.0]*12 for l in LINES}
flags = []

# ── BANK: reuse process_prop.process_5899 (source above its MAIN block) ─────
g = {}
exec(open('process_prop.py').read().split('# ─── MAIN')[0], g)
pm = g['MONTHS']
for fname in BANK_FILES:
    inc, mort, hoa, util, rep, off, trav, skip, unk = g['process_5899'](fname)
    for lbl, d in [('Rental Income',inc),('Mortgage',mort),('HOA',hoa),('Utilities',util),
                   ('Repair & Maintenance',rep),('Office Expenses',off),('Travel',trav)]:
        for (y, m), v in d.items():
            if y == YEAR: cf[lbl][pm.index(m)] += v
    # 2026-only bank items that process_5899 leaves as unknown
    for u in unk:
        parts = u.split()
        date, amt = parts[2], float(parts[3])
        mi = int(date[:2]) - 1
        U = u.upper()
        if 'LUIS ALEXANDER DEE PAINTER' in U:  cf['Repair & Maintenance'][mi] += amt
        elif 'GREATWAYS' in U:                 cf['Office Expenses'][mi] += amt      # same tax preparer as GREATWAY TAX
        elif 'ZELLE PAYMENT TO ADNAN' in U:    cf['Repair & Maintenance'][mi] += amt  # repair, per Roy
        elif 'LANDTRUST' in U and 'FEDWIRE CREDIT' in U: pass   # 6/18 cash-out refinance of a cash-bought property, per Roy — financing, not income
        else: flags.append('BANK ' + u)

# ── AMEX ────────────────────────────────────────────────────────────────────
RULES = [
    ('PAYMENT - THANK YOU',      None),      # card payment from ...5899 (skipped there as AMERICAN EXPRESS)
    ('RETURNED AUTOPAY',         None),      # bounced payment, nets against its payment
    ('ADJ REDIST',               None),      # Amex internal balance reshuffle, pair nets to 0
    ('COMMONWEALTH EDISON',      'Utilities'),
    ('PROPAY RESIDENTIAL',       'Repair & Maintenance'),
    ('HOME DEPOT',               'Repair & Maintenance'),
    ('SHERWIN-WILLIAMS',         'Repair & Maintenance'),
    ('AIR DYNAMICS HEATING',     'Repair & Maintenance'),
    ('SUMMERS OF YORKVILLE',     'Repair & Maintenance'),
    ('MENARDS',                  'Repair & Maintenance'),
    ('HEARTH',                   'Repair & Maintenance'),   # AC unit repair (incl. 7/21 refund), per Roy
    ('FOREMOST INSURANCE',       'Insurance'),
    ('TAMARISK APPRAISAL',       'Professional Fees'),
    ('APPRAISALFEE',             'Professional Fees'),
    ('COST SEG SMART',           'Professional Fees'),
    ('MEMBERSHIP FEE',           None),
    ('ADOBE',                    'Office Expenses'),
    ('FEDEX OFFICE',             'Office Expenses'),
    ('ILLINOIS SECRETARY',       'Office Expenses'),
    ('INTEREST CHARGE',          None),      # Amex interest / late / annual fee — skipped, per Roy 11/11
    ('LATE FEE',                 None),
    ('QATARAIR',                 'Travel'),             # business travel, per Roy
    ('CHEAPTIX',                 'Travel'),
    ('PARKING',                  'Travel'),
    ('KATOM',                    None),      # Smart Beginnings purchases on this card — ignored, per Roy
    ('FAST SIGNS',               None),
    ('LP CUSTOM',                None),
    ('ORKIN',                    None),
    ('WHITE CHOCOLATE',          'Office Expenses'),    # per Roy
    ('BEST BUY',                 'Office Expenses'),
    ('CANDY CLOUD',              'Office Expenses'),
    ('ARTISAN HAIR',             'Office Expenses'),
    ('DELTA SONIC',              'Office Expenses'),
    ('DUNKIN',                   'Office Expenses'),
]
audit = []
for r in csv.DictReader(open(AMEX_FILE, newline='', encoding='utf-8-sig')):
    if not r['Date'].endswith(str(YEAR)): continue
    d = ' '.join(r['Description'].split()).upper(); a = float(r['Amount']); mi = int(r['Date'][:2]) - 1
    cat = 'FLAG'
    for k, c in RULES:
        if k in d: cat = c; break
    audit.append((r['Date'], ' '.join(r['Description'].split()), a, cat or '(excluded)'))
    if cat is None: continue
    if cat == 'FLAG': flags.append(f'AMEX {r["Date"]} {a:>9,.2f}  {" ".join(r["Description"].split())[:50]}'); continue
    cf[cat][mi] += a

# ── REPORT + WRITE ──────────────────────────────────────────────────────────
last = 10   # data through Oct
print(f"{'':22}" + ''.join(f'{m:>8}' for m in MONTHS[:last]) + f"{'YTD':>11}")
ti = te = 0
for l in LINES:
    v = cf[l][:last]; s = sum(v)
    print(f'{l:22}' + ''.join(f'{x:>8,.0f}' for x in v) + f'{s:>11,.2f}')
    if l == 'Rental Income': ti += s
    else: te += s
print(f"{'NET CASH FLOW':22}{'':{8*last}}{ti-te:>11,.2f}")
if flags:
    print('\nNEEDS ROY:'); [print(' ', f) for f in flags]

with open('konfide_prop_cf_2026.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['Label'] + [f'{m} {YEAR}' for m in MONTHS])
    for l in LINES: w.writerow([l] + [f'{x:.2f}' for x in cf[l]])
with open('konfide_prop_amex_2026_line_items.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['Date','Description','Amount','Category']); w.writerows(audit)
print('\n✓ wrote konfide_prop_cf_2026.csv')
