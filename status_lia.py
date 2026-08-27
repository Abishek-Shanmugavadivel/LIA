"""
LIA Windows Launcher — Status of LIA Process
Reports LIA process running status and PID.
"""
import sys
import json
from process_manager import get_process_manager

if __name__ == "__main__":
    pm = get_process_manager()
    res = pm.status()
    print(json.dumps(res, indent=2))
    sys.exit(0)
