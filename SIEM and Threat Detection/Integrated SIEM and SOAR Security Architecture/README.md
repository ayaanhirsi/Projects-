# Automated Cyber Defense & Incident Response Framework

Automation supporting a CIS Top 18 Controls implementation across a
segmented lab network — asset inventory drift detection, centralized
audit logging, and brute-force login alerting.

## What's here

| Script / config | CIS Control | What it does |
|---|---|---|
| `scripts/asset_inventory.py` | Control 1 — Inventory of Enterprise Assets | Scans a subnet, diffs live hosts against a known-asset baseline, and flags anything unrecognized. |
| `configs/assets.json` | Control 1 | The known-asset baseline the inventory script checks against. |
| `configs/rsyslog-central-logging.conf` | Control 8 — Audit Log Management | Forwards auth/firewall/system logs from every host to a central, TLS-authenticated collector so logs survive a compromised host. |
| `scripts/alert_on_failed_logins.py` | Controls 8 & 13 — Audit Log Management / Network Monitoring | Scans the centralized auth log for bursts of failed logins from a single source within a configurable time window and raises an alert. |

## Running the asset inventory check

```bash
python3 scripts/asset_inventory.py --subnet 10.10.10.0/24 --baseline configs/assets.json
```

Exits non-zero if an unrecognized host shows up, so it can be wired into
a scheduled job that pages the on-call person on drift.

## Running the failed-login alert

```bash
python3 scripts/alert_on_failed_logins.py --log /var/log/auth-central.log \
    --threshold 5 --window-minutes 10
```

Flags any IP with 5+ failed logins inside a 10-minute window — tunable
via `--threshold` / `--window-minutes`.

## Scope note

This is a subset of the full CIS Top 18 implementation from the course
project (which also covered configuration management, account
management, malware defenses, data recovery, and more across an 89-page
report). These three pieces are the parts with the clearest automation
story; the rest of the controls were implemented via configuration
(GPOs, backup schedules, endpoint hardening) rather than scripts, so
they aren't represented as code here.
