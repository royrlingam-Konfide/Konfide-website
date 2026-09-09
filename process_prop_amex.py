#!/usr/bin/env python3
"""Merge the Konfide Properties Amex (card ...51001, opened Oct 2025) into the
Konfide Properties LLC 2025 cash flow.

Inputs:
  konfide_prop_cf_2025.csv   — bank-derived cash flow (Chase ...5899), 6 rows
  activity.csv               — Properties Amex export, Oct–Dec 2025, 18 rows

Amex categorization (confirmed with Roy):
  Commonwealth Edison ............... Utilities
  ProPay Residential ............... Repair & Maintenance
  Menards / Floor & Decor / Cintas /
    HCM Doors Systems ............... Repair & Maintenance
  Foremost Insurance .............. Insurance            (NEW line)
  Tamarisk Appraisals ............ Professional Fees     (NEW line)
  Amex Membership Fee ............ Office Expenses
  AUTOPAY PAYMENT - THANK YOU .... exclude (paid from Chase ...5899, skipped there)
  merchant refunds (negatives) ... net against their category

Output: konfide_prop_cf_2025.csv is REWRITTEN with the Amex folded in (+2 rows),
        plus konfide_prop_amex_2025_line_items.csv for the audit trail.
"""

import csv
import os

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
HDR = [f'{m} 2025' for m in MONTHS]

CF = 'konfide_prop_cf_2025.csv'
AMEX = 'activity.csv'
AUDIT = 'konfide_prop_amex_2025_line_items.csv'

RULES = [
    ('AUTOPAY PAYMENT - THANK YOU', '(exclude) Card payment'),
    ('PAYMENT - THANK YOU',         '(exclude) Card payment'),
    ('COMMONWEALTH EDISON',         'Utilities'),
    ('PROPAY RESIDENTIAL',          'Repair & Maintenance'),
    ('MENARDS',                     'Repair & Maintenance'),
    ('FLOOR & DECOR',               'Repair & Maintenance'),
    ('CINTAS',                      'Repair & Maintenance'),
    ('HCM=DOORS',                   'Repair & Maintenance'),
    ('DOORS SYSTEMS',               'Repair & Maintenance'),
    ('FOREMOST INSURANCE',          'Insurance'),
    ('TAMARISK APPRAISAL',          'Professional Fees'),
    ('MEMBERSHIP FEE',              'Office Expenses'),
]


def classify(desc):
    u = ' '.join(desc.split()).upper()
    for key, cat in RULES:
        if key in u:
            return cat
    return 'UNCATEGORIZED — review'


def mo_idx(date_str):
    return int(date_str.split('/')[0]) - 1


here = os.path.dirname(os.path.abspath(__file__))

# ── read the bank cash flow ────────────────────────────────────────────────
with open(os.path.join(here, CF), newline='') as f:
    rows = list(csv.reader(f))
bank = {r[0]: [float(x) for x in r[1:]] for r in rows[1:]}

# ── classify the Amex ─────────────────────────────────────────────────────
amex = {}            # category -> 12 monthly floats
audit = []
excluded = 0.0
with open(os.path.join(here, AMEX), newline='', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        amt = float(r['Amount'])
        cat = classify(r['Description'])
        audit.append((r['Date'], r['Card Member'], ' '.join(r['Description'].split()), amt, cat))
        if cat.startswith('(exclude)'):
            excluded += amt
            continue
        amex.setdefault(cat, [0.0] * 12)[mo_idx(r['Date'])] += amt

unc = [a for a in audit if a[4].startswith('UNCATEG')]
if unc:
    print('*** UNCATEGORIZED Amex rows — fix RULES before trusting output ***')
    for row in unc:
        print('   ', row)
    raise SystemExit(1)

# ── merge ─────────────────────────────────────────────────────────────────
LINE_ORDER = ['Rental Income', 'Mortgage', 'Insurance', 'HOA', 'Utilities',
              'Repair & Maintenance', 'Professional Fees', 'Office Expenses']
merged = {}
for lbl in LINE_ORDER:
    b = bank.get(lbl, [0.0] * 12)
    a = amex.get(lbl, [0.0] * 12)
    merged[lbl] = [round(x + y, 2) for x, y in zip(b, a)]

# ── report ───────────────────────────────────────────────────────────────
def show(title, d):
    print(f'\n{title}')
    print(f"  {'':24}" + ''.join(f'{m:>8}' for m in MONTHS) + f'{"Year":>12}')
    inc = exp = 0.0
    for lbl in LINE_ORDER:
        v = d[lbl]
        if not any(round(x, 2) for x in v):
            continue
        yr = sum(v)
        print(f'  {lbl:<24}' + ''.join(f'{x:>8,.0f}' for x in v) + f'{yr:>12,.2f}')
        if lbl == 'Rental Income':
            inc += yr
        else:
            exp += yr
    print(f'  {"— income":<24}{"":96}{inc:>12,.2f}')
    print(f'  {"— expenses":<24}{"":96}{exp:>12,.2f}')
    print(f'  {"— net cash flow":<24}{"":96}{inc-exp:>12,.2f}')

show('KONFIDE PROPERTIES LLC — 2025 cash flow  (bank + Amex merged)', merged)

amex_total = sum(sum(v) for v in amex.values())
print(f'\n  Amex folded in: ${amex_total:,.2f} of charges across '
      f'{sum(1 for a in audit if not a[4].startswith("(exclude)"))} transactions; '
      f'${excluded:,.2f} of payments excluded.')

# ── write ────────────────────────────────────────────────────────────────
with open(os.path.join(here, CF), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Label'] + HDR)
    for lbl in LINE_ORDER:
        w.writerow([lbl] + [f'{x:.2f}' for x in merged[lbl]])
print(f'\n✓ rewrote {CF}  ({len(LINE_ORDER)} rows)')

with open(os.path.join(here, AUDIT), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Date', 'Card Member', 'Description', 'Amount', 'Category'])
    for row in audit:
        w.writerow(row)
print(f'✓ wrote {AUDIT}  ({len(audit)} rows)')
