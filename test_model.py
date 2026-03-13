import sys
import os
import joblib
import numpy as np
import random

MODEL_PATH = "c:/Users/ASUS/Predictive Logistics and Societal Impact/ml_pipeline/model.pkl"
bundle = joblib.load(MODEL_PATH)
classifier = bundle["classifier"]
label_encoder = bundle["label_encoder"]

weather_list = ["Clear", "Cloudy", "Rain", "Fog", "Storm"]

delayed_count = 0
for i in range(100):
    weather = random.choice(weather_list)
    try:
        weather_encoded = label_encoder.transform([weather])[0]
    except:
        weather_encoded = label_encoder.transform(["Clear"])[0]
    
    speed = round(max(5, random.gauss(55, 15)), 1)
    traffic = random.randint(2, 6)
    backlog = random.randint(1, 5)
    dist = random.uniform(5.0, 300.0)

    t = [speed, weather_encoded, traffic, backlog, dist]
    proba = classifier.predict_proba(np.array([t]))[0]
    delay_prob = round(proba[1] * 100, 1) if len(proba) > 1 else 0.0

    if delay_prob > 30:
        delayed_count += 1
    
print(f"Total delayed out of 100: {delayed_count}")
