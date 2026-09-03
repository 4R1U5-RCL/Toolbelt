# Templates — Packages/Sentinel

Production-ready application forms. Each cites the use case it serves in
[`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md) (PROCESS.md §3, reciprocal pair).

| Id | Form | Implementation |
|---|---|---|
| [tpl-cron-wrapper](#tpl-cron-wrapper) | Scheduler wrapper, notify-on-exception | [imp-scheduled-sweep](IMPLEMENTATIONS.md#imp-scheduled-sweep) |
| [tpl-hosts-json](#tpl-hosts-json) | Fleet description | [imp-fleet-config](IMPLEMENTATIONS.md#imp-fleet-config) |
| [tpl-rebaseline](#tpl-rebaseline) | Re-baseline and record | [imp-rebaseline](IMPLEMENTATIONS.md#imp-rebaseline) |

---

## tpl-cron-wrapper

Serves [imp-scheduled-sweep](IMPLEMENTATIONS.md#imp-scheduled-sweep).

```bash
#!/usr/bin/env bash
# NO `set -e`. Sentinel exits non-zero when it FINDS something; under `set -e`
# this wrapper would die at the moment the sweep succeeds.
set -uo pipefail

SENTINEL=/path/to/Packages/Sentinel/Tooling/v1.0.0/bin/sentinel
OUT_DIR=/var/log/sentinel
mkdir -p "$OUT_DIR"

stamp=$(date -u +%Y-%m-%dT%H-%M-%SZ)
report="$OUT_DIR/sweep-$stamp.txt"

"$SENTINEL" sweep "$@" > "$report" 2>&1
code=$?

case "$code" in
  0) ;;                                    # clean — stay silent, the file is the record
  1) notify "Sentinel: FINDING" "$report" ;;
  2) notify "Sentinel: a check could not run" "$report" ;;
  *) notify "Sentinel: unexpected exit $code" "$report" ;;
esac

# Prune, but keep enough history to see a slow drift.
find "$OUT_DIR" -name 'sweep-*.txt' -mtime +90 -delete
exit 0
```

Two cadences, because the cheap check and the expensive one do not want the
same one:

```cron
17 6 * * *   /path/to/sentinel-sweep.sh --only aide_db_fingerprint
41 3 * * 0   /path/to/sentinel-sweep.sh
```

---

## tpl-hosts-json

Serves [imp-fleet-config](IMPLEMENTATIONS.md#imp-fleet-config).

Goes in the **baselines directory** — never in this repo.

```json
{
  "hosts": [
    {
      "name": "host.example",
      "target": "root@203.0.113.10",
      "identity": "~/.ssh/id_ed25519_sweep",
      "aide_db": "/var/lib/aide/aide.db",
      "checks": ["aide", "aide_db_fingerprint", "debsums", "rkhunter"],
      "notes": "Baseline 2026-09-01. Container layers excluded — see aide.conf.d/."
    },
    {
      "name": "this-machine",
      "local": true,
      "checks": ["debsums"],
      "notes": "No target needed. debsums speaks without a prior baseline."
    }
  ]
}
```

`name` must match the directory holding that host's `aide.db.sha256`. `identity`
is how an unattended sweep authenticates: without it, ssh picks whatever key it
likes and a working key reads as a host problem.

---

## tpl-rebaseline

Serves [imp-rebaseline](IMPLEMENTATIONS.md#imp-rebaseline).

```bash
# On the host, after a legitimate change:
aideinit -y -f
cp -f /var/lib/aide/aide.db.new /var/lib/aide/aide.db
sha256sum /var/lib/aide/aide.db
```

Then, in the baselines directory and in the same change:

```markdown
| `aide.db` sha256 | `<new hash>` |
| Baseline taken   | <UTC timestamp> |
| Re-baselined because | <the actual cause — "unattended-upgrades pulled openssl
                          3.0.13-1ubuntu2.5 on 2026-09-14", not "routine"> |
```

Confirm it took:

```bash
sentinel sweep --host <name> --only aide_db_fingerprint   # expect exit 0
```
