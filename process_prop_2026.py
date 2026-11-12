#!/usr/bin/env python3
"""Konfide Properties LLC + Konfide Aurora LLC — 2026 cash flow, kept separate for tax purposes.

Properties = Chase ...5899 + Properties Amex card ...51001. Aurora = Chase ...9012 (no card).
Rent belongs to whichever LLC's account it lands in (per Roy). Mortgage/HOA paid from ...5899 but billed
to KONFIDE AURORA LLC (Selene, Hometown Condominium) are moved to Aurora (per Roy 11/11).
Transfers between the accounts are skipped on both sides, so Combined = Properties + Aurora with no double count.

Bank rules are reused from process_prop.py (process_5899) so 2025 and 2026 categorize identically;
2026-only additions are applied here. Amex rules extend process_prop_amex.py's 2025 rules.
Output: konfide_prop_cf_2026.csv, konfide_aurora_cf_2026.csv (Label, Jan 2026 … Dec 2026), konfide_prop_amex_2026_line_items.csv.
"""
import csv, os
from collections import defaultdict

here = os.path.dirname(os.path.abspath(__file__))
os.chdir(here)
YEAR = 2026
BANK_FILES = ['Chase5899_Activity_20261111.csv']                 # Konfide Properties LLC
AURORA_FILES = ['Chase9012_Activity_20260623.CSV', 'Chase9012_Activity_20261111.csv']               # Konfide Aurora LLC (opened 4/30/2026)
AMEX_FILE = 'activity:kprop.csv'
MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
LINES = ['Rental Income','Mortgage','Insurance','HOA','Utilities','Repair & Maintenance',
         'Professional Fees','Travel','Office Expenses']
cf = {l: [0.0]*12 for l in LINES}
au = {l: [0.0]*12 for l in LINES}   # Konfide Aurora LLC
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

# Aurora-billed mortgage/HOA paid from ...5899 → move from Properties to Aurora
moved = 0.0
for fname in BANK_FILES:
    for r in csv.DictReader(open(fname, newline='', encoding='utf-8-sig')):
        d = r['Description'].upper()
        if not r['Posting Date'].endswith(str(YEAR)) or 'IND NAME:KONFIDE AURORA' not in d: continue
        a = abs(float(r['Amount'])); mi = int(r['Posting Date'][:2]) - 1
        if 'SELENE FINANCE' in d:     lbl = 'Mortgage'
        elif 'HOMETOWN CONDOMI' in d: lbl = 'HOA'
        else: flags.append(f"BANK Aurora-billed, not moved: {r['Posting Date']} {a:.2f} {d[:60]}"); continue
        cf[lbl][mi] -= a; au[lbl][mi] += a; moved += a

# ── KONFIDE AURORA LLC — Chase ...9012 ──────────────────────────────────────
seen = set(); moved_back = 0.0
for fname in AURORA_FILES:
    fk = set()
    for r in csv.DictReader(open(fname, newline='', encoding='utf-8-sig')):
        key = (r['Posting Date'], r['Description'], r['Amount'], r['Type'], r['Balance'])
        if key in seen: continue
        fk.add(key)
        if not r['Posting Date'].endswith(str(YEAR)): continue
        d = r['Description'].upper(); a = float(r['Amount']); tp = r['Type'].strip(); mi = int(r['Posting Date'][:2]) - 1
        if tp == 'ACCT_XFER': continue                          # between own accounts
        # Bills billed to KONFIDE PROPERTIES LLC but paid from ...9012 → Properties (mirror of the move above)
        if a < 0 and 'IND NAME:KONFIDE PROPERTIES' in d and ('SELENE FINANCE' in d or 'HOMETOWN CONDOMI' in d):
            cf['Mortgage' if 'SELENE' in d else 'HOA'][mi] += -a; moved_back += -a; continue
        if tp == 'WIRE_OUTGOING' or 'WIRE TRANSFER' in d: continue   # property purchase (title company)
        if 'BRC' in d and a > 0: continue                       # line-of-credit draw
        if a > 0:
            if any(k in d for k in ('HOUSING A', 'DOORLOOP', 'DOOR LOOP')) or tp in ('DEPOSIT','CHECK_DEPOSIT','ATM') \
               or ('ZELLE PAYMENT FROM' in d and a < 5000):
                au['Rental Income'][mi] += a
            else: flags.append(f"AURORA CREDIT {r['Posting Date']} {a:,.2f} {d[:60]}")
            continue
        a = -a
        if any(k in d for k in ('DEE PAINTER','LUIS ALEXANDER','MIGUEL','JOSE DIAZ','FOUR SEASON','HOME DEPOT','MENARDS')):
            au['Repair & Maintenance'][mi] += a
        elif 'SELENE FINANCE' in d or 'ORIG ID:9301144000' in d: au['Mortgage'][mi] += a   # 9301144000 = mortgage servicer (same rule as ...5899)
        elif 'ACCT INTEGRATORS' in d:                   au['HOA'][mi] += a                  # HOA payment-portal fee (same as ...5899)
        elif 'GARAGE DOORS REPAIRING' in d:             au['Repair & Maintenance'][mi] += a
        elif 'COUNTER CHECK' in d:                      au['Office Expenses'][mi] += a
        elif 'HOMETOWN CONDOMI' in d:                   au['HOA'][mi] += a
        elif 'COMED' in d or 'NICOR' in d:              au['Utilities'][mi] += a
        elif 'WIRE FEE' in d:                           au['Office Expenses'][mi] += a
        elif tp == 'MISC_DEBIT' and 'WITHDRAWAL' in d:  pass   # cash withdrawal — skipped per Roy (2025 rule)
        else: flags.append(f"AURORA DEBIT {r['Posting Date']} {a:,.2f} {d[:60]}")
    seen |= fk

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
def show(title, book):
    print(f"\n{title}\n{'':22}" + ''.join(f'{m:>8}' for m in MONTHS[:last]) + f"{'YTD':>11}")
    ti = te = 0
    for l in LINES:
        v = book[l][:last]; s_ = sum(v)
        if not any(round(x, 2) for x in v): continue
        print(f'{l:22}' + ''.join(f'{x:>8,.0f}' for x in v) + f'{s_:>11,.2f}')
        if l == 'Rental Income': ti += s_
        else: te += s_
    print(f"{'NET CASH FLOW':22}{'':{8*last}}{ti-te:>11,.2f}")
show('KONFIDE PROPERTIES LLC — 2026', cf)
show('KONFIDE AURORA LLC — 2026', au)
show('COMBINED — 2026', {l: [x + y for x, y in zip(cf[l], au[l])] for l in LINES})
print(f'\n(moved ${moved:,.2f} of Aurora-billed mortgage/HOA from Properties to Aurora; '
      f'${moved_back:,.2f} of Properties-billed paid from ...9012 to Properties)')
if flags:
    print('\nNEEDS ROY:'); [print(' ', f) for f in flags]

for fname, book in (('konfide_prop_cf_2026.csv', cf), ('konfide_aurora_cf_2026.csv', au)):
    with open(fname, 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['Label'] + [f'{m} {YEAR}' for m in MONTHS])
        for l in LINES: w.writerow([l] + [f'{x:.2f}' for x in book[l]])
with open('konfide_prop_amex_2026_line_items.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['Date','Description','Amount','Category']); w.writerows(audit)
print('\n✓ wrote konfide_prop_cf_2026.csv, konfide_aurora_cf_2026.csv')
