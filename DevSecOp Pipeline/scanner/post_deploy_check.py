#!/usr/bin/env python3
"""
Post-deployment validation: confirms the deployed service is reachable,
responding correctly, and sending the security headers the pipeline
expects (CSP, X-Frame-Options, HSTS, etc.) before the run is marked green.

Usage:
    python3 post_deploy_check.py --url https://staging.example.internal
"""
import argparse
import sys

import requests

REQUIRED_HEADERS = [
    "Content-Security-Policy",
    "X-Frame-Options",
    "Strict-Transport-Security",
    "X-Content-Type-Options",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    args = parser.parse_args()

    try:
        resp = requests.get(args.url, timeout=10)
    except requests.RequestException as exc:
        print(f"FAIL: could not reach {args.url}: {exc}", file=sys.stderr)
        return 1

    if resp.status_code >= 400:
        print(f"FAIL: {args.url} returned HTTP {resp.status_code}", file=sys.stderr)
        return 1

    missing = [h for h in REQUIRED_HEADERS if h not in resp.headers]
    if missing:
        print(f"FAIL: missing security headers: {', '.join(missing)}", file=sys.stderr)
        return 1

    print(f"PASS: {args.url} healthy, all required security headers present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
