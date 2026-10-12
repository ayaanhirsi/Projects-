# Automated DevSecOps Security Pipeline
A six-stage CI/CD security pipeline built with Gitea Actions and live-tested on a self-hosted Gitea v1.26.1 instance. Every step is documented with screenshots in the accompanying PDF report included in this repository.

## Pipeline stages

1. **Static code analysis** — Semgrep, running the OWASP Top 10 ruleset
   plus a project-specific rule (`scanners/semgrep.yml`) written after
   confirming a SQL-injection (CWE-89) finding in Gitea during testing.
2. **Dependency vulnerability scanning** — Grype against the full
   dependency tree.
3. **Build & test** — builds the hardened container image and runs the
   test suite inside it.
4. **Developer notification** — posts a scan summary to a Discord
   channel (`scanners/notify_discord.py`) so findings are visible the
   moment a run finishes.
5. **Automated secure deployment** — deploys the image behind an
   nginx + ModSecurity WAF (`waf/deploy_with_waf.sh`) using the OWASP
   Core Rule Set.
6. **Post-deployment validation** — checks the live service is reachable
   and returning required security headers (`scanners/post_deploy_check.py`).

All six stages run automatically on every push to `main` via
`.gitea/workflows/security-pipeline.yml`.

## Repo layout

```
.gitea/workflows/security-pipeline.yml   The pipeline definition
scanners/semgrep.yml                     Static analysis ruleset
scanners/notify_discord.py               Scan-result -> Discord webhook
scanners/post_deploy_check.py            Live health + header check
waf/deploy_with_waf.sh                   WAF-fronted deployment script
```

## Results from testing against Gitea v1.26.1

- **21** static analysis findings (Semgrep)
- **56** dependency vulnerabilities (Grype)
- **1** high-severity SQL injection vulnerability (CWE-89), confirmed,
  written up with reproduction steps, and prepared for responsible
  disclosure to the Gitea maintainers — see
  [Responsible Disclosure](#responsible-disclosure) below.

## Responsible disclosure

The CWE-89 finding is **not** reproduced here. Exploit details are
withheld until the maintainers have been notified and had a reasonable
window to patch, per standard responsible-disclosure practice. The
regression test added to confirm the fix (once released) lives in a
private branch and will be added here after disclosure closes.

## Running it locally

```bash
# Static analysis
semgrep scan --config scanners/semgrep.yml .

# Dependency scan
grype dir:.

# Deploy behind the WAF
./waf/deploy_with_waf.sh gitea-hardened:local

# Validate
python3 scanners/post_deploy_check.py --url https://localhost
```

`DISCORD_WEBHOOK_URL` must be set as a repo secret for the notification
step; it is never committed.
