# Copyright (c) 2026 Category One Limited. All rights reserved.
# Licensed for inspection, execution and verification only. See LICENSE.

"""Regenerate reference fixtures used by test_matches_stored_reference.

Run deliberately, after an intentional model change, and explain the change
in the commit message. Never run it to make a failing test pass.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from genosim.config import load_config  # noqa: E402
from genosim.engine import run  # noqa: E402
from genosim.manifest import _package_versions  # noqa: E402
from genosim.sweep import summarise  # noqa: E402

REFERENCE = ROOT / "reference"


def main() -> int:
    REFERENCE.mkdir(exist_ok=True)
    for path in sorted((ROOT / "configs").glob("*.yaml")):
        if "sweep" in path.stem:
            continue
        cfg = load_config(path)
        fixture = {
            "config_hash": cfg.content_hash(),
            "seed": cfg.seed,
            "packages": _package_versions(),
            "python": sys.version.split()[0],
            "summary": summarise(run(cfg)),
        }
        out = REFERENCE / f"{path.stem}.json"
        out.write_text(json.dumps(fixture, indent=2, sort_keys=True))
        print(f"wrote {out.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
