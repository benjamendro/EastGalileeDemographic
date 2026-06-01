// EGKC Bagrut Dashboard — runtime
// Mirrors the canonical excel-to-dashboard skill but written explicitly
// so this kit is readable as an example. Real implementations would use
// the build_dashboard.py pipeline that produces a single-file HTML.

(function () {
    "use strict";

    const DATA = window.EGKC_DATA;

    // ─────────────────────── STATE ───────────────────────
    const state = {
        authority: "גולן",            // default to one with rich coverage
        subject:   "מתמטיקה",
        yl:        5,
        search:    "",
        tab:       "auth",
    };

    // ─────────────────────── HELPERS ───────────────────────
    const fmt = {
        score: v => (v == null || isNaN(v)) ? "—" : Number(v).toFixed(2),
        int:   v => (v == null || isNaN(v)) ? "—" : Math.round(Number(v)).toLocaleString("he-IL"),
        pct1:  v => (v == null || isNaN(v)) ? "—" : Number(v).toFixed(1) + "%",
        diff:  v => {
            if (v == null || isNaN(v)) return { txt: "—", cls: "diff-zero" };
            const sign = v > 0 ? "+" : "";
            const cls = v > 0.5 ? "diff-pos" : (v < -0.5 ? "diff-neg" : "diff-zero");
            return { txt: sign + v.toFixed(2), cls };
        }
    };

    // Get a row from the authority's rows for the current subject + yl
    function authRow(authObj, subject, yl) {
        return (authObj.rows || []).find(r => r.subject === subject && r.yl === yl);
    }
    function natRow(subject, yl) {
        return DATA.national.find(r => r.subject === subject && r.yl === yl);
    }
    function authObj(name) {
        return DATA.authorities.find(a => a.name === name);
    }

    // Cluster mean weighted by examinees (treat each authority row as a group)
    function clusterMean(subject, yl) {
        let totW = 0, totS = 0, n = 0;
        DATA.authorities.forEach(a => {
            const r = authRow(a, subject, yl);
            if (!r) return;
            totW += r.examinees;
            totS += r.score * r.examinees;
            n += r.examinees;
        });
        return n > 0 ? { score: totS / totW, examinees: n } : null;
    }

    // ─────────────────────── INIT FILTERS ───────────────────────
    function initFilters() {
        const aSel = document.getElementById("f-authority");
        aSel.innerHTML = DATA.authorities
            .map(a => `<option value="${a.name}"${a.name===state.authority?" selected":""}>${a.name}</option>`)
            .join("");
        aSel.addEventListener("change", e => { state.authority = e.target.value; render(); });

        const sSel = document.getElementById("f-subject");
        sSel.innerHTML = DATA.subjects
            .map(s => `<option value="${s}"${s===state.subject?" selected":""}>${s}</option>`)
            .join("");
        sSel.addEventListener("change", e => { state.subject = e.target.value; render(); });

        document.querySelectorAll('input[name="yl"]').forEach(r => {
            r.addEventListener("change", e => { state.yl = parseInt(e.target.value, 10); render(); });
        });

        document.getElementById("reset-filters").addEventListener("click", e => {
            e.preventDefault();
            state.authority = "גולן"; state.subject = "מתמטיקה"; state.yl = 5;
            aSel.value = state.authority; sSel.value = state.subject;
            document.getElementById("yl5").checked = true;
            render();
        });

        document.getElementById("table-search").addEventListener("input", e => {
            state.search = e.target.value;
            renderTable();
        });

        document.querySelectorAll("#tab-row button").forEach(b => {
            b.addEventListener("click", () => {
                state.tab = b.dataset.tab;
                document.querySelectorAll("#tab-row button").forEach(x => {
                    x.className = (x.dataset.tab === state.tab) ? "egkc-tab-active" : "egkc-tab-inactive";
                });
                renderTable();
            });
        });
    }

    // ─────────────────────── KPI ROW ───────────────────────
    function renderKPIs() {
        const aRow = authRow(authObj(state.authority), state.subject, state.yl);
        const cMean = clusterMean(state.subject, state.yl);
        const nRow  = natRow(state.subject, state.yl);

        const aVal = aRow ? aRow.score : null;
        const cVal = cMean ? cMean.score : null;
        const nVal = nRow ? nRow.score : null;
        const diff = (aVal != null && nVal != null) ? (aVal - nVal) : null;
        const diffFmt = fmt.diff(diff);

        const row = document.getElementById("kpi-row");
        row.innerHTML = `
            <div class="egkc-kpi-card egkc-kpi-tinted" title="${state.authority}">
                <div class="egkc-kpi-numeral">${fmt.score(aVal)}</div>
                <div class="egkc-kpi-label">${state.authority}</div>
            </div>
            <div class="egkc-kpi-card">
                <div class="egkc-kpi-numeral" style="color:#475569;">${fmt.score(cVal)}</div>
                <div class="egkc-kpi-label">ממוצע אשכול</div>
            </div>
            <div class="egkc-kpi-card">
                <div class="egkc-kpi-numeral" style="color:#475569;">${fmt.score(nVal)}</div>
                <div class="egkc-kpi-label">ממוצע ארצי</div>
            </div>
            <div class="egkc-kpi-card">
                <div class="egkc-kpi-numeral ${diffFmt.cls}">${diffFmt.txt}</div>
                <div class="egkc-kpi-label">פער מול ארצי</div>
            </div>
        `;

        // Caption + row-count
        document.getElementById("headline-caption").textContent =
            `${state.authority} · ${state.yl} יח״ל · השוואה לאשכול ולארצי`;
        document.getElementById("ranked-caption").textContent =
            `${state.subject} · ${state.yl} יח״ל`;
        document.getElementById("yl-caption").textContent =
            `${state.authority}`;
        document.getElementById("row-count").textContent =
            (cMean ? cMean.examinees : 0).toLocaleString("he-IL");
    }

    // ─────────────────────── CHARTS ───────────────────────
    const charts = {};
    function destroy(name) { if (charts[name]) { charts[name].destroy(); delete charts[name]; } }

    const BASE_FONT = { family: "Heebo" };
    const COLORS = {
        accent:  "#18a8c0", /* brand cyan         */
        cluster: "#94a3b8", /* slate              */
        nat:     "#cbd5e1", /* slate-300          */
        natLine: "#903078", /* brand magenta line */
    };

    function chartHeadline() {
        destroy("headline");
        const ctx = document.getElementById("chart-headline");
        const aObj = authObj(state.authority);
        const subjects = DATA.subjects;

        const aScores = subjects.map(s => { const r = authRow(aObj, s, state.yl); return r ? r.score : null; });
        const cScores = subjects.map(s => { const c = clusterMean(s, state.yl); return c ? c.score : null; });
        const nScores = subjects.map(s => { const r = natRow(s, state.yl); return r ? r.score : null; });

        charts.headline = new Chart(ctx, {
            type: "bar",
            data: {
                labels: subjects,
                datasets: [
                    { label: state.authority, data: aScores, backgroundColor: COLORS.accent, borderRadius: 3 },
                    { label: "ממוצע אשכול",  data: cScores, backgroundColor: COLORS.cluster, borderRadius: 3 },
                    { label: "ממוצע ארצי",   data: nScores, backgroundColor: COLORS.nat,     borderRadius: 3 },
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: {
                    legend: { position: "bottom", labels: { font: BASE_FONT } },
                    tooltip: { callbacks: { label: c => `${c.dataset.label}: ${fmt.score(c.parsed.y)}` } }
                },
                scales: {
                    x: { ticks: { font: BASE_FONT, color: "#475569" }, grid: { display: false } },
                    y: { beginAtZero: false, suggestedMin: 60, suggestedMax: 100, ticks: { font: BASE_FONT, color: "#94a3b8" }, grid: { color: "#f1f5f9" } }
                }
            }
        });
    }

    function chartRanked() {
        destroy("ranked");
        const ctx = document.getElementById("chart-ranked");
        const nRow = natRow(state.subject, state.yl);
        const natAvg = nRow ? nRow.score : null;

        const rows = DATA.authorities.map(a => {
            const r = authRow(a, state.subject, state.yl);
            return r ? { name: a.name, score: r.score, examinees: r.examinees } : null;
        }).filter(Boolean).sort((x,y) => y.score - x.score);

        const colors = rows.map(r => r.name === state.authority ? COLORS.accent : "#cbd5e1");

        // Build "national line" as a second dataset of the same value across labels
        const natLineData = natAvg ? rows.map(() => natAvg) : null;
        const datasets = [{ data: rows.map(r => r.score), backgroundColor: colors, borderRadius: 3 }];
        if (natLineData) {
            datasets.push({
                type: "line", label: `ארצי: ${natAvg.toFixed(1)}`,
                data: natLineData, borderColor: COLORS.natLine, borderWidth: 2, borderDash: [5,4],
                pointRadius: 0, fill: false, order: 0
            });
        }

        charts.ranked = new Chart(ctx, {
            type: "bar",
            data: { labels: rows.map(r => r.name), datasets },
            options: {
                indexAxis: "y", responsive: true, maintainAspectRatio: false,
                plugins: {
                    legend: { display: !!natLineData, position: "bottom", labels: { font: BASE_FONT, filter: (item) => !!item.text && item.text.startsWith("ארצי") } },
                    tooltip: {
                        callbacks: {
                            label: c => {
                                if (c.dataset.type === "line") return `ארצי: ${fmt.score(c.parsed.x)}`;
                                const r = rows[c.dataIndex];
                                return `ממוצע: ${fmt.score(c.parsed.x)}  ·  נבחנים: ${fmt.int(r.examinees)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: { beginAtZero: false, suggestedMin: 55, suggestedMax: 100, ticks: { font: BASE_FONT, color: "#94a3b8" }, grid: { color: "#f1f5f9" } },
                    y: { ticks: { font: BASE_FONT, color: "#475569" }, grid: { display: false } }
                }
            }
        });
    }

    function chartYL() {
        destroy("yl");
        const ctx = document.getElementById("chart-yl");
        const aObj = authObj(state.authority);

        // For each yl level (3/4/5), sum examinees across subjects for this authority
        const totals = [3,4,5].map(yl => {
            const n = (aObj.rows || [])
                .filter(r => r.yl === yl && DATA.subjects.includes(r.subject))
                .reduce((a, r) => a + r.examinees, 0);
            return n;
        });
        const labels = ["3 יח״ל","4 יח״ל","5 יח״ל"];
        const colors = ["#ef4444","#f59e0b","#10b981"];

        charts.yl = new Chart(ctx, {
            type: "bar",
            data: { labels, datasets: [{ data: totals, backgroundColor: colors, borderRadius: 3 }] },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { callbacks: { label: c => `${fmt.int(c.parsed.y)} נבחנים` } }
                },
                scales: {
                    x: { ticks: { font: BASE_FONT, color: "#475569" }, grid: { display: false } },
                    y: { beginAtZero: true, ticks: { font: BASE_FONT, color: "#94a3b8" }, grid: { color: "#f1f5f9" } }
                }
            }
        });
    }

    // ─────────────────────── TABLE ───────────────────────
    function renderTable() {
        const tbl = document.getElementById("data-table");
        const q = state.search.trim().toLowerCase();

        if (state.tab === "auth") {
            // Authority × subject matrix at selected yl, showing avg + #examinees
            const subjects = DATA.subjects;
            const cMeans = subjects.map(s => clusterMean(s, state.yl));
            const nRows  = subjects.map(s => natRow(s, state.yl));

            let head = `<thead><tr>
                <th>רשות</th>
                ${subjects.map(s => `<th class="text-center">${s}</th>`).join("")}
            </tr></thead>`;

            const auths = DATA.authorities.slice().sort((a,b) => a.name.localeCompare(b.name, "he"));
            const filtered = auths.filter(a => !q || a.name.toLowerCase().includes(q));

            const body = filtered.map(a => {
                return `<tr ${a.name===state.authority?'style="background:var(--egkc-accent-soft);"':""}>
                    <td class="font-semibold">${a.name}</td>
                    ${subjects.map(s => {
                        const r = authRow(a, s, state.yl);
                        const n = natRow(s, state.yl);
                        if (!r) return `<td class="text-center text-slate-300">—</td>`;
                        const diff = n ? (r.score - n.score) : null;
                        const arrow = diff == null ? "" : (diff > 0.5 ? `<span style="color:var(--egkc-positive);font-size:11px;">▲</span>` : (diff < -0.5 ? `<span style="color:var(--egkc-negative);font-size:11px;">▼</span>` : ""));
                        return `<td class="text-center"><span>${fmt.score(r.score)}</span> ${arrow}</td>`;
                    }).join("")}
                </tr>`;
            }).join("");

            const footer = `<tfoot>
                <tr style="background:#f8fafc;font-weight:700;">
                    <td>ממוצע אשכול</td>
                    ${cMeans.map(c => `<td class="text-center" style="color:#475569;">${c ? fmt.score(c.score) : "—"}</td>`).join("")}
                </tr>
                <tr style="background:#f8fafc;color:#64748b;">
                    <td>ממוצע ארצי</td>
                    ${nRows.map(n => `<td class="text-center">${n ? fmt.score(n.score) : "—"}</td>`).join("")}
                </tr>
            </tfoot>`;

            tbl.innerHTML = head + "<tbody>" + body + "</tbody>" + footer;

        } else {
            // Detail: selected authority, every (subject, yl) row, vs national
            const aObj = authObj(state.authority);
            const rows = (aObj.rows || []).slice()
                .filter(r => DATA.subjects.includes(r.subject))
                .filter(r => !q || r.subject.toLowerCase().includes(q))
                .sort((a,b) => a.subject.localeCompare(b.subject,"he") || a.yl - b.yl);

            const head = `<thead><tr>
                <th>מקצוע</th>
                <th class="text-center">יח״ל</th>
                <th class="text-center">נבחנים</th>
                <th class="text-center">${state.authority}</th>
                <th class="text-center">ממוצע אשכול</th>
                <th class="text-center">ממוצע ארצי</th>
                <th class="text-center">פער מול ארצי</th>
            </tr></thead>`;

            const body = rows.map(r => {
                const c = clusterMean(r.subject, r.yl);
                const n = natRow(r.subject, r.yl);
                const diff = n ? (r.score - n.score) : null;
                const dfmt = fmt.diff(diff);
                return `<tr>
                    <td class="font-semibold">${r.subject}</td>
                    <td class="text-center">${r.yl}</td>
                    <td class="text-center">${fmt.int(r.examinees)}</td>
                    <td class="text-center" style="color:var(--egkc-accent);font-weight:700;">${fmt.score(r.score)}</td>
                    <td class="text-center" style="color:#475569;">${c?fmt.score(c.score):"—"}</td>
                    <td class="text-center" style="color:#475569;">${n?fmt.score(n.score):"—"}</td>
                    <td class="text-center ${dfmt.cls}" style="font-weight:600;">${dfmt.txt}</td>
                </tr>`;
            }).join("");

            tbl.innerHTML = head + "<tbody>" + (body || `<tr><td colspan="7" class="text-center text-slate-500 py-6">לא נמצאו נתונים</td></tr>`) + "</tbody>";
        }
    }

    // ─────────────────────── RENDER ALL ───────────────────────
    function render() {
        renderKPIs();
        chartHeadline();
        chartRanked();
        chartYL();
        renderTable();
    }

    // ─────────────────────── GO ───────────────────────
    document.addEventListener("DOMContentLoaded", () => {
        initFilters();
        render();
    });
})();
