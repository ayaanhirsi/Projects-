# Ansible Network Segregation & Firewall Automation

Automated deployment of host-specific `nftables` firewall rules and a
split-DNS configuration across a segmented internal network, built for a
network security lab exercise.

## What this does

- Uses an Ansible inventory (`inventory/inventory.ini`) to group hosts by
  role: Admin control node, Active Directory/DNS, Container/reverse proxy,
  and User workstation.
- A single playbook (`playbooks/deploy_firewall.yml`) pushes the correct
  `nftables` profile to each host, enables the service, and verifies the
  ruleset is active — no manual per-host configuration.
- Implements split-DNS so internal clients resolve internal IPs while
  external clients resolve the public-facing IP, without running a second
  DNS server (see `split-dns-zones-example.md`).

## Repo layout

```
inventory/inventory.ini          Host groups (ad, container, user, admin)
playbooks/deploy_firewall.yml    Deploy + validate firewalls across all hosts
firewall/*_nft.conf              Per-host-role nftables profiles
split-dns-zones-example.md       Internal vs. external DNS zone design
```

## Running it

```bash
cd playbooks
ansible-playbook -i ../inventory/inventory.ini deploy_firewall.yml
```

The playbook:
1. Installs `nftables` if missing.
2. Copies the host's matching profile from `firewall/` to
   `/etc/nftables.conf` (keeping a backup of the previous file).
3. Enables and restarts the `nftables` service.
4. Runs `nft list ruleset` on each host and reports how many rules are
   active, as a quick sanity check post-deploy.

## Design notes

- Every firewall profile defaults to **deny**, with explicit allow rules
  for SSH from the Admin management subnet, the specific service ports a
  given host needs, and a rate limit on new TCP connections (`tcp flags
  syn limit rate ...`) to blunt SYN-flood style traffic.
- Centralizing rules in Ansible instead of editing hosts by hand removes
  configuration drift and makes the ruleset auditable — the ruleset in
  Git *is* the ruleset in production.

## Environment

This was built and tested in an isolated VM lab (`g5.local` /
`g5.external` are lab-only domains, not a real network). Addresses in the
sample configs are placeholders from that lab and aren't publicly routable
or in use anywhere.
