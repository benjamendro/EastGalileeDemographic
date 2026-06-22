# דשבורד דמוגרפיה — אשכול גליל מזרחי ומערבי

דשבורד BI אינטראקטיבי לניתוח דמוגרפי של רשויות ויישובי אשכולות הגליל המזרחי והמערבי,
מבוסס נתוני הלשכה המרכזית לסטטיסטיקה (למ"ס). בנוי כאתר סטטי (HTML/JS) המוגש דרך GitHub Pages.

הדשבורד תומך בסינון מדורג (אשכול ← מועצה ← יישוב), פירמידת גילאים, התפלגות מורחבת/מצומצמת
לפי קבוצות גיל, מדדי תלות, פריון, מגזר, חרדים, הגירה ועוד.

## מבנה הריפו

```
.
├── dashboard/      # האתר המתפרסם (GitHub Pages). HTML + JS עצמאיים
│   ├── index.html
│   ├── data.js     # שכבת הנתונים המוזרקת (נוצרת ע"י etl/generate_dashboard.py)
│   ├── app.js
│   └── assets/     # לוגו, CSS מותג
├── data/
│   ├── sources/    # קובצי המקור של הלמ"ס (xlsx/csv) — לא נדרשים בזמן ריצה
│   ├── config/     # eshkol_mapping.xlsx — מקור האמת היחיד (רשימת הרשויות/יישובים)
│   └── data.json   # הפלט המצרפי של ה-ETL
├── etl/            # צינור הנתונים (Python)
│   ├── build_etl.py          # מסנן, מאמת ומאגד את כל המקורות -> data/data.json
│   ├── generate_dashboard.py # הופך את data.json ל-dashboard/
│   └── eshkol_matcher.py     # מודול ההתאמה (שם+קוד) עם עצירה על אי-התאמה
├── skills/
│   ├── demographic-dashboard/  # מיומנות: כל מה שצריך לבניית דשבורד מסוג זה (מערכת העיצוב RKCG)
│   └── eshkol-matching/        # מיומנות: לוגיקת הסינון/ההתאמה לשימוש חוזר בפרויקטים אחרים
├── docs/           # תיעוד
└── index.html      # הפניה (redirect) ל-dashboard/
```

## בנייה מחדש של הנתונים

```bash
pip install pandas openpyxl numpy
python etl/build_etl.py          # data/sources + data/config  ->  data/data.json
python etl/generate_dashboard.py # data/data.json              ->  dashboard/
```

ה-ETL **עוצר ומדווח** על כל אי-התאמה (קוד/שם, אוכלוסייה לא עקבית, מועצה אזורית ≠ סכום יישוביה)
ואינו כותב פלט עד שהבדיקות עוברות.

## הוספת אשכול/רשות חדשים — ללא שינוי קוד

מוסיפים שורות לקובץ `data/config/eshkol_mapping.xlsx` (שם, קוד למ"ס, אשכול, מגזר, צורת יישוב)
ומריצים מחדש את שני הסקריפטים. אין צורך לגעת בקוד.

## פרסום ל-GitHub Pages

1. ב-GitHub: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
2. ה-workflow שב-`.github/workflows/pages.yml` מפרסם אוטומטית את תיקיית `dashboard/`.
   הכתובת תהיה: `https://benjamendro.github.io/EastGalileeDemographic/`.

לחלופין: **Source: Deploy from a branch → main → / (root)**; קובץ ה-`index.html` שבשורש מפנה ל-`dashboard/`.

## מקורות נתונים

למ"ס: אומדני אוכלוסייה 2025 · גיל/מגדר 2023 · חרדים 2023 · קובץ רשויות מקומיות (p_libud) 2024 · מרשם אוכלוסין.
