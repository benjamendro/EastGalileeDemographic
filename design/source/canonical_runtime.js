(function () {
    "use strict";

    // --- Hebrew normalization (mirror of the Python cleaning logic) ---
    var ZERO_WIDTH = /[\u200B-\u200F\u202A-\u202E\u2066-\u2069\uFEFF]/g;
    // Hebrew combining marks: niqqud + te'amim, excluding punctuation like maqaf (U+05BE).
    // These code points are all Unicode category Mn within the 0x0591-0x05C7 block.
    var NIQQUD = /[\u0591-\u05BD\u05BF\u05C1-\u05C2\u05C4-\u05C5\u05C7]/g;
    function normHe(s) {
        if (s == null) return "";
        s = String(s).normalize("NFC");
        s = s.replace(ZERO_WIDTH, "").replace(NIQQUD, "");
        s = s.replace(/\s+/g, " ").trim();
        return s;
    }

    // --- Formatters ---
    var FORMATTERS = {
        int_comma: function (v) { if (v == null || isNaN(v)) return "-"; return Math.round(Number(v)).toLocaleString("he-IL"); },
        num_comma: function (v) { if (v == null || isNaN(v)) return "-"; return Number(v).toLocaleString("he-IL", { maximumFractionDigits: 2 }); },
        pct1: function (v) { if (v == null || isNaN(v)) return "-"; return Number(v).toFixed(1) + "%"; },
        pct0: function (v) { if (v == null || isNaN(v)) return "-"; return Math.round(Number(v)) + "%"; },
        currency_ils: function (v) { if (v == null || isNaN(v)) return "-"; return "₪" + Number(v).toLocaleString("he-IL"); },
        raw: function (v) { return v == null ? "" : String(v); }
    };
    function fmt(v, name) {
        var f = FORMATTERS[name] || FORMATTERS.raw;
        return f(v);
    }

    // --- Palettes ---
    var PALETTES = {
        qualitative: ["#2563eb", "#7c3aed", "#db2777", "#f59e0b", "#10b981", "#ef4444", "#06b6d4", "#8b5cf6", "#f97316", "#14b8a6"],
        sequential: ["#dbeafe", "#bfdbfe", "#93c5fd", "#60a5fa", "#3b82f6", "#2563eb", "#1d4ed8", "#1e40af", "#1e3a8a"],
        diverging: ["#b91c1c", "#ef4444", "#fca5a5", "#e5e7eb", "#93c5fd", "#3b82f6", "#1e40af"]
    };
    function palette(kind, n) {
        var base = PALETTES[kind] || PALETTES.qualitative;
        var out = [];
        for (var i = 0; i < n; i++) out.push(base[i % base.length]);
        return out;
    }

    // --- Aggregations ---
    function aggregate(rows, measure, agg) {
        if (!rows || rows.length === 0) return 0;
        if (agg === "count" || (!measure && agg !== "nunique")) return rows.length;
        if (agg === "nunique") {
            var s = {};
            rows.forEach(function (r) {
                var v = r[measure];
                if (v != null && v !== "") s[v] = true;
            });
            return Object.keys(s).length;
        }
        var values = rows.map(function (r) { return Number(r[measure]); }).filter(function (v) { return !isNaN(v); });
        if (values.length === 0) return 0;
        if (agg === "sum") return values.reduce(function (a, b) { return a + b; }, 0);
        if (agg === "mean") return values.reduce(function (a, b) { return a + b; }, 0) / values.length;
        if (agg === "min") return Math.min.apply(null, values);
        if (agg === "max") return Math.max.apply(null, values);
        if (agg === "ratio") return values.reduce(function (a, b) { return a + b; }, 0) / values.length;
        return 0;
    }

    function groupBy(rows, dim, measure, agg) {
        var g = {};
        rows.forEach(function (r) {
            var k = r[dim];
            if (k == null || k === "") return;
            if (!g[k]) g[k] = [];
            g[k].push(r);
        });
        var keys = Object.keys(g);
        return keys.map(function (k) {
            return { key: k, value: aggregate(g[k], measure, agg), count: g[k].length };
        });
    }

    // --- State ---
    var state = {
        data: null,        // { tableName: [rows] }
        config: null,
        filterValues: {},  // filterId -> selected value or "all"
        activeTab: null,
        charts: {},        // chartId -> Chart.js instance
        customRenderers: {}  // chartId -> fn(filteredRows, config)
    };

    // --- Filter logic ---
    function rowsForActiveTable() {
        if (!state.config || !state.data) return [];
        var tableName = state.activeTab || state.config.data.primary_table;
        return state.data[tableName] || [];
    }

    function applyFilters(rows) {
        var filters = state.config.filters || [];
        return rows.filter(function (r) {
            for (var i = 0; i < filters.length; i++) {
                var f = filters[i];
                var v = state.filterValues[f.id];
                if (!v || v === "all") continue;
                var cell = r[f.column];
                if (normHe(cell) !== normHe(v)) return false;
            }
            return true;
        });
    }

    // --- Rendering ---
    function renderKPIs(filtered) {
        (state.config.kpis || []).forEach(function (kpi) {
            var el = document.getElementById("kpi-value-" + kpi.id);
            if (!el) return;
            var v = aggregate(filtered, kpi.column, kpi.type);
            el.textContent = fmt(v, kpi.format || (kpi.type === "count" || kpi.type === "sum" ? "int_comma" : "num_comma"));
        });
        var rowCountEl = document.getElementById("row-count-value");
        if (rowCountEl) rowCountEl.textContent = filtered.length.toLocaleString("he-IL");
    }

    function renderChart(chart, filtered) {
        if (chart.type === "custom") {
            var fn = state.customRenderers[chart.id];
            if (fn) fn(filtered, state.config);
            return;
        }
        var canvas = document.getElementById("canvas-" + chart.id);
        if (!canvas) return;

        var activeDimension = chart.dimension;
        var activeTitle = chart.title;
        if (chart.drilldown_dimension && chart.drilldown_trigger) {
            var triggerVal = state.filterValues[chart.drilldown_trigger];
            if (triggerVal && triggerVal !== "all") {
                activeDimension = chart.drilldown_dimension;
                activeTitle = chart.title + " (" + triggerVal + ")";
            }
        }

        var groups = groupBy(filtered, activeDimension, chart.measure, chart.aggregation || "count");

        // Sort
        var sort = chart.sort || "measure_desc";
        if (sort === "measure_desc") groups.sort(function (a, b) { return b.value - a.value; });
        else if (sort === "measure_asc") groups.sort(function (a, b) { return a.value - b.value; });
        else if (sort === "dimension_asc") groups.sort(function (a, b) {
            var an = Number(a.key), bn = Number(b.key);
            if (!isNaN(an) && !isNaN(bn)) return an - bn;
            return String(a.key).localeCompare(String(b.key), "he");
        });

        // Rare bucket
        var max = chart.max_categories || 20;
        if (groups.length > max) {
            var kept = groups.slice(0, max);
            var rest = groups.slice(max);
            var restValue = rest.reduce(function (acc, g) { return acc + g.value; }, 0);
            kept.push({ key: chart.rare_bucket_label || "אחר", value: restValue, count: rest.reduce(function (a, g) { return a + g.count; }, 0) });
            groups = kept;
        }

        var labels = groups.map(function (g) { return g.key; });
        var values = groups.map(function (g) { return g.value; });
        var colors = palette(chart.palette || "qualitative", labels.length);

        if (state.charts[chart.id]) {
            state.charts[chart.id].destroy();
        }

        var chartType = chart.type;
        var indexAxis = "x";
        if (chartType === "bar" && chart.orientation === "horizontal") {
            indexAxis = "y";
        }
        var cjsType = (chartType === "pie" || chartType === "doughnut" || chartType === "line") ? chartType : "bar";

        state.charts[chart.id] = new Chart(canvas, {
            type: cjsType,
            data: {
                labels: labels,
                datasets: [{
                    label: activeTitle,
                    data: values,
                    backgroundColor: (cjsType === "pie" || cjsType === "doughnut") ? colors : colors[0],
                    borderColor: (cjsType === "line") ? colors[0] : undefined,
                    fill: cjsType === "line" ? false : undefined,
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: indexAxis,
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: (cjsType === "pie" || cjsType === "doughnut"), position: "bottom", labels: { font: { family: "Heebo" } } },
                    tooltip: {
                        callbacks: {
                            label: function (ctx) {
                                var val = (cjsType === "pie" || cjsType === "doughnut") ? ctx.parsed : (indexAxis === "y" ? ctx.parsed.x : ctx.parsed.y);
                                return ctx.label + ": " + fmt(val, chart.value_format || "int_comma");
                            }
                        }
                    }
                },
                scales: (cjsType === "pie" || cjsType === "doughnut") ? {} : {
                    x: { ticks: { font: { family: "Heebo" } } },
                    y: { ticks: { font: { family: "Heebo" } }, beginAtZero: true }
                }
            }
        });
    }

    function renderCharts(filtered) {
        (state.config.charts || []).forEach(function (chart) { renderChart(chart, filtered); });
    }

    // --- Table ---
    function renderTable() {
        var tabs = state.config.table.tabs || [];
        var activeTab = tabs.find(function (t) { return t.id === state.activeTab; }) || tabs[0];
        if (!activeTab) return;

        // Update tab visuals
        tabs.forEach(function (t) {
            var el = document.getElementById("tab-" + t.id);
            if (!el) return;
            el.className = (t.id === activeTab.id) ? "text-sm font-medium tab-active transition pb-1 px-1" : "text-sm font-medium tab-inactive transition pb-1 px-1";
        });

        // Header
        var headRow = document.getElementById("table-head-row");
        if (headRow) {
            headRow.innerHTML = activeTab.columns.map(function (col) {
                return '<th class="py-2 px-3">' + col + '</th>';
            }).join("");
        }

        // Body
        var rows = state.data[activeTab.source] || [];
        var filterable = (activeTab.source === state.config.data.primary_table);
        var filtered = filterable ? applyFilters(rows) : rows;

        var search = (document.getElementById("table-search") || {}).value || "";
        var searchCols = state.config.table.search_columns || activeTab.columns;
        if (search) {
            var q = normHe(search).toLowerCase();
            filtered = filtered.filter(function (r) {
                return searchCols.some(function (col) {
                    return normHe(r[col]).toLowerCase().indexOf(q) !== -1;
                });
            });
        }

        var body = document.getElementById("data-table-body");
        if (!body) return;
        var MAX_ROWS = 500;
        var rendered = filtered.slice(0, MAX_ROWS);
        body.innerHTML = rendered.map(function (r) {
            return "<tr class='hover:bg-slate-50'>" + activeTab.columns.map(function (col) {
                var v = r[col];
                if (typeof v === "number") v = v.toLocaleString("he-IL");
                return "<td class='py-2 px-3'>" + (v == null ? "" : String(v).replace(/</g, "&lt;")) + "</td>";
            }).join("") + "</tr>";
        }).join("");
        if (filtered.length > MAX_ROWS) {
            body.innerHTML += "<tr><td colspan='" + activeTab.columns.length + "' class='text-center text-xs text-slate-500 py-2'>מוצגות " + MAX_ROWS + " שורות ראשונות מתוך " + filtered.length.toLocaleString("he-IL") + "</td></tr>";
        }
    }

    // --- Filter wiring ---
    function initFilters() {
        var filters = state.config.filters || [];
        filters.forEach(function (f) {
            var sel = document.getElementById("filter-" + f.id);
            if (!sel) return;
            state.filterValues[f.id] = f.default_value || "all";
            sel.addEventListener("change", function (e) {
                state.filterValues[f.id] = e.target.value;
                updateFilterOptions();
                recomputeAndRender();
            });
        });
        var reset = document.getElementById("reset-filters");
        if (reset) {
            reset.addEventListener("click", function () {
                filters.forEach(function (f) {
                    state.filterValues[f.id] = f.default_value || "all";
                });
                updateFilterOptions();
                recomputeAndRender();
            });
        }
    }

    function updateFilterOptions() {
        var filters = state.config.filters || [];
        var primary = state.data[state.config.data.primary_table] || [];
        
        filters.forEach(function (f, i) {
            var sel = document.getElementById("filter-" + f.id);
            if (!sel) return;
            
            var upstreamFilters = filters.slice(0, i);
            var validRows = primary.filter(function (r) {
                for (var j = 0; j < upstreamFilters.length; j++) {
                    var uf = upstreamFilters[j];
                    var v = state.filterValues[uf.id];
                    if (!v || v === "all") continue;
                    if (normHe(r[uf.column]) !== normHe(v)) return false;
                }
                return true;
            });
            
            var values = {};
            validRows.forEach(function (r) {
                var v = r[f.column];
                if (v != null && v !== "") values[normHe(v)] = v;
            });
            
            var keys = Object.keys(values).sort(function (a, b) { return a.localeCompare(b, "he"); });
            var currentVal = state.filterValues[f.id] || "all";
            var isCurrentValid = (currentVal === "all" && !f.default_value);
            
            var html = f.include_all !== false ? '<option value="all">' + (f.all_label || "הכל") + "</option>" : "";
            keys.forEach(function (k) {
                var optionVal = values[k];
                if (String(optionVal) === String(currentVal)) isCurrentValid = true;
                if (f.default_value && String(optionVal) === String(f.default_value) && currentVal === "all") {
                    isCurrentValid = true;
                    currentVal = f.default_value;
                }
                var optionValStr = String(optionVal);
                html += '<option value="' + optionValStr.replace(/"/g, "&quot;") + '">' + optionValStr.replace(/</g, "&lt;") + "</option>";
            });
            
            sel.innerHTML = html;
            
            if (isCurrentValid) {
                sel.value = currentVal;
            } else {
                var fallback = f.default_value || "all";
                sel.value = fallback;
                state.filterValues[f.id] = fallback;
            }
        });
    }

    function wireTabs() {
        (state.config.table.tabs || []).forEach(function (t) {
            var el = document.getElementById("tab-" + t.id);
            if (!el) return;
            el.addEventListener("click", function () {
                state.activeTab = t.id;
                renderTable();
            });
        });
        var searchEl = document.getElementById("table-search");
        if (searchEl) searchEl.addEventListener("input", renderTable);
    }

    function recomputeAndRender() {
        var primary = state.data[state.config.data.primary_table] || [];
        var filtered = applyFilters(primary);
        renderKPIs(filtered);
        renderCharts(filtered);
        renderTable();
    }

    // --- Public API ---
    window.dashboard = {
        data: null,
        config: null,
        get filteredData() {
            return applyFilters(state.data[state.config.data.primary_table] || []);
        },
        registerChart: function (id, fn) {
            state.customRenderers[id] = fn;
        },
        format: fmt,
        palette: palette,
        normHe: normHe,
        init: function () {
            var dataEl = document.getElementById("dashboard-data");
            var cfgEl = document.getElementById("dashboard-config");
            state.data = JSON.parse(dataEl.textContent);
            state.config = JSON.parse(cfgEl.textContent);
            this.data = state.data;
            this.config = state.config;
            var tabs = (state.config.table && state.config.table.tabs) || [];
            var def = tabs.find(function (t) { return t.default; }) || tabs[0];
            if (def) state.activeTab = def.id;
            initFilters();
            updateFilterOptions();
            wireTabs();
            recomputeAndRender();
        },
        recompute: recomputeAndRender
    };
})();
