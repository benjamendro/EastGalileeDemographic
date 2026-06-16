import os
import json
import pandas as pd

pkg_dir = r'd:\Users\97252\Desktop\Benny\WORK\מרכז ידע\02-מסדי נתונים\01-רשויות\דמוגרפיה\Demography_Dashboard_Package'
data_file = os.path.join(pkg_dir, 'data.json')

with open(data_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Loading raw Excel files... This may take a minute.")
f_2025 = os.path.join(pkg_dir, 'אוכלוסייה ביישובים שבהם 2,000 תושבים ויותר - אומדנים ארעיים לסוף דצמבר 2025.xlsx')
f_2023 = os.path.join(pkg_dir, '. אוכלוסייה ביישובים יהודים, לא-יהודים, ומעורבים, לפי אזור סטטיסטי, קבוצת אוכלוסייה, מין וגיל, 2023.xlsx')
f_socio = os.path.join(pkg_dir, 'p_libud_24.xlsx')
f_haredi = os.path.join(pkg_dir, 'נתוני חרדים.xlsx')

def clean_value(val):
    if pd.isna(val) or val == '..': return 0
    if isinstance(val, str):
        val = val.replace(',', '').replace(' ', '')
        if val == '-': return 0
    try:
        return float(val)
    except ValueError:
        return 0

# Load 2025 Pop
df_25_loc = pd.read_excel(f_2025, sheet_name='אוכלוסייה ביישובים 2,000+', header=None, skiprows=8)
df_25_loc = df_25_loc[[1, 5, 6, 7]].dropna(subset=[1])

df_25_rc = pd.read_excel(f_2025, sheet_name='אוכלוסייה במועצות אזוריות', header=None, skiprows=8)
df_25_rc = df_25_rc[[1, 5, 6, 7]].dropna(subset=[1])
rc_code_map = {1: 5501, 2: 5502, 4: 5504, 52: 5552, 55: 5555, 71: 5571}
df_25_rc[1] = df_25_rc[1].map(rc_code_map)
df_25_rc = df_25_rc.dropna(subset=[1])

df_25 = pd.concat([df_25_loc, df_25_rc])
df_25[1] = pd.to_numeric(df_25[1], errors='coerce')

# Load Socio
df_socio_raw = pd.read_excel(f_socio, sheet_name='נתונים פיזיים ונתוני אוכלוסייה ', header=None)
df_socio_raw[1] = pd.to_numeric(df_socio_raw[1], errors='coerce')

# Load Haredi
df_h = pd.read_excel(f_haredi, sheet_name='חרדים ביישובים ', header=None, skiprows=13)
df_h[0] = pd.to_numeric(df_h[0], errors='coerce')

# Load 2023 Ages
dfs_23 = []
for sheet in ['יישובים יהודים', 'יישובים לא יהודים', 'יישובים מעורבים']:
    df = pd.read_excel(f_2023, sheet_name=sheet, header=None, skiprows=12)
    dfs_23.append(df)
df_23 = pd.concat(dfs_23)
df_23[1] = pd.to_numeric(df_23[1], errors='coerce')
df_23_totals = df_23[df_23[3] == 'סה"כ']

# Iterate through ALL settlements in JSON and verify
errors = []
verified_count = 0

for item in data:
    semel = item['SemelRashut']
    name = item['name']
    
    # Check 2025
    raw_25 = df_25[df_25[1] == semel]
    if not raw_25.empty:
        r = raw_25.iloc[0]
        pop_raw = clean_value(r[7])
        mig_int = clean_value(r[5])
        mig_intl = clean_value(r[6])
        
        j_pop = item.get('population', 0)
        j_mig = item.get('migration_balance', 0)
        
        if abs(pop_raw - (j_pop or 0)) > 1:
            errors.append(f"[{name}] Pop 2025 mismatch: Raw={pop_raw}, JSON={j_pop}")
            
        mig_tot = mig_int + mig_intl
        if abs(mig_tot - (j_mig or 0)) > 1:
            errors.append(f"[{name}] Migration mismatch: Raw={mig_tot}, JSON={j_mig}")
            
    # Check Socio
    raw_soc = df_socio_raw[df_socio_raw[1] == semel]
    if not raw_soc.empty:
        soc_val = raw_soc.iloc[0][250]
        if str(soc_val) == '..' or pd.isna(soc_val): soc_val = None
        else: soc_val = float(soc_val)
        
        j_soc = item.get('socio_rank')
        if soc_val != j_soc:
            if not (soc_val is None and j_soc is None):
                errors.append(f"[{name}] Socio mismatch: Raw={soc_val}, JSON={j_soc}")

    # Check Haredi
    raw_h = df_h[df_h[0] == semel]
    if not raw_h.empty:
        h_val = clean_value(raw_h.iloc[0][3])
        j_h = item.get('pop_haredim_2023', 0)
        if abs(h_val - (j_h or 0)) > 1:
            errors.append(f"[{name}] Haredi mismatch: Raw={h_val}, JSON={j_h}")

    # Check Ages 2023
    if item.get('type_gross') != 'מועצה אזורית':
        raw_23_city = df_23_totals[df_23_totals[1] == semel]
        if not raw_23_city.empty:
            age_0_14_raw = clean_value(raw_23_city[5].sum()) + clean_value(raw_23_city[6].sum()) + clean_value(raw_23_city[7].sum())
            j_age_0_14 = item.get('pop_0_14', 0)
            if abs(age_0_14_raw - (j_age_0_14 or 0)) > 1:
                errors.append(f"[{name}] Age 0-14 mismatch: Raw={age_0_14_raw}, JSON={j_age_0_14}")
                
    verified_count += 1

with open(os.path.join(pkg_dir, 'scripts', 'exhaustive_qa_results.txt'), 'w', encoding='utf-8') as f:
    f.write(f"Total Authorities Verified: {verified_count}\n")
    f.write(f"Total Discrepancies Found: {len(errors)}\n")
    f.write("----------------------------------------\n")
    if errors:
        for e in errors:
            f.write(e + "\n")
    else:
        f.write("ALL DATA PERFECTLY MATCHES RAW EXCEL SOURCES.\n")

print(f"Exhaustive QA done. Found {len(errors)} errors across {verified_count} authorities.")
