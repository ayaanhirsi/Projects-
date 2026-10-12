"""FastAPI IDS service. Run with: python main.py  (listens on port 5000)."""
import uvicorn
from fastapi import FastAPI
from pydantic import ValidationError

from app import alerts, sheets
from app.config import PORT
from app.models import ModelBundle
from app.pipeline import analyze_flow
from app.schemas import FlowData, BatchRequest

app = FastAPI(title="ML-Powered Intrusion Detection Service")
models = None


@app.on_event("startup")
def load_models():
    global models
    models = ModelBundle()


@app.post("/analyze")
def analyze(flow: FlowData):  # invalid input -> automatic 422
    data = flow.model_dump()
    try:
        result = analyze_flow(data, models)
    except Exception as exc:
        return {"error": f"Prediction failed: {exc}"}

    if result["verdict"] == "malicious":
        alerts.send_flow_alert(data, result["attack_type"],
                               result["_reputation_full"], result["geolocation"])
    else:
        sheets.log_normal_flow(data)

    result.pop("_reputation_full")
    return result


@app.post("/analyze/batch")
def analyze_batch(batch: BatchRequest):
    results, threat_ips = [], []
    for i, raw in enumerate(batch.flows):
        try:
            data = FlowData(**raw).model_dump()
            r = analyze_flow(data, models)
            if r["verdict"] == "malicious":
                threat_ips.append(data["src_ip"])
            r.pop("_reputation_full")
            results.append({"index": i, "verdict": r["verdict"], "attack_type": r["attack_type"]})
        except (ValidationError, Exception) as exc:  # skip bad rows, keep going
            results.append({"index": i, "error": str(exc)[:200]})

    if batch.flows:
        alerts.send_batch_summary(len(batch.flows), len(threat_ips), sorted(set(threat_ips))[:5])
    return {"results": results}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT)
