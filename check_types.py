import json
import codecs
data=json.load(open('d:/Users/97252/Desktop/Benny/WORK/מרכז ידע/02-מסדי נתונים/01-רשויות/דמוגרפיה/Demography_Dashboard_Package/data.json', encoding='utf-8'))
with codecs.open('d:/Users/97252/Desktop/Benny/WORK/מרכז ידע/02-מסדי נתונים/01-רשויות/דמוגרפיה/Demography_Dashboard_Package/check_types.txt', 'w', encoding='utf-8') as f:
    for d in data:
        if d['type_gross'] == 'לא ידוע':
            f.write(f"{d['name']}: {d['type_gross']}\n")
    
    # Also check if any authority is missing important data
    f.write("\nMissing Data Check:\n")
    for d in data:
        if not d.get('socio_index'):
            f.write(f"{d['name']} missing socio_index\n")
        if not d.get('Pop_Latest'):
            f.write(f"{d['name']} missing Pop_Latest\n")
