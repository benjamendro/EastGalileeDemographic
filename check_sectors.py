import json
import codecs
data=json.load(open('d:/Users/97252/Desktop/Benny/WORK/מרכז ידע/02-מסדי נתונים/01-רשויות/דמוגרפיה/Demography_Dashboard_Package/data.json', encoding='utf-8'))
with codecs.open('d:/Users/97252/Desktop/Benny/WORK/מרכז ידע/02-מסדי נתונים/01-רשויות/דמוגרפיה/Demography_Dashboard_Package/out.txt', 'w', encoding='utf-8') as f:
    for d in data:
        if d['sector'] != 'יהודי':
            f.write(f"{d['name']}: {d['sector']}\n")
