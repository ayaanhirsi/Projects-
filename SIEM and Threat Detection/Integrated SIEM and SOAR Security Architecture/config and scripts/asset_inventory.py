#!/usr/bin/env python3
"""
CIS Control 1 — Inventory of Enterprise Assets.

Sweeps a given subnet with an ARP/ping scan, cross-references discovered
hosts against the known-asset baseline, and flags anything unrecognized
so it can be investigated before it's trusted on the network.

Usage:
    python3 asset_inventory.py --subnet 10.10.10.0/24 --baseline assets.json
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone


def scan_subnet(subnet: str) -> list[str]:
    """Return a list of live host IPs found via nmap ping scan."""
    result = subprocess.run(
        ["nmap", "-sn", subnet, "-oG", "-"],
        capture_output=True, text=True, check=True,
    )
    hosts = []
    for line in result.stdout.splitlines():
        if line.startswith("Host:"):
            hosts.append(line.split()[1])
    return hosts


def load_baseline(path: str) -> set[str]:
    with open(path) as f:
        data = json.load(f)
    return {entry["ip"] for entry in data.get("assets", [])}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subnet", required=True)
    parser.add_argument("--baseline", required=True)
    args = parser.parse_args()

    try:
        live_hosts = scan_subnet(args.subnet)
    except FileNotFoundError:
        print("nmap not found; install it to run the scan.", file=sys.stderr)
        return 1

    known = load_baseline(args.baseline)
    unknown = sorted(set(live_hosts) - known)

    timestamp = datetime.now(timezone.utc).isoformat()
    print(f"[{timestamp}] Scanned {args.subnet}: {len(live_hosts)} host(s) up.")

    if unknown:
        print(f"UNRECOGNIZED hosts ({len(unknown)}):")
        for ip in unknown:
            print(f"  - {ip}")
        return 2  # non-zero so CI / cron can alert on drift

    print("No unrecognized hosts. Inventory matches baseline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
