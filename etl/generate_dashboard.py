import os
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root
data_dir = os.path.join(ROOT, 'data')
app_dir = os.path.join(ROOT, 'dashboard')   # published web app

if not os.path.exists(app_dir):
    os.makedirs(app_dir)

# 1. Load data.json
with open(os.path.join(data_dir, 'data.json'), 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

# 2. Split into settlements and regional councils
settlements = []
regional_councils = []
for row in raw_data:
    if row.get('type_gross') == 'מועצה אזורית':
        regional_councils.append(row)
    else:
        settlements.append(row)

# 3. Create data.js with window.DEMO_DATA
demo_data = {
    "ageLabels": ["0-4","5-9","10-14","15-19","20-24","25-29","30-34","35-39","40-44","45-49","50-54","55-59","60-64","65+"],
    "settlements": settlements,
    "regionalCouncils": regional_councils
}

with open(os.path.join(app_dir, 'data.js'), 'w', encoding='utf-8') as f:
    f.write("window.DEMO_DATA = " + json.dumps(demo_data, ensure_ascii=False) + ";")

# 4. Generate index.html
html_content = """<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>דשבורד דמוגרפיה גליל מזרחי ומערבי</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
    <link rel="stylesheet" href="assets/colors_and_type.css">
    <style>
        body { background-color: var(--egkc-bg-app); font-family: "Heebo", system-ui, sans-serif; }
        .chart-card { background-color: var(--egkc-surface); border-radius: var(--egkc-radius-lg); box-shadow: var(--egkc-shadow-sm); padding: 20px; }
        .chart-card-hover { transition: transform 0.2s ease, box-shadow 0.2s ease; }
        .chart-card-hover:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(0,0,0,0.05); }
        .table-container::-webkit-scrollbar { width: 8px; height: 8px; }
        .table-container::-webkit-scrollbar-thumb { background: var(--egkc-scrollbar); border-radius: 4px; }
        .table-container::-webkit-scrollbar-thumb:hover { background: var(--egkc-fg-faint); }
        select.egkc-select { background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2'><path d='m6 9 6 6 6-6'/></svg>"); background-repeat: no-repeat; background-position: left 10px center; padding-left: 28px; appearance: none; }
        .seg-toggle { display: inline-flex; background: var(--egkc-divider); border-radius: 6px; padding: 2px; }
        .seg-toggle button { padding: 4px 10px; font-size: 11px; border-radius: 4px; color: var(--egkc-fg-muted); font-weight: 500; transition: all 150ms ease; border: 0; background: transparent; cursor: pointer; }
        .seg-toggle button.active { background: #fff; box-shadow: 0 1px 2px rgba(0,0,0,.1); color: var(--egkc-accent); font-weight: 700; }
        .resolution-chip { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; color: var(--egkc-fg-muted); }
        .resolution-chip b { color: var(--egkc-accent); font-weight: 700; }
        #modal-overlay { transition: opacity 200ms ease; }
        .tab-active { border-bottom: 2px solid var(--egkc-accent); color: var(--egkc-accent); font-weight: 700; padding-bottom: 4px; }
        .tab-inactive { color: var(--egkc-fg-muted); padding-bottom: 4px; font-weight: 500; }
        .tab-inactive:hover { color: var(--egkc-fg); }
    </style>
</head>
<body class="text-slate-800 egkc-accent-cyan">
<div class="max-w-7xl mx-auto p-4 md:p-6 space-y-6 w-full">
    <header class="chart-card egkc-border-accent-edge flex flex-col md:flex-row justify-between items-center gap-4">
        <div class="flex items-center gap-4">
            <img src="assets/logo.jpg" alt="לוגו" class="h-16 w-auto">
            <div>
                <h1 class="egkc-h1" style="color:#183048;">דשבורד דמוגרפיה גליל מזרחי ומערבי</h1>
            </div>
        </div>
        <div id="kpi-row" class="flex gap-3 flex-wrap"></div>
    </header>

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <section class="lg:col-span-8 chart-card">
            <div class="flex flex-col md:flex-row gap-6">
                <aside class="w-full md:w-1/4 space-y-4 md:border-l md:pl-6 border-slate-100">
                    <h3 class="egkc-h2 flex items-center gap-2">
                        <span style="width:8px;height:8px;border-radius:50%;background:var(--egkc-accent);display:inline-block;"></span>
                        דמוגרפיה
                    </h3>
                    <div><label class="egkc-label block mb-1.5">אזור</label><select id="f-region" class="egkc-select w-full"><option value="all">כלל האשכול</option></select></div>
                    <div><label class="egkc-label block mb-1.5">רשות מוניציפלית</label><select id="f-authority" class="egkc-select w-full"><option value="all">כל הרשויות</option></select></div>
                    <div><label class="egkc-label block mb-1.5">מגזר</label><select id="f-sector" class="egkc-select w-full"><option value="all">כל המגזרים</option></select></div>
                    <div><label class="egkc-label block mb-1.5">צורת יישוב</label><select id="f-type" class="egkc-select w-full"><option value="all">כל הצורות</option></select></div>

                    <div class="pt-2 border-t border-slate-100"><label class="egkc-label block mb-1.5">יישוב ספציפי</label><select id="f-settlement" class="egkc-select w-full" style="background-color:var(--egkc-accent-soft);"><option value="all">כל היישובים</option></select></div>
                    <button id="reset-filters" class="egkc-link-accent mt-2">איפוס סינונים</button>
                    <div class="pt-4 border-t border-slate-100 resolution-chip"><span>רזולוציה:</span><b id="resolution-label">אשכול</b></div>
                </aside>
                <div class="w-full md:w-3/4 flex flex-col">
                    <div class="flex justify-between items-center mb-2 flex-wrap gap-2">
                        <h4 class="egkc-h3" id="pyramid-title">פירמידת גילים ומגדר</h4>
                        <div class="flex items-center gap-2">
                            <div class="seg-toggle" id="age-view"><button data-val="detailed" class="active">מורחב</button><button data-val="condensed">מצומצם</button></div>
                            <span id="pyramid-scope" class="px-2 py-0.5 text-xs rounded-full" style="background:var(--egkc-accent-soft);color:var(--egkc-accent-strong);"></span>
                        </div>
                    </div>
                    <div style="position:relative; min-height:360px; flex-grow:1;"><canvas id="chart-pyramid"></canvas></div>
                    <p id="pyramid-source" class="text-xs text-slate-500 mt-2 text-center">מקור: למ"ס - אוכלוסייה ברמת אזור סטטיסטי 2023 (התפלגות גיל ומגדר מפורטת)</p>
                </div>
            </div>
        </section>

        <section class="lg:col-span-4 space-y-4">
            <div class="chart-card chart-card-hover" style="height:300px;display:flex;flex-direction:column;">
                <div class="flex flex-col gap-2 mb-2">
                    <h3 class="egkc-h3 leading-tight">אוכלוסייה חרדית</h3>
                    <div class="flex justify-between items-center">
                        <div class="seg-toggle" id="haredi-scope"><button data-val="authorities" class="active">מועצות</button><button data-val="settlements">יישובים</button></div>
                        <div class="seg-toggle" id="haredi-metric"><button data-val="pct" class="active">%</button><button data-val="abs">מספר</button></div>
                    </div>
                </div>
                <div style="position:relative;flex-grow:1;width:100%;"><canvas id="chart-haredi"></canvas></div>
                <p class="text-xs text-slate-500 mt-2 text-center">מקור: למ"ס - חרדים 2023</p>
            </div>
            <div class="chart-card chart-card-hover" style="height:300px;display:flex;flex-direction:column;">
                <div class="flex justify-between items-start mb-2"><h3 class="egkc-h3">פילוח יישובים</h3></div>
                <div style="position:relative;flex-grow:1;width:100%;display:flex;justify-content:center;align-items:center;"><canvas id="chart-types"></canvas></div>
                <p class="text-xs text-slate-500 mt-2 text-center">מקור: מילון רשויות וצימודי אשכול</p>
            </div>
        </section>

        <section class="lg:col-span-12 chart-card">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                <!-- Row 1 -->
                <div>
                    <h3 class="egkc-h3 mb-2 flex items-center gap-2"><span style="width:6px;height:24px;background:var(--egkc-lime,#90c048);border-radius:2px;"></span>מדד סוציו-אקונומי (רשויות)</h3>
                    <div style="height:260px;position:relative;"><canvas id="chart-socio"></canvas></div>
                    <p class="text-xs text-slate-500 mt-2 text-center">מקור: למ"ס - מדד סוציו-אקונומי (קובץ רשויות מקומיות 2024)</p>
                </div>
                <div>
                    <h3 class="egkc-h3 mb-2 flex items-center gap-2"><span style="width:6px;height:24px;background:#48c0f0;border-radius:2px;"></span>גידול אוכלוסייה % (רשויות)</h3>
                    <div style="height:260px;position:relative;"><canvas id="chart-growth"></canvas></div>
                    <p class="text-xs text-slate-500 mt-2 text-center">מקור: למ"ס - אומדנים ארעיים לסוף דצמבר 2025</p>
                    <p class="text-[10px] text-slate-400 mt-0.5 text-center leading-tight">אופן חישוב: (אוכלוסיית 2025 חלקי אוכלוסיית 2023) פחות 1</p>
                </div>
                <!-- Row 2 -->
                <div class="mt-4">
                    <h3 class="egkc-h3 mb-2 flex items-center gap-2"><span style="width:6px;height:24px;background:#c0a860;border-radius:2px;"></span>מאזן הגירה מוחלט (רשויות)</h3>
                    <div style="height:260px;position:relative;"><canvas id="chart-migration"></canvas></div>
                    <p class="text-xs text-slate-500 mt-2 text-center">מקור: למ"ס - אומדנים ארעיים לסוף דצמבר 2025</p>
                    <p class="text-[10px] text-slate-400 mt-0.5 text-center leading-tight">אופן חישוב: חיבור מאזן הגירה פנימית + מאזן הגירה בינלאומית</p>
                </div>
                <div class="mt-4">
                    <h3 class="egkc-h3 mb-2 flex items-center gap-2"><span style="width:6px;height:24px;background:#1878a8;border-radius:2px;"></span>אחוז עולי 1990+ (רשויות)</h3>
                    <div style="height:260px;position:relative;"><canvas id="chart-immigrants"></canvas></div>
                    <p class="text-xs text-slate-500 mt-2 text-center">מקור: למ"ס - אוכלוסייה ופיזי (קובץ רשויות מקומיות 2024)</p>
                </div>
                <!-- Row 3 (Age & Dep 2x2 block starts here) -->
                <div class="mt-4">
                    <div class="flex justify-between items-center mb-2">
                        <h3 class="egkc-h3 flex items-center gap-2"><span style="width:6px;height:24px;background:#18a8c0;border-radius:2px;"></span>אוכלוסייה צעירה (0-14)</h3>
                        <div class="seg-toggle" id="age-young-metric"><button data-val="pct" class="active">%</button><button data-val="abs">מספר</button></div>
                    </div>
                    <div style="height:260px;position:relative;"><canvas id="chart-age-young"></canvas></div>
                    <p class="text-[10px] text-slate-400 mt-1 text-center leading-tight">אופן חישוב: אוכלוסיית 0-14 כאחוז מסך האוכלוסייה בעלת נתוני גיל (מקור: למ"ס 2023)</p>
                </div>
                <div class="mt-4">
                    <div class="flex justify-between items-center mb-2">
                        <h3 class="egkc-h3 flex items-center gap-2"><span style="width:6px;height:24px;background:#90c048;border-radius:2px;"></span>בגילאי עבודה (15-64)</h3>
                        <div class="seg-toggle" id="age-work-metric"><button data-val="pct" class="active">%</button><button data-val="abs">מספר</button></div>
                    </div>
                    <div style="height:260px;position:relative;"><canvas id="chart-age-work"></canvas></div>
                    <p class="text-[10px] text-slate-400 mt-1 text-center leading-tight">אופן חישוב: אוכלוסיית 15-64 כאחוז מסך האוכלוסייה בעלת נתוני גיל (מקור: למ"ס 2023)</p>
                </div>
                <!-- Row 4 -->
                <div class="mt-4">
                    <div class="flex justify-between items-center mb-2">
                        <h3 class="egkc-h3 flex items-center gap-2"><span style="width:6px;height:24px;background:#c0a860;border-radius:2px;"></span>אוכלוסייה ותיקה (65+)</h3>
                        <div class="seg-toggle" id="age-old-metric"><button data-val="pct" class="active">%</button><button data-val="abs">מספר</button></div>
                    </div>
                    <div style="height:260px;position:relative;"><canvas id="chart-age-old"></canvas></div>
                    <p class="text-[10px] text-slate-400 mt-1 text-center leading-tight">אופן חישוב: אוכלוסיית 65+ כאחוז מסך האוכלוסייה בעלת נתוני גיל (מקור: למ"ס 2023)</p>
                </div>
                <div class="mt-4">
                    <div class="flex justify-between items-center mb-2">
                        <h3 class="egkc-h3 flex items-center gap-2"><span style="width:6px;height:24px;background:#903078;border-radius:2px;"></span>יחס תלות (רשויות)</h3>
                        <div class="seg-toggle" id="dep-metric"><button data-val="ratio" class="active">יחסי</button><button data-val="per100">ל-100 תושבים</button></div>
                    </div>
                    <div style="height:260px;position:relative;"><canvas id="chart-dependency"></canvas></div>
                    <p class="text-xs text-slate-500 mt-2 text-center">מקור: למ"ס - דמוגרפיה 2023</p>
                    <p class="text-[10px] text-slate-400 mt-0.5 text-center leading-tight">אופן חישוב: אוכלוסייה תלויה חלקי אוכלוסייה בגילאי עבודה</p>
                </div>
                <!-- Row 5 -->
                <div class="mt-4">
                    <h3 class="egkc-h3 mb-2 flex items-center gap-2"><span style="width:6px;height:24px;background:#186078;border-radius:2px;"></span>שיעור פריון כולל (רשויות)</h3>
                    <div style="height:260px;position:relative;"><canvas id="chart-tfr"></canvas></div>
                    <p class="text-xs text-slate-500 mt-2 text-center">מקור: למ"ס - קובץ רשויות מקומיות 2024</p>
                    <p class="text-[10px] text-slate-400 mt-0.5 text-center leading-tight">מספר ילדים ממוצע לאישה. רמת תחלופה ≈ 2.1. מוצג עבור רשויות שעבורן קיים נתון</p>
                </div>
                <div class="mt-4">
                    <h3 class="egkc-h3 mb-2 flex items-center gap-2"><span style="width:6px;height:24px;background:#c0a860;border-radius:2px;"></span>צפיפות אוכלוסייה (רשויות)</h3>
                    <div style="height:260px;position:relative;"><canvas id="chart-density"></canvas></div>
                    <p class="text-xs text-slate-500 mt-2 text-center">מקור: למ"ס - קובץ רשויות מקומיות 2024</p>
                    <p class="text-[10px] text-slate-400 mt-0.5 text-center leading-tight">תושבים לקמ"ר. מוצג עבור יישובים המונים 5,000 תושבים ויותר</p>
                </div>

            </div>
        </section>

        <!-- TABLE -->
        <section class="lg:col-span-12 chart-card" style="padding:0;overflow:hidden;">
            <div class="p-4 border-b border-slate-100 flex flex-col md:flex-row justify-between items-center gap-4" style="background:var(--egkc-bg-app);">
                <div class="flex gap-5" id="tab-row">
                    <button class="tab-active" data-tab="authorities">טבלת רשויות</button>
                    <button class="tab-inactive" data-tab="settlements">כל היישובים</button>
                    <button class="tab-inactive" data-tab="haredi">יישובים עם חרדים</button>
                </div>
                <input id="table-search" type="text" placeholder="חיפוש..." class="egkc-input w-64">
            </div>
            <div class="overflow-auto table-container" style="max-height:460px;">
                <table id="data-table" class="egkc-data-table w-full"></table>
            </div>
        </section>
    </div>

    <footer class="text-center p-6 egkc-footer-attr leading-relaxed">
        המידע עובד על ידי מרכז ידע אזורי גליל מזרחי | מערבי.<br>
        מקור הנתונים: הלשכה המרכזית לסטטיסטיקה (אומדני אוכלוסייה 2025, ונתוני גילאים/חרדים נכון ל-2023).<br>
        <span class="text-slate-400" style="font-size:11px;">הערה מתודולוגית: נתונים מסוימים הושמטו מהספירה הכוללת עקב חסיון סטטיסטי של הלמ"ס (ערכים הקטנים או שווים ל-3 תושבים). נתוני האוכלוסייה הכוללת מעודכנים לסוף 2025 (אומדן ארעי); פילוחי גיל, מגדר, יחס תלות וחרדים מבוססים על נתוני סוף 2023; מדד "ילדים ונוער 0-18" והתצוגה המצומצמת מבוססים על מרשם האוכלוסין (בסיס מדידה רחב יותר מאומדני האוכלוסייה ולכן אינו בר-השוואה ישירה); פריון, שטח וצפיפות מתוך קובץ הרשויות המקומיות 2024.</span>
    </footer>
</div>

<div id="types-modal" class="hidden fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm" style="opacity:0; transition: opacity 200ms;">
    <div class="bg-white rounded-xl shadow-2xl w-full max-w-lg flex flex-col overflow-hidden transform scale-95 transition-transform">
        <div class="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
            <h3 class="egkc-h3" id="types-modal-title">יישובים</h3>
            <button onclick="closeTypesModal()" class="text-slate-400 hover:text-slate-600 transition-colors">
                <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"></path></svg>
            </button>
        </div>
        <div class="p-4 max-h-96 overflow-y-auto">
            <ul id="types-modal-list" class="space-y-2"></ul>
        </div>
    </div>
</div>
<script>
    function closeTypesModal() {
        const m = document.getElementById("types-modal");
        m.style.opacity = 0;
        setTimeout(() => { m.classList.add("hidden"); }, 200);
    }
</script>
<script src="data.js"></script>
<script src="app.js"></script>
</body>
</html>
"""

with open(os.path.join(app_dir, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(html_content)

# 5. Generate app.js
app_js_content = """(function () {
    "use strict";
    const D = window.DEMO_DATA;
    // Reverse age arrays so 0-4 is first (bottom) and 65+ is last (top)
    const AGES = D.ageLabels.slice().reverse();
    const SETTLEMENTS = D.settlements;
    const RCS = D.regionalCouncils;
    const INDEP_TYPES = ["עירייה", "מועצה מקומית", "עירייה / מועצה מקומית"];
    const AUTHORITIES = [...SETTLEMENTS.filter(s => INDEP_TYPES.includes(s.type_gross)), ...RCS];

    const C = {
        accent: "#18a8c0", magenta: "#903078", lime: "#90c048", gold: "#c0a860",
        navy: "#183048", blue: "#1878a8", sky: "#48c0f0", slate: "#94a3b8",
        qual: ["#18a8c0","#903078","#1878a8","#90c048","#c0a860","#183048","#48c0f0","#186078","#78c0f0","#d77b3a"]
    };
    const FONT = { family: "Heebo" };

    const state = {
        region: "all", authority: "all", sector: "all", type: "all", settlement: "all",
        search: "", tab: "authorities", harediScope: "authorities", harediMetric: "pct", depMetric: "ratio",
        ageYoungMetric: "pct", ageWorkMetric: "pct", ageOldMetric: "pct", ageView: "detailed"
    };
    // Registry life-stage bands (condensed view), youngest first
    const REG_BANDS = ["0-5","6-18","19-45","46-55","56-64","65+"];
    const REG_BAND_LABELS = { "0-5":"גיל הרך (0-5)","6-18":"בית ספר (6-18)","19-45":"צעירים (19-45)","46-55":"ביניים (46-55)","56-64":"טרום פרישה (56-64)","65+":"ותיקים (65+)" };

    const fmt = {
        int: v => (v==null||isNaN(v)) ? "—" : Math.round(v).toLocaleString("he-IL"),
        pct1: v => (v==null||isNaN(v)) ? "—" : v.toFixed(1) + "%",
    };

    function filtered() {
        return SETTLEMENTS.filter(s =>
            (state.region === "all" || s.region === state.region) &&
            (state.authority === "all" || s.authority === state.authority) &&
            (state.sector === "all" || s.sector === state.sector) &&
            (state.type === "all" || s.type_gross === state.type) &&
            (state.settlement === "all" || s.name === state.settlement)
        );
    }

    function filteredAuthorities() {
        return AUTHORITIES.filter(s => state.region === "all" || s.region === state.region);
    }

    function initFilters() {
        const fill = (id, items, allLabel) => document.getElementById(id).innerHTML = `<option value="all">${allLabel}</option>` + items.map(i => `<option value="${i}">${i}</option>`).join("");

        // Region options come from the data, not a hardcoded list — a new cluster
        // appears automatically once its rows are added to the config table.
        const regions = [...new Set(SETTLEMENTS.concat(RCS).map(s => s.region).filter(Boolean))].sort((a,b)=>a.localeCompare(b,"he"));
        fill("f-region", regions, "כלל האשכול");
        document.getElementById("f-region").value = state.region;

        const updateCascading = () => {
            const regPool = SETTLEMENTS.filter(s => state.region === "all" || s.region === state.region);
            
            const auths = [...new Set(regPool.map(s => s.authority))].sort((a,b)=>a.localeCompare(b,"he"));
            if (!auths.includes(state.authority)) state.authority = "all";
            fill("f-authority", auths, "כל הרשויות");
            document.getElementById("f-authority").value = state.authority;
            
            const authPool = regPool.filter(s => state.authority === "all" || s.authority === state.authority);
            
            const sectors = [...new Set(authPool.map(s => s.sector))].sort((a,b)=>a.localeCompare(b,"he"));
            if (!sectors.includes(state.sector)) state.sector = "all";
            fill("f-sector", sectors, "כל המגזרים");
            document.getElementById("f-sector").value = state.sector;
            
            const secPool = authPool.filter(s => state.sector === "all" || s.sector === state.sector);
            const types = [...new Set(secPool.map(s => s.type_gross))].sort((a,b)=>a.localeCompare(b,"he"));
            if (!types.includes(state.type)) state.type = "all";
            fill("f-type", types, "כל הצורות");
            document.getElementById("f-type").value = state.type;
            
            const finalPool = secPool.filter(s => state.type === "all" || s.type_gross === state.type).map(s=>s.name).sort();
            if (!finalPool.includes(state.settlement)) state.settlement = "all";
            fill("f-settlement", finalPool, "כל היישובים");
            document.getElementById("f-settlement").value = state.settlement;
        };

        updateCascading();

        const bindChange = (id, key) => {
            document.getElementById(id).addEventListener("change", e => {
                state[key] = e.target.value; 
                if(key !== "settlement") updateCascading(); 
                render();
            });
        };
        bindChange("f-region", "region");
        bindChange("f-authority", "authority"); 
        bindChange("f-sector", "sector"); 
        bindChange("f-type", "type"); 
        bindChange("f-settlement", "settlement");

        document.getElementById("reset-filters").addEventListener("click", e => {
            e.preventDefault();
            Object.assign(state, { region:"all", authority:"all", sector:"all", type:"all", settlement:"all" });
            document.getElementById("f-region").value = "all";
            document.getElementById("f-authority").value = "all";
            updateCascading(); render();
        });

        document.getElementById("table-search").addEventListener("input", e => { state.search = e.target.value; renderTable(); });
        document.querySelectorAll("#tab-row button").forEach(b => b.addEventListener("click", () => {
            state.tab = b.dataset.tab;
            document.querySelectorAll("#tab-row button").forEach(x => x.className = x.dataset.tab===state.tab ? "tab-active" : "tab-inactive");
            renderTable();
        }));

        const bindToggle = (groupId, cb) => {
            const group = document.getElementById(groupId);
            group.querySelectorAll("button").forEach(btn => btn.addEventListener("click", () => {
                group.querySelectorAll("button").forEach(b => b.classList.remove("active"));
                btn.classList.add("active"); cb(btn.dataset.val);
            }));
        };
        bindToggle("haredi-scope", v => { state.harediScope = v; chartHaredi(); });
        bindToggle("haredi-metric", v => { state.harediMetric = v; chartHaredi(); });
        bindToggle("dep-metric", v => { state.depMetric = v; renderDependency(); });
        bindToggle("age-view", v => { state.ageView = v; chartPyramid(); });
        bindToggle("age-young-metric", v => { state.ageYoungMetric = v; renderAgeCharts(); });
        bindToggle("age-work-metric", v => { state.ageWorkMetric = v; renderAgeCharts(); });
        bindToggle("age-old-metric", v => { state.ageOldMetric = v; renderAgeCharts(); });
    }

    function renderKPIs() {
        const rows = filtered();
        const totalPop = rows.reduce((a,s)=>a+s.population,0);
        const count = rows.length;
        
        const sum014 = rows.reduce((a,s)=>a+(s.pop_0_14||0),0);
        const sum1564 = rows.reduce((a,s)=>a+(s.pop_15_64||0),0);
        const sum65p = rows.reduce((a,s)=>a+(s.pop_65_plus||0),0);
        const knownAgesPop = sum014 + sum1564 + sum65p;
        const pct014 = knownAgesPop ? (sum014 / knownAgesPop * 100) : 0;
        const pct1564 = knownAgesPop ? (sum1564 / knownAgesPop * 100) : 0;
        const pct65p = knownAgesPop ? (sum65p / knownAgesPop * 100) : 0;

        // 0-18 from the population registry (0-5 + 6-18). Separate basis -> labelled מרשם.
        const sum018 = rows.reduce((a,s)=>a+(s.reg_0_18||0),0);
        const sumRegTot = rows.reduce((a,s)=>a+(s.reg_total||0),0);
        const pct018 = sumRegTot ? (sum018 / sumRegTot * 100) : 0;

        document.getElementById("kpi-row").innerHTML = `
            <div class="egkc-kpi-card egkc-kpi-tinted"><div class="egkc-kpi-numeral">${fmt.int(totalPop)}</div><div class="egkc-kpi-label">סה״כ אוכלוסייה</div></div>
            <div class="egkc-kpi-card"><div class="egkc-kpi-numeral" style="color:#475569;">${fmt.int(count)}</div><div class="egkc-kpi-label">יישובים</div></div>
            <div class="egkc-kpi-card"><div class="egkc-kpi-numeral" style="color:#903078;">${fmt.pct1(pct018)}</div><div class="egkc-kpi-label">ילדים ונוער 0-18 &bull; ${fmt.int(sum018)}<br><span style="font-size:9px;opacity:.7;">מרשם אוכלוסין</span></div></div>
            <div class="egkc-kpi-card"><div class="egkc-kpi-numeral" style="color:#18a8c0;">${fmt.pct1(pct014)}</div><div class="egkc-kpi-label">צעירים (0-14) &bull; ${fmt.int(sum014)}</div></div>
            <div class="egkc-kpi-card"><div class="egkc-kpi-numeral" style="color:#90c048;">${fmt.pct1(pct1564)}</div><div class="egkc-kpi-label">עבודה (15-64) &bull; ${fmt.int(sum1564)}</div></div>
            <div class="egkc-kpi-card"><div class="egkc-kpi-numeral" style="color:#c0a860;">${fmt.pct1(pct65p)}</div><div class="egkc-kpi-label">ותיקים (65+) &bull; ${fmt.int(sum65p)}</div></div>
        `;
        const scope = state.settlement!=="all" ? state.settlement : state.authority!=="all" ? state.authority : "כלל האשכול";
        document.getElementById("pyramid-scope").textContent = scope;
        
        let label = "אשכול";
        if (state.settlement !== "all") label = "יישוב";
        else if (state.authority !== "all") label = "רשות";
        else if (state.sector !== "all" || state.type !== "all") label = "פילוח";
        document.getElementById("resolution-label").textContent = label;
    }

    const charts = {};
    const kill = n => { if (charts[n]) { charts[n].destroy(); delete charts[n]; } };

    function setPyramidChrome() {
        const detailed = state.ageView === "detailed";
        document.getElementById("pyramid-title").textContent = detailed ? "פירמידת גילים ומגדר" : "התפלגות לפי קבוצות גיל (מורחב/מצומצם)";
        document.getElementById("pyramid-source").textContent = detailed
            ? 'מקור: למ"ס - אוכלוסייה ברמת אזור סטטיסטי 2023 (התפלגות גיל ומגדר מפורטת)'
            : 'מקור: מרשם אוכלוסין, למ"ס (קבוצות גיל מצומצמות; בסיס מדידה שונה מאומדני האוכלוסייה)';
    }

    function chartPyramid() {
        kill("pyramid");
        setPyramidChrome();
        const rows = filtered();
        if (state.ageView === "condensed") { return chartLifeStages(rows); }
        // Since AGES is reversed, we reverse the data arrays as well
        const m = AGES.map((_,i)=>{
            const origIndex = D.ageLabels.length - 1 - i;
            return rows.reduce((a,s)=>a+(s.ages.m[origIndex]||0),0);
        });
        const f = AGES.map((_,i)=>{
            const origIndex = D.ageLabels.length - 1 - i;
            return rows.reduce((a,s)=>a+(s.ages.f[origIndex]||0),0);
        });
        charts.pyramid = new Chart(document.getElementById("chart-pyramid"), {
            type: "bar",
            data: {
                labels: AGES,
                datasets: [
                    { label:"גברים", data:m.map(v=>-v), backgroundColor:C.accent, borderRadius:2 },
                    { label:"נשים", data:f, backgroundColor:C.magenta, borderRadius:2 },
                ]
            },
            options: {
                indexAxis:"y", responsive:true, maintainAspectRatio:false,
                scales:{
                    x:{ stacked:false, ticks:{ font:FONT, color:"#94a3b8", callback:v=>fmt.int(Math.abs(v)) }, grid:{ color:"#f1f5f9" } },
                    y:{ stacked:true, ticks:{ font:FONT, color:"#475569" }, grid:{ display:false } }
                },
                plugins:{ legend:{ position:"bottom", labels:{ font:FONT } }, tooltip:{ callbacks:{ label:c=>`${c.dataset.label}: ${fmt.int(Math.abs(c.parsed.x))}` } } }
            }
        });
    }

    function chartLifeStages(rows) {
        const order = REG_BANDS.slice().reverse(); // 65+ at top, 0-5 at bottom
        const labels = order.map(b=>REG_BAND_LABELS[b]);
        const data = order.map(b=>rows.reduce((a,s)=>a+((s.reg_bands&&s.reg_bands[b])||0),0));
        charts.pyramid = new Chart(document.getElementById("chart-pyramid"), {
            type:"bar",
            data:{ labels, datasets:[{ label:"תושבים (מרשם)", data, backgroundColor:C.accent, borderRadius:3 }] },
            options:{ indexAxis:"y", responsive:true, maintainAspectRatio:false,
                scales:{ x:{ ticks:{ font:FONT, color:"#94a3b8", callback:v=>fmt.int(v) }, grid:{ color:"#f1f5f9" } },
                         y:{ ticks:{ font:FONT, color:"#475569" }, grid:{ display:false } } },
                plugins:{ legend:{ display:false }, tooltip:{ callbacks:{ label:c=>fmt.int(c.parsed.x) } } } }
        });
    }

    function chartHaredi() {
        kill("haredi");
        let rows = (state.harediScope === "authorities" ? filteredAuthorities() : filtered()).filter(x => x.pop_haredim_2023 > 0).map(x => ({ name:x.name, pct:x.haredi_pct, abs:x.pop_haredim_2023 }));
        const key = state.harediMetric === "pct" ? "pct" : "abs";
        rows = rows.sort((a,b)=>b[key]-a[key]).slice(0,8);
        charts.haredi = new Chart(document.getElementById("chart-haredi"), {
            type:"bar", data:{ labels:rows.map(r=>r.name), datasets:[{ data:rows.map(r=>r[key]), backgroundColor:C.magenta, borderRadius:3 }] },
            options:{ indexAxis:"y", responsive:true, maintainAspectRatio:false, plugins:{ legend:{display:false}, tooltip:{ callbacks:{ label:c=> key==="pct" ? fmt.pct1(c.parsed.x) : fmt.int(c.parsed.x) } } }, scales:{ x:{ ticks:{ font:FONT, callback:v=> key==="pct"?v+"%":fmt.int(v) } }, y:{ ticks:{ font:{...FONT, size:10} } } } }
        });
    }

    function chartTypes() {
        kill("types");
        const rows = filtered();
        const counts = {};
        rows.forEach(s => { counts[s.type_gross] = (counts[s.type_gross]||0)+1; });
        const entries = Object.entries(counts).sort((a,b)=>b[1]-a[1]);
        charts.types = new Chart(document.getElementById("chart-types"), {
            type:"doughnut", data:{ labels:entries.map(e=>e[0]), datasets:[{ data:entries.map(e=>e[1]), backgroundColor:C.qual, borderWidth:2, borderColor:"#fff", hoverOffset:4 }] },
            options:{ 
                responsive:true, maintainAspectRatio:false, cutout:"58%", 
                plugins:{ legend:{ position:"right", labels:{ font:{...FONT, size:10}, boxWidth:10 } } },
                onClick: (e, elements) => {
                    if (!elements.length) return;
                    const index = elements[0].index;
                    const typeLabel = entries[index][0];
                    const sList = rows.filter(s => s.type_gross === typeLabel).map(s => s.name).sort();
                    
                    document.getElementById("types-modal-title").textContent = typeLabel + " (" + sList.length + ")";
                    document.getElementById("types-modal-list").innerHTML = sList.map(n => `<li class="p-2 bg-slate-50 rounded text-sm text-slate-700 border border-slate-100 font-medium">${n}</li>`).join("");
                    
                    const m = document.getElementById("types-modal");
                    m.classList.remove("hidden");
                    setTimeout(() => { m.style.opacity = 1; }, 10);
                }
            }
        });
    }

    function makeBarChart(id, rows, key, color, formatter, yOpts={}) {
        kill(id);
        const sorted = rows.filter(r=>r[key]!=null && r[key]!==0).sort((a,b)=>b[key]-a[key]);
        const bgColors = typeof color === "function" ? sorted.map(r=>color(r[key])) : color;
        charts[id] = new Chart(document.getElementById("chart-"+id), {
            type:"bar", data:{ labels:sorted.map(r=>r.name), datasets:[{ data:sorted.map(r=>r[key]), backgroundColor:bgColors, borderRadius:3 }] },
            options:{ responsive:true, maintainAspectRatio:false, plugins:{ legend:{display:false}, tooltip:{callbacks:{label:c=>formatter(c.parsed.y)}} }, scales:{ x:{ ticks:{ font:{...FONT,size:9}, maxRotation:90, minRotation:45 } }, y: Object.assign({ ticks:{ font:FONT, callback:v=>formatter(v) } }, yOpts) } }
        });
    }

    function renderAgeCharts() {
        const renderAgeChart = (id, key, color, metric) => {
            kill(id);
            const isPct = metric === "pct";
            let chartRows = filteredAuthorities().filter(r => (r[key]||0) > 0).map(r => {
                const totalAge = (r.pop_0_14||0) + (r.pop_15_64||0) + (r.pop_65_plus||0);
                const pct = totalAge > 0 ? (r[key] / totalAge * 100) : 0;
                return { name: r.name, abs: r[key], pct: pct };
            });
            chartRows.sort((a,b) => b[isPct ? "pct" : "abs"] - a[isPct ? "pct" : "abs"]);
            
            charts[id] = new Chart(document.getElementById("chart-"+id), {
                type:"bar", data:{ labels:chartRows.map(r=>r.name), datasets:[{ data:chartRows.map(r=>r[isPct ? "pct" : "abs"]), backgroundColor:color, borderRadius:3 }] },
                options:{ responsive:true, maintainAspectRatio:false, plugins:{ legend:{display:false}, tooltip:{callbacks:{label:c=>isPct ? fmt.pct1(c.parsed.y) : fmt.int(c.parsed.y)}} }, scales:{ x:{ ticks:{ font:{...FONT,size:9}, maxRotation:90, minRotation:45 } }, y:{ ticks:{ font:FONT, callback:v=>isPct ? fmt.pct1(v) : fmt.int(v) } } } }
            });
        };
        
        renderAgeChart("age-young", "pop_0_14", C.accent, state.ageYoungMetric);
        renderAgeChart("age-work", "pop_15_64", C.lime, state.ageWorkMetric);
        renderAgeChart("age-old", "pop_65_plus", C.gold, state.ageOldMetric);
    }

    function renderDependency() {
        kill("dependency");
        const rows = filteredAuthorities().filter(r=>r.dependency_ratio!=null && r.dependency_ratio!==0).sort((a,b)=>b.dependency_ratio-a.dependency_ratio);
        const mult = state.depMetric === "per100" ? 100 : 1;
        const fmtCb = v => state.depMetric === "per100" ? v.toFixed(1) : v.toFixed(2);
        charts["dependency"] = new Chart(document.getElementById("chart-dependency"), {
            type:"bar", data:{ labels:rows.map(r=>r.name), datasets:[{ data:rows.map(r=>r.dependency_ratio*mult), backgroundColor:C.magenta, borderRadius:3 }] },
            options:{ responsive:true, maintainAspectRatio:false, plugins:{ legend:{display:false}, tooltip:{callbacks:{label:c=>fmtCb(c.parsed.y)}} }, scales:{ x:{ ticks:{ font:{...FONT,size:9}, maxRotation:90, minRotation:45 } }, y:{ ticks:{ font:FONT, callback:v=>fmtCb(v) } } } }
        });
    }

    function renderTable() {
        const tbl = document.getElementById("data-table");
        const q = state.search.trim().toLowerCase();
        let rows, headers;
        if (state.tab === "authorities") {
            rows = filteredAuthorities().slice(); headers = ["שם","סוג/מעמד","מגזר","דירוג סוציו׳","שטח (קמ״ר)","גידול (%)","אוכלוסייה"];
        } else if (state.tab === "settlements") {
            rows = filtered().slice(); headers = ["שם","רשות","מגזר","צורת יישוב","אוכלוסייה","% חרדים"];
        } else {
            rows = filtered().filter(s=>s.haredi_pct>0).sort((a,b)=>b.haredi_pct-a.haredi_pct); headers = ["שם","רשות","אוכלוסייה","% חרדים"];
        }
        if (q) rows = rows.filter(r => (r.name||"").toLowerCase().includes(q) || (r.authority||"").toLowerCase().includes(q));
        
        const head = `<thead><tr>${headers.map((h,i)=>`<th class="${i===0?'':'text-center'}">${h}</th>`).join("")}</tr></thead>`;
        let body;
        if (state.tab === "authorities") {
            body = rows.map(r=>`<tr><td class="font-semibold">${r.name}</td><td class="text-center">${r.type_gross}</td><td class="text-center">${r.sector||"—"}</td><td class="text-center">${r.socio_rank||"—"}</td><td class="text-center">${r.area_sqkm!=null?r.area_sqkm.toFixed(1):"—"}</td><td class="text-center">${fmt.pct1(r.pop_growth)}</td><td class="text-center">${fmt.int(r.population)}</td></tr>`).join("");
        } else if (state.tab === "settlements") {
            body = rows.map(r=>`<tr><td class="font-semibold">${r.name}</td><td class="text-center">${r.authority}</td><td class="text-center">${r.sector}</td><td class="text-center">${r.type_gross}</td><td class="text-center">${fmt.int(r.population)}</td><td class="text-center">${r.haredi_pct?fmt.pct1(r.haredi_pct):"—"}</td></tr>`).join("");
        } else {
            body = rows.map(r=>`<tr><td class="font-semibold">${r.name}</td><td class="text-center">${r.authority}</td><td class="text-center">${fmt.int(r.pop_haredim_2023 || 0)}</td><td class="text-center" style="color:${C.magenta};font-weight:700;">${fmt.pct1(r.haredi_pct)}</td></tr>`).join("");
        }
        tbl.innerHTML = head + "<tbody>" + (body || `<tr><td colspan="${headers.length}" class="text-center text-slate-500 py-6">לא נמצאו נתונים</td></tr>`) + "</tbody>";
    }

    function renderAuthCharts() {
        const auths = filteredAuthorities();
        makeBarChart("socio", auths, "socio_rank", C.lime, v=>v, {min: 1, max: 10});
        // Brand rule: no red. Magenta carries the negative axis (skill §4).
        makeBarChart("growth", auths, "pop_growth", v => v >= 0 ? C.sky : C.magenta, fmt.pct1);
        makeBarChart("migration", auths, "migration_balance", v => v >= 0 ? C.gold : C.magenta, fmt.int);
        makeBarChart("immigrants", auths, "immigrants_1990_pct", C.blue, fmt.pct1);
        makeBarChart("tfr", auths, "tfr", "#186078", v=>v.toFixed(2));
        makeBarChart("density", auths, "density", C.gold, v=>fmt.int(v));
    }

    function render() {
        renderKPIs(); chartPyramid(); chartHaredi(); chartTypes(); renderTable(); renderAgeCharts(); renderDependency(); renderAuthCharts();
    }

    document.addEventListener("DOMContentLoaded", () => {
        initFilters(); render();
    });
})();
"""

with open(os.path.join(app_dir, 'app.js'), 'w', encoding='utf-8') as f:
    f.write(app_js_content)

print("Dashboard with 2x2 charts and all new functionality generated.")
