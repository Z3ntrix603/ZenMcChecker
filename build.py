"""Build a portable Windows executable: python build.py [--output PATH]."""
import argparse
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("dist"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--windowed",
                    "--name", "ZenMcChecker", "--collect-all", "customtkinter",
                    "--icon", str(root / "assets" / "studio.ico"),
                    "--add-data", str(root / "assets") + ";assets",
                    "--distpath", str(args.output.resolve()),
                    "--workpath", str(root / "build"), "--specpath", str(root / "build"),
                    str(root / "run.py")], cwd=root, check=True)


if __name__ == "__main__":
    main()
