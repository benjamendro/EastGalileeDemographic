import json
data=json.load(open('d:/Users/97252/Desktop/Benny/WORK/מרכז ידע/02-מסדי נתונים/01-רשויות/דמוגרפיה/Demography_Dashboard_Package/data.json', encoding='utf-8'))
sectors = list(set([d.get('sector') for d in data]))
with open('d:/Users/97252/Desktop/Benny/WORK/מרכז ידע/02-מסדי נתונים/01-רשויות/דמוגרפיה/Demography_Dashboard_Package/sectors.txt', 'w', encoding='utf-8') as f:
    for s in sectors: f.write(str(s) + '\n')
