"""Core decision logic shared by /analyze and /analyze/batch."""
from app.features import apply_inference_engineering
from app.enrichment import get_reputation, get_geolocation


def analyze_flow(flow: dict, models) -> dict:
    features = apply_inference_engineering(flow)
    is_malicious, attack_type = models.predict(features)

    reputation = get_reputation(flow["src_ip"])

    # Hybrid decision: a bad reputation overrides a "normal" ML verdict
    if not is_malicious and reputation["abuse_score"] > 0:
        is_malicious, attack_type = True, "reputation_override"

    geo = get_geolocation(flow["src_ip"]) if is_malicious else None

    return {
        "verdict": "malicious" if is_malicious else "normal",
        "attack_type": attack_type,
        "reputation": reputation["abuse_score"] if is_malicious else None,
        "geolocation": geo,
        "_reputation_full": reputation,
    }
