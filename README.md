# 🚛 Predictive Logistics Orchestrator — MVP

An AI-driven real-time logistics dashboard that predicts delivery delays using traffic, weather, and warehouse metrics. Built for hackathon demos with Firebase Firestore, Python ML, and Leaflet.js.

![Stack](https://img.shields.io/badge/Firebase-Firestore-orange?style=flat-square) ![ML](https://img.shields.io/badge/ML-scikit--learn-blue?style=flat-square) ![Frontend](https://img.shields.io/badge/Map-Leaflet.js-green?style=flat-square)

---

## 📁 Project Structure

```
├── firebase_config.py         # Shared Firebase Admin SDK init
├── credentials.json           # 🔒 Your service account key (not in repo)
├── requirements.txt           # Python dependencies
│
├── ml_pipeline/
│   ├── generate_mock_data.py  # Create 1,000-row synthetic CSV
│   ├── train_model.py         # Train Random Forest → model.pkl
│   ├── training_data.csv      # (generated)
│   └── model.pkl              # (generated)
│
├── backend/
│   ├── seed_firestore.py      # Populate Firestore with demo shipments
│   ├── ml_worker.py           # Real-time Firestore listener + ML inference
│   └── api.py                 # FastAPI: /api/trigger_storm/{id}
│
├── simulation/
│   └── simulator.py           # Continuous loop updating truck positions
│
└── frontend/
    ├── index.html             # Dashboard entry point
    ├── style.css              # Premium dark theme
    └── app.js                 # Firebase onSnapshot + Leaflet real-time map
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- A Firebase project with Firestore enabled
- A service account key (`credentials.json`)

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Add Firebase credentials
- Place your **`credentials.json`** (service account key) in the project root.
- Open `frontend/app.js` and replace the `firebaseConfig` placeholder with your Firebase web app config.

### 3. Generate training data & train the model
```bash
python ml_pipeline/generate_mock_data.py
python ml_pipeline/train_model.py
```

### 4. Seed Firestore with demo data
```bash
python backend/seed_firestore.py
```

### 5. Start the services (3 terminals)

**Terminal 1 — ML Worker** (listens for changes, runs predictions):
```bash
python backend/ml_worker.py
```

**Terminal 2 — Simulator** (moves trucks, fluctuates conditions):
```bash
python simulation/simulator.py
```

**Terminal 3 — API Server** (demo storm triggers):
```bash
uvicorn backend.api:app --reload --port 8000
```

### 6. Open the Dashboard
Open `frontend/dashboard.html` in your browser. You'll see live-updating truck markers on a dark-themed map.

---

## 🎬 Demo Flow

1. Open the dashboard — trucks move in real-time with green markers (on-time).
2. Click any marker to see delay probability, telemetry, and explainability factors.
3. Select a shipment and click **"⛈️ Simulate Storm"** — watch the marker turn red and delay prediction spike.
4. Click **"☀️ Clear Storm"** to reset conditions.

---

## 🧠 ML Model

- **Type:** Random Forest (Classifier + Regressor)
- **Features:** Speed, Weather (encoded), Traffic Index, Warehouse Backlog, Distance Remaining
- **Targets:** `is_delayed` (bool), `delay_minutes` (int)
- **Training Data:** 1,000 rows of synthetic data with realistic correlations

---

## 📜 License
MIT — Built for hackathon demonstration purposes.
