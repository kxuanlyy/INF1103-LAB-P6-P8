import subprocess
import sys

# 1. Run the first script
print("Starting file1...")
subprocess.run([sys.executable, "io_manager.py"], check=True)

