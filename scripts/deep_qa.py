import os
import json
import pandas as pd
import numpy as np

pkg_dir = r'd:\Users\97252\Desktop\Benny\WORK\מרכז ידע\02-מסדי נתונים\01-רשויות\דמוגרפיה\Demography_Dashboard_Package'
data_file = os.path.join(pkg_dir, 'data.json')

with open(data_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Raw files
f_2025 = os.path.join(pkg_dir, 'אוכלוסייה ביישובים שבהם 2,000 תושבים ויותר - אומדנים ארעיים לסוף דצמבר 2025.xlsx')
f_2023 = os.path.join(pkg_dir, '. אוכלוסייה ביישובים יהודים, לא-יהודים, ומעורבים, לפי אזור סטטיסטי, קבוצת אוכלוסייה, מין וגיל, 2023.xlsx')
f_socio = os.path.join(pkg_dir, 'p_libud_24.xlsx')
f_haredi = os.path.join(pkg_dir, 'נתוני חרדים.xlsx')

report = []
report.append("===================================")
report.append("  DEEP QA & QC PIPELINE TRACING")
report.append("===================================")

def verify_authority(semel, name, region):
    report.append(f"\n--- Tracing Authority: {name} (Code: {semel}) [{region}] ---")
    
    # 1. Fetch JSON data (Dashboard Representation)
    json_entry = next((d for d in data if d['SemelRashut'] == semel), None)
    if not json_entry:
        report.append(f"❌ FAILED: {name} not found in data.json")
        return
    
    report.append("1. DASHBOARD -> JSON VALUES")
    report.append(f"   Region Flag: {json_entry.get('region')} | Expected: {region}")
    report.append(f"   Population 2025: {json_entry.get('population')}")
    report.append(f"   Socio-Economic Index: {json_entry.get('socio_rank')}")
    report.append(f"   Migration Balance: {json_entry.get('migration_balance')}")
    report.append(f"   Haredi Population 2023: {json_entry.get('pop_haredim_2023')}")
    report.append(f"   Pop 0-14: {json_entry.get('pop_0_14')}")
    
    report.append("\n2. JSON -> RAW EXCEL TRACE")
    
    # Check 2025 Population & Migration
    try:
        df_25 = pd.read_excel(f_2025, sheet_name='אוכלוסייה ביישובים 2,000+', header=None, skiprows=8)
        raw_25 = df_25[df_25[1] == semel].iloc[0]
        pop_raw = raw_25[7]
        internal_mig = raw_25[5]
        intl_mig = raw_25[6]
        mig_calc = float(internal_mig if str(internal_mig).replace('.','').replace('-','').isdigit() else 0) + float(intl_mig if str(intl_mig).replace('.','').replace('-','').isdigit() else 0)
        
        report.append(f"   RAW Excel (2025 Pop): {pop_raw} -> Rounding match: {int(round(float(pop_raw))) == json_entry.get('population')}")
        report.append(f"   RAW Excel (Migration): Internal {internal_mig} + Intl {intl_mig} = {mig_calc} -> Match: {mig_calc == json_entry.get('migration_balance')}")
    except Exception as e:
        report.append(f"   Error fetching 2025 raw data: {e}")
        
    # Check Socio-Economic
    try:
        df_socio_raw = pd.read_excel(f_socio, sheet_name='נתונים פיזיים ונתוני אוכלוסייה ', header=None)
        raw_soc = df_socio_raw[df_socio_raw[1] == semel].iloc[0]
        socio_val = raw_soc[250]
        # In build_etl, socio is read directly and outputted
        if str(socio_val) == '..' or pd.isna(socio_val): socio_val = None
        else: socio_val = float(socio_val)
        json_socio = json_entry.get('socio_rank')
        report.append(f"   RAW Excel (Socio-Economic): {socio_val} -> Match: {socio_val == json_socio}")
    except Exception as e:
        report.append(f"   Error fetching Socio raw data: {e}")
        
    # Check Haredi
    try:
        df_h = pd.read_excel(f_haredi, sheet_name='חרדים ביישובים ', header=None, skiprows=13)
        raw_h = df_h[df_h[0] == semel]
        if not raw_h.empty:
            haredi_val = raw_h.iloc[0][3]
            haredi_val = float(haredi_val) if str(haredi_val).replace('.','').isdigit() else 0
        else:
            haredi_val = 0
        report.append(f"   RAW Excel (Haredim): {haredi_val} -> Match: {haredi_val == json_entry.get('pop_haredim_2023')}")
    except Exception as e:
        report.append(f"   Error fetching Haredi raw data: {e}")
        
    # Check 2023 Age
    try:
        dfs_23 = []
        for sheet in ['יישובים יהודים', 'יישובים לא יהודים', 'יישובים מעורבים']:
            df = pd.read_excel(f_2023, sheet_name=sheet, header=None, skiprows=12)
            dfs_23.append(df)
        df_23 = pd.concat(dfs_23)
        raw_23 = df_23[(df_23[1] == semel) & (df_23[3] == 'סה"כ')]
        if not raw_23.empty:
            age_0_4 = raw_23[5].sum()
            age_5_9 = raw_23[6].sum()
            age_10_14 = raw_23[7].sum()
            age_tot = float(age_0_4)+float(age_5_9)+float(age_10_14)
            report.append(f"   RAW Excel (Ages 0-14): {age_0_4} + {age_5_9} + {age_10_14} = {age_tot} -> Match: {age_tot == json_entry.get('pop_0_14')}")
        else:
            report.append("   RAW Excel (Ages): Not found in 2023 file.")
    except Exception as e:
        report.append(f"   Error fetching Age 2023 raw data: {e}")

# Run tests
verify_authority(2800, 'קריית שמונה', 'מזרחי')
verify_authority(9100, 'נהריה', 'מערבי')

with open(os.path.join(pkg_dir, 'scripts', 'qa_report_deep.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(report))

print("Deep QA completed. Report generated.")
