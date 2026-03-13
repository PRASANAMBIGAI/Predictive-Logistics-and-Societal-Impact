"""
Simulator — creates the illusion of a live logistics tracking system.

Runs in a continuous loop (every 3 seconds), updating every active shipment's
position, speed, traffic, and weather in the `live_tracking` Firestore collection.
"""

import sys
import os
import time
import random
from math import atan2, sqrt, radians, degrees, cos, sin

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from firebase_config import db
from google.cloud.firestore import SERVER_TIMESTAMP

WEATHER_OPTIONS = ["Clear", "Clear", "Clear", "Cloudy", "Rain", "Fog", "Storm"]
TICK_SECONDS = 15
SPEED_STEP = 0.010  # Commensurate speed step for 15 seconds


def _load_shipments():
    """Load destination coordinates from the shipments collection."""
    destinations = {}
    docs = db.collection("shipments").stream()
    for doc in docs:
        data = doc.to_dict()
        destinations[doc.id] = {
            "dest_lat": data["dest_lat"],
            "dest_lng": data["dest_lng"],
            "origin_lat": data.get("origin_lat", data["dest_lat"]),
            "origin_lng": data.get("origin_lng", data["dest_lng"]),
        }
    return destinations


def _move_toward(current_lat, current_lng, dest_lat, dest_lng, step):
    """Move current position one step closer to the destination."""
    dlat = dest_lat - current_lat
    dlng = dest_lng - current_lng
    dist = sqrt(dlat**2 + dlng**2)

    if dist < step:
        return dest_lat, dest_lng, True  # arrived

    ratio = step / dist
    new_lat = current_lat + dlat * ratio
    new_lng = current_lng + dlng * ratio
    return round(new_lat, 6), round(new_lng, 6), False


def main():
    destinations = _load_shipments()
    if not destinations:
        print("[ERROR] No shipments found in Firestore. Run seed_firestore.py first.")
        return

    print(f"[START] Simulator started -- tracking {len(destinations)} shipments (tick={TICK_SECONDS}s)")
    arrived = set()

    while True:
        for sid, dest in destinations.items():
            if sid in arrived:
                continue

            doc_ref = db.collection("live_tracking").document(sid)
            doc = doc_ref.get()
            if not doc.exists:
                continue

            data = doc.to_dict()
            cur_lat = data.get("current_lat", dest["origin_lat"])
            cur_lng = data.get("current_lng", dest["origin_lng"])

            # Move toward destination
            new_lat, new_lng, has_arrived = _move_toward(
                cur_lat, cur_lng, dest["dest_lat"], dest["dest_lng"], SPEED_STEP
            )

            if has_arrived:
                arrived.add(sid)
                print(f"  [ARRIVED] {sid} has arrived at destination!")

            # Fluctuate conditions
            speed = round(max(5, random.gauss(55, 15)), 1)
            traffic = max(1, min(10, data.get("traffic_index", 3) + random.choice([-1, 0, 0, 1])))

            # Occasional weather change (low probability per tick)
            weather = data.get("weather_condition", "Clear")
            if random.random() < 0.08:
                weather = random.choice(WEATHER_OPTIONS)

            # Fluctuate warehouse backlog
            backlog = max(1, min(10, data.get("warehouse_backlog_index", 2) + random.choice([-1, 0, 0, 0, 1])))

            update = {
                "current_lat": new_lat,
                "current_lng": new_lng,
                "current_speed_kmh": speed,
                "traffic_index": traffic,
                "weather_condition": weather,
                "warehouse_backlog_index": backlog,
                "last_updated": SERVER_TIMESTAMP,
            }
            doc_ref.update(update)

        active = len(destinations) - len(arrived)
        if active == 0:
            print("[OK] All shipments delivered! Restarting positions...")
            arrived.clear()
            # Reset positions to origin
            for sid, dest in destinations.items():
                db.collection("live_tracking").document(sid).update(
                    {
                        "current_lat": dest["origin_lat"],
                        "current_lng": dest["origin_lng"],
                        "last_updated": SERVER_TIMESTAMP,
                    }
                )

        time.sleep(TICK_SECONDS)


if __name__ == "__main__":
    main()
