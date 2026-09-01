# Host baselines

Off-host reference data for the audit workflow's `host` scope. Repo-level, so
`PROCESS.md` §3 and §4 do not apply here — the same carve-out as `bin/`
(decision 21). Baselines legitimately change whenever a host is patched, and an
immutable `Tooling/v<version>/` cannot hold something that must churn.

## What is stored here, and what is not

| Stored | Not stored |
|---|---|
| The AIDE config fragment deployed to every host | The AIDE databases themselves |
| The sha256 of each host's `aide.db` | Any credential, key or host secret |
| A per-host record: OS, kernel, entry count, size, date | Scan output (that belongs in `Tests/`) |

**The databases stay on their hosts.** The security property an off-host copy
buys is *tamper-evidence* — a compromised host can rewrite its own `aide.db`,
but it cannot rewrite this repo. A sha256 delivers that in 64 bytes. Storing the
databases would add ~50 MB per patch cycle to git history, forever, in exchange
for disaster recovery that the backup rail already covers.

## Verifying a host has not had its baseline swapped

```bash
ssh <host> 'sha256sum /var/lib/aide/aide.db'      # compare to aide.db.sha256 here
```

A mismatch means one of two things: the host was legitimately re-baselined and
this record was not updated, or the database was replaced. Neither is a verdict
on its own — but an unexplained mismatch is a finding, not noise.

## Re-baselining

Re-baseline after any legitimate change to system binaries or config — a
distribution upgrade, a package install, a deliberate config edit. Then update
the sha256 here in the same change, with a note saying what caused it. A
baseline whose hash is stale is worse than none, because it trains the reader to
ignore mismatches.

```bash
ssh <host> 'aideinit -y -f && cp -f /var/lib/aide/aide.db.new /var/lib/aide/aide.db \
            && sha256sum /var/lib/aide/aide.db'
```

## What a clean AIDE check does and does not prove

It proves **no watched file changed since the baseline was taken**. It does not
prove the host is clean.

Both baselines here were taken on 2026-09-01, after the hosts had already run
for 4 days and 2.5 weeks respectively **with no security tooling installed at
all**. A first baseline records whatever state the host is already in. If
something was present beforehand, this baseline enshrines it rather than
flagging it.

The checks that can speak to state *without* a prior baseline are `debsums`
(every packaged file against the distribution's own checksums) and the
signature-based half of `chkrootkit` / `rkhunter`. Both hosts passed those on
2026-09-01. That is meaningful evidence and it is not proof: a competent implant
defeats all three.

## Proven, not assumed

AIDE detection was verified by negative control on `n8n.arius.au`, 2026-09-01 —
a scoped baseline over a temporary tree, checked clean, then one watched file
appended to and re-checked:

```
GOOD tree      -> exit=0   AIDE found NO differences
TAMPERED tree  -> exit=4   Changed entries: 1
  File: .../config.conf
   Size    : 17        | 26
   SHA256  : UWrXs4iy… | 99ug/cMM…
```

**`aide --check` exits non-zero when it succeeds at detecting.** A wrapper
running under `set -e` therefore dies at the moment it finds something. This bit
during the run above and is recorded here so it is not rediscovered.
