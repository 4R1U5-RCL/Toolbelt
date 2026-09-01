# n8n.arius.au — AIDE baseline record

| | |
|---|---|
| Hostname | `Operand` (n8n.arius.au, 5.223.61.119) |
| Role | Self-hosted n8n + webhooks, Hetzner Singapore |
| OS / kernel | Ubuntu 26.04.1 LTS / 7.0.0-30-generic / amd64 |
| AIDE | 0.19.2 |
| Baseline taken | 2026-09-01T06:55Z |
| Entries | 87,847 |
| Database size | 25,244,426 bytes |
| `aide.db` sha256 | `dad9dfe67801cc0017d4003bfc3e19086a37692d892c45ec3ebbc6bc7b25396b` |

Before tuning this baseline held **846,423** entries at 239 MB; 758,092 of them
(89.6%) were `/var/lib/containerd` and `/var/lib/docker` image layers. See
`../aide.conf.d/99_studio_exclude`.
