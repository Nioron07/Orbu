"""
Build script for Orbu Deployer.

Creates standalone executables for Windows, macOS, and Linux using PyInstaller.

Usage:
    python build.py          # Build for current platform
    python build.py --clean  # Clean build artifacts first
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path


# Paths
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
DIST_DIR = SCRIPT_DIR / 'dist'
BUILD_DIR = SCRIPT_DIR / 'build'

# Files/folders to bundle as Orbu source
ORBU_SOURCE_ITEMS = [
    'backend',
    'frontend',
    'nginx',
    'docker',
    'Dockerfile',
]


def clean():
    """Remove build artifacts."""
    print("Cleaning build artifacts...")
    for path in [DIST_DIR, BUILD_DIR, SCRIPT_DIR / '__pycache__']:
        if path.exists():
            shutil.rmtree(path)
            print(f"  Removed: {path}")

    # Remove .spec files
    for spec_file in SCRIPT_DIR.glob('*.spec'):
        spec_file.unlink()
        print(f"  Removed: {spec_file}")


def check_pyinstaller():
    """Check if PyInstaller is installed."""
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("ERROR: PyInstaller is not installed.")
        print("Install it with: pip install pyinstaller")
        return False


def get_platform_name():
    """Get the current platform name for the output file."""
    if sys.platform == 'win32':
        return 'windows'
    elif sys.platform == 'darwin':
        return 'macos'
    else:
        return 'linux'


def build_add_data_args():
    """Build the --add-data arguments for PyInstaller."""
    add_data = []
    separator = ';' if sys.platform == 'win32' else ':'

    # Add assets folder (but not the icon, that's handled separately)
    assets_dir = SCRIPT_DIR / 'assets'
    if assets_dir.exists():
        add_data.append(f'--add-data={assets_dir}{separator}assets')

    # Add Orbu source files for Docker build
    for item in ORBU_SOURCE_ITEMS:
        source_path = PROJECT_ROOT / item
        if source_path.exists():
            if source_path.is_file():
                # For single files, destination must be a directory (orbu_source/)
                # The file will keep its original name inside that directory
                add_data.append(f'--add-data={source_path}{separator}orbu_source')
            else:
                # For directories, specify the full destination path
                add_data.append(f'--add-data={source_path}{separator}orbu_source/{item}')
        else:
            print(f"WARNING: Source item not found: {source_path}")

    return add_data


def get_icon_path():
    """Get the appropriate icon path for the current platform."""
    if sys.platform == 'darwin':
        # macOS needs .icns format
        icon_path = SCRIPT_DIR / 'assets' / 'icon.icns'
    else:
        # Windows and Linux use .ico
        icon_path = SCRIPT_DIR / 'assets' / 'icon.ico'

    return icon_path if icon_path.exists() else None


def build():
    """Build the executable using PyInstaller."""
    if not check_pyinstaller():
        return False

    platform = get_platform_name()
    output_name = f'orbu-deployer-{platform}'

    print(f"\nBuilding Orbu Deployer for {platform}...")
    print(f"Output: {output_name}")

    # Build PyInstaller command
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--windowed',
        f'--name={output_name}',
        f'--distpath={DIST_DIR}',
        f'--workpath={BUILD_DIR}',
        f'--specpath={SCRIPT_DIR}',
    ]

    # Add icon if available (platform-specific format)
    icon_path = get_icon_path()
    if icon_path:
        cmd.append(f'--icon={icon_path}')

    # Add data files
    cmd.extend(build_add_data_args())

    # Add hidden imports that PyInstaller might miss
    hidden_imports = [
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'queue',
        'threading',
        'subprocess',
        'webbrowser',
        'json',
        'dataclasses',
        'enum',
        'abc',
        'typing',
    ]
    for imp in hidden_imports:
        cmd.append(f'--hidden-import={imp}')

    # Main script
    cmd.append(str(SCRIPT_DIR / 'deployer.py'))

    print("\nRunning PyInstaller...")
    print(f"Command: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(cmd, cwd=SCRIPT_DIR, check=True)
        print(f"\nBuild successful!")
        print(f"Output: {DIST_DIR / output_name}")

        # Add .exe extension info for Windows
        if platform == 'windows':
            exe_path = DIST_DIR / f'{output_name}.exe'
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"Size: {size_mb:.1f} MB")

        return True

    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error code: {e.returncode}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Build Orbu Deployer executable')
    parser.add_argument('--clean', action='store_true', help='Clean build artifacts before building')
    parser.add_argument('--clean-only', action='store_true', help='Only clean, do not build')
    args = parser.parse_args()

    os.chdir(SCRIPT_DIR)

    if args.clean or args.clean_only:
        clean()

    if args.clean_only:
        return

    print("=" * 60)
    print("Orbu Deployer Build Script")
    print("=" * 60)

    success = build()

    if success:
        print("\n" + "=" * 60)
        print("BUILD COMPLETE")
        print("=" * 60)
        print(f"\nExecutable location: {DIST_DIR}")
        print("\nTo distribute:")
        print(f"  1. Test the executable on a clean machine")
        print(f"  2. Upload to GitHub Releases")
    else:
        print("\n" + "=" * 60)
        print("BUILD FAILED")
        print("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    main()
