import subprocess
import os
import sys

try:
    print("Searching for processes on port 8000...")
    out = subprocess.check_output('netstat -ano', shell=True).decode('utf-8', errors='ignore')
    pids = set()
    for line in out.splitlines():
        if ':8000' in line and 'LISTENING' in line:
            parts = line.strip().split()
            if len(parts) >= 5:
                try:
                    pid = int(parts[-1])
                    pids.add(pid)
                except ValueError:
                    pass
    
    print("Found PIDs on port 8000:", pids)
    my_pid = os.getpid()
    for pid in pids:
        if pid == my_pid:
            continue
        try:
            print(f"Killing process {pid} using taskkill...")
            subprocess.run(f"taskkill /F /PID {pid}", shell=True)
        except Exception as ex:
            print(f"Failed to kill process {pid}: {ex}")
except Exception as e:
    print("Error:", e)
