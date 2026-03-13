// js/data.js

import { collection, onSnapshot, getDocs } from "firebase/firestore";
import { db } from "./firebase.js";
import { upsertMarker, removeMarker } from "./map.js";
import { handleStatusChange, updateSidebarList, updateDashboardStats } from "./app.js";

// Keep a local copy of data to detect status transitions
const shipmentStateCache = {};
const shipmentMetaCache = {}; // For static destination data if needed

// Helper to determine status category
export function getStatusCategory(prob) {
    if (prob > 70) return "red";
    if (prob > 30) return "yellow";
    return "green";
}

export async function fetchStaticShipmentData() {
    try {
        const querySnapshot = await getDocs(collection(db, "shipments"));
        querySnapshot.forEach((doc) => {
            shipmentMetaCache[doc.id] = doc.data();
        });
        console.log(`Loaded ${Object.keys(shipmentMetaCache).length} static shipment routes.`);
    } catch (error) {
        console.error("Error fetching static shipment data:", error);
    }
}

export function listenToLiveTracking() {
    const q = collection(db, "live_tracking");

    const unsubscribe = onSnapshot(q,
        (snapshot) => {
            snapshot.docChanges().forEach((change) => {
                const id = change.doc.id;
                const data = change.doc.data();

                if (change.type === "added" || change.type === "modified") {

                    // Check for status threshold crossings
                    const newProb = data.ml_delay_probability || 0;
                    const newStatus = getStatusCategory(newProb);

                    if (shipmentStateCache[id]) {
                        const oldProb = shipmentStateCache[id].ml_delay_probability || 0;
                        const oldStatus = getStatusCategory(oldProb);

                        if (oldStatus !== newStatus) {
                            handleStatusChange(id, newStatus, newProb);
                        }
                    }

                    // Update cache
                    shipmentStateCache[id] = data;

                    // 1. Update Map
                    upsertMarker(id, data);

                    // 2. Update Sidebar List
                    updateSidebarList(id, data);

                } else if (change.type === "removed") {
                    // Cleanup
                    delete shipmentStateCache[id];
                    removeMarker(id);
                }
            });

            // 3. Update top widgets based on latest snapshot state
            updateDashboardStats(shipmentStateCache);

            // 4. Update UI connection badge (if it exists on this page)
            // 4. Update UI connection badge (if it exists on this page)
            const badge = document.getElementById("connectionStatus");
            if (badge) {
                badge.className = "status-badge live";
                badge.innerHTML = '<span class="pulse"></span> <span>Live Connected</span>';
            }
        },
        (error) => {
            console.error("Firestore onSnapshot Error:", error);
            const badge = document.getElementById("connectionStatus");
            if (badge) {
                badge.className = "status-badge disconnected";
                badge.innerHTML = '<span class="pulse" style="background:var(--status-red)"></span> <span class="text-red">Disconnected</span>';
            }
        }
    );

    return unsubscribe;
}
