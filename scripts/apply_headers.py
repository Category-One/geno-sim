"""Apply the copyright header to every source file. Idempotent."""
from pathlib import Path

HEADER = '''# Copyright (c) 2026 Category One Limited. All rights reserved.
# Licensed for inspection, execution and verification only. See LICENSE.
'''
MARK = "Category One Limited"
ROOT = Path(__file__).parent.parent

changed = 0
for path in sorted(ROOT.rglob("*.py")):
    if "__pycache__" in str(path) or path.name == "apply_headers.py":
        continue
    text = path.read_text()
    if MARK in text[:400]:
        continue
    path.write_text(HEADER + "\n" + text)
    changed += 1
    print(f"header added: {path.relative_to(ROOT)}")
print(f"\n{changed} file(s) updated")
