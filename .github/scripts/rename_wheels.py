"""Move and rename built wheels from dist_temp/ into dist_all/.

Inserts a build tag of the form ``1pt<PT_VERSION>cu<CUDA_VERSION>``
(e.g. ``1pt2_6_0cu12_6``) into the wheel filename so that wheels for
different PyTorch/CUDA combinations can coexist in the same release.

Expected environment variables
--------------------------------
PT_VERSION   : PyTorch version string, e.g. "2.6.0"
CUDA_VERSION : CUDA version string, e.g. "12.6"

Directory layout (relative to repo root)
-----------------------------------------
dist_temp/   – output directory used by ``python -m build``
dist_all/    – accumulation directory for all renamed wheels
"""
import os
import re
from pathlib import Path

pt = os.environ["PT_VERSION"].replace(".", "_")
cu = os.environ["CUDA_VERSION"].replace(".", "_")
build_tag = f"1pt{pt}cu{cu}"

wheel_name_pattern = re.compile(
    r"^(?P<distribution>[^-]+)-(?P<version>[^-]+)"
    r"(?:-(?P<build>[0-9][0-9A-Za-z_]*))?"
    r"-(?P<python_tag>[^-]+)-(?P<abi_tag>[^-]+)-(?P<platform_tag>[^-]+)$"
)

dist_temp = Path("dist_temp")
dist_all = Path("dist_all")
dist_all.mkdir(parents=True, exist_ok=True)

for wheel_path in dist_temp.glob("*.whl"):
    match = wheel_name_pattern.fullmatch(wheel_path.stem)
    if not match:
        print(f"Skipping unrecognised wheel name: {wheel_path.name}")
        continue
    parts = match.groupdict()
    if parts["build"]:
        # Already has a build tag — keep the original name.
        target_name = wheel_path.name
    else:
        target_name = (
            f"{parts['distribution']}-{parts['version']}-{build_tag}-"
            f"{parts['python_tag']}-{parts['abi_tag']}-{parts['platform_tag']}.whl"
        )
    target = dist_all / target_name
    wheel_path.rename(target)
    print(f"Moved and renamed: {target_name}")

# Remove any remaining files in dist_temp so the next submodule starts clean.
for f in dist_temp.glob("*"):
    if f.is_file():
        f.unlink()
