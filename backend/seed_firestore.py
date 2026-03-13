"""
Seed Firestore with initial demo data.

Generates 40 shipments (10 North, 10 South, 10 East, 10 West of India)
in the `shipments` collection and matching initial entries in `live_tracking`.
"""

import sys
import os
import random

# Add project root to path for firebase_config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from firebase_config import db
from google.cloud.firestore import SERVER_TIMESTAMP

# We will distribute across 4 major regions in India
def generate_shipments():
    shipments = []
    
    regions = [
        {"name": "North (Delhi)", "lat": 28.6139, "lng": 77.2090},
        {"name": "South (Bangalore)", "lat": 12.9716, "lng": 77.5946},
        {"name": "West (Mumbai)", "lat": 19.0760, "lng": 72.8777},
        {"name": "East (Kolkata)", "lat": 22.5726, "lng": 88.3639},
    ]
    
    count = 1
    for region in regions:
        for _ in range(10):  # 10 per region
            # Generate random origin around the city (up to ~50km away)
            o_lat = region["lat"] + random.uniform(-0.5, 0.5)
            o_lng = region["lng"] + random.uniform(-0.5, 0.5)
            
            # Generate random destination (mostly toward the center of the city)
            d_lat = region["lat"] + random.uniform(-0.1, 0.1)
            d_lng = region["lng"] + random.uniform(-0.1, 0.1)
            
            shipments.append({
                "shipment_id": f"SHIP-{count:03d}",
                "origin_lat": round(o_lat, 4),
                "origin_lng": round(o_lng, 4),
                "dest_lat": round(d_lat, 4),
                "dest_lng": round(d_lng, 4),
                "planned_duration_mins": random.randint(45, 120),
                "cargo_criticality": random.randint(3, 10),
            })
            count += 1
            
    return shipments

def seed():
    print("[SEED] Generating 40 Distributed Shipments...")
    shipments = generate_shipments()

    print("[SEED] Seeding Firestore...")
    batch = db.batch()
    docs_in_batch = 0

    for s in shipments:
        sid = s["shipment_id"]

        # ── shipments collection (static) ──
        shipment_data = {k: v for k, v in s.items() if k != "shipment_id"}
        shipment_ref = db.collection("shipments").document(sid)
        batch.set(shipment_ref, shipment_data)
        
        # ── live_tracking collection (dynamic — initial state) ──
        # Random initial weather to make the map look busy instantly
        initial_weather = random.choices(["Clear", "Cloudy", "Rain", "Fog", "Storm"], weights=[60, 20, 10, 5, 5])[0]
        
        live_data = {
            "current_lat": s["origin_lat"],
            "current_lng": s["origin_lng"],
            "current_speed_kmh": 50.0,
            "weather_condition": initial_weather,
            "traffic_index": random.randint(2, 6),
            "warehouse_backlog_index": random.randint(1, 5),
            "ml_delay_probability": 0.0,
            "ml_estimated_delay_mins": 0,
            "last_updated": SERVER_TIMESTAMP,
        }
        live_ref = db.collection("live_tracking").document(sid)
        batch.set(live_ref, live_data)
        
        docs_in_batch += 2
        
        # Commit in batches of 500 (Firestore limit is 500, we have 40*2=80)
        
    print(f"Committing {docs_in_batch} documents...")
    batch.commit()

    print(f"\n[OK] Seeded {len(shipments)} shipments successfully!")


if __name__ == "__main__":
    seed()
