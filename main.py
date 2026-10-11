import subprocess

# 1. Run the first script
print("Starting file1...")
subprocess.run(["python", "io_manager.py"], check=True)

# 2. This line will only execute after file1.py finishes
print("file1 finished. Starting file2...")
subprocess.run(["python", "logic_manager.py"], check=True)
