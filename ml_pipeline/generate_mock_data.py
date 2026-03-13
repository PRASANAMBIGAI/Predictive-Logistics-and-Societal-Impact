"""
Generate 1,000 rows of synthetic logistics training data.

Correlation logic:
  - High traffic + bad weather + high warehouse backlog → high delay probability & minutes.
  - Low traffic + good weather + low backlog → on-time delivery.

Output: ml_pipeline/training_data.csv
"""

import os
import random
import csv

import numpy as np

WEATHER_OPTIONS = ["Clear", "Cloudy", "Rain", "Fog", "Storm"]
NUM_ROWS = 1000
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "training_data.csv")


def generate_row():
    """Generate a single row of synthetic logistics data."""
    weather = random.choice(WEATHER_OPTIONS)
    traffic_index = random.randint(1, 10)
    warehouse_backlog = random.randint(1, 10)
    distance_remaining = round(random.uniform(5.0, 300.0), 2)

    # Speed inversely related to traffic
    base_speed = max(10, 80 - (traffic_index * 6) + random.uniform(-10, 10))
    if weather in ("Storm", "Fog"):
        base_speed *= 0.6
    elif weather == "Rain":
        base_speed *= 0.8
    current_speed = round(max(5.0, base_speed), 1)

    # ----- Delay calculation (correlated with features) -----
    weather_penalty = {"Clear": 0, "Cloudy": 2, "Rain": 8, "Fog": 10, "Storm": 20}
    delay_score = (
        traffic_index * 3
        + warehouse_backlog * 2
        + weather_penalty.get(weather, 0)
        - current_speed * 0.3
        + random.gauss(0, 5)
    )

    is_delayed = int(delay_score > 20)
    delay_minutes = max(0, int(delay_score * 1.5 + random.gauss(0, 8))) if is_delayed else 0

    return {
        "current_speed_kmh": current_speed,
        "weather_condition": weather,
        "traffic_index": traffic_index,
        "warehouse_backlog_index": warehouse_backlog,
        "distance_remaining": distance_remaining,
        "is_delayed": is_delayed,
        "delay_minutes": delay_minutes,
    }


def main():
    rows = [generate_row() for _ in range(NUM_ROWS)]
    fieldnames = list(rows[0].keys())

    with open(OUTPUT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    delayed_count = sum(r["is_delayed"] for r in rows)
    print(f"[OK] Generated {NUM_ROWS} rows -> {OUTPUT_PATH}")
    print(f"     Delayed: {delayed_count} | On-time: {NUM_ROWS - delayed_count}")


if __name__ == "__main__":
    main()
