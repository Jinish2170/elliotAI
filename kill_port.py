import os
import signal
import subprocess
import re

def free_port(port):
    try:
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)        
        lines = result.stdout.splitlines()
        for line in lines:
            if f':{port}' in line and 'LISTENING' in line:
                parts = re.split(r'\s+', line.strip())
                pid = int(parts[-1])
                print(f"Found process {pid} listening on port {port}. Terminating...")
                os.kill(pid, signal.SIGTERM) 
                print(f"Process {pid} terminated.")
                return
        print(f"No process found listening on port {port}.")
    except Exception as e:
        print(f"Could not free port {port}: {e}")

if __name__ == '__main__':
    free_port(8000)
