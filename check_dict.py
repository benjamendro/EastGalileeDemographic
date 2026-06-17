import pandas as pd
import json
import codecs
df_dict = pd.read_excel('d:/Users/97252/Desktop/Benny/WORK/מרכז ידע/02-מסדי נתונים/01-רשויות/דמוגרפיה/Demography_Dashboard_Package/מילון רשות מקומית + מטא דאטה.xlsx', sheet_name='רשימת הערכים')
with codecs.open('d:/Users/97252/Desktop/Benny/WORK/מרכז ידע/02-מסדי נתונים/01-רשויות/דמוגרפיה/Demography_Dashboard_Package/check_dict.txt', 'w', encoding='utf-8') as f:
    for _, row in df_dict.head(10).iterrows():
        f.write(f"{row['SemelRashut']} | {row['ShemRashut']} | {row.get('SemelSugMaamad')}\n")
