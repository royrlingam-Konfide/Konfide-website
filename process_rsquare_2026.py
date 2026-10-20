#!/usr/bin/env python3
"""R Square Education Inc. — 2026 P&L from Chase9019 (single operating account).
(October is partial — statement pulled 10/20/2026, covers through 10/09.)

Categorization rules confirmed with Roy:
  INCOME  -> single "Service Income" line: TSYS/TRANSFIRST card settlements + PAYMENTECH fin adj.
             Skip Zelle from Aleksandar Balan, Zelle from Thiyagarajah Magaswaran, BRC ...7001 draw.
  RENT                       -> "Online ACH Payment To KVRSquare (...3048)"
  Advertising & marketing    -> Zelle to Kerianne Cummings USMLE
  Repairs & maintenance      -> Zelle to Jose Diaz
  Merchant account fees      -> TSYS/TRANSFIRST debits, FATTMERCHANT, PAYMENTECH monthly
  Software & apps            -> Zoom, Elfsight/Paddle, Intuit, Google Workspace, OpenPhone
  Course materials           -> UWORLD
  Electricity                -> ComEd
  Heating & Cooling          -> Nicor Gas
  Internet & TV services     -> Comcast/Xfinity
  Bank fees & service charges -> monthly service charges, net of FEE REVERSAL (+$102)
  Legal & professional fees  -> GRTWAYS / GREATWAYS1445 tax service
  Taxes paid                 -> IL Dept of Revenue, IRS
  SBA EIDL loan              -> "SBA LOAN" + "SBA EIDL LOAN"
  Konfide Education Group    -> transfer out to CHK ...7651
  Konfide Management Fee     -> transfer out to CHK ...3252
  Owner withdrawal           -> transfer out to CHK ...8271
  SKIP: Sonny, Mark, Moriah, Justin, Mike Electrical, Cindy Magas, Khrystal;
        Chase card ...5667 payment; $1,000 cash withdrawal; every other transfer
        (in or out); all inbound transfers.
"""

import csv
import os
from collections import defaultdict

SRC = 'Chase9019_Activity_20261020.csv'
OUT = 'rsquare_pl_2026.csv'
SKIP_LOG = 'rsquare_2026_skipped_transactions.csv'

ALL_MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
MO = {f'{i:02d}': n for i, n in enumerate([''] + ALL_MONTHS, 0)}

pl = {m: defaultdict(float) for m in ALL_MONTHS}
skipped = []   # (month, date, amount, type, description, reason)
unknown = []   # rows no rule matched — must be resolved before trusting output

INCOME_CATS = ['Service Income']
EXPENSE_CATS = [
    'Rent',
    'Advertising & marketing',
    'Merchant account fees',
    'Software & apps',
    'Course materials',
    'Repairs & maintenance',
    'Electricity',
    'Heating & Cooling',
    'Internet & TV services',
    'Bank fees & service charges',
    'Legal & professional fees',
    'Taxes paid',
    'SBA EIDL loan',
    'Konfide Education Group',
    'Konfide Management Fee',
    'Owner withdrawal',
    'Supplies',
]
# Split used only by the dashboard's COGS vs Operating-Expenses model.
COGS_CATS = {'Merchant account fees', 'Course materials'}


def mo(date_str):
    return MO.get(date_str.strip()[:2])


def add(m, cat, amount):
    pl[m][cat] += abs(amount)


def skip(m, row, reason):
    skipped.append((m, row['Posting Date'], float(row['Amount']),
                    row['Type'].strip(), ' '.join(row['Description'].split())[:90], reason))


def categorize(row, m):
    d = row['Description'].upper()
    a = float(row['Amount'])
    tp = row['Type'].strip()

    # ── INBOUND MONEY ────────────────────────────────────────────────────────
    if a > 0:
        if 'TSYS/TRANSFIRST' in d:
            add(m, 'Service Income', a); return
        if 'PAYMENTECH' in d:
            add(m, 'Service Income', a); return          # FIN ADJ settlement top-up
        if 'FEE REVERSAL' in d:
            pl[m]['Bank fees & service charges'] -= abs(a); return   # offsets a service charge
        if 'ZELLE PAYMENT FROM ALEKSANDAR' in d:
            skip(m, row, 'per Roy: skip Aleksandar Balan deposit'); return
        if 'MAGASWARAN' in d:
            skip(m, row, 'per Roy: skip Magaswaran deposit'); return
        if 'FROM BRC' in d or 'BRC ...7001' in d:
            skip(m, row, 'line-of-credit draw (financing, not income)'); return
        if 'WEBBANK/INTUIT' in d:
            skip(m, row, 'QB Capital loan draw (financing, not income)'); return
        if 'ACCTVERIFY' in d or 'REAL TIME TRANSFER' in d:
            skip(m, row, 'bank-verification micro-transaction, nets to $0'); return
        if tp == 'ACCT_XFER':
            skip(m, row, 'inbound transfer (inter-company funding)'); return
        unknown.append((m, row['Posting Date'], a, tp, d[:90])); return

    # ── OUTBOUND MONEY ───────────────────────────────────────────────────────
    # Transfers first (need exact destination account).
    if tp == 'ACCT_XFER':
        if 'TO CHK ...7651' in d:
            add(m, 'Konfide Education Group', a); return
        if 'TO CHK ...3252' in d:
            add(m, 'Konfide Management Fee', a); return
        if 'TO CHK ...8271' in d:
            add(m, 'Owner withdrawal', a); return
        skip(m, row, 'transfer out to non-designated account'); return

    # Rent
    if 'KVRSQUARE' in d:
        add(m, 'Rent', a); return

    # Zelle out to individuals
    if 'ZELLE PAYMENT TO' in d:
        dz = ' '.join(d.split())   # collapse the double spaces Chase pads names with
        if 'KERIANNE CUMMINGS' in dz:
            add(m, 'Advertising & marketing', a); return
        if 'JOSE DIAZ' in dz:
            add(m, 'Repairs & maintenance', a); return
        if 'LORI TUTOR' in dz:
            add(m, 'Supplies', a); return   # per Roy
        if 'STROKE SAND SIGN' in dz:
            add(m, 'Advertising & marketing', a); return   # per Roy
        if any(n in dz for n in ('TO SONNY', 'TO MARK', 'TO MORIAH', 'TO JUSTIN',
                                 'MIKE ELECTRICAL', 'CINDY MAGAS', 'TO KHRYSTAL')):
            skip(m, row, 'per Roy: skip this Zelle recipient'); return
        unknown.append((m, row['Posting Date'], a, tp, d[:90])); return

    # Merchant / processing fees
    if 'TSYS/TRANSFIRST' in d or 'FATTMERCHANT' in d or 'PAYMENTECH' in d or 'STAX PAYMENTS' in d:
        add(m, 'Merchant account fees', a); return

    # Software & subscriptions
    if ('ZOOM.COM' in d or 'ZOOM.US' in d or 'ELFSIGHT' in d or 'PADDLE.NET' in d
            or 'INTUIT' in d or 'GSUITE' in d or 'GOOGLE *GSUITE' in d
            or 'GSUITE_DELPHIUS' in d or 'OPENPHONE' in d or 'WIX.COM' in d):
        add(m, 'Software & apps', a); return

    # Course materials
    if 'UWORLD' in d:
        add(m, 'Course materials', a); return

    # Supplies (Amazon)
    if 'AMAZON' in d:
        add(m, 'Supplies', a); return

    # Utilities
    if 'COMED' in d:
        add(m, 'Electricity', a); return
    if 'NICOR GAS' in d:
        add(m, 'Heating & Cooling', a); return
    if 'COMCAST' in d or 'XFINITY' in d:
        add(m, 'Internet & TV services', a); return

    # Bank fees
    if 'SERVICE CHARGES FOR THE MONTH' in d:
        add(m, 'Bank fees & service charges', a); return
    if 'ACCOUNT ANALYSIS SETTLEMENT CHARGE' in d:
        add(m, 'Bank fees & service charges', a); return

    # Tax prep / professional
    if 'GRTWAYS' in d or 'GREATWAYS' in d:
        add(m, 'Legal & professional fees', a); return

    # Tax payments
    if 'IL DEPT OF REVEN' in d or 'ILLINOIS DEPT' in d or 'ORIG CO NAME:IRS' in d:
        add(m, 'Taxes paid', a); return

    # SBA loan
    if 'SBA LOAN' in d or 'SBA EIDL LOAN' in d:
        add(m, 'SBA EIDL loan', a); return

    # Explicit skips
    if 'PAYMENT TO CHASE CARD' in d:
        skip(m, row, 'per Roy: credit-card payment, no purchase detail'); return
    if d.strip().startswith('WITHDRAWAL') or 'WITHDRAWAL 03/10' in d:
        skip(m, row, 'per Roy: cash withdrawal'); return

    unknown.append((m, row['Posting Date'], a, tp, d[:90]))


# ── READ ────────────────────────────────────────────────────────────────────
here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, SRC), newline='', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        m = mo(row['Posting Date'])
        if not m:
            continue
        categorize(row, m)


# ── REPORT ──────────────────────────────────────────────────────────────────
def print_block(title, cats):
    print(f'\n{title}')
    print(f"  {'':30}" + ''.join(f'{m:>9}' for m in ALL_MONTHS) + f'{"Year":>12}')
    print('  ' + '-' * (30 + 9 * 12 + 12))
    totals = [0.0] * 12
    for c in cats:
        vals = [pl[m].get(c, 0.0) for m in ALL_MONTHS]
        if not any(round(v, 2) for v in vals):
            continue
        print(f'  {c:<30}' + ''.join(f'{v:>9,.0f}' for v in vals) + f'{sum(vals):>12,.0f}')
        totals = [t + v for t, v in zip(totals, vals)]
    print(f"  {'TOTAL '+title:<30}" + ''.join(f'{v:>9,.0f}' for v in totals) + f'{sum(totals):>12,.0f}')
    return totals

print('=' * 132)
print('  R SQUARE EDUCATION INC. — 2026 P&L  (source: %s)' % SRC)
print('=' * 132)
inc = print_block('INCOME', INCOME_CATS)
exp = print_block('EXPENSES', EXPENSE_CATS)
net = [i - e for i, e in zip(inc, exp)]
print(f"\n  {'NET':<30}" + ''.join(f'{v:>9,.0f}' for v in net) + f'{sum(net):>12,.0f}')

cogs_year = sum(pl[m].get(c, 0.0) for m in ALL_MONTHS for c in COGS_CATS)
opex_year = sum(exp) - cogs_year
print(f'\n  Dashboard split:  Revenue {sum(inc):,.0f}   COGS {cogs_year:,.0f}   '
      f'OpEx {opex_year:,.0f}   Net {sum(inc)-cogs_year-opex_year:,.0f}')

if skipped:
    print(f'\n  SKIPPED: {len(skipped)} transactions, '
          f'${sum(abs(s[2]) for s in skipped):,.0f} total (see {SKIP_LOG})')
if unknown:
    print('\n  *** UNCATEGORIZED — RESOLVE BEFORE TRUSTING OUTPUT ***')
    for m, dt, a, tp, d in unknown:
        print(f'    {dt}  {a:>11,.2f}  [{tp}]  {d}')
else:
    print('\n  ✓ every transaction categorized or explicitly skipped')


# ── WRITE P&L CSV  (Label,Jan..Dec — same shape as the other entities) ───────
with open(os.path.join(here, OUT), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Label'] + ALL_MONTHS)
    for c in INCOME_CATS + EXPENSE_CATS:
        w.writerow([c] + [f'{pl[m].get(c, 0.0):.2f}' for m in ALL_MONTHS])
print(f'\n✓ wrote {OUT}')

with open(os.path.join(here, SKIP_LOG), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Month', 'Date', 'Amount', 'Type', 'Description', 'Reason'])
    for s in skipped:
        w.writerow(s)
print(f'✓ wrote {SKIP_LOG}')
