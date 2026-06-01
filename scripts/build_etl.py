import pandas as pd
import os
import json
import numpy as np
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

EASTERN_GALILEE_CODES = [
    # Councils & Cities
    5501, 5555, 5502, 8000, 487, 5571, 4100, 26, 2034, 29, 43, 2800, 4203, 4001, 4201, 4502, 962, 4501,
    # Settlements
    77, 667, 35, 852, 303, 302, 356, 253, 453, 623, 357, 76, 443, 345, 380, 308, 596, 347, 416, 378, 408, 578, 385, 319, 1213, 1211, 329, 366, 1132,
    1115, 1064, 1067, 431, 1047, 1214, 1229, 605, 664, 1230, 607, 609, 688, 846, 1294, 1191, 1297, 1212, 546, 540, 368, 599, 527,
    730, 1253, 322, 2063, 2009, 1252, 1210, 732, 843, 372, 324, 861, 1285,
    4011, 4002, 4012, 4021, 4028, 4008, 4551, 4304, 4303, 4025, 4702, 4009, 4013, 4003, 4301, 4022, 4004, 4204, 4019, 4101, 4014, 4503, 4010, 4017, 4007, 4006, 4701, 4015, 4026, 4024, 4005
]

directory = r'd:\Users\97252\Desktop\Benny\WORK\מרכז ידע\02-מסדי נתונים\01-רשויות\דמוגרפיה'

def clean_value(val):
    if pd.isna(val) or val == '..' or val == '-': return 0
    try: return float(val)
    except: return 0

# 1. Load HTML mapping (for sector)
with open(os.path.join(directory, 'mapping.json'), 'r', encoding='utf-8') as f:
    html_mapping = json.load(f)

# 2. Parse skill markdown for exact settlement types and true authorities
skill_path = os.path.join(directory, 'work', 'eshkol_matching_skill.md')
eshkol_type_map = {}
eshkol_auth_map = {}
if os.path.exists(skill_path):
    with open(skill_path, 'r', encoding='utf-8') as f:
        skill_text = f.read()
    current_type = "לא ידוע"
    current_auth = None
    for line in skill_text.split('\n'):
        line = line.strip()
        if line.startswith('**') and line.endswith('**'):
            if ':' not in line and 'גליל מערבי' not in line and 'גליל מזרחי' not in line:
                current_auth = line.replace('*', '').strip()
        if 'מסוג' in line and ':' in line:
            match = re.search(r'מסוג\s+([^:]+):', line)
            if match: current_type = match.group(1).strip()
        elif '(' in line and ')' in line:
            codes = re.findall(r'\((\d+)\)', line)
            for code in codes:
                c = int(code)
                if current_type != "לא ידוע":
                    eshkol_type_map[c] = current_type
                if current_auth:
                    eshkol_auth_map[c] = current_auth

# 3. 2025 Estimates + Migration Data
df_2025_loc = pd.read_excel(os.path.join(directory, 'אוכלוסייה ביישובים שבהם 2,000 תושבים ויותר - אומדנים ארעיים לסוף דצמבר 2025.xlsx'), sheet_name='אוכלוסייה ביישובים 2,000+', header=None, skiprows=8)
df_2025_loc = df_2025_loc[[1, 4, 5, 6, 7]].dropna(subset=[1])

df_2025_rc = pd.read_excel(os.path.join(directory, 'אוכלוסייה ביישובים שבהם 2,000 תושבים ויותר - אומדנים ארעיים לסוף דצמבר 2025.xlsx'), sheet_name='אוכלוסייה במועצות אזוריות', header=None, skiprows=8)
df_2025_rc = df_2025_rc[[1, 4, 5, 6, 7]].dropna(subset=[1])

# QA Fix: map internal RC codes to 4-digit CBS codes to prevent overlaps with Locality codes
rc_code_map = {1: 5501, 2: 5502, 4: 5504, 52: 5552, 55: 5555, 71: 5571}
df_2025_rc[1] = df_2025_rc[1].map(rc_code_map)
df_2025_rc = df_2025_rc.dropna(subset=[1])

df_2025 = pd.concat([df_2025_loc, df_2025_rc])
df_2025.columns = ['SemelRashut', 'Natural_Increase', 'Internal_Migration', 'International_Migration', 'Pop_2025']
df_2025['SemelRashut'] = pd.to_numeric(df_2025['SemelRashut'], errors='coerce')
for col in ['Natural_Increase', 'Internal_Migration', 'International_Migration', 'Pop_2025']:
    df_2025[col] = df_2025[col].apply(clean_value)

# 4. 2023 Detailed (Age/Gender)
detailed_file = os.path.join(directory, '. אוכלוסייה ביישובים יהודים, לא-יהודים, ומעורבים, לפי אזור סטטיסטי, קבוצת אוכלוסייה, מין וגיל, 2023.xlsx')
dfs_2023 = []
for sheet in ['יישובים יהודים', 'יישובים לא יהודים', 'יישובים מעורבים']:
    df = pd.read_excel(detailed_file, sheet_name=sheet, header=None, skiprows=12)
    df = df[[0, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]].dropna(subset=[1])
    dfs_2023.append(df)

df_2023_full = pd.concat(dfs_2023)
df_names = df_2023_full[[0, 1]].drop_duplicates(subset=[1])
df_names.columns = ['ShemRashut_2023', 'SemelRashut']
df_names['SemelRashut'] = pd.to_numeric(df_names['SemelRashut'], errors='coerce')

cols = ['Name', 'SemelRashut', 'Gender', 'Pop_2023', 'Age_0_4', 'Age_5_9', 'Age_10_14', 'Age_15_19', 'Age_20_24', 'Age_25_29', 'Age_30_34', 'Age_35_39', 'Age_40_44', 'Age_45_49', 'Age_50_54', 'Age_55_59', 'Age_60_64', 'Age_65_plus']
df_2023_full.columns = cols
df_2023_full['SemelRashut'] = pd.to_numeric(df_2023_full['SemelRashut'], errors='coerce')
for col in cols[3:]:
    df_2023_full[col] = df_2023_full[col].apply(clean_value)

df_gender = df_2023_full[df_2023_full['Gender'].isin(['זכר', 'נקבה'])]
df_gender = df_gender.groupby(['SemelRashut', 'Gender'])[cols[4:]].sum().reset_index()

df_total = df_2023_full[df_2023_full['Gender'] == 'סה"כ']
df_total = df_total.groupby('SemelRashut')[cols[3:]].sum().reset_index()

# 5. 2023 Haredim
df_haredim = pd.read_excel(os.path.join(directory, 'נתוני חרדים.xlsx'), sheet_name='חרדים ביישובים ', header=None, skiprows=13)
df_haredim = df_haredim[[0, 3]].dropna(subset=[0])
df_haredim.columns = ['SemelRashut', 'Pop_Haredim']
df_haredim['SemelRashut'] = pd.to_numeric(df_haredim['SemelRashut'], errors='coerce')
df_haredim['Pop_Haredim'] = df_haredim['Pop_Haredim'].apply(clean_value)
df_haredim = df_haredim.groupby('SemelRashut').sum().reset_index()

# QA Fix: Aggregate 2023 data for Regional Councils
# Because RCs do not appear in the 2023 localities file, we sum their settlements
rc_names_to_codes = {'הגליל העליון': 5501, 'מבואות החרמון': 5555, 'מרום הגליל': 5502, 'גולן': 5571, 'מטה אשר': 5504, 'מעלה יוסף': 5552}
rc_aggregated_total = []
rc_aggregated_haredi = []
rc_aggregated_gender = []

for rc_name, rc_code in rc_names_to_codes.items():
    # Find all settlements that belong to this RC
    child_codes = [code for code, auth in eshkol_auth_map.items() if auth == rc_name]
    
    if child_codes:
        # Aggregate total
        subset_total = df_total[df_total['SemelRashut'].isin(child_codes)]
        if not subset_total.empty:
            agg_row = subset_total[cols[3:]].sum().to_dict()
            agg_row['SemelRashut'] = rc_code
            rc_aggregated_total.append(agg_row)
        
        # Aggregate haredim
        subset_haredi = df_haredim[df_haredim['SemelRashut'].isin(child_codes)]
        if not subset_haredi.empty:
            h_sum = subset_haredi['Pop_Haredim'].sum()
            rc_aggregated_haredi.append({'SemelRashut': rc_code, 'Pop_Haredim': h_sum})
            
        # Aggregate gender
        subset_gender = df_gender[df_gender['SemelRashut'].isin(child_codes)]
        for g in ['זכר', 'נקבה']:
            g_rows = subset_gender[subset_gender['Gender'] == g]
            if not g_rows.empty:
                g_agg = g_rows[cols[4:]].sum().to_dict()
                g_agg['SemelRashut'] = rc_code
                g_agg['Gender'] = g
                rc_aggregated_gender.append(g_agg)

if rc_aggregated_total: df_total = pd.concat([df_total, pd.DataFrame(rc_aggregated_total)], ignore_index=True)
if rc_aggregated_haredi: df_haredim = pd.concat([df_haredim, pd.DataFrame(rc_aggregated_haredi)], ignore_index=True)
if rc_aggregated_gender: df_gender = pd.concat([df_gender, pd.DataFrame(rc_aggregated_gender)], ignore_index=True)

# Calculate dependency ratio AFTER aggregating RCs
df_total['Age_0_14'] = df_total['Age_0_4'] + df_total['Age_5_9'] + df_total['Age_10_14']
df_total['Age_15_64'] = df_total['Age_15_19'] + df_total['Age_20_24'] + df_total['Age_25_29'] + df_total['Age_30_34'] + df_total['Age_35_39'] + df_total['Age_40_44'] + df_total['Age_45_49'] + df_total['Age_50_54'] + df_total['Age_55_59'] + df_total['Age_60_64']
df_total['Dependency_Ratio'] = np.where(df_total['Age_15_64'] > 0, (df_total['Age_0_14'] + df_total['Age_65_plus']) / df_total['Age_15_64'], 0)

# 6. Socio-Economic + Immigrants (p_libud)
df_plibud = pd.read_excel(os.path.join(directory, 'p_libud_24.xlsx'), sheet_name='נתונים פיזיים ונתוני אוכלוסייה ', header=None)
df_plibud_data = df_plibud.iloc[4:].copy()
col_code = 1
col_socio = 250
col_immigrants = 43 # אחוז עולי 1990+ מסך האוכלוסייה
df_socio = df_plibud_data[[col_code, col_socio, col_immigrants]].dropna(subset=[col_code])
df_socio.columns = ['SemelRashut', 'SocioEconomicIndex', 'Pct_Immigrants_1990']
df_socio['SemelRashut'] = pd.to_numeric(df_socio['SemelRashut'], errors='coerce')
df_socio['SocioEconomicIndex'] = df_socio['SocioEconomicIndex'].apply(lambda x: float(x) if str(x).replace('.','').isdigit() else np.nan)
df_socio['Pct_Immigrants_1990'] = df_socio['Pct_Immigrants_1990'].apply(lambda x: float(x) if str(x).replace('.','').isdigit() else 0)

# 7. Metadata Dictionary
df_dict = pd.read_excel(os.path.join(directory, 'מילון רשות מקומית + מטא דאטה.xlsx'), sheet_name='רשימת הערכים')
df_dict = df_dict[['SemelRashut', 'ShemRashut', 'SemelSugMaamad']]

# 8. Merge Everything
result_df = pd.DataFrame({'SemelRashut': EASTERN_GALILEE_CODES})
result_df = result_df.merge(df_dict, on='SemelRashut', how='left')
result_df = result_df.merge(df_names, on='SemelRashut', how='left')
result_df['ShemRashut'] = result_df['ShemRashut'].fillna(result_df['ShemRashut_2023']).str.strip()
result_df = result_df.drop('ShemRashut_2023', axis=1)
result_df = result_df.merge(df_2025, on='SemelRashut', how='left')
result_df = result_df.merge(df_total, on='SemelRashut', how='left')
result_df = result_df.merge(df_haredim, on='SemelRashut', how='left')
result_df = result_df.merge(df_socio, on='SemelRashut', how='left')

result_df['SocioEconomicIndex'] = np.where(result_df['SemelSugMaamad'].isin([1, 2, 3]), result_df['SocioEconomicIndex'], None)
# Assume immigrants pct is relevant for authorities (same as socio)
result_df['Pct_Immigrants_1990'] = np.where(result_df['SemelSugMaamad'].isin([1, 2, 3]), result_df['Pct_Immigrants_1990'], 0)

def determine_latest(row):
    pop25 = row['Pop_2025']
    pop23 = row['Pop_2023']
    if pd.notna(pop25) and pop25 > 0:
        growth = (pop25 / pop23) - 1 if pd.notna(pop23) and pop23 > 0 else 0
        return pd.Series([pop25, 2025, growth])
    else:
        return pd.Series([pop23, 2023, 0])

result_df[['Pop_Latest', 'Data_Year', 'Pop_Growth']] = result_df.apply(determine_latest, axis=1)
result_df = result_df.replace({np.nan: None})

# Now format into JSON list with all fields
json_output = []
for idx, row in result_df.iterrows():
    semel = row['SemelRashut']
    name = row['ShemRashut']
    if not name: name = 'לא ידוע'

    map_data = html_mapping.get(name, {})
    sector = map_data.get('sector', 'יהודי')
    
    # Hardcode RC type to fix Double Counting bug
    if semel in rc_code_map.values():
        type_gross = 'מועצה אזורית'
    else:
        type_gross = eshkol_type_map.get(semel)
        if not type_gross:
            type_gross = map_data.get('type_gross', 'לא ידוע')
            if type_gross == 'עירייה': type_gross = 'עירייה / מועצה מקומית'
    
    authority = eshkol_auth_map.get(semel)
    if not authority:
        authority = map_data.get('authority', name)

    m_row = df_gender[(df_gender['SemelRashut'] == semel) & (df_gender['Gender'] == 'זכר')]
    m_arr = m_row.iloc[0][cols[4:]].tolist() if not m_row.empty else []

    f_row = df_gender[(df_gender['SemelRashut'] == semel) & (df_gender['Gender'] == 'נקבה')]
    f_arr = f_row.iloc[0][cols[4:]].tolist() if not f_row.empty else []
        
    pop_latest = row['Pop_Latest'] or 0
    pop_latest = int(round(float(pop_latest))) if pop_latest > 0 else 0
    
    pop_2023 = row['Pop_2023'] or 0
    pop_haredim = row['Pop_Haredim'] or 0
    haredi_pct = (pop_haredim / pop_2023 * 100) if pop_2023 > 0 else 0
    
    migration_balance = (row['Internal_Migration'] or 0) + (row['International_Migration'] or 0)

    obj = {
        'SemelRashut': semel,
        'name': name,
        'authority': authority,
        'sector': sector,
        'type_gross': type_gross,
        'population': pop_latest,
        'data_year': row['Data_Year'],
        'pop_growth': (row['Pop_Growth'] or 0) * 100, 
        'migration_balance': migration_balance,
        'natural_increase': row['Natural_Increase'] or 0,
        'immigrants_1990_pct': row['Pct_Immigrants_1990'] or 0,
        'socio_rank': row['SocioEconomicIndex'],
        'pop_haredim_2023': pop_haredim,
        'haredi_pct': haredi_pct,
        'dependency_ratio': row['Dependency_Ratio'],
        'pop_0_14': row['Age_0_14'] or 0,
        'pop_15_64': row['Age_15_64'] or 0,
        'pop_65_plus': row['Age_65_plus'] or 0,
        'ages': { 'm': m_arr, 'f': f_arr }
    }
    json_output.append(obj)

output_path = os.path.join(directory, 'data.json')
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(json_output, f, ensure_ascii=False, indent=2)

print(f"Data successfully extracted and saved to {output_path}")
