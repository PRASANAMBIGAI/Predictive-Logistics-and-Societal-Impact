// js/map.js

// Leaflet map instance
let map;
const markers = {}; // Maps shipment_id -> L.marker
const routeLines = {}; // Maps shipment_id -> L.polyline

// Initialize the map
export function initMap() {
    map = L.map("map-container", {
        zoomControl: false,
        attributionControl: true
    }).setView([20.5937, 78.9629], 5); // Center on India

    // Always use OpenStreetMap standard tiles (Google Maps-like view)
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);

    L.control.zoom({ position: "topright" }).addTo(map);
}

// Generate the custom HTML icon based on probability
function getMarkerIcon(prob) {
    let color = "#28C76F"; // green
    let label = "✓";

    if (prob > 70) {
        color = "#EA5455"; // red
        label = "!";
    } else if (prob > 30) {
        color = "#FF9F43"; // yellow
        label = "–";
    }

    return L.divIcon({
        className: "custom-div-icon",
        html: `<div style="
            width: 28px;
            height: 28px;
            background: ${color};
            border: 3px solid white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 800;
            font-size: 14px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.4);
        ">${label}</div>`,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
        popupAnchor: [0, -14]
    });
}

// Generate human-readable string for factors
function formatFactors(data) {
    const factors = [];
    if (["Storm", "Fog", "Rain"].includes(data.weather_condition)) {
        factors.push(`${data.weather_condition} Weather`);
    }
    if ((data.traffic_index || 0) >= 7) factors.push("Heavy Traffic");
    if ((data.warehouse_backlog_index || 0) >= 7) factors.push("Dock Congestion");
    if ((data.current_speed_kmh || 50) < 20) factors.push("Low Speed");

    return factors.length > 0 ? factors.join(", ") : "Normal Operations";
}

// Generate the HTML for the Leaflet popup tooltip
function generateTooltipHTML(id, data) {
    const prob = (data.ml_delay_probability || 0).toFixed(1);
    const delayMins = data.ml_estimated_delay_mins || 0;
    const factors = formatFactors(data);

    // Status text color matched to theme vars
    let statColor = "var(--status-green)";
    if (prob > 70) statColor = "var(--status-red)";
    else if (prob > 30) statColor = "var(--status-yellow)";

    return `
        <div class="custom-tooltip">
            <h3>${id}</h3>
            <div class="tooltip-stat">
                <span>Delay Prob:</span>
                <strong style="color: ${statColor}">${prob}%</strong>
            </div>
            <div class="tooltip-stat">
                <span>Est Delay:</span>
                <strong>+${delayMins} min</strong>
            </div>
            <div class="tooltip-factors">
                <strong>Factors:</strong> ${factors}
            </div>
        </div>
    `;
}

// Create or update a map marker
export function upsertMarker(id, data) {
    const lat = data.current_lat;
    const lng = data.current_lng;
    const prob = data.ml_delay_probability || 0;

    if (!lat || !lng) return;

    if (markers[id]) {
        // Update existing marker
        markers[id].setLatLng([lat, lng]);
        markers[id].setIcon(getMarkerIcon(prob));
        markers[id].setPopupContent(generateTooltipHTML(id, data));
    } else {
        // Create new marker
        const marker = L.marker([lat, lng], {
            icon: getMarkerIcon(prob)
        }).addTo(map);

        marker.bindPopup(generateTooltipHTML(id, data));
        markers[id] = marker;
    }
}

// Remove a map marker
export function removeMarker(id) {
    if (markers[id]) {
        map.removeLayer(markers[id]);
        delete markers[id];
    }
}

// Export map instance if needed by other modules
export { map };
