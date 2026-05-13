#!/usr/bin/env python3
"""
Build script for YT Stream 24/7 — Reencoder
Automates building executables and installers for Windows, macOS, and Linux
"""

import sys
import subprocess
import platform
import shutil
import os
from pathlib import Path

def run_command(cmd, check=True):
    """Run a shell command and return the result."""
    if isinstance(cmd, list):
        # If it's a list, run directly without shell (avoids path quoting issues)
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=check)
        return result.returncode == 0
    else:
        # If it's a string, use shell
        print(f"Running: {cmd}")
        result = subprocess.run(cmd, shell=True, check=check)
        return result.returncode == 0

def build_pyinstaller():
    """Build the application with PyInstaller."""
    print("\n" + "="*60)
    print("Building application with PyInstaller...")
    print("="*60)
    
    if not Path("pyinstaller.spec").exists():
        print("Error: pyinstaller.spec not found!")
        return False
    
    # Clean previous builds
    if Path("build").exists():
        shutil.rmtree("build")
    if Path("dist").exists():
        shutil.rmtree("dist")
    
    # Build - use list format to avoid shell quoting issues with paths containing spaces
    cmd = [sys.executable, "-m", "PyInstaller", "pyinstaller.spec", "--clean"]
    env = os.environ.copy()
    if platform.system() == "Darwin":
        target_arch = os.environ.get("PYI_TARGET_ARCH", "universal2").strip()
        if target_arch:
            print(f"Using PyInstaller target arch: {target_arch}")
            env["PYI_TARGET_ARCH"] = target_arch
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, env=env)
    return result.returncode == 0

def build_windows_installer():
    """Build Windows installer with Inno Setup."""
    print("\n" + "="*60)
    print("Building Windows installer with Inno Setup...")
    print("="*60)
    
    if not Path("installer/windows/setup.iss").exists():
        print("Error: installer/windows/setup.iss not found!")
        return False
    
    # Check if Inno Setup is installed
    inno_compiler = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if not Path(inno_compiler).exists():
        inno_compiler = r"C:\Program Files\Inno Setup 6\ISCC.exe"
        if not Path(inno_compiler).exists():
            print("Error: Inno Setup compiler not found!")
            print("Please install Inno Setup from https://jrsoftware.org/isdl.php")
            return False
    
    cmd = f'"{inno_compiler}" installer/windows/setup.iss'
    return run_command(cmd)

def build_macos_installer():
    """Build macOS DMG installer."""
    print("\n" + "="*60)
    print("Building macOS DMG installer...")
    print("="*60)
    
    if not Path("installer/macos/build_dmg.sh").exists():
        print("Error: installer/macos/build_dmg.sh not found!")
        return False
    
    if platform.system() != "Darwin":
        print("Warning: macOS installer can only be built on macOS")
        return False
    
    # PyInstaller already ran in build_pyinstaller(); skip duplicate build in DMG script.
    cmd = "SKIP_PYINSTALLER=1 bash installer/macos/build_dmg.sh"
    return run_command(cmd)

def build_linux_installer():
    """Build Linux AppImage."""
    print("\n" + "="*60)
    print("Building Linux AppImage...")
    print("="*60)
    
    if not Path("installer/linux/build_appimage.sh").exists():
        print("Error: installer/linux/build_appimage.sh not found!")
        return False
    
    if platform.system() != "Linux":
        print("Warning: Linux installer can only be built on Linux")
        return False
    
    cmd = "bash installer/linux/build_appimage.sh"
    return run_command(cmd)

def main():
    """Main build function."""
    print("YT Stream 24/7 Reencoder - Build Script")
    print("="*60)
    
    current_platform = platform.system()
    print(f"Current platform: {current_platform}")
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("Error: PyInstaller not installed!")
        print("Install it with: pip install pyinstaller")
        return 1
    
    # Build PyInstaller executable first
    if not build_pyinstaller():
        print("\nError: PyInstaller build failed!")
        return 1
    
    # Build platform-specific installer
    success = False
    if current_platform == "Windows":
        success = build_windows_installer()
    elif current_platform == "Darwin":
        success = build_macos_installer()
    elif current_platform == "Linux":
        success = build_linux_installer()
    else:
        print(f"Unknown platform: {current_platform}")
        return 1
    
    if success:
        print("\n" + "="*60)
        print("Build completed successfully!")
        print("="*60)
        return 0
    else:
        print("\n" + "="*60)
        print("Build failed!")
        print("="*60)
        return 1

if __name__ == "__main__":
    sys.exit(main())

