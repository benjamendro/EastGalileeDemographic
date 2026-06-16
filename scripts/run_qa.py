import json
import pandas as pd
import os

pkg_dir = r'd:\Users\97252\Desktop\Benny\WORK\מרכז ידע\02-מסדי נתונים\01-רשויות\דמוגרפיה\Demography_Dashboard_Package'
data_file = os.path.join(pkg_dir, 'data.json')

with open(data_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

report = []
report.append("QA REPORT")
report.append("=========")
report.append(f"Total entities in data.json: {len(data)}")

# Separate councils vs settlements
councils = [d for d in data if d.get('type_gross') == 'מועצה אזורית']
others = [d for d in data if d.get('type_gross') != 'מועצה אזורית']

report.append(f"Regional Councils: {len(councils)}")
report.append(f"Settlements / Cities: {len(others)}")

# Target lists
eastern = [5501, 5555, 5502, 8000, 487, 5571, 4100, 26, 2034, 29, 43, 2800, 4203, 4001, 4201, 4502, 962, 4501]
western = [9100, 7600, 5504, 1063, 1292, 502, 473, 480, 5552, 507, 1296, 812, 496, 536, 485, 1263, 517, 518, 535]

data_codes = [d['SemelRashut'] for d in data]

missing_e = [c for c in eastern if c not in data_codes]
missing_w = [c for c in western if c not in data_codes]

report.append(f"Missing Eastern Galilee Authorities: {missing_e}")
report.append(f"Missing Western Galilee Authorities: {missing_w}")

report.append("\n--- Raw Data Validation ---")
try:
    df_2025_loc = pd.read_excel(os.path.join(pkg_dir, 'אוכלוסייה ביישובים שבהם 2,000 תושבים ויותר - אומדנים ארעיים לסוף דצמבר 2025.xlsx'), sheet_name='אוכלוסייה ביישובים 2,000+', header=None, skiprows=8)
    nahariya_raw = df_2025_loc[df_2025_loc[1] == 9100].iloc[0]
    nahariya_data = next((d for d in data if d['SemelRashut'] == 9100), None)

    if nahariya_data:
        pop_json = nahariya_data["population"]
        pop_raw = nahariya_raw[7]
        report.append(f"Nahariya (9100) -> JSON Pop: {pop_json} | Raw 2025 Pop: {pop_raw} | Match: {pop_json == pop_raw}")
    else:
        report.append("Nahariya NOT FOUND in JSON")
except Exception as e:
    report.append(f"Error reading Nahariya raw data: {e}")

try:
    df_2025_rc = pd.read_excel(os.path.join(pkg_dir, 'אוכלוסייה ביישובים שבהם 2,000 תושבים ויותר - אומדנים ארעיים לסוף דצמבר 2025.xlsx'), sheet_name='אוכלוסייה במועצות אזוריות', header=None, skiprows=8)
    rc_map = {1: 5501, 2: 5502, 4: 5504, 52: 5552, 55: 5555, 71: 5571}
    df_2025_rc[1] = df_2025_rc[1].map(rc_map)
    masher_raw = df_2025_rc[df_2025_rc[1] == 5504].iloc[0]
    masher_data = next((d for d in data if d['SemelRashut'] == 5504), None)

    if masher_data:
        pop_json = masher_data["population"]
        pop_raw = masher_raw[7]
        report.append(f"Mateh Asher (5504) -> JSON Pop: {pop_json} | Raw 2025 Pop: {pop_raw} | Match: {pop_json == pop_raw}")
    else:
        report.append("Mateh Asher NOT FOUND in JSON")
except Exception as e:
    report.append(f"Error reading Mateh Asher raw data: {e}")

# Look for anomalies (0 population)
zeros = [d['name'] for d in data if d.get('population', 0) == 0]
report.append(f"\nEntities with 0 population: {len(zeros)} -> {zeros[:5]}")

# Look for Type anomalies
unknowns = [d['name'] for d in data if d.get('type_gross') == 'לא ידוע']
report.append(f"Entities with Unknown Type: {len(unknowns)} -> {unknowns[:5]}")

print('\n'.join(report))
