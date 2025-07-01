#!/usr/bin/env python3
"""Test imports to diagnose the issue"""

import sys
print("Python version:", sys.version)
print("Python executable:", sys.executable)
print("\nPython path:")
for p in sys.path:
    print(f"  - {p}")

print("\n\nTesting imports:")

# Test 1: Basic imports
try:
    import os
    print("✅ os module imported")
except Exception as e:
    print(f"❌ os import failed: {e}")

# Test 2: Flet import
try:
    import flet
    print(f"✅ flet module imported (version: {flet.__version__})")
except Exception as e:
    print(f"❌ flet import failed: {e}")

# Test 3: Local imports
try:
    from src.managers.enhanced_state import EnhancedStateManager
    print("✅ Local imports working")
except Exception as e:
    print(f"❌ Local import failed: {e}")

# Test 4: Check if flet is in installed packages
try:
    import pkg_resources
    installed = [pkg.key for pkg in pkg_resources.working_set]
    if 'flet' in installed:
        print("✅ flet found in installed packages")
    else:
        print("❌ flet not found in installed packages")
except:
    pass

print("\nDiagnostics complete!")