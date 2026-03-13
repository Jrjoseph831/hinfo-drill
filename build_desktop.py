#!/usr/bin/env python3
"""
build_desktop.py - Build a standalone desktop executable for Health Informatics Drill.

Installs build dependencies, then runs PyInstaller to produce a single-file
executable for the current platform.

Usage
-----
    python build_desktop.py            # build with native window (pywebview)
    python build_desktop.py --browser  # build browser-only (skip pywebview)

Output
------
    dist/HealthInformaticsDrill        (Linux / macOS executable)
    dist/HealthInformaticsDrill.exe    (Windows executable)
    dist/HealthInformaticsDrill.app    (macOS app bundle)
"""

import os
import subprocess
import sys
import platform


def run(cmd, desc):
    """Run a shell command, exit on failure."""
    print(f"\n{'='*60}")
    print(f"  {desc}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=isinstance(cmd, str))
    if result.returncode != 0:
        print(f"\nERROR: {desc} failed (exit code {result.returncode})")
        sys.exit(result.returncode)


def main():
    browser_only = "--browser" in sys.argv
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    # 1. Install runtime dependencies
    run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        "Installing runtime dependencies",
    )

    # 2. Install build dependencies
    build_deps = ["pyinstaller"]
    if not browser_only:
        build_deps.append("pywebview")
    run(
        [sys.executable, "-m", "pip", "install"] + build_deps,
        "Installing build dependencies",
    )

    # 3. Run PyInstaller
    run(
        [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", "hinfo_drill.spec"],
        "Building executable with PyInstaller",
    )

    # 4. Report result
    plat = platform.system()
    if plat == "Windows":
        exe_path = os.path.join("dist", "HealthInformaticsDrill.exe")
    elif plat == "Darwin":
        exe_path = os.path.join("dist", "HealthInformaticsDrill.app")
    else:
        exe_path = os.path.join("dist", "HealthInformaticsDrill")

    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024) if os.path.isfile(exe_path) else 0
        print(f"\n{'='*60}")
        print(f"  BUILD SUCCESSFUL")
        print(f"  Output: {os.path.abspath(exe_path)}")
        if size_mb:
            print(f"  Size:   {size_mb:.1f} MB")
        print(f"{'='*60}\n")
    else:
        print(f"\nWARNING: Expected output not found at {exe_path}")
        print("Check the dist/ directory for the built executable.\n")


if __name__ == "__main__":
    main()
