#!/usr/bin/env python3
"""Smart Beginnings Ogden/IL-59 — Full Jan–Aug 2026 P&L from Chase6820"""

import csv
from collections import defaultdict

MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug']
pl   = {m: defaultdict(float) for m in MONTHS}
unk  = []
checks_flag = []
zelle_flag  = []

MO = {'01':'Jan','02':'Feb','03':'Mar','04':'Apr','05':'May','06':'Jun','07':'Jul','08':'Aug'}

def mo(date_str):
    return MO.get(date_str.strip()[:2])

def add(m, cat, a):
    pl[m][cat] += abs(a)

# ── CHECK MAP (based on amount/date pattern analysis) ─────────────────────────
CHECK_MAP = {
    '842':  'Parts & Materials',        # $1,575 Jan 12
    '1083': 'Supplies & materials',        # $44 Jan 8
    '1084': 'Rent',                      # $2,000 Jan 13
    '1085': 'Parts & Materials',         # $1,785 Jan 21
    '1087': 'Rent',                      # $3,600 Jan 27
    '1088': 'Business loan interest',    # $3,000 Jan 27
    '997':  'Staff Bonus',               # $50 Feb 9
    '1089': 'Rent',                      # $3,600 Feb 25
    '1090': 'Business loan interest',    # $3,200 Mar 6
    '1091': 'Legal Fees',                # $684 Apr 17
    '1092': 'Rent',                      # $4,000 Apr 7
    '1093': 'Business loan interest',    # $3,500 Apr 7
    '50003': 'Supplies & materials',      # $127.76 Apr 30
    '50004': 'Supplies & materials',     # $48.98 May 18
    '1094': 'Business loan interest',    # $3,000 May 12
    '1095': 'Rent',                      # $3,000 May 12
    '1096': 'Rent',                      # $3,000 Jun 9
    '1097': 'Business loan interest',    # $3,000 Jun 9
    '1008': 'Rent',                      # $3,500 Jul — per Roy
    '1010': 'Business loan interest',    # $3,250 Jul — per Roy
    '1098': 'REFUND:Tuition Express',    # $200 Jul — tuition refund, per Roy
    '50005': 'Salaries & wages',         # $440.22 Jul — payroll, per Roy
    '1099': 'Entertainment',             # $350 Jul — per Roy
    '1011': 'Rent',                      # $18,000 Aug — per Roy
    '1012': 'Business loan interest',    # $3,200 Aug — per Roy
    '1013': 'Rent',                      # $12,000 Aug — per Roy
}

# ── ZELLE NAME MAP ─────────────────────────────────────────────────────────────
ZELLE_MAP = {
    'JOSE WORK':        'Parts & Materials',
    'JOSE SARENA':      'Parts & Materials',
    'LARRY':            'Parts & Materials',
    'ALEKSANDAR':       'Parts & Materials',
    'DESAI':            'Parts & Materials',
    'DUPAGE':           'Parts & Materials',    # DuPage radon testing
    'PAMELA JOHNSON':   'Supplies & materials',
    'NURSE':            'Nurse visit',
    'ERIC LANDSCAPING': 'Landscaping',
    'CINDY':            None,                   # skip — not business
    'CHAIRS':           'Entertainment',
    'STABLE':           'Entertainment',
    'LISETTE':          'Entertainment',
    'CATHY':            'Legal Fees',   # per Roy: legal & professional services
    'SMART BEGINNINGS AOA': None,               # skip — inter-entity
    'NICK LUNDEEN':     None,                   # skip — likely refund/personal
}

ZELLE_FLAG_NAMES = []  # all resolved

# Resolved flagged Zelle rules: (name_fragment, category_or_None_or_callable)
ZELLE_RESOLVED = [
    ('DEE ',             None),                                                 # skip
    ('NANCY',            lambda a: 'Staff Bonus' if a <= 100 else 'Salaries & wages'),
    ('ROLANDO',          'Landscaping'),       # snow plow
    ('BIANCA',           'Entertainment'),
    ('LESLIE PRESCHOOL', 'Entertainment'),
    ('GUADALUPE SALAZAR','Salaries & wages'),  # salary
    ('LORI TUTOR',       None),               # skip
    ('IMANI',            None),               # skip
]

def cat(d, a, tp, ck, m):
    # ── INCOME (positive) ──────────────────────────────────────────────────────
    if a > 0:
        if 'TUITIONEXPRESS' in d:       add(m, 'Tuition Express', a)
        elif 'DAY CARE RESOURC' in d:   add(m, 'Daycare Resource', a)
        elif 'STATE OF ILL' in d:       add(m, 'CCAP', a)
        elif 'NICHOLAS' in d or 'LUNDEEN' in d: add(m, 'Tuition Express', a)
        elif 'YWCA' in d:               add(m, 'Grants', a)
        elif 'ILLINOIS NETWORK' in d:   add(m, 'Grants', a)
        elif 'REMOTE ONLINE DEPOSIT' in d: add(m, 'Tuition Express', a)
        elif 'REAL TIME TRANSFER' in d: pass   # $0.03/$0.05 test transfers, ignore
        # Refunds
        elif 'GFS STORE' in d:          pl[m]['Meals'] -= abs(a)
        elif 'AMAZON' in d or 'AMZN' in d: pl[m]['Amazon'] -= abs(a)
        elif 'PARLORDOUGHNUTS' in d or 'POTBELLY' in d: pl[m]['Meals'] -= abs(a)
        elif 'WALMART' in d or 'WAL-MART' in d: pl[m]['Supplies & materials'] -= abs(a)
        return

    a = abs(a)

    # ── SKIP ──────────────────────────────────────────────────────────────────
    if tp in ('ACCT_XFER', 'LOAN_PMT'):  return
    if 'AMERICAN EXPRESS' in d:           return
    if 'CHASE CREDIT CRD' in d:           return
    if 'INTUIT FINANCING' in d:           return
    if 'APPLECARD GSBANK' in d:           return   # personal Apple Card
    if 'ILLINOIS SC ACH' in d:            return   # child support garnishment (already in payroll)
    if 'WEBBANK/INTUIT' in d:             return   # QB Capital draws

    # ── SBA EIDL LOAN ─────────────────────────────────────────────────────────
    if 'SBA EIDL LOAN' in d:             add(m, 'SBA EIDL loan', a); return

    # ── PAYROLL ───────────────────────────────────────────────────────────────
    if   'ADP WAGE PAY'     in d:         add(m, 'Salaries & wages', a); return
    elif 'ADP TAX'          in d:         add(m, 'Taxes paid', a); return
    elif 'ADP PAYROLL FEES' in d:         add(m, 'ADP Fee', a); return
    elif 'ADP PAY-BY-PAY'   in d:         add(m, "Workers' compensation insurance", a); return

    # ── INSURANCE ─────────────────────────────────────────────────────────────
    if 'WEST BEND' in d:                  add(m, 'West Bend', a); return

    # ── UTILITIES ─────────────────────────────────────────────────────────────
    if   'NICOR GAS' in d:               add(m, 'Heating & Cooling', a); return
    elif 'COMED' in d:                   add(m, 'Electricity', a); return
    elif 'COMCAST' in d or 'XFINITY' in d: add(m, 'Internet & TV services', a); return
    elif 'FOX METRO WRD' in d:           add(m, 'Water & sewer', a); return
    elif 'AURORA WATER' in d or 'AURORA IL WATER' in d: add(m, 'Water & sewer', a); return

    # ── VEHICLE ───────────────────────────────────────────────────────────────
    if   'GM FINANCIAL' in d:            add(m, 'Vehicle expenses', a); return
    elif 'DELTA SONIC'   in d:           add(m, 'Vehicle expenses', a); return
    elif 'THORNTONS'     in d:           add(m, 'Vehicle expenses', a); return
    elif 'SHELL OIL'     in d or 'SHELL ' in d: add(m, 'Vehicle expenses', a); return
    elif 'COFFMAN TRUCK' in d:           add(m, 'Vehicle expenses', a); return
    elif 'JP ILSOS VEH'  in d:           add(m, 'Vehicle expenses', a); return
    elif 'COSTCO GAS'    in d:           add(m, 'Vehicle expenses', a); return
    elif tp == 'DEBIT_CARD' and ('QT ' in d or ' QT' in d): add(m, 'Vehicle expenses', a); return

    # ── RETIREMENT ───────────────────────────────────────────────────────────
    if 'VESTWELL' in d:                  add(m, 'Employee retirement plans', a); return

    # ── MERCHANT / TUITIONEXPRESS FEES ────────────────────────────────────────
    if 'TUITIONEXPRESS' in d:            add(m, 'Merchant account fees', a); return

    # ── SOFTWARE ──────────────────────────────────────────────────────────────
    if   'INTUIT *' in d or 'INTUIT INC' in d: add(m, 'Software & apps', a); return
    elif 'PROCARE'  in d:                add(m, 'Software & apps', a); return
    elif 'MSFT' in d or 'MICROSOFT' in d or 'MSBILL' in d: add(m, 'Software & apps', a); return
    elif 'ALARM DETECTION' in d:         add(m, 'Software & apps', a); return
    elif 'SIMPLE CIRCUITS' in d:         add(m, 'Parts & Materials', a); return
    elif 'SIMPLETEXTING' in d:           add(m, 'Software & apps', a); return
    elif 'WALMART PLUS' in d or 'WALMART+' in d: add(m, 'Software & apps', a); return

    # ── MEALS / FOOD ──────────────────────────────────────────────────────────
    if   'INSTACART' in d or 'COSTCO BY INSTAC' in d: add(m, 'Meals', a); return
    elif 'JEWEL OSCO' in d or 'JEWEL-OSCO' in d: add(m, 'Meals', a); return
    elif 'GFS STORE'  in d:              add(m, 'Meals', a); return
    elif "MCDONALD'S" in d or 'MCDONALDS' in d: add(m, 'Meals', a); return
    elif 'ALDI' in d:                    add(m, 'Meals', a); return
    elif 'STARBUCKS' in d:               add(m, 'Meals', a); return
    elif 'POTBELLY' in d:                add(m, 'Meals', a); return
    elif 'DUNKIN' in d:                  add(m, 'Meals', a); return
    elif 'VELVET TACO' in d:             add(m, 'Meals', a); return
    elif 'EAST CHINA INN' in d:          add(m, 'Meals', a); return
    elif 'YARD HOUSE' in d:              add(m, 'Meals', a); return
    elif 'SUPERMERCADO' in d:            add(m, 'Meals', a); return
    elif 'WHOLEFDS' in d or 'WHOLE FOODS' in d: add(m, 'Meals', a); return
    elif 'TST*' in d:                    add(m, 'Meals', a); return
    elif 'PARLORDOUGHNUTS' in d:         add(m, 'Meals', a); return
    elif 'SAMS CLUB' in d:               add(m, 'Meals', a); return
    elif "MCALISTER'S" in d or 'MCALISTERS' in d: add(m, 'Meals', a); return

    # ── SUPPLIES ──────────────────────────────────────────────────────────────
    if   'WALMART' in d or 'WAL-MART' in d: add(m, 'Supplies & materials', a); return
    elif 'DOLLAR TREE' in d or 'DOLLARTREE' in d: add(m, 'Supplies & materials', a); return
    elif 'FIVE BELOW' in d:              add(m, 'Supplies & materials', a); return
    elif 'WALGREENS' in d:               add(m, 'Supplies & materials', a); return
    elif 'CRICUT' in d:                  add(m, 'Supplies & materials', a); return
    elif 'FEDEX OFFICE' in d or 'FEDEX OFFIC' in d: add(m, 'Supplies & materials', a); return
    elif 'USPS' in d:                    add(m, 'Supplies & materials', a); return
    elif 'TARGET' in d:                  add(m, 'Supplies & materials', a); return
    elif 'PETSMART' in d:                add(m, 'Supplies & materials', a); return
    elif 'CAROLINA BIOLOGIC' in d:       add(m, 'Supplies & materials', a); return
    elif 'PAMELA JOHNSON' in d:          add(m, 'Supplies & materials', a); return
    elif 'WM SUPERCENTER' in d:          add(m, 'Supplies & materials', a); return
    elif 'MICHAELS' in d:                add(m, 'Supplies & materials', a); return
    elif 'HOBBYLOBBY' in d or 'HOBBY-LOBBY' in d or 'HOBBY LOBBY' in d: add(m, 'Supplies & materials', a); return
    elif 'DOLLAR GENERAL' in d:          add(m, 'Supplies & materials', a); return
    elif 'UP \'N ADAM' in d or 'UP N ADAM' in d: add(m, 'Parts & Materials', a); return

    # ── AMAZON ────────────────────────────────────────────────────────────────
    if 'AMAZON' in d or 'AMZN' in d:    add(m, 'Amazon', a); return

    # ── ENTERTAINMENT ─────────────────────────────────────────────────────────
    if   'DUPAGE' in d and ('MUSEUM' in d or 'CHILDREN' in d): add(m, 'Entertainment', a); return
    elif 'BLACKBERRY FARM' in d:         add(m, 'Entertainment', a); return
    elif 'FOAM PARTY' in d:              add(m, 'Entertainment', a); return
    elif 'COLOR POWDER' in d:            add(m, 'Entertainment', a); return
    elif 'KONA ICE' in d:                add(m, 'Entertainment', a); return
    elif 'SQ *TRAVELING WORLD' in d:     add(m, 'Entertainment', a); return

    # ── LANDSCAPING ───────────────────────────────────────────────────────────
    if 'LANDSCAPING' in d or 'ERIC LANDS' in d: add(m, 'Landscaping', a); return

    # ── DISPOSAL ──────────────────────────────────────────────────────────────
    if 'WASTE CONNECTION' in d:          add(m, 'Disposal & waste fees', a); return

    # ── PEST CONTROL ──────────────────────────────────────────────────────────
    if 'ORKIN' in d or 'MICE TREATMENT' in d: add(m, 'Orkin', a); return

    # ── NURSE / HEALTH TRAINING ───────────────────────────────────────────────
    if 'NURSE' in d:                     add(m, 'Nurse visit', a); return
    if 'SQ *CPR MOBILE' in d:            add(m, 'Nurse visit', a); return

    # ── ACCOUNTING / LEGAL / ACCREDITATION ────────────────────────────────────
    if 'GRTWAYS' in d or 'GREATWAY' in d: add(m, 'Legal Fees', a); return
    if 'NECPA' in d:                      add(m, 'Legal Fees', a); return
    if '360TRAINING' in d:                add(m, 'Legal Fees', a); return

    # ── ADVERTISING ───────────────────────────────────────────────────────────
    if 'MIDLAND FUND RAISING' in d:      add(m, 'Advertising & marketing', a); return

    # ── BUSINESS LICENSES ─────────────────────────────────────────────────────
    if 'ILLINOIS SECRETARY' in d:        add(m, 'Business licenses', a); return

    # ── ZELLE PAYMENTS ────────────────────────────────────────────────────────
    if 'ZELLE' in d or 'JPM99' in d:
        du = d.upper()
        for name, cat_name in ZELLE_MAP.items():
            if name in du:
                if cat_name:
                    add(m, cat_name, a)
                return
        for name, rule in ZELLE_RESOLVED:
            if name in du:
                if rule is None:
                    return  # skip
                cat_name = rule(a) if callable(rule) else rule
                add(m, cat_name, a)
                return
        unk.append(f'{m}  ${a:>8,.2f}  ZELLE: {d[:60]}')
        return

    # ── CHECKS ────────────────────────────────────────────────────────────────
    if tp == 'CHECK_PAID':
        cat_name = CHECK_MAP.get(ck)
        if cat_name and cat_name.startswith('REFUND:'):
            pl[m][cat_name[len('REFUND:'):]] -= a   # reduces income, not an expense
        elif cat_name:
            add(m, cat_name, a)
        elif ck in CHECK_MAP:   # explicitly None — flag
            checks_flag.append(f'{m}  ${a:>8,.2f}  CHECK {ck}')
        else:
            checks_flag.append(f'{m}  ${a:>8,.2f}  CHECK {ck}  (unknown)')
        return

    unk.append(f'{m}  ${a:>8,.2f}  {d[:70]}')


# ── READ FILES ────────────────────────────────────────────────────────────────
for fname in ['Chase6820_Activity_20260622.CSV', 'Chase6820_Activity_2026june.CSV',
              'Chase6820_Activity_20260917.csv']:
    with open(fname, newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            m = mo(row['Posting Date'])
            if not m: continue
            d  = row['Description'].upper()
            a  = float(row['Amount'])
            tp = row['Type'].strip()
            ck = row.get('Check or Slip #','').strip()
            cat(d, a, tp, ck, m)


# ── REPORT ────────────────────────────────────────────────────────────────────
INCOME_CATS  = ['CCAP','Daycare Resource','Tuition Express','Grants']
EXPENSE_CATS = [
    'Salaries & wages',"Workers' compensation insurance",'Taxes paid','ADP Fee','Staff Bonus',
    'West Bend','Employee retirement plans','Business loan interest','Rent','SBA EIDL loan',
    'Merchant account fees','Meals','Amazon','Supplies & materials','Parts & Materials',
    'Vehicle expenses','Electricity','Heating & Cooling','Water & sewer',
    'Internet & TV services','Utilities','Disposal & waste fees','Orkin',
    'Software & apps','Entertainment','Landscaping','Legal Fees',
    'Business licenses','Advertising & marketing','Nurse visit',
]

print("=" * 70)
print("  SMART BEGINNINGS OGDEN / IL-59 — JAN–AUG 2026 P&L")
print("=" * 70)

months = MONTHS
print(f"\n{'':38}", end='')
for m in months: print(f'{m:>10}', end='')
print(f'{"YTD":>11}')
print("-" * 108)

print("INCOME:")
grand_inc = 0
for c in INCOME_CATS:
    row_vals = [pl[m].get(c,0) for m in months]
    ytd = sum(row_vals)
    grand_inc += ytd
    if any(v for v in row_vals):
        print(f"  {c:<36}", end='')
        for v in row_vals: print(f'{v:>10,.0f}', end='')
        print(f'{ytd:>11,.0f}')

print(f"\n  {'TOTAL INCOME':<36}", end='')
for m in months:
    v = sum(pl[m].get(c,0) for c in INCOME_CATS)
    print(f'{v:>10,.0f}', end='')
print(f'{grand_inc:>11,.0f}')

print("\nEXPENSES:")
grand_exp = 0
for c in EXPENSE_CATS:
    row_vals = [pl[m].get(c,0) for m in months]
    ytd = sum(row_vals)
    grand_exp += ytd
    if any(v for v in row_vals):
        print(f"  {c:<36}", end='')
        for v in row_vals: print(f'{v:>10,.0f}', end='')
        print(f'{ytd:>11,.0f}')

print(f"\n  {'TOTAL EXPENSES':<36}", end='')
for m in months:
    v = sum(pl[m].get(c,0) for c in EXPENSE_CATS)
    print(f'{v:>10,.0f}', end='')
print(f'{grand_exp:>11,.0f}')

net = grand_inc - grand_exp
print(f"\n  {'NET INCOME':<36}", end='')
for m in months:
    inc = sum(pl[m].get(c,0) for c in INCOME_CATS)
    exp = sum(pl[m].get(c,0) for c in EXPENSE_CATS)
    print(f'{inc-exp:>10,.0f}', end='')
print(f'{net:>11,.0f}')

if checks_flag:
    print("\n\nCHECKS — need your input:")
    for c in checks_flag: print(" ", c)

if zelle_flag:
    print("\n\nZELLE — need your input:")
    for z in zelle_flag: print(" ", z)

if unk:
    print("\n\nUNCATEGORIZED:")
    for u in unk: print(" ", u)


# ── WRITE CSV (upload-ready for the Google Sheet behind finance-sb.html) ──────
import os

ALL_MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

def write_csv(path, cats):
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Label'] + ALL_MONTHS)
        for c in cats:
            row = [c]
            for m in ALL_MONTHS:
                v = pl[m].get(c, 0) if m in MONTHS else 0.0
                row.append(f"{v:.2f}")
            w.writerow(row)

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ogden_pl_2026.csv')
write_csv(out_path, INCOME_CATS + EXPENSE_CATS)
print(f"\n✓ Wrote {out_path} — ready to upload to Google Drive")
