"""
ML Worker — Real-time Firestore listener + inference.

Listens to the `live_tracking` collection via on_snapshot().
On change, runs features through the trained XGBoost model and writes:
  - ml_delay_probability       (0–100%)
  - ml_estimated_delay_mins    (point estimate)
  - ml_delay_range_low         (25th percentile)
  - ml_delay_range_high        (75th percentile)
  - ml_contributing_factors    (human-readable list)
back to Firestore.
"""

import sys
import os
import time
import threading

import numpy as np
import joblib
from math import radians, sin, cos, sqrt, atan2

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from firebase_config import db

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "ml_pipeline",
    "model.pkl",
)

# ── Load model bundle ──────────────────────────────────────────
bundle = joblib.load(MODEL_PATH)
classifier = bundle["classifier"]
regressor = bundle["regressor"]
regressor_lower = bundle.get("regressor_lower")
regressor_upper = bundle.get("regressor_upper")
label_encoder = bundle["label_encoder"]

has_quantile = regressor_lower is not None and regressor_upper is not None
print(f"[OK] Model loaded successfully. Quantile regressors: {'YES' if has_quantile else 'NO'}")

# ── Cache shipment destinations ────────────────────────────────
_destinations = {}


def _get_destination(shipment_id: str):
    """Fetch and cache destination coordinates from the shipments collection."""
    if shipment_id not in _destinations:
        doc = db.collection("shipments").document(shipment_id).get()
        if doc.exists:
            data = doc.to_dict()
            _destinations[shipment_id] = (data["dest_lat"], data["dest_lng"])
        else:
            _destinations[shipment_id] = (0.0, 0.0)
    return _destinations[shipment_id]


def haversine_km(lat1, lng1, lat2, lng2):
    """Calculate distance in km between two lat/lng points."""
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def predict_delay(doc_data: dict, shipment_id: str):
    """Run ML inference on a single live_tracking document.
    
    Returns:
        delay_prob: float (0-100)
        delay_mins: int (point estimate)
        delay_low: int (25th percentile lower bound)
        delay_high: int (75th percentile upper bound)
    """
    dest_lat, dest_lng = _get_destination(shipment_id)
    distance_remaining = haversine_km(
        doc_data.get("current_lat", 0),
        doc_data.get("current_lng", 0),
        dest_lat,
        dest_lng,
    )

    weather = doc_data.get("weather_condition", "Clear")
    try:
        weather_encoded = label_encoder.transform([weather])[0]
    except ValueError:
        weather_encoded = label_encoder.transform(["Clear"])[0]

    features = np.array(
        [
            [
                doc_data.get("current_speed_kmh", 50),
                weather_encoded,
                doc_data.get("traffic_index", 3),
                doc_data.get("warehouse_backlog_index", 2),
                distance_remaining,
            ]
        ]
    )

    # Probability of delay (class 1)
    proba = classifier.predict_proba(features)[0]
    delay_prob = round(float(proba[1]) * 100, 1) if len(proba) > 1 else 0.0

    # Point estimate of delay minutes
    delay_mins = max(0, int(regressor.predict(features)[0]))

    # Confidence interval (quantile range)
    if has_quantile:
        delay_low = max(0, int(regressor_lower.predict(features)[0]))
        delay_high = max(delay_low, int(regressor_upper.predict(features)[0]))
    else:
        # Fallback: ±30% around point estimate
        margin = max(2, int(delay_mins * 0.3))
        delay_low = max(0, delay_mins - margin)
        delay_high = delay_mins + margin

    return delay_prob, delay_mins, delay_low, delay_high


def _get_primary_factors(doc_data: dict):
    """Return human-readable explainability factors."""
    factors = []
    weather = doc_data.get("weather_condition", "Clear")
    if weather in ("Storm", "Fog", "Rain"):
        severity = "Severe" if weather == "Storm" else "Moderate"
        factors.append(f"{severity} Weather ({weather})")
    if doc_data.get("traffic_index", 0) >= 7:
        factors.append("Heavy Traffic")
    if doc_data.get("warehouse_backlog_index", 0) >= 7:
        factors.append("Warehouse Congestion")
    if doc_data.get("current_speed_kmh", 80) < 20:
        factors.append("Very Low Speed")
    return factors if factors else ["All Clear"]


def on_snapshot(col_snapshot, changes, read_time):
    """Callback for Firestore on_snapshot — runs inference on changed docs."""
    for change in changes:
        if change.type.name in ("ADDED", "MODIFIED"):
            doc = change.document
            shipment_id = doc.id
            data = doc.to_dict()

            delay_prob, delay_mins, delay_low, delay_high = predict_delay(data, shipment_id)
            factors = _get_primary_factors(data)

            # Write predictions + confidence interval + factors back to Firestore
            db.collection("live_tracking").document(shipment_id).update(
                {
                    "ml_delay_probability": delay_prob,
                    "ml_estimated_delay_mins": delay_mins,
                    "ml_delay_range_low": delay_low,
                    "ml_delay_range_high": delay_high,
                    "ml_contributing_factors": factors,
                }
            )

            status = "[!!] DELAYED" if delay_prob > 70 else ("[!] AT RISK" if delay_prob > 30 else "[OK] ON TIME")
            print(
                f"  {status} {shipment_id}: "
                f"P(delay)={delay_prob}% | ETA+{delay_low}–{delay_high}min | "
                f"Factors: {', '.join(factors)}"
            )


def main():
    print("[START] ML Worker started -- listening to live_tracking collection...")
    print(f"        Model: XGBoost | Confidence Intervals: {'Enabled' if has_quantile else 'Disabled'}")
    col_ref = db.collection("live_tracking")
    col_ref.on_snapshot(on_snapshot)

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[STOP] ML Worker stopped.")


if __name__ == "__main__":
    main()
