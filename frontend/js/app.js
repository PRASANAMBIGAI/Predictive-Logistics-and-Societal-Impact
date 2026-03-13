// js/app.js

import { initMap, map } from "./map.js";
import { listenToLiveTracking, fetchStaticShipmentData, getStatusCategory } from "./data.js";

// FastAPI backend URL for demo triggers
const API_BASE = "http://localhost:8000";

// ============================================================================
// Initialization
// ============================================================================
const initDashboard = async () => {
    initClock();
    initThemeToggle();
    initDemoControls();

    // Initialize Map (only if it exists on page)
    if (document.getElementById("map-container")) {
        initMap();
    }

    // Fetch static shipment data (destinations, criticality)
    await fetchStaticShipmentData();

    // Start Real-time listener
    listenToLiveTracking();

    console.log("🚀 Predictive Logistics Dashboard initialized.");
};

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initDashboard);
} else {
    initDashboard();
}

// ============================================================================
// Clock & Theme
// ============================================================================
function initClock() {
    const clockEl = document.getElementById("clock");
    if (!clockEl) return;

    setInterval(() => {
        clockEl.textContent = new Date().toLocaleTimeString("en-IN", {
            hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false
        });
    }, 1000);
}

function initThemeToggle() {
    const toggleBtn = document.getElementById("theme-toggle");

    // Check saved preference or default to dark
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "light") {
        document.documentElement.setAttribute("data-theme", "light");
    }

    if (!toggleBtn) return;

    toggleBtn.addEventListener("click", () => {
        const currentTheme = document.documentElement.getAttribute("data-theme") || "dark";
        const newTheme = currentTheme === "dark" ? "light" : "dark";

        document.documentElement.setAttribute("data-theme", newTheme);
        localStorage.setItem("theme", newTheme);
    });
}

// ============================================================================
// UI Updaters (Called by data.js onSnapshot)
// ============================================================================

// ============================================================================
// UI Updaters (Called by data.js onSnapshot)
// ============================================================================

// Top KPI Widgets
export function updateDashboardStats(shipmentCache) {
    let active = 0, onTime = 0, atRisk = 0, delayed = 0;

    Object.values(shipmentCache).forEach(data => {
        active++;
        const status = getStatusCategory(data.ml_delay_probability || 0);
        if (status === "red") delayed++;
        else if (status === "yellow") atRisk++;
        else onTime++;
    });

    const elActive = document.getElementById("val-active");
    const elOnTime = document.getElementById("val-ontime");
    const elAtRisk = document.getElementById("val-atrisk");
    const elDelayed = document.getElementById("val-delayed");

    if (elActive) elActive.textContent = active;
    if (elOnTime) elOnTime.textContent = onTime;
    if (elAtRisk) elAtRisk.textContent = atRisk;
    if (elDelayed) elDelayed.textContent = delayed;
}

// Sidebar list / Alert Feed
export function updateSidebarList(id, data) {
    const listEl = document.getElementById("shipment-list");
    if (!listEl) return;

    let itemEl = document.getElementById(`li-${id}`);

    // Remove empty state if present
    const emptyState = listEl.querySelector(".empty-state");
    if (emptyState) emptyState.remove();

    const prob = (data.ml_delay_probability || 0).toFixed(1);
    const delayMins = data.ml_estimated_delay_mins || 0;
    const delayLow = data.ml_delay_range_low || 0;
    const delayHigh = data.ml_delay_range_high || 0;
    const factors = data.ml_contributing_factors || [];
    const statusCategory = getStatusCategory(data.ml_delay_probability || 0);

    let borderColor = "var(--border)";
    let bgColor = "var(--card-bg)";
    if (statusCategory === "red") {
        borderColor = "var(--danger)";
        bgColor = "rgba(255, 23, 68, 0.1)";
    } else if (statusCategory === "yellow") {
        borderColor = "var(--warning)";
        bgColor = "rgba(255, 179, 0, 0.1)";
    }

    // Build delay display: range if available, else point estimate
    const delayDisplay = (delayLow > 0 || delayHigh > 0)
        ? `+${delayLow}–${delayHigh} min`
        : `+${delayMins} min`;

    // Build factors display
    const factorsHTML = (factors.length > 0 && factors[0] !== "All Clear")
        ? `<div style="color:var(--text-muted); font-size:0.78rem; margin-top:3px;">⚡ ${factors.join(', ')}</div>`
        : '';

    const contentHTML = `
        <div style="font-weight:600; margin-bottom:4px;">Vehicle #${id}</div>
        <div style="color:var(--text-muted)">
            Delay Prob: <strong style="color:${borderColor}">${prob}%</strong> | ETA Impact: ${delayDisplay}
        </div>
        ${factorsHTML}
    `;

    if (itemEl) {
        itemEl.innerHTML = contentHTML;
        itemEl.style.borderLeftColor = borderColor;
        itemEl.style.background = bgColor;
    } else {
        itemEl = document.createElement("div");
        itemEl.id = `li-${id}`;
        itemEl.className = "alert-item";
        itemEl.style.borderLeftColor = borderColor;
        itemEl.style.background = bgColor;
        itemEl.style.cursor = "pointer";
        itemEl.innerHTML = contentHTML;

        // Click to pan map to shipment
        itemEl.addEventListener("click", () => {
            const lat = data.current_lat;
            const lng = data.current_lng;
            if (lat && lng && map) {
                map.flyTo([lat, lng], 14, { animate: true, duration: 1.5 });
            }
        });

        listEl.appendChild(itemEl);
    }
}

// ============================================================================
// Toast Notifications & Status Changes
// ============================================================================
export function handleStatusChange(id, newStatus, prob) {
    const labels = { "green": "On Time", "yellow": "At Risk", "red": "Delayed" };
    showToast(`${id} is now ${labels[newStatus]} (${prob.toFixed(1)}%)`);
}

function showToast(message, duration = 4000) {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = "toast";
    toast.style.cssText = `
        padding: 12px 16px;
        background: var(--glass-bg);
        backdrop-filter: blur(8px);
        border: 1px solid var(--glass-border);
        border-radius: var(--radius-sm);
        margin-top: 8px;
        font-size: 0.85rem;
        color: var(--text-primary);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        animation: slideIn 0.3s ease forwards;
    `;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Add simple animation for toast in JS since we didn't add it to CSS
if (!document.getElementById("toast-keyframes")) {
    const style = document.createElement('style');
    style.id = "toast-keyframes";
    style.innerHTML = `
        @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        .toast-container { position: fixed; top: 80px; right: 24px; z-index: 9999; display: flex; flex-direction: column; align-items: flex-end; }
    `;
    document.head.appendChild(style);
}

// ============================================================================
// Demo Controls (FastAPI Triggers)
// ============================================================================
function initDemoControls() {
    const btnStorm = document.getElementById("btn-storm");
    const btnClear = document.getElementById("btn-clear");

    if (btnStorm) {
        btnStorm.addEventListener("click", () => {
            triggerApiAction("trigger_storm");
        });
    }

    if (btnClear) {
        btnClear.addEventListener("click", () => {
            triggerApiAction("clear_storm");
        });
    }
}

async function triggerApiAction(endpoint) {
    const targetEl = document.getElementById("target-shipment");
    const shipmentId = targetEl ? targetEl.value : "SHIP-001";
    try {
        const res = await fetch(`${API_BASE}/api/${endpoint}/${shipmentId}`, {
            method: "POST"
        });
        const data = await res.json();
        showToast(data.message || `API Action: ${endpoint} sent.`);
    } catch (err) {
        console.error("API Call Failed:", err);
        showToast(`❌ Connection Refused. Is FastAPI running on port 8000?`);
    }
}
