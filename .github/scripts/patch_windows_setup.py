"""Patch setup.py in the current directory for Windows compatibility.

Replaces compiler flags that cause build failures on MSVC:
  /GR-  ->  /GR   (re-enable RTTI, required by PyTorch headers)
  /MT   ->  /MD   (use DLL runtime, required to match Python's CRT)
"""
from pathlib import Path

setup_py = Path("setup.py")
if setup_py.exists():
    text = setup_py.read_text(encoding="utf-8")
    modified = False
    if '"/GR-"' in text:
        text = text.replace('"/GR-"', '"/GR"')
        modified = True
    if '"/MT"' in text:
        text = text.replace('"/MT"', '"/MD"')
        modified = True
    if modified:
        setup_py.write_text(text, encoding="utf-8")
        print("Patched Windows compile flags in setup.py")
    else:
        print("No Windows flag patches needed in setup.py")
else:
    print("setup.py not found — skipping Windows flag patch")
