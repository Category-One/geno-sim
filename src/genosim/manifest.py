# Copyright (c) 2026 Category One Limited. All rights reserved.
# Licensed for inspection, execution and verification only. See LICENSE.

"""Provenance manifest.

Every output directory carries a manifest.json recording exactly what
produced the numbers in it. This is what lets a reviewer trace a figure in
your paper back to a reproducible run.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from .config import RunConfig


def _git_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:
        pass
    return "unavailable"


def _git_dirty() -> bool:
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return bool(out.stdout.strip())
    except Exception:
        return True


def _package_versions() -> dict[str, str]:
    versions = {}
    for name in ("numpy", "pandas", "yaml"):
        try:
            mod = __import__(name)
            versions[name] = getattr(mod, "__version__", "unknown")
        except ImportError:
            versions[name] = "not installed"
    return versions


def file_digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest(
    outdir: Path, cfg: RunConfig, outputs: list[Path]
) -> Path:
    """Write manifest.json describing this run.

    The timestamp is recorded for human reference only. It is never read by
    the simulator, so it cannot affect results.
    """
    manifest = {
        "run_name": cfg.name,
        "seed": cfg.seed,
        "config_hash": cfg.content_hash(),
        "config": cfg.to_dict(),
        "git_commit": _git_commit(),
        "git_dirty": _git_dirty(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "packages": _package_versions(),
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "outputs": [
            {"file": p.name, "sha256": file_digest(p)}
            for p in outputs
            if p.exists()
        ],
    }
    path = outdir / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return path
