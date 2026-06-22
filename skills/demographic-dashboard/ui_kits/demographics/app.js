// EGKC Demographics Dashboard — runtime
// Demonstrates the system handling VILLAGE-RESOLUTION data with a
// drill-down filter cascade (cluster → authority → sector → type → settlement),
// a population pyramid, segmented metric toggles, a donut, and a drill modal.

(function () {
    "use strict";

    const D = window.DEMO_DATA;
    const AGES = D.ageLabels;
    const SETTLEMENTS = D.settlements;
    const RCS = D.regionalCouncils;

    // Independent authorities are settlements whose type is עירייה / מועצה מקומית
    const INDEP_TYPES = ["עירייה", "מועצה מקומית"];
    // The full "authorities" table = independent authorities + regional councils
    const AUTHORITIES = [
        ...SETTLEMENTS.filter(s => INDEP_TYPES.includes(s.type_gross)),
        ...RCS
    ];

    // Brand palette
    const C = {
        accent: "#18a8c0", magenta: "#903078", lime: "#90c048", gold: "#c0a860",
        navy: "#183048", blue: "#1878a8", sky: "#48c0f0", slate: "#94a3b8",
        qual: ["#18a8c0","#903078","#1878a8","#90c048","#c0a860","#183048","#48c0f0","#186078","#78c0f0","#d77b3a"]
    };
    const FONT = { family: "Heebo" };

    const state = {
        authority: "all", sector: "all", type: "all", settlement: "all",
        search: "", tab: "authorities",
        harediScope: "authorities", harediMetric: "pct", typeMode: "gross",
    };

    const fmt = {
        int: v => (v==null||isNaN(v)) ? "—" : Math.round(v).toLocaleString("he-IL"),
        ils: v => (!v) ? "—" : "₪" + Math.round(v).toLocaleString("he-IL"),
        pct1: v => (v==null||isNaN(v)) ? "—" : v.toFixed(1) + "%",
    };

    // ───────── filtering ─────────
    function filtered() {
        return SETTLEMENTS.filter(s =>
            (state.authority === "all" || s.authority === state.authority) &&
            (state.sector === "all" || s.sector === state.sector) &&
            (state.type === "all" || s.type_gross === state.type) &&
            (state.settlement === "all" || s.name === state.settlement)
        );
    }

    function resolutionLabel() {
        if (state.settlement !== "all") return "יישוב";
        if (state.authority !== "all") return "רשות";
        if (state.sector !== "all" || state.type !== "all") return "פילוח";
        return "אשכול";
    }

    // ───────── filter population ─────────
    function initFilters() {
        const auths = [...new Set(SETTLEMENTS.map(s => s.authority))].sort((a,b)=>a.localeCompare(b,"he"));
        const sectors = [...new Set(SETTLEMENTS.map(s => s.sector))].sort((a,b)=>a.localeCompare(b,"he"));
        const types = [...new Set(SETTLEMENTS.map(s => s.type_gross))].sort((a,b)=>a.localeCompare(b,"he"));

        fill("f-authority", auths, "כל הרשויות");
        fill("f-sector", sectors, "כל המגזרים");
        fill("f-type", types, "כל הצורות");
        updateSettlementDropdown();

        document.getElementById("f-authority").addEventListener("change", e => { state.authority = e.target.value; state.settlement = "all"; updateSettlementDropdown(); render(); });
        document.getElementById("f-sector").addEventListener("change", e => { state.sector = e.target.value; state.settlement = "all"; updateSettlementDropdown(); render(); });
        document.getElementById("f-type").addEventListener("change", e => { state.type = e.target.value; state.settlement = "all"; updateSettlementDropdown(); render(); });
        document.getElementById("f-settlement").addEventListener("change", e => { state.settlement = e.target.value; render(); });

        document.getElementById("reset-filters").addEventListener("click", e => {
            e.preventDefault();
            Object.assign(state, { authority:"all", sector:"all", type:"all", settlement:"all" });
            ["f-authority","f-sector","f-type"].forEach(id => document.getElementById(id).value = "all");
            updateSettlementDropdown(); render();
        });

        document.getElementById("table-search").addEventListener("input", e => { state.search = e.target.value; renderTable(); });

        document.querySelectorAll("#tab-row button").forEach(b => b.addEventListener("click", () => {
            state.tab = b.dataset.tab;
            document.querySelectorAll("#tab-row button").forEach(x => x.className = x.dataset.tab===state.tab ? "tab-active" : "tab-inactive");
            renderTable();
        }));

        // Segmented toggles
        bindToggle("haredi-scope", v => { state.harediScope = v; chartHaredi(); });
        bindToggle("haredi-metric", v => { state.harediMetric = v; chartHaredi(); });
        bindToggle("type-mode", v => { state.typeMode = v; chartTypes(); });

        // Modal close
        document.getElementById("modal-close").addEventListener("click", closeModal);
        document.getElementById("modal-overlay").addEventListener("click", e => { if (e.target.id === "modal-overlay") closeModal(); });
    }

    function fill(id, items, allLabel) {
        const sel = document.getElementById(id);
        sel.innerHTML = `<option value="all">${allLabel}</option>` + items.map(i => `<option value="${i}">${i}</option>`).join("");
    }
    function updateSettlementDropdown() {
        const pool = SETTLEMENTS.filter(s =>
            (state.authority==="all"||s.authority===state.authority) &&
            (state.sector==="all"||s.sector===state.sector) &&
            (state.type==="all"||s.type_gross===state.type)
        ).map(s=>s.name).sort((a,b)=>a.localeCompare(b,"he"));
        fill("f-settlement", pool, "כל היישובים");
        document.getElementById("f-settlement").value = state.settlement;
    }
    function bindToggle(groupId, cb) {
        const group = document.getElementById(groupId);
        group.querySelectorAll("button").forEach(btn => btn.addEventListener("click", () => {
            group.querySelectorAll("button").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            cb(btn.dataset.val);
        }));
    }

    // ───────── KPIs ─────────
    function renderKPIs() {
        const rows = filtered();
        const totalPop = rows.reduce((a,s)=>a+s.population,0);
        const count = rows.length;
        // weighted socio + wage over rows that have them
        const withWage = rows.filter(s=>s.wage>0);
        const avgWage = withWage.length ? withWage.reduce((a,s)=>a+s.wage*s.population,0) / withWage.reduce((a,s)=>a+s.population,0) : 0;
        const withRank = rows.filter(s=>s.socio_rank>0);
        const avgRank = withRank.length ? withRank.reduce((a,s)=>a+s.socio_rank,0)/withRank.length : 0;

        document.getElementById("kpi-row").innerHTML = `
            <div class="egkc-kpi-card egkc-kpi-tinted"><div class="egkc-kpi-numeral">${fmt.int(totalPop)}</div><div class="egkc-kpi-label">סה״כ אוכלוסייה</div></div>
            <div class="egkc-kpi-card"><div class="egkc-kpi-numeral" style="color:#475569;">${fmt.int(count)}</div><div class="egkc-kpi-label">יישובים</div></div>
            <div class="egkc-kpi-card"><div class="egkc-kpi-numeral" style="color:#475569;">${avgRank?avgRank.toFixed(1):"—"}</div><div class="egkc-kpi-label">דירוג סוציו׳ ממוצע</div></div>
            <div class="egkc-kpi-card"><div class="egkc-kpi-numeral" style="color:#475569;">${avgWage?fmt.ils(avgWage):"—"}</div><div class="egkc-kpi-label">שכר ממוצע משוקלל</div></div>
        `;
        document.getElementById("resolution-label").textContent = resolutionLabel();
        const scope = state.settlement!=="all" ? state.settlement
            : state.authority!=="all" ? state.authority
            : "כלל האשכול";
        document.getElementById("pyramid-scope").textContent = scope;
    }

    // ───────── charts ─────────
    const charts = {};
    const kill = n => { if (charts[n]) { charts[n].destroy(); delete charts[n]; } };

    function chartPyramid() {
        kill("pyramid");
        const rows = filtered();
        const m = AGES.map((_,i)=>rows.reduce((a,s)=>a+(s.ages.m[i]||0),0));
        const f = AGES.map((_,i)=>rows.reduce((a,s)=>a+(s.ages.f[i]||0),0));
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
                plugins:{
                    legend:{ position:"bottom", labels:{ font:FONT } },
                    tooltip:{ callbacks:{ label:c=>`${c.dataset.label}: ${fmt.int(Math.abs(c.parsed.x))}` } }
                }
            }
        });
    }

    function chartHaredi() {
        kill("haredi");
        let rows;
        if (state.harediScope === "authorities") {
            rows = AUTHORITIES.filter(a => a.haredi_pct > 0).map(a => ({ name:a.name, pct:a.haredi_pct, abs:Math.round(a.population*a.haredi_pct/100) }));
        } else {
            rows = SETTLEMENTS.filter(s => s.haredi_pct > 0).map(s => ({ name:s.name, pct:s.haredi_pct, abs:Math.round(s.population*s.haredi_pct/100) }));
        }
        const key = state.harediMetric === "pct" ? "pct" : "abs";
        rows = rows.sort((a,b)=>b[key]-a[key]).slice(0,8);
        charts.haredi = new Chart(document.getElementById("chart-haredi"), {
            type:"bar",
            data:{ labels:rows.map(r=>r.name), datasets:[{ data:rows.map(r=>r[key]), backgroundColor:C.magenta, borderRadius:3 }] },
            options:{
                indexAxis:"y", responsive:true, maintainAspectRatio:false,
                plugins:{ legend:{display:false}, tooltip:{ callbacks:{ label:c=> key==="pct" ? fmt.pct1(c.parsed.x) : fmt.int(c.parsed.x)+" נפש" } } },
                scales:{ x:{ ticks:{ font:FONT, color:"#94a3b8", callback:v=> key==="pct"?v+"%":fmt.int(v) }, grid:{ color:"#f1f5f9" } }, y:{ ticks:{ font:{...FONT, size:10}, color:"#475569" }, grid:{display:false} } }
            }
        });
    }

    function chartTypes() {
        kill("types");
        const rows = filtered();
        const key = state.typeMode === "gross" ? "type_gross" : "type_detailed";
        const counts = {};
        rows.forEach(s => { counts[s[key]] = (counts[s[key]]||0)+1; });
        const entries = Object.entries(counts).sort((a,b)=>b[1]-a[1]);
        charts.types = new Chart(document.getElementById("chart-types"), {
            type:"doughnut",
            data:{ labels:entries.map(e=>e[0]), datasets:[{ data:entries.map(e=>e[1]), backgroundColor:C.qual, borderWidth:2, borderColor:"#fff" }] },
            options:{
                responsive:true, maintainAspectRatio:false, cutout:"58%",
                plugins:{ legend:{ position:"right", labels:{ font:{...FONT, size:10}, boxWidth:10, padding:6 } },
                          tooltip:{ callbacks:{ label:c=>`${c.label}: ${c.parsed} יישובים` } } },
                onClick:(e,els)=>{ if(els.length){ const lbl=entries[els[0].index][0]; openModal(lbl, rows.filter(s=>s[key]===lbl)); } }
            }
        });
    }

    function chartSocio() {
        kill("socio");
        const rows = AUTHORITIES.filter(a=>a.socio_rank>0).sort((a,b)=>b.socio_rank-a.socio_rank);
        charts.socio = new Chart(document.getElementById("chart-socio"), {
            type:"bar",
            data:{ labels:rows.map(r=>r.name), datasets:[{ data:rows.map(r=>r.socio_rank), backgroundColor:C.lime, borderRadius:3 }] },
            options:{ responsive:true, maintainAspectRatio:false, plugins:{ legend:{display:false} },
                scales:{ x:{ ticks:{ font:{...FONT,size:9}, color:"#475569", maxRotation:90, minRotation:45 }, grid:{display:false} }, y:{ beginAtZero:true, max:10, ticks:{ font:FONT, color:"#94a3b8", stepSize:2 }, grid:{color:"#f1f5f9"} } } }
        });
    }

    function chartWage() {
        kill("wage");
        const rows = AUTHORITIES.filter(a=>a.wage>0).sort((a,b)=>b.wage-a.wage);
        charts.wage = new Chart(document.getElementById("chart-wage"), {
            type:"bar",
            data:{ labels:rows.map(r=>r.name), datasets:[{ data:rows.map(r=>r.wage), backgroundColor:C.gold, borderRadius:3 }] },
            options:{ responsive:true, maintainAspectRatio:false, plugins:{ legend:{display:false}, tooltip:{ callbacks:{ label:c=>fmt.ils(c.parsed.y) } } },
                scales:{ x:{ ticks:{ font:{...FONT,size:9}, color:"#475569", maxRotation:90, minRotation:45 }, grid:{display:false} }, y:{ beginAtZero:true, ticks:{ font:FONT, color:"#94a3b8", callback:v=>fmt.int(v) }, grid:{color:"#f1f5f9"} } } }
        });
    }

    // ───────── table ─────────
    function renderTable() {
        const tbl = document.getElementById("data-table");
        const q = state.search.trim().toLowerCase();
        let rows, headers;

        if (state.tab === "authorities") {
            rows = AUTHORITIES.slice();
            headers = ["שם","סוג/מעמד","מגזר","דירוג סוציו׳","שכר ממוצע","אוכלוסייה"];
        } else if (state.tab === "settlements") {
            rows = SETTLEMENTS.slice();
            headers = ["שם","רשות","מגזר","צורת יישוב","אוכלוסייה","% חרדים"];
        } else {
            rows = SETTLEMENTS.filter(s=>s.haredi_pct>0).sort((a,b)=>b.haredi_pct-a.haredi_pct);
            headers = ["שם","רשות","אוכלוסייה","% חרדים","חרדים (מוערך)"];
        }
        if (q) rows = rows.filter(r => (r.name||"").toLowerCase().includes(q) || (r.authority||"").toLowerCase().includes(q));

        const head = `<thead><tr>${headers.map((h,i)=>`<th class="${i===0?'':'text-center'}">${h}</th>`).join("")}</tr></thead>`;
        let body;
        if (state.tab === "authorities") {
            body = rows.map(r=>`<tr><td class="font-semibold">${r.name}</td><td class="text-center">${r.type_gross}</td><td class="text-center">${r.sector||"—"}</td><td class="text-center">${r.socio_rank||"—"}</td><td class="text-center">${fmt.ils(r.wage)}</td><td class="text-center">${fmt.int(r.population)}</td></tr>`).join("");
        } else if (state.tab === "settlements") {
            body = rows.map(r=>`<tr><td class="font-semibold">${r.name}</td><td class="text-center">${r.authority}</td><td class="text-center">${r.sector}</td><td class="text-center">${r.type_gross}</td><td class="text-center">${fmt.int(r.population)}</td><td class="text-center">${r.haredi_pct?fmt.pct1(r.haredi_pct):"—"}</td></tr>`).join("");
        } else {
            body = rows.map(r=>`<tr><td class="font-semibold">${r.name}</td><td class="text-center">${r.authority}</td><td class="text-center">${fmt.int(r.population)}</td><td class="text-center" style="color:${C.magenta};font-weight:700;">${fmt.pct1(r.haredi_pct)}</td><td class="text-center">${fmt.int(r.population*r.haredi_pct/100)}</td></tr>`).join("");
        }
        tbl.innerHTML = head + "<tbody>" + (body || `<tr><td colspan="${headers.length}" class="text-center text-slate-500 py-6">לא נמצאו נתונים</td></tr>`) + "</tbody>";
    }

    // ───────── modal ─────────
    function openModal(title, rows) {
        document.getElementById("modal-title").textContent = title + " · " + rows.length + " יישובים";
        document.getElementById("modal-list").innerHTML = rows
            .sort((a,b)=>b.population-a.population)
            .map(s=>`<li class="flex justify-between border-b border-slate-100 py-1"><span>${s.name}</span><span class="text-slate-500" style="font-variant-numeric:tabular-nums;">${fmt.int(s.population)}</span></li>`).join("");
        const o = document.getElementById("modal-overlay");
        o.classList.remove("hidden"); o.classList.add("flex");
    }
    function closeModal() {
        const o = document.getElementById("modal-overlay");
        o.classList.add("hidden"); o.classList.remove("flex");
    }

    // ───────── render ─────────
    function render() {
        renderKPIs();
        chartPyramid();
        chartHaredi();
        chartTypes();
        renderTable();
    }

    document.addEventListener("DOMContentLoaded", () => {
        initFilters();
        render();
        // Static authority-level charts: defer to after layout settles so Chart.js
        // measures a non-zero container width (it would otherwise init at width 0).
        // setTimeout (not rAF) so it fires reliably even in a backgrounded iframe.
        setTimeout(() => {
            chartSocio();
            chartWage();
            setTimeout(() => {
                if (charts.socio) charts.socio.resize();
                if (charts.wage) charts.wage.resize();
            }, 60);
        }, 60);
    });
})();
