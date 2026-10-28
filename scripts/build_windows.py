"""Build a portable Windows folder; package_release.py archives it after testing."""
import importlib.metadata as metadata
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
if sys.platform != "win32" or platform.machine().upper() != "AMD64":
    raise SystemExit("Build this distribution on 64-bit Windows.")
destination = root / "dist/windows"
support_only = "--support-only" in sys.argv
if (destination / "AgarwoodMiniMS").exists() and not support_only:
    raise SystemExit("Build folder exists; choose a fresh local build before rebuilding.")
command = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--onedir", "--windowed",
           "--name", "AgarwoodMiniMS", "--paths", str(root / "src"),
           "--distpath", str(destination), "--workpath", str(root / "build/windows"),
           "--specpath", str(root / "build"), "--hidden-import", "PIL._tkinter_finder"]
for package in ("numpy", "pandas", "scikit-learn", "joblib"):
    command += ["--copy-metadata", package]
command += [str(root / "scripts/desktop_entry.py")]
if not support_only:
    subprocess.run(command, cwd=root, check=True)
app = destination / "AgarwoodMiniMS"
shutil.copytree(root / "demo", app / "demo", dirs_exist_ok=True)
for name in ("LICENSE", "NOTICE", "CITATION.cff"):
    shutil.copy2(root / name, app / name)
for name in ("README.md", "README.zh-CN.md"):
    shutil.copy2(root / name, app / name)
shutil.copytree(root / "docs/images", app / "docs/images", dirs_exist_ok=True)
licenses = app / "THIRD_PARTY_LICENSES"
licenses.mkdir(exist_ok=True)
runtime = ["numpy", "scipy", "pandas", "scikit-learn", "joblib", "threadpoolctl",
           "matplotlib", "contourpy", "cycler", "fonttools", "kiwisolver", "packaging",
           "pillow", "pyparsing", "python-dateutil", "six", "tzdata", "narwhals"]
inventory = {}
for name in runtime:
    dist = metadata.distribution(name)
    inventory[name] = dist.version
    copied = []
    for item in dist.files or []:
        if any(word in item.name.lower() for word in ("license", "copying", "notice")):
            source = Path(dist.locate_file(item))
            if source.is_file():
                relative = Path(str(item))
                if ".." in relative.parts:
                    continue
                target = licenses / name / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                copied.append(str(relative))
    if not copied:
        text = dist.metadata.get("License")
        if not text or text == "UNKNOWN":
            raise SystemExit(f"Missing third-party license: {name}")
        target = licenses / name
        target.mkdir(exist_ok=True)
        (target / "LICENSE.txt").write_text(text, encoding="utf-8")
base = Path(sys.base_prefix)
for name, source in (("Python", base / "LICENSE.txt"), ("Tcl", root / "third_party/Tcl-8.6.12-LICENSE.txt"), ("Tk", base / "tcl/tk8.6/license.terms")):
    if not source.is_file():
        raise SystemExit(f"Missing runtime license: {source}")
    shutil.copy2(source, licenses / (name + "-LICENSE.txt"))
for source in (root / "third_party").glob("*.txt"):
    shutil.copy2(source, licenses / source.name)
# PyInstaller's bootloader has an exception permitting bundled applications.
dist = metadata.distribution("pyinstaller")
for item in dist.files or []:
    if item.name == "COPYING.txt":
        shutil.copy2(dist.locate_file(item), licenses / "PyInstaller-COPYING.txt")
inventory.update({"python": platform.python_version(), "pyinstaller": metadata.version("pyinstaller"),
                  "pyinstaller-hooks-contrib": metadata.version("pyinstaller-hooks-contrib")})
(app / "runtime-versions.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")
print(app)
