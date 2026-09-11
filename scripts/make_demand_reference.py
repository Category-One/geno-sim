# Copyright (c) 2026 Category One Limited. All rights reserved.
# Licensed for inspection, execution and verification only. See LICENSE.

"""Regenerate demand reference fixtures. Run deliberately; explain in the commit."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
from genosim.demand import run_demand, summarise_demand           # noqa: E402
from genosim.demand_config import content_hash, load_demand_config  # noqa: E402
from genosim.manifest import _package_versions                     # noqa: E402

REF = ROOT / "reference"; REF.mkdir(exist_ok=True)
for p in sorted((ROOT / "configs" / "demand").glob("*.yaml")):
    c = load_demand_config(p)
    (REF / f"demand_{p.stem}.json").write_text(json.dumps({
        "config_hash": content_hash(c), "seed": c.seed,
        "python": sys.version.split()[0], "packages": _package_versions(),
        "summary": summarise_demand(run_demand(c)),
    }, indent=2, sort_keys=True))
    print(f"wrote demand_{p.stem}.json")
