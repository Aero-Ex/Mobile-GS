"""Patch setup.py in the current directory for Windows compatibility.

Replaces compiler flags that cause build failures on MSVC:
  /GR-  ->  /GR   (re-enable RTTI, required by PyTorch headers)
  /MT   ->  /MD   (use DLL runtime, required to match Python's CRT)

Injects Windows-specific nvcc flags to fix MSVC C2872 'std' ambiguous
symbol errors introduced in newer PyTorch versions (e.g. 2.10.0):
  -DNOMINMAX                     – prevent Windows.h min/max macro pollution
  --compiler-options=/Zc:__cplusplus – enable correct C++ standard version
                                       detection so MSVC uses the right
                                       inline-namespace rules
"""
import re
from pathlib import Path

# Windows-specific nvcc flags injected into every CUDAExtension.
_WIN_NVCC_FLAGS = ["-DNOMINMAX", "--compiler-options=/Zc:__cplusplus"]

# Compiled once at module level for efficiency.
_EMPTY_NVCC_PATTERN = re.compile(r'("nvcc"\s*:\s*)\[\s*\]')
_NONEMPTY_NVCC_PATTERN = re.compile(r'("nvcc"\s*:\s*\[)')


def _inject_nvcc_flags(text: str) -> tuple[str, bool]:
    """Insert _WIN_NVCC_FLAGS into the nvcc extra_compile_args list.

    Handles both an empty list (``"nvcc": []``) and a non-empty list
    (``"nvcc": ["existing", ...]``).  All occurrences are patched.
    Already-present flags are not duplicated.
    """
    modified = False
    for flag in _WIN_NVCC_FLAGS:
        # Skip if the flag is already present anywhere in the file.
        if flag in text:
            continue
        if _EMPTY_NVCC_PATTERN.search(text):
            # Replace every [] with [flag] (covers multiple extensions).
            text = _EMPTY_NVCC_PATTERN.sub(
                lambda m, f=flag: m.group(1) + f'["{f}"]', text
            )
        elif _NONEMPTY_NVCC_PATTERN.search(text):
            # Insert flag at the start of every existing list.
            text = _NONEMPTY_NVCC_PATTERN.sub(
                lambda m, f=flag: m.group(1) + f'"{f}", ', text
            )
        else:
            continue
        modified = True
    return text, modified


setup_py = Path("setup.py")
if setup_py.exists():
    text = setup_py.read_text(encoding="utf-8")
    modified = False

    # --- Existing host-compiler flag patches ---
    if '"/GR-"' in text:
        text = text.replace('"/GR-"', '"/GR"')
        modified = True
    if '"/MT"' in text:
        text = text.replace('"/MT"', '"/MD"')
        modified = True

    # --- Inject Windows-specific nvcc flags ---
    text, nvcc_modified = _inject_nvcc_flags(text)
    modified = modified or nvcc_modified

    if modified:
        setup_py.write_text(text, encoding="utf-8")
        print("Patched Windows compile flags in setup.py")
    else:
        print("No Windows flag patches needed in setup.py")
else:
    print("setup.py not found — skipping Windows flag patch")
