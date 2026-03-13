"""
FastAPI — Predictive Logistics API

Endpoints:
  GET  /api/predictions                  — All active shipment predictions
  GET  /api/predictions/{shipment_id}    — Single shipment prediction with delay range + factors
  GET  /api/fleet/summary                — Fleet-wide KPI summary
  POST /api/trigger_storm/{shipment_id}  — Sets Storm + traffic 10 (demo)
  POST /api/clear_storm/{shipment_id}    — Resets to Clear + traffic 3 (demo)
  POST /api/webhook/notify               — Simulated TMS webhook for delay notifications

Run:
  uvicorn backend.api:app --reload --port 8000
"""

import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from firebase_config import db

app = FastAPI(
    title="Predictive Logistics API",
    description="AI-driven delivery delay prediction and fleet management API for TMS/WMS/OMS integration",
    version="2.0.0",
)

# Allow frontend & external systems to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic Models ───────────────────────────────────────────

class PredictionResponse(BaseModel):
    shipment_id: str
    delay_probability: float
    estimated_delay_mins: int
    delay_range_low: int
    delay_range_high: int
    contributing_factors: List[str]
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None
    weather_condition: Optional[str] = None
    traffic_index: Optional[int] = None
    status: str  # "on_time", "at_risk", "delayed"


class FleetSummary(BaseModel):
    total_active: int
    on_time: int
    at_risk: int
    delayed: int
    avg_delay_probability: float
    high_risk_shipments: List[str]
    timestamp: str


class WebhookPayload(BaseModel):
    shipment_id: str
    event_type: str  # "delay_detected", "eta_updated", "reroute_suggested"
    message: Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────

def _classify_status(prob: float) -> str:
    if prob > 70:
        return "delayed"
    elif prob > 30:
        return "at_risk"
    return "on_time"


def _doc_to_prediction(doc_id: str, data: dict) -> PredictionResponse:
    prob = data.get("ml_delay_probability", 0.0)
    return PredictionResponse(
        shipment_id=doc_id,
        delay_probability=prob,
        estimated_delay_mins=data.get("ml_estimated_delay_mins", 0),
        delay_range_low=data.get("ml_delay_range_low", 0),
        delay_range_high=data.get("ml_delay_range_high", 0),
        contributing_factors=data.get("ml_contributing_factors", ["Unknown"]),
        current_lat=data.get("current_lat"),
        current_lng=data.get("current_lng"),
        weather_condition=data.get("weather_condition"),
        traffic_index=data.get("traffic_index"),
        status=_classify_status(prob),
    )


# ── Prediction Endpoints ─────────────────────────────────────

@app.get("/api/predictions", response_model=List[PredictionResponse])
async def get_all_predictions():
    """
    Retrieve ML predictions for all active shipments.
    
    Designed for TMS/WMS/OMS integration — returns delay probability,
    confidence interval (delay range), and contributing factors per shipment.
    """
    docs = db.collection("live_tracking").stream()
    predictions = []
    for doc in docs:
        data = doc.to_dict()
        predictions.append(_doc_to_prediction(doc.id, data))
    
    # Sort by delay probability descending (highest risk first)
    predictions.sort(key=lambda p: p.delay_probability, reverse=True)
    return predictions


@app.get("/api/predictions/{shipment_id}", response_model=PredictionResponse)
async def get_prediction(shipment_id: str):
    """
    Retrieve ML prediction for a specific shipment.
    
    Returns delay probability, estimated delay range (confidence interval),
    and explainability factors.
    """
    doc = db.collection("live_tracking").document(shipment_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail=f"Shipment {shipment_id} not found")
    return _doc_to_prediction(doc.id, doc.to_dict())


@app.get("/api/fleet/summary", response_model=FleetSummary)
async def get_fleet_summary():
    """
    Fleet-wide KPI summary for dashboard and alerting systems.
    
    Returns aggregate counts (on-time, at-risk, delayed) and
    identifies high-risk shipments requiring attention.
    """
    docs = db.collection("live_tracking").stream()
    
    total = 0
    on_time = 0
    at_risk = 0
    delayed = 0
    prob_sum = 0.0
    high_risk = []

    for doc in docs:
        data = doc.to_dict()
        total += 1
        prob = data.get("ml_delay_probability", 0.0)
        prob_sum += prob
        
        status = _classify_status(prob)
        if status == "delayed":
            delayed += 1
            high_risk.append(doc.id)
        elif status == "at_risk":
            at_risk += 1
        else:
            on_time += 1

    return FleetSummary(
        total_active=total,
        on_time=on_time,
        at_risk=at_risk,
        delayed=delayed,
        avg_delay_probability=round(prob_sum / max(total, 1), 1),
        high_risk_shipments=high_risk,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# ── TMS/WMS Webhook Endpoint ─────────────────────────────────

@app.post("/api/webhook/notify")
async def webhook_notify(payload: WebhookPayload):
    """
    Simulated webhook endpoint for TMS/WMS/OMS integration.
    
    In production, this would trigger:
    - Customer notification (SMS/email/push) for delay_detected
    - Route re-optimization for reroute_suggested
    - ETA update propagation for eta_updated
    """
    # Log the webhook event
    print(f"[WEBHOOK] {payload.event_type} for {payload.shipment_id}: {payload.message}")
    
    return {
        "status": "accepted",
        "event_type": payload.event_type,
        "shipment_id": payload.shipment_id,
        "message": f"Webhook processed: {payload.event_type}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Demo Trigger Endpoints ────────────────────────────────────

@app.post("/api/trigger_storm/{shipment_id}")
async def trigger_storm(shipment_id: str):
    """Force a severe storm scenario on a specific shipment."""
    doc_ref = db.collection("live_tracking").document(shipment_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail=f"Shipment {shipment_id} not found")

    doc_ref.update(
        {
            "weather_condition": "Storm",
            "traffic_index": 10,
            "warehouse_backlog_index": 9,
            "current_speed_kmh": 8.0,
        }
    )
    return {"status": "ok", "message": f"⛈️ Storm triggered on {shipment_id}"}


@app.post("/api/clear_storm/{shipment_id}")
async def clear_storm(shipment_id: str):
    """Clear storm conditions for a specific shipment."""
    doc_ref = db.collection("live_tracking").document(shipment_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail=f"Shipment {shipment_id} not found")

    doc_ref.update(
        {
            "weather_condition": "Clear",
            "traffic_index": 3,
            "warehouse_backlog_index": 2,
            "current_speed_kmh": 55.0,
        }
    )
    return {"status": "ok", "message": f"☀️ Storm cleared on {shipment_id}"}


@app.get("/")
async def root():
    return {
        "service": "Predictive Logistics API",
        "version": "2.0.0",
        "status": "running",
        "endpoints": [
            "GET  /api/predictions",
            "GET  /api/predictions/{shipment_id}",
            "GET  /api/fleet/summary",
            "POST /api/webhook/notify",
            "POST /api/trigger_storm/{shipment_id}",
            "POST /api/clear_storm/{shipment_id}",
        ],
    }
