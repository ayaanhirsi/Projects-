#!/usr/bin/env python3
"""
CIS Control 8 / 13 — detects a burst of failed authentication attempts in
the forwarded auth log and raises an alert. Intended to run as a cron job
against the central log collector's auth.log.

Usage:
    python3 alert_on_failed_logins.py --log /var/log/auth-central.log \
                                       --threshold 5 --window-minutes 10
"""
import argparse
import re
from collections import defaultdict
from datetime import datetime, timedelta

FAILED_LOGIN_RE = re.compile(
    r"(?P<month>\w{3})\s+(?P<day>\d+)\s+(?P<time>\d{2}:\d{2}:\d{2}).*"
    r"Failed password for (?:invalid user )?(?P<user>\S+) from (?P<ip>\d+\.\d+\.\d+\.\d+)"
)


def parse_line(line: str, year: int):
    m = FAILED_LOGIN_RE.search(line)
    if not m:
        return None
    ts = datetime.strptime(
        f"{year} {m['month']} {m['day']} {m['time']}", "%Y %b %d %H:%M:%S"
    )
    return ts, m["user"], m["ip"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", required=True)
    parser.add_argument("--threshold", type=int, default=5)
    parser.add_argument("--window-minutes", type=int, default=10)
    parser.add_argument("--year", type=int, default=datetime.now().year)
    args = parser.parse_args()

    attempts_by_ip: dict[str, list[datetime]] = defaultdict(list)

    with open(args.log) as f:
        for line in f:
            parsed = parse_line(line, args.year)
            if not parsed:
                continue
            ts, user, ip = parsed
            attempts_by_ip[ip].append(ts)

    window = timedelta(minutes=args.window_minutes)
    alerts = []
    for ip, timestamps in attempts_by_ip.items():
        timestamps.sort()
        for i in range(len(timestamps)):
            burst = [t for t in timestamps[i:] if t - timestamps[i] <= window]
            if len(burst) >= args.threshold:
                alerts.append((ip, len(burst), timestamps[i], timestamps[i] + window))
                break

    if not alerts:
        print("No brute-force patterns detected.")
        return 0

    print(f"ALERT: {len(alerts)} source(s) exceeded {args.threshold} failed logins "
          f"within {args.window_minutes} minutes:")
    for ip, count, start, end in alerts:
        print(f"  - {ip}: {count} attempts between {start} and {end}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
