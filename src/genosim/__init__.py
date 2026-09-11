# Copyright (c) 2026 Category One Limited. All rights reserved.
# Licensed for inspection, execution and verification only. See LICENSE.

"""Geno Project simulation harness.

Reproducibility contract: a run is fully determined by (config file, seed).
No module in this package may call a global RNG or read wall-clock time
inside the simulation loop.
"""

__version__ = "0.1.0"
