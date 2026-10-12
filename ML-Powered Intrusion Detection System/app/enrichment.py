"""Threat intelligence: AbuseIPDB reputation + ipinfo geolocation, with safe fallbacks."""
import requests

from app.config import ABUSEIPDB_API_KEY, IPINFO_TOKEN

TIMEOUT = 5


def get_reputation(ip: str) -> dict:
    """AbuseIPDB abuse confidence score. Never raises: returns a fallback on failure."""
    fallback = {"abuse_score": 0, "available": False}
    if not ABUSEIPDB_API_KEY:
        return fallback
    try:
        r = requests.get(
            "https://api.abuseipdb.com/api/v2/check",
            headers={"Key": ABUSEIPDB_API_KEY, "Accept": "application/json"},
            params={"ipAddress": ip, "maxAgeInDays": 90},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        score = r.json()["data"]["abuseConfidenceScore"]
        return {"abuse_score": score, "available": True}
    except Exception:  # timeout, quota (429), bad JSON, etc.
        return fallback


def get_geolocation(ip: str) -> dict:
    """ipinfo geolocation + ASN/ISP. Returns 'Unknown' values on failure."""
    unknown = {"country": "Unknown", "region": "Unknown", "city": "Unknown", "org": "Unknown"}
    try:
        r = requests.get(f"https://ipinfo.io/{ip}/json",
                         params={"token": IPINFO_TOKEN} if IPINFO_TOKEN else None,
                         timeout=TIMEOUT)
        r.raise_for_status()
        d = r.json()
        return {
            "country": d.get("country", "Unknown"),
            "region": d.get("region", "Unknown"),
            "city": d.get("city", "Unknown"),
            "org": d.get("org", "Unknown"),
        }
    except Exception:
        return unknown
