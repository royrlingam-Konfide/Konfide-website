#!/usr/bin/env python3
"""Smart Beginnings Oswego — Jul–Oct 2026 P&L from Chase9056 (operating) + Chase9072 (payroll).
(October is partial — statement pulled 10/14/2026, covers through 10/09.)

Jan–Jun 2026 are NOT recomputed here — those are already published and verified;
this script only adds Jul-Oct and carries Jan-Jun forward unchanged from the
committed oswego_pl_2026.csv.

NOTE: June's P&L drew partly on an American Express statement (Software & apps,
Supplies via Walmart/Wayfair, Orkin, Advertising/Indeed). No Oswego Amex export
exists for Jul–Oct, so those categories are under-counted for this stretch
until that statement is provided.
"""

import csv
import os
from collections import defaultdict

MONTHS = ['Jul', 'Aug', 'Sep', 'Oct']   # Jun and earlier are preserved unchanged, not recomputed
MO = {'07': 'Jul', '08': 'Aug', '09': 'Sep', '10': 'Oct'}
pl = {m: defaultdict(float) for m in MONTHS}
unknowns = []
checks_flag = []


def mo(date_str):
    return MO.get(date_str.strip()[:2])


def add(m, cat, amt):
    pl[m][cat] += abs(amt)


# ── CHECK MAP (carried over from the June-only script, extend as needed) ────
CHECK_MAP = {
    '1088': 'Parts & Materials',
    '1089': 'Entertainment',
    '1090': 'Entertainment',             # $250.00 Jul — per Roy
    '1091': 'Entertainment',             # $375.00 Jul — per Roy
    '1094': 'Parts & Materials',         # $1,100.00 Aug — radon testing, repair & maintenance, per Roy
    '7003': 'Heating & Cooling',         # $1,844.00 Aug — repair heating & cooling, per Roy
    '1093': 'Parts & Materials',         # $228.00 Sep — repair, per Roy
    '1095': 'REFUND:Tuition Express',    # $664.20 Sep — refund to parents, per Roy
    '1096': 'Parts & Materials',         # $198.33 Sep — fire extinguisher testing, per Roy
}

FILES_9056 = ['Chase9056_Activity_20261014.csv']
FILES_9072 = ['Chase9072_Activity_20261014.csv']


def cat_9056(d, a, tp, ck, m):
    if tp == 'ACCT_XFER': return
    if 'AMERICAN EXPRESS' in d: return
    if 'INTUIT FINANCING' in d: return
    if 'BRC' in d: return  # line-of-credit draw/payment, either direction

    if a > 0:
        if 'TUITIONEXPRESS' in d:              add(m, 'Tuition Express', a)
        elif 'DAY CARE RESOURC' in d:           add(m, 'Daycare Resource', a)
        elif 'STATE OF ILL' in d:                add(m, 'CCAP', a)
        elif 'ILLINOIS NETWORK' in d:            add(m, 'Grants', a)
        elif 'WEBBANK/INTUIT' in d:              pass   # loan draw, skip
        elif 'US FOODSERVICE' in d:              pl[m]['Meals'] -= abs(a)   # refund/credit
        elif tp in ('CHECK_DEPOSIT', 'DSLIP'):   add(m, 'Tuition Express', a)
        else: unknowns.append(f'{m}  9056 CREDIT ${a:>9,.2f}  {d[:70]}')
        return

    a = abs(a)
    if   'TUITIONEXPRESS' in d:                add(m, 'Merchant account fees', a)
    elif 'WEST BEND' in d:                      add(m, 'West Bend', a)
    elif 'COMED' in d:                          add(m, 'Electricity', a)
    elif 'NICOR GAS' in d:                       add(m, 'Heating & Cooling', a)
    elif 'FOX METRO' in d:                       add(m, 'Water & sewer', a)
    elif 'OSWEGO IL' in d:                       add(m, 'Water & sewer', a)
    elif 'INTUIT *' in d:                        add(m, 'Software & apps', a)
    elif 'SIMPLETEXTING' in d:                   add(m, 'Software & apps', a)
    elif 'TYLER TECH' in d:                      add(m, 'Software & apps', a)
    elif 'WALMART' in d or 'WAL-MART' in d:      add(m, 'Supplies & materials', a)
    elif 'SAMS CLUB' in d:                       add(m, 'Supplies & materials', a)
    elif 'INSTACART' in d:                       add(m, 'Meals', a)
    elif 'US FOODSERVICE' in d:                  add(m, 'Meals', a)
    elif 'DAISY' in d:                           add(m, 'Cleaning Service', a)
    elif 'BERTHA MORENO' in d:                   add(m, 'Cleaning Service', a)
    elif 'JOSE DIAZ' in d:                       add(m, 'Parts & Materials', a)
    elif 'PAINTER' in d:                         add(m, 'Parts & Materials', a)
    elif 'DOCTOR DRAIN' in d or 'PLUMM' in d:    add(m, 'Parts & Materials', a)
    elif 'GRTWAYS' in d or 'GREATWAY' in d:      add(m, 'Legal Fees', a)
    elif 'LEASE SERVICES' in d:                  add(m, 'Equipment Lease', a)   # same copier vendor as Kirk
    elif 'AMAZON' in d:                           add(m, 'Amazon', a)
    elif 'SEG INC' in d and tp == 'WIRE_OUTGOING': add(m, 'Rent', a)   # per Roy
    elif 'ZELLE PAYMENT TO MEGAN' in d:           pass   # loan to employee — not a P&L expense, per Roy
    elif tp == 'CHECK_PAID':
        cat_name = CHECK_MAP.get(ck)
        if cat_name and cat_name.startswith('REFUND:'):
            pl[m][cat_name[len('REFUND:'):]] -= a   # reduces income, not an expense
        elif cat_name:
            add(m, cat_name, a)
        else:
            checks_flag.append(f'{m}  ${a:>9,.2f}  CHECK {ck}  (no memo on statement)')
    else:
        unknowns.append(f'{m}  9056 DEBIT  ${a:>9,.2f}  {d[:70]}')


def cat_9072(d, a, tp, m):
    if tp == 'ACCT_XFER' or a > 0: return
    a = abs(a)
    if   'ADP WAGE PAY' in d:                   add(m, 'Salaries & wages', a)
    elif 'ADP TAX' in d:                        add(m, 'Taxes paid', a)
    elif 'ADP PAYROLL FEES' in d:               add(m, 'ADP Fee', a)
    elif 'ADP PAY-BY-PAY' in d:                 add(m, "Workers' compensation insurance", a)
    else: unknowns.append(f'{m}  9072 DEBIT  ${a:>9,.2f}  {d[:70]}')


for fname in FILES_9056:
    with open(fname, newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            m = mo(row['Posting Date'])
            if not m: continue
            cat_9056(row['Description'].upper(), float(row['Amount']), row['Type'].strip(),
                      row.get('Check or Slip #', '').strip(), m)

for fname in FILES_9072:
    with open(fname, newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            m = mo(row['Posting Date'])
            if not m: continue
            cat_9072(row['Description'].upper(), float(row['Amount']), row['Type'].strip(), m)

# ── AMERICAN EXPRESS — Jul 1 thru Oct 9 2026 (matches the bank-account cutoff) ──
with open('activity10:2026.csv', newline='', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        date = row['Date'].strip()
        m = mo(date)
        if not m: continue
        if date == '10/10/2026': continue   # one day past our Oct cutoff
        d = row['Description'].upper()
        a = float(row['Amount'])

        if a <= 0:
            v = abs(a)
            if   'AMAZON' in d: pl[m]['Amazon'] -= v
            elif 'WALMART' in d: pl[m]['Supplies & materials'] -= v
            # payments (MOBILE/ONLINE/AUTOPAY PAYMENT - THANK YOU) -> not an expense, skip
            continue

        if   'RETURNED AUTOPAY' in d:            pass   # bounced payment reversal, nets against its own payment
        elif 'RETURN PAYMENT FEE' in d:           add(m, 'Merchant account fees', a)
        elif 'LATE FEE' in d:                     add(m, 'Business loan interest', a)
        elif 'RENEWAL MEMBERSHIP FEE' in d:       add(m, 'Business loan interest', a)
        elif 'INTEREST CHARGE' in d:              add(m, 'Business loan interest', a)
        elif 'AMAZON' in d:                       add(m, 'Amazon', a)
        elif any(x in d for x in ('ALDI', 'GFS STORE', 'GFS ECOMM', 'GORDON FOOD')): add(m, 'Meals', a)
        elif 'INSTACART' in d or 'COSTCO BY INSTAC' in d: add(m, 'Meals', a)
        elif any(x in d for x in ('DOMINO', 'DUNKIN', 'JIMMY JOHNS', 'CHEESECAKE', 'CANDY CLOUD')): add(m, 'Meals', a)
        elif 'WALMART' in d or 'WAL-MART' in d:   add(m, 'Supplies & materials', a)
        elif 'SAMS CLUB' in d or "SAM'S CLUB" in d:
            add(m, 'Vehicle expenses' if 'FUEL' in d else 'Supplies & materials', a)
        elif 'WAYFAIR' in d:                      add(m, 'Supplies & materials', a)
        elif 'ZAZZLE' in d or 'LP CUSTOM' in d or 'NORTHWOOD' in d: add(m, 'Supplies & materials', a)
        elif 'DOLLARTREE' in d or 'DOLLAR TREE' in d: add(m, 'Supplies & materials', a)
        elif 'CRICUT' in d:                       add(m, 'Supplies & materials', a)
        elif 'MICHAELS' in d:                     add(m, 'Supplies & materials', a)
        elif 'HOBBY-LOBBY' in d or 'HOBBY LOBBY' in d: add(m, 'Supplies & materials', a)
        elif 'OFFICEMAX' in d or 'OFFICE DEPOT' in d: add(m, 'Supplies & materials', a)
        elif 'VISTAPRINT' in d:                   add(m, 'Supplies & materials', a)
        elif 'TARGET' in d:                       add(m, 'Supplies & materials', a)
        elif 'KATOM' in d:                        add(m, 'Supplies & materials', a)
        elif 'DISCOUNTSCH' in d:                  add(m, 'Supplies & materials', a)   # DiscountSchoolSupply
        elif 'KAPLAN EARLY LEARNIN' in d:         add(m, 'Supplies & materials', a)
        elif 'PROCARE' in d:                      add(m, 'Software & apps', a)
        elif 'MICROSOFT' in d or 'MSBILL' in d:   add(m, 'Software & apps', a)
        elif 'SLACK' in d:                        add(m, 'Software & apps', a)
        elif 'JOTFORM' in d:                      add(m, 'Software & apps', a)
        elif 'COMCAST' in d or 'XFINITY' in d:    add(m, 'Internet & TV services', a)
        elif 'ALARM DETECTION' in d:              add(m, 'Software & apps', a)
        elif 'NICOR GAS' in d:                    add(m, 'Heating & Cooling', a)
        elif 'PATRIOT HEATING' in d:              add(m, 'Heating & Cooling', a)
        elif 'GROOT' in d:                        add(m, 'Disposal & waste fees', a)
        elif 'DELTA SONIC' in d:                  add(m, 'Vehicle expenses', a)
        elif 'SPARKLE EXPRESS CAR' in d:          add(m, 'Vehicle expenses', a)
        elif 'INDEED' in d:                       add(m, 'Advertising & marketing', a)
        elif 'ORKIN' in d:                        add(m, 'Orkin', a)
        elif 'FOAM PARTY' in d or 'KONA ICE' in d: add(m, 'Entertainment', a)
        elif "A&T ELECTRIC" in d:                 add(m, 'Parts & Materials', a)
        elif 'VILLAGE*OF OSWEGO' in d:            add(m, 'Business licenses', a)
        elif 'SP IM8 HEALTH' in d:                add(m, 'Supplies & materials', a)   # per Roy
        elif 'ME-WARRENVILLE-ECOMM' in d:         add(m, 'Supplies & materials', a)   # per Roy
        elif 'WALMART PLUS' in d or 'WALMART+' in d: pass
        else:
            unknowns.append(f'{m}  AMEX  ${a:>9,.2f}  {" ".join(row["Description"].split())[:60]}')


# ── MANUAL OVERRIDES — not derived from any statement, entered per Roy ───────
# New "Health Insurance" line (distinct from the legacy "Health insurance &
# accident plans" row above). Rate changed starting September; carry Sep's
# rate forward to later months unless Roy says otherwise.
HEALTH_INSURANCE_BY_MONTH = {
    'Jul': 963.81,
    'Aug': 963.81,
    'Sep': 2719.40,
    'Oct': 2719.40,
    'Nov': 2719.40,
    'Dec': 2719.40,
}
for _m in MONTHS:
    if _m in HEALTH_INSURANCE_BY_MONTH:
        pl[_m]['Health Insurance'] = HEALTH_INSURANCE_BY_MONTH[_m]


# ── REPORT ──────────────────────────────────────────────────────────────────
INCOME_CATS = ['CCAP', 'Daycare Resource', 'Tuition Express', 'Grants']
EXPENSE_CATS = [
    'Salaries & wages', "Workers' compensation insurance", 'Health insurance & accident plans',
    'Health Insurance',
    'Taxes paid', 'ADP Fee', 'Staff Bonus', 'Business loan interest', 'Rent',
    'Merchant account fees', 'West Bend', 'Meals', 'Amazon', 'Supplies & materials',
    'Parts & Materials', 'Vehicle expenses', 'Electricity', 'Heating & Cooling',
    'Water & sewer', 'Internet & TV services', 'Utilities', 'Disposal & waste fees',
    'Orkin', 'Software & apps', 'Entertainment', 'Landscaping', 'Cleaning Service',
    'Legal Fees', 'Business licenses', 'Advertising & marketing', 'Nurse visit',
    'Equipment Lease',
]

print('=' * 110)
print('  SMART BEGINNINGS OSWEGO — JUL–OCT 2026 P&L  (Oct partial, thru 10/09; no Amex this stretch)')
print('=' * 110)
print(f"\n{'':32}" + ''.join(f'{m:>10}' for m in MONTHS))
print('-' * (32 + 10 * len(MONTHS)))

print('INCOME:')
tot_inc = [0] * len(MONTHS)
for c in INCOME_CATS:
    vals = [pl[m].get(c, 0) for m in MONTHS]
    if any(vals):
        print(f'  {c:<30}' + ''.join(f'{v:>10,.0f}' for v in vals))
    tot_inc = [t + v for t, v in zip(tot_inc, vals)]
print(f"  {'TOTAL INCOME':<30}" + ''.join(f'{v:>10,.0f}' for v in tot_inc))

print('\nEXPENSES:')
tot_exp = [0] * len(MONTHS)
for c in EXPENSE_CATS:
    vals = [pl[m].get(c, 0) for m in MONTHS]
    if any(vals):
        print(f'  {c:<30}' + ''.join(f'{v:>10,.0f}' for v in vals))
    tot_exp = [t + v for t, v in zip(tot_exp, vals)]
print(f"  {'TOTAL EXPENSES':<30}" + ''.join(f'{v:>10,.0f}' for v in tot_exp))

print(f"\n  {'NET INCOME':<30}" + ''.join(f'{i-e:>10,.0f}' for i, e in zip(tot_inc, tot_exp)))

if checks_flag:
    print('\nCHECKS — need Roy\'s input:')
    for c in checks_flag: print(' ', c)
if unknowns:
    print('\nUNCATEGORIZED:')
    for u in unknowns: print(' ', u)


# ── MERGE with existing Jan-May and WRITE CSV ────────────────────────────────
here = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(here, 'oswego_pl_2026.csv')
ALL_MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

existing = {}
with open(csv_path, newline='') as f:
    for row in csv.DictReader(f):
        existing[row['Label']] = row

all_labels = list(dict.fromkeys(list(existing.keys()) + INCOME_CATS + EXPENSE_CATS))

with open(csv_path, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Label'] + ALL_MONTHS)
    for label in all_labels:
        row = [label]
        for m in ALL_MONTHS:
            if m in ('Jan', 'Feb', 'Mar', 'Apr', 'May'):
                v = float(existing.get(label, {}).get(m, 0) or 0)
            elif m in MONTHS:
                v = pl[m].get(label, 0.0)
            else:
                v = float(existing.get(label, {}).get(m, 0) or 0)
            row.append(f'{v:.2f}')
        w.writerow(row)

print(f'\n✓ Wrote {csv_path} — Jan-May preserved, Jun-Oct recomputed from source')
