#!/usr/bin/env python3
"""Smart Beginnings of Kirk & Butterfield — Jan–Oct 2026 P&L from Chase7052 (operating) + Chase7060 (payroll)
(October is partial — statement pulled 10/14/2026, covers through 10/09.)"""

import csv
from collections import defaultdict

MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct']
pl = {m: defaultdict(float) for m in MONTHS}
unk = []
checks_flag = []
skip_log = []   # (month, date, amount, type, reason, description) — every deliberate skip

def log_skip(m, date, a, tp, d, reason):
    skip_log.append((m, date, a, tp, reason, ' '.join(d.split())[:90]))

MO = {'01':'Jan','02':'Feb','03':'Mar','04':'Apr','05':'May','06':'Jun','07':'Jul','08':'Aug','09':'Sep','10':'Oct'}

def mo(date_str):
    return MO.get(date_str.strip()[:2])

def add(m, cat, a):
    pl[m][cat] += abs(a)

# ── CHECK MAP (based on amount/date pattern analysis vs. existing kirk_butterfield_pl_2026.csv) ──
CHECK_MAP = {
    '319': 'Staff Bonus',        # $200 Jan 12
    '330': 'Cleaning Service',   # $1,790.75 Jan 26
    '332': 'Cleaning Service',   # $1,790.75 Feb 23
    '333': 'Cleaning Service',   # $1,790.75 Mar 30
    '331': 'Salaries & wages',   # $592.65 Feb 24 — resolved via CSV reconciliation
    '344': 'Salaries & wages',   # $592.65 Mar 23
    '334': 'Salaries & wages',   # $592.65 May 8
    '343': 'Landscaping',        # $595.00 Feb 2
    '345': 'Parts & Materials',  # $1,632.00 Apr 21
    '335': 'Parts & Materials',  # $3,500.00 May 19
    '336': 'Parts & Materials',  # $750.00 May 11
    '337': 'Entertainment',      # $334.24 May 26
    '338': 'Entertainment',      # $300.00 Jun 12 — party & entertainment, per Roy
    '339': 'Heating & Cooling',  # $1,210.00 Jun 15 — HVAC repair & maintenance, per Roy
    '346': 'Landscaping',        # $1,095.00 Jul 15 — landscaping, per Roy
    '349': 'Parts & Materials',  # $710.00 Aug 14 — repair, per Roy
    '350': 'Parts & Materials',  # $1,515.00 Aug 31 — maintenance & repair, per Roy
    '351': 'Parts & Materials',  # $1,469.00 Aug 31 — repair, per Roy
    '352': 'Salaries & wages',   # $218.09 Sep — payroll wages, per Roy
    '353': 'Landscaping',        # $340.00 Sep — repair & maintenance landscape, per Roy
    '355': 'Heating & Cooling',  # $4,190.00 Oct — repair heating & cooling, per Roy
}

def cat(d, a, tp, ck, m, date):
    # ── SKIP (internal transfers — regardless of direction) ─────────────────
    if tp == 'ACCT_XFER':                         log_skip(m,date,a,tp,d,'internal transfer between Konfide accounts'); return
    if 'ACCTVERIFY' in d:                         log_skip(m,date,a,tp,d,'bank-verification micro-txn, nets to $0'); return

    # ── INCOME (positive) ──────────────────────────────────────────────────
    if a > 0:
        if   'TUITIONEXPRESS' in d:            add(m, 'Tuition Express', a)
        elif 'DAY CARE RESOURC' in d:           add(m, 'Daycare Resource', a)
        elif 'STATE OF ILL' in d:                add(m, 'CCAP', a)
        elif 'ILLINOIS NETWORK' in d:            add(m, 'Grants', a)
        elif 'YWCA' in d:                        add(m, 'Grants', a)
        elif 'REMOTE ONLINE DEPOSIT' in d:       add(m, 'Tuition Express', a)
        elif d.strip() == 'DEPOSIT':             add(m, 'Tuition Express', a)   # cash deposit slip, per Roy
        elif 'REAL TIME TRANSFER' in d:          log_skip(m,date,a,tp,d,'test transfer, ignore')
        elif 'WEBBANK/INTUIT' in d:              log_skip(m,date,a,tp,d,'QB Capital loan draw (financing, not income)')
        elif 'HEADWAYCAPITAL' in d:              log_skip(m,date,a,tp,d,'Headway Capital loan draw (financing, not income)')
        elif 'APPLECARD GSBANK' in d:            log_skip(m,date,a,tp,d,'personal-card fluke')
        elif 'BRC' in d:                         log_skip(m,date,a,tp,d,'business line-of-credit draw (financing, not income)')
        # Refunds
        elif 'AMAZON' in d:                      pl[m]['Amazon'] -= abs(a)
        elif 'WALMART' in d or 'WAL-MART' in d:  pl[m]['Meals'] -= abs(a)
        elif 'DOLLAR TREE' in d:                 pl[m]['Supplies & materials'] -= abs(a)
        else: unk.append(f'{m}  CREDIT ${a:>9,.2f}  {d[:70]}')
        return

    a = abs(a)

    # ── SKIP (financing we can't see the underlying purchase detail of) ────
    if 'AMERICAN EXPRESS' in d:                   log_skip(m,date,a,tp,d,'Amex card payment, no purchase detail'); return
    if 'INTUIT FINANCING' in d:                   add(m, 'Business loan interest', a); return   # QB Capital repayment, per Roy
    if 'SMALL BUSINESS' in d:                     log_skip(m,date,a,tp,d,'SBA-type loan repayment'); return
    if tp == 'LOAN_PMT':
        if 'CHASE CARD' in d:                     log_skip(m,date,a,tp,d,'credit-card payment, no purchase detail'); return
        if 'BRC' in d:                            log_skip(m,date,a,tp,d,'business line-of-credit payment'); return
        if 'AUTO LOAN' in d or ' ALA ' in d:
            add(m, 'Vehicle expenses', a); return
        unk.append(f'{m}  LOAN_PMT ${a:>9,.2f}  {d[:70]}'); return
    if 'BRC' in d:                                 log_skip(m,date,a,tp,d,'business line-of-credit draw/payment'); return

    # ── TRANSPORTATION ───────────────────────────────────────────────────────
    if 'FIRST STUDENT' in d:                       add(m, 'Vehicle expenses', a); return   # school bus service
    if 'COSTCO GAS' in d:                          add(m, 'Vehicle expenses', a); return

    # ── TAXES (direct ACH, not via payroll) ───────────────────────────────────
    if 'ORIG CO NAME:IRS' in d:                    add(m, 'Taxes paid', a); return
    if 'IL DEPT OF REVEN' in d:                    add(m, 'Taxes paid', a); return

    # ── RENT (monthly wire to landlord) ─────────────────────────────────────
    if tp == 'WIRE_OUTGOING' and 'GLENWAY APTS' in d:
        add(m, 'Rent', a); return

    # ── LOAN (IDEA 247 recurring weekly note) ───────────────────────────────
    if 'IDEA 247 INC' in d:                       add(m, 'Business loan interest', a); return

    # ── LOAN (Headway Capital repayment — draws stay skipped, see above) ────
    if 'HWCRCVBLS23' in d:                        add(m, 'Business loan interest', a); return

    # ── PAYROLL (Chase7060) ─────────────────────────────────────────────────
    if   'ADP WAGE PAY'     in d:                 add(m, 'Salaries & wages', a); return
    elif 'ADP TAX'          in d:                 add(m, 'Taxes paid', a); return
    elif 'ADP PAYROLL FEES' in d:                 add(m, 'ADP Fee', a); return
    elif 'ADP PAY-BY-PAY'   in d:                 add(m, "Workers' compensation insurance", a); return
    elif 'ILLINOIS SC ACH'  in d:                  log_skip(m,date,a,tp,d,'child support garnishment, already in payroll'); return
    elif 'VESTWELL'         in d:                 add(m, 'Employee retirement plans', a); return

    # ── INSURANCE ────────────────────────────────────────────────────────────
    if 'WEST BEND' in d:                          add(m, 'West Bend', a); return
    if 'HEALTH CARE SERV' in d:                    add(m, 'Health insurance & accident plans', a); return

    # ── UTILITIES ────────────────────────────────────────────────────────────
    if   'COMED' in d:                            add(m, 'Electricity', a); return
    elif 'NICOR GAS' in d:                         add(m, 'Heating & Cooling', a); return
    elif 'TRANE' in d:                             add(m, 'Heating & Cooling', a); return
    elif 'HEATMAX' in d:                           add(m, 'Heating & Cooling', a); return
    elif 'LESLIE HEATING' in d:                    add(m, 'Heating & Cooling', a); return
    elif 'COMCAST' in d or 'XFINITY' in d:         add(m, 'Internet & TV services', a); return
    elif 'FOX METRO' in d:                         add(m, 'Water & sewer', a); return
    elif 'AURORA WATER' in d:                      add(m, 'Water & sewer', a); return
    elif 'WCI*AURORA' in d:                        add(m, 'Disposal & waste fees', a); return
    elif 'ALARM DETECTION' in d:                   add(m, 'Utilities', a); return
    elif 'PATRIOT HEATING' in d:                   add(m, 'Heating & Cooling', a); return

    # ── CLEANING ─────────────────────────────────────────────────────────────
    if 'BERTHA MORENO' in d:                       add(m, 'Cleaning Service', a); return

    # ── NURSE ────────────────────────────────────────────────────────────────
    if 'ZELLE PAYMENT TO DAISY' in d:               add(m, 'Nurse visit', a); return
    if 'CARLOS.HOLIDAY' in d:                       add(m, 'Parts & Materials', a); return
    if 'MARINA JAQUEZ' in d:                        add(m, 'Supplies & materials', a); return   # Zelle, per Roy

    # ── EQUIPMENT LEASE ────────────────────────────────────────────────────────
    if 'LEASE SERVICES' in d:                       add(m, 'Equipment Lease', a); return   # copy machine lease, per Roy

    # ── MERCHANT / TUITIONEXPRESS FEES ──────────────────────────────────────
    if 'TUITIONEXPRESS' in d:                      add(m, 'Merchant account fees', a); return

    # ── SOFTWARE ─────────────────────────────────────────────────────────────
    if   'INTUIT *' in d or 'INTUIT INC' in d:     add(m, 'Software & apps', a); return
    elif 'PROCARE'          in d:                  add(m, 'Software & apps', a); return
    elif 'MONDAY.COM' in d or 'MONDAY.COM INC' in d: add(m, 'Software & apps', a); return
    elif 'GOOGLE *WORKSPACE' in d or 'GOOGLE WORKSPACE' in d: add(m, 'Software & apps', a); return
    elif 'SIMPLETEXTING'    in d:                  add(m, 'Software & apps', a); return
    elif 'CANVA' in d:                             add(m, 'Software & apps', a); return
    elif 'MICROSOFT' in d or 'MSBILL' in d:        add(m, 'Software & apps', a); return
    elif 'WALMART+' in d or 'WALMART PLUS' in d:   add(m, 'Software & apps', a); return

    # ── MEALS / FOOD ─────────────────────────────────────────────────────────
    if   'DELICIOUS UNLIMITED' in d:               add(m, 'Meals', a); return
    elif "DOMINO'S" in d:                          add(m, 'Meals', a); return
    elif 'JEWEL OSCO' in d or 'JEWEL-OSCO' in d:   add(m, 'Meals', a); return
    elif 'PANERA BREAD' in d:                      add(m, 'Meals', a); return
    elif 'STARBUCKS' in d:                         add(m, 'Meals', a); return
    elif "MACIANO'S" in d:                         add(m, 'Meals', a); return
    elif 'NOTHING BUNDT' in d:                     add(m, 'Meals', a); return
    elif 'POTBELLY' in d:                          add(m, 'Meals', a); return
    elif 'FOOD SERVICE PREP' in d:                 add(m, 'Meals', a); return
    elif 'JEFA TACOS' in d:                        add(m, 'Meals', a); return
    elif 'TROPICAL SMOOTHIE' in d:                 add(m, 'Meals', a); return
    elif 'BANANA SPLIT' in d:                      add(m, 'Meals', a); return
    elif 'WALMART.COM' in d or 'WAL-MART' in d or 'WM SUPERCENTER' in d: add(m, 'Meals', a); return
    elif 'SAMS CLUB' in d or 'SAMSCLUB' in d:      add(m, 'Meals', a); return
    elif 'TST*' in d:                              add(m, 'Meals', a); return
    elif 'SQ *BATAVIA CREAMERY' in d:              add(m, 'Meals', a); return
    elif 'AURORA FRESH MARKET' in d:               add(m, 'Meals', a); return

    # ── SUPPLIES ─────────────────────────────────────────────────────────────
    if   'LP CUSTOM TEES' in d:                    add(m, 'Supplies & materials', a); return
    elif 'COLOR POWDER' in d:                      add(m, 'Supplies & materials', a); return
    elif "TCT*ANDERSON" in d:                      add(m, 'Supplies & materials', a); return
    elif 'ETSY' in d:                               add(m, 'Supplies & materials', a); return
    elif 'DOLLAR TREE' in d:                       add(m, 'Supplies & materials', a); return
    elif 'KATOM' in d:                             add(m, 'Supplies & materials', a); return
    elif 'TARGET' in d:                            add(m, 'Supplies & materials', a); return
    elif 'SUNGLASS HUT' in d:                       add(m, 'Supplies & materials', a); return
    elif 'UNTUCKIT' in d:                           add(m, 'Supplies & materials', a); return
    elif 'APPLE STORE' in d:                        add(m, 'Supplies & materials', a); return

    # ── AMAZON ───────────────────────────────────────────────────────────────
    if 'AMAZON' in d:                              add(m, 'Amazon', a); return

    # ── ENTERTAINMENT ────────────────────────────────────────────────────────
    if   'CINEMARK' in d:                          add(m, 'Entertainment', a); return
    elif 'FOAM PARTY' in d:                        add(m, 'Entertainment', a); return
    elif 'DUPAGECHILDRENSMUS' in d:                add(m, 'Entertainment', a); return
    elif 'SPECIAL EVENTS' in d:                    add(m, 'Entertainment', a); return
    elif 'SQ *TRAVELING WORLD' in d:               add(m, 'Entertainment', a); return
    elif 'TENNIS BALLERZ' in d:                    add(m, 'Entertainment', a); return

    # ── REPAIRS / PARTS ──────────────────────────────────────────────────────
    if   "UP 'N ADAM" in d:                        add(m, 'Parts & Materials', a); return
    elif 'ROTO-ROOTER' in d:                       add(m, 'Parts & Materials', a); return
    elif 'GRAINGER' in d:                          add(m, 'Parts & Materials', a); return
    elif 'ATOMIC FIRE PROT' in d:                  add(m, 'Parts & Materials', a); return
    elif 'BLACK GOLD SEPTIC' in d:                 add(m, 'Parts & Materials', a); return
    elif 'RELIABLE FIRE & SECUR' in d:             add(m, 'Parts & Materials', a); return
    elif 'ANTHONY PAINTER' in d:                   add(m, 'Parts & Materials', a); return   # Zelle, per name — painting

    # ── PEST CONTROL ─────────────────────────────────────────────────────────
    if 'ORKIN' in d:                               add(m, 'Orkin', a); return

    # ── ADVERTISING ──────────────────────────────────────────────────────────
    if 'INDEED' in d:                              add(m, 'Advertising & marketing', a); return

    # ── BUSINESS LICENSES ────────────────────────────────────────────────────
    if 'ILLINOIS SECRETARY' in d:                  add(m, 'Business licenses', a); return

    # ── LEGAL / ACCREDITATION ────────────────────────────────────────────────
    if 'NECPA' in d:                               add(m, 'Legal Fees', a); return
    if 'APLD LIB FEES' in d:                       add(m, 'Legal Fees', a); return
    if 'THE LANGUAGE LAB' in d:                    add(m, 'Legal Fees', a); return
    if 'GRTWAYS' in d or 'GREATWAY' in d:           add(m, 'Legal Fees', a); return
    if 'EFOODHANDLERS' in d:                       add(m, 'Legal Fees', a); return
    if 'CERTUS' in d:                               add(m, 'Legal Fees', a); return   # staff certification training

    # ── CHECKS ───────────────────────────────────────────────────────────────
    if tp == 'CHECK_PAID':
        cat_name = CHECK_MAP.get(ck)
        if cat_name:
            add(m, cat_name, a)
        else:
            checks_flag.append(f'{m}  ${a:>9,.2f}  CHECK {ck}  (no memo on statement)')
        return

    # ── ZELLE / QUICKPAY / CHASE_TO_PARTNERFI — unresolved names ────────────
    if tp in ('QUICKPAY_DEBIT', 'CHASE_TO_PARTNERFI'):
        unk.append(f'{m}  ${a:>9,.2f}  ZELLE: {d[:60]}')
        return

    if tp == 'MISC_DEBIT' and 'WITHDRAWAL' in d:
        log_skip(m,date,a,tp,d,'cash withdrawal — Roy confirmed skip, no business category'); return

    unk.append(f'{m}  ${a:>9,.2f}  {d[:70]}')


# ── READ FILES ────────────────────────────────────────────────────────────────
FILES_7052 = ['Chase7052_Activity_20260621.CSV', 'Chase7052_Activity_20260803.csv',
              'Chase7052_Activity_20260910.csv', 'Chase7052_Activity_20261014.csv']
FILES_7060 = ['Chase7060_Activity_20260621.CSV', 'Chase7060_Activity_20260803.csv',
              'Chase7060_Activity_20260910.csv', 'Chase7060_Activity_20261014.csv']

for fname in FILES_7052 + FILES_7060:
    with open(fname, newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            m = mo(row['Posting Date'])
            if not m: continue
            d  = row['Description'].upper()
            a  = float(row['Amount'])
            tp = row['Type'].strip()
            ck = row.get('Check or Slip #','').strip()
            cat(d, a, tp, ck, m, row['Posting Date'])


# ── REPORT ──────────────────────────────────────────────────────────────────
INCOME_CATS = ['Grants','CCAP','Daycare Resource','Tuition Express']
EXPENSE_CATS = [
    'Advertising & marketing','Business licenses',
    'Health insurance & accident plans',"Workers' compensation insurance",'Employee retirement plans',
    'Entertainment','Staff Bonus','West Bend','Business loan interest','Legal Fees',
    'Nurse visit','Meals','Merchant account fees','Software & apps','ADP Fee',
    'Salaries & wages','Taxes paid','Rent','Cleaning Service','Heating & Cooling',
    'Landscaping','Orkin','Parts & Materials','Amazon','Supplies & materials',
    'Utilities','Disposal & waste fees','Electricity','Internet & TV services',
    'Water & sewer','Vehicle expenses','Equipment Lease',
]

print("=" * 100)
print("  SMART BEGINNINGS OF KIRK & BUTTERFIELD — JAN–OCT 2026 P&L  (Oct partial, thru 10/09)")
print("=" * 100)

months = MONTHS
print(f"\n{'':38}", end='')
for m in months: print(f'{m:>10}', end='')
print()
print("-" * (38 + 10*len(months)))

print("INCOME:")
tot_inc = [0]*len(months)
for c in INCOME_CATS:
    row_vals = [pl[m].get(c,0) for m in months]
    if any(row_vals):
        print(f"  {c:<36}", end='')
        for v in row_vals: print(f'{v:>10,.0f}', end='')
        print()
    tot_inc = [t+v for t,v in zip(tot_inc,row_vals)]
print(f"  {'TOTAL INCOME':<36}", end='')
for v in tot_inc: print(f'{v:>10,.0f}', end='')
print()

print("\nEXPENSES:")
tot_exp = [0]*len(months)
for c in EXPENSE_CATS:
    row_vals = [pl[m].get(c,0) for m in months]
    if any(row_vals):
        print(f"  {c:<36}", end='')
        for v in row_vals: print(f'{v:>10,.0f}', end='')
        print()
    tot_exp = [t+v for t,v in zip(tot_exp,row_vals)]
print(f"  {'TOTAL EXPENSES':<36}", end='')
for v in tot_exp: print(f'{v:>10,.0f}', end='')
print()

print(f"\n  {'NET INCOME':<36}", end='')
for i,e in zip(tot_inc, tot_exp): print(f'{i-e:>10,.0f}', end='')
print()

if checks_flag:
    print("\nCHECKS — need Roy's input:")
    for c in checks_flag: print(" ", c)

if unk:
    print("\nUNCATEGORIZED:")
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

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kirk_butterfield_pl_2026.csv')
write_csv(out_path, INCOME_CATS + EXPENSE_CATS)
print(f"\n✓ Wrote {out_path} — ready to upload to Google Drive")

skip_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kirk_butterfield_skipped_transactions.csv')
with open(skip_path, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Month', 'Date', 'Amount', 'Type', 'Reason', 'Description'])
    for s in skip_log:
        w.writerow(s)
print(f"✓ Wrote {skip_path}  ({len(skip_log)} skipped transactions)")
