#!/usr/bin/env python3
"""Smart Beginnings of Kirk & Butterfield — 2026 YTD Profit & Loss PDF, QuickBooks layout.
Numbers come straight from process_kirk_butterfield.py (same categorization, same skips).
Run:  python3 make_kb_pl_pdf.py   →  writes Kirk_Butterfield_PL_2026_YTD.pdf
"""
import io, os, contextlib, datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
ns = {'__file__': os.path.join(HERE, 'process_kirk_butterfield.py')}
with contextlib.redirect_stdout(io.StringIO()):
    exec(open('process_kirk_butterfield.py').read(), ns)
pl, MONTHS = ns['pl'], ns['MONTHS']

PERIOD = 'January 1 – October 30, 2026'
OUT = os.path.join(HERE, 'Kirk_Butterfield_PL_2026_YTD.pdf')

def vals(cats):
    return [sum(pl[m].get(c, 0.0) for c in cats) for m in MONTHS]

# ── Layout: QuickBooks account groupings (from the QB P&L export) ───────────
# ('h', label, indent)              group header, no numbers
# ('l', category, indent, label)    detail line
# ('t', label, [cats], indent, style)  total line   style: 'sub' | 'major' | 'grand'
INCOME = ['Grants', 'CCAP', 'Daycare Resource', 'Tuition Express']
G = {
 'benefits':  ['Employee retirement plans', 'Health insurance & accident plans', "Workers' compensation insurance"],
 'general':   ['Staff Bonus'],
 'insurance': ['West Bend'],
 'interest':  ['QB Capital', 'Headway Capital', 'Chase loan', 'IDEA loan'],
 'legal':     ['Legal Fees', 'Nurse visit'],
 'office':    ['Merchant account fees', 'Software & apps', 'Equipment Lease'],
 'payroll':   ['ADP Fee', 'Salaries & wages', 'Taxes paid'],
 'repairs':   ['Cleaning Service', 'Heating & Cooling', 'Landscaping', 'Orkin', 'Parts & Materials'],
 'supplies':  ['Amazon', 'Supplies & materials'],
 'utilities': ['Utilities', 'Disposal & waste fees', 'Electricity', 'Internet & TV services', 'Water & sewer'],
}
SINGLE = ['Advertising & marketing', 'Business licenses', 'Entertainment', 'Meals', 'Rent']
OPEX = sum(G.values(), []) + SINGLE
OTHER_EXP = ['Vehicle expenses']

# Every expense category in the processor must be placed exactly once (Owner Draw is shown below Net Income).
placed = set(OPEX + OTHER_EXP + ['Owner Draw'])
missing = [c for c in ns['EXPENSE_CATS'] if c not in placed]
assert not missing, f'Unplaced expense categories: {missing}'

ROWS = [
 ('h', 'Income', 0),
 ('h', 'Services', 1),
 ('l', 'Grants', 2, 'Grants'), ('l', 'CCAP', 2, 'CCAP'),
 ('l', 'Daycare Resource', 2, 'Daycare Resource'), ('l', 'Tuition Express', 2, 'Tuition Express'),
 ('t', 'Total for Services', INCOME, 1, 'sub'),
 ('t', 'Total for Income', INCOME, 0, 'major'),
 ('t', 'Gross Profit', INCOME, 0, 'major'),
 ('h', 'Expenses', 0),
 ('l', 'Advertising & marketing', 1, 'Advertising & marketing'),
 ('l', 'Business licenses', 1, 'Business licenses'),
 ('h', 'Employee benefits', 1),
 *[('l', c, 2, c) for c in G['benefits']],
 ('t', 'Total for Employee benefits', G['benefits'], 1, 'sub'),
 ('l', 'Entertainment', 1, 'Entertainment'),
 ('h', 'General business expenses', 1),
 ('l', 'Staff Bonus', 2, 'Staff Bonus'),
 ('t', 'Total for General business expenses', G['general'], 1, 'sub'),
 ('h', 'Insurance', 1),
 ('h', 'Business insurance', 2),
 ('l', 'West Bend', 3, 'West Bend'),
 ('t', 'Total for Business insurance', G['insurance'], 2, 'sub'),
 ('t', 'Total for Insurance', G['insurance'], 1, 'sub'),
 ('h', 'Interest paid — loan payments (principal + interest)', 1),
 ('l', 'QB Capital', 2, 'QB Capital'), ('l', 'Headway Capital', 2, 'Headway Capital'),
 ('l', 'Chase loan', 2, 'Chase loan'), ('l', 'IDEA loan', 2, 'IDEA loan'),
 ('t', 'Total for Interest paid', G['interest'], 1, 'sub'),
 ('h', 'Legal & accounting services', 1),
 ('l', 'Legal Fees', 2, 'Legal Fees'), ('l', 'Nurse visit', 2, 'Nurse visit'),
 ('t', 'Total for Legal & accounting services', G['legal'], 1, 'sub'),
 ('l', 'Meals', 1, 'Meals'),
 ('h', 'Office expenses', 1),
 ('l', 'Merchant account fees', 2, 'Merchant account fees'),
 ('l', 'Software & apps', 2, 'Software & apps'),
 ('l', 'Equipment Lease', 2, 'Equipment Lease'),
 ('t', 'Total for Office expenses', G['office'], 1, 'sub'),
 ('h', 'Payroll expenses', 1),
 ('l', 'Salaries & wages', 2, 'Salaries & wages'),
 ('l', 'Taxes paid', 2, 'Payroll taxes (ADP)'),
 ('l', 'ADP Fee', 2, 'ADP fees'),
 ('t', 'Total for Payroll expenses', G['payroll'], 1, 'sub'),
 ('l', 'Rent', 1, 'Rent'),
 ('h', 'Repairs & maintenance', 1),
 *[('l', c, 2, c) for c in G['repairs']],
 ('t', 'Total for Repairs & maintenance', G['repairs'], 1, 'sub'),
 ('h', 'Supplies', 1),
 *[('l', c, 2, c) for c in G['supplies']],
 ('t', 'Total for Supplies', G['supplies'], 1, 'sub'),
 ('h', 'Utilities', 1),
 ('l', 'Utilities', 2, 'Alarm monitoring'),
 *[('l', c, 2, c) for c in G['utilities'][1:]],
 ('t', 'Total for Utilities', G['utilities'], 1, 'sub'),
 ('t', 'Total for Expenses', OPEX, 0, 'major'),
 ('net', 'Net Operating Income', (INCOME, OPEX), 0),
 ('h', 'Other Expenses', 0),
 ('l', 'Vehicle expenses', 1, 'Vehicle expenses'),
 ('t', 'Total for Other Expenses', OTHER_EXP, 0, 'major'),
 ('net', 'Net Other Income', ([], OTHER_EXP), 0),
 ('net', 'Net Income', (INCOME, OPEX + OTHER_EXP), 0, 'grand'),
 ('gap',),
 ('h', 'Below the line (not in Net Income)', 0),
 ('l', 'Owner Draw', 1, 'Owner draws (equity)'),
 ('net', 'Net Income after owner draws', (INCOME, OPEX + OTHER_EXP + ['Owner Draw']), 0),
 ('l', 'Inter-company Transfers', 1, 'Memo: inter-company transfers, net (+ in / – out)'),
]

# ── Render ────────────────────────────────────────────────────────────────
W, H = landscape(letter)
M = 30
LABEL_W = 184
COL_W = 44.5
TOT_W = 62
PCT_W = 52
x_cols = [M + LABEL_W + i * COL_W for i in range(len(MONTHS))]
x_tot = M + LABEL_W + len(MONTHS) * COL_W
x_pct = x_tot + TOT_W
RIGHT = x_pct + PCT_W
ROW_H = 10.6
FS = 6.6

c = canvas.Canvas(OUT, pagesize=(W, H))
c.setTitle('Smart Beginnings of Kirk & Butterfield — Profit and Loss 2026 YTD')
income_total = sum(vals(INCOME))
page = [1]

def fmt(v, money=False):
    if abs(v) < 0.005: return ''
    s = f'{abs(v):,.2f}'
    if money: s = '$' + s
    return ('-' + s) if v < 0 else s

def header():
    c.setFont('Helvetica-Bold', 15); c.drawCentredString(W / 2, H - 40, 'Smart Beginnings of Kirk & Butterfield')
    c.setFont('Helvetica-Bold', 11); c.drawCentredString(W / 2, H - 55, 'Profit and Loss % of Total Income')
    c.setFont('Helvetica-Bold', 9);  c.drawCentredString(W / 2, H - 68, PERIOD)
    y = H - 92
    c.setFont('Helvetica-Bold', FS + 0.4)
    for m, x in zip(MONTHS, x_cols): c.drawRightString(x + COL_W - 3, y, f'{m} 2026')
    c.drawRightString(x_tot + TOT_W - 3, y, 'Total')
    c.drawRightString(x_pct + PCT_W - 2, y, '% of Income')
    c.setLineWidth(1.1); c.line(M, y - 4, RIGHT, y - 4)
    return y - 15

def footer():
    c.setFont('Helvetica', 6.5); c.setFillGray(0.35)
    c.drawString(M, 28, 'Cash basis — prepared from Chase ...7052 (operating) and ...7060 (payroll) bank activity through 10/30/2026.')
    c.drawString(M, 19, 'Excludes financing draws, internal transfers, and card payments without purchase detail (Amex, Chase ...5667).')
    c.drawRightString(RIGHT, 19, f'Generated {datetime.date.today():%B %d, %Y}  ·  Page {page[0]}')
    c.setFillGray(0)

def line_numbers(y, v_list, bold=False, money=False):
    c.setFont('Helvetica-Bold' if bold else 'Helvetica', FS)
    for v, x in zip(v_list, x_cols): c.drawRightString(x + COL_W - 3, y, fmt(v, money))
    t = sum(v_list)
    c.drawRightString(x_tot + TOT_W - 3, y, fmt(t, money))
    if income_total: c.drawRightString(x_pct + PCT_W - 2, y, f'{t / income_total * 100:.2f}%' if abs(t) >= 0.005 else '')

y = header()
for r in ROWS:
    if y < 46:
        footer(); c.showPage(); page[0] += 1; y = header()
    kind = r[0]
    if kind == 'gap':
        y -= ROW_H * 0.6; continue
    label, ind = r[1], (r[2] if kind in ('h', 'l') else r[3])
    lx = M + 4 + ind * 11
    if kind == 'h':
        c.setFont('Helvetica', FS); c.drawString(lx, y, label)
    elif kind == 'l':
        v = vals([r[1]])
        c.setFont('Helvetica', FS); c.drawString(lx, y, r[3]); line_numbers(y, v)
    elif kind == 't':
        style = r[4]
        c.setLineWidth(0.6 if style == 'sub' else 0.9)
        c.line(x_cols[0] + 4, y + ROW_H - 2.5, RIGHT, y + ROW_H - 2.5)
        c.setFont('Helvetica-Bold', FS); c.drawString(lx, y, label)
        line_numbers(y, vals(r[2]), bold=True, money=True)
    elif kind == 'net':
        plus, minus = r[2]
        v = [a - b for a, b in zip(vals(plus), vals(minus))]
        grand = len(r) > 4 and r[4] == 'grand'
        c.setLineWidth(0.9); c.line(x_cols[0] + 4, y + ROW_H - 2.5, RIGHT, y + ROW_H - 2.5)
        c.setFont('Helvetica-Bold', FS + (0.6 if grand else 0)); c.drawString(lx, y, label)
        line_numbers(y, v, bold=True, money=True)
        if grand:
            c.setLineWidth(0.7); c.line(x_cols[0] + 4, y - 3, RIGHT, y - 3); c.line(x_cols[0] + 4, y - 4.6, RIGHT, y - 4.6)
            y -= 3
    y -= ROW_H
footer()
c.save()

inc = sum(vals(INCOME)); opx = sum(vals(OPEX)); oth = sum(vals(OTHER_EXP)); od = sum(vals(['Owner Draw']))
print(f'Wrote {OUT}  ({page[0]} page{"s" if page[0] > 1 else ""})')
print(f'  Income {inc:,.2f} | Opex {opx:,.2f} | Other {oth:,.2f} | Net Income {inc-opx-oth:,.2f} | Owner draws {od:,.2f} | After draws {inc-opx-oth-od:,.2f}')
