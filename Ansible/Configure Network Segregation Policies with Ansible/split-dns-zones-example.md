# Split-DNS Zone Design

One DNS server (`l1ad.g5.local`, co-located with the Domain Controller) is
authoritative for two logically separate namespaces, so internal and
external clients resolving the same name get different, appropriate
answers.

| Zone | Example record | Resolves to | Audience |
|---|---|---|---|
| `g5.local` (internal) | `container1.g5.local` | Container host's internal IP | Internal hosts only |
| `g5.external` (external) | `corpweb.g5.external` | External router's public IP | Internet clients |

**Internal zone (`g5.local`) — excerpt:**
```
$ORIGIN g5.local.
l1ad        IN A   10.10.10.10
container1  IN A   10.10.10.20
user1       IN A   10.10.10.30
router1     IN A   10.10.10.1
```

**External zone (`g5.external`) — excerpt:**
```
$ORIGIN g5.external.
corpweb     IN A   172.16.2.33
fileshare   IN A   172.16.2.33
intweb      IN A   172.16.2.33
```

This achieves segmentation without standing up a second DNS server:
internal lookups never leave the internal zone, and nothing on the
external zone discloses internal addressing.
