"""Sentinel — host integrity sweep.

Runs file-integrity and rootkit checks across configured hosts, classifies
what comes back, and reports. The baselines it checks against deliberately
live OUTSIDE this repository; see `config.resolve_baselines_dir`.
"""

__version__ = "1.0.0"
