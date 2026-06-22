"""
build_etl.py — Config-driven ETL for the Galilee demography dashboard.

Single source of truth: config/eshkol_mapping.xlsx (the צימודים table).
Adding a cluster = adding rows there. NO code changes, NO hardcoded code lists.

Every source join is cross-validated on code AND name via EshkolMatcher
(skill §3.3 — CBS RC/locality code collisions). A validation gate runs before
output: on any hard error it prints a report and HALTS without writing data.json
(skill §1 — halt & request approval).
"""

import os
import sys
import json
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eshkol_matcher import EshkolMatcher, sanitize

sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root
SRC = os.path.join(ROOT, 'data', 'sources')
CONFIG = os.path.join(ROOT, 'data', 'config', 'eshkol_mapping.xlsx')

F_2025 = os.path.join(SRC, 'אוכלוסייה ביישובים שבהם 2,000 תושבים ויותר - אומדנים ארעיים לסוף דצמבר 2025.xlsx')
F_2023 = os.path.join(SRC, '. אוכלוסייה ביישובים יהודים, לא-יהודים, ומעורבים, לפי אזור סטטיסטי, קבוצת אוכלוסייה, מין וגיל, 2023.xlsx')
F_HAREDIM = os.path.join(SRC, 'נתוני חרדים.xlsx')
F_PLIBUD = os.path.join(SRC, 'p_libud_24.xlsx')
F_REGISTRY = os.path.join(SRC, 'residents_by_age_groups.csv')  # population registry, coarse age bands

# Registry age bands (irregular; do NOT mix with the 2023 5-year schema). 0-5 + 6-18 = 0-18.
REG_BANDS = [('reg_0_5', 'גיל_0_5'), ('reg_6_18', 'גיל_6_18'), ('reg_19_45', 'גיל_19_45'),
             ('reg_46_55', 'גיל_46_55'), ('reg_56_64', 'גיל_56_64'), ('reg_65p', 'גיל_65_פלוס')]

AGE_COLS = ['Age_0_4', 'Age_5_9', 'Age_10_14', 'Age_15_19', 'Age_20_24', 'Age_25_29',
            'Age_30_34', 'Age_35_39', 'Age_40_44', 'Age_45_49', 'Age_50_54', 'Age_55_59',
            'Age_60_64', 'Age_65_plus']
def region_label(cluster):
    """Short region label derived from the cluster name — no hardcoded list, so a
    new cluster row flows through with zero code changes. 'גליל מזרחי' -> 'מזרחי'."""
    if cluster is None or (isinstance(cluster, float) and pd.isna(cluster)):
        return None
    c = str(cluster).strip()
    prefix = 'גליל '
    return c[len(prefix):].strip() if c.startswith(prefix) else c

# --- regression baseline (QA-confirmed correct East cluster authority total) ---
EAST_AUTHORITY_TOTAL_EXPECTED = 196456
RECON_TOLERANCE = 0.01  # 1%
AGE_INFLATION_TOLERANCE = 1.05  # age-sum may exceed total by <5% (CBS rounding); >5% = real double-count


# ======================================================================
# Validation gate
# ======================================================================
class Gate:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    def report(self):
        print("\n" + "=" * 64)
        print("VALIDATION REPORT")
        print("=" * 64)
        if self.warnings:
            print(f"\n⚠  WARNINGS ({len(self.warnings)}):")
            for w in self.warnings:
                print("   -", w)
        if self.errors:
            print(f"\n✘  ERRORS ({len(self.errors)}):")
            for e in self.errors:
                print("   -", e)
        else:
            print("\n✓  No hard errors.")
        print("=" * 64)

    def halt_if_errors(self):
        if self.errors:
            print(f"\nHALTED: {len(self.errors)} validation error(s). data.json NOT written.")
            print("Resolve the errors above (data or config) and re-run. (skill §1)")
            sys.exit(1)


G = Gate()


def clean_value(v):
    """Treat CBS confidentiality markers ('..','-') and blanks as 0 (skill §4b)."""
    if pd.isna(v) or v in ('..', '-', ''):
        return 0.0
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0


# ======================================================================
# 1. Load config (single source of truth) + derive structure
# ======================================================================
matcher = EshkolMatcher(CONFIG)
T = matcher.targets.copy()
T['code'] = T['code'].astype(int)
cfg = pd.read_excel(CONFIG)
cfg['code'] = pd.to_numeric(cfg['קוד למס (סמל)'], errors='coerce').astype('Int64')
SECTOR = dict(zip(cfg['code'], cfg['מגזר']))
CLUSTER = dict(zip(cfg['code'], cfg['אשכול']))
FORM = dict(zip(cfg['code'], cfg['צורת יישוב']))
ENTITY = dict(zip(T['code'], T['entity_type']))
NAME = dict(zip(T['code'], T['eshkol_name']))

# Regional councils = authorities that parent at least one settlement (structural,
# config-driven). Cross-checked against the 'Regional Council Custom Map' method flag.
settle_affil = {sanitize(a) for a in T[T['entity_type'] == 'יישוב']['affiliation']}
rc_codes = set()
rc_name2code = {}
for _, r in T[T['entity_type'] == 'רשות'].iterrows():
    variants = {sanitize(r['eshkol_name']), sanitize(r['official_name'])}
    if variants & settle_affil:
        rc_codes.add(int(r['code']))
        for v in variants:
            rc_name2code[v] = int(r['code'])
method_rc = set(int(c) for c in T[T['method'] == 'Regional Council Custom Map']['code'])
if rc_codes != method_rc:
    G.warn(f"RC set (structural) {sorted(rc_codes)} != method-flag {sorted(method_rc)}")

# settlement -> parent RC
child_to_rc = {}
rc_to_children = {c: [] for c in rc_codes}
for _, r in T[T['entity_type'] == 'יישוב'].iterrows():
    rc = rc_name2code.get(sanitize(r['affiliation']))
    if rc is None:
        G.error(f"settlement '{r['eshkol_name']}' ({int(r['code'])}): affiliation "
                f"'{r['affiliation']}' does not resolve to a regional council")
    else:
        child_to_rc[int(r['code'])] = rc
        rc_to_children[rc].append(int(r['code']))

TARGET_CODES = set(T['code'].tolist())
print(f"Config loaded: {len(TARGET_CODES)} entities "
      f"({(T['entity_type']=='רשות').sum()} רשות, {(T['entity_type']=='יישוב').sum()} יישוב), "
      f"{len(rc_codes)} regional councils.")


def cross_validate(df, name_col, code_col, source):
    """Run matcher; push any code/name collisions to the gate as hard errors."""
    _, errs = matcher.match_dataframe(df, name_col=name_col, code_col=code_col)
    for e in errs:
        if e['issue'] == 'code_name_mismatch':
            G.error(f"[{source}] {e['detail']}")


# ======================================================================
# 2. 2023 detailed age/gender — UNIFIED reader (fixes mixed-city inflation)
# ======================================================================
def read_2023(path):
    specs = [('יישובים יהודים', False), ('יישובים לא יהודים', False), ('יישובים מעורבים', True)]
    frames = []
    for sheet, has_group in specs:
        df = pd.read_excel(path, sheet_name=sheet, header=None, skiprows=12)
        if has_group:
            # mixed sheet has an extra population-group col (3). The groups OVERLAP
            # (סה"כ ⊇ ישראלים ⊇ יהודים ...). Keep ONLY the 'סה"כ' group, else every
            # locality is counted ~5x — the bug that broke West.
            df = df[df[3].astype(str).str.strip() == 'סה"כ']
            cols = [0, 1, 2, 4, 5] + list(range(6, 20))   # name,code,area,gender,total,14 ages
        else:
            cols = [0, 1, 2, 3, 4] + list(range(5, 19))
        sub = df[cols].copy()
        sub.columns = ['Name', 'code', 'area', 'Gender', 'total'] + AGE_COLS
        sub = sub.dropna(subset=['code'])
        sub['code'] = pd.to_numeric(sub['code'], errors='coerce')
        sub = sub.dropna(subset=['code'])
        sub['code'] = sub['code'].astype(int)
        sub['Gender'] = sub['Gender'].astype(str).str.strip()
        sub = sub[sub['Gender'].isin(['סה"כ', 'זכר', 'נקבה'])]
        for c in ['total'] + AGE_COLS:
            sub[c] = sub[c].apply(clean_value)
        frames.append(sub)
    return pd.concat(frames, ignore_index=True)


raw23 = read_2023(F_2023)

# cross-validate names for the codes we care about (collision guard)
names23 = raw23[raw23['code'].isin(TARGET_CODES)].drop_duplicates('code')[['Name', 'code']]
cross_validate(names23, 'Name', 'code', '2023 ages')

# sum across statistical areas -> one row per (code, gender)
g23 = raw23.groupby(['code', 'Gender'])[['total'] + AGE_COLS].sum().reset_index()
tot23 = g23[g23['Gender'] == 'סה"כ'].set_index('code')
male23 = g23[g23['Gender'] == 'זכר'].set_index('code')
female23 = g23[g23['Gender'] == 'נקבה'].set_index('code')


def ages_2023(code):
    """Return (total_pop, age_total_dict, m_arr, f_arr) for a locality code, else None."""
    if code not in tot23.index:
        return None
    row = tot23.loc[code]
    ad = {c: float(row[c]) for c in AGE_COLS}
    m = [float(male23.loc[code][c]) for c in AGE_COLS] if code in male23.index else []
    f = [float(female23.loc[code][c]) for c in AGE_COLS] if code in female23.index else []
    return float(row['total']), ad, m, f


# ======================================================================
# 3. 2025 estimates (localities by code; regional councils by NAME)
# ======================================================================
loc25 = pd.read_excel(F_2025, sheet_name='אוכלוסייה ביישובים 2,000+', header=None, skiprows=8)
loc25 = loc25[[1, 2, 4, 5, 6, 7]].dropna(subset=[1])
loc25.columns = ['code', 'Name', 'Natural_Increase', 'Internal_Migration', 'International_Migration', 'Pop_2025']
loc25['code'] = pd.to_numeric(loc25['code'], errors='coerce')
loc25 = loc25.dropna(subset=['code'])
loc25['code'] = loc25['code'].astype(int)
cross_validate(loc25[loc25['code'].isin(TARGET_CODES)], 'Name', 'code', '2025 localities')

rc25 = pd.read_excel(F_2025, sheet_name='אוכלוסייה במועצות אזוריות', header=None, skiprows=8)
rc25 = rc25[[2, 4, 5, 6, 7]].dropna(subset=[2])
rc25.columns = ['Name', 'Natural_Increase', 'Internal_Migration', 'International_Migration', 'Pop_2025']
rc25['code'] = rc25['Name'].apply(lambda n: rc_name2code.get(sanitize(n)))
rc25 = rc25.dropna(subset=['code'])
rc25['code'] = rc25['code'].astype(int)
found_rc = set(rc25['code'])
for c in rc_codes:
    if c not in found_rc:
        G.error(f"regional council '{NAME[c]}' ({c}) not found by name in 2025 RC sheet")

est25 = pd.concat([loc25[['code', 'Natural_Increase', 'Internal_Migration', 'International_Migration', 'Pop_2025']],
                   rc25[['code', 'Natural_Increase', 'Internal_Migration', 'International_Migration', 'Pop_2025']]])
for c in ['Natural_Increase', 'Internal_Migration', 'International_Migration', 'Pop_2025']:
    est25[c] = est25[c].apply(clean_value)
est25 = est25.set_index('code')


# ======================================================================
# 4. Haredim 2023 (by code) + p_libud (socio / olim, authorities)
# ======================================================================
har = pd.read_excel(F_HAREDIM, sheet_name='חרדים ביישובים ', header=None, skiprows=13)
har = har[[0, 3]].dropna(subset=[0])
har.columns = ['code', 'Pop_Haredim']
har['code'] = pd.to_numeric(har['code'], errors='coerce')
har = har.dropna(subset=['code'])
har['code'] = har['code'].astype(int)
har['Pop_Haredim'] = har['Pop_Haredim'].apply(clean_value)
HAREDIM = har.groupby('code')['Pop_Haredim'].sum().to_dict()

pl = pd.read_excel(F_PLIBUD, sheet_name='נתונים פיזיים ונתוני אוכלוסייה ', header=None).iloc[4:]
#  col 1=code, 250=socio rank, 43=olim%, 10=area km², 11=density, 35=total fertility rate
pl = pl[[1, 250, 43, 10, 11, 35]].dropna(subset=[1])
pl.columns = ['code', 'Socio', 'Olim', 'Area', 'Density', 'TFR']
pl['code'] = pd.to_numeric(pl['code'], errors='coerce')
pl = pl.dropna(subset=['code'])
pl['code'] = pl['code'].astype(int)


def _num(x):
    try:
        return float(x)
    except (ValueError, TypeError):
        return None


SOCIO = {int(r['code']): _num(r['Socio']) for _, r in pl.iterrows()}
OLIM = {int(r['code']): (_num(r['Olim']) or 0) for _, r in pl.iterrows()}
AREA = {int(r['code']): _num(r['Area']) for _, r in pl.iterrows()}
DENSITY = {int(r['code']): _num(r['Density']) for _, r in pl.iterrows()}
TFR = {int(r['code']): _num(r['TFR']) for _, r in pl.iterrows()}

# --- Population registry: coarse age bands (separate measurement basis from the
# de-facto estimates; used ONLY for the condensed life-stage view + exact 0-18). ---
reg = pd.read_csv(F_REGISTRY, encoding='cp1255')
reg['code'] = pd.to_numeric(reg['סמל_ישוב'], errors='coerce')
reg = reg.dropna(subset=['code'])
reg['code'] = reg['code'].astype(int)
cross_validate(reg[reg['code'].isin(TARGET_CODES)], 'שם_ישוב', 'code', 'registry')
REG = {}
for _, r in reg.iterrows():
    rec = {field: clean_value(r[col]) for field, col in REG_BANDS}
    rec['reg_total'] = clean_value(r['סהכ'])
    REG[int(r['code'])] = rec


def registry(code):
    """Registry bands for a code: localities direct, RCs = sum of children."""
    if code in rc_codes:
        agg = {field: 0.0 for field, _ in REG_BANDS}
        agg['reg_total'] = 0.0
        for ch in rc_to_children[code]:
            d = REG.get(ch)
            if d:
                for k in agg:
                    agg[k] += d[k]
        return agg
    return REG.get(code)


# ======================================================================
# 5. Build per-entity records (config-driven) with RC aggregation
# ======================================================================
def get_2023(code):
    """Age/gender for a code: localities read directly, RCs = sum of children."""
    if code in rc_codes:
        children = rc_to_children[code]
        tot, ad, m, f = 0.0, {c: 0.0 for c in AGE_COLS}, [0.0] * 14, [0.0] * 14
        for ch in children:
            r = ages_2023(ch)
            if r:
                t, a, mm, ff = r
                tot += t
                for c in AGE_COLS:
                    ad[c] += a[c]
                for i in range(14):
                    if mm:
                        m[i] += mm[i]
                    if ff:
                        f[i] += ff[i]
        return tot, ad, m, f
    return ages_2023(code)


def haredim(code):
    if code in rc_codes:
        return sum(HAREDIM.get(ch, 0) for ch in rc_to_children[code])
    return HAREDIM.get(code, 0)


def type_gross(code):
    # Type comes straight from the config 'צורת יישוב' column (single source of truth).
    # RC override is a safety net; fallbacks only fire if the config is incomplete.
    if code in rc_codes:
        return 'מועצה אזורית'
    return FORM.get(code) or ('עירייה / מועצה מקומית' if ENTITY[code] == 'רשות' else 'לא ידוע')


records = []
for code in T['code'].tolist():
    r23 = get_2023(code)
    pop23 = r23[0] if r23 else 0.0
    ad = r23[1] if r23 else {c: 0.0 for c in AGE_COLS}
    m_arr = r23[2] if r23 else []
    f_arr = r23[3] if r23 else []

    e = est25.loc[code] if code in est25.index else None
    pop25 = float(e['Pop_2025']) if e is not None else 0.0
    natural = float(e['Natural_Increase']) if e is not None else 0.0
    migration = (float(e['Internal_Migration']) + float(e['International_Migration'])) if e is not None else 0.0

    if pop25 > 0:
        pop_latest, data_year = pop25, 2023 if pop23 <= 0 else 2025
        growth = ((pop25 / pop23) - 1) * 100 if pop23 > 0 else 0.0
        data_year = 2025
    else:
        pop_latest, data_year, growth = pop23, 2023, 0.0

    age_0_14 = ad['Age_0_4'] + ad['Age_5_9'] + ad['Age_10_14']
    age_15_64 = sum(ad[c] for c in AGE_COLS[3:13])
    age_65 = ad['Age_65_plus']
    dep = (age_0_14 + age_65) / age_15_64 if age_15_64 > 0 else 0.0

    # Inflation guard: real area/group double-counts are multiplicative (2x–5x).
    # Sub-5% gaps are inherent CBS rounding/confidentiality-suppression noise.
    age_sum = age_0_14 + age_15_64 + age_65
    if pop23 > 0 and age_sum > pop23 * AGE_INFLATION_TOLERANCE:
        G.error(f"'{NAME[code]}' ({code}): age-sum {age_sum:.0f} exceeds 2023 population "
                f"{pop23:.0f} by >{(AGE_INFLATION_TOLERANCE-1)*100:.0f}% (mixed/area double-count?)")
    if m_arr and f_arr:
        mf = sum(m_arr) + sum(f_arr)
        if mf > pop23 * AGE_INFLATION_TOLERANCE:
            G.error(f"'{NAME[code]}' ({code}): male+female {mf:.0f} exceeds total {pop23:.0f} by >5%")

    har_pop = haredim(code)
    is_auth = ENTITY[code] == 'רשות'
    authority = NAME[code] if is_auth else NAME[child_to_rc[code]]

    rd = registry(code) or {}
    reg_total = rd.get('reg_total', 0) or 0
    reg_0_18 = (rd.get('reg_0_5', 0) or 0) + (rd.get('reg_6_18', 0) or 0)
    if reg_total > 0 and reg_0_18 > reg_total * 1.001:
        G.error(f"'{NAME[code]}' ({code}): registry 0-18 {reg_0_18:.0f} exceeds registry total {reg_total:.0f}")

    records.append({
        'SemelRashut': code,
        'name': NAME[code],
        'region': region_label(CLUSTER.get(code)),
        'authority': authority,
        'sector': SECTOR.get(code, 'יהודי'),
        'type_gross': type_gross(code),
        'population': int(round(pop_latest)) if pop_latest > 0 else 0,
        'data_year': data_year,
        'pop_growth': growth,
        'migration_balance': migration,
        'natural_increase': natural,
        'immigrants_1990_pct': OLIM.get(code, 0) if is_auth else 0,
        'socio_rank': SOCIO.get(code) if is_auth else None,
        'pop_haredim_2023': har_pop,
        'haredi_pct': (har_pop / pop23 * 100) if pop23 > 0 else 0.0,
        'dependency_ratio': dep,
        'pop_0_14': age_0_14,
        'pop_15_64': age_15_64,
        'pop_65_plus': age_65,
        'ages': {'m': m_arr, 'f': f_arr},
        # p_libud extras (authority-level)
        'tfr': TFR.get(code) if is_auth else None,
        'area_sqkm': AREA.get(code) if is_auth else None,
        'density': DENSITY.get(code) if is_auth else None,
        # population-registry life-stage view (separate basis; 0-5+6-18 = 0-18 exact)
        'reg_total': int(round(reg_total)),
        'reg_0_18': int(round(reg_0_18)),
        'reg_bands': {
            '0-5': int(round(rd.get('reg_0_5', 0) or 0)),
            '6-18': int(round(rd.get('reg_6_18', 0) or 0)),
            '19-45': int(round(rd.get('reg_19_45', 0) or 0)),
            '46-55': int(round(rd.get('reg_46_55', 0) or 0)),
            '56-64': int(round(rd.get('reg_56_64', 0) or 0)),
            '65+': int(round(rd.get('reg_65p', 0) or 0)),
        },
    })


# ======================================================================
# 6. Reconciliation checks (the proof West is fixed)
# ======================================================================
def authority_total(region):
    # independent authorities + regional-council aggregates (no double count)
    return sum(r['population'] for r in records
               if r['region'] == region and (ENTITY[r['SemelRashut']] == 'רשות'))


east_auth = authority_total('מזרחי')
west_auth = authority_total('מערבי')
print(f"\nReconciliation:  East authorities = {east_auth:,}   West authorities = {west_auth:,}")

# Registry coverage: every settlement-level target should be present
reg_missing = [NAME[c] for c in TARGET_CODES if c not in rc_codes and c not in REG]
if reg_missing:
    G.warn(f"registry file missing {len(reg_missing)} settlement-level entities: {reg_missing[:8]}")
reg_0_18_all = sum(r['reg_0_18'] for r in records if ENTITY[r['SemelRashut']] == 'רשות')
print(f"Registry 0-18 (authorities, both clusters) = {reg_0_18_all:,}")
if abs(east_auth - EAST_AUTHORITY_TOTAL_EXPECTED) > EAST_AUTHORITY_TOTAL_EXPECTED * RECON_TOLERANCE:
    G.warn(f"East authority total {east_auth:,} deviates >1% from baseline {EAST_AUTHORITY_TOTAL_EXPECTED:,}")

# RC aggregate must equal sum of its children (settlements view)
for rc in rc_codes:
    agg = next(r['pop_0_14'] + r['pop_15_64'] + r['pop_65_plus'] for r in records if r['SemelRashut'] == rc)
    kids = sum((r['pop_0_14'] + r['pop_15_64'] + r['pop_65_plus']) for r in records
               if r['SemelRashut'] in rc_to_children[rc])
    if abs(agg - kids) > 1:
        G.error(f"RC '{NAME[rc]}' 2023 aggregate {agg:.0f} != sum of children {kids:.0f}")

G.report()
G.halt_if_errors()


# ======================================================================
# 7. Write data.json
# ======================================================================
out = os.path.join(ROOT, 'data', 'data.json')
with open(out, 'w', encoding='utf-8') as fh:
    json.dump(records, fh, ensure_ascii=False, indent=2)
print(f"\n✓ Wrote {len(records)} records -> {out}")
