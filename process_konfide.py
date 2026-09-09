#!/usr/bin/env python3
"""Konfide Inc. (management company) — 2025 cash-flow from Chase3252 (single account).

Rules confirmed with Roy:
  INCOME — inbound Online Transfers, bucketed by the source account:
    ...7052 -> Smart Beginnings Kirk & Butterfield
    ...6820 -> Smart Beginnings AOA
    ...9019 -> R Square Education Inc.
    ...5899 -> Konfide Properties
    ...9056 -> Smart Beginnings of Oswego
    any other inbound transfer .......... SKIP
    every non-transfer credit ........... SKIP (owner Zelle, BRC/LOC draws, Amex "loan",
                                                remote check deposits, Greatways credit)
  EXPENSES:
    AccountantsWorld (PAYROLLDBT) + ADP WAGE PAY .......... Salaries & wages
    PAYROLLTAX + ADP TAX + IRS + IL DEPT OF REVENUE ....... Payroll taxes
    PAYCHEX-HRS + ADP PAYROLL FEES ....................... Payroll fees
    HEALTH CARE SERV .................................... Health insurance
    GREATWAYS / GRTWAYS tax service ...................... Accounting & tax prep
    INTUIT * ........................................... Software
    GM FINANCIAL ....................................... Vehicle loan
    every outgoing Zelle + both outgoing wires + all 6 checks ... Events / contractors
    AMERICAN EXPRESS card payments ..................... SKIP (no purchase detail here)
  TRANSFERS OUT:
    to ...8271 and ...8754 ............................. Owner Distribution
    to ...5899 / ...6820 / ...9019 / anything else .... SKIP
"""

import csv
import os
import re
from collections import defaultdict

SRC = 'Chase3252_Activity_20260908.csv'
OUT = 'konfide_inc_cf.csv'
SKIP_LOG = 'konfide_inc_skipped_transactions.csv'

YEAR = 2025
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

INCOME_BY_ACCT = {
    '7052': 'Smart Beginnings Kirk & Butterfield',
    '6820': 'Smart Beginnings AOA',
    '9019': 'R Square Education Inc.',
    '5899': 'Konfide Properties',
    '9056': 'Smart Beginnings of Oswego',
}
OWNER_DIST_ACCTS = {'8271', '8754'}

INCOME_ROWS = list(INCOME_BY_ACCT.values())
EXPENSE_ROWS = [
    'Salaries & wages',
    'Payroll taxes',
    'Payroll fees',
    'Health insurance',
    'Accounting & tax prep',
    'Software',
    'Vehicle loan',
    'Events / contractors',
    'Owner Distribution',
]

pl = {m: defaultdict(float) for m in MONTHS}
skipped = []
unknown = []


def mo(date_str):
    return MONTHS[int(date_str.split('/')[0]) - 1]


def add(m, cat, amount):
    pl[m][cat] += abs(amount)


def skip(m, row, reason):
    skipped.append((m, row['Posting Date'], float(row['Amount']),
                    row['Type'].strip(), ' '.join(row['Description'].split())[:90], reason))


def xfer_acct(d):
    m = re.search(r'Transfer (?:from|to) \w+ \.\.\.(\d{4})', d)
    return m.group(1) if m else None


def categorize(row, m):
    d = row['Description']
    du = d.upper()
    a = float(row['Amount'])
    tp = row['Type'].strip()

    # ── TRANSFERS ────────────────────────────────────────────────────────────
    if tp == 'ACCT_XFER':
        acct = xfer_acct(d)
        if a > 0:
            if acct in INCOME_BY_ACCT:
                add(m, INCOME_BY_ACCT[acct], a); return
            skip(m, row, f'inbound transfer from unmapped acct ...{acct}'); return
        if acct in OWNER_DIST_ACCTS:
            add(m, 'Owner Distribution', a); return
        skip(m, row, f'outbound transfer to acct ...{acct}'); return

    # ── OTHER INBOUND MONEY — all skipped ────────────────────────────────────
    if a > 0:
        skip(m, row, 'non-transfer credit (financing / capital / not income)'); return

    # ── OUTBOUND MONEY ──────────────────────────────────────────────────────
    if 'AMERICAN EXPRESS' in du:
        skip(m, row, 'Amex card payment — no purchase detail on this statement'); return

    # Payroll
    if 'ACCOUNTANTSWORLD' in du or 'ADP WAGE PAY' in du:
        add(m, 'Salaries & wages', a); return
    if 'PAYROLLTAX' in du or 'ADP TAX' in du or 'ORIG CO NAME:IRS' in du or 'IL DEPT OF REVEN' in du:
        add(m, 'Payroll taxes', a); return
    if 'PAYCHEX' in du or 'ADP PAYROLL FEES' in du:
        add(m, 'Payroll fees', a); return

    # Fixed operating costs
    if 'HEALTH CARE SERV' in du:
        add(m, 'Health insurance', a); return
    if 'GREATWAYS' in du or 'GRTWAYS' in du:
        add(m, 'Accounting & tax prep', a); return
    if 'INTUIT' in du:
        add(m, 'Software', a); return
    if 'GM FINANCIAL' in du:
        add(m, 'Vehicle loan', a); return

    # Events / contractors — every outgoing Zelle, both outgoing wires, all checks
    if 'ZELLE PAYMENT TO' in du:
        add(m, 'Events / contractors', a); return
    if tp == 'WIRE_OUTGOING':
        add(m, 'Events / contractors', a); return
    if tp == 'CHECK_PAID' or du.startswith('CHECK '):
        add(m, 'Events / contractors', a); return

    unknown.append((m, row['Posting Date'], a, tp, ' '.join(d.split())[:90]))


# ── READ ────────────────────────────────────────────────────────────────────
here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, SRC), newline='', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        yr = int(row['Posting Date'].split('/')[2])
        if yr != YEAR:
            continue
        categorize(row, mo(row['Posting Date']))


# ── REPORT ──────────────────────────────────────────────────────────────────
def block(title, rows):
    print(f'\n{title}')
    print(f"  {'':32}" + ''.join(f'{m:>9}' for m in MONTHS) + f'{"Year":>13}')
    print('  ' + '-' * (32 + 9 * 12 + 13))
    totals = [0.0] * 12
    for c in rows:
        vals = [pl[m].get(c, 0.0) for m in MONTHS]
        if any(round(v, 2) for v in vals):
            print(f'  {c:<32}' + ''.join(f'{v:>9,.0f}' for v in vals) + f'{sum(vals):>13,.0f}')
        totals = [t + v for t, v in zip(totals, vals)]
    print(f"  {'TOTAL ' + title:<32}" + ''.join(f'{v:>9,.0f}' for v in totals) + f'{sum(totals):>13,.0f}')
    return totals


print('=' * 140)
print('  KONFIDE INC. — 2025 CASH FLOW  (source: %s)' % SRC)
print('=' * 140)
inc = block('INCOME', INCOME_ROWS)
exp = block('EXPENSES', EXPENSE_ROWS)
net = [i - e for i, e in zip(inc, exp)]
print(f"\n  {'NET CASH FLOW':<32}" + ''.join(f'{v:>9,.0f}' for v in net) + f'{sum(net):>13,.0f}')

if skipped:
    print(f'\n  SKIPPED: {len(skipped)} transactions, ${sum(abs(s[2]) for s in skipped):,.0f} gross (see {SKIP_LOG})')
if unknown:
    print('\n  *** UNCATEGORIZED — RESOLVE BEFORE TRUSTING OUTPUT ***')
    for m, dt, a, tp, d in unknown:
        print(f'    {dt}  {a:>12,.2f}  [{tp}]  {d}')
else:
    print('\n  ✓ every transaction categorized or explicitly skipped')


# ── WRITE cash-flow CSV  (Label, "Jan 2025" … "Dec 2025") ────────────────────
with open(os.path.join(here, OUT), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Label'] + [f'{m} {YEAR}' for m in MONTHS])
    for c in INCOME_ROWS + EXPENSE_ROWS:
        w.writerow([c] + [f'{pl[m].get(c, 0.0):.2f}' for m in MONTHS])
print(f'\n✓ wrote {OUT}')

with open(os.path.join(here, SKIP_LOG), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Month', 'Date', 'Amount', 'Type', 'Description', 'Reason'])
    for s in skipped:
        w.writerow(s)
print(f'✓ wrote {SKIP_LOG}')
