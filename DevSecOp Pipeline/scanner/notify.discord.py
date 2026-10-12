#!/usr/bin/env python3
"""
Posts a summary of the static-analysis and dependency-scan results to a
Discord channel via webhook, so the team sees new findings as soon as a
pipeline run finishes instead of hunting through CI logs.

Usage:
    python3 notify_discord.py --semgrep scanners/semgrep-results.json \
                               --grype scanners/grype-results.json

Requires the DISCORD_WEBHOOK_URL environment variable to be set
(stored as a Gitea Actions secret, never committed to the repo).
"""
import argparse
import json
import os
import sys

import requests


def count_semgrep_findings(path: str) -> int:
    with open(path) as f:
        data = json.load(f)
    return len(data.get("results", []))


def count_grype_findings(path: str) -> int:
    with open(path) as f:
        data = json.load(f)
    return len(data.get("matches", []))


def build_message(semgrep_count: int, grype_count: int) -> dict:
    return {
        "content": (
            f"**Security scan complete**\n"
            f"Static analysis (Semgrep): {semgrep_count} finding(s)\n"
            f"Dependency scan (Grype): {grype_count} vulnerability(ies)\n"
        )
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--semgrep", required=True)
    parser.add_argument("--grype", required=True)
    args = parser.parse_args()

    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("DISCORD_WEBHOOK_URL not set; skipping notification.", file=sys.stderr)
        return 0

    semgrep_count = count_semgrep_findings(args.semgrep)
    grype_count = count_grype_findings(args.grype)
    payload = build_message(semgrep_count, grype_count)

    resp = requests.post(webhook_url, json=payload, timeout=10)
    resp.raise_for_status()
    print(f"Notified Discord: {semgrep_count} Semgrep / {grype_count} Grype findings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
