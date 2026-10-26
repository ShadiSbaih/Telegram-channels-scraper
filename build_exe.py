"""
Automated Build Script for TelegramScraper.exe
Runs PyInstaller using TelegramScraper.spec and reports build status.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def main():
    root_dir = Path(__file__).resolve().parent
    os.chdir(root_dir)

    print("==================================================")
    print("[*] Building TelegramScraper.exe (Windows Standalone)")
    print("==================================================")

    # Clean previous build directories if desired
    build_dir = root_dir / "build"
    dist_dir = root_dir / "dist"

    if build_dir.exists():
        print("Cleaning previous build/ folder...")
        shutil.rmtree(build_dir, ignore_errors=True)

    # Python executable from current venv
    python_exe = sys.executable
    print(f"Using Python: {python_exe}")

    cmd = [
        python_exe,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "TelegramScraper.spec",
    ]

    print("Running PyInstaller...")
    res = subprocess.run(cmd)

    if res.returncode != 0:
        print(f"\n[!] Build failed with return code {res.returncode}")
        sys.exit(res.returncode)

    exe_path = dist_dir / "TelegramScraper.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print("\n==================================================")
        print("[+] Build Succeeded!")
        print(f"Directory: {dist_dir}")
        print(f"Executable: {exe_path.name}")
        print(f"File Size: {size_mb:.2f} MB")
        print("==================================================")
    else:
        print("\n[!] Executable was not found in dist directory.")
        sys.exit(1)


if __name__ == "__main__":
    main()
