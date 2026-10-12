# ML-Powered Intrusion Detection System (Phase 3 – Deployment & Security Automation)

A FastAPI microservice that turns the machine learning models from Phases 1-2 into an operational intrusion detection service. It classifies network flows, enriches results with threat intelligence from AbuseIPDB and ipinfo, logs benign traffic for baselining, and sends real-time Discord alerts for malicious activity. Each stage is documented with annotated screenshots in the accompanying project report.
## Architecture

```
Client (Postman) → FastAPI /analyze → Validation (FlowData)
  → Feature engineering → Binary model (benign / malicious)
      ├─ benign    → AbuseIPDB check → (override if score > 0) → log to Google Sheets
      └─ malicious → Attack-type model + label encoder
                     → AbuseIPDB + ipinfo enrichment → Discord alert
  → JSON response
```

| Component | File |
|---|---|
| API + endpoints | `main.py` |
| Input schema (Pydantic) | `app/schemas.py` |
| Feature engineering | `app/features.py` |
| Model loading / 2-stage prediction | `app/models.py` |
| AbuseIPDB + ipinfo | `app/enrichment.py` |
| Hybrid decision logic | `app/pipeline.py` |
| Discord alerts | `app/alerts.py` |
| Google Sheets logging | `app/sheets.py` |

## Features

- **Two-stage ML**: binary classifier, then attack-type classifier (e.g. DoS, DDoS, PortScan, MITM) decoded to readable labels.
- **Hybrid decision engine**: if the model says normal but the AbuseIPDB score is above 0, the flow is treated as malicious (fewer false negatives).
- **Enrichment**: abuse confidence score plus country, region, city and ISP/ASN.
- **Alerting**: Discord webhook alerts per malicious flow, and a summary alert for batches.
- **Logging**: normal flows appended to Google Sheets for baseline monitoring.
- **Resilient**: strict validation (422), fallbacks for API timeouts/quota errors, try/except around inference, bad batch rows skipped.

## Setup

```bash
python -m venv .venv
source .venv/Scripts/activate      # Windows (Git Bash); use .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp .env.example .env               # then fill in your keys
```

Put your trained model files in `models/` (see `models/README.md`), then:

```bash
python main.py                     # serves on http://127.0.0.1:5000
```

## API

### `POST /analyze`
Single flow: full feature engineering, inference, enrichment; normal traffic is logged to Sheets, malicious traffic triggers a Discord alert.

```json
{
  "src_ip": "91.213.233.16", "dst_ip": "192.168.1.10",
  "src_port": 51234, "dst_port": 443, "proto": "tcp", "duration": 1.345,
  "src_bytes": 958, "dst_bytes": 4388, "conn_state": "SF",
  "missed_bytes": 0, "src_pkts": 12, "src_ip_bytes": 1500,
  "dst_pkts": 15, "dst_ip_bytes": 5000
}
```

Response:

```json
{ "verdict": "malicious", "attack_type": "ddos", "reputation": 0,
  "geolocation": { "country": "KG", "region": "...", "city": "...", "org": "..." } }
```

### `POST /analyze/batch`
Body: `{"flows": [ {...}, {...} ]}`. Skips Sheets logging, sends one summary alert to Discord, returns an array of verdicts and attack types. Invalid rows return an `error` entry and don't stop the rest.

## Results

Tested via Postman: a benign flow returned `normal` with no attack type, and malicious samples were classified (e.g. man-in-the-middle, DDoS) with a real-time Discord alert containing IPs, attack type, geolocation and reputation. Screenshots are in the project report.

## Security notes

- API keys live in environment variables (`.env`, git-ignored), never in source.
- `/analyze` assumes a trusted internal network. For production, add JWT/API-key auth, IP allow-listing or an API gateway.
- AbuseIPDB is rate-limited; caching or backoff is planned.

## Limitations & future work

No SIEM integration, single instance (no scaling), no streaming (Kafka/RabbitMQ), static feature engineering, no explainability. Planned: authentication, database/SIEM storage, dashboard, ensemble models, Docker/Kubernetes.

## Dataset & references

Trained on the ToN-IoT dataset (Moustafa, Creech & Slay, UNSW Canberra). Built with FastAPI, scikit-learn, Pydantic, AbuseIPDB, ipinfo and Discord webhooks.

## Team

Thuruvan, Ayaan, Shiza (Group 1, SRT521).
