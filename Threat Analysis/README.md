# Threat and Vulnerability Risk Assessment (TVRA)

A structured risk assessment of a segmented lab network, scoring each
threat event against likelihood and impact to produce a residual risk
rating, following a standard TVRA methodology (adapted from NIST SP
800-30 style adversarial/non-adversarial risk scoring).

This is a documentation deliverable, not a code project — the workbook
(`TVRA.xlsx`, not included publicly, see note below) contains four
linked sheets:

1. **TVRA** — adversarial and non-adversarial risk scoring per threat
   event: threat source, capability, intent, likelihood, severity,
   control effectiveness, and residual risk after controls.
2. **Vulnerabilities Catalog** — 10 identified vulnerabilities (e.g.,
   DNS zone transfer exposure, unencrypted proxy traffic, missing
   security headers), each mapped to an affected component and impact
   type.
3. **Threat Source Catalog** — groups vulnerabilities by the underlying
   threat pattern (e.g., reconnaissance, credential sniffing, service
   dependency failure).
4. **Security Controls Catalog** — the NIST 800-53 control IDs (e.g.
   AC-2, IA-2, SC-7) mapped to each mitigation.

## Example finding

| Threat event | Source | Vulnerability | Controls | Overall likelihood | Residual risk |
|---|---|---|---|---|---|
| Exploit poorly configured internet-facing systems | Outsider | VID-002 | AC-3, AC-4, SC-7 | Very High | High |
| Zone transfer allowed (DNS reconnaissance) | Outsider | VID-001 | SC-7, SI-4, AC-3 | High | Moderate |

## Why it's not published in full

The workbook names the specific lab network's addressing and service
layout. Since risk assessments map exactly where a system's weak points
are, I'm keeping the full workbook private and sharing this summary
instead — available on request for anyone reviewing my application.
