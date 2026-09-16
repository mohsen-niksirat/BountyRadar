#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build a Windows .exe for Bounty Radar Pro with PyInstaller.

Usage (from this folder, after:  pip install pyinstaller):
    python build_exe.py

Output:
    dist/BountyRadar/BountyRadar.exe   (one-folder build, faster start)
    dist/BountyRadar-onefile/BountyRadar.exe  (optional single file if --onefile)
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    onefile = "--onefile" in sys.argv
    name = "BountyRadar"
    work = os.path.join(HERE, "build")
    dist = os.path.join(HERE, "dist")

    icon = os.path.join(HERE, "assets", "app.ico")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name", name,
        "--paths", HERE,
        "--add-data", os.path.join(HERE, "ui") + os.pathsep + "ui",
        "--hidden-import", "tkinter",
    ]
    if os.path.isfile(icon):
        cmd.extend(["--icon", icon])
    if onefile:
        cmd.append("--onefile")
        spec_dist = os.path.join(dist, name + ".exe")
    else:
        # onedir is more reliable for data files + antivirus friendliness
        spec_dist = os.path.join(dist, name, name + ".exe")

    cmd.append(os.path.join(HERE, "bounty_radar.py"))
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd, cwd=HERE)

    # convenience launcher next to the folder build
    if not onefile:
        bat = os.path.join(dist, name, "Bounty Radar.bat")
        with open(bat, "w", encoding="ascii") as f:
            f.write('@echo off\r\ncd /d "%~dp0"\r\nstart "" BountyRadar.exe\r\n')
        print("Launcher:", bat)

    print("\nDone.")
    print("Exe:", spec_dist)
    print("Copy the whole folder (or the one-file exe) to any Windows PC.")
    print("settings.json / claims.json / seen.json are created next to the exe.")


if __name__ == "__main__":
    main()
