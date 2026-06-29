#!/usr/bin/env python3
"""
Konfide Properties P&L generator
Processes Chase5899 (Konfide Properties LLC) and Chase9012 (Konfide Aurora LLC)
"""

import csv, re
from collections import defaultdict

MONTHS = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
YEAR_RANGE = [2025, 2026]

def key(yr, mo): return (yr, mo)

def parse_date(d):
    m, day, y = d.split('/')
    return int(y), MONTHS[int(m)-1]

def amt(row):
    return float(row['Amount'].replace(',',''))

def desc(row):
    return row['Description'].upper()

def process_5899(path):
    """Konfide Properties LLC — operating account"""
    inc  = defaultdict(float)
    mort = defaultdict(float)
    hoa  = defaultdict(float)
    util = defaultdict(float)
    rep  = defaultdict(float)
    off  = defaultdict(float)
    trav = defaultdict(float)
    skip_log = []
    unk_log  = []

    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tp = row['Type'].strip()
            d  = desc(row)
            a  = amt(row)
            yr, mo = parse_date(row['Posting Date'].strip())
            k = (yr, mo)
            ck = row.get('Check or Slip #','').strip()

            # ── SKIP ──────────────────────────────────────────────
            if tp == 'ACCT_XFER':
                continue
            if tp == 'LOAN_PMT':
                skip_log.append(f"LOAN_PMT {row['Posting Date']} {a}")
                continue
            # Skip capital injections (wire in from investor)
            if 'THIYAGARAJAH' in d or 'MAGASWARAN' in d:
                skip_log.append(f"INVESTOR {row['Posting Date']} {a}")
                continue
            # Skip LOC draws (BRC 7001 credit)
            if 'BRC' in d and a > 0:
                skip_log.append(f"LOC DRAW {row['Posting Date']} {a}")
                continue
            # Skip AmEx payments (expenses on card not visible here)
            if 'AMERICAN EXPRESS' in d:
                continue
            # Skip property purchase wires
            if tp == 'WIRE_OUTGOING':
                skip_log.append(f"WIRE OUT (property purchase?) {row['Posting Date']} {abs(a)}")
                continue
            # Skip Keller Williams (realtor commissions for purchases)
            if 'KELLER WILLIAMS' in d:
                skip_log.append(f"KW commission {row['Posting Date']} {abs(a)}")
                continue
            if 'TRUSTFUNDS' in d or 'TRUST FUNDS' in d:
                skip_log.append(f"TrustFunds fee {row['Posting Date']} {abs(a)}")
                continue
            # Skip DoorLoop convenience fee (property purchase listing fee)
            if 'DOORLOOP' in d and 'PURCHASE D' in d and abs(a) == 169.0:
                pass  # these ARE office, don't skip

            # ── INCOME ────────────────────────────────────────────
            if a > 0:
                if 'AURORA HOUSING A' in d or 'DUPAGE HOUSING A' in d:
                    inc[k] += a
                elif 'DOORLOOP' in d or 'DOOR LOOP' in d:
                    inc[k] += a  # DoorLoop credit = tenant rent collected
                elif tp in ('ATM','CHECK_DEPOSIT','DSLIP','DEPOSIT'):
                    if a >= 5000:
                        skip_log.append(f"LARGE DEPOSIT (capital, not rent) {row['Posting Date']} ${a:.2f}")
                    else:
                        inc[k] += a
                elif 'LINNETTE LAMERSON' in d or 'DEAUNTE MARSHALL' in d:
                    inc[k] += a  # tenant Zelle rent
                elif 'SINTHUJA' in d and abs(a) <= 1.0:
                    skip_log.append(f"TEST PAYMENT {row['Posting Date']} {a}")
                elif 'SMART BEGINNINGS AOA' in d:
                    inc[k] += a  # inter-company rent/reimbursement
                elif 'BOOK TRANSFER CREDIT' in d:
                    skip_log.append(f"WIRE IN (investor/loan) {row['Posting Date']} {a}")
                elif 'SINTHUJA' in d:
                    inc[k] += a
                else:
                    unk_log.append(f"UNK CREDIT {row['Posting Date']} {a:.2f} | {row['Description'][:80]}")
                continue

            # ── EXPENSES (a < 0) ──────────────────────────────────
            a = abs(a)

            # Mortgage
            if 'SELENE FINANCE' in d:
                mort[k] += a
            elif 'ORIG ID:9301144000' in d:  # 1053 Symphony Dr / CT Chicago Metro / Coldwell Banker
                mort[k] += a

            # HOA
            elif 'HOMETOWN CONDOMI' in d or 'ACCT INTEGRATORS' in d:
                hoa[k] += a

            # Utilities
            elif 'NICOR GAS' in d or 'NICOR' in d:
                util[k] += a
            elif 'COMED' in d:
                util[k] += a

            # Repair
            elif 'JOSE DIAZ' in d:
                rep[k] += a
            elif 'DYLAN SCOTT' in d:
                rep[k] += a
            elif 'SALVADOR LOPEZ' in d:
                rep[k] += a
            elif 'TEMP TECH' in d:
                rep[k] += a
            elif 'PAUL SMERZ' in d:
                rep[k] += a
            elif 'BANDY LOCKSMITH' in d:
                rep[k] += a
            elif 'JUVE WINDOWS' in d:
                rep[k] += a
            elif 'WILLIAM' in d and tp in ('QUICKPAY_DEBIT','MISC_DEBIT') and a <= 500:
                rep[k] += a
            elif 'INVOICE2GO' in d:
                rep[k] += a
            elif 'GARAGE DOORS REPAIRING' in d:
                rep[k] += a
            elif 'VERIFY HOME INSPECT' in d:
                rep[k] += a

            # Office
            elif 'DOORLOOP' in d or 'DOOR LOOP' in d:
                off[k] += a
            elif 'GREATWAY TAX' in d:
                off[k] += a
            elif 'CHECK OR SUPPLY' in d:
                off[k] += a

            # Travel
            elif 'INGA TAXI' in d:
                trav[k] += a

            # Misc repair (confirmed by Roy)
            elif 'KHRYSTAL' in d:
                rep[k] += a

            # Checks — confirmed repair by Roy
            elif tp == 'CHECK_PAID':
                rep[k] += a

            elif 'LINNETTE' in d or 'LINETTE' in d:
                skip_log.append(f"Tenant refund/adjustment {row['Posting Date']} ${a:.2f} — skipped")
            else:
                unk_log.append(f"UNK DEBIT {row['Posting Date']} {a:.2f} | {row['Description'][:80]}")

    return inc, mort, hoa, util, rep, off, trav, skip_log, unk_log


def process_9012(path):
    """Konfide Aurora LLC"""
    rep  = defaultdict(float)
    off  = defaultdict(float)
    skip_log = []
    unk_log  = []

    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tp = row['Type'].strip()
            d  = desc(row)
            a  = amt(row)
            yr, mo = parse_date(row['Posting Date'].strip())
            k = (yr, mo)

            if tp == 'ACCT_XFER':
                continue
            if tp == 'WIRE_OUTGOING':
                skip_log.append(f"WIRE OUT (property purchase) {row['Posting Date']} {abs(a)}")
                continue
            if 'BRC' in d and a > 0:
                skip_log.append(f"LOC DRAW {row['Posting Date']} {a}")
                continue
            if a > 0:
                skip_log.append(f"UNK CREDIT {row['Posting Date']} {a:.2f} | {d[:60]}")
                continue

            a = abs(a)

            if 'LUIS ALEXANDER' in d or 'PAINTER' in d:
                rep[k] += a
            elif 'MIGUEL A ASTORGA' in d or 'MIGUEL' in d:
                rep[k] += a
            elif 'JOSE DIAZ' in d:
                rep[k] += a
            elif 'DENNIS' in d and 'FOUR SEASON' in d:
                rep[k] += a
            elif 'WIRE FEE' in d or 'DOMESTIC WIRE FEE' in d:
                off[k] += a
            elif tp == 'MISC_DEBIT' and 'WITHDRAWAL' in d:
                skip_log.append(f"CASH WITHDRAWAL ${a:.2f} on {row['Posting Date']} — skipped per Roy")
            else:
                unk_log.append(f"UNK {row['Posting Date']} {a:.2f} | {d[:60]}")

    return rep, off, skip_log, unk_log


def write_csv(path, rows, years=YEAR_RANGE):
    headers = ['Label']
    for yr in years:
        for m in MONTHS:
            headers.append(f"{m.capitalize()} {yr}")
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(headers)
        for label, data in rows:
            row_vals = [label]
            for yr in years:
                for m in MONTHS:
                    row_vals.append(f"{data.get((yr,m), 0):.2f}")
            w.writerow(row_vals)


# ─── MAIN ────────────────────────────────────────────────────────────────────
import os, sys

base = os.path.dirname(os.path.abspath(__file__))
f5899 = os.path.join(base, 'Chase5899_Activity_20260623.CSV')
f9012 = os.path.join(base, 'Chase9012_Activity_20260623.CSV')

print("=== Processing Chase5899 (Konfide Properties LLC) ===")
inc, mort, hoa, util, rep, off, trav, skip5, unk5 = process_5899(f5899)

print("\n=== Processing Chase9012 (Konfide Aurora LLC) ===")
rep9, off9, skip9, unk9 = process_9012(f9012)

# Write Konfide Properties LLC CSV
prop_rows = [
    ('Rental Income',        inc),
    ('Mortgage',             mort),
    ('HOA',                  hoa),
    ('Utilities',            util),
    ('Repair & Maintenance', rep),
    ('Travel',               trav),
    ('Office Expenses',      off),
]
prop_csv = os.path.join(base, 'konfide_prop_cf.csv')
write_csv(prop_csv, prop_rows)
print(f"\n✓ Wrote {prop_csv}")

# Write Konfide Aurora LLC CSV
aurora_rows = [
    ('Rental Income',        defaultdict(float)),
    ('Mortgage',             defaultdict(float)),
    ('HOA',                  defaultdict(float)),
    ('Utilities',            defaultdict(float)),
    ('Repair & Maintenance', rep9),
    ('Travel',               defaultdict(float)),
    ('Office Expenses',      off9),
]
aurora_csv = os.path.join(base, 'konfide_aurora_cf.csv')
write_csv(aurora_csv, aurora_rows)
print(f"✓ Wrote {aurora_csv}")

# Print summaries
print("\n=== Konfide Properties LLC — Summary (2025-2026 YTD) ===")
for label, d in prop_rows:
    total = sum(d.values())
    if total:
        print(f"  {label:30s}  ${total:>12,.2f}")

print("\n=== Konfide Aurora LLC — Summary (2026 YTD) ===")
for label, d in aurora_rows:
    total = sum(d.values())
    if total:
        print(f"  {label:30s}  ${total:>12,.2f}")

print("\n=== ITEMS NEEDING ROY'S CLARIFICATION ===")
print("\n--- Chase5899 ---")
for s in skip5:
    if 'NEEDS' in s or 'CHECK' in s:
        print(" ", s)
for u in unk5:
    print(" ", u)

print("\n--- Chase9012 ---")
for s in skip9:
    if 'NEEDS' in s:
        print(" ", s)
for u in unk9:
    print(" ", u)
