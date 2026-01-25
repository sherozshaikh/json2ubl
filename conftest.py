"""
Pytest configuration for json2ubl tests.
Adds src directory to sys.path to allow imports of json2ubl package.
"""

import sys
from pathlib import Path

# Add src directory to Python path so that 'import json2ubl' works
# This handles both:
# 1. Running from json2ubl/ directory: src is at ./src
# 2. Running from parent directory: src is at ./json2ubl/src
src_path_1 = Path(__file__).parent / "src"
src_path_2 = Path(__file__).parent.parent / "json2ubl" / "src"

for src_path in [src_path_1, src_path_2]:
    if src_path.exists() and str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
        print(f"Added to sys.path: {src_path}")
        break
