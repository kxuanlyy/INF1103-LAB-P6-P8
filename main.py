import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

print("Starting file1...")
subprocess.run(
    [sys.executable, str(BASE_DIR / "io_manager.py")],
    check=True,
    cwd=BASE_DIR,
)