"""Build a curated source ZIP and copy Python distributions into a new release."""
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
import argparse
import tomllib
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--windows", action="store_true", help="Include the tested Windows portable folder")
args = parser.parse_args()
version = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
release = root / "releases" / ("v" + version)
if release.exists():
    raise SystemExit("Release already exists; frozen releases must not be overwritten.")
names = json.loads((root / "public_files.json").read_text(encoding="utf-8"))
if len(names) != len(set(names)):
    raise SystemExit("Duplicate public paths.")
for name in names:
    path = (root / name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise SystemExit(f"Invalid release file: {name}")
    if any(p in {"private", "outputs", ".venv", "runtime"} for p in path.relative_to(root).parts):
        raise SystemExit(f"Private or generated file in public manifest: {name}")
windows = root / "dist/windows/AgarwoodMiniMS"
if args.windows:
    for required in ("AgarwoodMiniMS.exe", "_internal/python312.dll", "runtime-versions.json", "README.md", "README.zh-CN.md"):
        if not (windows / required).is_file():
            raise SystemExit(f"Missing Windows distribution file: {required}")
subprocess.run([sys.executable, "-m", "build"], cwd=root, check=True)
artifacts = [root / f"dist/agarwood_minims-{version}-py3-none-any.whl",
             root / f"dist/agarwood_minims-{version}.tar.gz"]
for artifact in artifacts:
    if not artifact.is_file():
        raise SystemExit(f"Missing distribution: {artifact}")
release.mkdir(parents=True)
with zipfile.ZipFile(release / f"AgarwoodMiniMS-{version}-source.zip", "w", zipfile.ZIP_DEFLATED) as archive:
    for name in names:
        archive.write(root / name, f"AgarwoodMiniMS-{version}/" + name)
for artifact in artifacts:
    shutil.copy2(artifact, release / artifact.name)
if args.windows:
    with zipfile.ZipFile(release / f"AgarwoodMiniMS-{version}-Windows-x64.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(windows.rglob("*")):
            if path.is_file():
                archive.write(path, "AgarwoodMiniMS/" + path.relative_to(windows).as_posix())
lines = [hashlib.sha256(p.read_bytes()).hexdigest() + "  " + p.name
         for p in sorted(release.iterdir()) if p.is_file()]
(release / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(release)
