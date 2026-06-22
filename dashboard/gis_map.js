// Initialize map
var map = L.map('map').setView([33.0, 35.6], 10);

// Add base layer (CartoDB Positron for a clean, light look)
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: 'abcd',
    maxZoom: 20
}).addTo(map);

// Current selected demographic field
var currentField = 'pop_0_19';

// Color scale for population
function getColor(d) {
    return d > 800 ? '#800026' :
           d > 600  ? '#BD0026' :
           d > 400  ? '#E31A1C' :
           d > 300  ? '#FC4E2A' :
           d > 200  ? '#FD8D3C' :
           d > 100  ? '#FEB24C' :
           d > 50   ? '#FED976' :
                      '#FFEDA0';
}

function style(feature) {
    return {
        fillColor: getColor(feature.properties[currentField] || 0),
        weight: 2,
        opacity: 1,
        color: 'white',
        dashArray: '3',
        fillOpacity: 0.7
    };
}

// Highlight on hover
function highlightFeature(e) {
    var layer = e.target;
    layer.setStyle({
        weight: 5,
        color: '#666',
        dashArray: '',
        fillOpacity: 0.7
    });
    layer.bringToFront();
    info.update(layer.feature.properties);
}

function resetHighlight(e) {
    geojson.resetStyle(e.target);
    info.update();
}

function zoomToFeature(e) {
    map.fitBounds(e.target.getBounds());
}

function getPopupContent(feature) {
    var val = feature.properties[currentField] || 0;
    var label = currentField === 'pop_0_19' ? 'גילאי 0-19' : 'גילאי 50+';
    var council = feature.properties.Municipali || feature.properties.city_desc || 'ללא שיוך';
    
    return `<div style="direction: rtl; text-align: right; font-family: inherit;">
                <b>${feature.properties.name || feature.properties.city_desc}</b><br/>
                מועצה אזורית: ${council}<br/>
                אוכלוסיית ${label}: ${val.toLocaleString() || 'אין נתונים'}
            </div>`;
}

function onEachFeature(feature, layer) {
    layer.on({
        mouseover: highlightFeature,
        mouseout: resetHighlight,
        click: zoomToFeature
    });
    
    layer.bindPopup(getPopupContent(feature));
}

// Add info control
var info = L.control({position: 'topright'});

info.onAdd = function (map) {
    this._div = L.DomUtil.create('div', 'info');
    this.update();
    return this._div;
};

info.update = function (props) {
    var label = currentField === 'pop_0_19' ? 'גילאי 0-19' : 'גילאי 50+';
    var val = props ? (props[currentField] || 0) : null;
    var council = props ? (props.Municipali || props.city_desc || 'ללא שיוך') : null;
    
    this._div.innerHTML = '<h4>נתוני ' + label + '</h4>' + (props ?
        '<b>' + (props.name || props.city_desc) + '</b><br />' +
        'מועצה: ' + council + '<br />' +
        val.toLocaleString() + ' תושבים'
        : 'העבר עכבר מעל יישוב');
};

info.addTo(map);

// Add legend control
var legend = L.control({position: 'bottomright'});

legend.onAdd = function (map) {
    var div = L.DomUtil.create('div', 'info legend');
    div.innerHTML = getLegendHtml();
    return div;
};

function getLegendHtml() {
    var label = currentField === 'pop_0_19' ? 'גילאי 0-19' : 'גילאי 50+';
    var grades = [0, 50, 100, 200, 300, 400, 600, 800];
    var html = '<h4>מקרא (' + label + ')</h4>';
    for (var i = 0; i < grades.length; i++) {
        html +=
            '<i style="background:' + getColor(grades[i] + 1) + '"></i> ' +
            grades[i] + (grades[i + 1] ? '&ndash;' + grades[i + 1] + '<br>' : '+');
    }
    return html;
}

legend.addTo(map);

// Load GeoJSON data
var geojson;
fetch('../GIS/all_settlements.geojson')
    .then(response => {
        if(!response.ok) {
            throw new Error("Cannot load geojson. Make sure process_gis.py ran successfully.");
        }
        return response.json();
    })
    .then(data => {
        geojson = L.geoJson(data, {
            style: style,
            onEachFeature: onEachFeature
        }).addTo(map);
        
        // Fit map bounds to the loaded data (focus on northern region)
        if (data.features && data.features.length > 0) {
            map.fitBounds(geojson.getBounds());
        }
    })
    .catch(err => {
        console.error("Error loading GIS data:", err);
        info._div.innerHTML = "<b>שגיאה בטעינת הנתונים:</b><br/>אנא ודא שהסקריפט רץ בהצלחה.";
    });

// Event listener for the layer toggle dropdown
document.getElementById('layer-select').addEventListener('change', function(e) {
    currentField = e.target.value;
    
    // Update geojson style based on selected field
    if (geojson) {
        geojson.setStyle(style);
        
        // Re-bind popup with new data field for each settlement
        geojson.eachLayer(function(layer) {
            layer.bindPopup(getPopupContent(layer.feature));
        });
    }
    
    // Update the legend and info panel title
    var legendDiv = document.querySelector('.legend');
    if (legendDiv) {
        legendDiv.innerHTML = getLegendHtml();
    }
    info.update();
});
