<<<<<<< HEAD
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
=======
# main.py
import io_manager

if __name__ == "__main__":
    io_manager.main()
>>>>>>> ef68fa88c472599ae2da2550c91a64224e229087
