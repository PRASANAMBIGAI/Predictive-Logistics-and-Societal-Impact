import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from firebase_config import db

def check_live():
    docs = db.collection("live_tracking").stream()
    count = 0
    delayed = 0
    for doc in docs:
        data = doc.to_dict()
        count += 1
        speed = data.get("current_speed_kmh")
        prob = data.get("ml_delay_probability")
        factors = data.get("ml_contributing_factors", [])
        print(f"{doc.id}: speed={speed}, prob={prob}%, factors={factors}")
        if float(prob) > 70:
            delayed += 1
    print(f"Total: {count}, Delayed: {delayed}")

if __name__ == "__main__":
    check_live()
