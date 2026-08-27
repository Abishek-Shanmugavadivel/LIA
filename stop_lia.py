"""
LIA Windows Launcher — Stop LIA Process
Stops LIA process safely.
"""
import sys
import json
from process_manager import get_process_manager

if __name__ == "__main__":
    pm = get_process_manager()
    res = pm.stop()
    print(json.dumps(res, indent=2))
    sys.exit(0 if res.get("success") else 1)
