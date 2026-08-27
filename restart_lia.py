"""
LIA Windows Launcher — Restart LIA Process
Restarts LIA process safely.
"""
import sys
import json
from process_manager import get_process_manager

if __name__ == "__main__":
    pm = get_process_manager()
    res = pm.restart()
    print(json.dumps(res, indent=2))
    sys.exit(0 if res.get("success") else 1)
